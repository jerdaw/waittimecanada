"""CLI tool for seeding hospitals from JSON data files.

Usage:
    python -m waittime.cli.seed --file data/hospitals/ontario-seed.json
    python -m waittime.cli.seed --file data/hospitals/ontario-seed.json --dry-run
    python -m waittime.cli.seed --source ontario-health --list
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from waittime.core import Hospital
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


def load_hospitals_from_json(file_path: Path, source_id: str) -> list[Hospital]:
    """Load hospitals from JSON file.

    Args:
        file_path: Path to JSON file
        source_id: Source ID to assign to hospitals

    Returns:
        List of Hospital objects

    Raises:
        ValueError: If JSON is invalid or missing required fields
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    # Allow source_id override or use from file
    effective_source_id = source_id or data.get("source_id")
    if not effective_source_id:
        raise ValueError("source_id must be provided via --source or in JSON file")

    hospitals_data = data.get("hospitals", [])
    if not hospitals_data:
        raise ValueError("No hospitals found in JSON file")

    hospitals = []
    for i, hospital_data in enumerate(hospitals_data, 1):
        try:
            # Ensure source_id is set
            hospital_data["source_id"] = effective_source_id
            hospital = Hospital(**hospital_data)
            hospitals.append(hospital)
        except Exception as e:
            logger.error(f"Invalid hospital at index {i}: {e}")
            raise ValueError(f"Hospital validation failed at index {i}: {e}") from e

    logger.info(f"Loaded {len(hospitals)} hospitals from {file_path}")
    return hospitals


def seed_hospitals(
    db: DatabaseService, hospitals: list[Hospital], dry_run: bool = False
) -> tuple[int, int]:
    """Seed hospitals into database.

    Args:
        db: Database service instance
        hospitals: List of hospitals to seed
        dry_run: If True, only validate without inserting

    Returns:
        Tuple of (inserted_count, skipped_count)
    """
    inserted = 0
    skipped = 0

    for hospital in hospitals:
        if dry_run:
            logger.info(f"[DRY RUN] Would insert: {hospital.id} - {hospital.name}")
            inserted += 1
            continue

        try:
            # Check if hospital already exists
            existing = db.get_hospital(hospital.id)
            if existing:
                logger.warning(f"Hospital {hospital.id} already exists, skipping")
                skipped += 1
                continue

            # Insert hospital
            db.insert_hospital(hospital)
            logger.info(f"✓ Inserted: {hospital.id} - {hospital.name}")
            inserted += 1

        except Exception as e:
            logger.error(f"Failed to insert {hospital.id}: {e}")
            raise

    return inserted, skipped


def list_hospitals_by_source(db: DatabaseService, source_id: str) -> None:
    """List all hospitals for a given source.

    Args:
        db: Database service instance
        source_id: Source ID to filter by
    """
    hospitals = db.get_hospitals_by_source(source_id)

    if not hospitals:
        print(f"No hospitals found for source: {source_id}")
        return

    print(f"\nHospitals for source '{source_id}' ({len(hospitals)} total):\n")
    for hospital in hospitals:
        status = "✓ visible" if hospital.is_visible else "○ hidden"
        verified = "✓" if hospital.is_verified else "✗"
        print(f"  [{verified}] {hospital.id:<30} {hospital.name:<50} {status}")


def main() -> int:
    """Main entry point for seed CLI."""
    parser = argparse.ArgumentParser(
        description="Seed hospitals from JSON data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed hospitals from file
  python -m waittime.cli.seed --file data/hospitals/ontario-seed.json

  # Dry run (validate without inserting)
  python -m waittime.cli.seed --file data/hospitals/ontario-seed.json --dry-run

  # Override source ID
  python -m waittime.cli.seed --file hospitals.json --source custom-source

  # List existing hospitals for a source
  python -m waittime.cli.seed --source ontario-health --list
        """,
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="Path to JSON file containing hospital data",
    )
    parser.add_argument(
        "--source",
        help="Source ID (overrides source_id in JSON file)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without inserting into database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing hospitals for the specified source",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    # Validate arguments
    if args.list:
        if not args.source:
            print("Error: --source is required with --list")
            return 1
    else:
        if not args.file:
            print("Error: --file is required (or use --list to view existing)")
            return 1

    try:
        db = DatabaseService()

        if args.list:
            # List mode
            list_hospitals_by_source(db, args.source)
            return 0

        # Seed mode
        logger.info(f"Loading hospitals from {args.file}...")
        hospitals = load_hospitals_from_json(args.file, args.source)

        logger.info(f"\nSeeding {len(hospitals)} hospitals...")
        if args.dry_run:
            logger.info("[DRY RUN MODE - No changes will be made]\n")

        inserted, skipped = seed_hospitals(db, hospitals, dry_run=args.dry_run)

        # Summary
        print(f"\n{'─' * 60}")
        print("Summary:")
        print(f"  Inserted: {inserted}")
        print(f"  Skipped:  {skipped}")
        print(f"  Total:    {len(hospitals)}")
        print(f"{'─' * 60}\n")

        if args.dry_run:
            print("✓ Dry run complete - no changes made")
        else:
            print("✓ Seeding complete")

        return 0

    except FileNotFoundError as e:
        logger.error(f"File error: {e}")
        return 1
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
