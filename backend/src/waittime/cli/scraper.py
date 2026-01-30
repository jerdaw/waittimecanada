"""CLI for running scrapers.

Usage:
    python -m waittime.cli.scraper --source quebec-msss
    python -m waittime.cli.scraper --all
"""

import argparse
import logging
import sys
from typing import NoReturn

from waittime.scrapers import QuebecScraper, create_quebec_source
from waittime.services import DatabaseService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Registry of available scrapers
SCRAPERS = {
    "quebec-msss": (QuebecScraper, create_quebec_source),
    # Add more as implemented:
    # "alberta-ahs": (AlbertaScraper, create_alberta_source),
}


def run_scraper(source_id: str, dry_run: bool = False) -> int:
    """Run a single scraper.

    Args:
        source_id: ID of the source to scrape
        dry_run: If True, don't write to database

    Returns:
        Number of measurements collected (0 on error)
    """
    if source_id not in SCRAPERS:
        logger.error(f"Unknown source: {source_id}")
        logger.info(f"Available sources: {', '.join(SCRAPERS.keys())}")
        return 0

    scraper_class, source_factory = SCRAPERS[source_id]
    source = source_factory()

    logger.info(f"Starting scraper for {source.name} ({source_id})")

    try:
        with scraper_class(source) as scraper:
            measurements = scraper.run()

        logger.info(f"Collected {len(measurements)} measurements")

        if dry_run:
            logger.info("Dry run - not writing to database")
            for m in measurements[:5]:  # Show first 5
                logger.info(f"  {m.hospital_id}: {m.value} min")
            if len(measurements) > 5:
                logger.info(f"  ... and {len(measurements) - 5} more")
            return len(measurements)

        # Write to database
        db = DatabaseService()
        count = db.insert_measurements(measurements)
        db.update_heartbeat(
            source_id=source_id,
            status="healthy",
            measurements_count=count,
        )

        logger.info(f"Wrote {count} measurements to database")
        return count

    except Exception as e:
        logger.exception(f"Scraper failed for {source_id}: {e}")

        if not dry_run:
            try:
                db = DatabaseService()
                db.update_heartbeat(
                    source_id=source_id,
                    status="error",
                    error_message=str(e)[:500],
                    measurements_count=0,
                )
            except Exception:
                logger.exception("Failed to update heartbeat")

        return 0


def main() -> NoReturn:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run WaitTime Canada scrapers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source",
        "-s",
        help=f"Source to scrape. Options: {', '.join(SCRAPERS.keys())}",
    )
    parser.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Run all available scrapers",
    )
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Don't write to database, just show results",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available scrapers and exit",
    )

    args = parser.parse_args()

    if args.list:
        print("Available scrapers:")
        for source_id in SCRAPERS:
            _, source_factory = SCRAPERS[source_id]
            source = source_factory()
            print(f"  {source_id}: {source.name} ({source.province})")
        sys.exit(0)

    if args.all:
        total = 0
        failed = 0
        for source_id in SCRAPERS:
            count = run_scraper(source_id, dry_run=args.dry_run)
            total += count
            if count == 0:
                failed += 1

        logger.info(f"Completed: {total} measurements from {len(SCRAPERS)} sources")
        if failed:
            logger.warning(f"{failed} scraper(s) failed")
            sys.exit(1)
        sys.exit(0)

    if args.source:
        count = run_scraper(args.source, dry_run=args.dry_run)
        sys.exit(0 if count > 0 else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
