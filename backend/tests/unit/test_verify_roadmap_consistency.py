from pathlib import Path

import pytest

from scripts.verify_roadmap_consistency import (
    check_execution_roadmap_structure,
    check_readme_status_alignment,
    check_status_summary_freshness,
    check_stewardship_trigger_reference,
)


def _write_roadmap(
    tmp_path: Path,
    progress: str,
    snapshot_date: str = "2026-06-12",
    extra_content: str = "",
) -> Path:
    roadmap_path = tmp_path / "roadmap.md"
    roadmap_path.write_text(
        f"""# Implementation Roadmap

## Current Snapshot (Updated {snapshot_date})

**Progress:** {progress}

## Completed Milestones

| Milestone | Summary |
|-----------|---------|
| **M14: Data Quality and Anomaly Detection** | Data-quality service |
| **M15: Analytics and Benchmarking** | Analytics dashboard |
| **M33: Historical Occupancy Trends** | Occupancy aggregation |
{extra_content}
""",
        encoding="utf-8",
    )
    return roadmap_path


def _write_readme(
    tmp_path: Path,
    baseline_date: str = "2026-06-12",
    status_date: str = "2026-06-12",
    current_status: str = "M30-M33: Reliability and historical occupancy trends",
) -> Path:
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        f"""# Wait Time Canada

As reflected in the current runtime and roadmap baseline on **{baseline_date}**:

## Current Status (as of {status_date})

### Milestones Completed

- {current_status}
""",
        encoding="utf-8",
    )
    return readme_path


def test_snapshot_summary_accepts_latest_completed_milestone(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is True
    assert "latest completed milestone" in message


def test_snapshot_summary_rejects_stale_milestone_reference(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(
        tmp_path,
        "Milestone 14 and Milestone 15 are complete.",
    )

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is False
    assert "M33" in message


def test_snapshot_summary_rejects_missing_current_snapshot(tmp_path: Path) -> None:
    roadmap_path = tmp_path / "roadmap.md"
    roadmap_path.write_text(
        """# Implementation Roadmap

## Completed Milestones

| Milestone | Summary |
|-----------|---------|
| **M33: Historical Occupancy Trends** | Occupancy aggregation |
""",
        encoding="utf-8",
    )

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is False
    assert "Current Snapshot" in message


def test_snapshot_summary_rejects_invalid_snapshot_date(tmp_path: Path) -> None:
    roadmap_path = tmp_path / "roadmap.md"
    roadmap_path.write_text(
        """# Implementation Roadmap

## Current Snapshot (Updated June 12, 2026)

**Progress:** Milestone 33 is complete.

## Completed Milestones

| Milestone | Summary |
|-----------|---------|
| **M33: Historical Occupancy Trends** | Occupancy aggregation |
""",
        encoding="utf-8",
    )

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is False
    assert "not in YYYY-MM-DD format" in message


def test_snapshot_summary_rejects_snapshot_date_with_extra_text(
    tmp_path: Path,
) -> None:
    roadmap_path = _write_roadmap(
        tmp_path,
        "Milestone 33 is complete.",
        snapshot_date="2026-06-12 extra",
    )

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is False
    assert "not in YYYY-MM-DD format" in message


def test_snapshot_summary_rejects_missing_completed_milestones(tmp_path: Path) -> None:
    roadmap_path = tmp_path / "roadmap.md"
    roadmap_path.write_text(
        """# Implementation Roadmap

## Current Snapshot (Updated 2026-06-12)

**Progress:** Milestone 33 is complete.
""",
        encoding="utf-8",
    )

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is False
    assert "latest completed milestone" in message


def test_snapshot_summary_ignores_future_milestone_references(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(
        tmp_path,
        "Milestone 33 is complete.",
        extra_content="""
## Future Work

- **M99: Future Candidate** remains only a planning placeholder.
""",
    )

    success, message = check_status_summary_freshness(roadmap_path)

    assert success is True
    assert "latest completed milestone" in message


def test_readme_status_alignment_accepts_matching_status(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    _write_readme(tmp_path)

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is True
    assert "M33" in message


def test_readme_status_alignment_ignores_future_milestone_references(
    tmp_path: Path,
) -> None:
    roadmap_path = _write_roadmap(
        tmp_path,
        "Milestone 33 is complete.",
        extra_content="""
## Future Work

- **M99: Future Candidate** remains only a planning placeholder.
""",
    )
    _write_readme(tmp_path)

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is True
    assert "M33" in message


def test_readme_status_alignment_rejects_stale_dates(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    _write_readme(tmp_path, baseline_date="2026-06-11")

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is False
    assert "date mismatch" in message


def test_readme_status_alignment_rejects_stale_milestone(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    _write_readme(tmp_path, current_status="M30-M32: Reliability hardening")

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is False
    assert "M33" in message


def test_readme_status_alignment_rejects_missing_baseline_date(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    (tmp_path / "README.md").write_text(
        """# Wait Time Canada

## Current Status (as of 2026-06-12)

- M33: Historical occupancy trends
""",
        encoding="utf-8",
    )

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is False
    assert "baseline date" in message


def test_readme_status_alignment_rejects_missing_status_date(tmp_path: Path) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    (tmp_path / "README.md").write_text(
        """# Wait Time Canada

As reflected in the current runtime and roadmap baseline on **2026-06-12**:

- M33: Historical occupancy trends
""",
        encoding="utf-8",
    )

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is False
    assert "Current Status date" in message


VALID_STEWARDSHIP_ROADMAP = """# Implementation Roadmap

## Continuous Guardrails

- Preserve clinical safety.
- Preserve ontology comparability.

## Event-Triggered Stewardship

There is no standing implementation or manual-review queue.

| Trigger | Bounded response | Stop condition |
| --- | --- | --- |
| Public freshness defect | Fail closed for the affected source | Public claims are truthful or the source is suspended |
| Security incident | Follow the incident process | The concrete risk is contained |
"""


def _write_execution_roadmap(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "roadmap.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_execution_structure_accepts_guardrails_and_dormant_stewardship(
    tmp_path: Path,
) -> None:
    roadmap_path = _write_execution_roadmap(tmp_path, VALID_STEWARDSHIP_ROADMAP)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is True
    assert "dormant stewardship" in message


@pytest.mark.parametrize("heading", ("Active Roadmap", "Execution Queue"))
def test_execution_structure_rejects_active_queue_sections(
    tmp_path: Path,
    heading: str,
) -> None:
    roadmap_path = _write_execution_roadmap(
        tmp_path,
        VALID_STEWARDSHIP_ROADMAP + f"\n## {heading}\n\n- [ ] Old item\n",
    )

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "active queue section" in message


@pytest.mark.parametrize(
    "task_item",
    (
        "- [ ] Preserve clinical safety.",
        "  * [x] Preserve clinical safety.",
        "    + [X] Preserve clinical safety.",
        "1. [ ] Preserve clinical safety.",
        "  1) [x] Preserve clinical safety.",
    ),
)
def test_execution_structure_rejects_guardrail_checkboxes(tmp_path: Path, task_item: str) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace("- Preserve clinical safety.", task_item)
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "Continuous Guardrails" in message
    assert "checkbox" in message


def test_execution_structure_requires_explicit_dormant_queue_marker(tmp_path: Path) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace(
        "There is no standing implementation or manual-review queue.\n\n",
        "",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "explicitly reject a standing queue" in message


def test_execution_structure_rejects_calendar_work_in_stewardship(tmp_path: Path) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace(
        "There is no standing implementation or manual-review queue.",
        "There is no standing implementation or manual-review queue.\n\n- Quarterly review",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "calendar-based work" in message


@pytest.mark.parametrize(
    "intervening_content",
    (
        "",
        "Operators review this supplemental table separately.\n\n",
    ),
)
def test_execution_structure_rejects_second_stewardship_table(
    tmp_path: Path, intervening_content: str
) -> None:
    second_table = """| Trigger | Response |
| --- | --- |
| Operator event | Inspect it |
"""
    content = VALID_STEWARDSHIP_ROADMAP + "\n" + intervening_content + second_table
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "exactly one table" in message


def test_execution_structure_rejects_wrong_columns(tmp_path: Path) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace(
        "| Trigger | Bounded response | Stop condition |",
        "| Trigger | Response |",
    ).replace(
        "| --- | --- | --- |",
        "| --- | --- |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "columns" in message


def test_execution_structure_rejects_row_without_leading_pipe(tmp_path: Path) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace(
        "| Security incident | Follow the incident process | The concrete risk is contained |",
        "Security incident | Follow the incident process | The concrete risk is contained |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "must start and end with '|'" in message


def test_execution_structure_rejects_invalid_separator(tmp_path: Path) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace(
        "| --- | --- | --- |",
        "| Trigger | Bounded response | Stop condition |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "separator" in message


def test_execution_structure_rejects_empty_response_and_stop_condition(
    tmp_path: Path,
) -> None:
    content = VALID_STEWARDSHIP_ROADMAP.replace(
        "| Security incident | Follow the incident process | The concrete risk is contained |",
        "| Security incident | | |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "non-empty bounded response" in message
    assert "non-empty stop condition" in message


def test_readme_status_alignment_rejects_malformed_baseline_date(
    tmp_path: Path,
) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    _write_readme(tmp_path, baseline_date="June 12, 2026")

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is False
    assert "YYYY-MM-DD" in message
    assert "baseline" in message


def test_readme_status_alignment_rejects_malformed_status_date(
    tmp_path: Path,
) -> None:
    roadmap_path = _write_roadmap(tmp_path, "Milestone 33 is complete.")
    _write_readme(tmp_path, status_date="June 12, 2026")

    success, message = check_readme_status_alignment(roadmap_path, tmp_path)

    assert success is False
    assert "YYYY-MM-DD" in message
    assert "current status" in message


def test_repository_roadmap_uses_dormant_stewardship_structure() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    success, message = check_execution_roadmap_structure(repo_root / "docs/planning/roadmap.md")

    assert success is True, message


def test_stewardship_trigger_reference_rejects_standing_manual_queue(
    tmp_path: Path,
) -> None:
    manual_tasks_path = tmp_path / "manual-tasks.md"
    manual_tasks_path.write_text(
        """# Manual Tasks

## External Operations

- [ ] Complete the pilot.

## Recurring Reviews

- [ ] Quarterly review source links.
""",
        encoding="utf-8",
    )

    success, message = check_stewardship_trigger_reference(manual_tasks_path)

    assert success is False
    assert "task-list checkboxes" in message
    assert "External Operations" in message
    assert "calendar-based" in message


def test_repository_stewardship_trigger_reference_is_dormant() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    success, message = check_stewardship_trigger_reference(
        repo_root / "docs/planning/manual-tasks.md"
    )

    assert success is True, message
