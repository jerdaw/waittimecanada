"""Audit and auto-assign hospital-to-region mappings.

Usage:
    python -m waittime.cli.region_mapping --province ON
    python -m waittime.cli.region_mapping --province ON --auto-assign
    python -m waittime.cli.region_mapping --province ON --auto-assign --dry-run
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from waittime.core import Hospital
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)

DEFAULT_OVERRIDES_FILE = (
    Path(__file__).resolve().parents[3] / "data" / "regions" / "ontario-region-overrides.json"
)
REQUIRED_REGION_CODES = {"EAST", "TORONTO", "CENTRAL", "WEST", "NORTH"}

TORONTO_TOKENS = (
    "toronto",
    "north york",
    "scarborough",
    "etobicoke",
    "downtown toronto",
    "east york",
)
EAST_TOKENS = (
    "ottawa",
    "kingston",
    "cornwall",
    "brockville",
    "pembroke",
    "hawkesbury",
    "arnprior",
    "smiths falls",
    "carleton place",
    "kemptville",
    "alexandria",
)
WEST_TOKENS = (
    "london",
    "windsor",
    "sarnia",
    "chatham",
    "stratford",
    "woodstock",
    "guelph",
    "kitchener",
    "waterloo",
    "cambridge",
)
NORTH_TOKENS = (
    "sudbury",
    "thunder bay",
    "north bay",
    "timmins",
    "sault ste marie",
    "kenora",
    "dryden",
    "nipigon",
    "englehart",
    "manitouwadge",
    "mattawa",
)


def normalize_text(value: str) -> str:
    """Normalize free text for token matching."""
    normalized = re.sub(r"[^a-z0-9\s]", " ", value.lower())
    return re.sub(r"\s+", " ", normalized).strip()


def load_overrides(file_path: Path) -> dict[str, str]:
    """Load hospital_id -> region_code overrides from JSON."""
    if not file_path.exists():
        return {}

    with open(file_path, encoding="utf-8") as handle:
        payload = json.load(handle)

    mappings = payload.get("mappings", {})
    if not isinstance(mappings, dict):
        raise ValueError("'mappings' must be an object in overrides JSON")

    normalized: dict[str, str] = {}
    for hospital_id, region_code in mappings.items():
        if not isinstance(hospital_id, str) or not isinstance(region_code, str):
            continue
        normalized[hospital_id] = region_code.upper()

    return normalized


def assign_region_code(hospital: Hospital, overrides: dict[str, str]) -> tuple[str, str]:
    """Assign a region code using overrides, tokens, and coordinate heuristics."""
    override = overrides.get(hospital.id)
    if override:
        return override, "override"

    text_blob = normalize_text(f"{hospital.name} {hospital.city}")

    if any(token in text_blob for token in TORONTO_TOKENS):
        return "TORONTO", "token"
    if any(token in text_blob for token in EAST_TOKENS):
        return "EAST", "token"
    if any(token in text_blob for token in WEST_TOKENS):
        return "WEST", "token"
    if any(token in text_blob for token in NORTH_TOKENS):
        return "NORTH", "token"

    lat = hospital.latitude
    lon = hospital.longitude

    # Northern Ontario tends to be much farther north than the dense southern corridor.
    if lat >= 47.0:
        return "NORTH", "latitude"

    # Greater Toronto Area fallback.
    if 43.4 <= lat <= 44.3 and -80.2 <= lon <= -78.7:
        return "TORONTO", "bbox"

    # Eastern Ontario roughly spans Kingston to Ottawa corridor and farther east.
    if lon >= -78.3:
        return "EAST", "longitude"

    # Southwestern Ontario cluster.
    if lon <= -81.1 and lat < 46.7:
        return "WEST", "longitude"

    # Remaining southern corridor defaults to Central.
    if lat < 46.7:
        return "CENTRAL", "fallback"

    return "NORTH", "fallback"


def build_coverage_report(
    hospitals: list[Hospital],
    mappings: list[dict[str, Any]],
    regions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compute mapping coverage and regional distribution report."""
    hospital_ids = {hospital.id for hospital in hospitals}
    region_code_by_id = {str(region["id"]): str(region["code"]) for region in regions}

    mapped_rows = [
        mapping for mapping in mappings if str(mapping.get("hospital_id")) in hospital_ids
    ]
    mapped_ids = {str(mapping["hospital_id"]) for mapping in mapped_rows}
    unmapped_ids = sorted(hospital_ids - mapped_ids)

    region_counts: Counter[str] = Counter()
    for mapping in mapped_rows:
        region_id = str(mapping.get("region_id"))
        region_code = region_code_by_id.get(region_id, "UNKNOWN")
        region_counts[region_code] += 1

    total_hospitals = len(hospital_ids)
    mapped_hospitals = len(mapped_ids)
    coverage_percent = (
        round((mapped_hospitals / total_hospitals) * 100, 1) if total_hospitals > 0 else 0.0
    )

    return {
        "total_hospitals": total_hospitals,
        "mapped_hospitals": mapped_hospitals,
        "unmapped_hospitals": len(unmapped_ids),
        "coverage_percent": coverage_percent,
        "region_counts": dict(sorted(region_counts.items())),
        "unmapped_ids": unmapped_ids,
    }


def auto_assign_regions(
    db: DatabaseService,
    province: str,
    overrides: dict[str, str],
    dry_run: bool = False,
    remap_all: bool = False,
    visible_only: bool = True,
) -> dict[str, Any]:
    """Assign regions for unmapped (or all) hospitals using heuristics."""
    regions = db.list_regions(province=province)
    region_id_by_code = {str(region["code"]).upper(): str(region["id"]) for region in regions}

    missing_codes = REQUIRED_REGION_CODES - set(region_id_by_code)
    if missing_codes:
        raise ValueError(
            f"Missing required regions for {province}: {', '.join(sorted(missing_codes))}"
        )

    hospitals = db.list_hospitals(province=province, visible_only=visible_only)
    existing_mappings = db.list_hospital_regions(province=province)
    mapped_hospital_ids = {str(mapping["hospital_id"]) for mapping in existing_mappings}

    assigned = 0
    skipped_existing = 0
    assigned_by_code: Counter[str] = Counter()
    assignment_reasons: Counter[str] = Counter()

    for hospital in hospitals:
        if not remap_all and hospital.id in mapped_hospital_ids:
            skipped_existing += 1
            continue

        region_code, reason = assign_region_code(hospital, overrides)
        region_id = region_id_by_code.get(region_code)
        if not region_id:
            continue

        if not dry_run:
            db.upsert_hospital_region(region_id=region_id, hospital_id=hospital.id, is_primary=True)

        assigned += 1
        assigned_by_code[region_code] += 1
        assignment_reasons[reason] += 1

    return {
        "assigned": assigned,
        "skipped_existing": skipped_existing,
        "assigned_by_code": dict(sorted(assigned_by_code.items())),
        "assignment_reasons": dict(sorted(assignment_reasons.items())),
    }


def print_report(province: str, report: dict[str, Any], include_unmapped: bool) -> None:
    """Print human-readable coverage report."""
    print("\n" + ("-" * 64))
    print(f"Region mapping coverage report ({province})")
    print(f"  Total hospitals:    {report['total_hospitals']}")
    print(f"  Mapped hospitals:   {report['mapped_hospitals']}")
    print(f"  Unmapped hospitals: {report['unmapped_hospitals']}")
    print(f"  Coverage:           {report['coverage_percent']:.1f}%")
    print("  Regional distribution:")
    for code, count in report["region_counts"].items():
        print(f"    {code:<8} {count}")
    if include_unmapped and report["unmapped_ids"]:
        print("  Unmapped IDs:")
        for hospital_id in report["unmapped_ids"]:
            print(f"    - {hospital_id}")
    print("-" * 64 + "\n")


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Audit and auto-assign hospital region mappings")
    parser.add_argument("--province", default="ON", help="Province code (default: ON)")
    parser.add_argument(
        "--overrides-file",
        type=Path,
        default=DEFAULT_OVERRIDES_FILE,
        help=f"Optional JSON overrides file (default: {DEFAULT_OVERRIDES_FILE})",
    )
    parser.add_argument(
        "--auto-assign",
        action="store_true",
        help="Auto-assign region mappings for unmapped hospitals",
    )
    parser.add_argument(
        "--remap-all",
        action="store_true",
        help="Recompute mapping for all hospitals (not just unmapped)",
    )
    parser.add_argument(
        "--all-hospitals",
        action="store_true",
        help="Include unverified/hidden hospitals in audit and auto-assignment",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview assignments without writing mappings",
    )
    parser.add_argument(
        "--include-unmapped",
        action="store_true",
        help="Print full unmapped hospital ID list",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Write report JSON to file",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    province = str(args.province).upper()

    try:
        db = DatabaseService()
        overrides = load_overrides(args.overrides_file)
        if overrides:
            logger.info("Loaded %d mapping overrides", len(overrides))
        elif args.overrides_file.exists():
            logger.info("Overrides file exists but contains no mappings")
        else:
            logger.info("Overrides file not found; proceeding without overrides")

        if args.auto_assign:
            assignment = auto_assign_regions(
                db=db,
                province=province,
                overrides=overrides,
                dry_run=args.dry_run,
                remap_all=args.remap_all,
                visible_only=not args.all_hospitals,
            )
            print("\nAuto-assignment summary:")
            print(f"  Assigned:         {assignment['assigned']}")
            print(f"  Skipped existing: {assignment['skipped_existing']}")
            if assignment["assigned_by_code"]:
                print("  Assigned by region:")
                for code, count in assignment["assigned_by_code"].items():
                    print(f"    {code:<8} {count}")
            if assignment["assignment_reasons"]:
                print("  Assignment reasons:")
                for reason, count in assignment["assignment_reasons"].items():
                    print(f"    {reason:<10} {count}")
            if args.dry_run:
                print("  [DRY RUN] No mappings written")

        hospitals = db.list_hospitals(province=province, visible_only=not args.all_hospitals)
        mappings = db.list_hospital_regions(province=province)
        regions = db.list_regions(province=province)
        report = build_coverage_report(hospitals, mappings, regions)
        print_report(province, report, include_unmapped=args.include_unmapped)

        if args.output_json:
            payload = {
                "province": province,
                "report": report,
            }
            args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"Saved report to: {args.output_json}")

        return 0
    except Exception as exc:  # pragma: no cover - CLI boundary
        logger.error("Region mapping command failed: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
