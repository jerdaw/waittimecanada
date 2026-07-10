#!/usr/bin/env python3
"""Validate migration file names and sequence numbers."""

from __future__ import annotations

import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
MIGRATIONS_README = MIGRATIONS_DIR / "README.md"
MIGRATION_NAME_RE = re.compile(r"^(?P<prefix>\d{3})_[a-z0-9][a-z0-9_]*\.sql(?P<skip>\.skip)?$")
MIGRATION_HEADING_RE = re.compile(
    r"^#### (?P<name>\d{3}_[a-z0-9][a-z0-9_]*\.sql(?:\.skip)?)$",
    re.MULTILINE,
)
EXECUTABLE_COUNT_RE = re.compile(
    r"^Found (?P<count>\d+) migration files:$",
    re.MULTILINE,
)
NEXT_MIGRATION_RE = re.compile(
    r"^The next migration number is `(?P<number>\d{3})`\.$",
    re.MULTILINE,
)
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD)\b")

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


def validate_migration_documentation(
    migrations_dir: Path = MIGRATIONS_DIR,
    readme_path: Path = MIGRATIONS_README,
) -> list[str]:
    """Return disk-derived migration README consistency errors."""
    try:
        readme = readme_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"migration README not found: {readme_path}"]
    except OSError as exc:
        return [f"could not read migration README {readme_path}: {exc}"]

    names = [path.name for path in migration_files(migrations_dir)]
    expected_names = set(names)
    heading_counts = Counter(MIGRATION_HEADING_RE.findall(readme))
    documented_names = set(heading_counts)
    errors: list[str] = []

    for name in sorted(expected_names - documented_names):
        errors.append(f"README is missing migration heading: {name}")
    for name in sorted(documented_names - expected_names):
        errors.append(f"README has migration heading without a file: {name}")
    for name, count in sorted(heading_counts.items()):
        if count > 1:
            errors.append(f"README has duplicate migration heading: {name}")

    executable_count = sum(name.endswith(".sql") for name in names)
    count_matches = list(EXECUTABLE_COUNT_RE.finditer(readme))
    if not count_matches:
        errors.append("README is missing the canonical executable migration count")
    elif len(count_matches) > 1:
        errors.append(
            "README must contain exactly one canonical executable migration count; "
            f"found {len(count_matches)}"
        )
    else:
        documented_count = int(count_matches[0].group("count"))
        if documented_count != executable_count:
            errors.append(
                f"README executable migration count is {documented_count}; "
                f"expected {executable_count}"
            )

    valid_prefixes = [
        int(match.group("prefix"))
        for name in names
        if (match := MIGRATION_NAME_RE.fullmatch(name)) is not None
    ]
    if valid_prefixes:
        expected_next = max(valid_prefixes) + 1
        next_matches = list(NEXT_MIGRATION_RE.finditer(readme))
        if not next_matches:
            errors.append("README is missing the canonical next migration statement")
        elif len(next_matches) > 1:
            errors.append(
                "README must contain exactly one canonical next migration statement; "
                f"found {len(next_matches)}"
            )
        else:
            documented_next = int(next_matches[0].group("number"))
            if documented_next != expected_next:
                errors.append(
                    f"README next migration number is {documented_next:03d}; "
                    f"expected {expected_next:03d}"
                )

    for line_number, line in enumerate(readme.splitlines(), start=1):
        for match in PLACEHOLDER_RE.finditer(line):
            errors.append(
                f"README contains unresolved placeholder {match.group(0)!r} at line {line_number}"
            )

    return errors


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
    errors = [*validate_migrations(), *validate_migration_documentation()]
    if errors:
        print("Migration validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Migration validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
