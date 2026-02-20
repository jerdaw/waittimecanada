import logging
from typing import Any

from psycopg2.extensions import connection

logger = logging.getLogger(__name__)


class QualityDiffService:
    def __init__(self, db_conn: connection) -> None:
        self.db_conn = db_conn

    def get_source_trend(self, source_id: str, days: int = 30) -> list[dict[str, Any]]:
        """
        Returns a time series of daily data quality snapshots for a source.
        """
        with self.db_conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    snapshot_date,
                    source_id,
                    COUNT(hospital_id) AS hospitals_snapshotted,
                    AVG(success_rate) AS avg_success_rate,
                    MIN(success_rate) AS min_success_rate,
                    SUM(CASE WHEN success_rate < 0.8 THEN 1 ELSE 0 END) AS hospitals_critical,
                    MAX(longest_gap_minutes) AS worst_gap_minutes
                FROM data_quality_snapshots
                WHERE source_id = %s
                  AND snapshot_date >= CURRENT_DATE - INTERVAL '%s days'
                GROUP BY snapshot_date, source_id
                ORDER BY snapshot_date DESC
                """,
                (source_id, days),
            )
            rows = cur.fetchall()

            if cur.description is None:
                return []
            # Use column names from cursor description
            columns = [desc[0] for desc in cur.description]
            return [dict(zip(columns, row, strict=False)) for row in rows]

    def get_source_diff(self, source_id: str, compare_days: int = 7) -> dict[str, Any]:
        """
        Compares the current quality mapping to the quality N days ago.
        Returns the delta for key metrics.
        """
        trend = self.get_source_trend(source_id, days=compare_days + 1)
        if not trend:
            return {
                "has_baseline": False,
                "summary": "No historical snapshot data available for comparison.",
            }

        current = trend[0]

        # Find the snapshot closest to compare_days ago
        # Trend is ordered DESC by date. If we want exactly compare_days ago, it should be trend[-1]
        baseline = trend[-1]

        if current["snapshot_date"] == baseline["snapshot_date"]:
            return {
                "has_baseline": False,
                "summary": "Insufficient historical snapshot data for comparison.",
            }

        # Calculate deltas
        # Using Decimal/float conversions where necessary based on psycopg2 return types
        curr_rate = (
            float(current["avg_success_rate"]) if current["avg_success_rate"] is not None else 0.0
        )
        base_rate = (
            float(baseline["avg_success_rate"]) if baseline["avg_success_rate"] is not None else 0.0
        )
        success_rate_delta = curr_rate - base_rate

        curr_hosp = current["hospitals_snapshotted"]
        base_hosp = baseline["hospitals_snapshotted"]
        hospitals_delta = curr_hosp - base_hosp

        curr_gap = current["worst_gap_minutes"]
        base_gap = baseline["worst_gap_minutes"]
        curr_gap_val = float(curr_gap) if curr_gap is not None else 0.0
        base_gap_val = float(base_gap) if base_gap is not None else 0.0
        worst_gap_delta = curr_gap_val - base_gap_val

        # Generate human-readable summary
        rate_change_pct = success_rate_delta * 100
        polarity = "Stable"
        if rate_change_pct >= 2.0:
            polarity = f"Improved by {rate_change_pct:.1f}%"
        elif rate_change_pct <= -2.0:
            polarity = f"Degraded by {abs(rate_change_pct):.1f}%"

        summary = (
            f"Coverage {polarity.lower()} vs. {compare_days} days ago. "
            f"Tracking {curr_hosp} hospitals (delta: {hospitals_delta:+d}). "
            f"{current['hospitals_critical']} hospitals currently reporting critical coverage (<80%)."
        )

        return {
            "has_baseline": True,
            "period_a_date": baseline["snapshot_date"].isoformat(),
            "period_b_date": current["snapshot_date"].isoformat(),
            "current_metrics": {
                "avg_success_rate": curr_rate,
                "hospitals_snapshotted": curr_hosp,
                "worst_gap_minutes": curr_gap_val,
            },
            "baseline_metrics": {
                "avg_success_rate": base_rate,
                "hospitals_snapshotted": base_hosp,
                "worst_gap_minutes": base_gap_val,
            },
            "deltas": {
                "success_rate_delta": success_rate_delta,
                "hospitals_reporting_delta": hospitals_delta,
                "worst_gap_delta": worst_gap_delta,
            },
            "summary": summary,
        }
