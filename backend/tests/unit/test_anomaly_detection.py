"""Tests for AnomalyDetectionService.

Covers z-score detection, IQR detection, insufficient data handling,
batch processing, and scraper integration.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest
from waittime.services.anomaly_detection import AnomalyDetectionService


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def service(mock_db):
    """Create an AnomalyDetectionService with mock DB."""
    return AnomalyDetectionService(mock_db)


def _make_baseline(mean: float, std: float, count: int) -> list[dict]:
    """Create mock measurement rows with controlled distribution.

    Generates values evenly spread around the mean.
    """
    import random

    random.seed(42)
    values = [mean + random.gauss(0, std) for _ in range(count)]
    base_time = datetime(2026, 2, 1, tzinfo=UTC)
    return [
        {"value": v, "timestamp_utc": base_time + timedelta(hours=i)} for i, v in enumerate(values)
    ]


def _make_uniform_baseline(value: float, count: int) -> list[dict]:
    """Create baseline with identical values (zero std)."""
    base_time = datetime(2026, 2, 1, tzinfo=UTC)
    return [{"value": value, "timestamp_utc": base_time + timedelta(hours=i)} for i in range(count)]


class TestZScore:
    """Tests for z-score based anomaly detection."""

    @pytest.mark.unit
    def test_normal_value_not_anomalous(self, service, mock_db):
        """Value within 1 std dev should not be flagged."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 65.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is False

    @pytest.mark.unit
    def test_high_outlier_flagged(self, service, mock_db):
        """Value >3 std dev above mean should be flagged."""
        # Mean ~60, std ~10. Value of 200 is way outside.
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 200.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is True
        assert result["reason"] is not None
        assert "Z-score" in result["reason"] or "IQR" in result["reason"]
        assert result["details"] is not None
        assert result["details"]["value"] == 200.0

    @pytest.mark.unit
    def test_low_outlier_flagged(self, service, mock_db):
        """Value >3 std dev below mean should be flagged."""
        baseline = _make_baseline(mean=120.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 5.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is True
        assert result["reason"] is not None
        assert "below" in result["reason"].lower() or "IQR" in result["reason"]

    @pytest.mark.unit
    def test_z_score_static_method(self):
        """Direct test of _compute_z_score."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]
        # mean = 30, stdev ≈ 15.81
        z = AnomalyDetectionService._compute_z_score(30.0, values)
        assert z is not None
        assert abs(z) < 0.01  # Should be ~0

        z_high = AnomalyDetectionService._compute_z_score(100.0, values)
        assert z_high is not None
        assert z_high > 3.0  # Should be a large positive

    @pytest.mark.unit
    def test_z_score_too_few_values(self):
        """z-score returns None with fewer than 3 values."""
        z = AnomalyDetectionService._compute_z_score(50.0, [10.0, 20.0])
        assert z is None

    @pytest.mark.unit
    def test_zero_std_dev(self, service, mock_db):
        """All same values, new same value = not anomalous."""
        baseline = _make_uniform_baseline(60.0, 30)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 60.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is False


class TestIQR:
    """Tests for IQR-based anomaly detection."""

    @pytest.mark.unit
    def test_iqr_bounds_normal(self, service, mock_db):
        """Value within IQR bounds should not be flagged."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 60.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is False

    @pytest.mark.unit
    def test_iqr_static_method(self):
        """Direct test of _compute_iqr_bounds."""
        values = list(range(1, 101))  # 1-100
        bounds = AnomalyDetectionService._compute_iqr_bounds(values)
        assert bounds is not None
        lower, upper = bounds
        assert lower < 1  # Q1 - 1.5*IQR should be < min
        assert upper > 100  # Q3 + 1.5*IQR should be > max for uniform

    @pytest.mark.unit
    def test_iqr_too_few_values(self):
        """IQR returns None with fewer than 4 values."""
        bounds = AnomalyDetectionService._compute_iqr_bounds([1.0, 2.0, 3.0])
        assert bounds is None


class TestInsufficientData:
    """Tests for handling insufficient historical data."""

    @pytest.mark.unit
    def test_fewer_than_min_samples(self, service, mock_db):
        """<20 samples should return not anomalous (safe default)."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=10)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 200.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is False
        assert result["reason"] is None
        assert result["details"] is None

    @pytest.mark.unit
    def test_no_historical_data(self, service, mock_db):
        """No historical data should return not anomalous."""
        mock_db.get_measurements_in_range.return_value = []

        result = service.check_measurement("ca-on-test", 999.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is False


class TestBatch:
    """Tests for check_batch()."""

    @pytest.mark.unit
    def test_batch_same_hospital_loads_once(self, service, mock_db):
        """Batch loading should only query DB once per hospital."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        ts = datetime(2026, 2, 5, tzinfo=UTC)
        measurements = [
            {"hospital_id": "h-1", "value": 60.0, "timestamp": ts},
            {"hospital_id": "h-1", "value": 65.0, "timestamp": ts},
            {"hospital_id": "h-1", "value": 55.0, "timestamp": ts},
        ]

        results = service.check_batch(measurements)

        assert len(results) == 3
        # Should only have called get_measurements_in_range once for h-1
        assert mock_db.get_measurements_in_range.call_count == 1

    @pytest.mark.unit
    def test_batch_multiple_hospitals(self, service, mock_db):
        """Batch with different hospitals loads baseline for each."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        ts = datetime(2026, 2, 5, tzinfo=UTC)
        measurements = [
            {"hospital_id": "h-1", "value": 60.0, "timestamp": ts},
            {"hospital_id": "h-2", "value": 65.0, "timestamp": ts},
        ]

        results = service.check_batch(measurements)

        assert len(results) == 2
        assert mock_db.get_measurements_in_range.call_count == 2

    @pytest.mark.unit
    def test_batch_detects_anomaly(self, service, mock_db):
        """Batch correctly flags anomalous measurements."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        ts = datetime(2026, 2, 5, tzinfo=UTC)
        measurements = [
            {"hospital_id": "h-1", "value": 60.0, "timestamp": ts},
            {"hospital_id": "h-1", "value": 500.0, "timestamp": ts},  # outlier
        ]

        results = service.check_batch(measurements)

        assert results[0]["is_anomaly"] is False
        assert results[1]["is_anomaly"] is True


class TestAnomalyReason:
    """Tests for anomaly reason format."""

    @pytest.mark.unit
    def test_reason_is_human_readable(self, service, mock_db):
        """Anomaly reason should be a readable string."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 300.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["is_anomaly"] is True
        reason = result["reason"]
        assert isinstance(reason, str)
        assert len(reason) > 10  # Non-trivial explanation

    @pytest.mark.unit
    def test_details_include_baseline_stats(self, service, mock_db):
        """Details should include baseline mean, std, z-score."""
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        result = service.check_measurement("ca-on-test", 300.0, datetime(2026, 2, 5, tzinfo=UTC))

        assert result["details"] is not None
        assert "baseline_mean" in result["details"]
        assert "baseline_std" in result["details"]
        assert "z_score" in result["details"]
        assert "sample_count" in result["details"]


class TestScraperIntegration:
    """Tests for anomaly detection integration with scraper pipeline."""

    @pytest.mark.unit
    def test_scraper_flags_anomalies(self):
        """Verify BaseScraper._check_anomalies flags measurements."""
        from waittime.core import Measurement, Source
        from waittime.core.enums import (
            EndEvent,
            MetricFamily,
            StartEvent,
            StatisticType,
        )
        from waittime.scrapers.base import BaseScraper

        mock_db = Mock()
        source = Source(
            id="test-src",
            name="Test",
            province="ON",
            url="https://example.com",
            telehealth_name="Health811",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.POINT_ESTIMATE,
        )

        # Create a concrete scraper for testing
        class TestScraper(BaseScraper):
            def parse(self, html: str) -> list[Measurement]:
                return []

        scraper = TestScraper(source=source, db=mock_db)

        # Create a measurement to check
        measurement = Measurement(
            hospital_id="ca-on-test",
            value=300.0,
            source_id="test-src",
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.POINT_ESTIMATE,
            raw_payload_hash="a" * 64,
            parser_version="v1.0",
        )

        # Mock the anomaly service to return anomaly
        baseline = _make_baseline(mean=60.0, std=10.0, count=50)
        mock_db.get_measurements_in_range.return_value = baseline

        # Call _check_anomalies directly
        scraper._check_anomalies([measurement])

        # Measurement should be flagged
        assert measurement.is_anomaly is True
        assert measurement.anomaly_reason is not None

    @pytest.mark.unit
    def test_scraper_anomaly_check_failure_does_not_crash(self):
        """Anomaly detection failure should not break the scraper."""
        from waittime.core import Measurement, Source
        from waittime.core.enums import (
            EndEvent,
            MetricFamily,
            StartEvent,
            StatisticType,
        )
        from waittime.scrapers.base import BaseScraper

        mock_db = Mock()
        source = Source(
            id="test-src",
            name="Test",
            province="ON",
            url="https://example.com",
            telehealth_name="Health811",
            telehealth_number="811",
            default_metric_family=MetricFamily.TIME_TO_PROVIDER,
            default_start_event=StartEvent.TRIAGE,
            default_end_event=EndEvent.PHYSICIAN,
            default_statistic_type=StatisticType.POINT_ESTIMATE,
        )

        class TestScraper(BaseScraper):
            def parse(self, html: str) -> list[Measurement]:
                return []

        scraper = TestScraper(source=source, db=mock_db)

        measurement = Measurement(
            hospital_id="ca-on-test",
            value=60.0,
            source_id="test-src",
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.POINT_ESTIMATE,
            raw_payload_hash="b" * 64,
            parser_version="v1.0",
        )

        # Make DB throw an error
        mock_db.get_measurements_in_range.side_effect = RuntimeError("DB error")

        # Should not raise — anomaly failure is non-fatal
        scraper._check_anomalies([measurement])

        # Measurement should NOT be flagged (anomaly detection failed gracefully)
        assert measurement.is_anomaly is False


class TestGetRecentAnomalies:
    """Tests for get_recent_anomalies()."""

    @pytest.mark.unit
    def test_delegates_to_db(self, service, mock_db):
        """get_recent_anomalies should delegate to db."""
        mock_db.get_recent_anomalies.return_value = [
            {"hospital_id": "h-1", "value": 300.0, "anomaly_reason": "test"}
        ]

        result = service.get_recent_anomalies(source_id="src-1", days=3)

        assert len(result) == 1
        mock_db.get_recent_anomalies.assert_called_once_with(source_id="src-1", days=3)
