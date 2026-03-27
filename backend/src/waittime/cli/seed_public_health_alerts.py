"""Seed public health alerts from approved Health Canada payloads.

Usage:
    python -m waittime.cli.seed_public_health_alerts --recalls-file recalls.json
    python -m waittime.cli.seed_public_health_alerts --fetch-live
    python -m waittime.cli.seed_public_health_alerts --list
"""

import argparse
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from waittime.services.database import DatabaseService
from waittime.services.public_health_alerts import (
    PublicHealthAlertService,
    load_alert_payload,
    normalize_health_canada_recall_feed,
    normalize_health_canada_recall_rss,
)

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entry point for public health alert seeding."""
    parser = argparse.ArgumentParser(
        description="Seed approved public health alert payloads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m waittime.cli.seed_public_health_alerts --recalls-file recalls.json
  python -m waittime.cli.seed_public_health_alerts --recalls-file recalls.json --dry-run
  python -m waittime.cli.seed_public_health_alerts --fetch-live
  python -m waittime.cli.seed_public_health_alerts --list
        """,
    )
    parser.add_argument(
        "--recalls-file",
        type=Path,
        help="Path to a Health Canada recalls/safety-alerts JSON payload",
    )
    parser.add_argument(
        "--fetch-live",
        action="store_true",
        help="Fetch the approved Health Canada recalls RSS feed directly",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing to DB")
    parser.add_argument("--list", action="store_true", help="List stored normalized alerts")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(message)s",
    )

    if not args.list and not args.recalls_file and not args.fetch_live:
        print("Error: provide --recalls-file, --fetch-live, or use --list")
        return 1

    try:
        db = DatabaseService()
        service = PublicHealthAlertService(db)

        if args.list:
            alerts = db.list_public_health_alerts(source_id="health-canada-recalls")
            if not alerts:
                print("No normalized recall alerts found.")
                return 0

            print("\nHealth Canada recall alerts:\n")
            for alert in alerts[:20]:
                print(f"  {alert.id:<24} {alert.title}")
                print(f"    Published: {alert.published_at.isoformat()}")
                print(f"    Source: {alert.provenance_url}")
                print()
            return 0

        service.ensure_alert_sources()

        if args.fetch_live:
            payload = service.fetch_health_canada_recall_rss()
            if args.dry_run:
                alerts = normalize_health_canada_recall_rss(payload, refreshed_at=_now())
                print(f"✓ Dry run complete - normalized {len(alerts)} alerts from live RSS")
                return 0

            summary = service.ingest_health_canada_recall_rss(payload)
            print(
                f"✓ Alert seeding complete - loaded {summary.records_loaded} alerts from live RSS"
            )
            return 0

        payload = load_alert_payload(args.recalls_file)
        if args.dry_run:
            alerts = normalize_health_canada_recall_feed(payload, refreshed_at=_now())
            print(f"✓ Dry run complete - normalized {len(alerts)} alerts")
            return 0

        summary = service.ingest_health_canada_recall_feed(payload)
        print(f"✓ Alert seeding complete - loaded {summary.records_loaded} alerts")
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
