"""Report operational status for public-health-hub source ingest.

Usage:
    python -m waittime.cli.public_health_hub_status
    python -m waittime.cli.public_health_hub_status --format markdown
    python -m waittime.cli.public_health_hub_status --format json
"""

import argparse
import json
import sys
from datetime import UTC, datetime

from waittime.services.database import DatabaseService, PublicHealthSourceStatus


def main() -> int:
    """Render a public-health-hub operational summary."""
    parser = argparse.ArgumentParser(description="Show public health hub ingest status")
    parser.add_argument(
        "--format",
        choices=("text", "markdown", "json"),
        default="text",
        help="Output format for the summary",
    )
    args = parser.parse_args()

    db = DatabaseService()
    statuses = db.list_public_health_source_statuses()
    generated_at = datetime.now(UTC)

    if args.format == "json":
        print(_render_json(statuses, generated_at))
    elif args.format == "markdown":
        print(_render_markdown(statuses, generated_at))
    else:
        print(_render_text(statuses, generated_at))

    return 0


def _render_text(
    statuses: list[PublicHealthSourceStatus],
    generated_at: datetime,
) -> str:
    lines = ["Public Health Hub Status", f"Generated at: {generated_at.isoformat()}", ""]

    if not statuses:
        lines.append("No public health hub sources found.")
        return "\n".join(lines)

    for status in statuses:
        lines.extend(
            [
                f"{status.source_name} ({status.source_id})",
                f"  Domain: {status.domain}",
                f"  Last refreshed: {_format_datetime(status.last_refreshed_at)}",
                f"  Resource rows: {status.resource_record_count}",
                f"  Alert rows: {status.alert_record_count}",
                f"  Latest alert published: {_format_datetime(status.latest_alert_published_at)}",
                f"  Mode: {status.recommended_usage_mode}",
                "",
            ]
        )

    return "\n".join(lines).rstrip()


def _render_markdown(
    statuses: list[PublicHealthSourceStatus],
    generated_at: datetime,
) -> str:
    lines = [
        "## Public Health Hub Source Status",
        "",
        f"Generated at: `{generated_at.isoformat()}`",
        "",
    ]

    if not statuses:
        lines.append("_No public health hub sources found._")
        return "\n".join(lines)

    lines.extend(
        [
            "| Source | Domain | Last refreshed | Resource rows | Alert rows | Latest alert published | Mode |",
            "| --- | --- | --- | ---: | ---: | --- | --- |",
        ]
    )

    for status in statuses:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{status.source_id}`<br>{status.source_name}",
                    status.domain,
                    _format_datetime(status.last_refreshed_at),
                    str(status.resource_record_count),
                    str(status.alert_record_count),
                    _format_datetime(status.latest_alert_published_at),
                    status.recommended_usage_mode,
                ]
            )
            + " |"
        )

    return "\n".join(lines)


def _render_json(
    statuses: list[PublicHealthSourceStatus],
    generated_at: datetime,
) -> str:
    payload = {
        "generated_at": generated_at.isoformat(),
        "sources": [
            {
                "source_id": status.source_id,
                "source_name": status.source_name,
                "domain": status.domain,
                "recommended_usage_mode": status.recommended_usage_mode,
                "freshness_sensitivity": status.freshness_sensitivity,
                "last_refreshed_at": _format_datetime(status.last_refreshed_at),
                "resource_record_count": status.resource_record_count,
                "alert_record_count": status.alert_record_count,
                "latest_alert_published_at": _format_datetime(status.latest_alert_published_at),
            }
            for status in statuses
        ],
    }
    return json.dumps(payload, indent=2)


def _format_datetime(value: datetime | None) -> str:
    return value.isoformat() if value is not None else "never"


if __name__ == "__main__":
    sys.exit(main())
