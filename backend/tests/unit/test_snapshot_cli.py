"""Tests for the snapshot CLI."""

from unittest.mock import MagicMock, patch

import pytest
from waittime.cli.snapshot import main


@pytest.fixture
def mock_db():
    with patch("waittime.cli.snapshot.DatabaseService") as mock:
        yield mock.return_value


@pytest.fixture
def mock_svc():
    with patch("waittime.cli.snapshot.DataQualityService") as mock:
        instance = mock.return_value
        instance.snapshot_daily_quality.return_value = 5
        yield instance


@patch("waittime.cli.snapshot.datetime")
def test_snapshot_calls_service_with_now(mock_datetime, mock_db, mock_svc, monkeypatch):
    monkeypatch.setattr("sys.argv", ["snapshot.py"])

    # Mock datetime.now(timezone.utc)
    mock_now = MagicMock()
    mock_now.date.return_value = "2026-02-19"
    mock_datetime.now.return_value = mock_now

    result = main()

    assert result == 0
    mock_svc.snapshot_daily_quality.assert_called_once_with(mock_now)


def test_snapshot_dry_run(mock_db, mock_svc, monkeypatch):
    monkeypatch.setattr("sys.argv", ["snapshot.py", "--dry-run"])

    result = main()

    assert result == 0
    # Service should not be called in dry-run
    mock_svc.snapshot_daily_quality.assert_not_called()


def test_snapshot_handles_exception(mock_db, mock_svc, monkeypatch):
    monkeypatch.setattr("sys.argv", ["snapshot.py"])
    mock_svc.snapshot_daily_quality.side_effect = Exception("Database connection failed")

    result = main()

    assert result == 1
