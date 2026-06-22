#!/usr/bin/env python3
"""Validate migration file names and sequence numbers."""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
MIGRATION_NAME_RE = re.compile(r"^(?P<prefix>\d{3})_[a-z0-9][a-z0-9_]*\.sql(?P<skip>\.skip)?$")

# Two 020 migrations were created before this guard existed. They may already be
# applied in deployed databases, so preserve the filenames and reject only new
# duplicate prefixes.
LEGACY_DUPLICATE_PREFIXES = {
    "020": frozenset(
        {
            "020_add_public_health_system_metrics.sql",
            "020_sync_active_source_definitions.sql",
        }
    )
}


def migration_files(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    """Return executable and intentionally skipped migration files."""
    return sorted(
        path
        for path in migrations_dir.iterdir()
        if path.is_file() and (path.name.endswith(".sql") or path.name.endswith(".sql.skip"))
    )


def validate_migrations(migrations_dir: Path = MIGRATIONS_DIR) -> list[str]:
    """Return validation errors for migration names and sequence numbers."""
    errors: list[str] = []
    numbers: set[int] = set()
    executable_names_by_prefix: dict[str, list[str]] = defaultdict(list)

    for path in migration_files(migrations_dir):
        match = MIGRATION_NAME_RE.fullmatch(path.name)
        if match is None:
            errors.append(
                f"{path.name}: expected NNN_descriptive_name.sql or NNN_descriptive_name.sql.skip"
            )
            continue

        prefix = match.group("prefix")
        numbers.add(int(prefix))
        if match.group("skip") is None:
            executable_names_by_prefix[prefix].append(path.name)

    for prefix, names in sorted(executable_names_by_prefix.items()):
        if len(names) <= 1:
            continue

        allowed_names = LEGACY_DUPLICATE_PREFIXES.get(prefix)
        if allowed_names is not None and frozenset(names) == allowed_names:
            continue

        errors.append(
            f"{prefix}: duplicate executable migration prefix in {', '.join(sorted(names))}"
        )

    if numbers:
        expected = set(range(min(numbers), max(numbers) + 1))
        missing = sorted(expected - numbers)
        if missing:
            formatted = ", ".join(f"{number:03d}" for number in missing)
            errors.append(
                f"migration sequence has missing reserved numbers: {formatted}. "
                "Use .sql.skip for intentionally skipped numbers."
            )

    return errors


def main() -> int:
    errors = validate_migrations()
    if errors:
        print("Migration sequence check failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Migration sequence check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
