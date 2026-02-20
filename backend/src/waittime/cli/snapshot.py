"""CLI tool for generating data quality snapshots."""

import argparse
import logging
import sys
from datetime import UTC

from waittime.services.data_quality import DataQualityService
from waittime.services.database import DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Run data quality snapshots for all sources."""
    parser = argparse.ArgumentParser(description="Generate daily data quality snapshots")
    parser.add_argument("--dry-run", action="store_true", help="Do not save, just print")
    args = parser.parse_args()

    try:
        from datetime import datetime

        db = DatabaseService()
        svc = DataQualityService(db)

        now = datetime.now(UTC)
        logger.info(f"Running daily quality snapshot for {now.date()}")

        if not args.dry_run:
            saved = svc.snapshot_daily_quality(now)
            logger.info(f"Daily quality snapshot completed successfully. Saved {saved} records.")
        else:
            logger.info("Dry run complete (no records saved).")
        return 0
    except Exception as e:
        logger.error(f"Snapshot generation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
