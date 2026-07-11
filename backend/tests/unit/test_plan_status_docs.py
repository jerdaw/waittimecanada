from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLANS_DIR = REPO_ROOT / "docs" / "superpowers" / "plans"


def _read_plan(filename: str) -> str:
    return (PLANS_DIR / filename).read_text(encoding="utf-8")


def test_merged_pull_request_plans_record_post_merge_evidence() -> None:
    expected = {
        "2026-07-10-reproducible-mkdocs-toolchain.md": (
            "PR #83 merged",
            "a14460e304288f13fe5daa159f0b2d9d014a6d30",  # pragma: allowlist secret
            ("29135426720", "29135426736", "29135426753"),
        ),
        "2026-07-10-migration-documentation-consistency.md": (
            "PR #84 merged",
            "2a88939c8ac744179e840c240f542bc0bd8cbc5c",  # pragma: allowlist secret
            ("29135462236", "29135462245", "29135462251", "29135462281"),
        ),
        "2026-07-10-ontario-methodology-revalidation.md": (
            "PR #85 merged",
            "cda6344ee4cc2cb1bafba461b93a1f4580da5521",  # pragma: allowlist secret
            ("29135499643", "29135499634", "29135499638"),
        ),
        "2026-07-10-integration-docs-migration-runner.md": (
            "PR #86 merged",
            "7c0473832e9cf27e838b0144b0c2a63dc2840235",  # pragma: allowlist secret
            ("29135530184", "29135530183", "29135530181"),
        ),
    }

    for filename, (status, merge_commit, run_ids) in expected.items():
        plan = _read_plan(filename)
        status_line = next(line for line in plan.splitlines() if line.startswith("**Status:**"))

        assert status in status_line
        assert merge_commit in plan
        assert "## Post-Merge Verification" in plan
        normalized_plan = " ".join(plan.lower().split())
        for stale_phrase in (
            "intentionally unmerged",
            "remains open",
            "do not merge",
        ):
            assert stale_phrase not in normalized_plan
        for run_id in run_ids:
            assert run_id in plan


def test_recovered_incident_plan_is_closed_as_historical() -> None:
    plan = _read_plan("2026-07-08-waittime-production-health-investigation.md")
    normalized_plan = " ".join(plan.split())
    status_line = next(line for line in plan.splitlines() if line.startswith("**Status:**"))

    assert "Historical execution plan" in status_line
    assert "docs/operations/waittime-health-investigation-2026-07-08.md" in plan
    assert "docs/planning/roadmap.md" in plan
    assert "docs/planning/manual-tasks.md" in plan
    assert "Do not execute the unchecked steps" in normalized_plan


def test_reconciliation_plan_is_closed_after_delivery() -> None:
    plan = _read_plan("2026-07-10-post-merge-plan-reconciliation.md")
    status_line = next(line for line in plan.splitlines() if line.startswith("**Status:**"))

    assert "Complete" in status_line
    assert "- [ ]" not in plan
    assert "PR #87" in plan
    assert "a8ea31945a98d97b78f9bb53ccbe742a0e9185e7" in plan  # pragma: allowlist secret
    for run_id in ("29136002101", "29136002086", "29136002079"):
        assert run_id in plan
    assert "No further autonomous implementation candidate remains" in plan
