"""CLI command for backend data cleanup tasks.

The default behavior:
1. optionally report raw-measurement age statistics
2. refresh recent aggregates so long-range analytics stay current
3. delete raw measurements older than the retention window

Usage:
    python -m waittime.cli.cleanup --dry-run
    python -m waittime.cli.cleanup
    python -m waittime.cli.cleanup --with-stats
    python -m waittime.cli.cleanup --retention-days 60
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
    """Run backend data cleanup."""
    parser = argparse.ArgumentParser(
        description="Refresh recent aggregates and clean up old measurements"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain measurements (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview cleanup without mutating data",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed statistics",
    )
    parser.add_argument(
        "--with-stats",
        action="store_true",
        help="Collect full-table age statistics during cleanup output",
    )

    args = parser.parse_args()

    try:
        db = DatabaseService()
        stats_requested = args.dry_run or args.verbose or args.with_stats
        stats_before = None

        if stats_requested:
            logger.info("Fetching current database statistics...")
            stats_before = db.get_measurement_age_stats(older_than_days=args.retention_days)
            logger.info("Database Statistics:")
            logger.info(f"  Total measurements: {stats_before['total_measurements']}")
            logger.info(
                f"  Oldest measurement: {stats_before['oldest_measurement_age_days']} days old"
            )
            logger.info(
                f"  Newest measurement: {stats_before['newest_measurement_age_days']} days old"
            )
            logger.info(
                "  Measurements older than %s days: %s",
                stats_before["older_than_days_threshold"],
                stats_before["measurements_older_than_threshold"],
            )
        else:
            logger.info(
                "Skipping full-table age statistics. Use --with-stats, --verbose, "
                "or --dry-run to collect them."
            )

        # Calculate what would be deleted
        if args.retention_days != 30:
            logger.info(f"\nUsing custom retention period: {args.retention_days} days")

        if args.dry_run:
            logger.info("\n🔍 DRY RUN MODE - No data will be deleted")
            if stats_before is not None:
                logger.info(
                    "Would delete approximately %s measurements older than %s days",
                    stats_before["measurements_older_than_threshold"],
                    args.retention_days,
                )
            else:
                logger.info(
                    "No age stats were collected; rerun with --with-stats "
                    "for a row estimate before deletion."
                )
            return 0

        logger.info("\nRefreshing recent daily aggregates before cleanup...")
        agg_service = AggregationService(db)

        three_days_ago = datetime.now(UTC) - timedelta(days=3)
        agg_counts = agg_service.backfill(
            start_date=three_days_ago,
            end_date=None,
            period_types=["daily"],
        )
        agg_total = sum(agg_counts.values())
        if agg_total > 0:
            logger.info(f"  Created {agg_total} new aggregates during cleanup")

        logger.info(f"\nDeleting measurements older than {args.retention_days} days...")
        deleted_count = db.cleanup_old_measurements(retention_days=args.retention_days)

        logger.info("\n✅ Cleanup complete!")
        logger.info(f"  Deleted: {deleted_count} measurements")

        # Get statistics after cleanup
        if args.verbose or args.with_stats:
            stats_after = db.get_measurement_age_stats(older_than_days=args.retention_days)
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
