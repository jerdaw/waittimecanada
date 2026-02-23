"""Tests for TemporalPatternService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from waittime.core import MeasurementAggregate
from waittime.services.patterns import TemporalPatternService


@pytest.fixture
def mock_db() -> Mock:
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def service(mock_db: Mock) -> TemporalPatternService:
    """Create TemporalPatternService with mock database."""
    mock_hospital = Mock()
    mock_hospital.name = "Test Hospital"
    mock_db.get_hospital.return_value = mock_hospital
    return TemporalPatternService(mock_db)


def _aggregate(
    period_type: str, period_start: datetime, mean: float, sample_count: int
) -> MeasurementAggregate:
    """Create aggregate test fixture."""
    duration_by_period = {
        "hourly": timedelta(hours=1),
        "daily": timedelta(days=1),
        "weekly": timedelta(days=7),
        "monthly": timedelta(days=31),
    }
    return MeasurementAggregate(
        hospital_id="ca-on-test",
        source_id="ontario-health",
        period_type=period_type,
        period_start=period_start,
        period_end=period_start + duration_by_period.get(period_type, timedelta(days=1)),
        mean_value=mean,
        median_value=mean,
        p90_value=mean,
        min_value=mean,
        max_value=mean,
        std_dev=0.0,
        sample_count=sample_count,
        metric_family="TIME_TO_PROVIDER",
        start_event="TRIAGE",
        end_event="PHYSICIAN",
        statistic_type="P90",
    )


@pytest.mark.unit
class TestTemporalPatternService:
    """Unit tests for temporal pattern computations."""

    def test_hour_of_day_24_entries(self, service: TemporalPatternService, mock_db: Mock) -> None:
        """Hour-of-day output should always contain 24 buckets."""
        mock_db.get_aggregates.return_value = [
            _aggregate("hourly", datetime(2026, 2, 5, 2, tzinfo=UTC), 90.0, 10),
            _aggregate("hourly", datetime(2026, 2, 5, 14, tzinfo=UTC), 180.0, 12),
        ]

        result = service.hour_of_day_pattern("ca-on-test")

        assert result["pattern_type"] == "hour_of_day"
        assert len(result["patterns"]) == 24
        assert result["patterns"][2]["mean"] == 90.0
        assert result["patterns"][14]["mean"] == 180.0
        assert result["patterns"][7]["sample_count"] == 0

    def test_peak_and_quiet_identification(
        self, service: TemporalPatternService, mock_db: Mock
    ) -> None:
        """Service should identify peak and quietest hours correctly."""
        mock_db.get_aggregates.return_value = [
            _aggregate("hourly", datetime(2026, 2, 5, 4, tzinfo=UTC), 70.0, 9),
            _aggregate("hourly", datetime(2026, 2, 5, 15, tzinfo=UTC), 175.0, 15),
        ]

        result = service.hour_of_day_pattern("ca-on-test")

        assert result["insights"]["peak_hour"] == 15
        assert result["insights"]["quietest_hour"] == 4
        assert result["insights"]["peak_vs_quiet_ratio"] == 2.5

    def test_day_of_week_7_entries(self, service: TemporalPatternService, mock_db: Mock) -> None:
        """Day-of-week output should always contain seven rows."""
        mock_db.get_aggregates.return_value = [
            _aggregate("daily", datetime(2026, 2, 2, tzinfo=UTC), 100.0, 20),  # Monday
            _aggregate("daily", datetime(2026, 2, 8, tzinfo=UTC), 150.0, 20),  # Sunday
        ]

        result = service.day_of_week_pattern("ca-on-test")

        assert result["pattern_type"] == "day_of_week"
        assert len(result["patterns"]) == 7
        assert result["patterns"][0]["day"] == "Monday"
        assert result["patterns"][6]["day"] == "Sunday"

    def test_weekend_vs_weekday_ratio(self, service: TemporalPatternService, mock_db: Mock) -> None:
        """Weekend/weekday ratio should be computed from populated buckets."""
        mock_db.get_aggregates.return_value = [
            _aggregate("daily", datetime(2026, 2, 3, tzinfo=UTC), 100.0, 20),  # Tuesday
            _aggregate("daily", datetime(2026, 2, 6, tzinfo=UTC), 100.0, 20),  # Friday
            _aggregate("daily", datetime(2026, 2, 8, tzinfo=UTC), 125.0, 20),  # Sunday
        ]

        result = service.day_of_week_pattern("ca-on-test")

        assert result["insights"]["weekend_vs_weekday_ratio"] == 1.25

    def test_monthly_trend_chronological(
        self, service: TemporalPatternService, mock_db: Mock
    ) -> None:
        """Monthly output should be sorted chronologically and include trend summary."""
        mock_db.get_aggregates.return_value = [
            _aggregate("monthly", datetime(2026, 3, 1, tzinfo=UTC), 120.0, 500),
            _aggregate("monthly", datetime(2026, 1, 1, tzinfo=UTC), 100.0, 400),
            _aggregate("monthly", datetime(2026, 2, 1, tzinfo=UTC), 110.0, 450),
        ]

        result = service.monthly_trend("ca-on-test")

        assert result["pattern_type"] == "monthly"
        assert [row["month"] for row in result["patterns"]] == ["2026-01", "2026-02", "2026-03"]
        assert result["insights"]["direction"] == "worsening"
        assert result["insights"]["change_percent"] == 20.0

    def test_insufficient_data(self, service: TemporalPatternService, mock_db: Mock) -> None:
        """Should gracefully return empty insights when there is insufficient data."""
        mock_db.get_aggregates.return_value = []

        hour_result = service.hour_of_day_pattern("ca-on-test")
        day_result = service.day_of_week_pattern("ca-on-test")
        month_result = service.monthly_trend("ca-on-test")

        assert hour_result["insights"]["peak_hour"] is None
        assert day_result["insights"]["worst_day"] is None
        assert month_result["insights"]["direction"] == "stable"
