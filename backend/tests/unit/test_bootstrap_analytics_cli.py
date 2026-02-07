"""Tests for analytics bootstrap CLI."""

from pathlib import Path
from unittest.mock import Mock, patch

from waittime.cli.bootstrap_analytics import (
    _migration_files,
    apply_migrations,
    backfill_analytics_aggregates,
    main,
    seed_region_mappings,
)


def test_migration_files_sorted(tmp_path: Path) -> None:
    """Migration files should be returned in lexical order."""
    (tmp_path / "010.sql").write_text("-- ten", encoding="utf-8")
    (tmp_path / "002.sql").write_text("-- two", encoding="utf-8")
    (tmp_path / "001.sql").write_text("-- one", encoding="utf-8")

    files = _migration_files(tmp_path)

    assert [file.name for file in files] == ["001.sql", "002.sql", "010.sql"]


def test_apply_migrations_dry_run() -> None:
    """Dry run should not open DB connections."""
    mock_db = Mock()
    migration = Path("001_test.sql")

    with patch("waittime.cli.bootstrap_analytics._migration_files", return_value=[migration]):
        count = apply_migrations(mock_db, dry_run=True)

    assert count == 1
    mock_db.get_connection.assert_not_called()


def test_apply_migrations_executes_sql(tmp_path: Path) -> None:
    """Migrations should execute SQL via db cursor."""
    migration = tmp_path / "001_test.sql"
    migration.write_text("SELECT 1;", encoding="utf-8")

    mock_cursor = Mock()
    mock_cursor_ctx = Mock()
    mock_cursor_ctx.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor_ctx.__exit__ = Mock(return_value=False)

    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor_ctx

    mock_conn_ctx = Mock()
    mock_conn_ctx.__enter__ = Mock(return_value=mock_conn)
    mock_conn_ctx.__exit__ = Mock(return_value=False)

    mock_db = Mock()
    mock_db.get_connection.return_value = mock_conn_ctx

    with patch("waittime.cli.bootstrap_analytics._migration_files", return_value=[migration]):
        count = apply_migrations(mock_db, dry_run=False)

    assert count == 1
    mock_cursor.execute.assert_called_once_with("SELECT 1;")


def test_apply_migrations_skips_duplicate_error(tmp_path: Path) -> None:
    """Duplicate-object errors should be treated as already applied."""
    migration = tmp_path / "001_test.sql"
    migration.write_text("SELECT 1;", encoding="utf-8")

    duplicate_exc = Exception('relation "sources" already exists')
    setattr(duplicate_exc, "pgcode", "42P07")

    mock_cursor = Mock()
    mock_cursor.execute.side_effect = duplicate_exc
    mock_cursor_ctx = Mock()
    mock_cursor_ctx.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor_ctx.__exit__ = Mock(return_value=False)

    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor_ctx
    mock_conn_ctx = Mock()
    mock_conn_ctx.__enter__ = Mock(return_value=mock_conn)
    mock_conn_ctx.__exit__ = Mock(return_value=False)

    mock_db = Mock()
    mock_db.get_connection.return_value = mock_conn_ctx

    with patch("waittime.cli.bootstrap_analytics._migration_files", return_value=[migration]):
        count = apply_migrations(mock_db, dry_run=False)

    assert count == 1


def test_seed_region_mappings_delegates_to_seed_helpers(tmp_path: Path) -> None:
    """seed_region_mappings should load payload and call seed_regions."""
    mock_db = Mock()
    region_file = tmp_path / "regions.json"
    region_file.write_text("{}", encoding="utf-8")

    payload = {"province": "ON", "regions": [{"id": "r1"}]}

    with (
        patch("waittime.cli.bootstrap_analytics.load_regions_from_json", return_value=payload),
        patch("waittime.cli.bootstrap_analytics.seed_regions", return_value=(1, 2, 0)) as seed_mock,
    ):
        result = seed_region_mappings(mock_db, region_file=region_file, province="ON", dry_run=False)

    assert result == (1, 2, 0)
    seed_mock.assert_called_once_with(
        db=mock_db,
        province="ON",
        regions=payload["regions"],
        dry_run=False,
    )


def test_backfill_analytics_aggregates_delegates_to_service() -> None:
    """Aggregate backfill should call service with daily/weekly/monthly defaults."""
    mock_db = Mock()

    with patch("waittime.cli.bootstrap_analytics.AggregationService") as service_cls:
        service = service_cls.return_value
        service.backfill.return_value = {"daily": 1, "weekly": 2, "monthly": 3}

        counts = backfill_analytics_aggregates(mock_db, days=90, dry_run=True)

    assert counts == {"daily": 1, "weekly": 2, "monthly": 3}
    service.backfill.assert_called_once()
    call_kwargs = service.backfill.call_args.kwargs
    assert call_kwargs["period_types"] == ["daily", "weekly", "monthly"]
    assert call_kwargs["dry_run"] is True


def test_main_returns_error_for_invalid_days() -> None:
    """CLI should fail fast on invalid --days values."""
    with patch("sys.argv", ["bootstrap_analytics.py", "--days", "0"]):
        exit_code = main()

    assert exit_code == 1


def test_main_happy_path() -> None:
    """CLI should orchestrate all steps successfully."""
    with (
        patch("sys.argv", ["bootstrap_analytics.py", "--days", "120"]),
        patch("waittime.cli.bootstrap_analytics.DatabaseService"),
        patch("waittime.cli.bootstrap_analytics.apply_migrations", return_value=10) as migrations,
        patch("waittime.cli.bootstrap_analytics.seed_region_mappings", return_value=(4, 20, 0)) as seed,
        patch(
            "waittime.cli.bootstrap_analytics.backfill_analytics_aggregates",
            return_value={"daily": 5, "weekly": 2, "monthly": 1},
        ) as backfill,
    ):
        exit_code = main()

    assert exit_code == 0
    migrations.assert_called_once()
    seed.assert_called_once()
    backfill.assert_called_once()
