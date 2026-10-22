"""Pure safety checks for the opt-in native PostgreSQL archive harness."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from .native_postgres_archive import (
    NativePostgresCluster,
    NativePostgresConfigurationError,
    PostgresBinaries,
    build_pg_ctl_start_options,
    conflicting_database_environment_keys,
    inspect_postgres_17_binaries,
    require_explicit_native_pg_options,
    require_sanitized_database_environment,
)

pytestmark = pytest.mark.unit


def test_native_runtime_requires_two_explicit_cli_gates(tmp_path: Path) -> None:
    binary_directory = (tmp_path / "postgres-bin").resolve()
    binary_directory.mkdir()

    with pytest.raises(NativePostgresConfigurationError, match="--run-native-archive-pg"):
        require_explicit_native_pg_options(False, binary_directory)
    with pytest.raises(NativePostgresConfigurationError, match="--native-pg-bin-dir"):
        require_explicit_native_pg_options(True, None)
    with pytest.raises(NativePostgresConfigurationError, match="absolute path"):
        require_explicit_native_pg_options(True, Path("postgres-bin"))

    cluster = NativePostgresCluster(binary_directory, explicitly_enabled=True)
    assert cluster.root is None
    assert cluster.data_directory is None
    cluster.socket_directory = tmp_path / "socket"
    parameters = cluster._connection_parameters("synthetic_database", "synthetic_reader", 4)
    assert parameters["dbname"] == "synthetic_database"
    assert parameters["user"] == "synthetic_reader"
    assert parameters["host"] == str(cluster.socket_directory)
    assert parameters["port"] == 55491
    assert parameters["passfile"] == os.devnull
    assert parameters["options"] == ""
    assert parameters["sslmode"] == "disable"
    assert "service" not in parameters
    assert "database_url" not in parameters


def test_poisoned_database_environment_is_rejected_by_key_name_only() -> None:
    poisoned_environment = {
        "PATH": "/bin",
        "PGSERVICEFILE": "poison-service-file-sentinel",
        "PGOPTIONS": "poison-options-sentinel",
        "DATABASE_URL": "poison-database-url-sentinel",
    }
    poisoned_keys = poisoned_environment.keys()
    assert conflicting_database_environment_keys(poisoned_keys) == (
        "DATABASE_URL",
        "PGOPTIONS",
        "PGSERVICEFILE",
    )
    with pytest.raises(NativePostgresConfigurationError) as error:
        require_sanitized_database_environment(poisoned_keys)
    message = str(error.value)
    assert "PGSERVICEFILE" in message and "DATABASE_URL" in message
    assert all(value not in message for key, value in poisoned_environment.items() if key != "PATH")


def test_binary_inspection_uses_only_exact_supplied_directory_and_scrubbed_env(
    tmp_path: Path,
) -> None:
    binary_directory = (tmp_path / "postgres-bin").resolve()
    binary_directory.mkdir()
    for name in ("initdb", "pg_ctl", "postgres"):
        executable = binary_directory / name
        executable.write_text("fake executable; never executed\n", encoding="utf-8")
        executable.chmod(0o700)

    inspected: list[tuple[str, ...]] = []

    def fake_runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        inspected.append(tuple(command))
        assert Path(command[0]).parent == binary_directory
        assert kwargs["cwd"] == str(binary_directory)
        environment = kwargs["env"]
        assert isinstance(environment, dict)
        assert "DATABASE_URL" not in environment
        assert not any(key.startswith("PG") for key in environment)
        assert set(environment) == {"PATH", "LC_ALL", "LANG", "TZ", "TMPDIR"}
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=f"{Path(command[0]).name} (PostgreSQL) 17.11\n",
            stderr="",
        )

    binaries = inspect_postgres_17_binaries(binary_directory, runner=fake_runner)
    assert binaries.directory == binary_directory
    assert binaries.version.startswith("postgres (PostgreSQL) 17.11")
    assert {Path(command[0]).name for command in inspected} == {"initdb", "pg_ctl", "postgres"}


def test_server_options_are_unix_socket_only_and_private(tmp_path: Path) -> None:
    options = build_pg_ctl_start_options(tmp_path / "socket")
    assert "-c listen_addresses=''" in options
    assert "-c unix_socket_permissions=0700" in options
    assert "-c ssl=off" in options
    assert f"unix_socket_directories={tmp_path}/socket" in options


@pytest.mark.parametrize("status_codes", [(4,), (0, 0, 4)])
def test_unknown_pg_ctl_status_preserves_owned_cluster_and_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    status_codes: tuple[int, ...],
) -> None:
    from . import native_postgres_archive as harness

    binary_directory = (tmp_path / "postgres-bin").resolve()
    binary_directory.mkdir()
    cluster = NativePostgresCluster(binary_directory, explicitly_enabled=True)
    root = (tmp_path / "owned-root").resolve()
    root.mkdir(mode=0o700)
    data_directory = root / "cluster"
    socket_directory = root / "socket"
    artifacts_directory = root / "artifacts"
    for directory in (data_directory, socket_directory, artifacts_directory):
        directory.mkdir(mode=0o700)
        (directory / "owned-marker").write_text("synthetic", encoding="utf-8")
    log_path = root / "postgres.log"
    log_path.write_text("bounded synthetic server log\n", encoding="utf-8")
    evidence_path = root / "evidence.json"
    cluster.binaries = PostgresBinaries(
        directory=binary_directory,
        initdb=binary_directory / "initdb",
        pg_ctl=binary_directory / "pg_ctl",
        postgres=binary_directory / "postgres",
        version="postgres (PostgreSQL) 17.11",
    )
    cluster.root = root
    cluster.data_directory = data_directory
    cluster.socket_directory = socket_directory
    cluster.artifacts_directory = artifacts_directory
    cluster.log_path = log_path
    cluster.evidence_path = evidence_path
    calls: list[tuple[str, ...]] = []
    remaining_codes = iter(status_codes)

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        del kwargs
        calls.append(tuple(command))
        code = next(remaining_codes)
        return subprocess.CompletedProcess(command, code, stdout="", stderr="synthetic status")

    monkeypatch.setattr(harness.subprocess, "run", fake_run)
    assert cluster.shutdown() == evidence_path

    assert data_directory.is_dir()
    assert socket_directory.is_dir()
    assert artifacts_directory.is_dir()
    assert log_path.is_file()
    assert [call[-1] for call in calls] == (
        ["status"] if status_codes == (4,) else ["status", "stop", "status"]
    )
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert evidence["server_stopped"] is False
    assert any(
        event.get("action") == "server_stop" and event.get("status_code") == 4
        for event in evidence["lifecycle"]
    )
