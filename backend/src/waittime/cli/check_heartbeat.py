"""Check scraper heartbeat and alert if stale."""
import argparse
import sys
from datetime import datetime, timezone

from waittime.services.database import DatabaseService
from waittime.services.alerts import AlertService


def main():
    """Check scraper heartbeat and send alerts if stale."""
    parser = argparse.ArgumentParser(
        description="Check scraper heartbeat and alert if stale"
    )
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

    # Get latest heartbeats
    if args.source:
        sources = [args.source]
    else:
        # Check all known sources
        sources = ["ontario-health", "quebec-msss"]

    all_healthy = True
    for source_id in sources:
        heartbeat = db.get_latest_heartbeat(source_id)

        if not heartbeat:
            print(f"❌ {source_id}: No heartbeat found")
            if not args.dry_run:
                alerts.alert_scraper_stale(source_id, age_minutes=9999)
            all_healthy = False
            continue

        age = datetime.now(timezone.utc) - heartbeat.timestamp
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
