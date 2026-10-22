#!/usr/bin/env python3
"""Command-line entry point for the canonical database migration runner."""

# ruff: noqa: T201

from __future__ import annotations

import sys

from waittime.services.database import DatabaseService
from waittime.services.migration_runner import (
    LEGACY_DUPLICATE_ADOPTION_MIGRATIONS,
    MIGRATIONS_DIR,
    SAFE_DUPLICATE_ERROR_CODES,
    MigrationChecksumMismatchError,
    MigrationError,
    MigrationResult,
    MigrationStatus,
    adopt_legacy_migration,
    allows_legacy_duplicate_adoption,
    apply_migration_file,
    ensure_schema_migrations,
    is_safe_duplicate_error,
    migration_checksum,
    migration_files,
    record_migration,
    recorded_checksum,
    require_matching_checksum,
    run_migrations,
)

__all__ = [
    "LEGACY_DUPLICATE_ADOPTION_MIGRATIONS",
    "MIGRATIONS_DIR",
    "SAFE_DUPLICATE_ERROR_CODES",
    "MigrationChecksumMismatchError",
    "MigrationError",
    "MigrationResult",
    "MigrationStatus",
    "adopt_legacy_migration",
    "allows_legacy_duplicate_adoption",
    "apply_migration_file",
    "ensure_schema_migrations",
    "is_safe_duplicate_error",
    "migration_checksum",
    "migration_files",
    "record_migration",
    "recorded_checksum",
    "require_matching_checksum",
    "run_migrations",
]


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
