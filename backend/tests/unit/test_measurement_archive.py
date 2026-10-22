"""Synthetic tests for private measurement archive creation and read-back."""

from __future__ import annotations

import copy
import json
import re
import stat
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg2
import pytest

from waittime.cli import measurement_archive as archive_cli
from waittime.cli.measurement_archive import main as archive_cli_main
from waittime.services.database import DatabaseService
from waittime.services.measurement_archive import (
    ARCHIVE_FILE,
    MANIFEST_FILE,
    MAX_FETCH_BATCH_SIZE,
    MEASUREMENT_COLUMN_SCHEMA,
    MEASUREMENT_FIELDS,
    MEASUREMENT_QUERY,
    MEASUREMENT_SCHEMA_QUERY,
    ArchiveUsePolicy,
    MeasurementArchiveError,
    MeasurementArchiveValidationError,
    build_measurement_archive,
    export_measurement_archive,
    verify_measurement_archive,
)

EXPORTED_AT = datetime(2026, 10, 18, 12, 0, tzinfo=UTC)
EXPIRY = datetime(2027, 10, 18, 12, 0, tzinfo=UTC)
POLICY = ArchiveUsePolicy(
    policy_reference="synthetic-policy-01",
    access_control_reference="synthetic-private-store-01",
    expires_at_utc=EXPIRY,
)


def _schema_from_migrations() -> dict[str, tuple[str, int, str, bool]]:
    """Derive measurement catalog order/types from the real migration SQL."""
    migration_dir = Path(__file__).resolve().parents[2] / "migrations"
    base_sql = (migration_dir / "002_create_tables.sql").read_text(encoding="utf-8")
    table_match = re.search(
        r"CREATE TABLE measurements\s*\((.*?)\n\);",
        base_sql,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert table_match is not None

    sql_types = {
        "BIGSERIAL": ("int8", -1, "b"),
        "TEXT": ("text", -1, "b"),
        "TIMESTAMPTZ": ("timestamptz", -1, "b"),
        "DOUBLE PRECISION": ("float8", -1, "b"),
        "CHAR(64)": ("bpchar", 68, "b"),
        "metric_family_enum": ("metric_family_enum", -1, "e"),
        "start_event_enum": ("start_event_enum", -1, "e"),
        "end_event_enum": ("end_event_enum", -1, "e"),
        "statistic_type_enum": ("statistic_type_enum", -1, "e"),
        "patient_scope_enum": ("patient_scope_enum", -1, "e"),
        "BOOLEAN": ("bool", -1, "b"),
        "INTEGER": ("int4", -1, "b"),
    }
    columns: dict[str, tuple[str, int, str, bool]] = {}

    def add_column(name: str, sql_type: str, modifiers: str) -> None:
        normalized_type = sql_type.upper() if sql_type.upper() in sql_types else sql_type
        if normalized_type not in sql_types:
            raise AssertionError(f"unhandled measurement migration type: {sql_type}")
        type_name, type_modifier, type_kind = sql_types[normalized_type]
        not_null = "NOT NULL" in modifiers.upper() or "PRIMARY KEY" in modifiers.upper()
        assert name not in columns
        columns[name] = (type_name, type_modifier, type_kind, not_null)

    column_pattern = re.compile(
        r"^([a-z][a-z0-9_]*)\s+"
        r"(BIGSERIAL|DOUBLE PRECISION|TIMESTAMPTZ|TEXT|CHAR\(\d+\)|[a-z][a-z0-9_]*)"
        r"(?=\s|,|$)",
        flags=re.IGNORECASE,
    )
    for line in table_match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        match = column_pattern.match(stripped)
        if match:
            add_column(match.group(1), match.group(2), stripped[match.end() :])

    add_column_pattern = re.compile(
        r"ADD COLUMN(?: IF NOT EXISTS)?\s+([a-z][a-z0-9_]*)\s+"
        r"(BOOLEAN|TEXT|INTEGER)(?=\s|,|;|$)",
        flags=re.IGNORECASE,
    )
    for migration_name in (
        "008_add_anomaly_columns.sql",
        "011_add_occupancy_columns.sql",
    ):
        for line in (migration_dir / migration_name).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("--"):
                continue
            match = add_column_pattern.search(stripped)
            if match:
                add_column(match.group(1), match.group(2), stripped[match.end() :])
    return columns


def _migration_schema_rows() -> list[dict[str, Any]]:
    schema = _schema_from_migrations()
    return [
        {
            "column_name": name,
            "type_name": signature[0],
            "type_modifier": signature[1],
            "type_kind": signature[2],
            "not_null": signature[3],
        }
        for name, signature in schema.items()
    ]


def _measurement_row(measurement_id: int, **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": measurement_id,
        "hospital_id": "ca-on-synthetic",
        "timestamp_utc": datetime(2026, 10, 18, 11, 0, tzinfo=UTC),
        "value": 123.5,
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "MEAN",
        "patient_scope": "ALL",
        "source_id": "ontario-health",
        "raw_payload_hash": "a" * 64,
        "raw_payload_snippet": "synthetic source excerpt",
        "parser_version": "synthetic-v1",
        "is_anomaly": False,
        "anomaly_reason": None,
        "patients_waiting": 4,
        "patients_in_treatment": 5,
        "total_treatment_spaces": 8,
        "created_at": datetime(2026, 10, 18, 11, 1, tzinfo=UTC),
    }
    row.update(overrides)
    return row


def _build(rows: list[dict[str, Any]], destination: Path):
    return build_measurement_archive(
        rows,
        destination,
        snapshot_id="synthetic-snapshot-01",
        exported_at_utc=EXPORTED_AT,
        policy=POLICY,
    )


def test_archive_round_trip_contains_all_stored_measurement_columns(tmp_path: Path) -> None:
    destination = tmp_path / "private-archive"
    rows = [
        _measurement_row(1),
        _measurement_row(
            2,
            patient_scope="FUTURE_SCOPE_LABEL",
            raw_payload_snippet=None,
            is_anomaly=True,
            anomaly_reason="synthetic flag",
            patients_waiting=None,
        ),
    ]

    result = _build(rows, destination)

    assert result.row_count == 2
    assert result.first_measurement_id == 1
    assert result.last_measurement_id == 2
    assert result.offline_readback_verified is True
    assert set(MEASUREMENT_FIELDS) == set(rows[0])
    manifest = json.loads((destination / MANIFEST_FILE).read_bytes())
    archived_rows = [
        json.loads(line) for line in (destination / ARCHIVE_FILE).read_bytes().splitlines()
    ]
    assert manifest["snapshot"] == {
        "id": "synthetic-snapshot-01",
        "isolation_level": "repeatable read",
        "read_only": True,
    }
    assert archived_rows[1]["patient_scope"] == "FUTURE_SCOPE_LABEL"
    assert archived_rows[1]["raw_payload_snippet"] is None
    assert archived_rows[1]["total_treatment_spaces"] == 8
    assert result == verify_measurement_archive(destination)


def test_manifest_and_artifact_are_deterministic_for_fixed_snapshot(tmp_path: Path) -> None:
    rows = [_measurement_row(1), _measurement_row(2, value=0.0)]
    first = tmp_path / "first"
    second = tmp_path / "second"

    _build(rows, first)
    _build(rows, second)

    assert (first / ARCHIVE_FILE).read_bytes() == (second / ARCHIVE_FILE).read_bytes()
    assert (first / MANIFEST_FILE).read_bytes() == (second / MANIFEST_FILE).read_bytes()


@pytest.mark.parametrize("damage", ["truncate", "modify", "append"])
def test_verifier_rejects_truncated_or_tampered_artifact(tmp_path: Path, damage: str) -> None:
    destination = tmp_path / "archive"
    _build([_measurement_row(1), _measurement_row(2)], destination)
    artifact_path = destination / ARCHIVE_FILE
    content = artifact_path.read_bytes()
    if damage == "truncate":
        content = content[:-7]
    elif damage == "modify":
        content = content.replace(b"123.5", b"321.5", 1)
    else:
        content += b"{}\n"
    artifact_path.write_bytes(content)

    with pytest.raises(MeasurementArchiveValidationError):
        verify_measurement_archive(destination)


def test_verifier_rejects_manifest_changes_and_unexpected_partial_files(tmp_path: Path) -> None:
    destination = tmp_path / "archive"
    _build([_measurement_row(1)], destination)
    manifest_path = destination / MANIFEST_FILE
    manifest = json.loads(manifest_path.read_bytes())
    manifest["row_count"] = 2
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(MeasurementArchiveValidationError):
        verify_measurement_archive(destination)

    manifest_path.unlink()
    (destination / ".manifest.json.partial").write_text("partial", encoding="utf-8")
    with pytest.raises(MeasurementArchiveValidationError):
        verify_measurement_archive(destination)


def test_build_failure_cleans_only_its_new_paths(tmp_path: Path) -> None:
    destination = tmp_path / "failed-archive"

    def broken_rows():
        yield _measurement_row(1)
        raise OSError("synthetic stream failure")

    with pytest.raises(OSError, match="synthetic stream failure"):
        _build(broken_rows(), destination)

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_invalid_row_and_existing_destination_fail_closed(tmp_path: Path) -> None:
    invalid_row = _measurement_row(1)
    del invalid_row["patients_in_treatment"]
    destination = tmp_path / "invalid-archive"
    with pytest.raises(MeasurementArchiveValidationError):
        _build([invalid_row], destination)
    assert not destination.exists()

    existing = tmp_path / "existing"
    existing.mkdir(mode=0o700)
    marker = existing / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError):
        _build([_measurement_row(1)], existing)
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_archive_files_and_directory_are_private(tmp_path: Path) -> None:
    destination = tmp_path / "private"
    _build([_measurement_row(1)], destination)

    assert stat.S_IMODE(destination.stat().st_mode) == 0o700
    assert stat.S_IMODE((destination / ARCHIVE_FILE).stat().st_mode) == 0o600
    assert stat.S_IMODE((destination / MANIFEST_FILE).stat().st_mode) == 0o600


class _SyntheticCursor:
    def __init__(self, connection, *, name=None, cursor_factory=None) -> None:
        self.connection = connection
        self.name = name
        self.cursor_factory = cursor_factory
        self.itersize = None
        self.rows = []
        self.index = 0
        self.fetch_calls = 0
        self.one = None
        self.closed = False

    def execute(self, query, params=None) -> None:
        self.connection.events.append(("execute", " ".join(query.split()), params))
        normalized = " ".join(query.split())
        if normalized == "SHOW transaction_read_only":
            self.one = {"transaction_read_only": "on"}
        elif normalized == "SHOW transaction_isolation":
            self.one = {"transaction_isolation": "repeatable read"}
        elif "txid_current_snapshot" in normalized:
            self.connection.snapshot_captured = True
            self.one = {"snapshot_id": "synthetic:1:2:1"}
        elif normalized == " ".join(MEASUREMENT_SCHEMA_QUERY.split()):
            self.rows = copy.deepcopy(self.connection.schema_rows)
        elif normalized == " ".join(MEASUREMENT_QUERY.split()):
            assert self.connection.snapshot_captured
            self.rows = copy.deepcopy(self.connection.rows_at_snapshot)
            # Simulate a concurrent insert after the transaction snapshot.
            self.connection.live_rows.append(_measurement_row(999))
            assert self.name is not None
        else:
            assert "set_config" in normalized

    def fetchone(self):
        result, self.one = self.one, None
        return result

    def fetchall(self):
        result, self.rows = self.rows, []
        return result

    def fetchmany(self, size):
        self.fetch_calls += 1
        self.connection.events.append(("fetchmany", size))
        if self.connection.fail_after_fetches == self.fetch_calls - 1:
            raise psycopg2.OperationalError("synthetic database fetch failure")
        result = self.rows[self.index : self.index + size]
        self.index += len(result)
        return result

    def close(self) -> None:
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        self.close()


class _SyntheticConnection:
    def __init__(self, rows, *, fail_after_fetches=None, schema_rows=None) -> None:
        self.rows_at_snapshot = copy.deepcopy(rows)
        self.live_rows = copy.deepcopy(rows)
        self.schema_rows = copy.deepcopy(
            _migration_schema_rows() if schema_rows is None else schema_rows
        )
        self.events = []
        self.session_options = None
        self.snapshot_captured = False
        self.fail_after_fetches = fail_after_fetches
        self.commit_count = 0
        self.rollback_count = 0
        self.named_cursor_count = 0

    def set_session(self, **kwargs) -> None:
        self.session_options = kwargs
        self.events.append(("set_session", kwargs))

    def cursor(self, name=None, cursor_factory=None):
        if name is not None:
            self.named_cursor_count += 1
        return _SyntheticCursor(self, name=name, cursor_factory=cursor_factory)


class _SyntheticDatabase:
    def __init__(self, connection) -> None:
        self.connection = connection
        self.uses_owned_connections = True
        self.connect_timeout = None

    @contextmanager
    def get_connection(self, *, connect_timeout=None):
        self.connect_timeout = connect_timeout
        try:
            yield self.connection
        except BaseException:
            self.connection.rollback_count += 1
            raise
        else:
            self.connection.commit_count += 1

    def get_cursor(self, conn):
        return conn.cursor()


def test_database_export_uses_one_read_only_snapshot_and_server_cursor(tmp_path: Path) -> None:
    connection = _SyntheticConnection([_measurement_row(1)])
    database = _SyntheticDatabase(connection)
    destination = tmp_path / "database-export"

    result = export_measurement_archive(
        database,
        destination,
        policy=POLICY,
        fetch_batch_size=1,
    )

    assert connection.session_options == {
        "isolation_level": "REPEATABLE READ",
        "readonly": True,
    }
    assert database.connect_timeout == 10
    assert connection.commit_count == 1
    assert connection.rollback_count == 0
    assert connection.named_cursor_count == 1
    assert [
        json.loads(line)["id"] for line in (destination / ARCHIVE_FILE).read_bytes().splitlines()
    ] == [1]
    assert len(connection.live_rows) == 2  # synthetic concurrent row was outside the snapshot
    assert result.snapshot_id == "synthetic:1:2:1"
    fetch_indexes = [
        index for index, event in enumerate(connection.events) if event[0] == "fetchmany"
    ]
    assert len(fetch_indexes) == 2  # one populated batch and the terminal empty batch
    for index in fetch_indexes:
        timeout_event = connection.events[index - 1]
        assert timeout_event[0] == "execute"
        assert "set_config('statement_timeout'" in timeout_event[1]
        assert 0 < int(timeout_event[2][0][:-2]) <= 120_000
    snapshot_query_index = next(
        index
        for index, event in enumerate(connection.events)
        if "txid_current_snapshot" in str(event)
    )
    data_query_index = next(
        index
        for index, event in enumerate(connection.events)
        if event[0] == "execute" and event[1] == " ".join(MEASUREMENT_QUERY.split())
    )
    schema_query_index = next(
        index
        for index, event in enumerate(connection.events)
        if event[0] == "execute" and event[1] == " ".join(MEASUREMENT_SCHEMA_QUERY.split())
    )
    assert schema_query_index < snapshot_query_index < data_query_index


def test_migration_order_and_catalog_types_match_projection_without_order_dependency() -> None:
    migration_schema = _schema_from_migrations()
    assert list(migration_schema) == [
        "id",
        "hospital_id",
        "timestamp_utc",
        "value",
        "metric_family",
        "start_event",
        "end_event",
        "statistic_type",
        "patient_scope",
        "source_id",
        "raw_payload_hash",
        "raw_payload_snippet",
        "parser_version",
        "created_at",
        "is_anomaly",
        "anomaly_reason",
        "patients_waiting",
        "patients_in_treatment",
        "total_treatment_spaces",
    ]
    assert migration_schema == MEASUREMENT_COLUMN_SCHEMA
    assert tuple(migration_schema) != MEASUREMENT_FIELDS


def test_measurement_query_select_order_matches_canonical_archive_fields() -> None:
    projection_match = re.search(
        r"SELECT\s+(.*?)\s+FROM\s+measurements",
        MEASUREMENT_QUERY,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert projection_match is not None
    selected_columns = tuple(column.strip() for column in projection_match.group(1).split(","))
    assert selected_columns == MEASUREMENT_FIELDS


@pytest.mark.parametrize("drift", ["missing", "unexpected", "duplicate", "type", "nullability"])
def test_database_export_fails_closed_on_schema_drift(tmp_path: Path, drift: str) -> None:
    schema_rows = _migration_schema_rows()
    if drift == "missing":
        schema_rows = schema_rows[:-1]
    elif drift == "unexpected":
        schema_rows.append(
            {
                "column_name": "untracked_column",
                "type_name": "text",
                "type_modifier": -1,
                "type_kind": "b",
                "not_null": False,
            }
        )
    elif drift == "duplicate":
        schema_rows.append(schema_rows[0].copy())
    else:
        if drift == "type":
            schema_rows[3]["type_name"] = "numeric"
        else:
            schema_rows[0]["not_null"] = False

    connection = _SyntheticConnection([_measurement_row(1)], schema_rows=schema_rows)
    database = _SyntheticDatabase(connection)
    destination = tmp_path / "schema-drift"

    with pytest.raises(MeasurementArchiveError, match="schema does not match"):
        export_measurement_archive(database, destination, policy=POLICY)

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert not destination.exists()
    assert not any(
        event[0] == "execute" and event[1] == " ".join(MEASUREMENT_QUERY.split())
        for event in connection.events
    )


def test_database_fetch_failure_rolls_back_and_removes_partial_archive(tmp_path: Path) -> None:
    connection = _SyntheticConnection(
        [_measurement_row(1), _measurement_row(2)], fail_after_fetches=1
    )
    database = _SyntheticDatabase(connection)
    destination = tmp_path / "failed-database-export"

    with pytest.raises(MeasurementArchiveError, match="no complete archive was published"):
        export_measurement_archive(
            database,
            destination,
            policy=POLICY,
            fetch_batch_size=1,
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []


def test_offline_cli_labels_readback_not_actual_postgresql_restore(tmp_path: Path, capsys) -> None:
    destination = tmp_path / "cli-archive"
    _build([_measurement_row(1)], destination)

    assert archive_cli_main(["restore-check", str(destination)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["check"] == "offline_readback"
    assert output["actual_postgresql_restore"] is False
    assert "123.5" not in json.dumps(output)


def _export_cli_args(destination: Path) -> list[str]:
    return [
        "export",
        "--destination",
        str(destination),
        "--policy-reference",
        "synthetic-policy-01",
        "--access-control-reference",
        "synthetic-private-store-01",
        "--expires-at-utc",
        "2099-10-18T12:00:00Z",
        "--confirm-export",
    ]


def test_export_cli_uses_existing_writer_and_emits_bounded_summary(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload_marker = "synthetic-payload-must-not-reach-output"
    connection = _SyntheticConnection(
        [_measurement_row(1, raw_payload_snippet=payload_marker, value=9876.5)]
    )
    database = _SyntheticDatabase(connection)
    monkeypatch.setattr(archive_cli, "DatabaseService", lambda: database)
    destination = tmp_path / "cli-export"

    assert archive_cli_main(_export_cli_args(destination)) == 0

    captured = capsys.readouterr()
    output = json.loads(captured.out)
    assert captured.err == ""
    assert output["status"] == "exported"
    assert output["row_count"] == 1
    assert output["offline_readback_verified"] is True
    assert output["actual_postgresql_restore"] is False
    assert len(captured.out) < 512
    assert payload_marker not in captured.out
    assert "9876.5" not in captured.out
    assert "synthetic-policy-01" not in captured.out
    assert "cli-export" not in captured.out
    assert (destination / ARCHIVE_FILE).exists()
    assert verify_measurement_archive(destination).row_count == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0


@pytest.mark.parametrize(
    "missing_option",
    [
        "--destination",
        "--policy-reference",
        "--access-control-reference",
        "--expires-at-utc",
        "--confirm-export",
    ],
)
def test_export_cli_missing_required_gate_never_constructs_database(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    missing_option: str,
) -> None:
    args = _export_cli_args(tmp_path / "missing-gate")
    if missing_option in {
        "--destination",
        "--policy-reference",
        "--access-control-reference",
        "--expires-at-utc",
    }:
        option_index = args.index(missing_option)
        del args[option_index : option_index + 2]
    else:
        args.remove(missing_option)

    def unexpected_database_construction():
        pytest.fail("database service was constructed before CLI gates passed")

    monkeypatch.setattr(archive_cli, "DatabaseService", unexpected_database_construction)
    with pytest.raises(SystemExit) as exc_info:
        archive_cli_main(args)

    assert exc_info.value.code == 2
    assert "synthetic-policy-01" not in capsys.readouterr().err
    assert not (tmp_path / "missing-gate").exists()


@pytest.mark.parametrize(
    "updates",
    [
        {"policy-reference": ""},
        {"access-control-reference": "   "},
        {"expires-at-utc": "2099-10-18T12:00:00"},
        {"expires-at-utc": "2000-10-18T12:00:00Z"},
    ],
)
def test_export_cli_invalid_policy_inputs_fail_before_database_or_paths(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    updates: dict[str, str],
) -> None:
    args = _export_cli_args(tmp_path / "invalid-policy")
    for option, value in updates.items():
        args[args.index(f"--{option}") + 1] = value

    def unexpected_database_construction():
        pytest.fail("database service was constructed before policy validation")

    monkeypatch.setattr(archive_cli, "DatabaseService", unexpected_database_construction)
    assert archive_cli_main(args) == 2

    assert json.loads(capsys.readouterr().err) == {
        "error": "invalid_export_options",
        "status": "failed",
    }
    assert not (tmp_path / "invalid-policy").exists()


@pytest.mark.parametrize("destination_kind", ["existing", "symlink"])
def test_export_cli_rejects_existing_or_symlink_destination_without_overwrite(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
    destination_kind: str,
) -> None:
    existing = tmp_path / "existing-destination"
    existing.mkdir()
    marker = existing / "keep.txt"
    marker.write_text("preserve", encoding="utf-8")
    destination = existing
    if destination_kind == "symlink":
        destination = tmp_path / "destination-link"
        destination.symlink_to(existing, target_is_directory=True)

    def unexpected_database_construction():
        pytest.fail("database service was constructed before destination validation")

    monkeypatch.setattr(archive_cli, "DatabaseService", unexpected_database_construction)
    args = _export_cli_args(destination)
    assert archive_cli_main(args) == 2

    assert json.loads(capsys.readouterr().err) == {
        "error": "invalid_export_options",
        "status": "failed",
    }
    assert marker.read_text(encoding="utf-8") == "preserve"


def test_export_cli_allows_resolved_parent_symlink_without_replacing_target(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    destination = linked_parent / "new-archive"
    connection = _SyntheticConnection([_measurement_row(1)])
    monkeypatch.setattr(archive_cli, "DatabaseService", lambda: _SyntheticDatabase(connection))

    assert archive_cli_main(_export_cli_args(destination)) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "exported"
    assert (real_parent / "new-archive" / ARCHIVE_FILE).exists()
    assert destination.is_dir()


def test_export_cli_redacts_unexpected_database_exception(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_error_text = "synthetic-database-error-marker-do-not-echo"
    monkeypatch.setattr(archive_cli, "DatabaseService", lambda: object())

    def fail_export(*_args: Any, **_kwargs: Any):
        raise RuntimeError(database_error_text)

    monkeypatch.setattr(archive_cli, "export_measurement_archive", fail_export)
    assert archive_cli_main(_export_cli_args(tmp_path / "redacted-failure")) == 2

    captured = capsys.readouterr()
    assert json.loads(captured.err) == {"error": "export_failed", "status": "failed"}
    assert database_error_text not in captured.err
    assert not (tmp_path / "redacted-failure").exists()


def test_export_cli_rejects_database_url_argument_without_echoing_it(
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    credential_text = "synthetic-credential-argument-marker-do-not-echo"

    def unexpected_database_construction():
        pytest.fail("unknown credential arguments must be rejected before database setup")

    monkeypatch.setattr(archive_cli, "DatabaseService", unexpected_database_construction)
    with pytest.raises(SystemExit) as exc_info:
        archive_cli_main(["export", "--database-url", credential_text])

    assert exc_info.value.code == 2
    assert credential_text not in capsys.readouterr().err


def test_offline_verify_command_remains_database_free(
    tmp_path: Path,
    capsys,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "offline-cli-archive"
    _build([_measurement_row(1)], destination)

    def unexpected_database_construction():
        pytest.fail("offline verification must not construct a database service")

    monkeypatch.setattr(archive_cli, "DatabaseService", unexpected_database_construction)
    assert archive_cli_main(["verify", str(destination)]) == 0

    output = json.loads(capsys.readouterr().out)
    assert output["check"] == "integrity"
    assert output["actual_postgresql_restore"] is False


def test_database_export_rejects_unsafe_batch_limits(tmp_path: Path) -> None:
    connection = _SyntheticConnection([])
    database = _SyntheticDatabase(connection)

    with pytest.raises(ValueError, match="fetch_batch_size"):
        export_measurement_archive(
            database,
            tmp_path / "unused",
            policy=POLICY,
            fetch_batch_size=MAX_FETCH_BATCH_SIZE + 1,
        )
    assert list(tmp_path.iterdir()) == []


def test_database_export_rejects_borrowed_connection_before_creating_paths(
    tmp_path: Path,
) -> None:
    database = DatabaseService(
        database_url="postgresql://synthetic.invalid/test",
        conn=_SyntheticConnection([]),
    )
    destination = tmp_path / "borrowed-connection"

    with pytest.raises(MeasurementArchiveError, match="fresh DatabaseService-owned"):
        export_measurement_archive(database, destination, policy=POLICY)

    assert not destination.exists()
    assert list(tmp_path.iterdir()) == []
