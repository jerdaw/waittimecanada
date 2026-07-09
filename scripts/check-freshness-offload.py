#!/usr/bin/env python3
"""Validate public-safe freshness offload runner artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

EXAMPLE_DIR = Path("docs/operations/examples")
RUNNER = Path("scripts/waittime-freshness-runner.py")
OFFLOAD_DOC = Path("docs/operations/heartbeat-offload-pilot.md")
CHECK_DOCS = Path("scripts/check-docs.sh")

SYSTEMD_FILES = {
    "waittime-freshness-scraper.service": [
        "EnvironmentFile=/etc/waittime/freshness.env",
        "waittime-freshness-runner.py scrape",
    ],
    "waittime-freshness-scraper.timer": [
        "OnCalendar=*-*-* *:17:00",
    ],
    "waittime-freshness-watchdog.service": [
        "EnvironmentFile=/etc/waittime/freshness.env",
        "waittime-freshness-runner.py watchdog",
    ],
    "waittime-freshness-watchdog.timer": [
        "OnCalendar=*-*-* *:07,37:00",
    ],
    "waittime-freshness-aggregate.service": [
        "EnvironmentFile=/etc/waittime/freshness.env",
        "waittime-freshness-runner.py aggregate",
    ],
    "waittime-freshness-aggregate.timer": [
        "OnCalendar=*-*-* 06:10:00",
        "Timezone=UTC",
    ],
}

SECRET_PATTERNS = [
    re.compile(r"postgres(?:ql)?://", re.IGNORECASE),
    re.compile(r"https://hooks\.slack\.com/", re.IGNORECASE),
    re.compile(
        r"(DATABASE_URL|ALERT_API_TOKEN|ALERT_USER_KEY|SENTRY_DSN)\s*=\s*['\"]?[^$<\s]",
        re.IGNORECASE,
    ),
]


def _emit(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def _read(root: Path, relative_path: Path) -> str:
    path = root / relative_path
    if not path.exists():
        raise AssertionError(f"Missing required offload artifact: {relative_path}")
    return path.read_text(encoding="utf-8")


def _require(text: str, needle: str, context: str, failures: list[str]) -> None:
    if needle not in text:
        failures.append(f"{context} must contain {needle!r}")


def _check_no_secret_literals(
    root: Path, relative_paths: list[Path], failures: list[str]
) -> None:
    for relative_path in relative_paths:
        try:
            text = _read(root, relative_path)
        except AssertionError:
            continue
        for pattern in SECRET_PATTERNS:
            match = pattern.search(text)
            if match:
                failures.append(
                    f"{relative_path} contains public-unsafe secret-like text: {match.group(0)}"
                )


def validate(root: Path) -> list[str]:
    failures: list[str] = []

    try:
        runner_text = _read(root, RUNNER)
    except AssertionError as exc:
        return [str(exc)]

    runner_expectations = [
        "DEFAULT_UNSAFE_AGE_MINUTES = 90",
        "DEFAULT_STALE_AGE_MINUTES = 120",
        "EXIT_SAFE = 0",
        "EXIT_CHECK_FAILED = 1",
        "EXIT_UNSAFE = 2",
        'DEFAULT_LOCK_FILE = Path("/tmp/waittime-freshness-runner.lock")',
        "waittime.cli.scraper",
        "waittime.cli.check_heartbeat",
        "waittime.cli.aggregate",
        "production-smoke.sh",
        "ENV_NAMES",
        "'SET' if os.environ.get(name) else 'UNSET'",
    ]
    for expectation in runner_expectations:
        _require(runner_text, expectation, str(RUNNER), failures)

    systemd_paths: list[Path] = []
    for filename, expectations in SYSTEMD_FILES.items():
        relative_path = EXAMPLE_DIR / filename
        systemd_paths.append(relative_path)
        try:
            text = _read(root, relative_path)
        except AssertionError as exc:
            failures.append(str(exc))
            continue
        _require(text, "Copy/adapt example only.", str(relative_path), failures)
        for expectation in expectations:
            _require(text, expectation, str(relative_path), failures)

    try:
        offload_doc = _read(root, OFFLOAD_DOC)
    except AssertionError as exc:
        failures.append(str(exc))
    else:
        for env_name in [
            "DATABASE_URL",
            "SENTRY_DSN",
            "ALERT_API_URL",
            "ALERT_USER_KEY",
            "ALERT_API_TOKEN",
            "OPERATIONAL_NOTIFICATION_MODE",
        ]:
            _require(offload_doc, env_name, str(OFFLOAD_DOC), failures)
        for required_phrase in [
            "generic trusted timer service",
            "GitHub `workflow_dispatch`",
            "Remove GitHub scheduled triggers only after",
            "24-hour soak",
        ]:
            _require(offload_doc, required_phrase, str(OFFLOAD_DOC), failures)

    try:
        check_docs = _read(root, CHECK_DOCS)
    except AssertionError as exc:
        failures.append(str(exc))
    else:
        _require(
            check_docs,
            "python3 scripts/check-freshness-offload.py",
            str(CHECK_DOCS),
            failures,
        )

    _check_no_secret_literals(root, [RUNNER, OFFLOAD_DOC, *systemd_paths], failures)
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()

    failures = validate(args.root)
    if failures:
        _emit("Freshness offload guardrail check failed:")
        for failure in failures:
            _emit(f"- {failure}")
        return 1

    _emit("OK: freshness offload guardrails are configured.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
