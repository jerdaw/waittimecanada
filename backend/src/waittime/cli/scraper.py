"""CLI for running scrapers.

Usage:
    python -m waittime.cli.scraper --source quebec-msss
    python -m waittime.cli.scraper --all
"""

import argparse
import logging
import sys
from typing import NoReturn

from waittime.core import Hospital
from waittime.scrapers import (
    OntarioScraper,
    QuebecScraper,
    create_ontario_source,
    create_quebec_source,
)
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
    "ontario-health": (OntarioScraper, create_ontario_source),
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

        # Step 1: Upsert hospitals (create if they don't exist)
        # Extract unique hospital IDs
        unique_hospital_ids = {m.hospital_id for m in measurements}
        logger.info(f"Upserting {len(unique_hospital_ids)} unique hospitals")

        for hospital_id in unique_hospital_ids:
            # Find first measurement to get source info
            sample = next(m for m in measurements if m.hospital_id == hospital_id)

            # Create hospital with unverified status
            # Use placeholder values - admin will update during verification
            hospital = Hospital(
                id=hospital_id,
                name=hospital_id,  # Use ID as name for now, admin will update
                province=source.province,
                city="Unknown",  # Placeholder
                latitude=0.0,  # Placeholder
                longitude=0.0,  # Placeholder
                is_verified=False,  # Requires manual verification
                is_visible=False,  # Hidden until verified
                source_id=source_id,
            )
            db.upsert_hospital(hospital)

        # Step 2: Insert measurements
        count = db.insert_measurements(measurements)

        # Step 3: Update heartbeat
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
