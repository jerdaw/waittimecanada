from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


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
