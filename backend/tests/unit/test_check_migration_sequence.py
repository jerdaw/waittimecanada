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


def test_repository_migrations_pass_sequence_check() -> None:
    errors = check_migration_sequence.validate_migrations()

    assert errors == []


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
