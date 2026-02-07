"""Service for computing and storing measurement aggregates.

Computes hourly, daily, weekly, and monthly summary statistics from raw
measurements and persists them as permanent aggregates. These aggregates
survive the 30-day raw measurement retention window, enabling longitudinal
research and long-range trend analysis.
"""

import logging
import statistics
from calendar import monthrange
from datetime import UTC, datetime, timedelta

from waittime.core import MeasurementAggregate
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class AggregationService:
    """Computes and stores permanent statistical aggregates from raw measurements."""

    MIN_SAMPLES_FOR_SPREAD = 3

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    @staticmethod
    def _compute_statistics(values: list[float]) -> dict | None:
        """Compute summary statistics from a list of measurement values.

        Returns:
            Dict with keys: mean, median, p90, min, max, std_dev, count.
            median/p90/std_dev are None if fewer than 3 samples.
            Returns None if the input list is empty.
        """
        if not values:
            return None

        result: dict = {
            "mean": statistics.mean(values),
            "min": min(values),
            "max": max(values),
            "count": len(values),
            "median": None,
            "p90": None,
            "std_dev": None,
        }

        if len(values) >= AggregationService.MIN_SAMPLES_FOR_SPREAD:
            result["median"] = statistics.median(values)
            result["std_dev"] = statistics.stdev(values)
            sorted_values = sorted(values)
            p90_index = int(len(sorted_values) * 0.9)
            result["p90"] = sorted_values[min(p90_index, len(sorted_values) - 1)]

        return result

    def aggregate_period(
        self,
        hospital_id: str,
        period_type: str,
        period_start: datetime,
        period_end: datetime,
    ) -> MeasurementAggregate | None:
        """Compute aggregate statistics for a hospital over an arbitrary time window.

        Args:
            hospital_id: Hospital to aggregate
            period_type: 'hourly', 'daily', 'weekly', or 'monthly'
            period_start: Start of the period (inclusive)
            period_end: End of the period (exclusive)

        Returns:
            MeasurementAggregate if data exists, None if no measurements in window
        """
        rows = self.db.get_measurements_in_range(hospital_id, period_start, period_end)
        if not rows:
            return None

        values = [row["value"] for row in rows]
        stats = self._compute_statistics(values)
        if stats is None:
            return None

        # Use ontology from the first measurement (denormalized snapshot)
        first = rows[0]

        return MeasurementAggregate(
            hospital_id=hospital_id,
            source_id=first["source_id"],
            period_type=period_type,
            period_start=period_start,
            period_end=period_end,
            mean_value=stats["mean"],
            median_value=stats["median"],
            p90_value=stats["p90"],
            min_value=stats["min"],
            max_value=stats["max"],
            std_dev=stats["std_dev"],
            sample_count=stats["count"],
            metric_family=first["metric_family"],
            start_event=first["start_event"],
            end_event=first["end_event"],
            statistic_type=first["statistic_type"],
        )

    def aggregate_hourly(
        self, hospital_id: str, hour_start: datetime
    ) -> MeasurementAggregate | None:
        """Compute aggregate for a single hour."""
        hour_end = hour_start + timedelta(hours=1)
        return self.aggregate_period(hospital_id, "hourly", hour_start, hour_end)

    def aggregate_daily(
        self, hospital_id: str, day_start: datetime
    ) -> MeasurementAggregate | None:
        """Compute aggregate for a full day (00:00 to next 00:00)."""
        day_end = day_start + timedelta(days=1)
        return self.aggregate_period(hospital_id, "daily", day_start, day_end)

    def aggregate_weekly(
        self, hospital_id: str, week_start: datetime
    ) -> MeasurementAggregate | None:
        """Compute aggregate for a full week (7 days from week_start)."""
        week_end = week_start + timedelta(weeks=1)
        return self.aggregate_period(hospital_id, "weekly", week_start, week_end)

    def aggregate_monthly(
        self, hospital_id: str, year: int, month: int
    ) -> MeasurementAggregate | None:
        """Compute aggregate for a full calendar month."""
        month_start = datetime(year, month, 1, tzinfo=UTC)
        days_in_month = monthrange(year, month)[1]
        month_end = month_start + timedelta(days=days_in_month)
        return self.aggregate_period(hospital_id, "monthly", month_start, month_end)

    def save_aggregate(self, aggregate: MeasurementAggregate) -> bool:
        """Save an aggregate to the database.

        Uses INSERT ... ON CONFLICT DO NOTHING to skip already-computed periods.

        Returns:
            True if inserted, False if already existed
        """
        return self.db.insert_aggregate(aggregate)

    def backfill(
        self,
        hospital_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period_types: list[str] | None = None,
        dry_run: bool = False,
    ) -> dict[str, int]:
        """Backfill missing aggregates for a hospital or all hospitals.

        Args:
            hospital_id: Specific hospital, or None for all visible hospitals
            start_date: Start of backfill range (defaults to 30 days ago)
            end_date: End of backfill range (defaults to now)
            period_types: Which periods to compute (default: all four)
            dry_run: If True, count what would be computed without saving

        Returns:
            Dict with counts per period type, e.g. {'hourly': 48, 'daily': 2, ...}
        """
        now = datetime.now(UTC)
        if start_date is None:
            start_date = now - timedelta(days=30)
        if end_date is None:
            end_date = now
        if period_types is None:
            period_types = ["hourly", "daily", "weekly", "monthly"]

        hospital_ids = (
            [hospital_id] if hospital_id else self.db.get_all_hospital_ids(visible_only=True)
        )

        counts: dict[str, int] = dict.fromkeys(period_types, 0)

        for h_id in hospital_ids:
            for period_type in period_types:
                computed = self._backfill_hospital_period(
                    h_id, period_type, start_date, end_date, dry_run
                )
                counts[period_type] += computed

        logger.info(f"Backfill complete: {counts} (dry_run={dry_run})")
        return counts

    def _backfill_hospital_period(
        self,
        hospital_id: str,
        period_type: str,
        start_date: datetime,
        end_date: datetime,
        dry_run: bool,
    ) -> int:
        """Backfill a single period type for a single hospital. Returns count of new aggregates."""
        existing = self.db.get_existing_aggregate_periods(
            hospital_id, period_type, start_date, end_date
        )

        periods = self._generate_periods(period_type, start_date, end_date)
        computed = 0

        for period_start, period_end in periods:
            if period_start in existing:
                continue

            agg = self.aggregate_period(hospital_id, period_type, period_start, period_end)
            if agg is None:
                continue

            if not dry_run:
                self.save_aggregate(agg)

            computed += 1

        return computed

    @staticmethod
    def _generate_periods(
        period_type: str, start: datetime, end: datetime
    ) -> list[tuple[datetime, datetime]]:
        """Generate (period_start, period_end) tuples covering the range."""
        periods: list[tuple[datetime, datetime]] = []

        if period_type == "hourly":
            current = start.replace(minute=0, second=0, microsecond=0)
            while current < end:
                next_period = current + timedelta(hours=1)
                periods.append((current, next_period))
                current = next_period

        elif period_type == "daily":
            current = start.replace(hour=0, minute=0, second=0, microsecond=0)
            while current < end:
                next_period = current + timedelta(days=1)
                periods.append((current, next_period))
                current = next_period

        elif period_type == "weekly":
            # Align to Monday
            current = start.replace(hour=0, minute=0, second=0, microsecond=0)
            current -= timedelta(days=current.weekday())
            while current < end:
                next_period = current + timedelta(weeks=1)
                periods.append((current, next_period))
                current = next_period

        elif period_type == "monthly":
            current = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            while current < end:
                days_in_month = monthrange(current.year, current.month)[1]
                next_period = current + timedelta(days=days_in_month)
                periods.append((current, next_period))
                current = next_period

        return periods

    def get_aggregates(
        self,
        hospital_id: str,
        period_type: str,
        start: datetime,
        end: datetime,
    ) -> list[MeasurementAggregate]:
        """Query stored aggregates for a hospital and time range."""
        return self.db.get_aggregates(hospital_id, period_type, start, end)

    def get_latest_aggregate(
        self,
        hospital_id: str,
        period_type: str = "daily",
    ) -> MeasurementAggregate | None:
        """Get the most recent aggregate for a hospital."""
        now = datetime.now(UTC)
        far_past = datetime(2020, 1, 1, tzinfo=UTC)
        results = self.db.get_aggregates(hospital_id, period_type, far_past, now)
        return results[-1] if results else None
