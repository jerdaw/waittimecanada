"""Service for detecting anomalous wait time measurements.

Uses z-score and IQR-based detection against a rolling 7-day baseline.
Anomalies are flagged but never excluded from display — the flag is
metadata that enables transparency about data quality.
"""

import logging
import statistics
from datetime import datetime, timedelta

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Detects statistical outliers in incoming measurements."""

    # Configuration
    LOOKBACK_DAYS = 7  # Use 7-day rolling window for baseline
    MIN_SAMPLES_FOR_DETECTION = 20  # Need enough data points
    Z_SCORE_THRESHOLD = 3.0  # Flag if >3 standard deviations from mean
    IQR_MULTIPLIER = 1.5  # For IQR-based detection

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    def check_measurement(self, hospital_id: str, value: float, timestamp: datetime) -> dict:
        """Check if a new measurement is anomalous compared to recent history.

        Uses a 7-day rolling window to compute baseline statistics, then
        flags measurements that are statistical outliers by either z-score
        or IQR methods.

        Args:
            hospital_id: Hospital being measured
            value: Wait time in minutes
            timestamp: When the measurement was taken

        Returns:
            Dict with is_anomaly, reason, and optional details
        """
        lookback_start = timestamp - timedelta(days=self.LOOKBACK_DAYS)

        recent = self.db.get_measurements_in_range(hospital_id, lookback_start, timestamp)
        values = [r["value"] for r in recent]

        # Insufficient data — can't judge, safe default
        if len(values) < self.MIN_SAMPLES_FOR_DETECTION:
            return {"is_anomaly": False, "reason": None, "details": None}

        mean = statistics.mean(values)
        std = statistics.stdev(values)
        z_score = self._compute_z_score(value, values)
        iqr_bounds = self._compute_iqr_bounds(values)

        reasons: list[str] = []

        # Z-score check
        if z_score is not None and abs(z_score) > self.Z_SCORE_THRESHOLD:
            direction = "above" if z_score > 0 else "below"
            reasons.append(f"Z-score {z_score:.1f} ({direction} mean of {mean:.0f} min)")

        # IQR check
        if iqr_bounds is not None:
            lower, upper = iqr_bounds
            if value < lower:
                reasons.append(f"Below IQR lower bound ({value:.0f} < {lower:.0f})")
            elif value > upper:
                reasons.append(f"Above IQR upper bound ({value:.0f} > {upper:.0f})")

        if reasons:
            reason = "; ".join(reasons)
            logger.info(
                "Anomaly detected for %s: value=%.0f, %s",
                hospital_id,
                value,
                reason,
            )
            return {
                "is_anomaly": True,
                "reason": reason,
                "details": {
                    "value": value,
                    "baseline_mean": round(mean, 1),
                    "baseline_std": round(std, 1),
                    "z_score": round(z_score, 2) if z_score is not None else None,
                    "iqr_lower": round(iqr_bounds[0], 1) if iqr_bounds else None,
                    "iqr_upper": round(iqr_bounds[1], 1) if iqr_bounds else None,
                    "sample_count": len(values),
                },
            }

        return {"is_anomaly": False, "reason": None, "details": None}

    def check_batch(self, measurements: list[dict]) -> list[dict]:
        """Check a batch of measurements from a scraper run.

        More efficient than checking one at a time — loads baselines
        once per hospital.

        Args:
            measurements: List of dicts with hospital_id, value, timestamp

        Returns:
            List of anomaly check results (same order as input)
        """
        # Group by hospital to load baselines once
        hospitals: dict[str, list[float]] = {}
        results: list[dict] = []

        for m in measurements:
            hospital_id = m["hospital_id"]

            if hospital_id not in hospitals:
                lookback_start = m["timestamp"] - timedelta(days=self.LOOKBACK_DAYS)
                recent = self.db.get_measurements_in_range(
                    hospital_id, lookback_start, m["timestamp"]
                )
                hospitals[hospital_id] = [r["value"] for r in recent]

            baseline = hospitals[hospital_id]

            if len(baseline) < self.MIN_SAMPLES_FOR_DETECTION:
                results.append({"is_anomaly": False, "reason": None, "details": None})
                continue

            mean = statistics.mean(baseline)
            std = statistics.stdev(baseline)
            z_score = self._compute_z_score(m["value"], baseline)
            iqr_bounds = self._compute_iqr_bounds(baseline)

            reasons: list[str] = []

            if z_score is not None and abs(z_score) > self.Z_SCORE_THRESHOLD:
                direction = "above" if z_score > 0 else "below"
                reasons.append(f"Z-score {z_score:.1f} ({direction} mean of {mean:.0f} min)")

            if iqr_bounds is not None:
                lower, upper = iqr_bounds
                if m["value"] < lower:
                    reasons.append(f"Below IQR lower bound ({m['value']:.0f} < {lower:.0f})")
                elif m["value"] > upper:
                    reasons.append(f"Above IQR upper bound ({m['value']:.0f} > {upper:.0f})")

            if reasons:
                results.append(
                    {
                        "is_anomaly": True,
                        "reason": "; ".join(reasons),
                        "details": {
                            "value": m["value"],
                            "baseline_mean": round(mean, 1),
                            "baseline_std": round(std, 1),
                            "z_score": round(z_score, 2) if z_score else None,
                            "iqr_lower": round(iqr_bounds[0], 1) if iqr_bounds else None,
                            "iqr_upper": round(iqr_bounds[1], 1) if iqr_bounds else None,
                            "sample_count": len(baseline),
                        },
                    }
                )
            else:
                results.append({"is_anomaly": False, "reason": None, "details": None})

        return results

    def get_recent_anomalies(self, source_id: str | None = None, days: int = 7) -> list[dict]:
        """Get recent anomalies for display/review.

        Args:
            source_id: Optional filter by source
            days: Lookback period

        Returns:
            List of anomalous measurements with hospital info
        """
        return self.db.get_recent_anomalies(source_id=source_id, days=days)

    @staticmethod
    def _compute_z_score(value: float, values: list[float]) -> float | None:
        """Compute z-score for a value against a distribution.

        Returns None if insufficient data or zero standard deviation.
        """
        if len(values) < 3:
            return None
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        if std == 0:
            return 0.0
        return (value - mean) / std

    @staticmethod
    def _compute_iqr_bounds(
        values: list[float],
    ) -> tuple[float, float] | None:
        """Compute IQR-based anomaly bounds.

        Returns (lower_bound, upper_bound) or None if insufficient data.
        """
        if len(values) < 4:
            return None
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        return (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
