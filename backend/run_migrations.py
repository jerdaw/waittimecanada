#!/usr/bin/env python3
"""Run database migrations."""

import sys
from pathlib import Path

from waittime.services import DatabaseService

SAFE_DUPLICATE_ERROR_CODES = {"42710", "42P07", "42723"}


def is_safe_duplicate_error(exc: Exception) -> bool:
    """Return True when migration error indicates the object already exists."""
    code = getattr(exc, "pgcode", None)
    if code in SAFE_DUPLICATE_ERROR_CODES:
        return True
    message = str(exc).lower()
    return "already exists" in message or "duplicate object" in message

# Find migration files
MIGRATIONS_DIR = Path(__file__).parent / "migrations"
migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

if not migration_files:
    print(f"❌ No migration files found in {MIGRATIONS_DIR}")
    sys.exit(1)

print(f"Found {len(migration_files)} migration files:\n")

db = DatabaseService()

for migration_file in migration_files:
    print(f"Running: {migration_file.name}")

    try:
        sql = migration_file.read_text()

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)

        print(f"  ✓ Success\n")

    except Exception as e:
        if is_safe_duplicate_error(e):
            print(f"  ⚠ Skipped (already applied): {e}\n")
            continue
        print(f"  ❌ Failed: {e}\n")
        print("Stopping migrations. You may need to rollback manually.")
        sys.exit(1)

print("✅ All migrations completed successfully!")
