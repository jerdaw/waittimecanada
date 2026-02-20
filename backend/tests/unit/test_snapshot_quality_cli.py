"""Unit tests for the snapshot_quality CLI."""

import sys
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest
from waittime.cli.snapshot_quality import main


@pytest.fixture
def mock_db():
    with patch("waittime.cli.snapshot_quality.DatabaseService") as mock:
        instance = MagicMock()
        mock.return_value = instance
        yield instance


@pytest.fixture
def mock_quality_service():
    with patch("waittime.cli.snapshot_quality.DataQualityService") as mock:
        instance = MagicMock()
        mock.return_value = instance
        # Return 5 saved snapshots by default
        instance.snapshot_daily_quality.return_value = 5
        yield instance


def test_snapshot_quality_cli_default(mock_db, mock_quality_service):
    """Test CLI runs for yesterday by default."""
    test_args = ["snapshot_quality"]
    with patch.object(sys, "argv", test_args):
        assert main() == 0

    assert mock_quality_service.snapshot_daily_quality.call_count == 1
    # Check that it was called with roughly yesterday
    expected_date = (datetime.now(UTC) - timedelta(days=1)).date()
    called_date = mock_quality_service.snapshot_daily_quality.call_args[0][0].date()
    assert called_date == expected_date


def test_snapshot_quality_cli_specific_date(mock_db, mock_quality_service):
    """Test CLI runs for a specific valid date."""
    test_args = ["snapshot_quality", "--date", "2026-02-18"]
    with patch.object(sys, "argv", test_args):
        assert main() == 0

    assert mock_quality_service.snapshot_daily_quality.call_count == 1
    called_date = mock_quality_service.snapshot_daily_quality.call_args[0][0].date()
    assert called_date == datetime(2026, 2, 18).date()


def test_snapshot_quality_cli_invalid_date(mock_db, mock_quality_service):
    """Test CLI handles invalid date formats."""
    test_args = ["snapshot_quality", "--date", "18-02-2026"]
    with patch.object(sys, "argv", test_args):
        assert main() == 1

    assert mock_quality_service.snapshot_daily_quality.call_count == 0


def test_snapshot_quality_cli_backfill(mock_db, mock_quality_service):
    """Test CLI backfills for N days."""
    test_args = ["snapshot_quality", "--date", "2026-02-18", "--backfill-days", "3"]
    with patch.object(sys, "argv", test_args):
        assert main() == 0

    assert mock_quality_service.snapshot_daily_quality.call_count == 3
    # Check that it processed oldest first
    call_args_list = mock_quality_service.snapshot_daily_quality.call_args_list
    assert call_args_list[0][0][0].date() == datetime(2026, 2, 16).date()
    assert call_args_list[1][0][0].date() == datetime(2026, 2, 17).date()
    assert call_args_list[2][0][0].date() == datetime(2026, 2, 18).date()


def test_snapshot_quality_cli_exception(mock_db, mock_quality_service):
    """Test CLI gracefully handles exceptions."""
    mock_quality_service.snapshot_daily_quality.side_effect = Exception("DB Error")

    test_args = ["snapshot_quality", "--date", "2026-02-18"]
    with patch.object(sys, "argv", test_args):
        assert main() == 1

    assert mock_quality_service.snapshot_daily_quality.call_count == 1
    assert mock_db.close.call_count == 1
