"""CLI tool for seeding health regions and hospital mappings.

Usage:
    python -m waittime.cli.seed_regions --file data/regions/ontario-regions.json
    python -m waittime.cli.seed_regions --file data/regions/ontario-regions.json --dry-run
    python -m waittime.cli.seed_regions --province ON --list
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


REQUIRED_REGION_FIELDS = {"id", "name", "code", "hospitals"}


def load_regions_from_json(
    file_path: Path,
    province_override: str | None = None,
) -> dict[str, Any]:
    """Load and validate region seed payload."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding="utf-8") as handle:
        payload = json.load(handle)

    province = (province_override or payload.get("province", "")).upper()
    if not province:
        raise ValueError("Province must be provided via --province or in JSON file")

    regions = payload.get("regions", [])
    if not isinstance(regions, list) or not regions:
        raise ValueError("JSON must include a non-empty 'regions' array")

    normalized_regions: list[dict[str, Any]] = []
    for index, region in enumerate(regions, start=1):
        if not isinstance(region, dict):
            raise ValueError(f"Region at index {index} must be an object")

        missing = REQUIRED_REGION_FIELDS - set(region)
        if missing:
            missing_fields = ", ".join(sorted(missing))
            raise ValueError(f"Region at index {index} is missing fields: {missing_fields}")

        hospitals = region.get("hospitals")
        if not isinstance(hospitals, list) or not all(isinstance(value, str) for value in hospitals):
            raise ValueError(f"Region at index {index} must have 'hospitals' as a list of IDs")

        normalized_regions.append(
            {
                "id": str(region["id"]),
                "name": str(region["name"]),
                "code": str(region["code"]).upper(),
                "sort_order": int(region.get("sort_order", index)),
                "metadata": {
                    "description": str(region.get("description", "")).strip(),
                },
                "hospitals": hospitals,
            }
        )

    return {
        "province": province,
        "regions": normalized_regions,
    }


def seed_regions(
    db: DatabaseService,
    province: str,
    regions: list[dict[str, Any]],
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """Seed region records and hospital mappings.

    Returns:
        Tuple of (regions_upserted, mappings_upserted, missing_hospitals)
    """
    regions_upserted = 0
    mappings_upserted = 0
    missing_hospitals = 0

    if not dry_run:
        removed = db.clear_hospital_regions_for_province(province)
        logger.info(f"Cleared {removed} existing mappings for {province}")

    for region in regions:
        if dry_run:
            logger.info(
                f"[DRY RUN] Would upsert region {region['id']} ({region['name']}) in {province}"
            )
        else:
            db.upsert_region(
                region_id=region["id"],
                province=province,
                name=region["name"],
                code=region["code"],
                sort_order=region["sort_order"],
                metadata=region["metadata"],
            )
        regions_upserted += 1

        for hospital_id in region["hospitals"]:
            if dry_run:
                logger.info(
                    f"[DRY RUN] Would map hospital {hospital_id} -> {region['id']}"
                )
                mappings_upserted += 1
                continue

            if db.get_hospital(hospital_id) is None:
                logger.warning(
                    f"Skipping unknown hospital '{hospital_id}' for region '{region['id']}'"
                )
                missing_hospitals += 1
                continue

            db.upsert_hospital_region(region_id=region["id"], hospital_id=hospital_id)
            mappings_upserted += 1

    return regions_upserted, mappings_upserted, missing_hospitals


def list_regions_by_province(db: DatabaseService, province: str) -> None:
    """Print region records and mapping counts for a province."""
    regions = db.list_regions(province=province)
    mappings = db.list_hospital_regions(province=province)

    hospitals_by_region: dict[str, list[str]] = {}
    for mapping in mappings:
        hospitals_by_region.setdefault(str(mapping["region_id"]), []).append(
            str(mapping["hospital_id"])
        )

    if not regions:
        print(f"No regions found for province: {province}")
        return

    print(f"\nRegions for province '{province}' ({len(regions)} total):\n")
    for region in regions:
        hospital_ids = hospitals_by_region.get(str(region["id"]), [])
        print(
            f"  {region['code']:<10} {region['name']:<30}"
            f" hospitals={len(hospital_ids)}"
        )


def main() -> int:
    """Main entry point for region seed CLI."""
    parser = argparse.ArgumentParser(
        description="Seed regions and hospital mappings from JSON files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Seed regions from file
  python -m waittime.cli.seed_regions --file data/regions/ontario-regions.json

  # Dry run (validate only)
  python -m waittime.cli.seed_regions --file data/regions/ontario-regions.json --dry-run

  # List existing seeded regions
  python -m waittime.cli.seed_regions --province ON --list
        """,
    )

    parser.add_argument(
        "--file",
        type=Path,
        help="Path to JSON file containing region and hospital mapping data",
    )
    parser.add_argument(
        "--province",
        help="Province override/filter (e.g., ON)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate data without writing to database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List seeded regions for a province",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if args.list and not args.province:
        print("Error: --province is required with --list")
        return 1

    if not args.list and not args.file:
        print("Error: --file is required (or use --list)")
        return 1

    try:
        db = DatabaseService()

        if args.list:
            list_regions_by_province(db, str(args.province).upper())
            return 0

        payload = load_regions_from_json(args.file, args.province)
        province = str(payload["province"]).upper()
        regions = payload["regions"]

        logger.info(f"Loaded {len(regions)} region rows for {province}")
        if args.dry_run:
            logger.info("[DRY RUN MODE - No changes will be made]")

        regions_upserted, mappings_upserted, missing_hospitals = seed_regions(
            db=db,
            province=province,
            regions=regions,
            dry_run=args.dry_run,
        )

        print(f"\n{'─' * 60}")
        print("Summary:")
        print(f"  Regions upserted:   {regions_upserted}")
        print(f"  Mappings upserted:  {mappings_upserted}")
        print(f"  Missing hospitals:  {missing_hospitals}")
        print(f"{'─' * 60}\n")

        if args.dry_run:
            print("✓ Dry run complete - no changes made")
        else:
            print("✓ Region seeding complete")

        return 0

    except FileNotFoundError as exc:
        logger.error(f"File error: {exc}")
        return 1
    except ValueError as exc:
        logger.error(f"Validation error: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        logger.error(f"Unexpected error: {exc}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
