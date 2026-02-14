"""Check scraper heartbeat and alert if stale."""

import argparse
import sys
from datetime import UTC, datetime

from waittime.cli.scraper import SCRAPERS
from waittime.services.alerts import AlertService
from waittime.services.database import DatabaseService


def _get_sources_to_check(source: str | None) -> list[str]:
    """Resolve source IDs to monitor.

    Defaults to operational scrapers (registry), not every seeded source.
    """
    if source:
        return [source]
    return sorted(SCRAPERS.keys())


def main() -> None:
    """Check scraper heartbeat and send alerts if stale."""
    parser = argparse.ArgumentParser(description="Check scraper heartbeat and alert if stale")
    parser.add_argument(
        "--max-age",
        type=int,
        default=60,
        help="Max heartbeat age in minutes before alerting (default: 60)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Check specific source (default: all sources)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print status without sending alerts",
    )
    args = parser.parse_args()

    db = DatabaseService()
    alerts = AlertService()

    # Check operational scrapers by default to avoid alerting on dormant seeded sources.
    sources = _get_sources_to_check(args.source)

    all_healthy = True

    with db.get_connection() as conn:
        with db.get_cursor(conn) as cur:
            for source_id in sources:
                # Query scraper_status table for this source
                cur.execute(
                    """
                    SELECT last_run, status, error_message
                    FROM scraper_status
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )
                row = cur.fetchone()

                if not row or not row["last_run"]:
                    print(f"❌ {source_id}: No heartbeat found")
                    if not args.dry_run:
                        alerts.alert_scraper_stale(source_id, age_minutes=9999)
                    all_healthy = False
                    continue

                last_run = row["last_run"]
                if last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=UTC)

                age = datetime.now(UTC) - last_run
                age_minutes = int(age.total_seconds() / 60)

                if age_minutes > args.max_age:
                    print(
                        f"⚠️  {source_id}: Heartbeat is {age_minutes} minutes old "
                        f"(max: {args.max_age})"
                    )
                    if not args.dry_run:
                        alerts.alert_scraper_stale(source_id, age_minutes)
                    all_healthy = False
                else:
                    print(f"✅ {source_id}: Heartbeat is {age_minutes} minutes old")

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
