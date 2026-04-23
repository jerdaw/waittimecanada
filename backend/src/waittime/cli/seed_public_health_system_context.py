"""Seed approved Ontario EMS system-context data.

Usage:
    python -m waittime.cli.seed_public_health_system_context --average-response-times-file path.csv --paramedic-performance-file path.csv
    python -m waittime.cli.seed_public_health_system_context --fetch-live
    python -m waittime.cli.seed_public_health_system_context --list
"""

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from waittime.services.database import DatabaseService
from waittime.services.public_health_system_context import (
    PublicHealthSystemContextService,
    load_system_context_payload,
    normalize_average_response_times_and_call_volumes,
    normalize_paramedic_service_response_time_plans_and_performance,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for Ontario EMS system-context seeding."""
    parser = argparse.ArgumentParser(
        description="Seed approved Ontario EMS system-context payloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m waittime.cli.seed_public_health_system_context \
    --average-response-times-file average_response_times.csv \
    --paramedic-performance-file paramedic_performance.csv
  python -m waittime.cli.seed_public_health_system_context --fetch-live
  python -m waittime.cli.seed_public_health_system_context --list
        """,
    )
    parser.add_argument(
        "--average-response-times-file",
        type=Path,
        help="Path to the English Average Response Times and Call Volumes CSV",
    )
    parser.add_argument(
        "--paramedic-performance-file",
        type=Path,
        help="Path to the English Paramedic Services Response Time Plans and Performance CSV",
    )
    parser.add_argument(
        "--fetch-live",
        action="store_true",
        help="Fetch the two approved Ontario EMS CSV resources directly",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing to DB")
    parser.add_argument("--list", action="store_true", help="List stored normalized EMS metrics")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    has_file_pair = bool(args.average_response_times_file and args.paramedic_performance_file)
    if not args.list and not args.fetch_live and not has_file_pair:
        print("Error: provide both CSV file flags, use --fetch-live, or use --list")
        return 1

    if (args.average_response_times_file and not args.paramedic_performance_file) or (
        args.paramedic_performance_file and not args.average_response_times_file
    ):
        print(
            "Error: --average-response-times-file and --paramedic-performance-file must be provided together"
        )
        return 1

    try:
        if args.list:
            db = DatabaseService()
            rows = db.list_public_health_system_metrics(
                source_id="ontario-land-ambulance-response-times"
            )
            if not rows:
                print("No normalized EMS system-context rows found.")
                return 0

            print("\nOntario EMS system-context rows:\n")
            for row in rows[:20]:
                print(f"  {row.id:<48} {row.geography_name}")
                print(f"    Series: {row.series_key}")
                print(f"    Reporting year: {row.reporting_year}")
                print(f"    Source: {row.provenance_url}")
                print()
            return 0

        service = PublicHealthSystemContextService()

        if args.fetch_live:
            average_csv = service.fetch_average_response_times_and_call_volumes_csv()
            paramedic_csv = (
                service.fetch_paramedic_service_response_time_plans_and_performance_csv()
            )

            if args.dry_run:
                average_rows = normalize_average_response_times_and_call_volumes(
                    average_csv,
                    refreshed_at=_now(),
                )
                paramedic_rows = normalize_paramedic_service_response_time_plans_and_performance(
                    paramedic_csv,
                    refreshed_at=_now(),
                )
                print(
                    "✓ Dry run complete - normalized "
                    f"{len(average_rows)} CACC rows and {len(paramedic_rows)} paramedic rows"
                )
                return 0

            db = DatabaseService()
            service = PublicHealthSystemContextService(db)
            service.ensure_system_context_sources()
            summary = service.ingest_ontario_land_ambulance_context(
                average_csv,
                paramedic_csv,
            )
            print(
                "✓ EMS system-context seeding complete - loaded "
                f"{summary.records_loaded} rows from live Ontario sources"
            )
            return 0

        average_csv = load_system_context_payload(args.average_response_times_file)
        paramedic_csv = load_system_context_payload(args.paramedic_performance_file)

        if args.dry_run:
            average_rows = normalize_average_response_times_and_call_volumes(
                average_csv,
                refreshed_at=_now(),
            )
            paramedic_rows = normalize_paramedic_service_response_time_plans_and_performance(
                paramedic_csv,
                refreshed_at=_now(),
            )
            print(
                "✓ Dry run complete - normalized "
                f"{len(average_rows)} CACC rows and {len(paramedic_rows)} paramedic rows"
            )
            return 0

        db = DatabaseService()
        service = PublicHealthSystemContextService(db)
        service.ensure_system_context_sources()
        summary = service.ingest_ontario_land_ambulance_context(
            average_csv,
            paramedic_csv,
        )
        print(f"✓ EMS system-context seeding complete - loaded {summary.records_loaded} rows")
        return 0
    except FileNotFoundError as exc:
        logger.error("File error: %s", exc)
        return 1
    except Exception as exc:
        logger.error("Unexpected error: %s", exc, exc_info=args.verbose)
        return 1


def _now() -> datetime:
    return datetime.now(UTC)


if __name__ == "__main__":
    sys.exit(main())
