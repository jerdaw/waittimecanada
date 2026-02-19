"""Unit tests for MeasurementAggregate model validation."""

from datetime import UTC, datetime, timedelta

import pytest
from waittime.core import MeasurementAggregate


def _make_aggregate(**overrides: object) -> MeasurementAggregate:
    """Helper to create a valid aggregate with sensible defaults."""
    now = datetime.now(UTC)
    defaults = {
        "hospital_id": "ca-on-ottawa-civic",
        "source_id": "ontario-health",
        "period_type": "daily",
        "period_start": now.replace(hour=0, minute=0, second=0, microsecond=0),
        "period_end": (now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)),
        "mean_value": 125.5,
        "median_value": 118.0,
        "p90_value": 210.0,
        "min_value": 45.0,
        "max_value": 320.0,
        "std_dev": 52.3,
        "sample_count": 96,
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "MEAN",
    }
    defaults.update(overrides)
    return MeasurementAggregate(**defaults)


@pytest.mark.unit
class TestMeasurementAggregateCreation:
    """Tests for valid MeasurementAggregate construction."""

    def test_valid_aggregate(self) -> None:
        """An aggregate with valid fields should be accepted."""
        agg = _make_aggregate()
        assert agg.hospital_id == "ca-on-ottawa-civic"
        assert agg.mean_value == 125.5
        assert agg.sample_count == 96
        assert agg.period_type == "daily"

    def test_all_period_types_accepted(self) -> None:
        """All four valid period types should be accepted."""
        for period_type in ("hourly", "daily", "weekly", "monthly"):
            agg = _make_aggregate(period_type=period_type)
            assert agg.period_type == period_type

    def test_nullable_fields_can_be_none(self) -> None:
        """median_value, p90_value, std_dev, and created_at can all be None."""
        agg = _make_aggregate(
            median_value=None,
            p90_value=None,
            std_dev=None,
        )
        assert agg.median_value is None
        assert agg.p90_value is None
        assert agg.std_dev is None
        assert agg.created_at is None

    def test_created_at_preserved(self) -> None:
        """created_at should be preserved when provided."""
        ts = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)
        agg = _make_aggregate(created_at=ts)
        assert agg.created_at == ts

    def test_ontology_stored_as_strings(self) -> None:
        """Ontology fields are plain strings (denormalized, not enums)."""
        agg = _make_aggregate(
            metric_family="TOTAL_LOS",
            start_event="DOOR",
            end_event="DISCHARGE",
            statistic_type="P90",
        )
        assert agg.metric_family == "TOTAL_LOS"
        assert agg.start_event == "DOOR"
        assert agg.end_event == "DISCHARGE"
        assert agg.statistic_type == "P90"


@pytest.mark.unit
class TestMeasurementAggregateValidation:
    """Tests for MeasurementAggregate validation rules."""

    def test_sample_count_must_be_positive(self) -> None:
        """sample_count must be > 0."""
        with pytest.raises(ValueError, match="greater than"):
            _make_aggregate(sample_count=0)

    def test_sample_count_cannot_be_negative(self) -> None:
        """sample_count must be > 0."""
        with pytest.raises(ValueError, match="greater than"):
            _make_aggregate(sample_count=-1)

    def test_invalid_period_type_rejected(self) -> None:
        """period_type must be one of the four allowed values."""
        with pytest.raises(ValueError, match="period_type must be one of"):
            _make_aggregate(period_type="yearly")

    def test_period_end_must_be_after_start(self) -> None:
        """period_end must be strictly after period_start."""
        now = datetime.now(UTC)
        with pytest.raises(ValueError, match="period_end must be after period_start"):
            _make_aggregate(
                period_start=now,
                period_end=now,  # equal, not after
            )

    def test_period_end_before_start_rejected(self) -> None:
        """period_end before period_start should be rejected."""
        now = datetime.now(UTC)
        with pytest.raises(ValueError, match="period_end must be after period_start"):
            _make_aggregate(
                period_start=now,
                period_end=now - timedelta(hours=1),
            )

    def test_single_sample_is_valid(self) -> None:
        """An aggregate with sample_count=1 is valid (edge case)."""
        agg = _make_aggregate(
            sample_count=1,
            median_value=None,
            p90_value=None,
            std_dev=None,
        )
        assert agg.sample_count == 1


@pytest.mark.unit
class TestMeasurementAggregateHourlyPeriods:
    """Tests specific to hourly aggregate period boundaries."""

    def test_hourly_period_boundaries(self) -> None:
        """Hourly aggregate should span exactly 1 hour."""
        start = datetime(2026, 2, 6, 14, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 6, 15, 0, 0, tzinfo=UTC)
        agg = _make_aggregate(
            period_type="hourly",
            period_start=start,
            period_end=end,
        )
        assert (agg.period_end - agg.period_start).total_seconds() == 3600

    def test_daily_period_boundaries(self) -> None:
        """Daily aggregate should span exactly 24 hours."""
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)
        agg = _make_aggregate(
            period_type="daily",
            period_start=start,
            period_end=end,
        )
        assert (agg.period_end - agg.period_start).total_seconds() == 86400

    def test_weekly_period_boundaries(self) -> None:
        """Weekly aggregate should span exactly 7 days."""
        start = datetime(2026, 2, 2, 0, 0, 0, tzinfo=UTC)  # Monday
        end = datetime(2026, 2, 9, 0, 0, 0, tzinfo=UTC)  # Next Monday
        agg = _make_aggregate(
            period_type="weekly",
            period_start=start,
            period_end=end,
        )
        assert (agg.period_end - agg.period_start).days == 7
