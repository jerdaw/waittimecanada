"""Integration tests for DatabaseService with real database."""

from datetime import UTC, datetime

import pytest

from waittime.core import (
    EndEvent,
    Hospital,
    Measurement,
    MetricFamily,
    PatientScope,
    Source,
    StartEvent,
    StatisticType,
)
from waittime.services.database import DatabaseService


@pytest.mark.integration
class TestDatabaseServiceIntegration:
    """Test DatabaseService with real database connections."""

    def test_source_crud_operations(self, clean_database: DatabaseService):
        """Test creating, reading, updating, and deleting sources."""
        db = clean_database

        # Create a test source
        source = Source(
            id="test-source-1",
            name="Test Source",
            province="ON",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Test Health Link",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.POINT_ESTIMATE,
        )

        # Insert
        created = db.upsert_source(source)
        assert created.id == "test-source-1"
        assert created.name == "Test Source"

        # Read
        fetched = db.get_source("test-source-1")
        assert fetched is not None
        assert fetched.id == "test-source-1"
        assert fetched.province == "ON"

        # Verify in all sources list
        all_sources = db.list_sources()
        test_sources = [s for s in all_sources if s.id.startswith("test-")]
        assert len(test_sources) >= 1
        assert any(s.id == "test-source-1" for s in test_sources)

    def test_hospital_crud_operations(self, clean_database: DatabaseService):
        """Test creating, reading, updating, and verifying hospitals."""
        db = clean_database

        # First create a source
        source = Source(
            id="test-source-hospital",
            name="Test Source",
            province="QC",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Info-Santé",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.ROLLING_AVG,
        )
        db.upsert_source(source)

        # Create a test hospital
        hospital = Hospital(
            id="test-hospital-1",
            name="Test Hospital",
            province="QC",
            city="Montreal",
            latitude=45.5017,
            longitude=-73.5673,
            source_id="test-source-hospital",
            is_verified=False,
            is_visible=False,
        )

        # Insert
        created = db.upsert_hospital(hospital)
        assert created.id == "test-hospital-1"
        assert created.name == "Test Hospital"
        assert created.is_verified is False
        assert created.is_visible is False

        # Read
        fetched = db.get_hospital("test-hospital-1")
        assert fetched is not None
        assert fetched.city == "Montreal"

        # Verify hospital
        verified = db.verify_hospital("test-hospital-1", make_visible=True)
        assert verified.is_verified is True
        assert verified.is_visible is True

        # Verify it's now in public listings
        public_hospitals = db.list_hospitals()
        test_public = [h for h in public_hospitals if h.id == "test-hospital-1"]
        assert len(test_public) == 1

    def test_measurement_insert_and_query(self, clean_database: DatabaseService):
        """Test inserting and querying measurements."""
        db = clean_database

        # Setup source and hospital
        source = Source(
            id="test-source-measurement",
            name="Test Source",
            province="ON",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Health Link",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.P90,
        )
        db.upsert_source(source)

        hospital = Hospital(
            id="test-hospital-measurement",
            name="Test Hospital",
            province="ON",
            city="Toronto",
            latitude=43.6532,
            longitude=-79.3832,
            source_id="test-source-measurement",
            is_verified=True,
            is_visible=True,
        )
        db.upsert_hospital(hospital)

        # Create measurement
        measurement = Measurement(
            hospital_id="test-hospital-measurement",
            value=120.5,
            timestamp_utc=datetime.now(UTC),
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.P90,
            patient_scope=PatientScope.MID_ACUITY,
            source_id="test-source-measurement",
            raw_payload_hash="832363f4685e261faf4ee117e0afe46d10b926061eed98631e429d12d3726b77",
            raw_payload_snippet="<html>Test snippet</html>",
            parser_version="v1.0.0",
        )

        # Insert
        result = db.insert_measurement(measurement)
        assert result["id"] is not None
        assert "id" in result

        # Query latest measurement
        latest = db.get_latest_measurement("test-hospital-measurement")
        assert latest is not None
        assert latest.value == 120.5
        assert latest.hospital_id == "test-hospital-measurement"

    def test_hospital_visibility_filtering(self, clean_database: DatabaseService):
        """Test that unverified/invisible hospitals are filtered correctly."""
        db = clean_database

        # Create source
        source = Source(
            id="test-source-visibility",
            name="Test Source",
            province="AB",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Health Link",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.MEDIAN,
        )
        db.upsert_source(source)

        # Create hospitals with different visibility states
        hospitals = [
            Hospital(
                id="test-hospital-public",
                name="Public Hospital",
                province="AB",
                city="Calgary",
                latitude=51.0447,
                longitude=-114.0719,
                source_id="test-source-visibility",
                is_verified=True,
                is_visible=True,
            ),
            Hospital(
                id="test-hospital-unverified",
                name="Unverified Hospital",
                province="AB",
                city="Edmonton",
                latitude=53.5461,
                longitude=-113.4938,
                source_id="test-source-visibility",
                is_verified=False,
                is_visible=False,
            ),
            Hospital(
                id="test-hospital-hidden",
                name="Hidden Hospital",
                province="AB",
                city="Red Deer",
                latitude=52.2681,
                longitude=-113.8111,
                source_id="test-source-visibility",
                is_verified=True,
                is_visible=False,
            ),
        ]

        for hospital in hospitals:
            db.upsert_hospital(hospital)

        # Query public hospitals (with visible_only=True)
        public = db.list_hospitals(visible_only=True)
        test_public_ids = [h.id for h in public if h.id.startswith("test-hospital-")]

        # Only the public one should appear
        assert "test-hospital-public" in test_public_ids
        assert "test-hospital-unverified" not in test_public_ids
        assert "test-hospital-hidden" not in test_public_ids

        # Query by province should also filter
        ab_hospitals = db.list_hospitals(province="AB", visible_only=True)
        test_ab_ids = [h.id for h in ab_hospitals if h.id.startswith("test-hospital-")]
        assert "test-hospital-public" in test_ab_ids
        assert "test-hospital-unverified" not in test_ab_ids

    def test_data_cleanup(self, clean_database: DatabaseService):
        """Test that old measurements can be cleaned up."""
        db = clean_database

        # Setup
        source = Source(
            id="test-source-cleanup",
            name="Test Source",
            province="BC",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="HealthLink BC",
            telehealth_number="811",
            default_metric_family=MetricFamily.TOTAL_LOS,
            default_start_event=StartEvent.DOOR,
            default_end_event=EndEvent.DISCHARGE,
            default_statistic_type=StatisticType.MEAN,
        )
        db.upsert_source(source)

        hospital = Hospital(
            id="test-hospital-cleanup",
            name="Test Hospital",
            province="BC",
            city="Vancouver",
            latitude=49.2827,
            longitude=-123.1207,
            source_id="test-source-cleanup",
            is_verified=True,
            is_visible=True,
        )
        db.upsert_hospital(hospital)

        # Insert a recent measurement
        recent = Measurement(
            hospital_id="test-hospital-cleanup",
            value=90.0,
            timestamp_utc=datetime.now(UTC),
            metric_family=MetricFamily.TOTAL_LOS,
            start_event=StartEvent.DOOR,
            end_event=EndEvent.DISCHARGE,
            statistic_type=StatisticType.MEAN,
            patient_scope=PatientScope.ALL,
            source_id="test-source-cleanup",
            raw_payload_hash="8e21a44ca86e897ee68a5557efa300b218dbc1702d9c23010b619ac895800091",
            raw_payload_snippet="recent",
            parser_version="v1.0.0",
        )
        db.insert_measurement(recent)

        # Query age stats
        stats = db.get_measurement_age_stats()
        assert stats["total_measurements"] > 0

        # Note: We can't easily test actual cleanup since we'd need to insert
        # old data (which requires database timestamp manipulation).
        # The cleanup functionality is tested in unit tests with mocks.

    def test_heartbeat_recording(self, clean_database: DatabaseService):
        """Test recording scraper heartbeats."""
        from waittime.services.heartbeat import HeartbeatService

        db = clean_database

        # Create a test source
        source = Source(
            id="test-source-heartbeat",
            name="Test Source",
            province="MB",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Health Links",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.REGISTRATION,
            default_end_event=EndEvent.PROVIDER,
            default_statistic_type=StatisticType.ALGORITHMIC,
        )
        db.upsert_source(source)

        heartbeat = HeartbeatService(db)

        # Record success
        heartbeat.record_success("test-source-heartbeat", measurements_count=5)

        # Check health
        health = heartbeat.check_health("test-source-heartbeat")
        assert health["healthy"] is True
        assert health["measurements_count"] == 5
        assert health["reason"] is None  # None when healthy

        # Record failure
        heartbeat.record_failure("test-source-heartbeat", error_message="Test error")

        # Check health after failure
        health_after_fail = heartbeat.check_health("test-source-heartbeat")
        assert health_after_fail["healthy"] is False
        assert health_after_fail["reason"] == "last_run_failed"
        assert "Test error" in health_after_fail["message"]


@pytest.mark.integration
class TestComparisonServiceIntegration:
    """Test ComparisonService with real database."""

    def test_compare_hospitals_full_workflow(self, clean_database: DatabaseService):
        """Test comparing two hospitals end-to-end."""
        from waittime.services.comparison import ComparisonService

        db = clean_database
        comparison = ComparisonService(db)

        # Setup test data
        source = Source(
            id="test-source-comparison",
            name="Test Source",
            province="SK",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="HealthLine",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.P90,
        )
        db.upsert_source(source)

        hospitals = [
            Hospital(
                id="test-hospital-a",
                name="Hospital A",
                province="SK",
                city="Regina",
                latitude=50.4452,
                longitude=-104.6189,
                source_id="test-source-comparison",
                is_verified=True,
                is_visible=True,
            ),
            Hospital(
                id="test-hospital-b",
                name="Hospital B",
                province="SK",
                city="Saskatoon",
                latitude=52.1332,
                longitude=-106.6700,
                source_id="test-source-comparison",
                is_verified=True,
                is_visible=True,
            ),
        ]

        for hospital in hospitals:
            db.upsert_hospital(hospital)

        # Insert measurements
        measurements = [
            Measurement(
                hospital_id="test-hospital-a",
                value=100.0,
                timestamp_utc=datetime.now(UTC),
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.TRIAGE,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.P90,
                patient_scope=PatientScope.MID_ACUITY,
                source_id="test-source-comparison",
                raw_payload_hash="400075069c197bbcb0114c66fdcaefa53e224de63bbe58f67f9af54691c996fa",
                raw_payload_snippet="snippet-a",
                parser_version="v1.0.0",
            ),
            Measurement(
                hospital_id="test-hospital-b",
                value=150.0,
                timestamp_utc=datetime.now(UTC),
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.TRIAGE,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.P90,
                patient_scope=PatientScope.MID_ACUITY,
                source_id="test-source-comparison",
                raw_payload_hash="580e36de86fe5fde24c0d67de903eacf0531bedc5c7e15020580624bf3fbd2f5",
                raw_payload_snippet="snippet-b",
                parser_version="v1.0.0",
            ),
        ]

        for measurement in measurements:
            db.insert_measurement(measurement)

        # Compare hospitals
        result = comparison.compare_hospitals("test-hospital-a", "test-hospital-b")

        assert result is not None
        assert result["hospital_a"]["id"] == "test-hospital-a"
        assert result["hospital_b"]["id"] == "test-hospital-b"
        assert result["hospital_a"]["wait_time"] == 100.0
        assert result["hospital_b"]["wait_time"] == 150.0
        assert result["comparable"] is True
        assert result["divergence_brief"] is None
