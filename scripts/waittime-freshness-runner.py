#!/usr/bin/env python3
"""Trusted-runner wrapper for Wait Time Canada freshness operations."""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

DEFAULT_BASE_URL = "https://wait-time.ca"
DEFAULT_UNSAFE_AGE_MINUTES = 90
DEFAULT_STALE_AGE_MINUTES = 120
DEFAULT_LOCK_FILE = Path("/tmp/waittime-freshness-runner.lock")  # noqa: S108 - documented runner lock path.
HTTP_TIMEOUT_SECONDS = 30

EXIT_SAFE = 0
EXIT_CHECK_FAILED = 1
EXIT_UNSAFE = 2

ENV_NAMES = (
    "DATABASE_URL",
    "SENTRY_DSN",
    "ALERT_API_URL",
    "ALERT_USER_KEY",
    "ALERT_API_TOKEN",
    "OPERATIONAL_NOTIFICATION_MODE",
)

CommandRunner = Callable[[list[str], Path | None, Mapping[str, str] | None], int]
HealthFetcher = Callable[[], dict[str, Any]]
Clock = Callable[[], datetime]


def _emit(message: str) -> None:
    sys.stdout.write(f"{message}\n")


@dataclass(frozen=True)
class HealthDecision:
    exit_code: int
    reason: str
    healthy: bool | None
    age_minutes: int | None
    last_update: datetime | None
    unsafe_age_minutes: int
    stale_age_minutes: int


def utc_now() -> datetime:
    return datetime.now(UTC)


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def evaluate_health(
    payload: Mapping[str, Any],
    *,
    now: datetime | None = None,
    unsafe_age_minutes: int = DEFAULT_UNSAFE_AGE_MINUTES,
    stale_age_minutes: int = DEFAULT_STALE_AGE_MINUTES,
) -> HealthDecision:
    current_time = (now or utc_now()).astimezone(UTC)
    healthy_value = payload.get("healthy")
    healthy = healthy_value if isinstance(healthy_value, bool) else None
    last_update = _parse_timestamp(payload.get("last_update"))

    if last_update is None:
        return HealthDecision(
            exit_code=EXIT_CHECK_FAILED,
            reason="missing_last_update",
            healthy=healthy,
            age_minutes=None,
            last_update=None,
            unsafe_age_minutes=unsafe_age_minutes,
            stale_age_minutes=stale_age_minutes,
        )

    age_minutes = int((current_time - last_update).total_seconds() // 60)

    if healthy is False:
        return HealthDecision(
            exit_code=EXIT_UNSAFE,
            reason="unhealthy",
            healthy=healthy,
            age_minutes=age_minutes,
            last_update=last_update,
            unsafe_age_minutes=unsafe_age_minutes,
            stale_age_minutes=stale_age_minutes,
        )

    if age_minutes >= unsafe_age_minutes:
        return HealthDecision(
            exit_code=EXIT_UNSAFE,
            reason="age_threshold",
            healthy=healthy,
            age_minutes=age_minutes,
            last_update=last_update,
            unsafe_age_minutes=unsafe_age_minutes,
            stale_age_minutes=stale_age_minutes,
        )

    return HealthDecision(
        exit_code=EXIT_SAFE,
        reason="fresh",
        healthy=healthy,
        age_minutes=age_minutes,
        last_update=last_update,
        unsafe_age_minutes=unsafe_age_minutes,
        stale_age_minutes=stale_age_minutes,
    )


def print_decision(decision: HealthDecision) -> None:
    last_update = (
        decision.last_update.isoformat().replace("+00:00", "Z")
        if decision.last_update is not None
        else "unknown"
    )
    _emit(
        "health_check "
        f"reason={decision.reason} "
        f"exit_code={decision.exit_code} "
        f"healthy={decision.healthy} "
        f"age_minutes={decision.age_minutes} "
        f"last_update={last_update} "
        f"unsafe_age_minutes={decision.unsafe_age_minutes} "
        f"stale_age_minutes={decision.stale_age_minutes}"
    )


def fetch_health(base_url: str = DEFAULT_BASE_URL) -> dict[str, Any]:
    health_url = base_url.rstrip("/") + "/api/health"
    parsed = urllib.parse.urlparse(health_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("health URL must use http or https")

    request = urllib.request.Request(  # noqa: S310 - scheme is validated above.
        health_url,
        headers={"User-Agent": "waittime-freshness-runner/1.0"},
    )
    with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:  # noqa: S310
        payload = json.load(response)
    if not isinstance(payload, dict):
        raise ValueError("health endpoint did not return a JSON object")
    return payload


def fetch_health_from_file(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("health JSON file must contain an object")
    return payload


def _env_presence() -> str:
    return " ".join(
        f"{name}={'SET' if os.environ.get(name) else 'UNSET'}" for name in ENV_NAMES
    )


def _run_command(
    command: list[str],
    cwd: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    result = subprocess.run(  # noqa: S603 - trusted runner executes fixed command argv.
        command,
        cwd=cwd,
        env=merged_env,
        check=False,
    )
    return result.returncode


def _dry_run_command(command: Sequence[str], cwd: Path | None) -> None:
    cwd_text = str(cwd) if cwd is not None else str(ROOT)
    _emit(f"DRY RUN: cwd={cwd_text} command={' '.join(command)}")


def run_check(
    *,
    fetcher: HealthFetcher,
    now: Clock = utc_now,
    unsafe_age_minutes: int = DEFAULT_UNSAFE_AGE_MINUTES,
    stale_age_minutes: int = DEFAULT_STALE_AGE_MINUTES,
) -> int:
    try:
        payload = fetcher()
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        _emit(
            f"health_check reason=fetch_failed exit_code={EXIT_CHECK_FAILED} error={exc.__class__.__name__}"
        )
        return EXIT_CHECK_FAILED

    decision = evaluate_health(
        payload,
        now=now(),
        unsafe_age_minutes=unsafe_age_minutes,
        stale_age_minutes=stale_age_minutes,
    )
    print_decision(decision)
    return decision.exit_code


def run_scrape(
    *,
    run_command: CommandRunner = _run_command,
    dry_run: bool = False,
) -> int:
    _emit(f"environment {_env_presence()}")
    commands = [
        ["uv", "run", "python", "-m", "waittime.cli.scraper", "--all"],
        [
            "uv",
            "run",
            "python",
            "-m",
            "waittime.cli.check_heartbeat",
            "--max-age",
            str(DEFAULT_STALE_AGE_MINUTES),
            "--max-consecutive-failures",
            "1",
            "--dry-run",
            "--verbose",
        ],
    ]
    for command in commands:
        if dry_run:
            _dry_run_command(command, BACKEND)
            continue
        exit_code = run_command(command, BACKEND, None)
        if exit_code != EXIT_SAFE:
            return exit_code
    return EXIT_SAFE


def run_aggregate(
    *,
    run_command: CommandRunner = _run_command,
    dry_run: bool = False,
) -> int:
    command = [
        "uv",
        "run",
        "python",
        "-m",
        "waittime.cli.aggregate",
        "--incremental",
        "--period",
        "daily",
    ]
    if dry_run:
        _dry_run_command(command, BACKEND)
        return EXIT_SAFE
    return run_command(command, BACKEND, None)


def run_smoke(
    *,
    base_url: str = DEFAULT_BASE_URL,
    run_command: CommandRunner = _run_command,
    dry_run: bool = False,
) -> int:
    command = ["bash", "scripts/production-smoke.sh"]
    env = {"PRODUCTION_BASE_URL": base_url}
    if dry_run:
        _emit("DRY RUN: PRODUCTION_BASE_URL=SET")
        _dry_run_command(command, ROOT)
        return EXIT_SAFE
    return run_command(command, ROOT, env)


def run_watchdog(
    *,
    fetch_health: HealthFetcher,
    now: Clock = utc_now,
    run_command: CommandRunner = _run_command,
    dry_run: bool = False,
    unsafe_age_minutes: int = DEFAULT_UNSAFE_AGE_MINUTES,
    stale_age_minutes: int = DEFAULT_STALE_AGE_MINUTES,
) -> int:
    try:
        payload = fetch_health()
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        _emit(
            f"watchdog reason=fetch_failed exit_code={EXIT_CHECK_FAILED} error={exc.__class__.__name__}"
        )
        return EXIT_CHECK_FAILED

    decision = evaluate_health(
        payload,
        now=now(),
        unsafe_age_minutes=unsafe_age_minutes,
        stale_age_minutes=stale_age_minutes,
    )
    print_decision(decision)

    if decision.exit_code == EXIT_CHECK_FAILED:
        return EXIT_CHECK_FAILED
    if decision.exit_code == EXIT_SAFE:
        _emit("watchdog action=none")
        return EXIT_SAFE

    if dry_run:
        _emit("DRY RUN: would run freshness-only scraper recovery")
        return EXIT_SAFE

    _emit("watchdog action=freshness_only_scrape")
    scrape_exit = run_scrape(run_command=run_command, dry_run=False)
    if scrape_exit != EXIT_SAFE:
        return scrape_exit

    return run_check(
        fetcher=fetch_health,
        now=now,
        unsafe_age_minutes=unsafe_age_minutes,
        stale_age_minutes=stale_age_minutes,
    )


@contextlib.contextmanager
def exclusive_lock(path: Path) -> Iterator[bool]:
    try:
        import fcntl  # pylint: disable=import-outside-toplevel
    except ImportError:
        yield True
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        try:
            yield True
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _fetcher_from_args(args: argparse.Namespace) -> HealthFetcher:
    if args.health_json_file is not None:
        return lambda: fetch_health_from_file(args.health_json_file)
    return lambda: fetch_health(args.base_url)


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument(
        "--unsafe-age-minutes", type=int, default=DEFAULT_UNSAFE_AGE_MINUTES
    )
    parser.add_argument(
        "--stale-age-minutes", type=int, default=DEFAULT_STALE_AGE_MINUTES
    )
    parser.add_argument("--health-json-file", type=Path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-file", type=Path, default=DEFAULT_LOCK_FILE)

    subparsers = parser.add_subparsers(dest="command", required=True)

    check = subparsers.add_parser("check", help="Check public freshness state")
    _add_common_args(check)

    watchdog = subparsers.add_parser("watchdog", help="Recover freshness when unsafe")
    _add_common_args(watchdog)
    watchdog.add_argument("--dry-run", action="store_true")

    scrape = subparsers.add_parser("scrape", help="Run a freshness-only scraper cycle")
    scrape.add_argument("--dry-run", action="store_true")

    aggregate = subparsers.add_parser(
        "aggregate", help="Refresh daily analytics aggregates"
    )
    aggregate.add_argument("--dry-run", action="store_true")

    smoke = subparsers.add_parser("smoke", help="Run production smoke checks")
    smoke.add_argument("--base-url", default=DEFAULT_BASE_URL)
    smoke.add_argument("--dry-run", action="store_true")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "check":
        return run_check(
            fetcher=_fetcher_from_args(args),
            unsafe_age_minutes=args.unsafe_age_minutes,
            stale_age_minutes=args.stale_age_minutes,
        )

    with exclusive_lock(args.lock_file) as acquired:
        if not acquired:
            _emit("Another freshness runner invocation is active; skipping overlap.")
            return EXIT_SAFE

        if args.command == "watchdog":
            return run_watchdog(
                fetch_health=_fetcher_from_args(args),
                dry_run=args.dry_run,
                unsafe_age_minutes=args.unsafe_age_minutes,
                stale_age_minutes=args.stale_age_minutes,
            )
        if args.command == "scrape":
            return run_scrape(dry_run=args.dry_run)
        if args.command == "aggregate":
            return run_aggregate(dry_run=args.dry_run)
        if args.command == "smoke":
            return run_smoke(base_url=args.base_url, dry_run=args.dry_run)

    return EXIT_CHECK_FAILED


if __name__ == "__main__":
    sys.exit(main())
