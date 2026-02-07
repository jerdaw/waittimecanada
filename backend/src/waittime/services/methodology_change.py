"""Service for detecting when a province silently changes measurement methodology.

Compares distributional statistics between consecutive time periods. If a
province-wide mean shifts significantly, it flags a potential methodology
change. This depends on M13 aggregation tables for efficient comparisons.
"""

import logging
from datetime import UTC, datetime, timedelta

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class MethodologyChangeDetector:
    """Detects distributional shifts that may indicate methodology changes.

    Example: If Ontario switches from MEAN to P90 reporting, all hospitals
    would suddenly report higher values. This detector compares rolling
    statistics between consecutive periods to flag such shifts.
    """

    COMPARISON_WINDOW_DAYS = 7  # Compare this week vs last week
    MIN_HOSPITALS_FOR_DETECTION = 5  # Need data from enough hospitals
    SHIFT_THRESHOLD_PERCENT = 20  # Flag if province-wide mean shifts >20%

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    def check_source(self, source_id: str) -> dict:
        """Check a source for potential methodology changes.

        Compares mean wait times for the current period vs the previous
        period across all hospitals for this source. A large shift
        suggests a possible methodology change.

        Args:
            source_id: Source to analyze

        Returns:
            Dict with source_id, change_detected, and optional details
        """
        now = datetime.now(UTC)
        current_start = now - timedelta(days=self.COMPARISON_WINDOW_DAYS)
        previous_start = current_start - timedelta(days=self.COMPARISON_WINDOW_DAYS)

        # Get hospitals for this source
        hospitals = self.db.get_hospitals_by_source(source_id)

        if len(hospitals) < self.MIN_HOSPITALS_FOR_DETECTION:
            return {
                "source_id": source_id,
                "change_detected": False,
                "details": None,
            }

        # Collect per-hospital means for both periods
        current_means: list[float] = []
        previous_means: list[float] = []

        for hospital in hospitals:
            # Current period
            current_data = self.db.get_measurements_in_range(hospital.id, current_start, now)
            if current_data:
                current_means.append(sum(r["value"] for r in current_data) / len(current_data))

            # Previous period
            previous_data = self.db.get_measurements_in_range(
                hospital.id, previous_start, current_start
            )
            if previous_data:
                previous_means.append(sum(r["value"] for r in previous_data) / len(previous_data))

        # Need enough hospitals with data in both periods
        if (
            len(current_means) < self.MIN_HOSPITALS_FOR_DETECTION
            or len(previous_means) < self.MIN_HOSPITALS_FOR_DETECTION
        ):
            return {
                "source_id": source_id,
                "change_detected": False,
                "details": None,
            }

        # Province-wide means
        current_province_mean = sum(current_means) / len(current_means)
        previous_province_mean = sum(previous_means) / len(previous_means)

        # Calculate shift
        if previous_province_mean == 0:
            shift_percent = 0.0
        else:
            shift_percent = (
                (current_province_mean - previous_province_mean) / previous_province_mean * 100
            )

        change_detected = abs(shift_percent) > self.SHIFT_THRESHOLD_PERCENT

        if change_detected:
            direction = "increased" if shift_percent > 0 else "decreased"
            explanation = (
                f"Province-wide mean {direction} by {abs(shift_percent):.1f}% "
                f"(from {previous_province_mean:.0f} to {current_province_mean:.0f} min) "
                f"across {min(len(current_means), len(previous_means))} hospitals. "
                f"This may indicate a change in measurement methodology."
            )

            logger.warning(
                "Methodology change detected for %s: %s",
                source_id,
                explanation,
            )

            # Save the event
            self.db.insert_methodology_change(
                {
                    "source_id": source_id,
                    "previous_period_start": previous_start.date(),
                    "previous_period_end": current_start.date(),
                    "current_period_start": current_start.date(),
                    "current_period_end": now.date(),
                    "previous_mean": round(previous_province_mean, 1),
                    "current_mean": round(current_province_mean, 1),
                    "shift_percent": round(shift_percent, 1),
                    "hospitals_analyzed": min(len(current_means), len(previous_means)),
                    "explanation": explanation,
                }
            )

            return {
                "source_id": source_id,
                "change_detected": True,
                "details": {
                    "current_period_mean": round(current_province_mean, 1),
                    "previous_period_mean": round(previous_province_mean, 1),
                    "shift_percent": round(shift_percent, 1),
                    "hospitals_analyzed": min(len(current_means), len(previous_means)),
                    "explanation": explanation,
                },
            }

        return {
            "source_id": source_id,
            "change_detected": False,
            "details": None,
        }

    def check_all_sources(self) -> list[dict]:
        """Check all active sources for methodology changes.

        Returns:
            List of check results, one per source
        """
        source_ids = self.db.get_all_source_ids()
        results = []
        for source_id in source_ids:
            result = self.check_source(source_id)
            results.append(result)
        return results

    def get_change_history(self, source_id: str | None = None) -> list[dict]:
        """Get history of detected methodology changes.

        Args:
            source_id: Optional filter by source

        Returns:
            List of change events
        """
        return self.db.get_methodology_changes(source_id=source_id)
