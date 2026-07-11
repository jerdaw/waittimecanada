#!/usr/bin/env python3
"""
Roadmap Consistency Checker

Verifies that docs/planning/roadmap.md stays consistent with actual implementation.
Prevents documentation drift by checking:
- Schema table counts match declarations
- ADR file references exist
- Implementation plan references exist
- Status claims are internally consistent
"""

import re
import sys
from pathlib import Path


def get_repo_root() -> Path:
    """Find repository root by locating .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root (no .git directory)")


def check_schema_table_count(roadmap_path: Path) -> tuple[bool, str]:
    """Verify declared table count matches listed tables."""
    content = roadmap_path.read_text()

    # Find the schema section
    match = re.search(r"### Database Schema \((\d+) tables\)", content)
    if not match:
        return False, "Could not find 'Database Schema (N tables)' heading"

    declared_count = int(match.group(1))

    # Count table rows in the section (lines starting with | `tablename` |)
    table_pattern = r"\| `([a-z_]+)` \|"
    tables = re.findall(table_pattern, content)
    actual_count = len(tables)

    if declared_count != actual_count:
        return (
            False,
            f"Schema table count mismatch: header says {declared_count}, but {actual_count} tables listed: {', '.join(tables)}",
        )

    return True, f"✓ Schema table count correct: {actual_count} tables"


def check_adr_files(roadmap_path: Path, repo_root: Path) -> tuple[bool, str]:
    """Verify all referenced ADR files exist."""
    content = roadmap_path.read_text()
    adr_dir = repo_root / "docs" / "adr"

    # Find ADR references like [0002](../adr/0002-metric-ontology.md)
    adr_pattern = r"\[(\d{4})\]\(\.\./adr/([\w-]+\.md)\)"
    references = re.findall(adr_pattern, content)

    if not references:
        return False, "No ADR references found in roadmap"

    missing = []
    for adr_num, filename in references:
        adr_path = adr_dir / filename
        if not adr_path.exists():
            missing.append(f"ADR-{adr_num}: {filename}")

    if missing:
        return False, "Missing ADR files:\n  " + "\n  ".join(missing)

    return True, f"✓ All {len(references)} referenced ADRs exist"


def check_implementation_plans(roadmap_path: Path, repo_root: Path) -> tuple[bool, str]:
    """Verify all referenced implementation plan files exist."""
    content = roadmap_path.read_text()

    # Find implementation plan references like `docs/planning/implementation/milestone-9-launch.md`
    plan_pattern = r"`(docs/planning/(?:implementation|archive)/[\w-]+\.md)`"
    references = re.findall(plan_pattern, content)

    if not references:
        return False, "No implementation plan references found"

    missing = []
    for plan_path_str in references:
        plan_path = repo_root / plan_path_str
        if not plan_path.exists():
            missing.append(plan_path_str)

    if missing:
        return False, "Missing implementation plan files:\n  " + "\n  ".join(missing)

    return True, f"✓ All {len(references)} referenced implementation plans exist"


def _completed_milestones_table(content: str) -> str | None:
    """Extract only the Completed Milestones table body."""
    table_section = re.search(
        r"## Completed Milestones\s*\n\s*\| Milestone \| Summary \|\s*\n\s*\|[-|]+\|\s*\n((?:\| \*\*M\d+:.*\n)+)",
        content,
        re.MULTILINE,
    )
    if not table_section:
        return None
    return table_section.group(1)


def check_milestone_completion_consistency(roadmap_path: Path) -> tuple[bool, str]:
    """Verify completed milestones in table match milestone list."""
    content = roadmap_path.read_text()

    table_content = _completed_milestones_table(content)
    if not table_content:
        return False, "Could not find Completed Milestones table"

    # Extract milestone numbers from table
    table_milestones = set(re.findall(r"\*\*M(\d+):", table_content))

    # Check if milestone descriptions exist (basic sanity check)
    if len(table_milestones) < 8:  # We know we have at least M1-M8, M10-M15
        return (
            False,
            f"Only {len(table_milestones)} completed milestones found in table, expected more",
        )

    return True, f"✓ Found {len(table_milestones)} completed milestones"


def _extract_roadmap_status(content: str) -> tuple[str, str] | None:
    """Extract roadmap Current Snapshot date and progress text."""
    status_match = re.search(
        r"## Current Snapshot \(Updated ([^)]+)\)\s*\n\s*\*\*Progress:\*\* (.+?)(?=\n\n|\*\*|\Z)",
        content,
        re.DOTALL,
    )

    if not status_match:
        return None

    update_date = status_match.group(1)
    progress_text = status_match.group(2)
    return update_date, progress_text


def _latest_completed_milestone(content: str) -> int | None:
    """Return the highest completed milestone number from roadmap content."""
    table_content = _completed_milestones_table(content)
    if not table_content:
        return None
    completed_milestones = [int(value) for value in re.findall(r"\*\*M(\d+):", table_content)]
    if not completed_milestones:
        return None
    return max(completed_milestones)


def check_status_summary_freshness(roadmap_path: Path) -> tuple[bool, str]:
    """Verify Current Snapshot section mentions latest completed work."""
    content = roadmap_path.read_text()

    status = _extract_roadmap_status(content)
    if not status:
        return False, "Could not find 'Current Snapshot' section"

    update_date, progress_text = status

    # Verify date is in YYYY-MM-DD format
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", update_date):
        return False, f"Current Snapshot date '{update_date}' is not in YYYY-MM-DD format"

    latest_milestone = _latest_completed_milestone(content)
    if latest_milestone is None:
        return False, "Could not determine latest completed milestone"

    expected_keywords = [f"Milestone {latest_milestone}", f"M{latest_milestone}"]

    if not any(keyword in progress_text for keyword in expected_keywords):
        return (
            False,
            f"Current Snapshot may be stale - doesn't mention latest completed milestone M{latest_milestone}",
        )

    return True, f"✓ Current Snapshot updated {update_date} and mentions latest completed milestone"


def check_readme_status_alignment(roadmap_path: Path, repo_root: Path) -> tuple[bool, str]:
    """Verify README public status dates and latest milestone align with roadmap."""
    readme_path = repo_root / "README.md"
    if not readme_path.exists():
        return False, "README.md not found"

    roadmap_content = roadmap_path.read_text()
    readme_content = readme_path.read_text()

    roadmap_status = _extract_roadmap_status(roadmap_content)
    if not roadmap_status:
        return False, "Could not find roadmap Current Snapshot section"
    roadmap_date, _progress_text = roadmap_status

    latest_milestone = _latest_completed_milestone(roadmap_content)
    if latest_milestone is None:
        return False, "Could not determine latest completed milestone"

    baseline_match = re.search(r"roadmap baseline on \*\*([^*]+)\*\*", readme_content)
    status_heading_match = re.search(
        r"^## .*Current Status \(as of ([^)]+)\)",
        readme_content,
        re.MULTILINE,
    )

    if not baseline_match:
        return False, "README is missing the roadmap baseline date"
    if not status_heading_match:
        return False, "README is missing the Current Status date"

    readme_dates = {
        "baseline": baseline_match.group(1),
        "current status": status_heading_match.group(1),
    }
    malformed_dates = {
        label: date
        for label, date in readme_dates.items()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date)
    }
    if malformed_dates:
        details = ", ".join(f"{label}='{date}'" for label, date in malformed_dates.items())
        return (
            False,
            f"README status dates must use YYYY-MM-DD format: {details}",
        )

    stale_dates = {label: date for label, date in readme_dates.items() if date != roadmap_date}
    if stale_dates:
        details = ", ".join(f"{label}={date}" for label, date in stale_dates.items())
        return (
            False,
            f"README status date mismatch: roadmap={roadmap_date}, {details}",
        )

    current_status_start = status_heading_match.start()
    next_h2_match = re.search(
        r"^## ",
        readme_content[status_heading_match.end() :],
        re.MULTILINE,
    )
    current_status_end = (
        status_heading_match.end() + next_h2_match.start() if next_h2_match else len(readme_content)
    )
    current_status_section = readme_content[current_status_start:current_status_end]
    expected_keywords = [f"Milestone {latest_milestone}", f"M{latest_milestone}"]

    if not any(keyword in current_status_section for keyword in expected_keywords):
        return (
            False,
            f"README Current Status may be stale - doesn't mention latest completed milestone M{latest_milestone}",
        )

    return (
        True,
        f"✓ README status dates match roadmap date {roadmap_date} and mention M{latest_milestone}",
    )


EXECUTION_COLUMNS = ("Priority", "Outcome", "State", "Gate", "Done when")
ALLOWED_PRIORITIES = {"P0", "P1", "P2"}
ALLOWED_STATES = {
    "Ready",
    "Decision required",
    "External prerequisite",
    "In validation",
    "Later",
}


def _section_bodies(content: str, heading: str) -> list[str]:
    pattern = rf"^## {re.escape(heading)}\s*$\n(.*?)(?=^## |\Z)"
    return re.findall(pattern, content, re.MULTILINE | re.DOTALL)


def _table_cells(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_table_separator(line: str) -> bool:
    cells = _table_cells(line)
    return len(cells) == len(EXECUTION_COLUMNS) and all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in cells
    )


def check_execution_roadmap_structure(roadmap_path: Path) -> tuple[bool, str]:
    """Validate permanent guardrails and the finite execution queue."""
    content = roadmap_path.read_text(encoding="utf-8")
    issues: list[str] = []

    for legacy_heading in ("Active Priorities", "Active Roadmap"):
        if re.search(rf"^## {re.escape(legacy_heading)}\s*$", content, re.MULTILINE):
            issues.append(f"legacy section '## {legacy_heading}' must be removed")

    guardrail_sections = _section_bodies(content, "Continuous Guardrails")
    if len(guardrail_sections) != 1:
        issues.append("expected exactly one '## Continuous Guardrails' section")
    elif re.search(r"^- \[[ xX]\] ", guardrail_sections[0], re.MULTILINE):
        issues.append("Continuous Guardrails must not contain task-list checkboxes")

    queue_sections = _section_bodies(content, "Execution Queue")
    if len(queue_sections) != 1:
        issues.append("expected exactly one '## Execution Queue' section")
    else:
        table_lines = [
            line.strip() for line in queue_sections[0].splitlines() if line.strip().startswith("|")
        ]
        if len(table_lines) < 3:
            issues.append("Execution Queue must contain a header, separator, and row")
        elif tuple(_table_cells(table_lines[0])) != EXECUTION_COLUMNS:
            issues.append("Execution Queue columns must be: " + ", ".join(EXECUTION_COLUMNS))
        elif not _is_table_separator(table_lines[1]):
            issues.append("Execution Queue must use a valid Markdown separator row")
        else:
            for row_number, line in enumerate(table_lines[2:], start=1):
                cells = _table_cells(line)
                if len(cells) != len(EXECUTION_COLUMNS):
                    issues.append(f"Execution Queue row {row_number} has the wrong column count")
                    continue
                priority, outcome, state, gate, done_when = cells
                if priority not in ALLOWED_PRIORITIES:
                    issues.append(
                        f"Execution Queue row {row_number} has invalid priority '{priority}'"
                    )
                if state not in ALLOWED_STATES:
                    issues.append(f"Execution Queue row {row_number} has invalid state '{state}'")
                if not outcome:
                    issues.append(f"Execution Queue row {row_number} requires a non-empty outcome")
                if not gate:
                    issues.append(f"Execution Queue row {row_number} requires a non-empty gate")
                if not done_when:
                    issues.append(
                        f"Execution Queue row {row_number} requires a non-empty done-when value"
                    )

    if issues:
        return False, "Roadmap execution structure issues:\n  " + "\n  ".join(issues)
    return True, "✓ Roadmap execution structure is complete"


def main() -> int:
    """Run all consistency checks."""
    print("🔍 Roadmap Consistency Checker\n")

    try:
        repo_root = get_repo_root()
        roadmap_path = repo_root / "docs" / "planning" / "roadmap.md"

        if not roadmap_path.exists():
            print(f"❌ Roadmap not found: {roadmap_path}")
            return 1

        print(f"Checking: {roadmap_path.relative_to(repo_root)}\n")

        # Run all checks
        checks = [
            ("Schema Table Count", check_schema_table_count, (roadmap_path,)),
            ("ADR File References", check_adr_files, (roadmap_path, repo_root)),
            ("Implementation Plans", check_implementation_plans, (roadmap_path, repo_root)),
            ("Milestone Completion", check_milestone_completion_consistency, (roadmap_path,)),
            ("Snapshot Summary", check_status_summary_freshness, (roadmap_path,)),
            ("README Status Alignment", check_readme_status_alignment, (roadmap_path, repo_root)),
            ("Roadmap Execution Structure", check_execution_roadmap_structure, (roadmap_path,)),
        ]

        results = []
        for check_name, check_func, args in checks:
            try:
                success, message = check_func(*args)
                results.append((check_name, success, message))
            except Exception as e:
                results.append((check_name, False, f"Check failed with error: {e}"))

        # Print results
        all_passed = True
        for check_name, success, message in results:
            status = "✓" if success else "✗"
            print(f"{status} {check_name}")
            if not success:
                print(f"  {message}\n")
                all_passed = False

        print("\n" + "=" * 60)
        if all_passed:
            print("✅ All roadmap consistency checks passed!")
            return 0
        else:
            print("❌ Some roadmap consistency checks failed.")
            print("   Update docs/planning/roadmap.md to fix inconsistencies.")
            return 1

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
