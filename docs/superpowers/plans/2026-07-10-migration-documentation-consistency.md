# Migration Documentation Consistency Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile the canonical migration README with the files on disk and extend the existing migration guard so inventory, count, next-prefix, and placeholder drift fails CI.

**Status:** Implementation and independent review complete; delivery pending

**Architecture:** Keep filename validation in `validate_migrations()` and add an independently callable `validate_migration_documentation()` beside it. The new validator derives facts from migration filenames, parses only exact migration history headings and two canonical README statements, and returns actionable errors without modifying files. The existing CLI aggregates both validation groups.

**Tech Stack:** Python 3.12+, pathlib, regular expressions, collections.Counter, pytest, Markdown, uv

## Global Constraints

- Do not edit any existing SQL migration or apply a database migration.
- Preserve the historical duplicate-`020` exception exactly.
- Count executable `*.sql` files but exclude `*.sql.skip` from the quick-start count.
- Include both executable and skipped migrations in heading inventory and next-prefix calculation.
- Parse exact level-four migration headings; filename mentions in prose or examples do not satisfy the inventory contract.
- Reject whole-word `TODO` and `TBD` placeholders in `backend/migrations/README.md`; Markdown task-list checkboxes remain valid.
- Keep `validate_migrations()` independently callable without implicit README validation.
- Keep the Ontario methodology and ontology decision out of scope.
- Do not merge the resulting PR because its documentation paths trigger deployment on `main`.

---

## File Structure

- `backend/scripts/check_migration_sequence.py`: retain sequence checks and add pure README consistency validation plus aggregated CLI reporting.
- `backend/tests/unit/test_check_migration_sequence.py`: synthetic unit tests for every new invariant and one repository-level contract test.
- `backend/migrations/README.md`: canonical migration history, quick-start count, next prefix, examples, and completed entries.
- `docs/maintenance-audit.md`: durable completion note for the documented drift follow-up.
- `docs/superpowers/plans/2026-07-10-migration-documentation-consistency.md`: execution checklist and exact verification evidence.

### Task 1: Add Migration History Inventory Validation

**Files:**
- Modify: `backend/tests/unit/test_check_migration_sequence.py`
- Modify: `backend/scripts/check_migration_sequence.py`

**Interfaces:**
- Consumes: `migration_files(migrations_dir: Path) -> list[Path]`
- Produces: `validate_migration_documentation(migrations_dir: Path = MIGRATIONS_DIR, readme_path: Path = MIGRATIONS_README) -> list[str]`
- Produces: `MIGRATIONS_README: Path`

- [x] **Step 1: Add a synthetic README helper and failing inventory tests**

Add this helper and tests to `backend/tests/unit/test_check_migration_sequence.py`:

```python
def _write_readme(
    path: Path,
    migration_names: list[str],
    *,
    executable_count: int | None = None,
    next_number: int | None = None,
    extra_lines: list[str] | None = None,
) -> None:
    executable_count = executable_count if executable_count is not None else sum(
        name.endswith(".sql") for name in migration_names
    )
    next_number = next_number if next_number is not None else (
        max(int(name[:3]) for name in migration_names) + 1
    )
    lines = [
        "# Database Migrations",
        "",
        f"Found {executable_count} migration files:",
        "",
        f"The next migration number is `{next_number:03d}`.",
        "",
        *(f"#### {name}" for name in migration_names),
    ]
    if extra_lines:
        lines.extend(["", *extra_lines])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_complete_migration_documentation_passes(tmp_path: Path) -> None:
    names = ["001_create_tables.sql", "002_deferred_policy.sql.skip"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names)

    assert check_migration_sequence.validate_migration_documentation(tmp_path, readme) == []


def test_missing_migration_readme_is_rejected(tmp_path: Path) -> None:
    _touch(tmp_path, "001_create_tables.sql")
    readme = tmp_path / "README.md"

    assert check_migration_sequence.validate_migration_documentation(tmp_path, readme) == [
        f"migration README not found: {readme}"
    ]


def test_missing_migration_heading_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql", "002_add_index.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names[:1], executable_count=2, next_number=3)

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README is missing migration heading: 002_add_index.sql" in errors


def test_stale_migration_heading_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, [*names, "002_removed_table.sql"], executable_count=1, next_number=2)

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README has migration heading without a file: 002_removed_table.sql" in errors


def test_duplicate_migration_heading_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names, extra_lines=["#### 001_create_tables.sql"])

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README has duplicate migration heading: 001_create_tables.sql" in errors
```

- [x] **Step 2: Run the new tests and verify RED**

Run:

```bash
cd backend
uv run pytest tests/unit/test_check_migration_sequence.py \
  -k "migration_documentation or migration_readme or migration_heading" -q
```

Expected: fail because `validate_migration_documentation` does not exist.

- [x] **Step 3: Implement exact-heading inventory validation**

Add imports, constants, and the new function in `backend/scripts/check_migration_sequence.py`:

```python
from collections import Counter, defaultdict

MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"
MIGRATIONS_README = MIGRATIONS_DIR / "README.md"
MIGRATION_HEADING_RE = re.compile(
    r"^#### (?P<name>\d{3}_[a-z0-9][a-z0-9_]*\.sql(?:\.skip)?)$",
    re.MULTILINE,
)


def validate_migration_documentation(
    migrations_dir: Path = MIGRATIONS_DIR,
    readme_path: Path = MIGRATIONS_README,
) -> list[str]:
    """Return disk-derived migration README consistency errors."""
    try:
        readme = readme_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return [f"migration README not found: {readme_path}"]
    except OSError as exc:
        return [f"could not read migration README {readme_path}: {exc}"]

    names = [path.name for path in migration_files(migrations_dir)]
    expected_names = set(names)
    heading_counts = Counter(MIGRATION_HEADING_RE.findall(readme))
    documented_names = set(heading_counts)
    errors: list[str] = []

    for name in sorted(expected_names - documented_names):
        errors.append(f"README is missing migration heading: {name}")
    for name in sorted(documented_names - expected_names):
        errors.append(f"README has migration heading without a file: {name}")
    for name, count in sorted(heading_counts.items()):
        if count > 1:
            errors.append(f"README has duplicate migration heading: {name}")

    return errors
```

- [x] **Step 4: Run inventory and existing sequence tests and verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/unit/test_check_migration_sequence.py \
  -k "not repository_migration_documentation_is_current" -q
```

Expected: all selected tests pass.

- [x] **Step 5: Commit Task 1**

```bash
git add backend/scripts/check_migration_sequence.py \
  backend/tests/unit/test_check_migration_sequence.py
git commit -m "test: validate migration history inventory"
```

### Task 2: Guard Count, Next Prefix, Placeholders, and CLI Integration

**Files:**
- Modify: `backend/tests/unit/test_check_migration_sequence.py`
- Modify: `backend/scripts/check_migration_sequence.py`

**Interfaces:**
- Consumes: `validate_migration_documentation(...) -> list[str]` from Task 1
- Produces: one error per canonical count/next-number defect and per placeholder line
- Produces: `main() -> int` aggregating sequence and documentation validation

- [x] **Step 1: Add failing derived-fact and CLI tests**

Add tests covering missing and stale count, stale and duplicate next-number
statements, placeholder line reporting, and CLI aggregation. Use exact assertions:

```python
def test_stale_executable_count_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql", "002_add_index.sql", "003_policy.sql.skip"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names, executable_count=1)

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README executable migration count is 1; expected 2" in errors


def test_missing_executable_count_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names)
    readme.write_text(
        readme.read_text(encoding="utf-8").replace("Found 1 migration files:\n", ""),
        encoding="utf-8",
    )

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README is missing the canonical executable migration count" in errors


def test_duplicate_executable_count_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names, extra_lines=["Found 1 migration files:"])

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert (
        "README must contain exactly one canonical executable migration count; found 2"
        in errors
    )


def test_stale_next_migration_number_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql", "002_add_index.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names, next_number=2)

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README next migration number is 002; expected 003" in errors


def test_missing_next_migration_statement_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names)
    readme.write_text(
        readme.read_text(encoding="utf-8").replace(
            "The next migration number is `002`.\n",
            "",
        ),
        encoding="utf-8",
    )

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README is missing the canonical next migration statement" in errors


def test_duplicate_next_migration_statement_is_rejected(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(
        readme,
        names,
        extra_lines=["The next migration number is `001`."],
    )

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README must contain exactly one canonical next migration statement; found 2" in errors


def test_readme_placeholder_reports_line_number(tmp_path: Path) -> None:
    names = ["001_create_tables.sql"]
    _touch(tmp_path, *names)
    readme = tmp_path / "README.md"
    _write_readme(readme, names, extra_lines=["Details: TBD after review"])

    errors = check_migration_sequence.validate_migration_documentation(tmp_path, readme)

    assert "README contains unresolved placeholder 'TBD' at line 9" in errors


def test_main_aggregates_sequence_and_documentation_errors(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        check_migration_sequence,
        "validate_migrations",
        lambda: ["sequence defect"],
    )
    monkeypatch.setattr(
        check_migration_sequence,
        "validate_migration_documentation",
        lambda: ["documentation defect"],
    )

    assert check_migration_sequence.main() == 1
    assert capsys.readouterr().out == (
        "Migration validation failed:\n"
        "- sequence defect\n"
        "- documentation defect\n"
    )
```

- [x] **Step 2: Run the new tests and verify RED**

Run:

```bash
cd backend
uv run pytest tests/unit/test_check_migration_sequence.py \
  -k "count or next_migration or placeholder or main_aggregates" -q
```

Expected: failures because the validator does not yet inspect these facts and
`main()` does not aggregate documentation errors.

- [x] **Step 3: Implement derived-fact validation and aggregate CLI output**

Add these regex constants:

```python
EXECUTABLE_COUNT_RE = re.compile(
    r"^Found (?P<count>\d+) migration files:$",
    re.MULTILINE,
)
NEXT_MIGRATION_RE = re.compile(
    r"^The next migration number is `(?P<number>\d{3})`\.$",
    re.MULTILINE,
)
PLACEHOLDER_RE = re.compile(r"\b(?:TODO|TBD)\b")
```

Before returning from `validate_migration_documentation()`, append validation
for the canonical count, next prefix, and placeholders:

```python
    executable_count = sum(name.endswith(".sql") for name in names)
    count_matches = list(EXECUTABLE_COUNT_RE.finditer(readme))
    if not count_matches:
        errors.append("README is missing the canonical executable migration count")
    elif len(count_matches) > 1:
        errors.append(
            "README must contain exactly one canonical executable migration count; "
            f"found {len(count_matches)}"
        )
    else:
        documented_count = int(count_matches[0].group("count"))
        if documented_count != executable_count:
            errors.append(
                f"README executable migration count is {documented_count}; "
                f"expected {executable_count}"
            )

    if names:
        expected_next = max(int(name[:3]) for name in names) + 1
        next_matches = list(NEXT_MIGRATION_RE.finditer(readme))
        if not next_matches:
            errors.append("README is missing the canonical next migration statement")
        elif len(next_matches) > 1:
            errors.append(
                "README must contain exactly one canonical next migration statement; "
                f"found {len(next_matches)}"
            )
        else:
            documented_next = int(next_matches[0].group("number"))
            if documented_next != expected_next:
                errors.append(
                    f"README next migration number is {documented_next:03d}; "
                    f"expected {expected_next:03d}"
                )

    for line_number, line in enumerate(readme.splitlines(), start=1):
        for match in PLACEHOLDER_RE.finditer(line):
            errors.append(
                f"README contains unresolved placeholder {match.group(0)!r} "
                f"at line {line_number}"
            )
```

Update `main()`:

```python
def main() -> int:
    errors = [*validate_migrations(), *validate_migration_documentation()]
    if errors:
        print("Migration validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Migration validation passed.")
    return 0
```

- [x] **Step 4: Run all synthetic checker tests and verify GREEN**

Run:

```bash
cd backend
uv run pytest tests/unit/test_check_migration_sequence.py \
  -k "not repository_migration_documentation_is_current" -q
```

Expected: all selected tests pass.

- [x] **Step 5: Commit Task 2**

```bash
git add backend/scripts/check_migration_sequence.py \
  backend/tests/unit/test_check_migration_sequence.py
git commit -m "build: guard migration README consistency"
```

### Task 3: Reconcile the Canonical Migration README

**Files:**
- Modify: `backend/tests/unit/test_check_migration_sequence.py`
- Modify: `backend/migrations/README.md`
- Modify: `docs/maintenance-audit.md`

**Interfaces:**
- Consumes: all validation behavior implemented in Tasks 1 and 2
- Produces: a repository-level contract proving the real migration inventory and README agree

- [x] **Step 1: Add the repository documentation contract test**

Add beside the existing repository sequence test:

```python
def test_repository_migration_documentation_is_current() -> None:
    errors = check_migration_sequence.validate_migration_documentation()

    assert errors == []
```

- [x] **Step 2: Run the repository contract and verify RED with the known drift**

Run:

```bash
cd backend
uv run pytest \
  tests/unit/test_check_migration_sequence.py::test_repository_migration_documentation_is_current \
  -q
```

Expected: fail with missing headings for `014`, `015`, `018`, `019`, and
`020_add_public_health_system_metrics.sql`, stale count `21`, stale next prefix
`022`, and the unresolved `TBD` line.

- [x] **Step 3: Correct top-level counts, ranges, and examples**

In `backend/migrations/README.md`:

- replace `Found 21 migration files:` with `Found 22 migration files:`;
- change naming and execution ranges ending at `021` to end at `022`;
- change the canonical next number from `022` to `023`;
- keep the existing `# Next: 023` example;
- change `touch backend/migrations/022_your_descriptive_name.sql` to `023`;
- change the SQL template comment from `022_your_descriptive_name.sql` to
  `023_your_descriptive_name.sql`.

- [x] **Step 4: Restore chronological migration history and complete `005`**

Move the existing `020_sync_active_source_definitions.sql`,
`021_add_alert_notification_state.sql`, and
`022_update_ontario_health_source_url.sql` entries out of the M1 section.
Keep `005_create_functions.sql` immediately after `004_seed_sources.sql` and
replace its placeholder with:

```markdown
**Functions Created:**
- `are_measurements_comparable(BIGINT, BIGINT)`
- `get_latest_measurement(TEXT)`
- `update_scraper_heartbeat(TEXT, scraper_status_enum, TEXT, INTEGER)`
- `get_stale_scrapers(INTEGER)`
- `update_updated_at()`

**Triggers Created:**
- `sources_updated_at`
- `hospitals_updated_at`
- `scraper_status_updated_at`
```

- [x] **Step 5: Add the five missing migration history entries**

Add concise, SQL-backed sections in chronological order:

- `014_relax_value_constraint.sql`: allow zero measurement values by changing
  the check to `value >= 0` for zero-percent occupancy and zero-minute values.
- `015_add_metric_family_to_aggregates.sql`: replace the aggregate uniqueness
  key with `(hospital_id, period_type, period_start, metric_family)`; cite
  ADR-0019.
- `018_create_public_health_hub_tables.sql`: create `public_data_sources`,
  `resource_locations`, `public_health_alerts`, and their indexes.
- `019_add_public_health_source_alert_state.sql`: create state-change-aware
  public-health source incident tracking and its partial active-incident index.
- `020_add_public_health_system_metrics.sql`: create the Ontario EMS/system
  context metric table and its source/series/year and geography indexes.

Place the preserved `020_sync_active_source_definitions.sql` entry after the
other `020` entry, followed by `021` and `022`. Do not edit either SQL file or
imply that duplicate `020` ordering can be changed.

- [x] **Step 6: Record the completed follow-up in the maintenance audit**

Amend the migration-health finding and migration-docs summary in
`docs/maintenance-audit.md` to state that the 2026-07-10 follow-up reconciled
all migration history headings and added CI-enforced count, next-prefix,
inventory, and placeholder validation. Preserve the audit's statement that no
schema or data operation occurred.

- [x] **Step 7: Run the repository contract, checker, and full checker module**

Run:

```bash
cd backend
uv run pytest tests/unit/test_check_migration_sequence.py -q
uv run python scripts/check_migration_sequence.py
```

Expected: all tests pass and the command prints
`Migration validation passed.`

- [x] **Step 8: Commit Task 3**

```bash
git add backend/migrations/README.md \
  backend/tests/unit/test_check_migration_sequence.py \
  docs/maintenance-audit.md
git commit -m "docs: reconcile migration history"
```

### Task 4: Full Verification, Plan Closure, and Delivery

**Files:**
- Modify: `docs/superpowers/plans/2026-07-10-migration-documentation-consistency.md`

**Interfaces:**
- Consumes: completed checker, tests, README, and maintenance note
- Produces: exact verification evidence and a ready unmerged pull request

- [x] **Step 1: Run backend quality and test gates**

Run:

```bash
cd backend
uv sync --locked --extra dev
uv run ruff format --check .
uv run ruff check .
uv run mypy src
uv run pytest -q
```

Expected: every command exits zero. Record actual pytest counts rather than
copying historical counts.

- [x] **Step 2: Run documentation and diff validation**

From the repository root, run:

```bash
bash scripts/check-docs.sh
git diff --check main...HEAD
git -c core.filemode=false status --short --branch
```

Expected: documentation checks and diff check exit zero; status contains only
the intended plan update before its final commit.

- [x] **Step 3: Update this plan with exact evidence**

Mark completed checkboxes, add a `## Verification Evidence` section containing
the exact commands, pass/fail outcomes, test counts, commit SHAs, and any
prerequisite-dependent skips. State explicitly that no database operation,
deployment, release, or secret access occurred.

- [x] **Step 4: Commit plan closure**

```bash
git add docs/superpowers/plans/2026-07-10-migration-documentation-consistency.md
git commit -m "docs: close migration consistency plan"
```

- [x] **Step 5: Request independent code review and address findings**

Review the complete range from `main` to `HEAD` for correctness, security,
test coverage, documentation accuracy, scope control, and preservation of the
legacy duplicate-`020` behavior. Re-run affected checks after any correction.

- [ ] **Step 6: Push and open a ready PR without merging**

```bash
git push -u origin codex/migration-docs-consistency
gh pr create \
  --base main \
  --head codex/migration-docs-consistency \
  --title "build: keep migration documentation consistent" \
  --body-file - <<'EOF'
## Summary
- reconcile the canonical migration history with every SQL and skipped migration
- extend the existing sequence checker with README inventory, count, next-prefix, and placeholder validation
- record the completed maintenance follow-up without changing schema or data

## Validation
- focused migration-sequence unit tests
- migration validation command
- backend lint, format, type, security, and pytest gates
- documentation quality checks

## Delivery boundary
This PR is ready for review but intentionally unmerged because its documentation paths trigger deployment on `main`.
EOF
```

The PR body must summarize the guard, README reconciliation, tests, and
non-deployment boundary. Do not merge because `docs/**` changes trigger the
documentation deployment workflow on `main`.

- [ ] **Step 7: Verify the exact pushed head and PR checks**

Use `gh pr view` and `gh pr checks` to confirm the PR head SHA equals local
`HEAD`, all required checks pass, and the PR remains open and unmerged.

## Verification Evidence

### Baseline

- Worktree: `/home/jer/repos/vps/waittimecanada/.worktrees/migration-docs-consistency`
- Branch base: `main` at `18dbcfef4e3c44695c2433b763d7f48e15deb124`
- Toolchain: uv 0.11.25 with CPython 3.14.6; the project requires Python 3.12+
- Locked setup: `uv sync --locked --extra dev` completed successfully
- Existing focused baseline: 5 tests passed in 0.36 seconds

### TDD Cycles

- Task 1 RED: 5 selected tests failed because
  `validate_migration_documentation` did not exist.
- Task 1 GREEN: 10 checker tests passed; committed as `9756cfcc`.
- Task 2 RED: 8 selected tests failed on missing count, next-prefix,
  placeholder, and CLI aggregation behavior.
- Task 2 GREEN: 18 checker tests passed; committed as `fe690ad8`.
- Task 3 RED: the repository contract failed with the expected 8 README
  defects: five missing headings, stale count, stale next prefix, and the
  unresolved `TBD` placeholder.
- Task 3 GREEN: 19 checker tests passed and
  `uv run python scripts/check_migration_sequence.py` printed
  `Migration validation passed.`; committed as `a62d6402`.
- Disk audit: 23 executable/skipped migration files have 23 exact README
  headings in matching lexicographic order.
- Review hardening RED: an invalid `*.sql` filename raised `ValueError` while
  the documentation validator calculated the next prefix.
- Review hardening GREEN: prefix calculation now uses names accepted by
  `MIGRATION_NAME_RE`; 20 focused tests passed on Python 3.12.13 and Ruff
  0.14.14 passed. The fix is committed as `c58a99b0`.
- Independent review found no critical or important issues. Its one minor
  finding was that invalid UTF-8 contradicted the documented unreadable-README
  behavior.
- Review finding RED: a one-byte invalid UTF-8 README raised
  `UnicodeDecodeError` instead of returning a validation error.
- Review finding GREEN: the read boundary now handles `UnicodeError`; all 21
  focused tests, Ruff format/check, and the migration CLI guard passed on
  Python 3.12.13. The fix is committed as `02404ba6`.

### Full Verification

- `uv run ruff format --check .`: passed; 130 files already formatted.
- `uv run ruff check .`: passed.
- `uv run mypy src`: passed with no issues in 49 source files.
- `uv run bandit -r src -ll`: passed with zero low, medium, or high issues.
- `uv run pytest -q`: 593 passed, 27 prerequisite-dependent tests skipped in
  27.99 seconds.
- `bash scripts/check-docs.sh`: all 11 documentation/roadmap guard groups
  passed.
- `git diff --check main...HEAD`: passed.
- Intended implementation files were clean after the implementation commits;
  only this delivery-plan update remained to commit.

The recurring `/home/jer/.profile` warning about a missing temporary Codex uv
environment file did not affect uv discovery, dependency sync, or command exit
status. After full verification, WSL process startup became intermittently
unavailable. The two final review-hardening commits therefore used the existing
isolated Windows Python 3.12 environment for focused tests and exact-file
Windows Git staging; hooks were bypassed for those commits only. Fresh CI on
the pushed final head is required before delivery is considered verified. No
database operation, deployment, release, secret access, or production write
occurred.
