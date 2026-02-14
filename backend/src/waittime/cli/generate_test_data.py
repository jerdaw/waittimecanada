"""Generate test measurement data for seeded hospitals.

This is a development/testing tool to populate the database with synthetic
measurements when real scraper data is not available yet.

Usage:
    python -m waittime.cli.generate_test_data --source ontario-health
    python -m waittime.cli.generate_test_data --source ontario-health --count 10
"""

import argparse
import hashlib
import logging
import secrets
import sys
from datetime import UTC, datetime

from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    PatientScope,
    StartEvent,
    StatisticType,
)
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


def generate_measurement_for_hospital(hospital_id: str, source_id: str) -> Measurement:
    """Generate a synthetic measurement for a hospital.

    Args:
        hospital_id: Hospital ID
        source_id: Source ID

    Returns:
        Synthetic Measurement object
    """
    # Generate realistic wait time values (in minutes)
    # P90 times typically range from 60-300 minutes
    value = 60 + secrets.randbelow(241)

    # Create synthetic payload
    payload = f"{{hospital_id: {hospital_id}, value: {value}, timestamp: {datetime.now(UTC)}}}"
    payload_hash = hashlib.sha256(payload.encode()).hexdigest()

    return Measurement(
        hospital_id=hospital_id,
        source_id=source_id,
        value=float(value),
        timestamp_utc=datetime.now(UTC),
        metric_family=MetricFamily.TIME_TO_PROVIDER,
        start_event=StartEvent.TRIAGE,
        end_event=EndEvent.PHYSICIAN,
        statistic_type=StatisticType.P90,
        patient_scope=PatientScope.ALL,
        raw_payload_hash=payload_hash,
        raw_payload_snippet=payload[:200],
        parser_version="test-v1.0",
    )


def generate_test_data(
    db: DatabaseService, source_id: str, count: int = 1, dry_run: bool = False
) -> int:
    """Generate test measurements for all hospitals in a source.

    Args:
        db: Database service instance
        source_id: Source ID to generate data for
        count: Number of measurements per hospital
        dry_run: If True, only simulate without inserting

    Returns:
        Number of measurements generated
    """
    # Get all hospitals for this source
    hospitals = db.get_hospitals_by_source(source_id)

    if not hospitals:
        logger.error(f"No hospitals found for source: {source_id}")
        return 0

    logger.info(f"Generating {count} measurement(s) for {len(hospitals)} hospital(s)...")

    total_generated = 0

    for hospital in hospitals:
        for _ in range(count):
            measurement = generate_measurement_for_hospital(hospital.id, source_id)

            if dry_run:
                logger.info(f"[DRY RUN] Would insert: {hospital.id} - {measurement.value:.0f} min")
            else:
                db.insert_measurement(measurement)
                logger.info(
                    f"✓ {hospital.name}: {measurement.value:.0f} min (P90 triage→physician)"
                )

            total_generated += 1

    return total_generated


def main() -> int:
    """Main entry point for test data generation."""
    parser = argparse.ArgumentParser(
        description="Generate test measurement data for seeded hospitals",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate 1 measurement per hospital
  python -m waittime.cli.generate_test_data --source ontario-health

  # Generate 5 measurements per hospital
  python -m waittime.cli.generate_test_data --source ontario-health --count 5

  # Dry run (don't insert)
  python -m waittime.cli.generate_test_data --source ontario-health --dry-run
        """,
    )

    parser.add_argument(
        "--source",
        required=True,
        help="Source ID to generate data for",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of measurements per hospital (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate without inserting data",
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

    try:
        db = DatabaseService()

        if args.dry_run:
            logger.info("[DRY RUN MODE - No changes will be made]\n")

        generated = generate_test_data(db, args.source, count=args.count, dry_run=args.dry_run)

        print(f"\n{'─' * 60}")
        print(f"✓ Generated {generated} test measurements")
        print(f"{'─' * 60}\n")

        if args.dry_run:
            print("Dry run complete - no changes made")

        return 0

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
