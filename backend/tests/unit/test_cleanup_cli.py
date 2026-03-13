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
def test_cleanup_execution_without_purge(mock_db, mock_aggregation, mock_db_stats):
    """Verify that default maintenance does not delete raw measurements."""
    mock_db_instance = mock_db.return_value
    mock_aggregation.return_value.backfill.return_value = {"hourly": 1, "daily": 1}

    with patch("sys.argv", ["cleanup.py"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.get_measurement_age_stats.assert_not_called()
        mock_db_instance.cleanup_old_measurements.assert_not_called()


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_execution_with_explicit_purge(mock_db, mock_aggregation, mock_db_stats):
    """Verify that deletion only happens with the explicit purge flag."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.cleanup_old_measurements.return_value = 200
    mock_aggregation.return_value.backfill.return_value = {"hourly": 1, "daily": 1}

    with patch(
        "sys.argv",
        ["cleanup.py", "--purge-old-measurements", "--retention-days", "60"],
    ):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.get_measurement_age_stats.assert_not_called()
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(retention_days=60)


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_with_stats_collects_measurement_age_stats(
    mock_db, mock_aggregation, mock_db_stats
):
    """Verify that full-table stats are opt-in during non-dry-run maintenance."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.get_measurement_age_stats.return_value = mock_db_stats
    mock_aggregation.return_value.backfill.return_value = {"hourly": 1, "daily": 1}

    with patch("sys.argv", ["cleanup.py", "--with-stats"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.get_measurement_age_stats.assert_called()


@patch("waittime.cli.cleanup.AggregationService")
@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_handles_exception(mock_db, mock_aggregation):
    """Verify that exceptions return exit code 1."""
    mock_aggregation.return_value.backfill.side_effect = Exception("DB Error")

    with patch("sys.argv", ["cleanup.py"]):
        exit_code = main()
        assert exit_code == 1
