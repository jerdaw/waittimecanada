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
from typing import List, Tuple


def get_repo_root() -> Path:
    """Find repository root by locating .git directory."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find repository root (no .git directory)")


def check_schema_table_count(roadmap_path: Path) -> Tuple[bool, str]:
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
        return False, f"Schema table count mismatch: header says {declared_count}, but {actual_count} tables listed: {', '.join(tables)}"

    return True, f"✓ Schema table count correct: {actual_count} tables"


def check_adr_files(roadmap_path: Path, repo_root: Path) -> Tuple[bool, str]:
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
        return False, f"Missing ADR files:\n  " + "\n  ".join(missing)

    return True, f"✓ All {len(references)} referenced ADRs exist"


def check_implementation_plans(roadmap_path: Path, repo_root: Path) -> Tuple[bool, str]:
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
        return False, f"Missing implementation plan files:\n  " + "\n  ".join(missing)

    return True, f"✓ All {len(references)} referenced implementation plans exist"


def check_milestone_completion_consistency(roadmap_path: Path) -> Tuple[bool, str]:
    """Verify completed milestones in table match milestone list."""
    content = roadmap_path.read_text()

    # Find the completed milestones table
    table_section = re.search(
        r"## Completed Milestones\s*\n\s*\| Milestone \| Summary \|\s*\n\s*\|[-|]+\|\s*\n((?:\| \*\*M\d+:.*\n)+)",
        content,
        re.MULTILINE
    )

    if not table_section:
        return False, "Could not find Completed Milestones table"

    # Extract milestone numbers from table
    table_content = table_section.group(1)
    table_milestones = set(re.findall(r"\*\*M(\d+):", table_content))

    # Check if milestone descriptions exist (basic sanity check)
    if len(table_milestones) < 8:  # We know we have at least M1-M8, M10-M15
        return False, f"Only {len(table_milestones)} completed milestones found in table, expected more"

    return True, f"✓ Found {len(table_milestones)} completed milestones"


def check_status_summary_freshness(roadmap_path: Path) -> Tuple[bool, str]:
    """Verify Current Status section mentions latest completed work."""
    content = roadmap_path.read_text()

    # Find Current Status section
    status_match = re.search(
        r"## Current Status \(Updated ([\d-]+)\)\s*\n\s*\*\*Progress:\*\* (.+?)(?=\n\n|\*\*)",
        content,
        re.DOTALL
    )

    if not status_match:
        return False, "Could not find 'Current Status' section"

    update_date = status_match.group(1)
    progress_text = status_match.group(2)

    # Verify date is in YYYY-MM-DD format
    if not re.match(r"\d{4}-\d{2}-\d{2}", update_date):
        return False, f"Current Status date '{update_date}' is not in YYYY-MM-DD format"

    # Check that major completed milestones are mentioned
    expected_keywords = ["Milestone 14", "Milestone 15"]
    missing_keywords = [kw for kw in expected_keywords if kw not in progress_text]

    if missing_keywords:
        return False, f"Current Status may be stale - doesn't mention: {', '.join(missing_keywords)}"

    return True, f"✓ Current Status updated {update_date} and mentions recent milestones"


def check_roadmap_items_formatting(roadmap_path: Path) -> Tuple[bool, str]:
    """Verify roadmap items use consistent checkbox formatting."""
    content = roadmap_path.read_text()

    # Find roadmap sections (Now/Next/Later) - extract the full section content
    section_pattern = r"### (Now|Next|Later) \([^)]+\)(.*?)(?=###|\Z)"
    sections = re.findall(section_pattern, content, re.DOTALL)

    if not sections:
        return False, "Could not find Now/Next/Later roadmap sections"

    issues = []
    for section_name, section_content in sections:
        # Extract only lines that are checkbox items (start with "- [")
        lines = [line for line in section_content.split("\n") if line.strip().startswith("- [")]
        for line in lines:
            # Allow strikethrough for removed items: ~~**P1 / Name:**~~
            # Allow "Deferred" prefix for deprioritized items
            if not re.match(r"^- \[[x ]\] (?:~~)?\*\*(?:P\d+|Deferred) / ", line):
                issues.append(f"Malformed item in '{section_name}': {line[:60]}")

    if issues:
        return False, "Roadmap item formatting issues:\n  " + "\n  ".join(issues[:5])

    return True, f"✓ All roadmap items use consistent checkbox formatting"


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
            ("Status Summary", check_status_summary_freshness, (roadmap_path,)),
            ("Roadmap Item Formatting", check_roadmap_items_formatting, (roadmap_path,)),
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

        print("\n" + "="*60)
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
