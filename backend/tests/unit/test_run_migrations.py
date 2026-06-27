"""Unit tests for the database migration runner."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "run_migrations.py"
SPEC = importlib.util.spec_from_file_location("run_migrations", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
run_migrations = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_migrations
SPEC.loader.exec_module(run_migrations)


class DuplicateTableError(Exception):
    """Fake PostgreSQL duplicate-table error."""

    pgcode = "42P07"


class FakeCursor:
    """Small cursor fake for ledger-oriented migration tests."""

    def __init__(self, conn: FakeConnection) -> None:
        self.conn = conn
        self.closed = False
        self._row: tuple[str] | None = None

    def execute(self, query: str, params: tuple[str, ...] | None = None) -> None:
        query_text = str(query).strip()
        self.conn.executed.append((query_text, params))

        if query_text.startswith("CREATE TABLE IF NOT EXISTS schema_migrations"):
            self.conn.schema_table_ensured = True
            return

        if query_text.startswith("SELECT checksum_sha256"):
            assert params is not None
            checksum = self.conn.records.get(params[0])
            self._row = (checksum,) if checksum is not None else None
            return

        if query_text.startswith("INSERT INTO schema_migrations"):
            assert params is not None
            self.conn.records.setdefault(params[0], params[1])
            return

        self.conn.migration_sql.append(query_text)
        if self.conn.migration_error is not None:
            raise self.conn.migration_error

    def fetchone(self) -> tuple[str] | None:
        return self._row

    def close(self) -> None:
        self.closed = True


class FakeConnection:
    """Small connection fake for migration runner tests."""

    def __init__(self, migration_error: Exception | None = None) -> None:
        self.records: dict[str, str] = {}
        self.executed: list[tuple[str, tuple[str, ...] | None]] = []
        self.migration_sql: list[str] = []
        self.migration_error = migration_error
        self.rollback_count = 0
        self.schema_table_ensured = False

    def cursor(self) -> FakeCursor:
        return FakeCursor(self)

    def rollback(self) -> None:
        self.rollback_count += 1


def write_migration(tmp_path: Path, name: str, sql: str) -> Path:
    migration = tmp_path / name
    migration.write_text(sql, encoding="utf-8")
    return migration


def test_apply_migration_records_success(tmp_path: Path) -> None:
    migration = write_migration(tmp_path, "001_test.sql", "SELECT 1;")
    conn = FakeConnection()

    result = run_migrations.apply_migration_file(conn, migration)

    assert result.status == "applied"
    assert conn.records["001_test.sql"] == run_migrations.migration_checksum("SELECT 1;")
    assert conn.migration_sql == ["SELECT 1;"]


def test_apply_migration_skips_matching_checksum(tmp_path: Path) -> None:
    migration = write_migration(tmp_path, "001_test.sql", "SELECT 1;")
    checksum = run_migrations.migration_checksum("SELECT 1;")
    conn = FakeConnection()
    conn.records["001_test.sql"] = checksum

    result = run_migrations.apply_migration_file(conn, migration)

    assert result.status == "skipped"
    assert conn.migration_sql == []


def test_apply_migration_rejects_changed_applied_file(tmp_path: Path) -> None:
    migration = write_migration(tmp_path, "001_test.sql", "SELECT 1;")
    conn = FakeConnection()
    conn.records["001_test.sql"] = "0" * 64

    with pytest.raises(run_migrations.MigrationChecksumMismatchError, match="already applied"):
        run_migrations.apply_migration_file(conn, migration)


def test_safe_duplicate_error_records_legacy_adoption(tmp_path: Path) -> None:
    migration = write_migration(tmp_path, "001_test.sql", "CREATE TABLE test_table (id int);")
    conn = FakeConnection(migration_error=DuplicateTableError("relation already exists"))

    result = run_migrations.apply_migration_file(conn, migration)

    assert result.status == "adopted"
    assert conn.rollback_count == 1
    assert conn.schema_table_ensured is True
    assert conn.records["001_test.sql"] == run_migrations.migration_checksum(
        "CREATE TABLE test_table (id int);"
    )
