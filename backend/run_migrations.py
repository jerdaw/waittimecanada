#!/usr/bin/env python3
"""Run database migrations with a checksum ledger."""

# ruff: noqa: T201

from __future__ import annotations

import hashlib
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from waittime.services import DatabaseService

SAFE_DUPLICATE_ERROR_CODES = {"42710", "42P07", "42723"}
MIGRATIONS_DIR = Path(__file__).parent / "migrations"

MigrationStatus = Literal["applied", "skipped", "adopted"]


class MigrationError(RuntimeError):
    """Base exception for migration runner failures."""


class MigrationChecksumMismatchError(MigrationError):
    """Raised when an applied migration file has changed."""


@dataclass(frozen=True)
class MigrationResult:
    """Outcome for one migration file."""

    filename: str
    checksum: str
    status: MigrationStatus
    detail: str = ""


def migration_files(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    """Return executable migration files in deterministic order."""
    return sorted(migrations_dir.glob("*.sql"))


def migration_checksum(sql_text: str) -> str:
    """Return the SHA256 checksum used by the migration ledger."""
    return hashlib.sha256(sql_text.encode("utf-8")).hexdigest()


def is_safe_duplicate_error(exc: Exception) -> bool:
    """Return True when migration error indicates the object already exists."""
    code = getattr(exc, "pgcode", None)
    if code in SAFE_DUPLICATE_ERROR_CODES:
        return True
    message = str(exc).lower()
    return "already exists" in message or "duplicate object" in message


def ensure_schema_migrations(conn: Any) -> None:
    """Create the runner-owned migration ledger table if needed."""
    cur = conn.cursor()
    try:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename TEXT PRIMARY KEY,
                checksum_sha256 TEXT NOT NULL,
                applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                CONSTRAINT schema_migrations_checksum_sha256_format
                    CHECK (checksum_sha256 ~ '^[0-9a-f]{64}$')
            )
            """
        )
    finally:
        cur.close()


def recorded_checksum(cur: Any, filename: str) -> str | None:
    """Return the recorded checksum for a migration filename, if present."""
    cur.execute(
        "SELECT checksum_sha256 FROM schema_migrations WHERE filename = %s",
        (filename,),
    )
    row = cur.fetchone()
    if row is None:
        return None
    if isinstance(row, dict):
        value = row["checksum_sha256"]
    else:
        value = row[0]
    return str(value)


def record_migration(cur: Any, filename: str, checksum: str) -> None:
    """Insert a successful migration into the ledger."""
    cur.execute(
        """
        INSERT INTO schema_migrations (filename, checksum_sha256)
        VALUES (%s, %s)
        ON CONFLICT (filename) DO NOTHING
        """,
        (filename, checksum),
    )


def require_matching_checksum(recorded: str | None, filename: str, checksum: str) -> None:
    """Reject a migration file that differs from the applied ledger entry."""
    if recorded is not None and recorded != checksum:
        raise MigrationChecksumMismatchError(
            f"{filename} was already applied with checksum {recorded}, "
            f"but the file now has checksum {checksum}. "
            "Create a new migration instead of editing applied history."
        )


def adopt_legacy_migration(conn: Any, filename: str, checksum: str) -> None:
    """Record a migration that already existed before the ledger was introduced."""
    conn.rollback()
    ensure_schema_migrations(conn)

    cur = conn.cursor()
    try:
        existing_checksum = recorded_checksum(cur, filename)
        require_matching_checksum(existing_checksum, filename, checksum)
        if existing_checksum is None:
            record_migration(cur, filename, checksum)
    finally:
        cur.close()


def apply_migration_file(conn: Any, migration_file: Path) -> MigrationResult:
    """Apply one migration file and update the ledger."""
    filename = migration_file.name
    sql_text = migration_file.read_text(encoding="utf-8")
    checksum = migration_checksum(sql_text)

    cur = conn.cursor()
    try:
        existing_checksum = recorded_checksum(cur, filename)
        require_matching_checksum(existing_checksum, filename, checksum)
        if existing_checksum == checksum:
            return MigrationResult(filename=filename, checksum=checksum, status="skipped")

        try:
            cur.execute(sql_text)
        except Exception as exc:
            cur.close()
            if not is_safe_duplicate_error(exc):
                raise
            adopt_legacy_migration(conn, filename, checksum)
            return MigrationResult(
                filename=filename,
                checksum=checksum,
                status="adopted",
                detail=str(exc),
            )

        record_migration(cur, filename, checksum)
        return MigrationResult(filename=filename, checksum=checksum, status="applied")
    finally:
        if not getattr(cur, "closed", False):
            cur.close()


def run_migrations(
    db: DatabaseService,
    migration_paths: Sequence[Path] | None = None,
) -> list[MigrationResult]:
    """Apply all migration files and return their outcomes."""
    files = list(migration_paths) if migration_paths is not None else migration_files()
    if not files:
        raise MigrationError(f"No migration files found in {MIGRATIONS_DIR}")

    with db.get_connection() as conn:
        ensure_schema_migrations(conn)

    results: list[MigrationResult] = []
    for migration_file in files:
        with db.get_connection() as conn:
            results.append(apply_migration_file(conn, migration_file))

    return results


def main() -> int:
    """CLI entry point."""
    files = migration_files()
    if not files:
        print(f"No migration files found in {MIGRATIONS_DIR}")
        return 1

    print(f"Found {len(files)} migration files:\n")
    db = DatabaseService()

    try:
        for result in run_migrations(db, files):
            print(f"Running: {result.filename}")
            if result.status == "applied":
                print("  Success\n")
            elif result.status == "skipped":
                print("  Skipped (already applied)\n")
            else:
                print(f"  Adopted legacy migration (already applied): {result.detail}\n")
    except Exception as exc:
        print(f"Migration failed: {exc}\n")
        print("Stopping migrations. You may need to rollback manually.")
        return 1

    print("All migrations completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
