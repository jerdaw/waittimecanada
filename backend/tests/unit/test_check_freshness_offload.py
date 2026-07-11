from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from shutil import copy2

REPO_ROOT = Path(__file__).resolve().parents[3]


CONTRACT_PATHS = [
    Path("scripts/waittime-freshness-runner.py"),
    Path("scripts/check-docs.sh"),
    Path("docs/operations/heartbeat-offload-pilot.md"),
    Path("docs/operations/examples/waittime-freshness-scraper.service"),
    Path("docs/operations/examples/waittime-freshness-scraper.timer"),
    Path("docs/operations/examples/waittime-freshness-watchdog.service"),
    Path("docs/operations/examples/waittime-freshness-watchdog.timer"),
    Path("docs/operations/examples/waittime-freshness-aggregate.service"),
    Path("docs/operations/examples/waittime-freshness-aggregate.timer"),
]


def test_freshness_offload_guardrail_accepts_repo_contract() -> None:
    result = subprocess.run(  # noqa: S603 - trusted repo script with fixed argv.
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check-freshness-offload.py"),
            "--root",
            str(REPO_ROOT),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr


def test_freshness_offload_guardrail_rejects_missing_hardening_section(
    tmp_path: Path,
) -> None:
    for relative_path in CONTRACT_PATHS:
        destination = tmp_path / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        copy2(REPO_ROOT / relative_path, destination)

    offload_doc = tmp_path / "docs/operations/heartbeat-offload-pilot.md"
    offload_doc.write_text(
        offload_doc.read_text(encoding="utf-8").replace(
            "## Runner Isolation", "## Runner Execution"
        ),
        encoding="utf-8",
    )

    result = subprocess.run(  # noqa: S603 - trusted repo script with fixed argv.
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check-freshness-offload.py"),
            "--root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 1
    assert "## Runner Isolation" in result.stdout
