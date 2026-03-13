"""CLI command for backend data maintenance tasks.

The default behavior is non-destructive:
1. report raw-measurement age statistics
2. report lightweight maintenance status

Raw measurement deletion is now opt-in and requires an explicit purge flag.

Usage:
    python -m waittime.cli.cleanup --dry-run
    python -m waittime.cli.cleanup
    python -m waittime.cli.cleanup --with-stats
    python -m waittime.cli.cleanup --purge-old-measurements --retention-days 60
"""

import argparse
import logging
import sys

from waittime.services.database import DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run backend data maintenance."""
    parser = argparse.ArgumentParser(
        description="Run lightweight maintenance and optionally purge old raw rows"
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=30,
        help="Number of days to retain measurements when purge is explicitly enabled (default: 30)",
    )
    parser.add_argument(
        "--purge-old-measurements",
        action="store_true",
        help="Actually delete raw measurements older than --retention-days",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview maintenance and any requested purge without mutating data",
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
        help="Collect full-table age statistics during maintenance output",
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
            if args.purge_old_measurements:
                if stats_before is not None:
                    logger.info(
                        "Would delete approximately %s measurements older than %s days",
                        stats_before["measurements_older_than_threshold"],
                        args.retention_days,
                    )
                else:
                    logger.info(
                        "Purge requested, but no stats were collected; rerun with --with-stats "
                        "for an estimate before deletion."
                    )
            else:
                logger.info("Raw measurements will be preserved; no purge requested.")
            return 0

        logger.info(
            "\nSkipping aggregate refresh in maintenance. "
            "Current buckets are refreshed by the post-scrape aggregation path."
        )

        deleted_count = 0
        if args.purge_old_measurements:
            logger.info(f"\nDeleting measurements older than {args.retention_days} days...")
            deleted_count = db.cleanup_old_measurements(retention_days=args.retention_days)
        else:
            logger.info(
                "\nSkipping raw measurement deletion. "
                "Indefinite raw-data retention is the current default policy."
            )

        logger.info("\n✅ Maintenance complete!")
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
