"""Report operational status for public-health-hub source ingest.

Usage:
    python -m waittime.cli.public_health_hub_status
    python -m waittime.cli.public_health_hub_status --format markdown
    python -m waittime.cli.public_health_hub_status --format json
"""

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

from waittime.services.database import DatabaseService, PublicHealthSourceStatus

HOUR_SECONDS = 60 * 60
DAY_SECONDS = 24 * HOUR_SECONDS

STATUS_THRESHOLDS: dict[str, tuple[int, int]] = {
    "provider_facility": (548 * DAY_SECONDS, 913 * DAY_SECONDS),
    "aed": (30 * DAY_SECONDS, 90 * DAY_SECONDS),
    "safety_alert": (24 * HOUR_SECONDS, 48 * HOUR_SECONDS),
    "health_product_reference": (24 * HOUR_SECONDS, 48 * HOUR_SECONDS),
    "environmental_overlay": (6 * HOUR_SECONDS, 12 * HOUR_SECONDS),
    "system_context": (30 * DAY_SECONDS, 90 * DAY_SECONDS),
}
BEST_EFFORT_SOURCE_IDS = {"osm-aed"}


@dataclass(frozen=True)
class SourceOperationalAssessment:
    """Operator-facing health assessment for one public-health source."""

    status: PublicHealthSourceStatus
    state: str
    reasons: list[str]


def main() -> int:
    """Render a public-health-hub operational summary."""
    parser = argparse.ArgumentParser(description="Show public health hub ingest status")
    parser.add_argument(
        "--source",
        dest="source_ids",
        action="append",
        default=[],
        help="Limit status output to a specific source_id. Repeat for multiple sources.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Output format for the summary",
    )
    args = parser.parse_args()

    db = DatabaseService()
    statuses = db.list_public_health_source_statuses()
    if args.source_ids:
        requested_source_ids = set(args.source_ids)
        statuses = [status for status in statuses if status.source_id in requested_source_ids]
    generated_at = datetime.now(UTC)
    assessments = [assess_source_status(status, now=generated_at) for status in statuses]

    if args.format == "json":
        print(_render_json(assessments, generated_at))
    elif args.format == "markdown":
        print(_render_markdown(assessments, generated_at))
    else:
        print(_render_text(assessments, generated_at))

    return 0


def _render_text(
    assessments: list[SourceOperationalAssessment],
    generated_at: datetime,
) -> str:
    lines = [
        "Public Health Hub Status",
        f"Generated at: {generated_at.isoformat()}",
        f"Overall state: {_derive_overall_state(assessments).upper()}",
        "",
    ]

    if not assessments:
        lines.append("No public health hub sources found.")
        return "\n".join(lines)

    for assessment in assessments:
        status = assessment.status
        lines.extend(
            [
                f"{status.source_name} ({status.source_id})",
                f"  State: {assessment.state}",
                f"  Domain: {status.domain}",
                f"  Last refreshed: {_format_datetime(status.last_refreshed_at)}",
                f"  Resource rows: {status.resource_record_count}",
                f"  Alert rows: {status.alert_record_count}",
                f"  System metric rows: {status.system_metric_record_count}",
                f"  Latest alert published: {_format_datetime(status.latest_alert_published_at)}",
                f"  Mode: {status.recommended_usage_mode}",
                f"  Reasons: {_format_reasons(assessment.reasons)}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def _render_markdown(
    assessments: list[SourceOperationalAssessment],
    generated_at: datetime,
) -> str:
    lines = [
        "## Public Health Hub Source Status",
        "",
        f"Generated at: `{generated_at.isoformat()}`",
        f"Overall state: `{_derive_overall_state(assessments)}`",
        "",
    ]

    if not assessments:
        lines.append("_No public health hub sources found._")
        return "\n".join(lines)

    lines.extend(
        [
            "| Source | State | Domain | Last refreshed | Resource rows | Alert rows | System metric rows | Latest alert published | Reasons |",
            "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
        ]
    )

    for assessment in assessments:
        status = assessment.status
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{status.source_id}`<br>{status.source_name}",
                    _format_state_badge(assessment.state),
                    status.domain,
                    _format_datetime(status.last_refreshed_at),
                    str(status.resource_record_count),
                    str(status.alert_record_count),
                    str(status.system_metric_record_count),
                    _format_datetime(status.latest_alert_published_at),
                    _escape_markdown_cell(_format_reasons(assessment.reasons)),
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _render_json(
    assessments: list[SourceOperationalAssessment],
    generated_at: datetime,
) -> str:
    payload = {
        "generated_at": generated_at.isoformat(),
        "overall_state": _derive_overall_state(assessments),
        "sources": [
            {
                "state": assessment.state,
                "reasons": assessment.reasons,
                "source_id": assessment.status.source_id,
                "source_name": assessment.status.source_name,
                "domain": assessment.status.domain,
                "recommended_usage_mode": assessment.status.recommended_usage_mode,
                "freshness_sensitivity": assessment.status.freshness_sensitivity,
                "last_refreshed_at": _format_datetime(assessment.status.last_refreshed_at),
                "resource_record_count": assessment.status.resource_record_count,
                "alert_record_count": assessment.status.alert_record_count,
                "system_metric_record_count": assessment.status.system_metric_record_count,
                "latest_alert_published_at": _format_datetime(
                    assessment.status.latest_alert_published_at
                ),
            }
            for assessment in assessments
        ],
    }
    return json.dumps(payload, indent=2)


def assess_source_status(
    status: PublicHealthSourceStatus,
    *,
    now: datetime,
) -> SourceOperationalAssessment:
    """Classify one source as healthy, partial, or degraded for operators."""
    severity = 0
    reasons: list[str] = []
    is_best_effort = status.source_id in BEST_EFFORT_SOURCE_IDS

    if status.last_refreshed_at is None:
        severity = max(severity, 1 if is_best_effort else 2)
        reasons.append("No successful refresh recorded yet")
    else:
        age_seconds = max(0, int((now - status.last_refreshed_at).total_seconds()))
        warn_seconds, suppress_seconds = STATUS_THRESHOLDS.get(
            status.domain,
            (24 * HOUR_SECONDS, 48 * HOUR_SECONDS),
        )

        if age_seconds > suppress_seconds:
            severity = max(severity, 2)
            reasons.append(
                f"Refresh age exceeds suppress threshold ({_format_duration(age_seconds)})"
            )
        elif age_seconds > warn_seconds:
            severity = max(severity, 1)
            reasons.append(f"Refresh age exceeds warn threshold ({_format_duration(age_seconds)})")

    if status.domain in {"provider_facility", "aed"} and status.resource_record_count == 0:
        severity = max(severity, 1 if is_best_effort else 2)
        reasons.append("No normalized resource rows available")

    if status.domain == "safety_alert" and status.alert_record_count == 0:
        severity = max(severity, 2)
        reasons.append("No normalized alert rows available")

    if status.domain == "system_context" and status.system_metric_record_count == 0:
        severity = max(severity, 2)
        reasons.append("No normalized system metric rows available")

    if not reasons:
        reasons.append("Freshness and normalized row checks passed")

    return SourceOperationalAssessment(
        status=status,
        state={0: "healthy", 1: "partial", 2: "degraded"}[severity],
        reasons=reasons,
    )


def _format_datetime(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "never"


def _derive_overall_state(assessments: list[SourceOperationalAssessment]) -> str:
    if any(assessment.state == "degraded" for assessment in assessments):
        return "degraded"
    if any(assessment.state == "partial" for assessment in assessments):
        return "partial"
    return "healthy"


def _format_reasons(reasons: list[str]) -> str:
    return "; ".join(reasons)


def _escape_markdown_cell(value: str) -> str:
    return value.replace("|", "\\|")


def _format_state_badge(state: str) -> str:
    return {
        "healthy": "✅ healthy",
        "partial": "⚠️ partial",
        "degraded": "❌ degraded",
    }[state]


def _format_duration(total_seconds: int) -> str:
    days, remainder = divmod(total_seconds, DAY_SECONDS)
    hours = remainder // HOUR_SECONDS
    if days and hours:
        return f"{days}d {hours}h"
    if days:
        return f"{days}d"
    return f"{hours}h"


if __name__ == "__main__":
    sys.exit(main())
