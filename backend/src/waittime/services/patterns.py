"""Service for computing temporal wait time patterns."""

import logging
import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from waittime.core import MeasurementAggregate
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class TemporalPatternService:
    """Analyzes temporal patterns in wait time aggregates."""

    DAYS_OF_WEEK = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    def hour_of_day_pattern(self, hospital_id: str, lookback_days: int = 30) -> dict[str, Any]:
        """Compute average wait time by hour of day using hourly aggregates."""
        if lookback_days <= 0:
            raise ValueError("lookback_days must be > 0")

        hospital_name = self._get_hospital_name(hospital_id)
        if hospital_name is None:
            raise ValueError(f"Hospital not found: {hospital_id}")

        end = datetime.now(UTC)
        start = end - timedelta(days=lookback_days)

        aggregates = self.db.get_aggregates(
            hospital_id=hospital_id,
            period_type="hourly",
            start=start,
            end=end,
        )

        buckets: dict[int, list[MeasurementAggregate]] = defaultdict(list)
        for aggregate in aggregates:
            buckets[aggregate.period_start.hour].append(aggregate)

        patterns: list[dict[str, Any]] = []
        for hour in range(24):
            patterns.append(
                {
                    "hour": hour,
                    **self._bucket_stats(buckets.get(hour, [])),
                }
            )

        populated = [row for row in patterns if row["mean"] is not None]
        sample_count = sum(row["sample_count"] for row in patterns)

        insights: dict[str, Any]
        if not populated:
            insights = {
                "peak_hour": None,
                "quietest_hour": None,
                "peak_mean": None,
                "quietest_mean": None,
                "peak_vs_quiet_ratio": None,
            }
        else:
            peak = max(populated, key=lambda row: float(row["mean"]))
            quiet = min(populated, key=lambda row: float(row["mean"]))
            quiet_mean = float(quiet["mean"])
            peak_mean = float(peak["mean"])
            insights = {
                "peak_hour": peak["hour"],
                "quietest_hour": quiet["hour"],
                "peak_mean": peak_mean,
                "quietest_mean": quiet_mean,
                "peak_vs_quiet_ratio": round(peak_mean / quiet_mean, 2) if quiet_mean > 0 else None,
            }

        return {
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "pattern_type": "hour_of_day",
            "data_period": {
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
            },
            "sample_count": sample_count,
            "patterns": patterns,
            "insights": insights,
        }

    def day_of_week_pattern(self, hospital_id: str, lookback_days: int = 90) -> dict[str, Any]:
        """Compute average wait time by day of week using daily aggregates."""
        if lookback_days <= 0:
            raise ValueError("lookback_days must be > 0")

        hospital_name = self._get_hospital_name(hospital_id)
        if hospital_name is None:
            raise ValueError(f"Hospital not found: {hospital_id}")

        end = datetime.now(UTC)
        start = end - timedelta(days=lookback_days)

        aggregates = self.db.get_aggregates(
            hospital_id=hospital_id,
            period_type="daily",
            start=start,
            end=end,
        )

        buckets: dict[int, list[MeasurementAggregate]] = defaultdict(list)
        for aggregate in aggregates:
            buckets[aggregate.period_start.weekday()].append(aggregate)

        patterns: list[dict[str, Any]] = []
        for day_index, day_name in enumerate(self.DAYS_OF_WEEK):
            patterns.append(
                {
                    "day": day_name,
                    "day_index": day_index,
                    **self._bucket_stats(buckets.get(day_index, [])),
                }
            )

        populated = [row for row in patterns if row["mean"] is not None]
        sample_count = sum(row["sample_count"] for row in patterns)

        if not populated:
            insights = {
                "worst_day": None,
                "best_day": None,
                "weekend_vs_weekday_ratio": None,
            }
        else:
            worst_day = max(populated, key=lambda row: float(row["mean"]))
            best_day = min(populated, key=lambda row: float(row["mean"]))

            weekend_means = [
                float(row["mean"])
                for row in patterns
                if row["day_index"] in {5, 6} and row["mean"] is not None
            ]
            weekday_means = [
                float(row["mean"])
                for row in patterns
                if row["day_index"] in {0, 1, 2, 3, 4} and row["mean"] is not None
            ]

            insights = {
                "worst_day": str(worst_day["day"]),
                "best_day": str(best_day["day"]),
                "weekend_vs_weekday_ratio": self._ratio(
                    statistics.mean(weekend_means) if weekend_means else None,
                    statistics.mean(weekday_means) if weekday_means else None,
                ),
            }

        return {
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "pattern_type": "day_of_week",
            "data_period": {
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
            },
            "sample_count": sample_count,
            "patterns": patterns,
            "insights": insights,
        }

    def monthly_trend(self, hospital_id: str, lookback_months: int = 12) -> dict[str, Any]:
        """Compute monthly averages and trend direction using monthly aggregates."""
        if lookback_months <= 0:
            raise ValueError("lookback_months must be > 0")

        hospital_name = self._get_hospital_name(hospital_id)
        if hospital_name is None:
            raise ValueError(f"Hospital not found: {hospital_id}")

        end = datetime.now(UTC)
        start = end - timedelta(days=lookback_months * 31)

        aggregates = self.db.get_aggregates(
            hospital_id=hospital_id,
            period_type="monthly",
            start=start,
            end=end,
        )
        aggregates.sort(key=lambda aggregate: aggregate.period_start)

        patterns = [
            {
                "month": aggregate.period_start.strftime("%Y-%m"),
                "mean": round(float(aggregate.mean_value), 1),
                "median": (
                    round(float(aggregate.median_value), 1)
                    if aggregate.median_value is not None
                    else None
                ),
                "sample_count": int(aggregate.sample_count),
            }
            for aggregate in aggregates
        ]

        sample_count = sum(row["sample_count"] for row in patterns)

        populated = [row for row in patterns if row["mean"] is not None]
        if len(populated) < 2:
            insights = {
                "direction": "stable",
                "change_percent": 0.0,
                "start_mean": populated[0]["mean"] if populated else None,
                "end_mean": populated[0]["mean"] if populated else None,
            }
        else:
            start_mean = float(populated[0]["mean"])
            end_mean = float(populated[-1]["mean"])
            change_percent = self._percent_change(end_mean, start_mean)
            direction = "stable"
            if change_percent < -5:
                direction = "improving"
            elif change_percent > 5:
                direction = "worsening"

            insights = {
                "direction": direction,
                "change_percent": round(change_percent, 1),
                "start_mean": start_mean,
                "end_mean": end_mean,
            }

        return {
            "hospital_id": hospital_id,
            "hospital_name": hospital_name,
            "pattern_type": "monthly",
            "data_period": {
                "start": start.date().isoformat(),
                "end": end.date().isoformat(),
            },
            "sample_count": sample_count,
            "patterns": patterns,
            "insights": insights,
        }

    def _get_hospital_name(self, hospital_id: str) -> str | None:
        hospital = self.db.get_hospital(hospital_id)
        if hospital is None:
            return None
        return hospital.name

    @staticmethod
    def _bucket_stats(aggregates: list[MeasurementAggregate]) -> dict[str, Any]:
        if not aggregates:
            return {"mean": None, "median": None, "sample_count": 0}

        means = [float(aggregate.mean_value) for aggregate in aggregates]
        medians = [
            float(aggregate.median_value)
            for aggregate in aggregates
            if aggregate.median_value is not None
        ]

        return {
            "mean": round(statistics.mean(means), 1),
            "median": round(statistics.mean(medians), 1) if medians else None,
            "sample_count": sum(int(aggregate.sample_count) for aggregate in aggregates),
        }

    @staticmethod
    def _ratio(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator is None or denominator <= 0:
            return None
        return round(numerator / denominator, 2)

    @staticmethod
    def _percent_change(current: float, previous: float) -> float:
        if previous <= 0:
            return 0.0
        return ((current - previous) / previous) * 100
