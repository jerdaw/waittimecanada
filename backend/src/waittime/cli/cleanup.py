"""CLI command for running database cleanup tasks.

This script implements the 30-day retention policy from the strategic plan.
Run this via cron job or GitHub Actions to prevent database bloat.

Usage:
    python -m waittime.cli.cleanup --dry-run  # Preview what would be deleted
    python -m waittime.cli.cleanup            # Actually delete old measurements
    python -m waittime.cli.cleanup --retention-days 60  # Custom retention period
"""

import argparse
import logging
import sys
from datetime import UTC, datetime, timedelta

from waittime.services.aggregation import AggregationService
from waittime.services.database import DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run database cleanup."""
    parser = argparse.ArgumentParser(description="Clean up old measurements from the database")
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain measurements (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed statistics",
    )

    args = parser.parse_args()

    try:
        db = DatabaseService()

        # Get statistics before cleanup
        logger.info("Fetching current database statistics...")
        stats_before = db.get_measurement_age_stats()

        logger.info("Database Statistics:")
        logger.info(f"  Total measurements: {stats_before['total_measurements']}")
        logger.info(f"  Oldest measurement: {stats_before['oldest_measurement_age_days']} days old")
        logger.info(f"  Newest measurement: {stats_before['newest_measurement_age_days']} days old")
        logger.info(
            f"  Measurements older than 30 days: {stats_before['measurements_older_than_30_days']}"
        )

        # Calculate what would be deleted
        if args.retention_days != 30:
            logger.info(f"\nUsing custom retention period: {args.retention_days} days")

        if args.dry_run:
            logger.info("\n🔍 DRY RUN MODE - No data will be deleted")
            logger.info(
                f"Would delete approximately {stats_before['measurements_older_than_30_days']} "
                f"measurements older than {args.retention_days} days"
            )
            return 0

        # Aggregate before cleanup to ensure no data is lost
        logger.info("\nAggregating measurements before cleanup...")
        agg_service = AggregationService(db)

        # Reduced lookback range (3 days) to save Neon network transfer.
        # Since cleanup runs daily, a 3-day buffer is sufficient.
        three_days_ago = datetime.now(UTC) - timedelta(days=3)
        agg_counts = agg_service.backfill(
            start_date=three_days_ago,
            end_date=None,
            period_types=["hourly", "daily"],
        )
        agg_total = sum(agg_counts.values())
        if agg_total > 0:
            logger.info(f"  Created {agg_total} new aggregates before cleanup")

        # Actually perform cleanup
        logger.info(f"\nDeleting measurements older than {args.retention_days} days...")
        deleted_count = db.cleanup_old_measurements(retention_days=args.retention_days)

        logger.info("\n✅ Cleanup complete!")
        logger.info(f"  Deleted: {deleted_count} measurements")

        # Get statistics after cleanup
        if args.verbose:
            stats_after = db.get_measurement_age_stats()
            logger.info("\nAfter cleanup:")
            logger.info(f"  Total measurements: {stats_after['total_measurements']}")
            logger.info(
                f"  Oldest measurement: {stats_after['oldest_measurement_age_days']} days old"
            )
            logger.info(f"  Space saved: {deleted_count} rows")

        return 0

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
