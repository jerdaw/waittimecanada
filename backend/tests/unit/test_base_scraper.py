"""Tests for BaseScraper."""

from unittest.mock import MagicMock, Mock, patch

import pytest
from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    PatientScope,
    Source,
    StartEvent,
    StatisticType,
)
from waittime.scrapers.base import BaseScraper


class ConcreteScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""

    def parse(self, html: str) -> list[Measurement]:
        """Simple parse implementation that returns fixed measurements."""
        if not html or html == "<empty/>":
            return []

        return [
            Measurement(
                hospital_id="ca-test-hospital",
                value=120,
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.TRIAGE,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.P90,
                patient_scope=PatientScope.ALL,
                source_id="test-source",
                raw_payload_hash=self.hash_payload(html),
                raw_payload_snippet=self.snippet(html),
            )
        ]


@pytest.fixture
def test_source():
    """Create a test Source object."""
    return Source(
        id="test-source",
        name="Test Source",
        province="ON",
        url="https://example.com/data",
        telehealth_name="Test Health Link",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.TRIAGE,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.P90,
    )


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def scraper_without_db(test_source):
    """Create scraper without database."""
    return ConcreteScraper(test_source, db=None)


@pytest.fixture
def scraper_with_db(test_source, mock_db):
    """Create scraper with database."""
    return ConcreteScraper(test_source, db=mock_db)


class TestInitialization:
    """Test scraper initialization."""

    def test_initializes_without_db(self, test_source):
        """Should initialize successfully without database."""
        scraper = ConcreteScraper(test_source, db=None)

        assert scraper.source == test_source
        assert scraper.db is None
        assert scraper._heartbeat is None

    def test_initializes_with_db(self, test_source, mock_db):
        """Should initialize with database and create heartbeat service."""
        scraper = ConcreteScraper(test_source, db=mock_db)

        assert scraper.source == test_source
        assert scraper.db is mock_db
        assert scraper._heartbeat is not None

    def test_creates_http_client(self, test_source):
        """Should create HTTP client with proper configuration."""
        scraper = ConcreteScraper(test_source, db=None)

        assert scraper.client is not None
        assert "WaitTimeCanada" in scraper.client.headers["User-Agent"]


class TestContextManager:
    """Test context manager functionality."""

    def test_enter_returns_self(self, scraper_without_db):
        """__enter__ should return the scraper instance."""
        with scraper_without_db as scraper:
            assert scraper is scraper_without_db

    def test_exit_closes_client(self, scraper_without_db):
        """__exit__ should close the HTTP client."""
        with patch.object(scraper_without_db.client, "close") as mock_close:
            with scraper_without_db:
                pass
            mock_close.assert_called_once()


class TestFetch:
    """Test HTTP fetching functionality."""

    def test_fetch_uses_source_url_by_default(self, scraper_without_db):
        """Should use source.url when no URL provided."""
        mock_response = Mock()
        mock_response.text = "<html>Test</html>"

        with patch.object(scraper_without_db.client, "get", return_value=mock_response):
            result = scraper_without_db.fetch()

            scraper_without_db.client.get.assert_called_once_with("https://example.com/data")
            assert result == "<html>Test</html>"

    def test_fetch_accepts_custom_url(self, scraper_without_db):
        """Should use custom URL when provided."""
        mock_response = Mock()
        mock_response.text = "<html>Custom</html>"

        with patch.object(scraper_without_db.client, "get", return_value=mock_response):
            result = scraper_without_db.fetch("https://custom.com/endpoint")

            scraper_without_db.client.get.assert_called_once_with("https://custom.com/endpoint")
            assert result == "<html>Custom</html>"

    def test_fetch_raises_for_http_errors(self, scraper_without_db):
        """Should raise HTTP errors after retries."""
        import httpx
        from tenacity import RetryError

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=Mock(status_code=404)
        )

        with patch.object(scraper_without_db.client, "get", return_value=mock_response):
            # fetch() uses @retry, so expect RetryError after 3 attempts
            with pytest.raises(RetryError):
                scraper_without_db.fetch()


class TestHashPayload:
    """Test payload hashing functionality."""

    def test_hash_payload_returns_sha256(self, scraper_without_db):
        """Should return 64-character SHA256 hash."""
        content = "<html>Test content</html>"
        result = scraper_without_db.hash_payload(content)

        assert len(result) == 64
        assert all(c in "0123456789abcdef" for c in result)

    def test_hash_payload_is_deterministic(self, scraper_without_db):
        """Should return same hash for same content."""
        content = "<html>Test content</html>"

        hash1 = scraper_without_db.hash_payload(content)
        hash2 = scraper_without_db.hash_payload(content)

        assert hash1 == hash2

    def test_hash_payload_differs_for_different_content(self, scraper_without_db):
        """Should return different hashes for different content."""
        hash1 = scraper_without_db.hash_payload("content1")
        hash2 = scraper_without_db.hash_payload("content2")

        assert hash1 != hash2


class TestSnippet:
    """Test snippet extraction functionality."""

    def test_snippet_returns_first_n_characters(self, scraper_without_db):
        """Should return first N characters of content."""
        content = "A" * 500
        result = scraper_without_db.snippet(content, max_length=200)

        assert len(result) == 200
        assert result == "A" * 200

    def test_snippet_returns_full_content_if_shorter(self, scraper_without_db):
        """Should return full content if shorter than max_length."""
        content = "Short content"
        result = scraper_without_db.snippet(content, max_length=200)

        assert result == content
        assert len(result) < 200

    def test_snippet_default_length_is_200(self, scraper_without_db):
        """Should use 200 as default max_length."""
        content = "A" * 500
        result = scraper_without_db.snippet(content)

        assert len(result) == 200


class TestRun:
    """Test full scrape cycle."""

    def test_run_without_db_returns_measurements(self, scraper_without_db):
        """Should fetch, parse, and return measurements without saving."""
        html = "<html>Test</html>"

        with patch.object(scraper_without_db, "fetch", return_value=html):
            measurements = scraper_without_db.run(save_to_db=False)

            assert len(measurements) == 1
            assert measurements[0].value == 120

    def test_run_with_db_saves_measurements(self, scraper_with_db, mock_db):
        """Should save measurements to database when configured."""
        html = "<html>Test</html>"

        with patch.object(scraper_with_db, "fetch", return_value=html):
            measurements = scraper_with_db.run(save_to_db=True)

            mock_db.insert_measurements.assert_called_once()
            assert len(measurements) == 1

    def test_run_skips_save_when_no_measurements(self, scraper_with_db, mock_db):
        """Should not attempt to save when no measurements found."""
        html = "<empty/>"

        with patch.object(scraper_with_db, "fetch", return_value=html):
            measurements = scraper_with_db.run(save_to_db=True)

            mock_db.insert_measurements.assert_not_called()
            assert len(measurements) == 0

    def test_run_records_success_heartbeat(self, scraper_with_db):
        """Should record successful heartbeat after scrape."""
        html = "<html>Test</html>"

        with patch.object(scraper_with_db, "fetch", return_value=html):
            with patch.object(scraper_with_db._heartbeat, "record_success") as mock_success:
                _measurements = scraper_with_db.run(save_to_db=False)

                mock_success.assert_called_once_with(
                    source_id="test-source",
                    measurements_count=1,
                )

    def test_run_records_failure_heartbeat_on_error(self, scraper_with_db):
        """Should record failure heartbeat when scrape fails."""
        with patch.object(scraper_with_db, "fetch", side_effect=Exception("Network error")):
            with patch.object(scraper_with_db._heartbeat, "record_failure") as mock_failure:
                with pytest.raises(Exception, match="Network error"):
                    scraper_with_db.run()

                mock_failure.assert_called_once_with(
                    source_id="test-source",
                    error_message="Network error",
                )

    def test_run_without_heartbeat_service_succeeds(self, scraper_without_db):
        """Should complete successfully even without heartbeat service."""
        html = "<html>Test</html>"

        with patch.object(scraper_without_db, "fetch", return_value=html):
            measurements = scraper_without_db.run(save_to_db=False)

            assert len(measurements) == 1
            # Should not crash even though _heartbeat is None

    def test_run_with_save_false_skips_db_insert(self, scraper_with_db, mock_db):
        """Should skip database insert when save_to_db=False."""
        html = "<html>Test</html>"

        with patch.object(scraper_with_db, "fetch", return_value=html):
            measurements = scraper_with_db.run(save_to_db=False)

            mock_db.insert_measurements.assert_not_called()
            assert len(measurements) == 1

    def test_run_calls_before_save_hook_when_saving(self, scraper_with_db):
        """Should execute before_save callback before persisting measurements."""
        html = "<html>Test</html>"
        hook = MagicMock()

        with patch.object(scraper_with_db, "fetch", return_value=html):
            scraper_with_db.run(save_to_db=True, before_save=hook)

        hook.assert_called_once()
        call_arg_measurements = hook.call_args.args[0]
        assert len(call_arg_measurements) == 1
        assert call_arg_measurements[0].hospital_id == "ca-test-hospital"
