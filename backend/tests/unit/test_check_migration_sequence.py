import importlib.util
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "check_migration_sequence.py"
SPEC = importlib.util.spec_from_file_location("check_migration_sequence", SCRIPT_PATH)
assert SPEC is not None
assert SPEC.loader is not None
check_migration_sequence = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_migration_sequence)


def _touch(directory: Path, *names: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name in names:
        (directory / name).write_text("-- test migration\n", encoding="utf-8")


def _write_readme(
    path: Path,
    migration_names: list[str],
    *,
    executable_count: int | None = None,
    next_number: int | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    executable_count = (
        executable_count
        if executable_count is not None
        else sum(name.endswith(".sql") for name in migration_names)
    )
    next_number = (
        next_number
        if next_number is not None
        else (max(int(name[:3]) for name in migration_names) + 1)
    )
    lines = [
        "# Database Migrations",
        "",
        f"Found {executable_count} migration files:",
        "",
        f"The next migration number is `{next_number:03d}`.",
        "",
        *(f"#### {name}" for name in migration_names),
    ]
    if extra_lines:
        lines.extend(["", *extra_lines])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_repository_migrations_pass_sequence_check() -> None:
    errors = check_migration_sequence.validate_migrations()

    assert errors == []


def test_complete_migration_documentation_passes(tmp_path: Path) -> None:
    names = ["001_create_tables.sql", "002_deferred_policy.sql.skip"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names)

    assert check_migration_sequence.validate_migration_documentation(tmp_path, readme) == []


def test_missing_migration_readme_is_rejected(tmp_path: Path) -> None:
    _touch(tmp_path, "001_create_tables.sql")
    readme = tmp_path / "README.md"

    assert check_migration_sequence.validate_migration_documentation(tmp_path, readme) == [
        f"migration README not found: {readme}"
    ]


def test_missing_migration_heading_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql", "002_add_index.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names[:1], executable_count=2, next_number=3)

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README is missing migration heading: 002_add_index.sql" in errors


def test_stale_migration_heading_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, [*names, "002_removed_table.sql"], executable_count=1, next_number=2)

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README has migration heading without a file: 002_removed_table.sql" in errors


def test_duplicate_migration_heading_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names, extra_lines=["#### 001_create_tables.sql"])

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README has duplicate migration heading: 001_create_tables.sql" in errors


def test_missing_migration_number_is_rejected(tmp_path: Path) -> None:
    _touch(tmp_path, "001_create_tables.sql", "003_add_index.sql")

    errors = check_migration_sequence.validate_migrations(tmp_path)

    assert errors == [
        "migration sequence has missing reserved numbers: 002. "
        "Use .sql.skip for intentionally skipped numbers."
    ]


def test_sql_skip_file_reserves_migration_number(tmp_path: Path) -> None:
    _touch(
        tmp_path,
        "001_create_tables.sql",
        "002_deferred_policy.sql.skip",
        "003_add_index.sql",
    )

    errors = check_migration_sequence.validate_migrations(tmp_path)

    assert errors == []


def test_new_duplicate_executable_prefix_is_rejected(tmp_path: Path) -> None:
    _touch(tmp_path, "001_create_tables.sql", "001_add_index.sql")

    errors = check_migration_sequence.validate_migrations(tmp_path)

    assert errors == [
        "001: duplicate executable migration prefix in 001_add_index.sql, 001_create_tables.sql"
    ]


def test_existing_020_duplicate_exception_is_documented(tmp_path: Path) -> None:
    _touch(
        tmp_path,
        *(f"{number:03d}_placeholder.sql" for number in range(1, 20)),
        "020_add_public_health_system_metrics.sql",
        "020_sync_active_source_definitions.sql",
    )

    errors = check_migration_sequence.validate_migrations(tmp_path)

    assert errors == []
