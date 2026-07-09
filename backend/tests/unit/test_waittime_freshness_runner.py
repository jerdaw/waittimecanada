from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER_PATH = REPO_ROOT / "scripts" / "waittime-freshness-runner.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("waittime_freshness_runner", RUNNER_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _health_payload(
    *,
    healthy: bool = True,
    last_update: datetime | None,
    threshold: int = 120,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "healthy": healthy,
        "stale_threshold_minutes": threshold,
        "sources": [],
    }
    if last_update is not None:
        payload["last_update"] = last_update.isoformat().replace("+00:00", "Z")
    return payload


def test_check_marks_fresh_health_safe() -> None:
    runner = _load_runner()
    now = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)

    decision = runner.evaluate_health(
        _health_payload(last_update=now - timedelta(minutes=30)),
        now=now,
    )

    assert decision.exit_code == runner.EXIT_SAFE
    assert decision.age_minutes == 30
    assert decision.reason == "fresh"


def test_check_marks_unhealthy_payload_unsafe() -> None:
    runner = _load_runner()
    now = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)

    decision = runner.evaluate_health(
        _health_payload(healthy=False, last_update=now - timedelta(minutes=15)),
        now=now,
    )

    assert decision.exit_code == runner.EXIT_UNSAFE
    assert decision.reason == "unhealthy"


def test_check_marks_age_at_recovery_threshold_unsafe() -> None:
    runner = _load_runner()
    now = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)

    decision = runner.evaluate_health(
        _health_payload(last_update=now - timedelta(minutes=90)),
        now=now,
    )

    assert decision.exit_code == runner.EXIT_UNSAFE
    assert decision.age_minutes == 90
    assert decision.reason == "age_threshold"


def test_check_marks_missing_last_update_as_failure() -> None:
    runner = _load_runner()
    now = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)

    decision = runner.evaluate_health(_health_payload(last_update=None), now=now)

    assert decision.exit_code == runner.EXIT_CHECK_FAILED
    assert decision.reason == "missing_last_update"


def test_watchdog_dry_run_reports_recovery_without_running_scrape(capsys) -> None:
    runner = _load_runner()
    now = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)
    commands: list[list[str]] = []

    exit_code = runner.run_watchdog(
        fetch_health=lambda: _health_payload(last_update=now - timedelta(minutes=95)),
        now=lambda: now,
        run_command=lambda command, cwd=None, env=None: commands.append(command) or 0,
        dry_run=True,
    )

    output = capsys.readouterr().out
    assert exit_code == runner.EXIT_SAFE
    assert commands == []
    assert "would run freshness-only scraper recovery" in output


def test_scrape_dry_run_does_not_print_secret_values(monkeypatch, capsys) -> None:
    runner = _load_runner()
    sensitive_value = "do-not-print-database-url-value"
    monkeypatch.setenv("DATABASE_URL", sensitive_value)

    exit_code = runner.run_scrape(dry_run=True)

    output = capsys.readouterr().out
    assert exit_code == runner.EXIT_SAFE
    assert sensitive_value not in output
    assert "DATABASE_URL=SET" in output
