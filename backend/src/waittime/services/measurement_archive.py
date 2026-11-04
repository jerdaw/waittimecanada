"""Private, opt-in measurement archive writer and offline verifier.

This module is not called by the public exporter, cleanup command, scheduler,
or any application route. A generated archive contains complete stored
measurement rows and must be treated as sensitive. Export requires an
explicit retention/access policy reference; this check records those values
but does not authenticate approval or enforce expiry.

The offline verifier checks artifact integrity and a canonical parse/serialize
round trip. It is not an independent PostgreSQL restore or a purge receipt.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
import tempfile
import time
import uuid
from collections.abc import Iterable, Iterator, Mapping
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg2.extras

from waittime.services.database import DatabaseService

ARCHIVE_FORMAT = "waittime-measurement-archive"
ARCHIVE_VERSION = 1
ARCHIVE_FILE = "measurements.jsonl"
MANIFEST_FILE = "manifest.json"
DEFAULT_FETCH_BATCH_SIZE = 1_000
MAX_FETCH_BATCH_SIZE = 10_000
DEFAULT_MAX_SNAPSHOT_SECONDS = 600
MAX_SNAPSHOT_SECONDS = 600
ARCHIVE_CONNECT_TIMEOUT_SECONDS = 10
STATEMENT_TIMEOUT_MS = 120_000
STATEMENT_TIMEOUT_GUARD_MS = 100
IDLE_TRANSACTION_TIMEOUT = "30000ms"
ARCHIVE_DIRECTORY_MODE = 0o700
ARCHIVE_FILE_MODE = 0o600

MEASUREMENT_FIELDS = (
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
    "is_anomaly",
    "anomaly_reason",
    "patients_waiting",
    "patients_in_treatment",
    "total_treatment_spaces",
    "created_at",
)

# PostgreSQL catalog signatures for the current migrations. Physical column
# order is deliberately excluded; the archive's explicit SELECT owns output order.
MEASUREMENT_COLUMN_SCHEMA: dict[str, tuple[str, int, str, bool]] = {
    "id": ("int8", -1, "b", True),
    "hospital_id": ("text", -1, "b", True),
    "timestamp_utc": ("timestamptz", -1, "b", True),
    "value": ("float8", -1, "b", True),
    "metric_family": ("metric_family_enum", -1, "e", True),
    "start_event": ("start_event_enum", -1, "e", True),
    "end_event": ("end_event_enum", -1, "e", True),
    "statistic_type": ("statistic_type_enum", -1, "e", True),
    "patient_scope": ("patient_scope_enum", -1, "e", True),
    "source_id": ("text", -1, "b", True),
    "raw_payload_hash": ("bpchar", 68, "b", True),
    "raw_payload_snippet": ("text", -1, "b", False),
    "parser_version": ("text", -1, "b", True),
    "is_anomaly": ("bool", -1, "b", True),
    "anomaly_reason": ("text", -1, "b", False),
    "patients_waiting": ("int4", -1, "b", False),
    "patients_in_treatment": ("int4", -1, "b", False),
    "total_treatment_spaces": ("int4", -1, "b", False),
    "created_at": ("timestamptz", -1, "b", True),
}

MEASUREMENT_QUERY = """
SELECT id, hospital_id, timestamp_utc, value,
       metric_family, start_event, end_event, statistic_type, patient_scope,
       source_id, raw_payload_hash, raw_payload_snippet, parser_version,
       is_anomaly, anomaly_reason,
       patients_waiting, patients_in_treatment, total_treatment_spaces,
       created_at
FROM measurements
ORDER BY id ASC
"""
MEASUREMENT_SCHEMA_QUERY = """
SELECT a.attname AS column_name,
       t.typname AS type_name,
       a.atttypmod AS type_modifier,
       t.typtype AS type_kind,
       a.attnotnull AS not_null
FROM pg_attribute AS a
JOIN pg_type AS t ON t.oid = a.atttypid
WHERE a.attrelid = 'measurements'::regclass
  AND a.attnum > 0
  AND NOT a.attisdropped
ORDER BY a.attnum
"""

_REQUIRED_STRINGS = (
    "hospital_id",
    "metric_family",
    "start_event",
    "end_event",
    "statistic_type",
    "patient_scope",
    "source_id",
    "raw_payload_hash",
    "parser_version",
)
_OPTIONAL_STRINGS = ("raw_payload_snippet", "anomaly_reason")
_OPTIONAL_NONNEGATIVE_INTS = (
    "patients_waiting",
    "patients_in_treatment",
    "total_treatment_spaces",
)
_UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class MeasurementArchiveError(RuntimeError):
    """Raised when an archive cannot be safely created or verified."""


class MeasurementArchiveValidationError(MeasurementArchiveError):
    """Raised when the archive shape, permissions, or content is invalid."""


@dataclass(frozen=True)
class ArchiveUsePolicy:
    """Required policy references for a private archive; not proof of approval."""

    policy_reference: str
    access_control_reference: str
    expires_at_utc: datetime


@dataclass(frozen=True)
class ArchiveVerification:
    """Sanitized verification result; contains no measurement values."""

    row_count: int
    first_measurement_id: int | None
    last_measurement_id: int | None
    artifact_sha256: str
    manifest_sha256: str
    snapshot_id: str
    offline_readback_verified: bool


def _utc_datetime(value: datetime, *, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise MeasurementArchiveValidationError(f"{field} must be timezone-aware")
    return value.astimezone(UTC)


def _timestamp_text(value: datetime, *, field: str) -> str:
    return _utc_datetime(value, field=field).strftime(_UTC_FORMAT)


def _timestamp_value(value: Any, *, field: str) -> str:
    if not isinstance(value, datetime):
        raise MeasurementArchiveValidationError(f"{field} must be a datetime")
    return _timestamp_text(value, field=field)


def _serialize_measurement_row(row: Mapping[str, Any]) -> dict[str, Any]:
    """Validate and serialize every currently stored measurements column."""
    if set(row) != set(MEASUREMENT_FIELDS):
        raise MeasurementArchiveValidationError(
            "measurement row columns do not match archive schema"
        )

    measurement_id = row["id"]
    if (
        isinstance(measurement_id, bool)
        or not isinstance(measurement_id, int)
        or measurement_id < 1
    ):
        raise MeasurementArchiveValidationError("measurement id is invalid")

    normalized: dict[str, Any] = {
        "id": measurement_id,
        "hospital_id": row["hospital_id"],
        "timestamp_utc": _timestamp_value(row["timestamp_utc"], field="timestamp_utc"),
    }

    value = row["value"]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MeasurementArchiveValidationError("measurement value is invalid")
    normalized["value"] = float(value)
    if not math.isfinite(normalized["value"]):
        raise MeasurementArchiveValidationError("measurement value is non-finite")

    for field in _REQUIRED_STRINGS:
        field_value = row[field]
        if not isinstance(field_value, str) or not field_value:
            raise MeasurementArchiveValidationError(f"{field} is missing or invalid")
        normalized[field] = field_value

    for field in _OPTIONAL_STRINGS:
        field_value = row[field]
        if field_value is not None and not isinstance(field_value, str):
            raise MeasurementArchiveValidationError(f"{field} is invalid")
        normalized[field] = field_value

    is_anomaly = row["is_anomaly"]
    if not isinstance(is_anomaly, bool):
        raise MeasurementArchiveValidationError("is_anomaly is invalid")
    normalized["is_anomaly"] = is_anomaly

    for field in _OPTIONAL_NONNEGATIVE_INTS:
        field_value = row[field]
        if field_value is not None and (
            isinstance(field_value, bool) or not isinstance(field_value, int) or field_value < 0
        ):
            raise MeasurementArchiveValidationError(f"{field} is invalid")
        normalized[field] = field_value

    normalized["created_at"] = _timestamp_value(row["created_at"], field="created_at")
    return normalized


def _decode_measurement_row(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != set(MEASUREMENT_FIELDS):
        raise MeasurementArchiveValidationError("archived row columns do not match archive schema")
    restored = dict(value)
    for field in ("timestamp_utc", "created_at"):
        timestamp_text = restored[field]
        if not isinstance(timestamp_text, str):
            raise MeasurementArchiveValidationError(f"archived {field} is invalid")
        try:
            restored[field] = datetime.strptime(timestamp_text, _UTC_FORMAT).replace(tzinfo=UTC)
        except ValueError as exc:
            raise MeasurementArchiveValidationError(f"archived {field} is invalid") from exc
    return _serialize_measurement_row(restored)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise MeasurementArchiveValidationError(
            "archive contains an unsupported JSON value"
        ) from exc


def _validate_policy(policy: ArchiveUsePolicy, exported_at_utc: datetime) -> dict[str, str]:
    if not policy.policy_reference.strip() or not policy.access_control_reference.strip():
        raise MeasurementArchiveValidationError("archive policy references are required")
    expires_at = _utc_datetime(policy.expires_at_utc, field="archive expiry")
    exported_at = _utc_datetime(exported_at_utc, field="export timestamp")
    if expires_at <= exported_at:
        raise MeasurementArchiveValidationError("archive expiry must follow export time")
    return {
        "policy_reference": policy.policy_reference.strip(),
        "access_control_reference": policy.access_control_reference.strip(),
        "expires_at_utc": _timestamp_text(expires_at, field="archive expiry"),
    }


def _manifest_bytes(manifest: dict[str, Any]) -> bytes:
    return _canonical_json_bytes(manifest) + b"\n"


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_private_file(path: Path, content: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, ARCHIVE_FILE_MODE)
    try:
        os.fchmod(descriptor, ARCHIVE_FILE_MODE)
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(content)
            stream.flush()
            os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_archive_contents(
    rows: Iterable[Mapping[str, Any]],
    staging_directory: Path,
    *,
    snapshot_id: str,
    exported_at_utc: datetime,
    policy: ArchiveUsePolicy,
    deadline: float | None,
) -> dict[str, Any]:
    if not snapshot_id or not isinstance(snapshot_id, str):
        raise MeasurementArchiveValidationError("database snapshot identifier is missing")
    exported_at = _utc_datetime(exported_at_utc, field="export timestamp")
    policy_values = _validate_policy(policy, exported_at)

    artifact_path = staging_directory / ARCHIVE_FILE
    artifact_hash = hashlib.sha256()
    row_hash = hashlib.sha256()
    row_count = 0
    first_id: int | None = None
    last_id: int | None = None
    previous_id = 0

    descriptor = os.open(artifact_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, ARCHIVE_FILE_MODE)
    try:
        os.fchmod(descriptor, ARCHIVE_FILE_MODE)
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            for raw_row in rows:
                if deadline is not None and time.monotonic() > deadline:
                    raise MeasurementArchiveError("archive snapshot exceeded its time budget")
                row = _serialize_measurement_row(raw_row)
                measurement_id = row["id"]
                if measurement_id <= previous_id:
                    raise MeasurementArchiveValidationError(
                        "measurement rows are not in strictly increasing id order"
                    )
                previous_id = measurement_id
                first_id = measurement_id if first_id is None else first_id
                last_id = measurement_id
                line = _canonical_json_bytes(row) + b"\n"
                stream.write(line)
                artifact_hash.update(line)
                row_hash.update(line)
                row_count += 1
            stream.flush()
            os.fsync(descriptor)
    finally:
        os.close(descriptor)

    artifact_sha256 = artifact_hash.hexdigest()
    manifest = {
        "archive_format": ARCHIVE_FORMAT,
        "archive_version": ARCHIVE_VERSION,
        "measurement_fields": list(MEASUREMENT_FIELDS),
        "row_count": row_count,
        "first_measurement_id": first_id,
        "last_measurement_id": last_id,
        "artifact_file": ARCHIVE_FILE,
        "artifact_sha256": artifact_sha256,
        "measurement_rows_sha256": row_hash.hexdigest(),
        "exported_at_utc": _timestamp_text(exported_at, field="export timestamp"),
        "snapshot": {
            "id": snapshot_id,
            "isolation_level": "repeatable read",
            "read_only": True,
        },
        "policy": policy_values,
    }
    _write_private_file(staging_directory / MANIFEST_FILE, _manifest_bytes(manifest))
    _fsync_directory(staging_directory)
    return manifest


def _reserve_archive_paths(destination: Path) -> tuple[Path, Path]:
    if not destination.name or destination.name in {".", ".."}:
        raise MeasurementArchiveValidationError("archive destination must name a new directory")
    try:
        parent = destination.parent.resolve(strict=True)
    except OSError as exc:
        raise MeasurementArchiveError("archive destination parent is unavailable") from exc
    if not parent.is_dir():
        raise MeasurementArchiveError("archive destination parent is not a directory")

    final_directory = parent / destination.name
    final_directory.mkdir(mode=ARCHIVE_DIRECTORY_MODE, exist_ok=False)
    staging_directory: Path | None = None
    try:
        os.chmod(final_directory, ARCHIVE_DIRECTORY_MODE)
        staging_directory = Path(
            tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=parent)
        )
        os.chmod(staging_directory, ARCHIVE_DIRECTORY_MODE)
    except BaseException:
        if staging_directory is not None:
            with suppress(OSError):
                staging_directory.rmdir()
        with suppress(OSError):
            final_directory.rmdir()
        raise
    return final_directory, staging_directory


def _publish_archive(staging_directory: Path, final_directory: Path) -> None:
    os.replace(staging_directory / ARCHIVE_FILE, final_directory / ARCHIVE_FILE)
    # The manifest is the completion marker and is deliberately published last.
    os.replace(staging_directory / MANIFEST_FILE, final_directory / MANIFEST_FILE)
    _fsync_directory(final_directory)
    staging_directory.rmdir()
    _fsync_directory(final_directory.parent)


def _cleanup_archive_paths(final_directory: Path, staging_directory: Path) -> None:
    for directory in (staging_directory, final_directory):
        for filename in (ARCHIVE_FILE, MANIFEST_FILE):
            with suppress(FileNotFoundError):
                (directory / filename).unlink()
        with suppress(FileNotFoundError, OSError):
            directory.rmdir()


def build_measurement_archive(
    rows: Iterable[Mapping[str, Any]],
    destination: Path,
    *,
    snapshot_id: str,
    exported_at_utc: datetime,
    policy: ArchiveUsePolicy,
) -> ArchiveVerification:
    """Build an archive from a supplied row stream (used with synthetic fixtures)."""
    final_directory, staging_directory = _reserve_archive_paths(Path(destination))
    try:
        _write_archive_contents(
            rows,
            staging_directory,
            snapshot_id=snapshot_id,
            exported_at_utc=exported_at_utc,
            policy=policy,
            deadline=None,
        )
        verify_measurement_archive(staging_directory)
        _publish_archive(staging_directory, final_directory)
        _fsync_directory(final_directory.parent)
        return verify_measurement_archive(final_directory)
    except BaseException:
        _cleanup_archive_paths(final_directory, staging_directory)
        raise


def _set_statement_timeout_for_deadline(conn: Any, deadline: float) -> None:
    remaining_seconds = deadline - time.monotonic()
    if remaining_seconds <= 0:
        raise MeasurementArchiveError("archive snapshot exceeded its time budget")
    remaining_ms = max(
        1,
        int(remaining_seconds * 1_000) - STATEMENT_TIMEOUT_GUARD_MS,
    )
    timeout_ms = min(STATEMENT_TIMEOUT_MS, remaining_ms)
    with conn.cursor() as timeout_cursor:
        timeout_cursor.execute(
            "SELECT set_config('statement_timeout', %s, true)",
            (f"{timeout_ms}ms",),
        )
        timeout_cursor.fetchone()


def _cursor_rows(
    conn: Any,
    cursor: Any,
    *,
    batch_size: int,
    deadline: float,
) -> Iterator[Mapping[str, Any]]:
    while True:
        if time.monotonic() > deadline:
            raise MeasurementArchiveError("archive snapshot exceeded its time budget")
        _set_statement_timeout_for_deadline(conn, deadline)
        batch = cursor.fetchmany(batch_size)
        if time.monotonic() > deadline:
            raise MeasurementArchiveError("archive snapshot exceeded its time budget")
        if not batch:
            return
        yield from batch


def export_measurement_archive(
    database: DatabaseService,
    destination: Path,
    *,
    policy: ArchiveUsePolicy,
    fetch_batch_size: int = DEFAULT_FETCH_BATCH_SIZE,
    max_snapshot_seconds: int = DEFAULT_MAX_SNAPSHOT_SECONDS,
) -> ArchiveVerification:
    """Stream every stored measurement under one private read-only PG snapshot.

    This function is intentionally not wired to any routine command or cleanup
    path. Callers must obtain the archive policy and actual-restore approvals
    separately; the supplied policy references are recorded, not authenticated.
    Borrowed connections are rejected so the writer cannot publish while a
    caller-owned transaction is still open.
    """
    if not 1 <= fetch_batch_size <= MAX_FETCH_BATCH_SIZE:
        raise ValueError(f"fetch_batch_size must be between 1 and {MAX_FETCH_BATCH_SIZE}")
    if not 1 <= max_snapshot_seconds <= MAX_SNAPSHOT_SECONDS:
        raise ValueError(f"max_snapshot_seconds must be between 1 and {MAX_SNAPSHOT_SECONDS}")
    if not database.uses_owned_connections:
        raise MeasurementArchiveError(
            "archive export requires a fresh DatabaseService-owned connection"
        )

    final_directory, staging_directory = _reserve_archive_paths(Path(destination))
    exported_at = datetime.now(UTC)
    deadline = time.monotonic() + max_snapshot_seconds
    try:
        with database.get_connection(
            connect_timeout=min(ARCHIVE_CONNECT_TIMEOUT_SECONDS, max_snapshot_seconds)
        ) as conn:
            conn.set_session(isolation_level="REPEATABLE READ", readonly=True)
            with database.get_cursor(conn) as control_cursor:
                _set_statement_timeout_for_deadline(conn, deadline)
                control_cursor.execute(
                    "SELECT set_config('idle_in_transaction_session_timeout', %s, true)",
                    (IDLE_TRANSACTION_TIMEOUT,),
                )
                _set_statement_timeout_for_deadline(conn, deadline)
                control_cursor.execute("SHOW transaction_read_only")
                read_only = control_cursor.fetchone()
                _set_statement_timeout_for_deadline(conn, deadline)
                control_cursor.execute("SHOW transaction_isolation")
                isolation = control_cursor.fetchone()
                if read_only is None or read_only["transaction_read_only"] != "on":
                    raise MeasurementArchiveError(
                        "database read-only transaction was not established"
                    )
                if isolation is None or isolation["transaction_isolation"] != "repeatable read":
                    raise MeasurementArchiveError("database snapshot isolation was not established")
                _set_statement_timeout_for_deadline(conn, deadline)
                control_cursor.execute(MEASUREMENT_SCHEMA_QUERY)
                schema_rows = control_cursor.fetchall()
                schema: dict[str, tuple[str, int, str, bool]] = {}
                for row in schema_rows:
                    column_name = row["column_name"]
                    if column_name in schema:
                        raise MeasurementArchiveError(
                            "database measurement schema does not match archive format"
                        )
                    schema[column_name] = (
                        row["type_name"],
                        row["type_modifier"],
                        row["type_kind"],
                        row["not_null"],
                    )
                if schema != MEASUREMENT_COLUMN_SCHEMA:
                    raise MeasurementArchiveError(
                        "database measurement schema does not match archive format"
                    )
                _set_statement_timeout_for_deadline(conn, deadline)
                control_cursor.execute("SELECT txid_current_snapshot()::text AS snapshot_id")
                snapshot = control_cursor.fetchone()
                if snapshot is None or not snapshot["snapshot_id"]:
                    raise MeasurementArchiveError("database snapshot identifier is unavailable")
                snapshot_id = str(snapshot["snapshot_id"])

            cursor_name = f"wtc_measurement_archive_{uuid.uuid4().hex}"
            with conn.cursor(
                name=cursor_name,
                cursor_factory=psycopg2.extras.RealDictCursor,
            ) as measurement_cursor:
                measurement_cursor.itersize = fetch_batch_size
                _set_statement_timeout_for_deadline(conn, deadline)
                measurement_cursor.execute(MEASUREMENT_QUERY)
                _write_archive_contents(
                    _cursor_rows(
                        conn,
                        measurement_cursor,
                        batch_size=fetch_batch_size,
                        deadline=deadline,
                    ),
                    staging_directory,
                    snapshot_id=snapshot_id,
                    exported_at_utc=exported_at,
                    policy=policy,
                    deadline=deadline,
                )
        # DatabaseService commits after the read-only context exits. Do not
        # publish a complete manifest until that transaction has ended cleanly.
        verify_measurement_archive(staging_directory)
        _publish_archive(staging_directory, final_directory)
        _fsync_directory(final_directory.parent)
        return verify_measurement_archive(final_directory)
    except psycopg2.Error:
        _cleanup_archive_paths(final_directory, staging_directory)
        raise MeasurementArchiveError(
            "database archive read failed; no complete archive was published"
        ) from None
    except BaseException:
        _cleanup_archive_paths(final_directory, staging_directory)
        raise


def _read_private_file(path: Path, *, max_bytes: int | None = None) -> bytes:
    try:
        file_stat = path.lstat()
    except OSError as exc:
        raise MeasurementArchiveValidationError("archive file is unavailable") from exc
    if not stat.S_ISREG(file_stat.st_mode) or stat.S_ISLNK(file_stat.st_mode):
        raise MeasurementArchiveValidationError("archive entries must be regular files")
    if stat.S_IMODE(file_stat.st_mode) & 0o077:
        raise MeasurementArchiveValidationError("archive file permissions are not private")
    if max_bytes is not None and file_stat.st_size > max_bytes:
        raise MeasurementArchiveValidationError("archive manifest exceeds its size limit")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise MeasurementArchiveValidationError("archive file could not be read") from exc


def verify_measurement_archive(archive_directory: Path) -> ArchiveVerification:
    """Verify checksums, full row shape, order, private modes, and offline read-back."""
    directory = Path(archive_directory)
    try:
        directory_stat = directory.lstat()
    except OSError as exc:
        raise MeasurementArchiveValidationError("archive directory is unavailable") from exc
    if not stat.S_ISDIR(directory_stat.st_mode) or stat.S_ISLNK(directory_stat.st_mode):
        raise MeasurementArchiveValidationError("archive path must be a real directory")
    if stat.S_IMODE(directory_stat.st_mode) & 0o077:
        raise MeasurementArchiveValidationError("archive directory permissions are not private")
    try:
        entries = {entry.name for entry in directory.iterdir()}
    except OSError as exc:
        raise MeasurementArchiveValidationError("archive directory could not be listed") from exc
    if entries != {ARCHIVE_FILE, MANIFEST_FILE}:
        raise MeasurementArchiveValidationError(
            "archive is incomplete or contains unexpected files"
        )

    manifest_bytes = _read_private_file(directory / MANIFEST_FILE, max_bytes=65_536)
    try:
        manifest = json.loads(manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MeasurementArchiveValidationError("archive manifest is not valid JSON") from exc
    if not isinstance(manifest, dict) or _manifest_bytes(manifest) != manifest_bytes:
        raise MeasurementArchiveValidationError("archive manifest is not canonical")

    expected_manifest_fields = {
        "archive_format",
        "archive_version",
        "measurement_fields",
        "row_count",
        "first_measurement_id",
        "last_measurement_id",
        "artifact_file",
        "artifact_sha256",
        "measurement_rows_sha256",
        "exported_at_utc",
        "snapshot",
        "policy",
    }
    if set(manifest) != expected_manifest_fields:
        raise MeasurementArchiveValidationError("archive manifest fields are unsupported")
    if (
        manifest["archive_format"] != ARCHIVE_FORMAT
        or manifest["archive_version"] != ARCHIVE_VERSION
        or manifest["measurement_fields"] != list(MEASUREMENT_FIELDS)
        or manifest["artifact_file"] != ARCHIVE_FILE
    ):
        raise MeasurementArchiveValidationError("archive format or field projection is unsupported")

    snapshot = manifest["snapshot"]
    policy = manifest["policy"]
    if (
        not isinstance(snapshot, dict)
        or set(snapshot) != {"id", "isolation_level", "read_only"}
        or not isinstance(snapshot["id"], str)
        or snapshot["isolation_level"] != "repeatable read"
        or snapshot["read_only"] is not True
    ):
        raise MeasurementArchiveValidationError("archive snapshot metadata is invalid")
    if (
        not isinstance(policy, dict)
        or set(policy) != {"policy_reference", "access_control_reference", "expires_at_utc"}
        or not all(isinstance(policy[key], str) and policy[key] for key in policy)
    ):
        raise MeasurementArchiveValidationError("archive policy metadata is invalid")

    exported_at = manifest["exported_at_utc"]
    expires_at = policy["expires_at_utc"]
    try:
        exported_time = datetime.strptime(exported_at, _UTC_FORMAT).replace(tzinfo=UTC)
        expires_time = datetime.strptime(expires_at, _UTC_FORMAT).replace(tzinfo=UTC)
    except (TypeError, ValueError) as exc:
        raise MeasurementArchiveValidationError("archive timestamps are invalid") from exc
    if expires_time <= exported_time:
        raise MeasurementArchiveValidationError("archive expiry does not follow export time")

    expected_artifact_sha256 = manifest["artifact_sha256"]
    expected_rows_sha256 = manifest["measurement_rows_sha256"]
    if not isinstance(expected_artifact_sha256, str) or not _SHA256_RE.fullmatch(
        expected_artifact_sha256
    ):
        raise MeasurementArchiveValidationError("archive artifact checksum is invalid")
    if not isinstance(expected_rows_sha256, str) or not _SHA256_RE.fullmatch(expected_rows_sha256):
        raise MeasurementArchiveValidationError("archive row checksum is invalid")

    artifact_path = directory / ARCHIVE_FILE
    try:
        artifact_stat = artifact_path.lstat()
    except OSError as exc:
        raise MeasurementArchiveValidationError("archive artifact is unavailable") from exc
    if not stat.S_ISREG(artifact_stat.st_mode) or stat.S_ISLNK(artifact_stat.st_mode):
        raise MeasurementArchiveValidationError("archive artifact must be a regular file")
    if stat.S_IMODE(artifact_stat.st_mode) & 0o077:
        raise MeasurementArchiveValidationError("archive artifact permissions are not private")

    artifact_hash = hashlib.sha256()
    rows_hash = hashlib.sha256()
    row_count = 0
    first_id: int | None = None
    last_id: int | None = None
    previous_id = 0
    try:
        with artifact_path.open("rb") as stream:
            for line in stream:
                if not line.endswith(b"\n") or line == b"\n":
                    raise MeasurementArchiveValidationError("archive has a truncated or blank row")
                try:
                    decoded = json.loads(line)
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise MeasurementArchiveValidationError(
                        "archive row is not valid JSON"
                    ) from exc
                row = _decode_measurement_row(decoded)
                if _canonical_json_bytes(row) + b"\n" != line:
                    raise MeasurementArchiveValidationError("archive row is not canonical")
                measurement_id = row["id"]
                if measurement_id <= previous_id:
                    raise MeasurementArchiveValidationError(
                        "archive measurement ids are not ordered"
                    )
                previous_id = measurement_id
                first_id = measurement_id if first_id is None else first_id
                last_id = measurement_id
                artifact_hash.update(line)
                rows_hash.update(line)
                row_count += 1
    except OSError as exc:
        raise MeasurementArchiveValidationError("archive artifact could not be read") from exc

    artifact_sha256 = artifact_hash.hexdigest()
    rows_sha256 = rows_hash.hexdigest()
    if artifact_sha256 != expected_artifact_sha256 or rows_sha256 != expected_rows_sha256:
        raise MeasurementArchiveValidationError("archive content checksum does not match manifest")
    if manifest["row_count"] != row_count:
        raise MeasurementArchiveValidationError("archive row count does not match manifest")
    if manifest["first_measurement_id"] != first_id or manifest["last_measurement_id"] != last_id:
        raise MeasurementArchiveValidationError("archive id bounds do not match manifest")

    return ArchiveVerification(
        row_count=row_count,
        first_measurement_id=first_id,
        last_measurement_id=last_id,
        artifact_sha256=artifact_sha256,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        snapshot_id=snapshot["id"],
        offline_readback_verified=True,
    )
