"""Heartbeat monitoring service for scraper health tracking.

Provides a high-level interface for recording scraper runs and checking health status.
Wraps the DatabaseService heartbeat methods with additional logic for stale detection.
"""

import logging
from datetime import UTC, datetime

from waittime.core import ScraperStatus
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class HeartbeatService:
    """Manages scraper heartbeat recording and health checks.

    Usage:
        heartbeat = HeartbeatService(db)

        # After successful scrape
        heartbeat.record_success("qc-msss", measurements_count=15)

        # After failed scrape
        heartbeat.record_failure("qc-msss", "Connection timeout")

        # Check health
        health = heartbeat.check_health("qc-msss")
    """

    # Default threshold for considering a scraper stale (in minutes)
    DEFAULT_STALE_THRESHOLD = 60

    def __init__(self, db: DatabaseService) -> None:
        """Initialize with database service.

        Args:
            db: DatabaseService instance for persistence
        """
        self.db = db

    def record_success(
        self,
        source_id: str,
        measurements_count: int,
    ) -> ScraperStatus:
        """Record a successful scraper run.

        Args:
            source_id: Source identifier (e.g., "qc-msss", "on-hqo")
            measurements_count: Number of measurements collected

        Returns:
            ScraperStatus with recorded state
        """
        status = self.db.update_heartbeat(
            source_id=source_id,
            status="healthy",
            error_message=None,
            measurements_count=measurements_count,
        )

        logger.info(
            f"Heartbeat recorded for {source_id}: "
            f"{measurements_count} measurements, status=healthy"
        )

        return status

    def record_failure(
        self,
        source_id: str,
        error_message: str,
    ) -> ScraperStatus:
        """Record a failed scraper run.

        Args:
            source_id: Source identifier
            error_message: Description of the failure

        Returns:
            ScraperStatus with error state
        """
        # Truncate long error messages
        truncated_error = error_message[:500] if error_message else "Unknown error"

        status = self.db.update_heartbeat(
            source_id=source_id,
            status="error",
            error_message=truncated_error,
            measurements_count=0,
        )

        logger.error(f"Heartbeat error for {source_id}: {truncated_error}")

        return status

    def check_health(
        self,
        source_id: str,
        max_age_minutes: int | None = None,
    ) -> dict:
        """Check if a scraper is healthy.

        A scraper is considered healthy if:
        1. It has a heartbeat record
        2. The last run was successful (status != 'error')
        3. The last run was within max_age_minutes

        Args:
            source_id: Source identifier to check
            max_age_minutes: Maximum age in minutes before considered stale
                           (defaults to DEFAULT_STALE_THRESHOLD)

        Returns:
            Dict with health status:
            {
                'source_id': str,
                'healthy': bool,
                'reason': str | None,  # 'no_heartbeat', 'last_run_failed', 'stale'
                'message': str | None,
                'last_run': str | None,  # ISO timestamp
                'age_minutes': float | None,
                'measurements_count': int | None
            }
        """
        threshold = max_age_minutes or self.DEFAULT_STALE_THRESHOLD

        # Get latest heartbeat from database
        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT source_id, last_run, status, error_message, measurements_count
                    FROM scraper_status
                    WHERE source_id = %s
                    ORDER BY last_run DESC
                    LIMIT 1
                    """,
                    (source_id,),
                )
                row = cur.fetchone()

        # No heartbeat ever recorded
        if not row:
            return {
                "source_id": source_id,
                "healthy": False,
                "reason": "no_heartbeat",
                "message": "No heartbeat ever recorded for this source",
                "last_run": None,
                "age_minutes": None,
                "measurements_count": None,
            }

        last_run = row["last_run"]
        age_minutes = (datetime.now(UTC) - last_run).total_seconds() / 60

        # Last run failed
        if row["status"] == "error":
            return {
                "source_id": source_id,
                "healthy": False,
                "reason": "last_run_failed",
                "message": row["error_message"],
                "last_run": last_run.isoformat(),
                "age_minutes": round(age_minutes, 1),
                "measurements_count": row["measurements_count"],
            }

        # Data is stale
        if age_minutes > threshold:
            return {
                "source_id": source_id,
                "healthy": False,
                "reason": "stale",
                "message": f"Last run was {round(age_minutes)} minutes ago (threshold: {threshold})",
                "last_run": last_run.isoformat(),
                "age_minutes": round(age_minutes, 1),
                "measurements_count": row["measurements_count"],
            }

        # Healthy
        return {
            "source_id": source_id,
            "healthy": True,
            "reason": None,
            "message": None,
            "last_run": last_run.isoformat(),
            "age_minutes": round(age_minutes, 1),
            "measurements_count": row["measurements_count"],
        }

    def check_all_sources(
        self,
        max_age_minutes: int | None = None,
    ) -> dict:
        """Check health of all registered sources.

        Args:
            max_age_minutes: Maximum age threshold

        Returns:
            Dict with overall health and per-source details:
            {
                'healthy': bool,  # True only if ALL sources are healthy
                'sources': [...]  # List of check_health results
                'unhealthy_count': int
            }
        """
        sources = self.db.list_sources()
        results = []

        for source in sources:
            health = self.check_health(source.id, max_age_minutes)
            results.append(health)

        unhealthy = [r for r in results if not r["healthy"]]

        return {
            "healthy": len(unhealthy) == 0,
            "sources": results,
            "unhealthy_count": len(unhealthy),
            "total_count": len(results),
        }

    def get_stale_scrapers(
        self,
        threshold_minutes: int | None = None,
    ) -> list[ScraperStatus]:
        """Get list of scrapers that haven't run recently or have errors.

        Args:
            threshold_minutes: Minutes since last run to consider stale

        Returns:
            List of ScraperStatus for unhealthy scrapers
        """
        threshold = threshold_minutes or self.DEFAULT_STALE_THRESHOLD
        return self.db.get_stale_scrapers(threshold)
