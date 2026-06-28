from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from waittime.core.enums import (
    EndEvent,
    MetricFamily,
    PatientScope,
    StartEvent,
    StatisticType,
)
from waittime.core.models import (
    Hospital,
    Measurement,
    MeasurementAggregate,
    PublicHealthSourceAlertState,
    ScraperAlertState,
    Source,
)
from waittime.services.database import DatabaseService


@pytest.fixture
def mock_db_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost/db")
    return "postgresql://user@localhost/db"


@pytest.fixture
def db_service(mock_db_url):
    return DatabaseService(mock_db_url)


class TestDatabaseService:
    def test_init_uses_existing_env(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://user@localhost/db")

        db = DatabaseService(database_url=None)

        assert db.database_url == "postgresql://user@localhost/db"

    def test_init_prefers_explicit_database_url(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "postgresql://env@localhost/db")

        db = DatabaseService(database_url="postgresql://explicit@localhost/db")

        assert db.database_url == "postgresql://explicit@localhost/db"

    def test_init_raises_if_no_url(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValueError, match="Database URL or connection required"):
            DatabaseService(database_url=None)

    @patch("psycopg2.connect")
    def test_upsert_source(self, mock_connect, db_service):
        # Setup mock
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor  # Ensure context manager returns cursor

        mock_cursor.fetchone.return_value = {
            "id": "test_source",
            "name": "Test Source",
            "province": "ON",
            "url": "http://test.com",
            "methodology_url": "http://test.com/meth",
            "telehealth_name": "Tele",
            "telehealth_number": "811",
            "default_metric_family": "TIME_TO_PROVIDER",
            "default_start_event": "TRIAGE",
            "default_end_event": "PHYSICIAN",
            "default_statistic_type": "MEAN",
        }

        # Test object
        source = Source(
            id="test_source",
            name="Test Source",
            province="ON",
            url="http://test.com",
            methodology_url="http://test.com/meth",
            telehealth_name="Tele",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.MEAN,
        )

        # Execute
        result = db_service.upsert_source(source)

        # Verify
        assert result.id == "test_source"
        mock_cursor.execute.assert_called_once()
        executed_sql = mock_cursor.execute.call_args[0][0]
        assert "INSERT INTO sources" in executed_sql
        assert "methodology_url = EXCLUDED.methodology_url" in executed_sql
        assert "default_statistic_type = EXCLUDED.default_statistic_type" in executed_sql

    @patch("psycopg2.connect")
    def test_upsert_hospital(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "id": "hosp1",
            "name": "Test Hosp",
            "province": "ON",
            "city": "Toronto",
            "latitude": 43.0,
            "longitude": -79.0,
            "is_verified": True,
            "is_visible": True,
            "source_id": "src1",
        }

        hospital = Hospital(
            id="hosp1",
            name="Test Hosp",
            province="ON",
            city="Toronto",
            latitude=43.0,
            longitude=-79.0,
            is_verified=True,
            is_visible=True,
            source_id="src1",
        )

        result = db_service.upsert_hospital(hospital)
        assert result.id == "hosp1"
        assert "INSERT INTO hospitals" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_insert_measurement(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {"id": 1, "value": 45}

        measurement = Measurement(
            hospital_id="hosp1",
            timestamp_utc=datetime.now(UTC),
            value=45,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            patient_scope=PatientScope.ALL,
            source_id="src1",
            raw_payload_hash="a" * 64,
            parser_version="1.0",
        )

        result = db_service.insert_measurement(measurement)
        assert result["value"] == 45
        assert "INSERT INTO measurements" in mock_cursor.execute.call_args[0][0]
        assert "ON CONFLICT" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_insert_measurement_returns_existing_row_when_duplicate(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        existing_row = {
            "id": 99,
            "hospital_id": "hosp1",
            "timestamp_utc": datetime.now(UTC),
            "value": 45,
            "metric_family": "TIME_TO_PROVIDER",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "MEAN",
            "patient_scope": "ALL",
            "source_id": "src1",
            "raw_payload_hash": "a" * 64,
            "parser_version": "1.0",
        }
        mock_cursor.fetchone.side_effect = [None, existing_row]

        measurement = Measurement(
            hospital_id="hosp1",
            timestamp_utc=existing_row["timestamp_utc"],
            value=45,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            patient_scope=PatientScope.ALL,
            source_id="src1",
            raw_payload_hash="a" * 64,
            parser_version="1.0",
        )

        result = db_service.insert_measurement(measurement)
        assert result["id"] == 99
        assert mock_cursor.execute.call_count == 2

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    def test_insert_measurements_batch(self, mock_execute_values, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_execute_values.return_value = [(1,)]

        measurements = [
            Measurement(
                hospital_id="hosp1",
                timestamp_utc=datetime.now(UTC),
                value=45,
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.TRIAGE,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.MEAN,
                patient_scope=PatientScope.ALL,
                source_id="src1",
                raw_payload_hash="a" * 64,
                parser_version="1.0",
            )
        ]

        count = db_service.insert_measurements(measurements)
        assert count == 1
        mock_execute_values.assert_called_once()

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    def test_insert_measurements_batch_dedupes_exact_duplicates(
        self, mock_execute_values, mock_connect, db_service
    ):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_execute_values.return_value = [(1,)]

        timestamp = datetime.now(UTC)
        measurement = Measurement(
            hospital_id="hosp1",
            timestamp_utc=timestamp,
            value=45,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            patient_scope=PatientScope.ALL,
            source_id="src1",
            raw_payload_hash="a" * 64,
            parser_version="1.0",
        )

        count = db_service.insert_measurements([measurement, measurement])
        assert count == 1
        insert_rows = mock_execute_values.call_args[0][2]
        assert len(insert_rows) == 1

    @patch("psycopg2.connect")
    def test_insert_measurements_empty(self, mock_connect, db_service):
        count = db_service.insert_measurements([])
        assert count == 0
        mock_connect.assert_not_called()

    @patch("psycopg2.connect")
    def test_open_scraper_alert_incident(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "source_id": "ontario-health",
            "active_incident_kind": "error",
            "active_incident_fingerprint": "error:ontario-health:fetch:abc123",
            "opened_at": datetime.now(UTC),
            "last_notified_at": datetime.now(UTC),
            "last_resolved_at": None,
            "updated_at": datetime.now(UTC),
        }

        result = db_service.open_scraper_alert_incident(
            "ontario-health",
            "error",
            "error:ontario-health:fetch:abc123",
            "P2",
        )

        assert isinstance(result, ScraperAlertState)
        assert result.source_id == "ontario-health"
        assert result.active_incident_kind == "error"
        query, params = mock_cursor.execute.call_args[0]
        assert "INSERT INTO scraper_alert_state" in query
        assert "active_incident_notified_tier" in query
        assert params[-1] == "P2"

    @patch("psycopg2.connect")
    def test_resolve_scraper_alert_incident(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "source_id": "ontario-health",
            "active_incident_kind": None,
            "active_incident_fingerprint": None,
            "opened_at": None,
            "last_notified_at": None,
            "last_resolved_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        result = db_service.resolve_scraper_alert_incident("ontario-health")

        assert isinstance(result, ScraperAlertState)
        assert result.source_id == "ontario-health"
        assert result.active_incident_kind is None
        assert "INSERT INTO scraper_alert_state" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_open_public_health_source_alert_incident(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "source_id": "mohserlo",
            "active_incident_kind": "degraded",
            "active_incident_fingerprint": "degraded:mohserlo:abc123",
            "opened_at": datetime.now(UTC),
            "last_notified_at": datetime.now(UTC),
            "last_resolved_at": None,
            "updated_at": datetime.now(UTC),
        }

        result = db_service.open_public_health_source_alert_incident(
            "mohserlo",
            "degraded",
            "degraded:mohserlo:abc123",
            "P2",
        )

        assert isinstance(result, PublicHealthSourceAlertState)
        assert result.source_id == "mohserlo"
        assert result.active_incident_kind == "degraded"
        query, params = mock_cursor.execute.call_args[0]
        assert "INSERT INTO public_health_source_alert_state" in query
        assert "active_incident_notified_tier" in query
        assert params[-1] == "P2"

    @patch("psycopg2.connect")
    def test_resolve_public_health_source_alert_incident(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "source_id": "mohserlo",
            "active_incident_kind": None,
            "active_incident_fingerprint": None,
            "opened_at": None,
            "last_notified_at": None,
            "last_resolved_at": datetime.now(UTC),
            "updated_at": datetime.now(UTC),
        }

        result = db_service.resolve_public_health_source_alert_incident("mohserlo")

        assert isinstance(result, PublicHealthSourceAlertState)
        assert result.source_id == "mohserlo"
        assert result.active_incident_kind is None
        assert "INSERT INTO public_health_source_alert_state" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_cleanup_old_measurements(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.rowcount = 100

        deleted = db_service.cleanup_old_measurements(retention_days=30)
        assert deleted == 100
        assert "DELETE FROM measurements" in mock_cursor.execute.call_args[0][0]
        assert mock_cursor.execute.call_args[0][1][1] == 5000

    @patch("psycopg2.connect")
    def test_cleanup_old_measurements_honors_batch_controls(self, mock_connect, db_service):
        mock_conn1 = MagicMock()
        mock_cursor1 = MagicMock()
        mock_conn1.cursor.return_value = mock_cursor1
        mock_cursor1.__enter__.return_value = mock_cursor1
        mock_cursor1.rowcount = 50

        mock_conn2 = MagicMock()
        mock_cursor2 = MagicMock()
        mock_conn2.cursor.return_value = mock_cursor2
        mock_cursor2.__enter__.return_value = mock_cursor2
        mock_cursor2.rowcount = 0

        mock_connect.side_effect = [mock_conn1, mock_conn2]

        deleted = db_service.cleanup_old_measurements(
            retention_days=45,
            batch_size=2500,
            max_batches=2,
        )

        assert deleted == 50
        assert mock_cursor1.execute.call_args[0][1][1] == 2500

    @patch("psycopg2.connect")
    def test_get_measurement_baseline_stats(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "sample_count": 10,
            "mean_value": 50.0,
            "std_dev": 5.0,
            "q1": 40.0,
            "q3": 60.0,
        }

        now = datetime.now(UTC)
        stats = db_service.get_measurement_baseline_stats("hosp1", now, now)

        assert stats["sample_count"] == 10
        assert stats["mean_value"] == 50.0

    @patch("psycopg2.connect")
    def test_get_measurement_baseline_stats_none(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None

        now = datetime.now(UTC)
        stats = db_service.get_measurement_baseline_stats("hosp1", now, now)
        assert stats is None

    @patch("psycopg2.connect")
    def test_get_measurement_age_stats_empty(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "oldest_age_days": None,
            "newest_age_days": None,
            "total_measurements": 0,
            "measurements_older_than_threshold": 0,
        }

        stats = db_service.get_measurement_age_stats()
        assert stats["total_measurements"] == 0
        assert stats["older_than_days_threshold"] == 30
        assert stats["measurements_older_than_threshold"] == 0

    @patch("psycopg2.connect")
    def test_get_relation_storage_stats(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.return_value = {
            "relation_name": "measurements",
            "estimated_row_count": 1234,
            "table_bytes": 4096,
            "index_bytes": 2048,
            "total_bytes": 6144,
        }

        stats = db_service.get_relation_storage_stats()
        assert stats["relation_name"] == "measurements"
        assert stats["estimated_row_count"] == 1234
        assert stats["table_bytes"] == 4096

    @patch("psycopg2.connect")
    def test_get_relation_storage_stats_with_exact_count(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchone.side_effect = [
            {
                "relation_name": "measurements",
                "estimated_row_count": 1234,
                "table_bytes": 4096,
                "index_bytes": 2048,
                "total_bytes": 6144,
            },
            {"exact_row_count": 1200},
        ]

        stats = db_service.get_relation_storage_stats(exact_count=True)
        assert stats["exact_row_count"] == 1200

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    def test_insert_aggregates_batch(self, mock_execute_values, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_execute_values.return_value = [(1,), (1,)]

        aggregates = [
            MeasurementAggregate(
                hospital_id="hosp1",
                source_id="src1",
                period_type="daily",
                period_start=datetime(2026, 2, 1, tzinfo=UTC),
                period_end=datetime(2026, 2, 2, tzinfo=UTC),
                mean_value=100,
                median_value=100,
                p90_value=100,
                min_value=90,
                max_value=110,
                std_dev=5,
                sample_count=3,
                metric_family="TIME_TO_PROVIDER",
                start_event="TRIAGE",
                end_event="PHYSICIAN",
                statistic_type="MEAN",
            ),
            MeasurementAggregate(
                hospital_id="hosp2",
                source_id="src1",
                period_type="daily",
                period_start=datetime(2026, 2, 1, tzinfo=UTC),
                period_end=datetime(2026, 2, 2, tzinfo=UTC),
                mean_value=120,
                median_value=120,
                p90_value=120,
                min_value=100,
                max_value=140,
                std_dev=10,
                sample_count=4,
                metric_family="TIME_TO_PROVIDER",
                start_event="TRIAGE",
                end_event="PHYSICIAN",
                statistic_type="MEAN",
            ),
        ]

        inserted = db_service.insert_aggregates(aggregates)
        assert inserted == 2
        mock_execute_values.assert_called_once()

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_values")
    def test_upsert_aggregates_batch(self, mock_execute_values, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_execute_values.return_value = [(1,), (1,)]

        aggregates = [
            MeasurementAggregate(
                hospital_id="hosp1",
                source_id="src1",
                period_type="daily",
                period_start=datetime(2026, 2, 1, tzinfo=UTC),
                period_end=datetime(2026, 2, 2, tzinfo=UTC),
                mean_value=100,
                median_value=100,
                p90_value=100,
                min_value=90,
                max_value=110,
                std_dev=5,
                sample_count=3,
                metric_family="TIME_TO_PROVIDER",
                start_event="TRIAGE",
                end_event="PHYSICIAN",
                statistic_type="MEAN",
            ),
            MeasurementAggregate(
                hospital_id="hosp1",
                source_id="src1",
                period_type="weekly",
                period_start=datetime(2026, 2, 1, tzinfo=UTC),
                period_end=datetime(2026, 2, 8, tzinfo=UTC),
                mean_value=120,
                median_value=120,
                p90_value=120,
                min_value=100,
                max_value=140,
                std_dev=10,
                sample_count=4,
                metric_family="TIME_TO_PROVIDER",
                start_event="TRIAGE",
                end_event="PHYSICIAN",
                statistic_type="MEAN",
            ),
        ]

        refreshed = db_service.upsert_aggregates(aggregates)
        assert refreshed == 2
        mock_execute_values.assert_called_once()
        assert "DO UPDATE SET" in mock_execute_values.call_args[0][1]

    @patch("psycopg2.connect")
    def test_get_hospital_ids_with_measurements_since(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [
            {"hospital_id": "ca-on-a"},
            {"hospital_id": "ca-on-b"},
        ]

        hospital_ids = db_service.get_hospital_ids_with_measurements_since(
            datetime(2026, 2, 1, tzinfo=UTC)
        )

        assert hospital_ids == ["ca-on-a", "ca-on-b"]
        assert "SELECT DISTINCT m.hospital_id" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_insert_hospital(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "id": "hosp2",
            "name": "New Hosp",
            "province": "BC",
            "city": "Vancouver",
            "latitude": 49.0,
            "longitude": -123.0,
            "is_verified": False,
            "is_visible": False,
            "source_id": "src2",
        }

        hospital = Hospital(
            id="hosp2",
            name="New Hosp",
            province="BC",
            city="Vancouver",
            latitude=49.0,
            longitude=-123.0,
            is_verified=False,
            is_visible=False,
            source_id="src2",
        )

        result = db_service.insert_hospital(hospital)
        assert result.id == "hosp2"
        assert "INSERT INTO hospitals" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_verify_hospital(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "id": "hosp1",
            "name": "Test Hosp",
            "province": "ON",
            "city": "Toronto",
            "latitude": 43.0,
            "longitude": -79.0,
            # Verified and Visible now
            "is_verified": True,
            "is_visible": True,
            "source_id": "src1",
        }

        result = db_service.verify_hospital("hosp1", make_visible=True)
        assert result.is_verified is True
        assert result.is_visible is True
        assert "UPDATE hospitals" in mock_cursor.execute.call_args[0][0]

    @patch("psycopg2.connect")
    def test_get_latest_measurement(self, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

        mock_cursor.fetchone.return_value = {
            "hospital_id": "hosp1",
            "timestamp_utc": datetime.now(UTC),
            "value": 30,
            "metric_family": "TIME_TO_PROVIDER",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "MEAN",
            "patient_scope": "ALL",
            "source_id": "src1",
            "raw_payload_hash": "a" * 64,
            "parser_version": "1.0",
        }

        result = db_service.get_latest_measurement("hosp1")
        assert result.value == 30.0
        assert "SELECT * FROM measurements" in mock_cursor.execute.call_args[0][0]
        assert "ORDER BY timestamp_utc DESC" in mock_cursor.execute.call_args[0][0]
