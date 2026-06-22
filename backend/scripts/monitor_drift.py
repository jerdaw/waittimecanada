"""Data drift monitoring script for Wait Time Canada.

Checks all provincial sources for potential methodology changes by comparing
distributional statistics between consecutive time periods. Exits with code 1
if any change is detected (for use in CI/alerting pipelines).

Usage:
    python scripts/monitor_drift.py [--fail-on-change]

Options:
    --fail-on-change  Exit with code 1 if any drift is detected (default: 0)
"""

from __future__ import annotations

import argparse
import os
import sys

import structlog

from waittime.services.database import DatabaseService
from waittime.services.methodology_change import MethodologyChangeDetector

logger = structlog.get_logger(__name__)


def run_drift_check(fail_on_change: bool = False) -> int:
    """Run drift detection across all sources.

    Args:
        fail_on_change: If True, return exit code 1 when drift is detected.

    Returns:
        Exit code: 0 for success/no drift, 1 for drift detected (when
        fail_on_change=True) or on unrecoverable error.
    """
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL environment variable not set")
        return 1

    db = DatabaseService(database_url)
    detector = MethodologyChangeDetector(db)

    logger.info("Starting drift check across all sources")

    try:
        results = detector.check_all_sources()
    except Exception:
        logger.exception("Failed to run drift check")
        return 1

    if not results:
        logger.info("No sources found to check")
        return 0

    changes_detected: list[dict[str, object]] = []
    for result in results:
        source_id = result["source_id"]
        if result["change_detected"]:
            details = result["details"]
            logger.warning(
                "Methodology drift detected",
                source_id=source_id,
                shift_percent=details["shift_percent"],
                hospitals_analyzed=details["hospitals_analyzed"],
                explanation=details["explanation"],
            )
            changes_detected.append(result)
        else:
            logger.info("No drift detected", source_id=source_id)

    total = len(results)
    n_changes = len(changes_detected)

    if n_changes == 0:
        logger.info(
            "Drift check complete: all sources stable",
            sources_checked=total,
        )
        return 0

    logger.warning(
        "Drift check complete: changes detected",
        sources_checked=total,
        sources_with_drift=n_changes,
        source_ids=[r["source_id"] for r in changes_detected],
    )

    return 1 if fail_on_change else 0


def main() -> None:
    """Entry point for the drift monitor script."""
    parser = argparse.ArgumentParser(
        description="Check all provincial sources for potential methodology drift."
    )
    parser.add_argument(
        "--fail-on-change",
        action="store_true",
        default=False,
        help="Exit with code 1 if drift is detected (useful for CI pipelines).",
    )
    args = parser.parse_args()

    exit_code = run_drift_check(fail_on_change=args.fail_on_change)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
