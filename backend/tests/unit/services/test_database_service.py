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
    def test_init_raises_if_no_url(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        with pytest.raises(ValueError, match="Database URL required"):
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
        assert "INSERT INTO sources" in mock_cursor.execute.call_args[0][0]

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

    @patch("psycopg2.connect")
    @patch("psycopg2.extras.execute_batch")
    def test_insert_measurements_batch(self, mock_execute_batch, mock_connect, db_service):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__.return_value = mock_cursor

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
        mock_execute_batch.assert_called_once()

    @patch("psycopg2.connect")
    def test_insert_measurements_empty(self, mock_connect, db_service):
        count = db_service.insert_measurements([])
        assert count == 0
        mock_connect.assert_not_called()

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
        assert mock_cursor.execute.call_args[0][1] == (30,)

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
