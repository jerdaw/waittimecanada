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
from waittime.services import DatabaseService, GeocodingService

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


def hospital_id_to_name(hospital_id: str) -> str:
    """Convert hospital ID slug to searchable name.

    Args:
        hospital_id: ID like "ca-on-cheo" or "ca-on-ottawa-hospital-civic"

    Returns:
        Human-readable name like "CHEO" or "Ottawa Hospital Civic"

    Example:
        >>> hospital_id_to_name("ca-on-cheo")
        "CHEO"
        >>> hospital_id_to_name("ca-on-ottawa-hospital-the-civic-site")
        "Ottawa Hospital The Civic Site"
    """
    # Remove country-province prefix (e.g., "ca-on-")
    parts = hospital_id.split("-")
    if len(parts) >= 3 and parts[0] == "ca":
        # Remove "ca" and province code
        name_parts = parts[2:]
    else:
        name_parts = parts

    # Convert kebab-case to Title Case
    # "ottawa-hospital-civic" -> "Ottawa Hospital Civic"
    return " ".join(word.title() for word in name_parts)


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
        geocoder = GeocodingService()

        # Step 1: Upsert hospitals (create if they don't exist)
        # Extract unique hospital IDs
        unique_hospital_ids = {m.hospital_id for m in measurements}
        logger.info(f"Upserting {len(unique_hospital_ids)} unique hospitals")

        geocoded_count = 0
        skipped_count = 0
        for hospital_id in unique_hospital_ids:
            # Check if hospital already exists with valid coordinates
            existing_hospital = db.get_hospital(hospital_id)
            if existing_hospital and existing_hospital.latitude != 0.0 and existing_hospital.longitude != 0.0:
                # Hospital already has valid coordinates, skip geocoding
                skipped_count += 1
                continue

            # Try to get official name from scraper's mapping
            hospital_name = None
            if hasattr(scraper_class, "HOSPITAL_MAPPING"):
                # Reverse lookup: find the key that maps to this hospital_id
                reverse_map = {v: k for k, v in scraper_class.HOSPITAL_MAPPING.items()}
                hospital_name = reverse_map.get(hospital_id)

            # Fall back to converting ID to name
            if not hospital_name:
                hospital_name = hospital_id_to_name(hospital_id)

            # Try to geocode using the hospital name
            geocoding_result = geocoder.geocode_hospital(
                hospital_name, 
                province=source.province,
                hospital_id=hospital_id
            )

            if geocoding_result:
                # Use geocoded data (accept any confidence level)
                city = geocoding_result.city
                latitude = geocoding_result.latitude
                longitude = geocoding_result.longitude
                geocoded_count += 1
                logger.info(
                    f"Geocoded {hospital_name}: ({latitude:.4f}, {longitude:.4f}) "
                    f"confidence={geocoding_result.confidence:.2f}"
                )
            else:
                # Fall back to placeholders
                logger.warning(
                    f"Failed to geocode {hospital_name} ({hospital_id}) - using placeholders"
                )
                city = "Unknown"
                latitude = 0.0
                longitude = 0.0

            # Create hospital with geocoded or placeholder data
            hospital = Hospital(
                id=hospital_id,
                name=hospital_name,  # Use official or converted name
                province=source.province,
                city=city,
                latitude=latitude,
                longitude=longitude,
                is_verified=False,  # Still requires manual verification
                is_visible=False,  # Hidden until verified
                source_id=source_id,
            )
            db.upsert_hospital(hospital)

        logger.info(
            f"✅ Geocoded {geocoded_count} new hospitals, "
            f"skipped {skipped_count} existing (total {len(unique_hospital_ids)})"
        )

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
        for source_id in SCRAPERS:
            _, source_factory = SCRAPERS[source_id]
            source_factory()
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
        
        # Exit with success if we collected ANY data
        if total > 0:
            logger.info(f"Successfully collected {total} measurements total")
            sys.exit(0)
        
        # Only fail if we collected NOTHING and had failures
        if failed > 0:
            logger.error("All scrapers failed")
            sys.exit(1)
            
        sys.exit(0)

    if args.source:
        count = run_scraper(args.source, dry_run=args.dry_run)
        sys.exit(0 if count > 0 else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
