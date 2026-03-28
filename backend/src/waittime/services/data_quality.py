"""Service for computing and reporting data quality metrics.

Tracks scraper reliability, data coverage gaps, and collection frequency.
Quality metrics are computed from existing measurements and scraper_status
tables, with optional caching to data_quality_snapshots.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class DataQualityService:
    """Computes data quality metrics for hospitals and sources.

    Live production scrapers currently run hourly, so we expect 24 measurements per
    hospital per day. This service measures actual vs expected collection
    rates and identifies gaps in data coverage.
    """

    # Live GitHub Actions cadence is hourly = 24 expected scrapes per day
    EXPECTED_SCRAPES_PER_DAY = 24
    SCRAPE_INTERVAL_MINUTES = 60
    ACTIVE_LIVE_SOURCE_IDS = (
        "quebec-msss",
        "ontario-health",
        "alberta-ahs",
        "bc-phsa",
    )

    # Status thresholds
    HEALTHY_THRESHOLD = 0.95  # >=95% success rate
    DEGRADED_THRESHOLD = 0.80  # >=80% success rate (below = critical)

    def __init__(self, db: DatabaseService) -> None:
        self.db = db

    def compute_hospital_quality(self, hospital_id: str, date: datetime) -> dict[str, Any]:
        """Compute data quality metrics for a single hospital on a single day.

        Args:
            hospital_id: Hospital to analyze
            date: The day to compute metrics for (uses date portion only)

        Returns:
            Dict with hospital_id, date, expected/actual scrapes,
            success_rate, gap analysis
        """
        day_start = datetime(date.year, date.month, date.day, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)

        timestamps = self.db.get_measurement_timestamps(hospital_id, day_start, day_end)

        actual_scrapes = len(timestamps)
        success_rate = actual_scrapes / self.EXPECTED_SCRAPES_PER_DAY

        # Compute gaps between consecutive measurements
        gaps = self._compute_gaps(timestamps, day_start, day_end)

        longest_gap = max((g["duration_minutes"] for g in gaps), default=None)
        mean_gap = sum(g["duration_minutes"] for g in gaps) / len(gaps) if gaps else None

        return {
            "hospital_id": hospital_id,
            "date": day_start.date().isoformat(),
            "expected_scrapes": self.EXPECTED_SCRAPES_PER_DAY,
            "actual_scrapes": actual_scrapes,
            "success_rate": min(success_rate, 1.0),
            "longest_gap_minutes": longest_gap,
            "mean_gap_minutes": round(mean_gap, 1) if mean_gap is not None else None,
            "gaps": gaps,
        }

    def compute_source_quality(
        self, source_id: str, start_date: datetime, end_date: datetime
    ) -> dict[str, Any]:
        """Compute quality metrics for an entire source over a date range.

        Args:
            source_id: Source to analyze
            start_date: Start of range
            end_date: End of range

        Returns:
            Dict with source_id, period, total/actual counts,
            daily rates, and hospital coverage
        """
        hospitals = self.db.get_hospitals_by_source(source_id)
        total_hospitals = len(hospitals)

        counts = self.db.get_measurement_count_by_hospital(source_id, start_date, end_date)

        days = max((end_date - start_date).days, 1)
        total_expected = total_hospitals * self.EXPECTED_SCRAPES_PER_DAY * days
        total_actual = sum(counts.values())
        overall_rate = total_actual / total_expected if total_expected > 0 else 0.0

        # Compute daily success rates
        daily_rates: list[dict[str, Any]] = []
        current = start_date
        while current < end_date:
            next_day = current + timedelta(days=1)
            day_counts = self.db.get_measurement_count_by_hospital(source_id, current, next_day)
            day_total = sum(day_counts.values())
            day_expected = total_hospitals * self.EXPECTED_SCRAPES_PER_DAY
            daily_rates.append(
                {
                    "date": current.date().isoformat()
                    if hasattr(current, "date")
                    else str(current),
                    "rate": min(day_total / day_expected, 1.0) if day_expected > 0 else 0.0,
                }
            )
            current = next_day

        hospitals_with_data = len(counts)
        coverage_rate = hospitals_with_data / total_hospitals if total_hospitals > 0 else 0.0

        # Dynamic expected count based on hospital onboarding
        onboarding_dates = self.db.get_hospital_onboarding_dates(source_id)
        total_expected = 0

        # Calculate expected scrapes day by day for each hospital
        # This prevents new hospitals from dragging down historical success rates
        current = start_date
        while current < end_date:
            next_day = current + timedelta(days=1)
            day_expected = 0

            for hospital in hospitals:
                # If hospital has never been seen, it doesn't contribute to expected count
                # (Treat as not yet onboarded)
                first_seen = onboarding_dates.get(hospital.id)
                if not first_seen:
                    continue

                # If hospital was onboarded on or before this day, expect data
                # We use the date of the first measurement as the "active since" date
                if current.date() >= first_seen.date():
                    day_expected += self.EXPECTED_SCRAPES_PER_DAY

            total_expected += day_expected
            current = next_day

        overall_rate = total_actual / total_expected if total_expected > 0 else 0.0

        return {
            "source_id": source_id,
            "period": {
                "start": start_date.date().isoformat()
                if hasattr(start_date, "date")
                else str(start_date),
                "end": end_date.date().isoformat() if hasattr(end_date, "date") else str(end_date),
            },
            "total_expected": total_expected,
            "total_actual": total_actual,
            "overall_success_rate": min(overall_rate, 1.0),
            "daily_success_rates": daily_rates,
            "hospitals_with_data_today": hospitals_with_data,
            "total_hospitals": total_hospitals,
            "coverage_rate": min(coverage_rate, 1.0),
        }

    def compute_system_quality(self) -> dict[str, Any]:
        """Compute system-wide quality metrics (all sources, last 24h and 7d).

        Returns:
            Dict with overall_status, per-source metrics,
            system uptime, and measurement counts
        """
        now = datetime.now(UTC)
        start_24h = now - timedelta(hours=24)
        start_7d = now - timedelta(days=7)

        source_ids = [
            source_id
            for source_id in self.db.get_all_source_ids()
            if source_id in self.ACTIVE_LIVE_SOURCE_IDS
        ]
        sources_info: list[dict[str, Any]] = []
        rates_24h: list[float] = []
        total_measurements_24h = 0
        total_measurements_7d = 0

        for source_id in source_ids:
            quality_24h = self.compute_source_quality(source_id, start_24h, now)
            quality_7d = self.compute_source_quality(source_id, start_7d, now)
            total_measurements_24h += quality_24h["total_actual"]
            total_measurements_7d += quality_7d["total_actual"]

            # Get source province
            source = self.db.get_source(source_id)
            province = source.province if source else "??"

            # Get last heartbeat
            stale_scrapers = self.db.get_stale_scrapers(threshold_minutes=0)
            last_heartbeat_age = None
            for s in stale_scrapers:
                if s.source_id == source_id:
                    age = (now - s.last_run).total_seconds() / 60
                    last_heartbeat_age = int(age)
                    break

            rate_24h = quality_24h["overall_success_rate"]
            rates_24h.append(rate_24h)

            sources_info.append(
                {
                    "source_id": source_id,
                    "province": province,
                    "last_24h_success_rate": rate_24h,
                    "last_7d_success_rate": quality_7d["overall_success_rate"],
                    "hospitals_reporting": quality_24h["hospitals_with_data_today"],
                    "last_heartbeat_age_minutes": last_heartbeat_age,
                }
            )

        # Compute overall status
        if rates_24h:
            system_rate = sum(rates_24h) / len(rates_24h)
        else:
            system_rate = 0.0

        if system_rate >= self.HEALTHY_THRESHOLD:
            overall_status = "healthy"
        elif system_rate >= self.DEGRADED_THRESHOLD:
            overall_status = "degraded"
        else:
            overall_status = "critical"

        return {
            "overall_status": overall_status,
            "sources": sources_info,
            "system_uptime_24h": min(system_rate, 1.0),
            "system_uptime_7d": min(system_rate, 1.0),
            "total_measurements_24h": total_measurements_24h,
            "total_measurements_7d": total_measurements_7d,
        }

    def get_coverage_timeline(self, hospital_id: str, days: int = 30) -> list[dict[str, Any]]:
        """Get data availability timeline for a hospital.

        Args:
            hospital_id: Hospital to analyze
            days: Number of days to look back (default 30)

        Returns:
            List of daily entries with date, scrape_count, success_rate, has_gaps
        """
        now = datetime.now(UTC)
        timeline: list[dict[str, Any]] = []

        for i in range(days):
            day = now - timedelta(days=days - 1 - i)
            day_start = datetime(day.year, day.month, day.day, tzinfo=UTC)
            day_end = day_start + timedelta(days=1)

            timestamps = self.db.get_measurement_timestamps(hospital_id, day_start, day_end)
            scrape_count = len(timestamps)
            success_rate = min(scrape_count / self.EXPECTED_SCRAPES_PER_DAY, 1.0)

            # Detect if there are significant gaps (>= 2x expected interval)
            has_gaps = False
            for j in range(1, len(timestamps)):
                gap = (timestamps[j] - timestamps[j - 1]).total_seconds() / 60
                if gap >= self.SCRAPE_INTERVAL_MINUTES * 2:
                    has_gaps = True
                    break

            timeline.append(
                {
                    "date": day_start.date().isoformat(),
                    "scrape_count": scrape_count,
                    "success_rate": success_rate,
                    "has_gaps": has_gaps,
                }
            )

        return timeline

    def snapshot_daily_quality(self, date: datetime) -> int:
        """Compute and cache quality metrics for all hospitals on a date.

        Saves to data_quality_snapshots table. Idempotent: existing
        snapshots for the same hospital+date are skipped.

        Args:
            date: The day to snapshot

        Returns:
            Number of new snapshots saved
        """
        hospital_ids = self.db.get_all_hospital_ids(visible_only=False)
        saved = 0

        for hospital_id in hospital_ids:
            quality = self.compute_hospital_quality(hospital_id, date)

            # Need source_id for the snapshot
            hospital = self.db.get_hospital(hospital_id)
            if hospital is None:
                continue

            snapshot = {
                "hospital_id": hospital_id,
                "source_id": hospital.source_id,
                "snapshot_date": datetime(date.year, date.month, date.day, tzinfo=UTC).date(),
                "expected_scrapes": quality["expected_scrapes"],
                "actual_scrapes": quality["actual_scrapes"],
                "success_rate": quality["success_rate"],
                "longest_gap_minutes": quality["longest_gap_minutes"],
                "mean_gap_minutes": quality["mean_gap_minutes"],
            }

            if self.db.insert_quality_snapshot(snapshot):
                saved += 1

        logger.info(
            "Snapshot for %s: saved %d/%d hospitals",
            date.date().isoformat() if hasattr(date, "date") else str(date),
            saved,
            len(hospital_ids),
        )
        return saved

    @staticmethod
    def _compute_gaps(
        timestamps: list[datetime],
        day_start: datetime,
        day_end: datetime,
    ) -> list[dict[str, Any]]:
        """Compute gaps between consecutive measurements.

        A gap is any period longer than 1.5x the expected scrape interval
        (90 minutes) with no data.

        Args:
            timestamps: Sorted list of measurement timestamps
            day_start: Start of the analysis window
            day_end: End of the analysis window

        Returns:
            List of gap dicts with start, end, duration_minutes
        """
        gap_threshold = DataQualityService.SCRAPE_INTERVAL_MINUTES * 1.5
        gaps: list[dict[str, Any]] = []

        if not timestamps:
            # Entire day is one big gap
            duration = (day_end - day_start).total_seconds() / 60
            return [
                {
                    "start": day_start.isoformat(),
                    "end": day_end.isoformat(),
                    "duration_minutes": int(duration),
                }
            ]

        # Check gap from day start to first measurement
        first_gap = (timestamps[0] - day_start).total_seconds() / 60
        if first_gap >= gap_threshold:
            gaps.append(
                {
                    "start": day_start.isoformat(),
                    "end": timestamps[0].isoformat(),
                    "duration_minutes": int(first_gap),
                }
            )

        # Check gaps between consecutive measurements
        for i in range(1, len(timestamps)):
            delta = (timestamps[i] - timestamps[i - 1]).total_seconds() / 60
            if delta >= gap_threshold:
                gaps.append(
                    {
                        "start": timestamps[i - 1].isoformat(),
                        "end": timestamps[i].isoformat(),
                        "duration_minutes": int(delta),
                    }
                )

        # Check gap from last measurement to day end
        last_gap = (day_end - timestamps[-1]).total_seconds() / 60
        if last_gap >= gap_threshold:
            gaps.append(
                {
                    "start": timestamps[-1].isoformat(),
                    "end": day_end.isoformat(),
                    "duration_minutes": int(last_gap),
                }
            )

        return gaps
