"""Service for computing hospital peer benchmarks."""

import logging
import statistics
from datetime import UTC, datetime, timedelta
from typing import Any

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class BenchmarkingService:
    """Compute peer rankings and trend summaries for hospitals within a province."""

    TREND_THRESHOLD_PERCENT = 5.0

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    def compute_benchmarks(
        self,
        province: str,
        period_days: int = 7,
        ontology: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Compute benchmark stats for all visible/verified hospitals in a province."""
        if period_days <= 0:
            raise ValueError("period_days must be > 0")

        normalized_province = province.upper()
        period_label = self._period_label(period_days)

        period_end = datetime.now(UTC)
        period_start = period_end - timedelta(days=period_days)
        previous_start = period_start - timedelta(days=period_days)

        # 1. Determine ontology if not provided
        selected_ontology = ontology
        if not selected_ontology:
            selected_ontology = self._get_dominant_ontology(
                normalized_province, period_start, period_end
            )

        # 2. Query only for that ontology
        rows = self._query_benchmark_rows(
            province=normalized_province,
            current_start=period_start,
            current_end=period_end,
            previous_start=previous_start,
            previous_end=period_start,
            ontology=selected_ontology,
        )

        ranked_rows = [row for row in rows if row.get("period_mean") is not None]
        ranked_rows.sort(key=lambda row: float(row["period_mean"]))

        hospitals: list[dict[str, Any]] = []
        total = len(ranked_rows)

        for rank, row in enumerate(ranked_rows, start=1):
            period_mean = float(row["period_mean"])
            previous_period_mean = (
                float(row["previous_period_mean"])
                if row.get("previous_period_mean") is not None
                else None
            )

            percentile = self._compute_percentile(rank, total)
            trend = self._compute_trend(
                current_mean=period_mean,
                previous_mean=previous_period_mean,
                threshold=self.TREND_THRESHOLD_PERCENT,
            )

            hospitals.append(
                {
                    "hospital_id": row["hospital_id"],
                    "hospital_name": row["hospital_name"],
                    "city": row["city"],
                    "current_wait": (
                        float(row["current_wait"]) if row.get("current_wait") is not None else None
                    ),
                    "period_mean": period_mean,
                    "percentile": percentile,
                    "quartile": self._compute_quartile(percentile),
                    "trend": trend,
                    "trend_change_percent": self._compute_trend_change_percent(
                        period_mean, previous_period_mean
                    ),
                }
            )

        period_means = [item["period_mean"] for item in hospitals]

        return {
            "province": normalized_province,
            "period": period_label,
            "generated_at": datetime.now(UTC).isoformat(),
            "hospital_count": len(hospitals),
            "province_stats": self._compute_summary_stats(period_means),
            "hospitals": hospitals,
            "ontology": selected_ontology or {},
        }

    def get_hospital_benchmark(
        self,
        hospital_id: str,
        period_days: int = 7,
        ontology: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Return benchmark details for a single hospital with province context."""
        province = self._get_province_for_hospital(hospital_id)
        if province is None:
            raise ValueError(f"Hospital not found: {hospital_id}")

        benchmark_data = self.compute_benchmarks(
            province=province,
            period_days=period_days,
            ontology=ontology,
        )
        hospital_data = next(
            (
                hospital
                for hospital in benchmark_data["hospitals"]
                if hospital["hospital_id"] == hospital_id
            ),
            None,
        )

        if hospital_data is None:
            raise ValueError(f"Hospital has insufficient aggregate data: {hospital_id}")

        return {
            "province": benchmark_data["province"],
            "period": benchmark_data["period"],
            "generated_at": benchmark_data["generated_at"],
            "hospital_count": benchmark_data["hospital_count"],
            "province_stats": benchmark_data["province_stats"],
            "hospital": hospital_data,
            "ontology": benchmark_data["ontology"],
        }

    def _get_dominant_ontology(
        self,
        province: str,
        start: datetime,
        end: datetime,
    ) -> dict[str, str] | None:
        """Identify the most common ontology used in the province for this period."""
        query = """
            SELECT
                metric_family,
                start_event,
                end_event,
                statistic_type,
                COUNT(*) as cnt
            FROM measurement_aggregates ma
            JOIN hospitals h ON h.id = ma.hospital_id
            WHERE h.province = %s
              AND ma.period_type = 'daily'
              AND ma.period_start >= %s
              AND ma.period_start < %s
            GROUP BY 1, 2, 3, 4
            ORDER BY cnt DESC
            LIMIT 1
        """
        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute(query, (province, start, end))
                row = cur.fetchone()
                if not row:
                    return None
                return {
                    "metric_family": row["metric_family"],
                    "start_event": row["start_event"],
                    "end_event": row["end_event"],
                    "statistic_type": row["statistic_type"],
                }

    def _query_benchmark_rows(
        self,
        province: str,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
        ontology: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query period means and latest wait time for hospitals in a province."""
        # We construct query parts dynamically based on ontology presence

        # Base query structure with placeholders
        base_query = """
            WITH current_period AS (
                SELECT
                    hospital_id,
                    AVG(mean_value)::float AS period_mean
                FROM measurement_aggregates
                WHERE period_type = 'daily'
                  AND period_start >= %s
                  AND period_start < %s
                  {ontology_filter}
                GROUP BY hospital_id
            ),
            previous_period AS (
                SELECT
                    hospital_id,
                    AVG(mean_value)::float AS period_mean
                FROM measurement_aggregates
                WHERE period_type = 'daily'
                  AND period_start >= %s
                  AND period_start < %s
                  {ontology_filter}
                GROUP BY hospital_id
            )
            SELECT
                h.id AS hospital_id,
                h.name AS hospital_name,
                h.city,
                lm.value AS current_wait,
                cp.period_mean,
                pp.period_mean AS previous_period_mean
            FROM hospitals h
            LEFT JOIN LATERAL (
                SELECT value
                FROM measurements
                WHERE hospital_id = h.id
                  {ontology_filter_measurements}
                ORDER BY timestamp_utc DESC
                LIMIT 1
            ) lm ON TRUE
            LEFT JOIN current_period cp ON cp.hospital_id = h.id
            LEFT JOIN previous_period pp ON pp.hospital_id = h.id
            WHERE h.province = %s
              AND h.is_visible = TRUE
              AND h.is_verified = TRUE
            ORDER BY h.id
        """

        # Helper to append ontology params repeatedly
        ontology_params = []
        ontology_clause = ""
        ontology_clause_measurements = ""

        if ontology:
            if "metric_family" in ontology:
                ontology_clause += " AND metric_family = %s"
                ontology_params.append(ontology["metric_family"])
            if "start_event" in ontology:
                ontology_clause += " AND start_event = %s"
                ontology_params.append(ontology["start_event"])
            if "end_event" in ontology:
                ontology_clause += " AND end_event = %s"
                ontology_params.append(ontology["end_event"])
            if "statistic_type" in ontology:
                ontology_clause += " AND statistic_type = %s"
                ontology_params.append(ontology["statistic_type"])

            # Measurements table doesn't have statistic_type usually?
            # Wait, measurements table DOES NOT have statistic_type. Aggregates do.
            # Measurements has metric_family, start_event, end_event.
            if "metric_family" in ontology:
                ontology_clause_measurements += " AND metric_family = %s"
            if "start_event" in ontology:
                ontology_clause_measurements += " AND start_event = %s"
            if "end_event" in ontology:
                ontology_clause_measurements += " AND end_event = %s"

        # Params order:
        # 1. current_period (time + ontology)
        # 2. previous_period (time + ontology)
        # 3. measurements (ontology only, no time params in LATERAL?)
        # 4. province

        # Construct full params list
        full_params: list[Any] = []

        # current_period
        full_params.extend([current_start, current_end])
        full_params.extend(ontology_params)

        # previous_period
        full_params.extend([previous_start, previous_end])
        full_params.extend(ontology_params)

        # measurements
        # Note: measurements only uses metric/start/end, NOT statistic_type
        # We need separate params list for measurements
        ontology_params_measurements = []
        if ontology:
            if "metric_family" in ontology:
                ontology_params_measurements.append(ontology["metric_family"])
            if "start_event" in ontology:
                ontology_params_measurements.append(ontology["start_event"])
            if "end_event" in ontology:
                ontology_params_measurements.append(ontology["end_event"])

        full_params.extend(ontology_params_measurements)

        # province
        full_params.append(province)

        final_query = base_query.format(
            ontology_filter=ontology_clause,
            ontology_filter_measurements=ontology_clause_measurements,
        )

        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute(final_query, tuple(full_params))
                return [dict(row) for row in cur.fetchall()]

    def _get_province_for_hospital(self, hospital_id: str) -> str | None:
        """Resolve province code for a hospital ID."""
        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute("SELECT province FROM hospitals WHERE id = %s", (hospital_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                return str(row["province"]).upper()

    @staticmethod
    def _period_label(period_days: int) -> str:
        if period_days == 1:
            return "24h"
        return f"{period_days}d"

    @staticmethod
    def _compute_summary_stats(values: list[float]) -> dict[str, float | None]:
        if not values:
            return {
                "mean": None,
                "median": None,
                "p25": None,
                "p75": None,
                "min": None,
                "max": None,
            }

        sorted_values = sorted(values)
        return {
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "p25": BenchmarkingService._compute_quantile(sorted_values, 0.25),
            "p75": BenchmarkingService._compute_quantile(sorted_values, 0.75),
            "min": min(values),
            "max": max(values),
        }

    @staticmethod
    def _compute_quantile(sorted_values: list[float], q: float) -> float | None:
        if not sorted_values:
            return None
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
    def _compute_percentile(rank: int, total: int) -> int:
        """Compute percentile from rank where rank=1 is shortest waits."""
        if total <= 0:
            return 0
        percentile = int(round((rank / total) * 100))
        return max(1, min(percentile, 100))

    @staticmethod
    def _compute_quartile(percentile: int) -> int:
        if percentile <= 25:
            return 1
        if percentile <= 50:
            return 2
        if percentile <= 75:
            return 3
        return 4

    @staticmethod
    def _compute_trend(
        current_mean: float,
        previous_mean: float | None,
        threshold: float = 5.0,
    ) -> str:
        """Classify trend direction using percent change threshold."""
        if previous_mean is None or previous_mean <= 0:
            return "stable"

        change_pct = ((current_mean - previous_mean) / previous_mean) * 100
        if change_pct < -threshold:
            return "improving"
        if change_pct > threshold:
            return "worsening"
        return "stable"

    @staticmethod
    def _compute_trend_change_percent(current_mean: float, previous_mean: float | None) -> float:
        if previous_mean is None or previous_mean <= 0:
            return 0.0
        return round(((current_mean - previous_mean) / previous_mean) * 100, 1)
