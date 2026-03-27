"""Seed public health hub resources from approved source files.

Usage:
    python -m waittime.cli.seed_public_health_resources --mohserlo-file path/to/mohserlo.csv
    python -m waittime.cli.seed_public_health_resources --mohserlo-file file.csv --odhf-file file.csv
    python -m waittime.cli.seed_public_health_resources --osm-aed-file ontario-aed.json
    python -m waittime.cli.seed_public_health_resources --fetch-mohserlo-live --fetch-osm-aed-live
    python -m waittime.cli.seed_public_health_resources --list
"""

import argparse
import logging
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from waittime.services.database import DatabaseService
from waittime.services.public_health_resources import (
    FacilityIngestSummary,
    PublicHealthResourceService,
    load_text_file,
    normalize_mohserlo_geojson,
    normalize_osm_aed_overpass_json,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for public health resource seeding."""
    parser = argparse.ArgumentParser(
        description="Seed public health hub resources from approved facility files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m waittime.cli.seed_public_health_resources --mohserlo-file mohserlo.csv
  python -m waittime.cli.seed_public_health_resources --mohserlo-file mohserlo.csv --odhf-file odhf.csv
  python -m waittime.cli.seed_public_health_resources --osm-aed-file ontario-aed.json
  python -m waittime.cli.seed_public_health_resources --fetch-mohserlo-live --fetch-osm-aed-live
  python -m waittime.cli.seed_public_health_resources --list
        """,
    )
    parser.add_argument("--mohserlo-file", type=Path, help="Path to MOHSERLO CSV export")
    parser.add_argument("--odhf-file", type=Path, help="Path to ODHF CSV export")
    parser.add_argument(
        "--osm-aed-file",
        type=Path,
        help="Path to an OpenStreetMap / Overpass AED JSON export",
    )
    parser.add_argument(
        "--fetch-mohserlo-live",
        action="store_true",
        help="Fetch MOHSERLO directly from the approved Ontario ArcGIS feature service",
    )
    parser.add_argument(
        "--fetch-osm-aed-live",
        action="store_true",
        help="Fetch Ontario AED fallback data directly from the approved Overpass query",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and summarize records without writing to the database",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List currently stored public health hub source metadata",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if (
        not args.list
        and not args.mohserlo_file
        and not args.odhf_file
        and not args.osm_aed_file
        and not args.fetch_mohserlo_live
        and not args.fetch_osm_aed_live
    ):
        print("Error: provide a file flag, a live-fetch flag, or use --list")
        return 1

    try:
        db = DatabaseService()
        service = PublicHealthResourceService(db)

        if args.list:
            sources = db.list_public_data_sources()
            if not sources:
                print("No public data sources found.")
                return 0

            print("\nPublic data sources:\n")
            for source in sources:
                print(f"  {source.source_id:<12} {source.source_name}")
                print(f"    Mode: {source.recommended_usage_mode}")
                print(f"    Last refreshed: {source.last_refreshed_at}")
                print(f"    Provenance: {source.provenance_url}")
                print()
            return 0

        if args.dry_run:
            logger.info("[DRY RUN MODE - No changes will be made]\n")
        else:
            service.ensure_batch_a_facility_sources()
            service.ensure_aed_sources()

        if args.mohserlo_file:
            _process_file(
                file_path=args.mohserlo_file,
                label="MOHSERLO",
                dry_run=args.dry_run,
                loader=lambda text: service.ingest_mohserlo_csv(text),
            )

        if args.odhf_file:
            _process_file(
                file_path=args.odhf_file,
                label="ODHF",
                dry_run=args.dry_run,
                loader=lambda text: service.ingest_odhf_csv(text),
            )

        if args.osm_aed_file:
            _process_file(
                file_path=args.osm_aed_file,
                label="OpenStreetMap AED",
                dry_run=args.dry_run,
                loader=lambda text: service.ingest_osm_aed_overpass_json(text),
            )

        if args.fetch_mohserlo_live:
            _process_live_payload(
                label="MOHSERLO",
                dry_run=args.dry_run,
                fetcher=service.fetch_mohserlo_geojson,
                dry_run_counter=lambda text: len(
                    normalize_mohserlo_geojson(text, refreshed_at=_now())
                ),
                loader=lambda text: service.ingest_mohserlo_geojson(text),
            )

        if args.fetch_osm_aed_live:
            _process_live_payload(
                label="OpenStreetMap AED",
                dry_run=args.dry_run,
                fetcher=service.fetch_osm_aed_overpass_json,
                dry_run_counter=lambda text: len(
                    normalize_osm_aed_overpass_json(text, refreshed_at=_now())
                ),
                loader=lambda text: service.ingest_osm_aed_overpass_json(text),
            )

        return 0
    except FileNotFoundError as exc:
        logger.error("File error: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=args.verbose)
        return 1


def _process_file(
    *,
    file_path: Path,
    label: str,
    dry_run: bool,
    loader: Callable[[str], FacilityIngestSummary],
) -> None:
    logger.info("Loading %s from %s...", label, file_path)
    text = load_text_file(file_path)

    if dry_run:
        logger.info("[DRY RUN] Loaded %s (%s bytes)", label, len(text))
        return

    summary = loader(text)
    logger.info("✓ Seeded %s facility records: %s", label, summary.records_loaded)


def _process_live_payload(
    *,
    label: str,
    dry_run: bool,
    fetcher: Callable[[], str],
    dry_run_counter: Callable[[str], int],
    loader: Callable[[str], FacilityIngestSummary],
) -> None:
    logger.info("Fetching %s from approved upstream...", label)
    payload = fetcher()

    if dry_run:
        logger.info("[DRY RUN] Fetched %s (%s bytes)", label, len(payload))
        logger.info("[DRY RUN] Normalized %s records: %s", label, dry_run_counter(payload))
        return

    summary = loader(payload)
    logger.info("✓ Seeded %s records: %s", label, summary.records_loaded)


def _now() -> datetime:
    return datetime.now(UTC)


if __name__ == "__main__":
    sys.exit(main())
