"""Tests for HeartbeatService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, Mock

import pytest

from waittime.core import ScraperStatus
from waittime.services.heartbeat import HeartbeatService


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    db = Mock()
    return db


@pytest.fixture
def heartbeat_service(mock_db):
    """Create HeartbeatService with mocked database."""
    return HeartbeatService(mock_db)


class TestRecordSuccess:
    """Test successful scraper run recording."""

    def test_records_success_with_measurement_count(self, heartbeat_service, mock_db):
        """Should call database with correct parameters for successful run."""
        mock_status = ScraperStatus(
            source_id="qc-msss",
            last_run=datetime.now(UTC),
            status="healthy",
            error_message=None,
            measurements_count=15,
        )
        mock_db.update_heartbeat.return_value = mock_status

        result = heartbeat_service.record_success("qc-msss", measurements_count=15)

        mock_db.update_heartbeat.assert_called_once_with(
            source_id="qc-msss",
            status="healthy",
            error_message=None,
            measurements_count=15,
        )
        assert result == mock_status
        assert result.status == "healthy"
        assert result.measurements_count == 15

    def test_records_zero_measurements(self, heartbeat_service, mock_db):
        """Should handle case where no measurements were collected."""
        mock_status = ScraperStatus(
            source_id="on-hqo",
            last_run=datetime.now(UTC),
            status="healthy",
            error_message=None,
            measurements_count=0,
        )
        mock_db.update_heartbeat.return_value = mock_status

        result = heartbeat_service.record_success("on-hqo", measurements_count=0)

        assert result.measurements_count == 0
        assert result.status == "healthy"


class TestRecordFailure:
    """Test failed scraper run recording."""

    def test_records_failure_with_error_message(self, heartbeat_service, mock_db):
        """Should call database with error status and message."""
        mock_status = ScraperStatus(
            source_id="qc-msss",
            last_run=datetime.now(UTC),
            status="error",
            error_message="Connection timeout",
            measurements_count=0,
        )
        mock_db.update_heartbeat.return_value = mock_status

        result = heartbeat_service.record_failure("qc-msss", "Connection timeout")

        mock_db.update_heartbeat.assert_called_once_with(
            source_id="qc-msss",
            status="error",
            error_message="Connection timeout",
            measurements_count=0,
        )
        assert result.status == "error"
        assert result.error_message == "Connection timeout"

    def test_truncates_long_error_messages(self, heartbeat_service, mock_db):
        """Should truncate error messages longer than 500 characters."""
        long_error = "X" * 600
        mock_status = ScraperStatus(
            source_id="qc-msss",
            last_run=datetime.now(UTC),
            status="error",
            error_message=long_error[:500],
            measurements_count=0,
        )
        mock_db.update_heartbeat.return_value = mock_status

        _result = heartbeat_service.record_failure("qc-msss", long_error)

        # Should truncate to 500 characters
        call_args = mock_db.update_heartbeat.call_args
        assert len(call_args.kwargs["error_message"]) == 500

    def test_handles_empty_error_message(self, heartbeat_service, mock_db):
        """Should use default message if error is empty."""
        mock_status = ScraperStatus(
            source_id="qc-msss",
            last_run=datetime.now(UTC),
            status="error",
            error_message="Unknown error",
            measurements_count=0,
        )
        mock_db.update_heartbeat.return_value = mock_status

        _result = heartbeat_service.record_failure("qc-msss", "")

        call_args = mock_db.update_heartbeat.call_args
        assert call_args.kwargs["error_message"] == "Unknown error"


class TestCheckHealth:
    """Test health check for individual scrapers."""

    def test_no_heartbeat_returns_unhealthy(self, heartbeat_service, mock_db):
        """Should return unhealthy if no heartbeat ever recorded."""
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.return_value = mock_cursor

        result = heartbeat_service.check_health("new-source")

        assert result["healthy"] is False
        assert result["reason"] == "no_heartbeat"
        assert result["source_id"] == "new-source"
        assert result["last_run"] is None

    def test_failed_last_run_returns_unhealthy(self, heartbeat_service, mock_db):
        """Should return unhealthy if last run failed."""
        last_run = datetime.now(UTC) - timedelta(minutes=10)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "source_id": "qc-msss",
            "last_run": last_run,
            "status": "error",
            "error_message": "HTTP 500",
            "measurements_count": 0,
        }
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.return_value = mock_cursor

        result = heartbeat_service.check_health("qc-msss")

        assert result["healthy"] is False
        assert result["reason"] == "last_run_failed"
        assert result["message"] == "HTTP 500"
        assert result["measurements_count"] == 0

    def test_stale_data_returns_unhealthy(self, heartbeat_service, mock_db):
        """Should return unhealthy if data is older than threshold."""
        last_run = datetime.now(UTC) - timedelta(minutes=90)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "source_id": "qc-msss",
            "last_run": last_run,
            "status": "healthy",
            "error_message": None,
            "measurements_count": 15,
        }
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.return_value = mock_cursor

        result = heartbeat_service.check_health("qc-msss", max_age_minutes=60)

        assert result["healthy"] is False
        assert result["reason"] == "stale"
        assert "90 minutes ago" in result["message"]

    def test_recent_successful_run_returns_healthy(self, heartbeat_service, mock_db):
        """Should return healthy if recent successful run exists."""
        last_run = datetime.now(UTC) - timedelta(minutes=10)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "source_id": "qc-msss",
            "last_run": last_run,
            "status": "healthy",
            "error_message": None,
            "measurements_count": 15,
        }
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.return_value = mock_cursor

        result = heartbeat_service.check_health("qc-msss")

        assert result["healthy"] is True
        assert result["reason"] is None
        assert result["measurements_count"] == 15

    def test_uses_custom_threshold(self, heartbeat_service, mock_db):
        """Should use custom age threshold when provided."""
        last_run = datetime.now(UTC) - timedelta(minutes=50)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "source_id": "qc-msss",
            "last_run": last_run,
            "status": "healthy",
            "error_message": None,
            "measurements_count": 15,
        }
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.return_value = mock_cursor

        result = heartbeat_service.check_health("qc-msss", max_age_minutes=30)

        assert result["healthy"] is False
        assert result["reason"] == "stale"

    def test_uses_default_threshold(self, heartbeat_service, mock_db):
        """Should use DEFAULT_STALE_THRESHOLD when no threshold provided."""
        last_run = datetime.now(UTC) - timedelta(minutes=50)
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = {
            "source_id": "qc-msss",
            "last_run": last_run,
            "status": "healthy",
            "error_message": None,
            "measurements_count": 15,
        }
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.return_value = mock_cursor

        result = heartbeat_service.check_health("qc-msss")

        # 50 minutes is less than DEFAULT_STALE_THRESHOLD (60), so should be healthy
        assert result["healthy"] is True


class TestCheckAllSources:
    """Test health check for all sources."""

    def test_all_healthy_sources(self, heartbeat_service, mock_db):
        """Should return healthy=True when all sources are healthy."""
        from waittime.core import EndEvent, MetricFamily, Source, StartEvent, StatisticType

        mock_sources = [
            Source(
                id="qc-msss",
                name="Quebec",
                province="QC",
                url="http://example.com",
                telehealth_name="Info-Santé 811",
                telehealth_number="811",
                default_metric_family=MetricFamily.TIME_TO_PROVIDER,
                default_start_event=StartEvent.TRIAGE,
                default_end_event=EndEvent.PHYSICIAN,
                default_statistic_type=StatisticType.P90,
            ),
            Source(
                id="on-hqo",
                name="Ontario",
                province="ON",
                url="http://example.com",
                telehealth_name="Health Link 811",
                telehealth_number="811",
                default_metric_family=MetricFamily.TIME_TO_PROVIDER,
                default_start_event=StartEvent.TRIAGE,
                default_end_event=EndEvent.PHYSICIAN,
                default_statistic_type=StatisticType.P90,
            ),
        ]
        mock_db.list_sources.return_value = mock_sources

        # Mock check_health to return healthy for both
        _original_check = heartbeat_service.check_health
        healthy_result = {
            "source_id": "test",
            "healthy": True,
            "reason": None,
            "message": None,
            "last_run": datetime.now(UTC).isoformat(),
            "age_minutes": 10.0,
            "measurements_count": 15,
        }

        def mock_check_health(source_id, max_age_minutes=None):
            result = healthy_result.copy()
            result["source_id"] = source_id
            return result

        heartbeat_service.check_health = mock_check_health

        result = heartbeat_service.check_all_sources()

        assert result["healthy"] is True
        assert result["unhealthy_count"] == 0
        assert result["total_count"] == 2
        assert len(result["sources"]) == 2

    def test_some_unhealthy_sources(self, heartbeat_service, mock_db):
        """Should return healthy=False when any source is unhealthy."""
        from waittime.core import EndEvent, MetricFamily, Source, StartEvent, StatisticType

        mock_sources = [
            Source(
                id="qc-msss",
                name="Quebec",
                province="QC",
                url="http://example.com",
                telehealth_name="Info-Santé 811",
                telehealth_number="811",
                default_metric_family=MetricFamily.TIME_TO_PROVIDER,
                default_start_event=StartEvent.TRIAGE,
                default_end_event=EndEvent.PHYSICIAN,
                default_statistic_type=StatisticType.P90,
            ),
            Source(
                id="on-hqo",
                name="Ontario",
                province="ON",
                url="http://example.com",
                telehealth_name="Health Link 811",
                telehealth_number="811",
                default_metric_family=MetricFamily.TIME_TO_PROVIDER,
                default_start_event=StartEvent.TRIAGE,
                default_end_event=EndEvent.PHYSICIAN,
                default_statistic_type=StatisticType.P90,
            ),
        ]
        mock_db.list_sources.return_value = mock_sources

        def mock_check_health(source_id, max_age_minutes=None):
            if source_id == "qc-msss":
                return {
                    "source_id": source_id,
                    "healthy": True,
                    "reason": None,
                    "message": None,
                    "last_run": datetime.now(UTC).isoformat(),
                    "age_minutes": 10.0,
                    "measurements_count": 15,
                }
            else:
                return {
                    "source_id": source_id,
                    "healthy": False,
                    "reason": "stale",
                    "message": "Data is stale",
                    "last_run": datetime.now(UTC).isoformat(),
                    "age_minutes": 90.0,
                    "measurements_count": 10,
                }

        heartbeat_service.check_health = mock_check_health

        result = heartbeat_service.check_all_sources()

        assert result["healthy"] is False
        assert result["unhealthy_count"] == 1
        assert result["total_count"] == 2


class TestGetStalescrapers:
    """Test retrieving stale scrapers."""

    def test_delegates_to_database(self, heartbeat_service, mock_db):
        """Should call database get_stale_scrapers with threshold."""
        mock_statuses = [
            ScraperStatus(
                source_id="old-source",
                last_run=datetime.now(UTC) - timedelta(minutes=90),
                status="healthy",
                error_message=None,
                measurements_count=10,
            )
        ]
        mock_db.get_stale_scrapers.return_value = mock_statuses

        result = heartbeat_service.get_stale_scrapers(threshold_minutes=60)

        mock_db.get_stale_scrapers.assert_called_once_with(60)
        assert len(result) == 1
        assert result[0].source_id == "old-source"

    def test_uses_default_threshold(self, heartbeat_service, mock_db):
        """Should use DEFAULT_STALE_THRESHOLD when not specified."""
        mock_db.get_stale_scrapers.return_value = []

        _result = heartbeat_service.get_stale_scrapers()

        mock_db.get_stale_scrapers.assert_called_once_with(60)
