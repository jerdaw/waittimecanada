"""Service for detecting anomalous wait time measurements.

Uses z-score and IQR-based detection against a rolling 7-day baseline.
Anomalies are flagged but never excluded from display — the flag is
metadata that enables transparency about data quality.
"""

import logging
import statistics
from datetime import datetime, timedelta
from typing import Any

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

    def check_measurement(
        self, hospital_id: str, value: float, timestamp: datetime
    ) -> dict[str, Any]:
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
        stats = self._get_baseline_stats(hospital_id, lookback_start, timestamp)
        return self._evaluate_with_stats(hospital_id, value, stats)

    def check_batch(self, measurements: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Check a batch of measurements from a scraper run.

        More efficient than checking one at a time — loads baselines
        once per hospital.

        Args:
            measurements: List of dicts with hospital_id, value, timestamp

        Returns:
            List of anomaly check results (same order as input)
        """
        if not measurements:
            return []

        hospital_windows: dict[str, tuple[str, datetime, datetime]] = {}
        for measurement in measurements:
            hospital_id = measurement["hospital_id"]
            if hospital_id not in hospital_windows:
                end_time = measurement["timestamp"]
                lookback_start = end_time - timedelta(days=self.LOOKBACK_DAYS)
                hospital_windows[hospital_id] = (hospital_id, lookback_start, end_time)

        stats_by_hospital = self._get_baseline_stats_batch(list(hospital_windows.values()))

        return [
            self._evaluate_with_stats(
                measurement["hospital_id"],
                measurement["value"],
                stats_by_hospital.get(measurement["hospital_id"]),
            )
            for measurement in measurements
        ]

    def get_recent_anomalies(
        self, source_id: str | None = None, days: int = 7
    ) -> list[dict[str, Any]]:
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

    def _get_baseline_stats(
        self, hospital_id: str, lookback_start: datetime, end_time: datetime
    ) -> dict[str, Any] | None:
        get_stats = getattr(self.db, "get_measurement_baseline_stats", None)
        if callable(get_stats):
            stats = get_stats(hospital_id, lookback_start, end_time)
            if isinstance(stats, dict):
                return stats

        recent = self.db.get_measurements_in_range(hospital_id, lookback_start, end_time)
        values = [float(row["value"]) for row in recent]
        if not values:
            return None

        q1 = None
        q3 = None
        if len(values) >= 4:
            sorted_values = sorted(values)
            n = len(sorted_values)
            q1 = sorted_values[n // 4]
            q3 = sorted_values[3 * n // 4]

        return {
            "sample_count": len(values),
            "mean_value": statistics.mean(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
            "q1": q1,
            "q3": q3,
        }

    def _get_baseline_stats_batch(
        self, hospital_windows: list[tuple[str, datetime, datetime]]
    ) -> dict[str, dict[str, Any]]:
        get_stats_batch = getattr(self.db, "get_measurement_baseline_stats_batch", None)
        if callable(get_stats_batch):
            stats_by_hospital = get_stats_batch(hospital_windows)
            if isinstance(stats_by_hospital, dict):
                return stats_by_hospital

        stats: dict[str, dict[str, Any]] = {}
        for hospital_id, lookback_start, end_time in hospital_windows:
            result = self._get_baseline_stats(hospital_id, lookback_start, end_time)
            if result is not None:
                stats[hospital_id] = result
        return stats

    def _evaluate_with_stats(
        self, hospital_id: str, value: float, stats: dict[str, Any] | None
    ) -> dict[str, Any]:
        if not stats:
            return {"is_anomaly": False, "reason": None, "details": None}

        sample_count = int(stats.get("sample_count") or 0)
        if sample_count < self.MIN_SAMPLES_FOR_DETECTION:
            return {"is_anomaly": False, "reason": None, "details": None}

        mean = float(stats.get("mean_value") or 0.0)
        std = float(stats.get("std_dev") or 0.0)

        z_score = None
        if sample_count >= 3:
            z_score = 0.0 if std == 0 else (value - mean) / std

        q1 = stats.get("q1")
        q3 = stats.get("q3")
        iqr_bounds = None
        if sample_count >= 4 and q1 is not None and q3 is not None:
            q1_value = float(q1)
            q3_value = float(q3)
            iqr = q3_value - q1_value
            iqr_bounds = (
                q1_value - self.IQR_MULTIPLIER * iqr,
                q3_value + self.IQR_MULTIPLIER * iqr,
            )

        reasons: list[str] = []

        if z_score is not None and abs(z_score) > self.Z_SCORE_THRESHOLD:
            direction = "above" if z_score > 0 else "below"
            reasons.append(f"Z-score {z_score:.1f} ({direction} mean of {mean:.0f} min)")

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
                    "sample_count": sample_count,
                },
            }

        return {"is_anomaly": False, "reason": None, "details": None}

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
