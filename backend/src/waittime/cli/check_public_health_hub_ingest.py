"""Check public-health-hub ingest state and send transition-aware alerts."""

import argparse
import hashlib
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

from waittime.cli.public_health_hub_status import SourceOperationalAssessment, assess_source_status
from waittime.core import PublicHealthSourceAlertState
from waittime.services.alerts import AlertService
from waittime.services.database import DatabaseService

DEFAULT_HARD_FAIL_SOURCE_IDS = ("health-canada-recalls", "mohserlo")


def _get_sources_to_check(source_ids: list[str]) -> list[str]:
    """Resolve which public-health sources should participate in alerting."""
    return sorted(source_ids) if source_ids else sorted(DEFAULT_HARD_FAIL_SOURCE_IDS)


@dataclass(frozen=True)
class CurrentIncident:
    """The current incident detected for one public-health source."""

    kind: str
    fingerprint: str
    reasons: list[str]


@dataclass(frozen=True)
class IngestEvaluation:
    """Operational evaluation for one public-health source."""

    ok: bool
    summary: str
    details: list[str]
    incident: CurrentIncident | None = None


def _normalize_reasons(reasons: list[str]) -> str:
    return " | ".join(" ".join(reason.split()).strip().lower() for reason in reasons)


def _build_degraded_fingerprint(source_id: str, reasons: list[str]) -> str:
    """Build a stable fingerprint for materially identical degraded incidents."""
    digest = hashlib.sha256(_normalize_reasons(reasons).encode("utf-8")).hexdigest()
    return f"degraded:{source_id}:{digest[:16]}"


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


def evaluate_source_status(assessment: SourceOperationalAssessment) -> IngestEvaluation:
    """Classify the current ingest state for one hard-fail public-health source."""
    if assessment.state == "degraded":
        return IngestEvaluation(
            ok=False,
            summary=(
                f"❌ {assessment.status.source_id}: degraded ({'; '.join(assessment.reasons)})"
            ),
            details=[
                (
                    f"last_refreshed={assessment.status.last_refreshed_at} "
                    f"resources={assessment.status.resource_record_count} "
                    f"alerts={assessment.status.alert_record_count}"
                )
            ],
            incident=CurrentIncident(
                kind="degraded",
                fingerprint=_build_degraded_fingerprint(
                    assessment.status.source_id,
                    assessment.reasons,
                ),
                reasons=assessment.reasons,
            ),
        )

    icon = "⚠️" if assessment.state == "partial" else "✅"
    return IngestEvaluation(
        ok=True,
        summary=f"{icon} {assessment.status.source_id}: {assessment.state}",
        details=[f"reasons={'; '.join(assessment.reasons)}"],
    )


def reconcile_incident_state(
    source_id: str,
    source_name: str,
    evaluation: IngestEvaluation,
    alert_state: PublicHealthSourceAlertState | None,
    *,
    alerts: AlertService,
    db: DatabaseService,
    run_url: str | None,
    dry_run: bool,
    now: datetime | None = None,
) -> None:
    """Send transition-aware alerts and persist incident state."""
    now = now or datetime.now(UTC)
    active_kind = alert_state.active_incident_kind if alert_state else None
    active_fingerprint = alert_state.active_incident_fingerprint if alert_state else None
    opened_at = alert_state.opened_at if alert_state else None
    current = evaluation.incident

    if current is None:
        if active_kind and not dry_run:
            alerts.alert_public_health_source_resolved(
                source_id,
                source_name=source_name,
                duration=_format_incident_duration(opened_at, now),
                run_url=run_url,
            )
            db.resolve_public_health_source_alert_incident(source_id)
        return

    if active_kind == current.kind and active_fingerprint == current.fingerprint:
        return

    if active_kind and not dry_run:
        alerts.alert_public_health_source_resolved(
            source_id,
            source_name=source_name,
            duration=_format_incident_duration(opened_at, now),
            run_url=run_url,
        )

    if dry_run:
        return

    alerts.alert_public_health_source_degraded(
        source_id,
        source_name=source_name,
        reasons=current.reasons,
        run_url=run_url,
    )
    db.open_public_health_source_alert_incident(
        source_id,
        current.kind,
        current.fingerprint,
    )


def main() -> None:
    """Check public-health ingest state and send alerts on incident transitions."""
    parser = argparse.ArgumentParser(
        description="Check public health hub ingest state and send transition-aware alerts"
    )
    parser.add_argument(
        "--source",
        dest="source_ids",
        action="append",
        default=[],
        help="Check specific source_id (default: hard-fail live ingest sources)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed operational fields",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print status without sending alerts",
    )
    args = parser.parse_args()

    db = DatabaseService()
    alerts = AlertService()
    sources_to_check = _get_sources_to_check(args.source_ids)
    statuses = {
        status.source_id: status
        for status in db.list_public_health_source_statuses()
        if status.source_id in sources_to_check
    }

    run_url = None
    repo = os.environ.get("GITHUB_REPOSITORY")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if repo and run_id:
        run_url = f"https://github.com/{repo}/actions/runs/{run_id}"

    now = datetime.now(UTC)

    for source_id in sources_to_check:
        status = statuses.get(source_id)
        if status is None:
            evaluation = IngestEvaluation(
                ok=False,
                summary=f"❌ {source_id}: no public health source metadata found",
                details=[],
                incident=CurrentIncident(
                    kind="degraded",
                    fingerprint=_build_degraded_fingerprint(
                        source_id,
                        ["No public health source metadata found"],
                    ),
                    reasons=["No public health source metadata found"],
                ),
            )
            source_name = source_id
        else:
            assessment = assess_source_status(status, now=now)
            evaluation = evaluate_source_status(assessment)
            source_name = status.source_name

        print(evaluation.summary)
        if args.verbose:
            for detail in evaluation.details:
                print(f"   {detail}")

        alert_state = db.get_public_health_source_alert_state(source_id)
        reconcile_incident_state(
            source_id,
            source_name,
            evaluation,
            alert_state,
            alerts=alerts,
            db=db,
            run_url=run_url,
            dry_run=args.dry_run,
            now=now,
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
