"""Check scraper heartbeat and alert if stale."""

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict, cast

from waittime.cli.scraper import SCRAPERS
from waittime.services.alerts import AlertService, NotificationPolicy
from waittime.services.database import DatabaseService

CRITICAL_NOTIFICATION_TIERS = {"P0", "P1"}


def _write_recovery_required_output(
    recovery_required: bool,
    output_path: str | None = None,
) -> None:
    """Expose whether this check opened a new incident to GitHub Actions."""
    resolved_output_path = output_path or os.environ.get("GITHUB_OUTPUT")
    if not resolved_output_path:
        return

    with Path(resolved_output_path).open("a", encoding="utf-8") as output:
        output.write(f"recovery_required={'true' if recovery_required else 'false'}\n")


def _get_sources_to_check(source: str | None) -> list[str]:
    """Resolve source IDs to monitor.

    Defaults to operational scrapers (registry), not every seeded source.
    """
    if source:
        return [source]
    return sorted(SCRAPERS.keys())


@dataclass(frozen=True)
class CurrentIncident:
    """The incident detected for the current heartbeat observation."""

    kind: str
    fingerprint: str
    age_minutes: int | None = None
    error_message: str | None = None
    category: str | None = None
    stage: str | None = None


@dataclass(frozen=True)
class HeartbeatEvaluation:
    """Evaluation result for a single source heartbeat."""

    ok: bool
    summary: str
    details: list[str]
    incident: CurrentIncident | None = None


class ScraperStatusRow(TypedDict, total=False):
    """Subset of scraper_status fields needed by the heartbeat checker."""

    last_run: datetime | None
    status: str
    error_message: str | None
    measurements_count: int
    last_success_run: datetime | None
    last_success_measurements_count: int | None
    last_error_run: datetime | None
    last_error_category: str | None
    last_error_stage: str | None
    consecutive_failures: int | None


class AlertStateRow(TypedDict, total=False):
    """Subset of scraper_alert_state fields needed by the heartbeat checker."""

    active_incident_kind: str | None
    active_incident_fingerprint: str | None
    opened_at: datetime | None
    last_notified_at: datetime | None
    active_incident_notified_tier: str | None
    active_incident_notified_at: datetime | None
    last_resolved_at: datetime | None


def _normalize_error_message(error: str) -> str:
    """Normalize noisy error text so equivalent failures share a fingerprint."""
    return " ".join(error.split()).strip().lower()


def _build_error_fingerprint(
    source_id: str,
    category: str,
    stage: str,
    error_message: str,
) -> str:
    """Build a stable fingerprint for materially identical scraper failures."""
    digest = hashlib.sha256(_normalize_error_message(error_message).encode("utf-8")).hexdigest()
    return f"error:{source_id}:{category}:{stage}:{digest[:16]}"


def _format_incident_duration(opened_at: datetime | None, now: datetime) -> str | None:
    """Format a compact incident duration for resolved alerts."""
    if opened_at is None:
        return None
    if opened_at.tzinfo is None:
        opened_at = opened_at.replace(tzinfo=UTC)
    total_seconds = max(0, int((now - opened_at).total_seconds()))
    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _critical_only_enabled(alerts: AlertService) -> bool:
    return getattr(alerts.config, "operational_notification_mode", "normal") == "critical_only"


def _should_send_recovery(alert_state: AlertStateRow | None, alerts: AlertService) -> bool:
    if not _critical_only_enabled(alerts):
        return True
    notified_tier = alert_state.get("active_incident_notified_tier") if alert_state else None
    return notified_tier in CRITICAL_NOTIFICATION_TIERS


def evaluate_source_status(
    source_id: str,
    row: ScraperStatusRow | None,
    *,
    max_age: int,
    max_consecutive_failures: int,
    now: datetime | None = None,
) -> HeartbeatEvaluation:
    """Classify the current heartbeat state for one source."""
    now = now or datetime.now(UTC)

    if not row or not row.get("last_run"):
        return HeartbeatEvaluation(
            ok=False,
            summary=f"❌ {source_id}: No heartbeat found",
            details=[],
            incident=CurrentIncident(
                kind="stale",
                fingerprint=f"stale:{source_id}",
                age_minutes=9999,
            ),
        )

    last_run = row["last_run"]
    if last_run is None:
        return HeartbeatEvaluation(
            ok=False,
            summary=f"❌ {source_id}: No heartbeat found",
            details=[],
            incident=CurrentIncident(
                kind="stale",
                fingerprint=f"stale:{source_id}",
                age_minutes=9999,
            ),
        )
    if last_run.tzinfo is None:
        last_run = last_run.replace(tzinfo=UTC)

    age_minutes = int((now - last_run).total_seconds() / 60)
    consecutive_failures = int(row.get("consecutive_failures") or 0)
    category = row.get("last_error_category") or "unknown"
    stage = row.get("last_error_stage") or "unknown"
    error_message = row.get("error_message") or "Unknown error"

    if row["status"] == "error" and consecutive_failures >= max_consecutive_failures:
        return HeartbeatEvaluation(
            ok=False,
            summary=(
                f"❌ {source_id}: error ({category}/{stage}), "
                f"consecutive_failures={consecutive_failures}"
            ),
            details=[
                f"last_error={row.get('last_error_run')} message={error_message}",
                (
                    f"last_success={row.get('last_success_run')} "
                    f"count={row.get('last_success_measurements_count')}"
                ),
            ],
            incident=CurrentIncident(
                kind="error",
                fingerprint=_build_error_fingerprint(source_id, category, stage, error_message),
                error_message=error_message,
                category=category,
                stage=stage,
            ),
        )

    if age_minutes > max_age:
        return HeartbeatEvaluation(
            ok=False,
            summary=f"⚠️  {source_id}: Heartbeat is {age_minutes} minutes old (max: {max_age})",
            details=[
                (
                    f"status={row['status']} consecutive_failures={consecutive_failures} "
                    f"last_success={row.get('last_success_run')}"
                )
            ],
            incident=CurrentIncident(
                kind="stale",
                fingerprint=f"stale:{source_id}",
                age_minutes=age_minutes,
            ),
        )

    return HeartbeatEvaluation(
        ok=True,
        summary=(
            f"✅ {source_id}: Heartbeat is {age_minutes} minutes old "
            f"(status={row['status']}, measurements={row['measurements_count']})"
        ),
        details=[
            (
                f"last_success={row.get('last_success_run')} "
                f"count={row.get('last_success_measurements_count')}"
            ),
            (f"last_error={row.get('last_error_run')} classification={category}/{stage}"),
        ],
    )


def reconcile_incident_state(
    source_id: str,
    evaluation: HeartbeatEvaluation,
    alert_state: AlertStateRow | None,
    *,
    alerts: AlertService,
    db: DatabaseService,
    run_url: str | None,
    dry_run: bool,
    now: datetime | None = None,
) -> bool:
    """Persist incident state and report whether one bounded recovery is eligible."""
    now = now or datetime.now(UTC)
    active_kind = alert_state.get("active_incident_kind") if alert_state else None
    active_fingerprint = alert_state.get("active_incident_fingerprint") if alert_state else None
    opened_at = alert_state.get("opened_at") if alert_state else None
    current = evaluation.incident

    if current is None:
        if active_kind and not dry_run:
            if _should_send_recovery(alert_state, alerts):
                alerts.alert_scraper_resolved(
                    source_id,
                    incident_kind=active_kind,
                    duration=_format_incident_duration(opened_at, now),
                    run_url=run_url,
                )
            db.resolve_scraper_alert_incident(source_id)
        return False

    if active_kind == current.kind and active_fingerprint == current.fingerprint:
        return False

    if active_kind and not dry_run:
        if _should_send_recovery(alert_state, alerts):
            alerts.alert_scraper_resolved(
                source_id,
                incident_kind=active_kind,
                duration=_format_incident_duration(opened_at, now),
                run_url=run_url,
            )

    if dry_run:
        return False

    policy = NotificationPolicy(
        tier="P2",
        incident_key=f"scraper:{source_id}:{current.kind}:{current.fingerprint}",
    )
    notified_tier = None

    if current.kind == "stale":
        if alerts.should_send_operational_notification(policy):
            if alerts.alert_scraper_stale(source_id, age_minutes=current.age_minutes or 9999):
                notified_tier = policy.tier
    else:
        if alerts.should_send_operational_notification(policy):
            if alerts.alert_scraper_error(
                source_id,
                error=current.error_message or "Unknown error",
                category=current.category,
                stage=current.stage,
                run_url=run_url,
            ):
                notified_tier = policy.tier

    db.open_scraper_alert_incident(source_id, current.kind, current.fingerprint, notified_tier)
    return True


def main() -> None:
    """Check scraper heartbeat and send alerts if stale."""
    parser = argparse.ArgumentParser(description="Check scraper heartbeat and alert if stale")
    parser.add_argument(
        "--max-age",
        type=int,
        default=720,
        help="Max heartbeat age in minutes before alerting (default: 720)",
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
        default=6,
        help="Alert when consecutive failures are at or above this threshold (default: 6)",
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
    recovery_required = False
    now = datetime.now(UTC)

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
                cur.execute(
                    """
                    SELECT
                        active_incident_kind,
                        active_incident_fingerprint,
                        opened_at,
                        last_notified_at,
                        active_incident_notified_tier,
                        active_incident_notified_at,
                        last_resolved_at
                    FROM scraper_alert_state
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )
                alert_state = cur.fetchone()

                evaluation = evaluate_source_status(
                    source_id,
                    cast(ScraperStatusRow | None, row),
                    max_age=args.max_age,
                    max_consecutive_failures=args.max_consecutive_failures,
                    now=now,
                )

                print(evaluation.summary)
                if args.verbose:
                    for detail in evaluation.details:
                        print(f"   {detail}")

                incident_requires_recovery = reconcile_incident_state(
                    source_id,
                    evaluation,
                    cast(AlertStateRow | None, alert_state),
                    alerts=alerts,
                    db=db,
                    run_url=run_url,
                    dry_run=args.dry_run,
                    now=now,
                )
                recovery_required = recovery_required or incident_requires_recovery
                all_healthy = all_healthy and evaluation.ok

    _write_recovery_required_output(recovery_required)
    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
