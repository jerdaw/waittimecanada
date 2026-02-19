from unittest.mock import patch

import pytest
from waittime.cli.cleanup import main


@pytest.fixture
def mock_db_stats():
    return {
        "total_measurements": 1000,
        "oldest_measurement_age_days": 45,
        "newest_measurement_age_days": 0,
        "measurements_older_than_30_days": 200,
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


@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_execution(mock_db, mock_db_stats):
    """Verify that cleanup execution calls the database service."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.get_measurement_age_stats.return_value = mock_db_stats
    mock_db_instance.cleanup_old_measurements.return_value = 200

    with patch("sys.argv", ["cleanup.py", "--retention-days", "60"]):
        exit_code = main()
        assert exit_code == 0
        mock_db_instance.cleanup_old_measurements.assert_called_once_with(retention_days=60)


@patch("waittime.cli.cleanup.DatabaseService")
def test_cleanup_handles_exception(mock_db):
    """Verify that exceptions return exit code 1."""
    mock_db_instance = mock_db.return_value
    mock_db_instance.get_measurement_age_stats.side_effect = Exception("DB Error")

    with patch("sys.argv", ["cleanup.py"]):
        exit_code = main()
        assert exit_code == 1
