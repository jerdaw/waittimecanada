"""Isolated, explicit-opt-in PostgreSQL 17 support for archive tests.

Nothing in this module runs at import time. Native PostgreSQL starts only when
the integration fixture is requested with both explicit pytest options. It
never reads DATABASE_URL or PG* environment values, rejects those inherited
key names before use, and connects only to a fresh Unix socket below its own
private /private/tmp directory.
"""

from __future__ import annotations

import hashlib
import json
import os
import pwd
import re
import shlex
import shutil
import stat
import subprocess
import tempfile
import uuid
from collections.abc import Callable, Generator, Iterable, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

import psycopg2
import psycopg2.extras
from psycopg2 import sql

from waittime.services.measurement_archive import MEASUREMENT_FIELDS, MEASUREMENT_QUERY

PG_MAJOR_VERSION = 17
PG_SOCKET_PORT = 55491
MAX_EVIDENCE_BYTES = 16_384
MAX_LOG_TAIL_BYTES = 8_192
MIGRATION_FILES = (
    "001_create_enums.sql",
    "002_create_tables.sql",
    "008_add_anomaly_columns.sql",
    "011_add_occupancy_columns.sql",
)
WAIT_TIME_ONTOLOGY = (
    "TIME_TO_PROVIDER",
    "TRIAGE",
    "PHYSICIAN",
    "P90",
    "ALL",
)
# Match QuebecScraper's current point-in-time snapshot tag: UNKNOWN / PHYSICIAN / POINT_ESTIMATE.
OCCUPANCY_SNAPSHOT_ONTOLOGY = (
    "STRETCHER_OCCUPANCY",
    "UNKNOWN",
    "PHYSICIAN",
    "POINT_ESTIMATE",
    "ALL",
)
FIXTURE_ENUM_VALUES = {
    "metric_family_enum": frozenset((WAIT_TIME_ONTOLOGY[0], OCCUPANCY_SNAPSHOT_ONTOLOGY[0])),
    "start_event_enum": frozenset((WAIT_TIME_ONTOLOGY[1], OCCUPANCY_SNAPSHOT_ONTOLOGY[1])),
    "end_event_enum": frozenset((WAIT_TIME_ONTOLOGY[2], OCCUPANCY_SNAPSHOT_ONTOLOGY[2])),
    "statistic_type_enum": frozenset((WAIT_TIME_ONTOLOGY[3], OCCUPANCY_SNAPSHOT_ONTOLOGY[3])),
    "patient_scope_enum": frozenset((WAIT_TIME_ONTOLOGY[4], OCCUPANCY_SNAPSHOT_ONTOLOGY[4])),
}


class NativePostgresConfigurationError(RuntimeError):
    """The explicit native PostgreSQL test configuration is unsafe or invalid."""


class NativePostgresLifecycleError(RuntimeError):
    """The owned native PostgreSQL cluster could not be safely managed."""


@dataclass(frozen=True)
class PostgresBinaries:
    directory: Path
    initdb: Path
    pg_ctl: Path
    postgres: Path
    version: str


def require_explicit_native_pg_options(
    enabled: bool,
    binary_directory: Path | None,
) -> Path:
    """Require both the run switch and a supplied absolute binary directory."""
    if not enabled:
        raise NativePostgresConfigurationError(
            "native PostgreSQL tests require --run-native-archive-pg"
        )
    if binary_directory is None:
        raise NativePostgresConfigurationError(
            "native PostgreSQL tests require --native-pg-bin-dir"
        )
    if not binary_directory.is_absolute():
        raise NativePostgresConfigurationError("--native-pg-bin-dir must be an absolute path")
    if binary_directory.is_symlink():
        raise NativePostgresConfigurationError("--native-pg-bin-dir must not be a symlink")
    try:
        resolved = binary_directory.resolve(strict=True)
    except OSError as exc:
        raise NativePostgresConfigurationError("--native-pg-bin-dir is unavailable") from exc
    if resolved != binary_directory:
        raise NativePostgresConfigurationError(
            "--native-pg-bin-dir must be its canonical absolute path"
        )
    if not resolved.is_dir():
        raise NativePostgresConfigurationError("--native-pg-bin-dir must name a directory")
    return resolved


def conflicting_database_environment_keys(environment_keys: Iterable[str]) -> tuple[str, ...]:
    """Return only names of inherited DB settings, never their values."""
    return tuple(
        sorted(key for key in environment_keys if key == "DATABASE_URL" or key.startswith("PG"))
    )


def require_sanitized_database_environment(environment_keys: Iterable[str]) -> None:
    """Reject inherited database settings before libpq or a PostgreSQL tool runs."""
    conflicts = conflicting_database_environment_keys(environment_keys)
    if conflicts:
        names = ", ".join(conflicts)
        raise NativePostgresConfigurationError(
            "native archive tests require a sanitized process environment; "
            f"remove inherited database setting keys: {names}"
        )


def _private_subprocess_environment(binary_directory: Path, temp_directory: Path) -> dict[str, str]:
    """Use a minimal environment without inheriting DB URLs or PG* settings."""
    return {
        "PATH": os.pathsep.join((str(binary_directory), "/usr/bin", "/bin")),
        "LC_ALL": "C",
        "LANG": "C",
        "TZ": "UTC",
        "TMPDIR": str(temp_directory),
    }


def inspect_postgres_17_binaries(
    binary_directory: Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> PostgresBinaries:
    """Validate only the named executables inside the supplied binary folder."""
    directory = require_explicit_native_pg_options(True, binary_directory)
    paths: dict[str, Path] = {}
    versions: dict[str, tuple[int, int, str]] = {}
    environment = _private_subprocess_environment(directory, Path("/private/tmp"))

    for name in ("initdb", "pg_ctl", "postgres"):
        executable = directory / name
        if (
            executable.is_symlink()
            or not executable.is_file()
            or not os.access(executable, os.X_OK)
        ):
            raise NativePostgresConfigurationError(
                f"required executable is missing or unsafe: {name}"
            )
        paths[name] = executable
        try:
            result = runner(
                [str(executable), "--version"],
                check=False,
                capture_output=True,
                text=True,
                cwd=str(directory),
                env=environment,
                timeout=10,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise NativePostgresConfigurationError(
                f"could not inspect PostgreSQL binary: {name}"
            ) from exc
        output = f"{result.stdout}\n{result.stderr}".strip()
        match = re.search(r"\b(\d+)\.(\d+)(?:\.\d+)?\b", output)
        if result.returncode != 0 or match is None:
            raise NativePostgresConfigurationError(
                f"could not parse PostgreSQL binary version: {name}"
            )
        major, minor = int(match.group(1)), int(match.group(2))
        if major != PG_MAJOR_VERSION:
            raise NativePostgresConfigurationError(
                f"PostgreSQL {PG_MAJOR_VERSION} is required; {name} reports {major}"
            )
        versions[name] = (major, minor, output)

    numeric_versions = {(major, minor) for major, minor, _ in versions.values()}
    if len(numeric_versions) != 1:
        raise NativePostgresConfigurationError(
            "initdb, pg_ctl, and postgres must report the same PostgreSQL 17 minor version"
        )
    return PostgresBinaries(
        directory=directory,
        initdb=paths["initdb"],
        pg_ctl=paths["pg_ctl"],
        postgres=paths["postgres"],
        version=versions["postgres"][2],
    )


def build_pg_ctl_start_options(socket_directory: Path) -> str:
    """Return server options that disable TCP and bind only the owned socket."""
    socket_path = str(socket_directory)
    return " ".join(
        (
            "-c listen_addresses=''",
            f"-c port={PG_SOCKET_PORT}",
            f"-c unix_socket_directories={shlex.quote(socket_path)}",
            "-c unix_socket_permissions=0700",
            "-c ssl=off",
        )
    )


def _make_private_directory(path: Path) -> None:
    path.mkdir(mode=0o700)
    os.chmod(path, 0o700)
    if stat.S_IMODE(path.stat().st_mode) != 0o700:
        raise NativePostgresLifecycleError("private test directory permissions were not applied")


class NativePostgresCluster:
    """One owned ephemeral cluster with bounded evidence and exact-child cleanup."""

    def __init__(self, binary_directory: Path, *, explicitly_enabled: bool) -> None:
        self.binary_directory = require_explicit_native_pg_options(
            explicitly_enabled,
            binary_directory,
        )
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            raise NativePostgresConfigurationError("initdb must run as an unprivileged local user")
        self.binaries: PostgresBinaries | None = None
        self.owner = pwd.getpwuid(os.getuid()).pw_name
        self.root: Path | None = None
        self.data_directory: Path | None = None
        self.socket_directory: Path | None = None
        self.artifacts_directory: Path | None = None
        self.log_path: Path | None = None
        self.evidence_path: Path | None = None
        self._started = False
        self._owned_databases: set[str] = set()
        self._owned_roles: set[str] = set()
        self._artifact_paths: set[Path] = set()
        self._evidence: dict[str, Any] = {
            "format": "wtc-native-archive-pg-evidence-v1",
            "postgres_major_required": PG_MAJOR_VERSION,
            "test_results": [],
            "migrations": [],
            "database_cleanup": [],
            "lifecycle": [],
        }

    def _command(
        self,
        command: Sequence[str],
        *,
        timeout: int = 30,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        if self.root is None or self.binaries is None:
            raise NativePostgresLifecycleError("cluster directories are not initialized")
        # Only fixed subcommands and paths validated below the supplied bin directory reach here.
        result = subprocess.run(  # noqa: S603
            list(command),
            check=False,
            capture_output=True,
            text=True,
            cwd=str(self.root),
            env=_private_subprocess_environment(self.binaries.directory, self.root),
            timeout=timeout,
        )
        self._record_lifecycle(
            {
                "command": Path(command[0]).name,
                "exit_code": result.returncode,
                "action": command[-1] if command else "unknown",
            }
        )
        if check and result.returncode != 0:
            details = (result.stderr or result.stdout or "").strip()[-1_000:]
            raise NativePostgresLifecycleError(
                f"owned PostgreSQL command failed ({Path(command[0]).name}): {details}"
            )
        return result

    def _record_lifecycle(self, event: Mapping[str, Any]) -> None:
        lifecycle = self._evidence["lifecycle"]
        if len(lifecycle) < 64:
            lifecycle.append(dict(event))

    def record_test_result(self, test_name: str, phase: str, outcome: str) -> None:
        results = self._evidence["test_results"]
        if len(results) < 64:
            results.append({"test": test_name, "phase": phase, "outcome": outcome})

    def record_assertion(self, name: str, values: Mapping[str, Any]) -> None:
        assertions = self._evidence.setdefault("assertions", [])
        if len(assertions) < 32:
            assertions.append({"name": name, **dict(values)})

    def start(self) -> NativePostgresCluster:
        if self.root is not None:
            raise NativePostgresLifecycleError("cluster start may be called only once")
        require_sanitized_database_environment(os.environ.keys())
        self.binaries = inspect_postgres_17_binaries(self.binary_directory)
        base = Path("/private/tmp")
        if not base.is_dir() or base.is_symlink():
            raise NativePostgresConfigurationError("required private temporary directory is unsafe")
        self.root = Path(tempfile.mkdtemp(prefix="wtc-native-archive-", dir=str(base)))
        os.chmod(self.root, 0o700)
        self.data_directory = self.root / "cluster"
        self.socket_directory = self.root / "socket"
        self.artifacts_directory = self.root / "artifacts"
        self.log_path = self.root / "postgres.log"
        self.evidence_path = self.root / "evidence.json"
        _make_private_directory(self.data_directory)
        _make_private_directory(self.socket_directory)
        _make_private_directory(self.artifacts_directory)
        descriptor = os.open(
            self.log_path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
        os.fchmod(descriptor, 0o600)
        os.close(descriptor)
        self._evidence["postgres_version"] = self.binaries.version
        self._evidence["binary_directory"] = str(self.binaries.directory)
        self._evidence["cluster_directory_mode"] = "0700"
        try:
            self._command(
                (
                    str(self.binaries.initdb),
                    "--pgdata",
                    str(self.data_directory),
                    f"--username={self.owner}",
                    "--no-locale",
                    "--encoding=UTF8",
                    "--auth-local=trust",
                    "--auth-host=reject",
                ),
                timeout=60,
            )
            start_options = build_pg_ctl_start_options(self.socket_directory)
            self._command(
                (
                    str(self.binaries.pg_ctl),
                    "-D",
                    str(self.data_directory),
                    "-o",
                    start_options,
                    "-l",
                    str(self.log_path),
                    "-w",
                    "-t",
                    "30",
                    "start",
                ),
                timeout=40,
            )
            self._started = True
            self._verify_socket_only_server()
            self._evidence["network"] = {
                "listen_addresses": "",
                "unix_socket_only": True,
                "socket_permissions": "0700",
            }
            return self
        except BaseException:
            self.shutdown()
            raise

    def _connection_parameters(self, database: str, role: str, timeout: int) -> dict[str, Any]:
        if self.socket_directory is None:
            raise NativePostgresLifecycleError("cluster socket is not initialized")
        # No URL or service is used; passfile is pinned to os.devnull and settings are explicit.
        return {
            "dbname": database,
            "user": role,
            "host": str(self.socket_directory),
            "hostaddr": "",
            "port": PG_SOCKET_PORT,
            "connect_timeout": timeout,
            "password": "",
            "passfile": os.devnull,
            "options": "",
            "sslmode": "disable",
            "gssencmode": "disable",
            "client_encoding": "UTF8",
            "application_name": "wtc-native-archive-validation",
            "target_session_attrs": "any",
        }

    def connect(self, database: str, role: str, *, timeout: int = 5) -> Any:
        require_sanitized_database_environment(os.environ.keys())
        return psycopg2.connect(**self._connection_parameters(database, role, timeout))

    @contextmanager
    def admin_connection(self, database: str = "postgres") -> Generator[Any, None, None]:
        connection = self.connect(database, self.owner)
        try:
            yield connection
            if not connection.autocommit:
                connection.commit()
        except BaseException:
            if not connection.closed:
                connection.rollback()
            raise
        finally:
            connection.close()

    def _verify_socket_only_server(self) -> None:
        with self.admin_connection() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT current_setting('listen_addresses') AS listen_addresses, "
                    "current_setting('unix_socket_permissions') AS socket_permissions, "
                    "inet_server_addr() AS server_address"
                )
                row = cursor.fetchone()
        if (
            row is None
            or row["listen_addresses"] != ""
            or row["socket_permissions"] != "0700"
            or row["server_address"] is not None
        ):
            raise NativePostgresLifecycleError(
                "PostgreSQL did not bind exclusively to its Unix socket"
            )

    def create_database(self) -> NativePostgresDatabase:
        suffix = uuid.uuid4().hex[:12]
        database_name = f"wtc_archive_test_{suffix}"
        reader_role = f"wtc_archive_reader_{suffix}"
        if database_name in self._owned_databases or reader_role in self._owned_roles:
            raise NativePostgresLifecycleError("generated native test identifier collision")
        with self.admin_connection() as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL(
                        "CREATE ROLE {} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT"
                    ).format(sql.Identifier(reader_role))
                )
                self._owned_roles.add(reader_role)
                cursor.execute(
                    sql.SQL("CREATE DATABASE {} OWNER {}").format(
                        sql.Identifier(database_name),
                        sql.Identifier(self.owner),
                    )
                )
                self._owned_databases.add(database_name)
        database = NativePostgresDatabase(self, database_name, reader_role)
        try:
            database.apply_migrations()
            database.create_reader_grants()
            database.insert_synthetic_parents()
        except BaseException:
            database.drop()
            raise
        return database

    def drop_database(self, database_name: str, reader_role: str) -> None:
        if database_name not in self._owned_databases or reader_role not in self._owned_roles:
            raise NativePostgresLifecycleError("refusing to drop a non-owned test database or role")
        with self.admin_connection() as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(database_name)))
                self._owned_databases.remove(database_name)
                cursor.execute(sql.SQL("DROP ROLE {}").format(sql.Identifier(reader_role)))
                self._owned_roles.remove(reader_role)
        database_cleanup = self._evidence["database_cleanup"]
        if len(database_cleanup) < 32:
            database_cleanup.append({"database_dropped": True, "reader_role_dropped": True})

    def archive_destination(self, label: str) -> Path:
        if self.artifacts_directory is None:
            raise NativePostgresLifecycleError("cluster artifact directory is not initialized")
        safe_label = re.sub(r"[^a-z0-9-]+", "-", label.lower()).strip("-")[:32] or "archive"
        destination = self.artifacts_directory / f"{safe_label}-{uuid.uuid4().hex[:12]}"
        self._artifact_paths.add(destination)
        return destination

    def record_archive_verification(self, label: str, result: Any) -> None:
        self.record_assertion(
            label,
            {
                "row_count": result.row_count,
                "artifact_sha256": result.artifact_sha256,
                "manifest_sha256": result.manifest_sha256,
                "offline_readback_verified": result.offline_readback_verified,
            },
        )

    def _server_state(self) -> tuple[Literal["running", "stopped", "unknown"], int | None]:
        if self.binaries is None or self.data_directory is None:
            return "unknown", None
        result = self._command(
            (str(self.binaries.pg_ctl), "-D", str(self.data_directory), "status"),
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            return "running", result.returncode
        if result.returncode == 3:
            return "stopped", result.returncode
        return "unknown", result.returncode

    def shutdown(self) -> Path | None:
        if self.root is None:
            return None
        stop_succeeded = False
        status_code: int | None = None
        try:
            state, status_code = self._server_state()
            if state == "running":
                assert self.binaries is not None
                assert self.data_directory is not None
                stop_result = self._command(
                    (
                        str(self.binaries.pg_ctl),
                        "-D",
                        str(self.data_directory),
                        "-m",
                        "fast",
                        "-w",
                        "-t",
                        "30",
                        "stop",
                    ),
                    timeout=40,
                    check=False,
                )
                self._record_lifecycle(
                    {"action": "server_stop_command", "exit_code": stop_result.returncode}
                )
                state, status_code = self._server_state()
            stop_succeeded = state == "stopped"
            if stop_succeeded:
                self._started = False
            else:
                self._record_lifecycle(
                    {
                        "action": "server_stop",
                        "outcome": "unknown_or_running",
                        "status_code": status_code,
                    }
                )
        except BaseException as exc:
            stop_succeeded = False
            self._record_lifecycle(
                {"action": "server_stop", "outcome": "error", "error_type": type(exc).__name__}
            )

        if stop_succeeded:
            self._cleanup_owned_artifacts()
            self._remove_owned_child(self.data_directory)
            self._remove_owned_child(self.socket_directory)
            self._remove_owned_child(self.artifacts_directory)
            self._preserve_bounded_log_tail()
        else:
            self._record_lifecycle({"action": "server_log", "outcome": "preserved_with_owned_root"})
        self._write_evidence(stop_succeeded)
        return self.evidence_path

    def _remove_owned_child(self, path: Path | None) -> None:
        if path is None or self.root is None or path.parent != self.root:
            return
        try:
            root_metadata = self.root.lstat()
        except OSError:
            return
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
            self._record_lifecycle({"action": "cleanup", "outcome": "refused_unsafe_root"})
            return
        try:
            metadata = path.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            self._record_lifecycle({"action": "cleanup", "outcome": "refused_non_directory"})
            return
        shutil.rmtree(path)
        self._record_lifecycle({"action": "cleanup", "outcome": "owned_child_removed"})

    def _cleanup_owned_artifacts(self) -> None:
        if self.root is None or self.artifacts_directory is None:
            return
        if self.artifacts_directory.parent != self.root:
            return
        try:
            root_metadata = self.root.lstat()
            artifacts_metadata = self.artifacts_directory.lstat()
        except OSError:
            return
        if (
            stat.S_ISLNK(root_metadata.st_mode)
            or not stat.S_ISDIR(root_metadata.st_mode)
            or stat.S_ISLNK(artifacts_metadata.st_mode)
            or not stat.S_ISDIR(artifacts_metadata.st_mode)
        ):
            self._record_lifecycle(
                {"action": "artifact_cleanup", "outcome": "refused_unsafe_parent"}
            )
            return
        for artifact in tuple(self._artifact_paths):
            if artifact.parent != self.artifacts_directory:
                continue
            try:
                metadata = artifact.lstat()
            except FileNotFoundError:
                continue
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                self._record_lifecycle(
                    {"action": "artifact_cleanup", "outcome": "refused_non_directory"}
                )
                continue
            shutil.rmtree(artifact)
            self._record_lifecycle(
                {"action": "artifact_cleanup", "outcome": "owned_artifact_removed"}
            )

    def _preserve_bounded_log_tail(self) -> None:
        if self.root is None or self.log_path is None:
            return
        try:
            with self.log_path.open("rb") as log_stream:
                log_stream.seek(0, os.SEEK_END)
                log_size = log_stream.tell()
                log_stream.seek(max(0, log_size - MAX_LOG_TAIL_BYTES), os.SEEK_SET)
                tail = log_stream.read(MAX_LOG_TAIL_BYTES)
        except OSError:
            return
        tail_path = self.root / "postgres.log.tail"
        descriptor = os.open(tail_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(tail)
                stream.flush()
        finally:
            os.close(descriptor)
        try:
            self.log_path.unlink()
        except OSError:
            pass

    def _write_evidence(self, server_stopped: bool) -> None:
        if self.root is None:
            return
        self._evidence["server_stopped"] = server_stopped
        evidence = json.dumps(self._evidence, sort_keys=True, separators=(",", ":")).encode()
        if len(evidence) > MAX_EVIDENCE_BYTES:
            self._evidence["test_results"] = self._evidence["test_results"][-16:]
            self._evidence["lifecycle"] = self._evidence["lifecycle"][-32:]
            evidence = json.dumps(self._evidence, sort_keys=True, separators=(",", ":")).encode()
        if len(evidence) > MAX_EVIDENCE_BYTES or self.evidence_path is None:
            raise NativePostgresLifecycleError("native test evidence exceeded its size limit")
        descriptor = os.open(
            self.evidence_path,
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
            0o600,
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb", closefd=False) as stream:
                stream.write(evidence + b"\n")
                stream.flush()
                os.fsync(descriptor)
        finally:
            os.close(descriptor)


class NativePostgresDatabase:
    """A generated per-test database and non-superuser archive reader."""

    def __init__(self, cluster: NativePostgresCluster, name: str, reader_role: str) -> None:
        self.cluster = cluster
        self.name = name
        self.reader_role = reader_role
        self._dropped = False

    @contextmanager
    def admin_connection(self) -> Generator[Any, None, None]:
        with self.cluster.admin_connection(self.name) as connection:
            yield connection

    def reader_connection(self, *, timeout: int = 5) -> Any:
        return self.cluster.connect(self.name, self.reader_role, timeout=timeout)

    def archive_service(
        self,
        *,
        after_first_fetch: Callable[[], None] | None = None,
    ) -> NativeArchiveDatabaseService:
        return NativeArchiveDatabaseService(self, after_first_fetch=after_first_fetch)

    def apply_migrations(self) -> None:
        migration_directory = Path(__file__).resolve().parents[2] / "migrations"
        hashes: list[dict[str, str]] = []
        with self.admin_connection() as connection:
            with connection.cursor() as cursor:
                for filename in MIGRATION_FILES:
                    path = migration_directory / filename
                    contents = path.read_text(encoding="utf-8")
                    cursor.execute(contents)
                    hashes.append(
                        {"name": filename, "sha256": hashlib.sha256(contents.encode()).hexdigest()}
                    )
            connection.commit()
        migrations = self.cluster._evidence["migrations"]
        migrations.extend(hashes[: max(0, 32 - len(migrations))])

    def create_reader_grants(self) -> None:
        with self.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                        sql.Identifier(self.name),
                        sql.Identifier(self.reader_role),
                    )
                )
                cursor.execute(
                    sql.SQL("GRANT USAGE ON SCHEMA public TO {}").format(
                        sql.Identifier(self.reader_role)
                    )
                )
                cursor.execute(
                    sql.SQL("GRANT SELECT ON TABLE measurements TO {}").format(
                        sql.Identifier(self.reader_role)
                    )
                )
            connection.commit()

    def insert_synthetic_parents(self) -> None:
        with self.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO sources (
                        id, name, province, url, methodology_url,
                        telehealth_name, telehealth_number,
                        default_metric_family, default_start_event,
                        default_end_event, default_statistic_type
                    ) VALUES (
                        'wtc-native-source', 'Synthetic archive source', 'ON',
                        'https://example.invalid/source', 'https://example.invalid/methods',
                        'Synthetic 811', '811', %s, %s, %s, %s
                    )
                    """,
                    WAIT_TIME_ONTOLOGY[:4],
                )
                cursor.execute(
                    """
                    INSERT INTO hospitals (
                        id, name, province, city, latitude, longitude, source_id
                    ) VALUES (
                        'wtc-native-hospital', 'Synthetic archive hospital', 'ON',
                        'Example City', 45.0, -75.0, 'wtc-native-source'
                    )
                    """
                )
            connection.commit()

    def insert_synthetic_measurements(self, count: int = 3) -> list[int]:
        if not 1 <= count <= 20:
            raise ValueError("synthetic native fixture row count must be between 1 and 20")
        measurement_ids: list[int] = []
        timestamp = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
        with self.admin_connection() as connection:
            with connection.cursor() as cursor:
                for index in range(count):
                    occupancy = index == 1
                    ontology = OCCUPANCY_SNAPSHOT_ONTOLOGY if occupancy else WAIT_TIME_ONTOLOGY
                    raw_hash = hashlib.sha256(f"wtc-native-row-{index}".encode()).hexdigest()
                    cursor.execute(
                        """
                        INSERT INTO measurements (
                            hospital_id, timestamp_utc, value, metric_family,
                            start_event, end_event, statistic_type, patient_scope,
                            source_id, raw_payload_hash, raw_payload_snippet,
                            parser_version, is_anomaly, anomaly_reason,
                            patients_waiting, patients_in_treatment,
                            total_treatment_spaces, created_at
                        ) VALUES (
                            'wtc-native-hospital', %s, %s,
                            %s, %s, %s, %s, %s, 'wtc-native-source', %s, %s,
                            'native-fixture-v1', %s, %s, %s, %s, %s, %s
                        ) RETURNING id
                        """,
                        (
                            timestamp + timedelta(minutes=index),
                            float(120 + index),
                            *ontology,
                            raw_hash,
                            f"synthetic archive fixture row {index}" if index != 1 else None,
                            index == 2,
                            "synthetic anomaly fixture" if index == 2 else None,
                            0 if occupancy else None,
                            3 if occupancy else None,
                            8 if occupancy else None,
                            timestamp + timedelta(minutes=index, seconds=1),
                        ),
                    )
                    row = cursor.fetchone()
                    if row is None:
                        raise NativePostgresLifecycleError(
                            "synthetic measurement insert returned no id"
                        )
                    measurement_ids.append(int(row[0]))
            connection.commit()
        return measurement_ids

    def read_measurements(self) -> list[dict[str, Any]]:
        with self.admin_connection() as connection:
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.execute(MEASUREMENT_QUERY)
                return [dict(row) for row in cursor.fetchall()]

    def insert_archive_rows(self, rows: Sequence[Mapping[str, Any]]) -> None:
        columns = sql.SQL(", ").join(sql.Identifier(field) for field in MEASUREMENT_FIELDS)
        placeholders = sql.SQL(", ").join(sql.Placeholder() for _ in MEASUREMENT_FIELDS)
        statement = sql.SQL("INSERT INTO measurements ({}) VALUES ({})").format(
            columns,
            placeholders,
        )
        with self.admin_connection() as connection:
            with connection.cursor() as cursor:
                for row in rows:
                    values = tuple(
                        datetime.strptime(row[field], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)
                        if field in {"timestamp_utc", "created_at"}
                        else row[field]
                        for field in MEASUREMENT_FIELDS
                    )
                    cursor.execute(statement, values)
            connection.commit()

    def drop(self) -> None:
        if self._dropped:
            return
        self.cluster.drop_database(self.name, self.reader_role)
        self._dropped = True


class _CursorProxy:
    def __init__(
        self,
        cursor: Any,
        record_query: Callable[[str], None],
        after_first_fetch: Callable[[], None] | None,
    ) -> None:
        object.__setattr__(self, "_cursor", cursor)
        object.__setattr__(self, "_record_query", record_query)
        object.__setattr__(self, "_after_first_fetch", after_first_fetch)
        object.__setattr__(self, "_fetch_callback_called", False)

    def __enter__(self) -> _CursorProxy:
        self._cursor.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc: Any, traceback: Any) -> Any:
        return self._cursor.__exit__(exc_type, exc, traceback)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._cursor, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._cursor, name, value)

    def execute(self, query: str, *args: Any, **kwargs: Any) -> Any:
        self._record_query(" ".join(query.split()))
        return self._cursor.execute(query, *args, **kwargs)

    def fetchmany(self, size: int | None = None) -> list[Any]:
        rows = self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()
        callback = self._after_first_fetch
        if rows and callback is not None and not self._fetch_callback_called:
            object.__setattr__(self, "_fetch_callback_called", True)
            callback()
        return rows


class _ConnectionProxy:
    def __init__(self, connection: Any, service: NativeArchiveDatabaseService) -> None:
        self._connection = connection
        self._service = service

    def __getattr__(self, name: str) -> Any:
        return getattr(self._connection, name)

    def cursor(self, *args: Any, **kwargs: Any) -> _CursorProxy:
        cursor = self._connection.cursor(*args, **kwargs)
        after_first_fetch = self._service.after_first_fetch if kwargs.get("name") else None
        return _CursorProxy(cursor, self._service._record_query, after_first_fetch)

    def set_session(self, **kwargs: Any) -> None:
        self._service.last_session_settings = dict(kwargs)
        self._connection.set_session(**kwargs)


class NativeArchiveDatabaseService:
    """Test-only direct Unix-socket adapter; it never accepts a database URL."""

    uses_owned_connections = True

    def __init__(
        self,
        database: NativePostgresDatabase,
        *,
        after_first_fetch: Callable[[], None] | None = None,
    ) -> None:
        self.database = database
        self.after_first_fetch = after_first_fetch
        self.executed_queries: list[str] = []
        self.last_session_settings: dict[str, Any] = {}
        self.rollback_performed = False
        self.transaction_status_after_rollback: int | None = None
        self.last_error_type: str | None = None

    @contextmanager
    def get_connection(self, *, connect_timeout: int | None = None) -> Generator[Any, None, None]:
        connection = self.database.reader_connection(timeout=connect_timeout or 5)
        try:
            yield _ConnectionProxy(connection, self)
            connection.commit()
        except BaseException as exc:
            connection.rollback()
            self.rollback_performed = True
            self.transaction_status_after_rollback = connection.get_transaction_status()
            self.last_error_type = type(exc).__name__
            raise
        finally:
            connection.close()

    def get_cursor(self, connection: Any) -> _CursorProxy:
        return connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    def _record_query(self, query: str) -> None:
        if len(self.executed_queries) < 64:
            self.executed_queries.append(query)


def canonical_measurement_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize a native row to the archive's documented JSON timestamp/value form."""
    normalized = dict(row)
    for field in ("timestamp_utc", "created_at"):
        timestamp = normalized[field]
        if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
            raise AssertionError(f"native {field} was not a timezone-aware datetime")
        normalized[field] = timestamp.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    normalized["value"] = float(normalized["value"])
    return {field: normalized[field] for field in MEASUREMENT_FIELDS}
