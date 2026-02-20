"""CLI for generating daily data quality snapshots.

Provides a command-line interface to compute and save daily data quality
metrics for all hospitals. Can be run for a specific date or used to
backfill a range of dates.
"""

import argparse
import logging
import sys
from datetime import UTC, datetime, timedelta

from waittime.services.data_quality import DataQualityService
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging level and format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def main() -> int:
    """Entry point for the snapshot CLI."""
    parser = argparse.ArgumentParser(
        description="Generate daily data quality snapshots for all hospitals."
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Date to snapshot (YYYY-MM-DD). Defaults to yesterday.",
    )
    parser.add_argument(
        "--backfill-days",
        type=int,
        help="Run snapshots for the last N days up to the target date. Idempotent.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable detailed debug logging.",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    db = None
    try:
        db = DatabaseService()
        quality_service = DataQualityService(db)

        # Determine target date
        if args.date:
            try:
                target_date = datetime.strptime(args.date, "%Y-%m-%d").replace(tzinfo=UTC)
            except ValueError:
                logger.error("Invalid date format. Expected YYYY-MM-DD.")
                return 1
        else:
            # Default to yesterday (safest, since today is not yet complete)
            target_date = datetime.now(UTC) - timedelta(days=1)

        dates_to_run = [target_date]

        if args.backfill_days and args.backfill_days > 1:
            dates_to_run = [target_date - timedelta(days=i) for i in range(args.backfill_days)]
            # Process oldest first
            dates_to_run.reverse()

        total_saved = 0
        for date in dates_to_run:
            logger.info("Running quality snapshot for date: %s", date.date().isoformat())
            saved = quality_service.snapshot_daily_quality(date)
            total_saved += saved

        logger.info(
            "Snapshot operation completed. Processed %d dates, total %d snapshots saved.",
            len(dates_to_run),
            total_saved,
        )

        return 0

    except Exception as e:
        logger.error("Failed to run snapshot generation: %s", str(e), exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
