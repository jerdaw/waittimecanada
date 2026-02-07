"""Service for computing system-wide trend analysis."""

import logging
import statistics
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class SystemTrendService:
    """Computes province-level wait-time trends for weekly or monthly periods."""

    TREND_THRESHOLD_PERCENT = 5.0

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    def province_trend(
        self,
        province: str,
        period_type: str = "monthly",
        lookback_months: int = 6,
    ) -> dict[str, Any]:
        """Compute province-wide trend from hospital aggregates."""
        if period_type not in {"weekly", "monthly"}:
            raise ValueError("period_type must be 'weekly' or 'monthly'")
        if lookback_months <= 0:
            raise ValueError("lookback_months must be > 0")

        normalized_province = province.upper()
        end = datetime.now(UTC)
        start = end - timedelta(days=lookback_months * 31)

        rows = self._query_period_rows(
            province=normalized_province,
            period_type=period_type,
            start=start,
            end=end,
        )

        grouped: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            grouped[row["period_start"]].append(row)

        data_points: list[dict[str, Any]] = []
        for period_start in sorted(grouped):
            period_rows = grouped[period_start]
            means = [float(row["mean_value"]) for row in period_rows]
            sample_counts = [int(row["sample_count"]) for row in period_rows]

            weighted_mean = self._weighted_mean(means, sample_counts)
            if weighted_mean is None:
                continue

            period_end = max(row["period_end"] for row in period_rows)

            data_points.append(
                {
                    "period_start": period_start.date().isoformat(),
                    "period_end": period_end.date().isoformat(),
                    "province_mean": round(weighted_mean, 1),
                    "province_median": round(statistics.median(means), 1),
                    "province_p90": round(self._compute_quantile(sorted(means), 0.9), 1),
                    "hospitals_reporting": len(period_rows),
                    "total_measurements": sum(sample_counts),
                    "range_min": round(min(float(row["min_value"]) for row in period_rows), 1),
                    "range_max": round(max(float(row["max_value"]) for row in period_rows), 1),
                }
            )

        summary = self._trend_summary(
            province=normalized_province,
            data_points=data_points,
            lookback_months=lookback_months,
        )

        return {
            "province": normalized_province,
            "period": period_type,
            "lookback": self._lookback_label(lookback_months),
            "data_points": data_points,
            "trend_summary": summary,
        }

    def generate_narrative(
        self,
        province: str,
        direction: str,
        change_pct: float,
        start_mean: float | None,
        end_mean: float | None,
        lookback: str,
    ) -> str:
        """Generate human-readable trend narrative."""
        province_name = self._province_name(province)

        if start_mean is None or end_mean is None:
            return (
                f"Not enough data to determine a province-wide emergency wait time trend "
                f"for {province_name} over the past {lookback}."
            )

        rounded_start = round(start_mean)
        rounded_end = round(end_mean)

        if direction == "improving":
            return (
                f"{province_name} ER wait times have decreased approximately "
                f"{abs(change_pct):.1f}% over the past {lookback}, from an average of "
                f"{rounded_start} minutes to {rounded_end} minutes."
            )

        if direction == "worsening":
            return (
                f"{province_name} ER wait times have increased approximately "
                f"{abs(change_pct):.1f}% over the past {lookback}, from an average of "
                f"{rounded_start} minutes to {rounded_end} minutes."
            )

        return (
            f"{province_name} ER wait times have remained stable over the past {lookback}, "
            f"holding near {rounded_end} minutes on average."
        )

    def _query_period_rows(
        self,
        province: str,
        period_type: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        """Query hospital-level aggregates for a province and period window."""
        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        ma.hospital_id,
                        ma.period_start,
                        ma.period_end,
                        ma.mean_value,
                        ma.min_value,
                        ma.max_value,
                        ma.sample_count
                    FROM measurement_aggregates ma
                    JOIN hospitals h ON h.id = ma.hospital_id
                    WHERE h.province = %s
                      AND h.is_visible = TRUE
                      AND h.is_verified = TRUE
                      AND ma.period_type = %s
                      AND ma.period_start >= %s
                      AND ma.period_start <= %s
                    ORDER BY ma.period_start, ma.hospital_id
                    """,
                    (province, period_type, start, end),
                )
                return [dict(row) for row in cur.fetchall()]

    def _trend_summary(
        self,
        province: str,
        data_points: list[dict[str, Any]],
        lookback_months: int,
    ) -> dict[str, Any]:
        """Summarize trend direction and generate narrative."""
        if len(data_points) < 2:
            narrative = self.generate_narrative(
                province=province,
                direction="stable",
                change_pct=0.0,
                start_mean=(float(data_points[0]["province_mean"]) if data_points else None),
                end_mean=float(data_points[-1]["province_mean"]) if data_points else None,
                lookback=self._lookback_label(lookback_months),
            )
            return {
                "direction": "stable",
                "change_percent": 0.0,
                "start_mean": (float(data_points[0]["province_mean"]) if data_points else None),
                "end_mean": float(data_points[-1]["province_mean"]) if data_points else None,
                "narrative": narrative,
            }

        start_mean = float(data_points[0]["province_mean"])
        end_mean = float(data_points[-1]["province_mean"])

        change_pct = self._percent_change(end_mean, start_mean)
        direction = self._classify_direction(change_pct, self.TREND_THRESHOLD_PERCENT)

        narrative = self.generate_narrative(
            province=province,
            direction=direction,
            change_pct=change_pct,
            start_mean=start_mean,
            end_mean=end_mean,
            lookback=self._lookback_label(lookback_months),
        )

        return {
            "direction": direction,
            "change_percent": round(change_pct, 1),
            "start_mean": start_mean,
            "end_mean": end_mean,
            "narrative": narrative,
        }

    @staticmethod
    def _weighted_mean(values: list[float], weights: list[int]) -> float | None:
        """Compute weighted mean where weights are sample counts."""
        if not values or not weights or len(values) != len(weights):
            return None

        total_weight = sum(weights)
        if total_weight <= 0:
            return None

        weighted_sum = sum(value * weight for value, weight in zip(values, weights, strict=True))
        return weighted_sum / total_weight

    @staticmethod
    def _compute_quantile(sorted_values: list[float], q: float) -> float:
        """Linear interpolation quantile."""
        if not sorted_values:
            return 0.0
        if len(sorted_values) == 1:
            return sorted_values[0]

        index = (len(sorted_values) - 1) * q
        lower = int(index)
        upper = min(lower + 1, len(sorted_values) - 1)
        fraction = index - lower

        if lower == upper:
            return sorted_values[lower]
        return sorted_values[lower] + (sorted_values[upper] - sorted_values[lower]) * fraction

    @staticmethod
    def _percent_change(new_value: float, old_value: float) -> float:
        """Compute percent change, guarding divide-by-zero."""
        if old_value <= 0:
            return 0.0
        return ((new_value - old_value) / old_value) * 100

    @staticmethod
    def _classify_direction(change_pct: float, threshold: float = 5.0) -> str:
        """Map percent change to improving/stable/worsening."""
        if change_pct < -threshold:
            return "improving"
        if change_pct > threshold:
            return "worsening"
        return "stable"

    @staticmethod
    def _lookback_label(lookback_months: int) -> str:
        if lookback_months == 12:
            return "1 year"
        return f"{lookback_months} months"

    @staticmethod
    def _province_name(code: str) -> str:
        labels = {
            "ON": "Ontario",
            "QC": "Quebec",
            "AB": "Alberta",
            "BC": "British Columbia",
            "MB": "Manitoba",
            "SK": "Saskatchewan",
            "NS": "Nova Scotia",
            "NB": "New Brunswick",
            "NL": "Newfoundland and Labrador",
            "PE": "Prince Edward Island",
            "NT": "Northwest Territories",
            "NU": "Nunavut",
            "YT": "Yukon",
        }
        return labels.get(code.upper(), code.upper())
