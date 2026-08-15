#!/usr/bin/env python3
"""Validate production scraper freshness workflow guardrails."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRAPER_WORKFLOW = ROOT / ".github" / "workflows" / "scraper-cron.yml"
HEARTBEAT_WORKFLOW = ROOT / ".github" / "workflows" / "heartbeat-monitor.yml"
LIVE_SOURCE_CONFIG = ROOT / "frontend" / "utils" / "live-scraper-sources.ts"
EN_MESSAGES = ROOT / "frontend" / "messages" / "en.json"
FR_MESSAGES = ROOT / "frontend" / "messages" / "fr.json"

EXPECTED_SCRAPER_CRON = "29 * * * *"
EXPECTED_HEARTBEAT_CRON = "14,44 * * * *"


def _step_block(text: str, step_name: str) -> str:
    marker = f"      - name: {step_name}"
    start = text.find(marker)
    if start == -1:
        raise AssertionError(f"Missing workflow step: {step_name}")

    next_step = text.find("\n      - name: ", start + len(marker))
    return text[start:] if next_step == -1 else text[start:next_step]


def _job_timeout_minutes(text: str) -> int:
    match = re.search(r"^\s{4}timeout-minutes:\s*(\d+)\s*$", text, re.MULTILINE)
    if not match:
        raise AssertionError("run-scrapers job must define timeout-minutes")
    return int(match.group(1))


def _has_permission(text: str, permission: str, level: str) -> bool:
    return bool(
        re.search(
            rf"^permissions:\n(?:\s{{2}}\w[\w-]*:\s*\w+\n)*\s{{2}}{permission}:\s*{level}\s*$",
            text,
            re.MULTILINE,
        )
    )


def _schedule_crons(text: str) -> list[str]:
    return re.findall(r"""^\s+- cron:\s*["']([^"']+)["']\s*$""", text, re.MULTILINE)


def _main() -> int:
    text = SCRAPER_WORKFLOW.read_text(encoding="utf-8")
    heartbeat_text = HEARTBEAT_WORKFLOW.read_text(encoding="utf-8")
    live_source_text = LIVE_SOURCE_CONFIG.read_text(encoding="utf-8")
    en_messages = EN_MESSAGES.read_text(encoding="utf-8")
    fr_messages = FR_MESSAGES.read_text(encoding="utf-8")

    failures: list[str] = []

    if _schedule_crons(text) != [EXPECTED_SCRAPER_CRON]:
        failures.append(
            f"scraper schedule must be exactly hourly at minute 29: {EXPECTED_SCRAPER_CRON}"
        )
    if _schedule_crons(heartbeat_text) != [EXPECTED_HEARTBEAT_CRON]:
        failures.append(
            "heartbeat schedule must be exactly twice hourly at minutes 14 and 44"
        )
    if 'LIVE_SCRAPER_CADENCE_LABEL = "hourly"' not in live_source_text:
        failures.append("frontend live scraper cadence label must remain hourly")
    if "HEARTBEAT_STALE_THRESHOLD_MINUTES = 120" not in live_source_text:
        failures.append("frontend heartbeat stale threshold must remain 120 minutes")
    if '"cadence": "Sources Checked Hourly"' not in en_messages:
        failures.append("English hero cadence must say Sources Checked Hourly")
    if '"cadence": "Sources vérifiées chaque heure"' not in fr_messages:
        failures.append("French hero cadence must describe hourly source checks")
    if (
        "Fresh Data Every 4 Hours" in en_messages
        or "Données fraîches toutes les 4h" in fr_messages
    ):
        failures.append("locale files must not claim fresh data every four hours")

    if _job_timeout_minutes(text) < 35:
        failures.append("run-scrapers timeout-minutes must be at least 35")

    if "refresh_analytics:" not in text:
        failures.append("workflow_dispatch must expose a refresh_analytics input")

    required_steps = [
        "Run scrapers",
        "Summarize scraper operational status",
        "Generate Freshness Badge",
        "Upload Badge Artifact",
        "Refresh current analytics aggregates",
    ]
    try:
        positions = {
            step: text.index(f"      - name: {step}") for step in required_steps
        }
    except ValueError as exc:
        failures.append(str(exc))
        positions = {}

    if positions:
        if not (
            positions["Run scrapers"]
            < positions["Summarize scraper operational status"]
            < positions["Generate Freshness Badge"]
            < positions["Upload Badge Artifact"]
            < positions["Refresh current analytics aggregates"]
        ):
            failures.append(
                "freshness summary and badge upload must run before aggregate refresh"
            )

    try:
        aggregate_step = _step_block(text, "Refresh current analytics aggregates")
    except AssertionError as exc:
        failures.append(str(exc))
        aggregate_step = ""

    if aggregate_step:
        if "timeout-minutes:" not in aggregate_step:
            failures.append("aggregate refresh step must have its own timeout-minutes")
        if "refresh_analytics" not in aggregate_step:
            failures.append("aggregate refresh step must honor refresh_analytics input")
        if "--period daily" not in aggregate_step:
            failures.append(
                "scheduled post-scrape aggregate refresh must be limited to daily"
            )

    if not _has_permission(heartbeat_text, "contents", "read"):
        failures.append("heartbeat workflow must grant contents: read")
    if not _has_permission(heartbeat_text, "actions", "write"):
        failures.append(
            "heartbeat workflow must grant actions: write for recovery dispatch"
        )

    try:
        check_step = _step_block(heartbeat_text, "Check heartbeats")
    except AssertionError as exc:
        failures.append(str(exc))
        check_step = ""

    if check_step and "id: check_heartbeats" not in check_step:
        failures.append("heartbeat check step must expose id: check_heartbeats")

    try:
        recovery_step = _step_block(
            heartbeat_text, "Dispatch freshness-only scraper recovery"
        )
    except AssertionError as exc:
        failures.append(str(exc))
        recovery_step = ""

    if recovery_step:
        if "steps.check_heartbeats.outcome == 'failure'" not in recovery_step:
            failures.append(
                "heartbeat recovery dispatch must only run after heartbeat check failure"
            )
        if (
            "steps.check_heartbeats.outputs.recovery_required == 'true'"
            not in recovery_step
        ):
            failures.append(
                "heartbeat recovery dispatch must require a new or changed incident"
            )
        if "GH_TOKEN: ${{ github.token }}" not in recovery_step:
            failures.append("heartbeat recovery dispatch must use github.token")
        if "gh workflow run scraper-cron.yml" not in recovery_step:
            failures.append("heartbeat recovery dispatch must run scraper-cron.yml")
        if "refresh_analytics=false" not in recovery_step:
            failures.append(
                "heartbeat recovery dispatch must skip analytics aggregation"
            )
        if "--status in_progress" not in recovery_step:
            failures.append("heartbeat recovery dispatch must check in-progress runs")
        if "--status queued" not in recovery_step:
            failures.append("heartbeat recovery dispatch must check queued runs")

    if failures:
        print("Scraper workflow guardrail check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("OK: scraper workflow guardrails are configured.")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
