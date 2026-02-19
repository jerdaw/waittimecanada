"""Check scraper heartbeat and alert if stale."""

import argparse
import os
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
        default=90,
        help="Max heartbeat age in minutes before alerting (default: 90)",
    )
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Check specific source (default: all sources)",
    )
    parser.add_argument(
        "--max-consecutive-failures",
        type=int,
        default=1,
        help="Alert when consecutive failures are at or above this threshold (default: 1)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed operational fields (last success/error and classification)",
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
    run_url = None
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if repo and run_id:
        run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    all_healthy = True

    with db.get_connection() as conn:
        with db.get_cursor(conn) as cur:
            for source_id in sources:
                # Query scraper_status table for this source
                cur.execute(
                    """
                    SELECT
                        last_run,
                        status,
                        error_message,
                        measurements_count,
                        last_success_run,
                        last_success_measurements_count,
                        last_error_run,
                        last_error_category,
                        last_error_stage,
                        consecutive_failures
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
                consecutive_failures = int(row.get("consecutive_failures") or 0)
                category = row.get("last_error_category") or "unknown"
                stage = row.get("last_error_stage") or "unknown"
                error_message = row.get("error_message") or "Unknown error"

                if (
                    row["status"] == "error"
                    and consecutive_failures >= args.max_consecutive_failures
                ):
                    print(
                        f"❌ {source_id}: error ({category}/{stage}), "
                        f"consecutive_failures={consecutive_failures}"
                    )
                    if args.verbose:
                        print(f"   last_error={row.get('last_error_run')} message={error_message}")
                        print(
                            f"   last_success={row.get('last_success_run')} "
                            f"count={row.get('last_success_measurements_count')}"
                        )

                    if not args.dry_run:
                        alerts.alert_scraper_error(
                            source_id,
                            error=error_message,
                            category=category,
                            stage=stage,
                            run_url=run_url,
                        )
                    all_healthy = False
                    continue

                if age_minutes > args.max_age:
                    print(
                        f"⚠️  {source_id}: Heartbeat is {age_minutes} minutes old "
                        f"(max: {args.max_age})"
                    )
                    if args.verbose:
                        print(
                            f"   status={row['status']} consecutive_failures={consecutive_failures} "
                            f"last_success={row.get('last_success_run')}"
                        )
                    if not args.dry_run:
                        alerts.alert_scraper_stale(source_id, age_minutes)
                    all_healthy = False
                else:
                    print(
                        f"✅ {source_id}: Heartbeat is {age_minutes} minutes old "
                        f"(status={row['status']}, measurements={row['measurements_count']})"
                    )
                    if args.verbose:
                        print(
                            f"   last_success={row.get('last_success_run')} "
                            f"count={row.get('last_success_measurements_count')}"
                        )
                        print(
                            f"   last_error={row.get('last_error_run')} "
                            f"classification={category}/{stage}"
                        )

    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
