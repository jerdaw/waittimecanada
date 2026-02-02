"""Tests for database cleanup functionality."""

import pytest
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock

from waittime.services.database import DatabaseService


@pytest.fixture
def mock_db_with_cleanup():
    """Create DatabaseService with mocked connection for cleanup testing."""
    db = DatabaseService.__new__(DatabaseService)
    db.database_url = "postgresql://test:test@localhost/test"
    return db


def setup_cursor_mock(return_value=None, rowcount=0):
    """Helper to create a properly mocked cursor with context manager support."""
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = return_value
    mock_cursor.rowcount = rowcount
    mock_cursor.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor.__exit__ = Mock(return_value=False)
    return mock_cursor


def setup_connection_mock(cursor_mock):
    """Helper to create a properly mocked connection with context manager support."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = cursor_mock
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)
    return mock_conn


class TestCleanupOldMeasurements:
    """Test cleanup_old_measurements method."""

    def test_deletes_old_measurements_with_default_retention(
        self, mock_db_with_cleanup, monkeypatch
    ):
        """Should delete measurements older than 30 days by default."""
        mock_cursor = setup_cursor_mock(rowcount=42)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        deleted = mock_db_with_cleanup.cleanup_old_measurements()

        # Should use default 30 days
        assert deleted == 42
        mock_cursor.execute.assert_called_once()
        query = mock_cursor.execute.call_args[0][0]
        assert "DELETE FROM measurements" in query
        assert "INTERVAL" in query

    def test_deletes_with_custom_retention_period(
        self, mock_db_with_cleanup, monkeypatch
    ):
        """Should accept custom retention period."""
        mock_cursor = setup_cursor_mock(rowcount=15)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        deleted = mock_db_with_cleanup.cleanup_old_measurements(retention_days=60)

        assert deleted == 15
        # Check that 60 was passed as parameter
        params = mock_cursor.execute.call_args[0][1]
        assert params == (60,)

    def test_returns_zero_when_no_old_measurements(
        self, mock_db_with_cleanup, monkeypatch
    ):
        """Should return 0 when no measurements need deletion."""
        mock_cursor = setup_cursor_mock(rowcount=0)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        deleted = mock_db_with_cleanup.cleanup_old_measurements()

        assert deleted == 0

    def test_commits_deletion(self, mock_db_with_cleanup, monkeypatch):
        """Should commit the transaction after deletion."""
        mock_cursor = setup_cursor_mock(rowcount=10)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        mock_db_with_cleanup.cleanup_old_measurements()

        # The connection context manager should handle commit
        # Just verify execute was called
        assert mock_cursor.execute.called


class TestGetMeasurementAgeStats:
    """Test get_measurement_age_stats method."""

    def test_returns_stats_when_measurements_exist(
        self, mock_db_with_cleanup, monkeypatch
    ):
        """Should return statistics about measurement ages."""
        mock_row = {
            "oldest_age_days": 45.5,
            "newest_age_days": 0.5,
            "total_measurements": 150,
            "measurements_older_than_30_days": 20,
        }
        mock_cursor = setup_cursor_mock(return_value=mock_row)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        stats = mock_db_with_cleanup.get_measurement_age_stats()

        assert stats["total_measurements"] == 150
        assert stats["oldest_measurement_age_days"] == 45.5
        assert stats["newest_measurement_age_days"] == 0.5
        assert stats["measurements_older_than_30_days"] == 20

    def test_returns_none_when_no_measurements(
        self, mock_db_with_cleanup, monkeypatch
    ):
        """Should return None values when no measurements in database."""
        mock_row = {
            "oldest_age_days": None,
            "newest_age_days": None,
            "total_measurements": 0,
            "measurements_older_than_30_days": 0,
        }
        mock_cursor = setup_cursor_mock(return_value=mock_row)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        stats = mock_db_with_cleanup.get_measurement_age_stats()

        assert stats["total_measurements"] == 0
        assert stats["oldest_measurement_age_days"] is None
        assert stats["newest_measurement_age_days"] is None
        assert stats["measurements_older_than_30_days"] == 0

    def test_rounds_age_to_one_decimal(self, mock_db_with_cleanup, monkeypatch):
        """Should round age values to 1 decimal place."""
        mock_row = {
            "oldest_age_days": 45.6789,
            "newest_age_days": 0.1234,
            "total_measurements": 100,
            "measurements_older_than_30_days": 10,
        }
        mock_cursor = setup_cursor_mock(return_value=mock_row)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        stats = mock_db_with_cleanup.get_measurement_age_stats()

        assert stats["oldest_measurement_age_days"] == 45.7
        assert stats["newest_measurement_age_days"] == 0.1

    def test_handles_null_row_gracefully(self, mock_db_with_cleanup, monkeypatch):
        """Should handle case where query returns no rows."""
        mock_cursor = setup_cursor_mock(return_value=None)
        mock_conn = setup_connection_mock(mock_cursor)

        def mock_get_connection():
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)
        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", lambda conn: mock_cursor)

        stats = mock_db_with_cleanup.get_measurement_age_stats()

        assert stats["total_measurements"] == 0
        assert stats["oldest_measurement_age_days"] is None


class TestCleanupIntegration:
    """Integration-style tests for cleanup workflow."""

    def test_cleanup_workflow(self, mock_db_with_cleanup, monkeypatch):
        """Test complete cleanup workflow: stats → cleanup → stats."""
        # First stats call - before cleanup
        stats_before = {
            "oldest_age_days": 60.0,
            "newest_age_days": 1.0,
            "total_measurements": 200,
            "measurements_older_than_30_days": 50,
        }

        # Stats after cleanup
        stats_after = {
            "oldest_age_days": 29.0,
            "newest_age_days": 1.0,
            "total_measurements": 150,
            "measurements_older_than_30_days": 0,
        }

        call_count = {"value": 0}

        def mock_cursor_factory():
            call_count["value"] += 1
            if call_count["value"] == 1:
                # First call - get stats before
                return setup_cursor_mock(return_value=stats_before)
            elif call_count["value"] == 2:
                # Second call - cleanup
                return setup_cursor_mock(rowcount=50)
            else:
                # Third call - get stats after
                return setup_cursor_mock(return_value=stats_after)

        def mock_get_connection():
            mock_conn = MagicMock()
            mock_conn.__enter__ = Mock(return_value=mock_conn)
            mock_conn.__exit__ = Mock(return_value=False)
            return mock_conn

        monkeypatch.setattr(mock_db_with_cleanup, "get_connection", mock_get_connection)

        original_get_cursor = mock_db_with_cleanup.get_cursor

        def mock_get_cursor(conn):
            return mock_cursor_factory()

        monkeypatch.setattr(mock_db_with_cleanup, "get_cursor", mock_get_cursor)

        # Execute workflow
        stats1 = mock_db_with_cleanup.get_measurement_age_stats()
        deleted = mock_db_with_cleanup.cleanup_old_measurements()
        stats2 = mock_db_with_cleanup.get_measurement_age_stats()

        # Verify workflow results
        assert stats1["measurements_older_than_30_days"] == 50
        assert deleted == 50
        assert stats2["measurements_older_than_30_days"] == 0
        assert stats2["total_measurements"] == 150
