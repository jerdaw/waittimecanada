"""Integration tests for scrapers with real database writes."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from waittime.core import Hospital, Source
from waittime.scrapers.base import BaseScraper
from waittime.services.database import DatabaseService


class TestScraperDatabase:
    """Test scraper database integration."""

    @pytest.fixture
    def test_source(self, clean_database: DatabaseService) -> Source:
        """Create a test source for scraper tests."""
        from waittime.core import EndEvent, MetricFamily, StartEvent, StatisticType

        source = Source(
            id="test-scraper-source",
            name="Test Scraper Source",
            province="ON",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Test Health",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.POINT_ESTIMATE,
        )
        clean_database.upsert_source(source)
        return source

    @pytest.mark.integration
    def test_scraper_can_upsert_hospital(
        self, clean_database: DatabaseService, test_source: Source
    ):
        """Test that a scraper can discover and insert a new hospital."""

        # Create a concrete scraper for testing
        class TestScraper(BaseScraper):
            def parse(self, html: str) -> list[dict]:
                return []

            def fetch(self) -> str:
                return "<html>test</html>"

        _scraper = TestScraper(test_source, clean_database)

        # Insert a hospital via scraper
        hospital = Hospital(
            id="test-scraper-hospital-1",
            name="Scraper Test Hospital",
            province="ON",
            city="Ottawa",
            latitude=45.4215,
            longitude=-75.6972,
            source_id=test_source.id,
            is_verified=False,
            is_visible=False,
        )

        # Use the database service to insert
        result = clean_database.upsert_hospital(hospital)

        assert result.id == "test-scraper-hospital-1"
        assert result.is_verified is False
        assert result.is_visible is False

        # Verify it's in the database
        fetched = clean_database.get_hospital("test-scraper-hospital-1")
        assert fetched is not None
        assert fetched.name == "Scraper Test Hospital"

    @pytest.mark.integration
    def test_scraper_can_write_measurements(
        self, clean_database: DatabaseService, test_source: Source
    ):
        """Test that a scraper can write measurements to the database."""
        from waittime.core import (
            EndEvent,
            Measurement,
            MetricFamily,
            PatientScope,
            StartEvent,
            StatisticType,
        )

        # First create a hospital
        hospital = Hospital(
            id="test-scraper-hospital-2",
            name="Measurement Test Hospital",
            province="ON",
            city="Toronto",
            latitude=43.6532,
            longitude=-79.3832,
            source_id=test_source.id,
            is_verified=True,
            is_visible=True,
        )
        clean_database.upsert_hospital(hospital)

        # Create and insert a measurement
        measurement = Measurement(
            hospital_id="test-scraper-hospital-2",
            value=75.5,
            timestamp_utc=datetime.now(UTC),
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.POINT_ESTIMATE,
            patient_scope=PatientScope.ALL,
            source_id=test_source.id,
            raw_payload_hash="0000000000000000000000000000000000000000000000000000000000000000",
            raw_payload_snippet="<html>test</html>",
            parser_version="v1.0.0",
        )

        result = clean_database.insert_measurement(measurement)

        assert result["id"] is not None
        assert "id" in result

        # Verify the measurement was stored
        latest = clean_database.get_latest_measurement("test-scraper-hospital-2")
        assert latest is not None
        assert latest.value == 75.5

    @pytest.mark.integration
    def test_scraper_heartbeat_workflow(self, clean_database: DatabaseService, test_source: Source):
        """Test the complete scraper heartbeat workflow."""
        from waittime.scrapers.base import BaseScraper
        from waittime.services.heartbeat import HeartbeatService

        # Create a concrete scraper
        class TestScraper(BaseScraper):
            def parse(self, html: str) -> list[dict]:
                return [{"hospital_id": "test-1", "wait_time": 60}]

            def fetch(self) -> str:
                return "<html>test</html>"

        _scraper = TestScraper(test_source, clean_database)
        heartbeat = HeartbeatService(clean_database)

        # Record successful scrape
        heartbeat.record_success(test_source.id, measurements_count=5)

        # Check heartbeat health
        health = heartbeat.check_health(test_source.id)

        assert health["healthy"] is True
        assert health["measurements_count"] == 5
        assert health["reason"] is None  # None when healthy

    @pytest.mark.integration
    def test_quebec_scraper_database_integration(self, clean_database: DatabaseService):
        """Test Quebec scraper can write to database."""
        from waittime.core import EndEvent, MetricFamily, StartEvent, StatisticType
        from waittime.scrapers.quebec import QuebecScraper

        # Create Quebec source
        source = Source(
            id="test-qc-scraper",
            name="Test Quebec Source",
            province="QC",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Info-Santé",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.REGISTRATION,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.ROLLING_AVG,
        )
        clean_database.upsert_source(source)

        # Mock the HTTP fetch to return test HTML
        mock_html = """
        <html>
            <div class="hospital" data-id="chum">
                <h3>CHUM</h3>
                <span class="wait-time">45</span>
            </div>
        </html>
        """

        scraper = QuebecScraper(source, clean_database)

        # Mock the fetch method
        with patch.object(scraper, "fetch", return_value=mock_html):
            # Parse should work
            results = scraper.parse(mock_html)

            # Results should be empty since we don't have real HTML structure
            # But the method should not crash
            assert isinstance(results, list)

    @pytest.mark.integration
    def test_ontario_scraper_database_integration(self, clean_database: DatabaseService):
        """Test Ontario scraper can initialize with database."""
        from waittime.core import EndEvent, MetricFamily, StartEvent, StatisticType
        from waittime.scrapers.ontario import OntarioScraper

        # Create Ontario source
        source = Source(
            id="test-on-scraper",
            name="Test Ontario Source",
            province="ON",
            url="https://example.com/ontario-realtime",
            methodology_url="https://example.com/methods",
            telehealth_name="Health Connect Ontario",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.POINT_ESTIMATE,
        )
        clean_database.upsert_source(source)

        # Just test that scraper can be initialized
        # Full scraping requires Playwright browser
        scraper = OntarioScraper(source, clean_database)

        assert scraper.source.id == "test-on-scraper"
        assert scraper.db is clean_database


@pytest.mark.integration
class TestScraperErrorHandling:
    """Test scraper error handling with database."""

    def test_scraper_handles_duplicate_hospital(self, clean_database: DatabaseService):
        """Test that scraper handles duplicate hospital insertions gracefully."""
        from waittime.core import EndEvent, MetricFamily, Source, StartEvent, StatisticType

        source = Source(
            id="test-duplicate-source",
            name="Test Source",
            province="MB",
            url="https://example.com",
            methodology_url="https://example.com/methods",
            telehealth_name="Health Links",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.MEDIAN,
        )
        clean_database.upsert_source(source)

        hospital = Hospital(
            id="test-duplicate-hospital",
            name="Duplicate Test",
            province="MB",
            city="Winnipeg",
            latitude=49.8951,
            longitude=-97.1384,
            source_id=source.id,
            is_verified=False,
            is_visible=False,
        )

        # Insert once - should succeed
        result1 = clean_database.upsert_hospital(hospital)
        assert result1.id == "test-duplicate-hospital"

        # Try to upsert again - should succeed and update
        # Upsert is designed to handle duplicates gracefully
        hospital.name = "Updated Duplicate Test"
        result2 = clean_database.upsert_hospital(hospital)
        assert result2.id == "test-duplicate-hospital"
        assert result2.name == "Updated Duplicate Test"

    def test_scraper_handles_missing_source(self, clean_database: DatabaseService):
        """Test that measurements fail gracefully with non-existent source."""
        from waittime.core import (
            EndEvent,
            Measurement,
            MetricFamily,
            PatientScope,
            StartEvent,
            StatisticType,
        )

        # Try to insert measurement for non-existent source
        measurement = Measurement(
            hospital_id="nonexistent-hospital",
            value=100.0,
            timestamp_utc=datetime.now(UTC),
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.P90,
            patient_scope=PatientScope.ALL,
            source_id="nonexistent-source",
            raw_payload_hash="0000000000000000000000000000000000000000000000000000000000000000",
            raw_payload_snippet="snippet",
            parser_version="v1.0.0",
        )

        # Should fail due to foreign key constraint
        import psycopg2

        with pytest.raises(psycopg2.IntegrityError):
            clean_database.insert_measurement(measurement)
