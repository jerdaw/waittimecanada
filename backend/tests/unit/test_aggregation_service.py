"""Unit tests for AggregationService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from waittime.core import MeasurementAggregate
from waittime.services.aggregation import AggregationService


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def service(mock_db):
    """Create AggregationService with mocked database."""
    return AggregationService(mock_db)


def _make_measurement_row(
    value: float = 120.0,
    timestamp_utc: datetime | None = None,
    source_id: str = "ontario-health",
    metric_family: str = "TIME_TO_PROVIDER",
    start_event: str = "TRIAGE",
    end_event: str = "PHYSICIAN",
    statistic_type: str = "MEAN",
) -> dict:
    """Helper to create a measurement row dict as returned by DatabaseService."""
    return {
        "value": value,
        "timestamp_utc": timestamp_utc or datetime.now(UTC),
        "source_id": source_id,
        "metric_family": metric_family,
        "start_event": start_event,
        "end_event": end_event,
        "statistic_type": statistic_type,
    }


# ─────────────────────────────────────────────────────────────────
# _compute_statistics
# ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestComputeStatistics:
    """Tests for the _compute_statistics static method."""

    def test_basic_statistics(self) -> None:
        """Should compute mean, min, max, and count correctly."""
        values = [100.0, 200.0, 300.0, 400.0, 500.0]
        stats = AggregationService._compute_statistics(values)
        assert stats is not None
        assert stats["mean"] == 300.0
        assert stats["min"] == 100.0
        assert stats["max"] == 500.0
        assert stats["count"] == 5

    def test_median_and_p90_with_enough_samples(self) -> None:
        """Should compute median, p90, and std_dev when >= 3 samples."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0]
        stats = AggregationService._compute_statistics(values)
        assert stats is not None
        assert stats["median"] == 55.0
        assert stats["p90"] == 100.0  # index 9 = sorted[9]
        assert stats["std_dev"] is not None
        assert stats["std_dev"] > 0

    def test_few_samples_no_spread(self) -> None:
        """Should set median/p90/std_dev to None when < 3 samples."""
        values = [100.0, 200.0]
        stats = AggregationService._compute_statistics(values)
        assert stats is not None
        assert stats["mean"] == 150.0
        assert stats["min"] == 100.0
        assert stats["max"] == 200.0
        assert stats["count"] == 2
        assert stats["median"] is None
        assert stats["p90"] is None
        assert stats["std_dev"] is None

    def test_empty_list_returns_none(self) -> None:
        """Should return None for an empty list."""
        assert AggregationService._compute_statistics([]) is None

    def test_single_value(self) -> None:
        """Should have mean=min=max=value for a single sample."""
        stats = AggregationService._compute_statistics([42.0])
        assert stats is not None
        assert stats["mean"] == 42.0
        assert stats["min"] == 42.0
        assert stats["max"] == 42.0
        assert stats["count"] == 1
        assert stats["median"] is None

    def test_exactly_three_samples(self) -> None:
        """Three samples is the threshold for computing spread statistics."""
        values = [10.0, 20.0, 30.0]
        stats = AggregationService._compute_statistics(values)
        assert stats is not None
        assert stats["median"] == 20.0
        assert stats["std_dev"] is not None
        assert stats["p90"] is not None

    def test_identical_values(self) -> None:
        """Identical values should produce std_dev=0."""
        values = [50.0, 50.0, 50.0, 50.0]
        stats = AggregationService._compute_statistics(values)
        assert stats is not None
        assert stats["mean"] == 50.0
        assert stats["std_dev"] == 0.0
        assert stats["median"] == 50.0


# ─────────────────────────────────────────────────────────────────
# aggregate_period / aggregate_hourly / daily / weekly / monthly
# ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestAggregatePeriod:
    """Tests for period aggregation methods."""

    def test_aggregate_hourly_with_data(self, service, mock_db) -> None:
        """Should return a valid aggregate when measurements exist."""
        hour_start = datetime(2026, 2, 6, 14, 0, 0, tzinfo=UTC)
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=100.0),
            _make_measurement_row(value=200.0),
            _make_measurement_row(value=300.0),
        ]

        result = service.aggregate_hourly("ca-on-test", hour_start)

        assert result is not None
        assert result.hospital_id == "ca-on-test"
        assert result.period_type == "hourly"
        assert result.period_start == hour_start
        assert result.period_end == hour_start + timedelta(hours=1)
        assert result.mean_value == 200.0
        assert result.min_value == 100.0
        assert result.max_value == 300.0
        assert result.sample_count == 3
        assert result.source_id == "ontario-health"
        assert result.metric_family == "TIME_TO_PROVIDER"

    def test_aggregate_hourly_no_data(self, service, mock_db) -> None:
        """Should return None when no measurements exist."""
        mock_db.get_measurements_in_range.return_value = []
        result = service.aggregate_hourly("ca-on-test", datetime(2026, 2, 6, 14, 0, tzinfo=UTC))
        assert result is None

    def test_aggregate_daily_window(self, service, mock_db) -> None:
        """Should query the correct 24-hour window."""
        day_start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=150.0),
        ]

        result = service.aggregate_daily("ca-on-test", day_start)

        mock_db.get_measurements_in_range.assert_called_once_with(
            "ca-on-test", day_start, day_start + timedelta(days=1)
        )
        assert result is not None
        assert result.period_type == "daily"

    def test_aggregate_weekly_window(self, service, mock_db) -> None:
        """Should query the correct 7-day window."""
        week_start = datetime(2026, 2, 2, 0, 0, 0, tzinfo=UTC)  # Monday
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=180.0),
            _make_measurement_row(value=220.0),
            _make_measurement_row(value=200.0),
        ]

        result = service.aggregate_weekly("ca-on-test", week_start)

        mock_db.get_measurements_in_range.assert_called_once_with(
            "ca-on-test", week_start, week_start + timedelta(weeks=1)
        )
        assert result is not None
        assert result.period_type == "weekly"

    def test_aggregate_monthly_window(self, service, mock_db) -> None:
        """Should query the correct calendar month window."""
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=160.0),
        ]

        result = service.aggregate_monthly("ca-on-test", 2026, 2)

        expected_start = datetime(2026, 2, 1, 0, 0, 0, tzinfo=UTC)
        expected_end = datetime(2026, 3, 1, 0, 0, 0, tzinfo=UTC)
        mock_db.get_measurements_in_range.assert_called_once_with(
            "ca-on-test", expected_start, expected_end
        )
        assert result is not None
        assert result.period_type == "monthly"

    def test_aggregate_monthly_leap_year(self, service, mock_db) -> None:
        """February in a leap year should span 29 days."""
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=100.0),
        ]

        _result = service.aggregate_monthly("ca-on-test", 2028, 2)

        expected_start = datetime(2028, 2, 1, 0, 0, 0, tzinfo=UTC)
        expected_end = datetime(2028, 3, 1, 0, 0, 0, tzinfo=UTC)
        mock_db.get_measurements_in_range.assert_called_once_with(
            "ca-on-test", expected_start, expected_end
        )

    def test_ontology_from_first_measurement(self, service, mock_db) -> None:
        """Should use ontology tags from the first measurement in the window."""
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(
                value=100.0,
                metric_family="TOTAL_LOS",
                start_event="DOOR",
                end_event="DISCHARGE",
                statistic_type="P90",
            ),
            _make_measurement_row(value=200.0),
        ]

        result = service.aggregate_hourly(
            "ca-on-test", datetime(2026, 2, 6, 14, 0, tzinfo=UTC)
        )

        assert result is not None
        assert result.metric_family == "TOTAL_LOS"
        assert result.start_event == "DOOR"
        assert result.end_event == "DISCHARGE"
        assert result.statistic_type == "P90"


# ─────────────────────────────────────────────────────────────────
# save_aggregate
# ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestSaveAggregate:
    """Tests for saving aggregates."""

    def _make_test_aggregate(self) -> MeasurementAggregate:
        now = datetime.now(UTC)
        return MeasurementAggregate(
            hospital_id="ca-on-test",
            source_id="ontario-health",
            period_type="daily",
            period_start=now.replace(hour=0, minute=0, second=0, microsecond=0),
            period_end=now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
            mean_value=150.0,
            median_value=140.0,
            p90_value=200.0,
            min_value=80.0,
            max_value=250.0,
            std_dev=45.0,
            sample_count=24,
            metric_family="TIME_TO_PROVIDER",
            start_event="TRIAGE",
            end_event="PHYSICIAN",
            statistic_type="MEAN",
        )

    def test_save_new_aggregate(self, service, mock_db) -> None:
        """Should delegate to db.insert_aggregate and return True on success."""
        mock_db.insert_aggregate.return_value = True
        agg = self._make_test_aggregate()

        result = service.save_aggregate(agg)

        assert result is True
        mock_db.insert_aggregate.assert_called_once_with(agg)

    def test_save_duplicate_returns_false(self, service, mock_db) -> None:
        """Should return False when aggregate already exists."""
        mock_db.insert_aggregate.return_value = False
        agg = self._make_test_aggregate()

        result = service.save_aggregate(agg)

        assert result is False


# ─────────────────────────────────────────────────────────────────
# _generate_periods
# ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestGeneratePeriods:
    """Tests for period generation logic."""

    def test_hourly_periods(self) -> None:
        """Should generate correct hourly boundaries."""
        start = datetime(2026, 2, 6, 10, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 6, 13, 0, 0, tzinfo=UTC)
        periods = AggregationService._generate_periods("hourly", start, end)
        assert len(periods) == 3
        assert periods[0] == (
            datetime(2026, 2, 6, 10, 0, tzinfo=UTC),
            datetime(2026, 2, 6, 11, 0, tzinfo=UTC),
        )
        assert periods[2] == (
            datetime(2026, 2, 6, 12, 0, tzinfo=UTC),
            datetime(2026, 2, 6, 13, 0, tzinfo=UTC),
        )

    def test_daily_periods(self) -> None:
        """Should generate correct daily boundaries."""
        start = datetime(2026, 2, 4, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)
        periods = AggregationService._generate_periods("daily", start, end)
        assert len(periods) == 3

    def test_weekly_periods_aligned_to_monday(self) -> None:
        """Should align weekly periods to Monday."""
        # 2026-02-06 is a Friday
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 20, 0, 0, 0, tzinfo=UTC)
        periods = AggregationService._generate_periods("weekly", start, end)
        # Should align back to Monday Feb 2, then generate weeks
        for period_start, _ in periods:
            assert period_start.weekday() == 0  # Monday

    def test_monthly_periods(self) -> None:
        """Should generate correct monthly boundaries."""
        start = datetime(2026, 1, 1, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 4, 1, 0, 0, 0, tzinfo=UTC)
        periods = AggregationService._generate_periods("monthly", start, end)
        assert len(periods) == 3
        assert periods[0][0] == datetime(2026, 1, 1, tzinfo=UTC)
        assert periods[1][0] == datetime(2026, 2, 1, tzinfo=UTC)
        assert periods[2][0] == datetime(2026, 3, 1, tzinfo=UTC)

    def test_empty_range(self) -> None:
        """Should return empty list if start >= end."""
        start = datetime(2026, 2, 6, 14, 0, tzinfo=UTC)
        periods = AggregationService._generate_periods("hourly", start, start)
        assert periods == []

    def test_hourly_aligns_to_hour(self) -> None:
        """Should truncate start to the hour boundary."""
        start = datetime(2026, 2, 6, 10, 35, 22, tzinfo=UTC)
        end = datetime(2026, 2, 6, 12, 0, 0, tzinfo=UTC)
        periods = AggregationService._generate_periods("hourly", start, end)
        assert periods[0][0] == datetime(2026, 2, 6, 10, 0, tzinfo=UTC)


# ─────────────────────────────────────────────────────────────────
# backfill
# ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestBackfill:
    """Tests for the backfill method."""

    def test_backfill_single_hospital(self, service, mock_db) -> None:
        """Should process only the specified hospital."""
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)

        mock_db.get_existing_aggregate_periods.return_value = set()
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=100.0),
            _make_measurement_row(value=200.0),
            _make_measurement_row(value=300.0),
        ]
        mock_db.insert_aggregate.return_value = True

        counts = service.backfill(
            hospital_id="ca-on-test",
            start_date=start,
            end_date=end,
            period_types=["daily"],
        )

        assert counts["daily"] == 1
        # Should NOT have called get_all_hospital_ids
        mock_db.get_all_hospital_ids.assert_not_called()

    def test_backfill_all_hospitals(self, service, mock_db) -> None:
        """Should process all visible hospitals when hospital_id is None."""
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)

        mock_db.get_all_hospital_ids.return_value = ["ca-on-a", "ca-on-b"]
        mock_db.get_existing_aggregate_periods.return_value = set()
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=150.0),
        ]
        mock_db.insert_aggregate.return_value = True

        counts = service.backfill(
            start_date=start,
            end_date=end,
            period_types=["daily"],
        )

        assert counts["daily"] == 2
        mock_db.get_all_hospital_ids.assert_called_once_with(visible_only=True)

    def test_backfill_skips_existing(self, service, mock_db) -> None:
        """Should skip periods that already have aggregates."""
        start = datetime(2026, 2, 5, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)

        # Feb 5 already exists, Feb 6 does not
        mock_db.get_existing_aggregate_periods.return_value = {
            datetime(2026, 2, 5, 0, 0, 0, tzinfo=UTC),
        }
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=100.0),
        ]
        mock_db.insert_aggregate.return_value = True

        counts = service.backfill(
            hospital_id="ca-on-test",
            start_date=start,
            end_date=end,
            period_types=["daily"],
        )

        # Only Feb 6 should be computed
        assert counts["daily"] == 1

    def test_backfill_dry_run(self, service, mock_db) -> None:
        """Dry run should count but not save."""
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)

        mock_db.get_existing_aggregate_periods.return_value = set()
        mock_db.get_measurements_in_range.return_value = [
            _make_measurement_row(value=100.0),
        ]

        counts = service.backfill(
            hospital_id="ca-on-test",
            start_date=start,
            end_date=end,
            period_types=["daily"],
            dry_run=True,
        )

        assert counts["daily"] == 1
        mock_db.insert_aggregate.assert_not_called()

    def test_backfill_skips_empty_periods(self, service, mock_db) -> None:
        """Should not count periods with no measurements."""
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 7, 0, 0, 0, tzinfo=UTC)

        mock_db.get_existing_aggregate_periods.return_value = set()
        mock_db.get_measurements_in_range.return_value = []

        counts = service.backfill(
            hospital_id="ca-on-test",
            start_date=start,
            end_date=end,
            period_types=["daily"],
        )

        assert counts["daily"] == 0
        mock_db.insert_aggregate.assert_not_called()

    def test_backfill_defaults_to_all_period_types(self, service, mock_db) -> None:
        """Should compute all four period types when none specified."""
        start = datetime(2026, 2, 6, 0, 0, 0, tzinfo=UTC)
        end = datetime(2026, 2, 6, 1, 0, 0, tzinfo=UTC)

        mock_db.get_existing_aggregate_periods.return_value = set()
        mock_db.get_measurements_in_range.return_value = []

        counts = service.backfill(hospital_id="ca-on-test", start_date=start, end_date=end)

        assert set(counts.keys()) == {"hourly", "daily", "weekly", "monthly"}


# ─────────────────────────────────────────────────────────────────
# get_aggregates / get_latest_aggregate
# ─────────────────────────────────────────────────────────────────


@pytest.mark.unit
class TestQueryAggregates:
    """Tests for aggregate query methods."""

    def test_get_aggregates_delegates_to_db(self, service, mock_db) -> None:
        """Should pass through to db.get_aggregates."""
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 2, 1, tzinfo=UTC)
        mock_db.get_aggregates.return_value = []

        result = service.get_aggregates("ca-on-test", "daily", start, end)

        mock_db.get_aggregates.assert_called_once_with("ca-on-test", "daily", start, end)
        assert result == []

    def test_get_latest_aggregate_returns_last(self, service, mock_db) -> None:
        """Should return the last aggregate from the DB results."""
        now = datetime.now(UTC)
        agg = MeasurementAggregate(
            hospital_id="ca-on-test",
            source_id="ontario-health",
            period_type="daily",
            period_start=now.replace(hour=0, minute=0, second=0, microsecond=0),
            period_end=now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
            mean_value=120.0,
            min_value=80.0,
            max_value=200.0,
            sample_count=10,
            metric_family="TIME_TO_PROVIDER",
            start_event="TRIAGE",
            end_event="PHYSICIAN",
            statistic_type="MEAN",
        )
        mock_db.get_aggregates.return_value = [agg]

        result = service.get_latest_aggregate("ca-on-test")

        assert result is not None
        assert result.mean_value == 120.0

    def test_get_latest_aggregate_no_data(self, service, mock_db) -> None:
        """Should return None when no aggregates exist."""
        mock_db.get_aggregates.return_value = []

        result = service.get_latest_aggregate("ca-on-test")

        assert result is None
