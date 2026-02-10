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
        ontology: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Compute province-wide trend from hospital aggregates.

        Enforces ontology safety: if multiple methodologies exist (e.g. "Triage->Nurse"
        vs "Triage->Doctor"), this will automatically select the one with the most
        measurements to prevent mixing incompatible data, unless a specific
        ontology is requested.
        """
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
            ontology=ontology,
        )

        if not rows:
            return {
                "province": normalized_province,
                "period": period_type,
                "lookback": self._lookback_label(lookback_months),
                "data_points": [],
                "trend_summary": self._empty_summary(normalized_province, lookback_months),
                "ontology": ontology or {},
            }

        # Ontology Safety: Group by methodology
        by_ontology = defaultdict(list)
        for row in rows:
            key = (
                row["metric_family"],
                row["start_event"],
                row["end_event"],
                row["statistic_type"],
            )
            by_ontology[key].append(row)

        # Select dominant ontology (most measurements)
        selected_key = max(
            by_ontology.keys(),
            key=lambda k: sum(r["sample_count"] for r in by_ontology[k]),
        )
        selected_rows = by_ontology[selected_key]

        selected_ontology = {
            "metric_family": selected_key[0],
            "start_event": selected_key[1],
            "end_event": selected_key[2],
            "statistic_type": selected_key[3],
        }

        grouped: dict[datetime, list[dict[str, Any]]] = defaultdict(list)
        for row in selected_rows:
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
            "ontology": selected_ontology,
        }

    def _empty_summary(self, province: str, lookback_months: int) -> dict[str, Any]:
        """Return a stable/no-data summary."""
        return {
            "direction": "stable",
            "change_percent": 0.0,
            "start_mean": None,
            "end_mean": None,
            "narrative": self.generate_narrative(
                province, "stable", 0.0, None, None, self._lookback_label(lookback_months)
            ),
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
        ontology: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query hospital-level aggregates for a province and period window."""
        query = """
            SELECT
                ma.hospital_id,
                ma.period_start,
                ma.period_end,
                ma.mean_value,
                ma.min_value,
                ma.max_value,
                ma.sample_count,
                ma.metric_family,
                ma.start_event,
                ma.end_event,
                ma.statistic_type
            FROM measurement_aggregates ma
            JOIN hospitals h ON h.id = ma.hospital_id
            WHERE h.province = %s
              AND h.is_visible = TRUE
              AND h.is_verified = TRUE
              AND ma.period_type = %s
              AND ma.period_start >= %s
              AND ma.period_start <= %s
        """
        params = [province, period_type, start, end]

        if ontology:
            if "metric_family" in ontology:
                query += " AND ma.metric_family = %s"
                params.append(ontology["metric_family"])
            if "start_event" in ontology:
                query += " AND ma.start_event = %s"
                params.append(ontology["start_event"])
            if "end_event" in ontology:
                query += " AND ma.end_event = %s"
                params.append(ontology["end_event"])
            if "statistic_type" in ontology:
                query += " AND ma.statistic_type = %s"
                params.append(ontology["statistic_type"])

        query += " ORDER BY ma.period_start, ma.hospital_id"

        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute(query, tuple(params))
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
