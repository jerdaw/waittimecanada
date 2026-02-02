"""CLI tool for seeding data sources from JSON files.

Usage:
    python -m waittime.cli.seed_sources --file data/sources/ontario-health.json
    python -m waittime.cli.seed_sources --list
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from waittime.core import Source
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


def load_source_from_json(file_path: Path) -> Source:
    """Load source from JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Source object

    Raises:
        ValueError: If JSON is invalid or missing required fields
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    try:
        source = Source(**data)
        logger.info(f"Loaded source: {source.id} - {source.name}")
        return source
    except Exception as e:
        logger.error(f"Invalid source data: {e}")
        raise ValueError(f"Source validation failed: {e}") from e


def seed_source(db: DatabaseService, source: Source, dry_run: bool = False) -> bool:
    """Seed source into database.

    Args:
        db: Database service instance
        source: Source to seed
        dry_run: If True, only validate without inserting

    Returns:
        True if inserted, False if already exists
    """
    if dry_run:
        logger.info(f"[DRY RUN] Would upsert: {source.id} - {source.name}")
        return True

    try:
        # Upsert (insert or update)
        db.upsert_source(source)
        logger.info(f"✓ Upserted: {source.id} - {source.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to upsert {source.id}: {e}")
        raise


def list_sources(db: DatabaseService) -> None:
    """List all sources in the database.

    Args:
        db: Database service instance
    """
    sources = db.list_sources()

    if not sources:
        print("No sources found in database")
        return

    print(f"\nData Sources ({len(sources)} total):\n")
    for source in sources:
        print(f"  {source.id:<25} {source.name:<50} [{source.province}]")
        print(f"    URL: {source.url}")
        print(f"    Telehealth: {source.telehealth_name} ({source.telehealth_number})")
        print()


def main() -> int:
    """Main entry point for source seeding CLI."""
    parser = argparse.ArgumentParser(
        description="Seed data sources from JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed a source from file
  python -m waittime.cli.seed_sources --file data/sources/ontario-health.json

  # Dry run (validate without inserting)
  python -m waittime.cli.seed_sources --file data/sources/ontario-health.json --dry-run

  # List existing sources
  python -m waittime.cli.seed_sources --list
        """,
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="Path to JSON file containing source data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without inserting into database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List existing sources in database",
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
    if not args.list and not args.file:
        print("Error: --file is required (or use --list to view existing)")
        return 1

    try:
        db = DatabaseService()

        if args.list:
            # List mode
            list_sources(db)
            return 0

        # Seed mode
        logger.info(f"Loading source from {args.file}...")
        source = load_source_from_json(args.file)

        if args.dry_run:
            logger.info("[DRY RUN MODE - No changes will be made]\n")

        seed_source(db, source, dry_run=args.dry_run)

        if args.dry_run:
            print("\n✓ Dry run complete - no changes made")
        else:
            print("\n✓ Source seeding complete")

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
