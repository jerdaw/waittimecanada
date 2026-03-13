"""CLI tool for computing measurement aggregates.

Computes and stores permanent statistical aggregates from raw measurements.
Run via cron job, GitHub Actions, or manually for backfill operations.

Usage:
    python -m waittime.cli.aggregate --backfill --days 30
    python -m waittime.cli.aggregate --incremental
    python -m waittime.cli.aggregate --hospital ca-on-ottawa-civic --period daily
    python -m waittime.cli.aggregate --dry-run
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

VALID_PERIOD_TYPES = ["hourly", "daily", "weekly", "monthly"]
INCREMENTAL_PERIOD_TYPES = ["daily", "weekly", "monthly"]


def main() -> int:
    """Run measurement aggregation."""
    parser = argparse.ArgumentParser(description="Compute measurement aggregates")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Compute all missing aggregates for the specified range",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        help="Refresh current daily/weekly/monthly buckets for hospitals with recent data",
    )
    parser.add_argument(
        "--hospital",
        type=str,
        default=None,
        help="Process a specific hospital ID (default: all visible hospitals)",
    )
    parser.add_argument(
        "--period",
        type=str,
        default=None,
        choices=VALID_PERIOD_TYPES,
        help="Compute only this period type (default: all)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="How far back to look for backfill (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be computed without saving",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress",
    )

    args = parser.parse_args()

    if not args.backfill and not args.incremental:
        parser.error("Must specify either --backfill or --incremental")

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if args.incremental and args.period and args.period not in INCREMENTAL_PERIOD_TYPES:
        parser.error("--incremental only supports daily, weekly, or monthly periods")

    try:
        db = DatabaseService()
        service = AggregationService(db)
        period_types: list[str] | None

        if args.incremental:
            now = datetime.now(UTC)
            since = now - timedelta(hours=2)
            period_types = [args.period] if args.period else INCREMENTAL_PERIOD_TYPES
            mode_label = "Incremental refresh (recent daily/weekly/monthly buckets)"
        else:
            now = datetime.now(UTC)
            start_date = now - timedelta(days=args.days)
            period_types = [args.period] if args.period else None
            mode_label = f"Backfill (last {args.days} days)"

        logger.info(f"Aggregation mode: {mode_label}")
        if args.hospital:
            logger.info(f"Hospital: {args.hospital}")
        else:
            logger.info("Hospital: all visible")
        if period_types:
            logger.info(f"Period types: {period_types}")
        else:
            logger.info("Period types: all")
        if args.dry_run:
            logger.info("DRY RUN - no data will be saved")

        if args.incremental:
            counts = service.refresh_recent_periods(
                hospital_id=args.hospital,
                since=since,
                period_types=period_types,
                dry_run=args.dry_run,
            )
        else:
            counts = service.backfill(
                hospital_id=args.hospital,
                start_date=start_date,
                end_date=now,
                period_types=period_types,
                dry_run=args.dry_run,
            )

        total = sum(counts.values())
        logger.info(
            f"Aggregation complete: {total} aggregates {'would be ' if args.dry_run else ''}computed"
        )
        for period_type, count in counts.items():
            if count > 0:
                logger.info(f"  {period_type}: {count}")

        return 0

    except Exception as e:
        logger.error(f"Aggregation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
