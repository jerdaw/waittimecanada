from unittest.mock import patch

import pytest

from waittime.cli.cleanup import main


@pytest.fixture
def mock_db_stats():
    return {
        "total_measurements": 1000,
        "oldest_measurement_age_days": 45,
        "newest_measurement_age_days": 0,
        "older_than_days_threshold": 30,
        "measurements_older_than_threshold": 200,
    }


@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_dry_run(mock_db, mock_db_stats):
    """Verify that dry run doesn't call cleanup_old_measurements."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.get_measurement_age_stats.return_value = mock_db_stats

    with patch("sys.argv", ["cleanup.py", "--dry-run"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.cleanup_old_measurements.assert_not_called()


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_execution_default_retention(mock_db, mock_aggregation, mock_db_stats):
    """Verify that default cleanup refreshes aggregates and deletes old rows."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.cleanup_old_measurements.return_value = 200
    mock_aggregation.return_value.backfill.return_value = {"daily": 1}

    with patch("sys.argv", ["cleanup.py"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.get_measurement_age_stats.assert_not_called()
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(
            retention_days=30,
            batch_size=5000,
            max_batches=None,
        )


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_execution_with_custom_retention(mock_db, mock_aggregation, mock_db_stats):
    """Verify that cleanup respects a custom retention window."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.cleanup_old_measurements.return_value = 200
    mock_aggregation.return_value.backfill.return_value = {"daily": 1}

    with patch("sys.argv", ["cleanup.py", "--retention-days", "60"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.get_measurement_age_stats.assert_not_called()
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(
            retention_days=60,
            batch_size=5000,
            max_batches=None,
        )


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_execution_uses_aggregation_backfill(mock_db, mock_aggregation, mock_db_stats):
    """Verify that cleanup refreshes recent daily aggregates before deletion."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.cleanup_old_measurements.return_value = 200
    mock_aggregation.return_value.backfill.return_value = {"daily": 1}

    with patch("sys.argv", ["cleanup.py"]):
        exit_code = main()
        assert exit_code == 0
        mock_aggregation.return_value.backfill.assert_called_once()


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_with_stats_collects_measurement_age_stats(
    mock_db, mock_aggregation, mock_db_stats
):
    """Verify that full-table stats are opt-in during non-dry-run maintenance."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.get_measurement_age_stats.return_value = mock_db_stats
    mock_db_instance.cleanup_old_measurements.return_value = 200
    mock_aggregation.return_value.backfill.return_value = {"daily": 1}

    with patch("sys.argv", ["cleanup.py", "--with-stats"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.get_measurement_age_stats.assert_called()
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(
            retention_days=30,
            batch_size=5000,
            max_batches=None,
        )


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_with_batch_controls(mock_db, mock_aggregation, mock_db_stats):
    """Verify that cleanup forwards batch-control flags to the database service."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.cleanup_old_measurements.return_value = 200
    mock_aggregation.return_value.backfill.return_value = {"daily": 1}

    with patch(
        "sys.argv",
        ["cleanup.py", "--delete-batch-size", "2500", "--max-delete-batches", "4"],
    ):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(
            retention_days=30,
            batch_size=2500,
            max_batches=4,
        )


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_can_skip_aggregate_refresh(mock_db, mock_aggregation, mock_db_stats):
    """Verify that skip flag bypasses aggregate backfill."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.cleanup_old_measurements.return_value = 200

    with patch("sys.argv", ["cleanup.py", "--skip-aggregate-refresh"]):
        exit_code = main()
        assert exit_code == 0
        mock_aggregation.return_value.backfill.assert_not_called()
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(
            retention_days=30,
            batch_size=5000,
            max_batches=None,
        )


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_handles_exception(mock_db, mock_aggregation):
    """Verify that exceptions return exit code 1."""
    mock_aggregation.return_value.backfill.side_effect = Exception("DB Error")

    with patch("sys.argv", ["cleanup.py"]):
        exit_code = main()
        assert exit_code == 1
