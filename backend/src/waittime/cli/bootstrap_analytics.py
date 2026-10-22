"""Bootstrap analytics prerequisites in one command.

This command applies migrations, seeds region mappings, and backfills
daily/weekly/monthly aggregates needed by analytics endpoints.

Usage:
    python -m waittime.cli.bootstrap_analytics
    python -m waittime.cli.bootstrap_analytics --days 365
    python -m waittime.cli.bootstrap_analytics --skip-migrations
"""

import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

from waittime.cli.seed_regions import load_regions_from_json, seed_regions
from waittime.services.aggregation import AggregationService
from waittime.services.database import DatabaseService
from waittime.services.migration_runner import run_migrations as run_canonical_migrations

logger = logging.getLogger(__name__)


BACKEND_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = BACKEND_ROOT / "migrations"
DEFAULT_REGIONS_FILE = BACKEND_ROOT / "data" / "regions" / "ontario-regions.json"


def _migration_files(migrations_dir: Path = MIGRATIONS_DIR) -> list[Path]:
    """Return migration SQL files sorted lexicographically."""
    return sorted(migrations_dir.glob("*.sql"))


def apply_migrations(db: DatabaseService, dry_run: bool = False) -> int:
    """Apply all SQL migrations in backend/migrations."""
    files = _migration_files()
    if not files:
        raise FileNotFoundError(f"No migration files found in {MIGRATIONS_DIR}")

    if dry_run:
        for file_path in files:
            logger.info("[DRY RUN] Would apply migration: %s", file_path.name)
        return len(files)

    results = run_canonical_migrations(db, files)
    for result in results:
        if result.status == "applied":
            logger.info("Applied migration: %s", result.filename)
        elif result.status == "skipped":
            logger.info("Skipped migration (already applied): %s", result.filename)
        else:
            logger.info(
                "Adopted legacy migration (already applied): %s: %s",
                result.filename,
                result.detail,
            )

    return len(results)


def seed_region_mappings(
    db: DatabaseService,
    region_file: Path = DEFAULT_REGIONS_FILE,
    province: str = "ON",
    dry_run: bool = False,
) -> tuple[int, int, int]:
    """Seed regions and hospital mappings from JSON."""
    payload = load_regions_from_json(region_file, province_override=province.upper())
    return seed_regions(
        db=db,
        province=str(payload["province"]).upper(),
        regions=payload["regions"],
        dry_run=dry_run,
    )


def backfill_analytics_aggregates(
    db: DatabaseService,
    days: int = 180,
    period_types: Sequence[str] = ("daily", "weekly", "monthly"),
    dry_run: bool = False,
) -> dict[str, int]:
    """Backfill aggregate rows needed by analytics endpoints."""
    service = AggregationService(db)
    now = datetime.now(UTC)
    start = now - timedelta(days=days)
    return service.backfill(
        start_date=start,
        end_date=now,
        period_types=list(period_types),
        dry_run=dry_run,
    )


def main() -> int:
    """Run analytics bootstrap workflow."""
    parser = argparse.ArgumentParser(
        description="Bootstrap analytics schema, seed data, and aggregates"
    )
    parser.add_argument(
        "--regions-file",
        type=Path,
        default=DEFAULT_REGIONS_FILE,
        help=f"Path to region seed JSON (default: {DEFAULT_REGIONS_FILE})",
    )
    parser.add_argument(
        "--province",
        default="ON",
        help="Province code for seeding region mappings (default: ON)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        help="Backfill window in days for aggregates (default: 180)",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip migration application",
    )
    parser.add_argument(
        "--skip-regions",
        action="store_true",
        help="Skip region seed step",
    )
    parser.add_argument(
        "--skip-aggregates",
        action="store_true",
        help="Skip aggregate backfill step",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would run without writing changes",
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

    if args.days <= 0:
        logger.error("--days must be greater than 0")
        return 1

    try:
        db = DatabaseService()

        print("\nAnalytics bootstrap starting...\n")

        migration_count = 0
        if args.skip_migrations:
            logger.info("Skipping migrations")
        else:
            migration_count = apply_migrations(db, dry_run=args.dry_run)

        regions_upserted = 0
        mappings_upserted = 0
        missing_hospitals = 0
        if args.skip_regions:
            logger.info("Skipping region seed")
        else:
            regions_upserted, mappings_upserted, missing_hospitals = seed_region_mappings(
                db=db,
                region_file=args.regions_file,
                province=args.province,
                dry_run=args.dry_run,
            )

        aggregate_counts: dict[str, int] = {}
        if args.skip_aggregates:
            logger.info("Skipping aggregate backfill")
        else:
            aggregate_counts = backfill_analytics_aggregates(
                db=db,
                days=args.days,
                dry_run=args.dry_run,
            )

        print("\n" + ("-" * 64))
        print("Analytics bootstrap summary")
        print(f"  Migrations processed: {migration_count}")
        print(f"  Regions upserted:     {regions_upserted}")
        print(f"  Mappings upserted:    {mappings_upserted}")
        print(f"  Missing hospitals:    {missing_hospitals}")
        if aggregate_counts:
            print("  Aggregates:")
            for period in ("daily", "weekly", "monthly"):
                print(f"    {period:<8} {aggregate_counts.get(period, 0)}")
        print("-" * 64)
        if args.dry_run:
            print("Dry run complete. No database changes were written.")
        else:
            print("Analytics bootstrap complete.")
        print()
        return 0

    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        logger.error("Analytics bootstrap failed: %s", exc, exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
