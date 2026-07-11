from pathlib import Path

from scripts.verify_roadmap_consistency import (
    check_execution_roadmap_structure,
    check_readme_status_alignment,
    check_status_summary_freshness,
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


VALID_EXECUTION_ROADMAP = """# Implementation Roadmap

## Continuous Guardrails

- Preserve clinical safety.
- Preserve ontology comparability.

## Execution Queue

| Priority | Outcome | State | Gate | Done when |
| --- | --- | --- | --- | --- |
| P1 | Complete the pilot | In validation | Trusted runner available | A clean 24-hour soak completes |
| P2 | Evaluate expansion | Decision required | Official source selected | Provenance and tests are merged |
"""


def _write_execution_roadmap(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "roadmap.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_execution_structure_accepts_guardrails_and_complete_queue(tmp_path: Path) -> None:
    roadmap_path = _write_execution_roadmap(tmp_path, VALID_EXECUTION_ROADMAP)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is True
    assert "execution structure" in message


def test_execution_structure_rejects_legacy_active_sections(tmp_path: Path) -> None:
    roadmap_path = _write_execution_roadmap(
        tmp_path,
        VALID_EXECUTION_ROADMAP + "\n## Active Roadmap\n\n- [ ] Old item\n",
    )

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "legacy section" in message


def test_execution_structure_rejects_guardrail_checkboxes(tmp_path: Path) -> None:
    content = VALID_EXECUTION_ROADMAP.replace(
        "- Preserve clinical safety.", "- [ ] Preserve clinical safety."
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "Continuous Guardrails" in message
    assert "checkbox" in message


def test_execution_structure_rejects_wrong_columns(tmp_path: Path) -> None:
    content = VALID_EXECUTION_ROADMAP.replace(
        "| Priority | Outcome | State | Gate | Done when |",
        "| Priority | Outcome | State | Done when |",
    ).replace(
        "| --- | --- | --- | --- | --- |",
        "| --- | --- | --- | --- |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "columns" in message


def test_execution_structure_rejects_row_without_leading_pipe(tmp_path: Path) -> None:
    content = VALID_EXECUTION_ROADMAP.replace(
        "| P2 | Evaluate expansion | Decision required | Official source selected | Provenance and tests are merged |",
        "P2 | Evaluate expansion | Decision required | Official source selected | Provenance and tests are merged |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "must start and end with '|'" in message


def test_execution_structure_rejects_invalid_separator(tmp_path: Path) -> None:
    content = VALID_EXECUTION_ROADMAP.replace(
        "| --- | --- | --- | --- | --- |",
        "| Priority | Outcome | State | Gate | Done when |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "separator" in message


def test_execution_structure_rejects_invalid_priority_and_state(tmp_path: Path) -> None:
    content = VALID_EXECUTION_ROADMAP.replace(
        "| P1 | Complete the pilot | In validation |",
        "| P9 | Complete the pilot | Blocked |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "priority 'P9'" in message
    assert "state 'Blocked'" in message


def test_execution_structure_rejects_empty_gate_and_done_when(tmp_path: Path) -> None:
    content = VALID_EXECUTION_ROADMAP.replace(
        "| P1 | Complete the pilot | In validation | Trusted runner available | A clean 24-hour soak completes |",
        "| P1 | Complete the pilot | In validation | | |",
    )
    roadmap_path = _write_execution_roadmap(tmp_path, content)

    success, message = check_execution_roadmap_structure(roadmap_path)

    assert success is False
    assert "non-empty gate" in message
    assert "non-empty done-when" in message


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


def test_repository_roadmap_uses_optimized_execution_structure() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    success, message = check_execution_roadmap_structure(repo_root / "docs/planning/roadmap.md")

    assert success is True, message
