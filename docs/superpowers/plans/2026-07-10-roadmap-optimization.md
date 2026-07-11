# Roadmap Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace duplicated and ambiguous planning lists with a concise public snapshot, permanent guardrails, and one dependency-aware finite execution queue.

**Architecture:** `docs/planning/roadmap.md` remains the public source of truth. A pure Python checker enforces its guardrail and execution-table structure, while `manual-tasks.md` holds typed human/operator triggers and README links to the canonical queue instead of duplicating it.

**Tech Stack:** Markdown, Python 3.12+, regular expressions, pathlib, pytest, Ruff, MkDocs, repository documentation checks.

## Global Constraints

- Preserve clinical-safety, non-triage, ontology-comparability, provenance, retention, cost-control, and public/private documentation boundaries.
- Build on PR #89 commit `3c2f363c12965bd2b5cb28d2c14610176483f904`; do not reintroduce its completed repository-side offload-hardening item.
- Do not select or provision a trusted runner, inspect secrets or private operations notes, run live production commands, change schedules, remove fallbacks, deploy, or release.
- Keep runner selection, credentials, live validation, schedule cutover, and the 24-hour soak explicitly open.
- Keep `docs/planning/roadmap.md` as the single public source of truth and `docs/planning/manual-tasks.md` as its typed manual companion.
- Do not invent owner names, delivery dates, data sources, product decisions, or Ontario ontology decisions.
- Keep README's roadmap baseline date aligned with the roadmap date.
- Do not merge the stacked roadmap PR before PR #89 is merged and the roadmap branch is updated onto the resulting `main`.

---

## File Structure

- `backend/scripts/verify_roadmap_consistency.py`: pure structural validation for continuous guardrails and the finite execution queue; CLI registration for the new check.
- `backend/tests/unit/test_verify_roadmap_consistency.py`: synthetic RED/GREEN cases plus a repository-level contract for the optimized roadmap.
- `docs/planning/roadmap.md`: concise public snapshot, completed foundations, continuous guardrails, and canonical execution queue.
- `docs/planning/manual-tasks.md`: decision, external-operations, recurring-review, conditional-follow-up, and completed-prerequisite groups.
- `docs/planning/roadmap-process.md`: lifecycle and formatting rules matching the optimized structure.
- `README.md`: concise future-outcome summary linking to the canonical execution queue without duplicate checkboxes.
- `docs/superpowers/specs/2026-07-10-roadmap-optimization-design.md`: approved design and README-alignment clarification.
- `docs/superpowers/plans/2026-07-10-roadmap-optimization.md`: execution checklist and final evidence.

---

### Task 1: Add The Execution-Structure Validator

**Files:**
- Modify: `backend/tests/unit/test_verify_roadmap_consistency.py`
- Modify: `backend/scripts/verify_roadmap_consistency.py`

**Interfaces:**
- Consumes: a UTF-8 Markdown file at `roadmap_path: Path`.
- Produces: `check_execution_roadmap_structure(roadmap_path: Path) -> tuple[bool, str]`.
- Produces constants `EXECUTION_COLUMNS`, `ALLOWED_PRIORITIES`, and `ALLOWED_STATES` for the exact public roadmap contract.

- [x] **Step 1: Add the failing validator unit tests**

Add `check_execution_roadmap_structure` to the existing import list and append these tests:

```python
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
```

- [x] **Step 2: Run the new tests and verify RED**

Run:

```bash
cd backend
uv run --locked --extra dev pytest tests/unit/test_verify_roadmap_consistency.py -q
```

Expected: collection fails because `check_execution_roadmap_structure` does not yet exist.

- [x] **Step 3: Implement the pure structural checker**

Add this contract alongside the existing `check_roadmap_items_formatting`.
Keep the legacy function and its CLI registration unchanged during Task 1 so
the unconverted repository roadmap remains valid until Task 2:

```python
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
            line.strip()
            for line in queue_sections[0].splitlines()
            if line.strip().startswith("|")
        ]
        if len(table_lines) < 3:
            issues.append("Execution Queue must contain a header, separator, and row")
        elif tuple(_table_cells(table_lines[0])) != EXECUTION_COLUMNS:
            issues.append(
                "Execution Queue columns must be: " + ", ".join(EXECUTION_COLUMNS)
            )
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
                    issues.append(f"Execution Queue row {row_number} has invalid priority '{priority}'")
                if state not in ALLOWED_STATES:
                    issues.append(f"Execution Queue row {row_number} has invalid state '{state}'")
                if not outcome:
                    issues.append(f"Execution Queue row {row_number} requires a non-empty outcome")
                if not gate:
                    issues.append(f"Execution Queue row {row_number} requires a non-empty gate")
                if not done_when:
                    issues.append(f"Execution Queue row {row_number} requires a non-empty done-when value")

    if issues:
        return False, "Roadmap execution structure issues:\n  " + "\n  ".join(issues)
    return True, "✓ Roadmap execution structure is complete"
```

- [x] **Step 4: Run focused tests and verify GREEN**

Run the focused command from Step 2.

Expected: 22 tests pass: the existing 15 plus the 7 new structural tests.

- [x] **Step 5: Run Ruff for changed Python files**

```bash
cd backend
uv run --locked --extra dev ruff format scripts/verify_roadmap_consistency.py tests/unit/test_verify_roadmap_consistency.py
uv run --locked --extra dev ruff check scripts/verify_roadmap_consistency.py tests/unit/test_verify_roadmap_consistency.py
```

Expected: both commands pass.

- [x] **Step 6: Commit the validator**

```bash
git add backend/scripts/verify_roadmap_consistency.py \
  backend/tests/unit/test_verify_roadmap_consistency.py
git commit -m "test: enforce actionable roadmap structure"
```

Expected: commit succeeds with no non-human attribution trailer.

---

### Task 2: Replace Duplicated Planning Surfaces

**Files:**
- Modify: `backend/scripts/verify_roadmap_consistency.py`
- Modify: `backend/tests/unit/test_verify_roadmap_consistency.py`
- Modify: `docs/planning/roadmap.md`
- Modify: `docs/planning/manual-tasks.md`
- Modify: `docs/planning/roadmap-process.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: the checker and allowed values introduced in Task 1.
- Produces: a canonical `## Execution Queue` with columns `Priority`, `Outcome`, `State`, `Gate`, and `Done when`.
- Produces: typed manual sections `Decision Required`, `External Operations`, `Recurring Reviews`, `Conditional Follow-Ups`, and `Completed Repository Prerequisites`.

- [x] **Step 1: Add the repository-level failing contract and CLI registration**

Append this test:

```python
def test_repository_roadmap_uses_optimized_execution_structure() -> None:
    repo_root = Path(__file__).resolve().parents[3]

    success, message = check_execution_roadmap_structure(
        repo_root / "docs/planning/roadmap.md"
    )

    assert success is True, message
```

Replace the final CLI check tuple with:

```python
("Roadmap Execution Structure", check_execution_roadmap_structure, (roadmap_path,)),
```

Then remove the now-unused `check_roadmap_items_formatting` function. The
roadmap conversion and CLI switch belong in the same task so no committed
intermediate state applies the new contract to the legacy document.

Expected: the focused tests fail because the current roadmap still contains legacy active sections and has no new guardrail/queue sections.

- [x] **Step 2: Replace the current status and duplicate priority sections**

In `docs/planning/roadmap.md`:

1. Replace the current status chronology with this exact snapshot:

```markdown
## Current Snapshot (Updated 2026-07-10)

**Progress:** Milestone 33 is complete. Wait Time Canada is in a stewardship
and selective-expansion phase.

The observatory covers Ontario, Quebec, Alberta, and British Columbia while
preserving each source's methodology and exposing invalid direct comparisons.
Historical occupancy aggregation and the Ontario-first public-health resources
module are live. Repository-side reliability, documentation, migration, and
offloaded-operations contracts are implemented.

The immediate delivery focus is the trusted source-freshness offload pilot.
Runner provisioning, protected credential configuration, live command
validation, schedule cutover, and the 24-hour proof window remain external
operator work. GitHub manual dispatch remains the fallback until that evidence
is accepted.
```

2. Promote the existing completed-foundations list to `## Completed Foundations`, retaining PR #89's offloaded-operations acceptance-control bullet.
3. Remove `## Public Documentation Boundary`, `## Active Priorities`, `## Active Roadmap`, `## Roadmap Operating Model`, and `## Future Work` as separate duplicate sections.
4. Insert these canonical sections before `## Completed Milestones`:

```markdown
## Continuous Guardrails

- Keep emergency, non-triage, and non-medical-advice boundaries prominent.
- Compare measurements directly only when metric family, start event, end event,
  and statistic type match.
- Keep source freshness, data-quality state, and official-source attribution
  visible without exposing private monitoring configuration.
- Retain raw measurements for 30 days while preserving permanent aggregates.
- Keep public documentation free of credentials, private hostnames, private
  paths, monitoring routes, and environment-specific deployment details.
- Preserve low-frequency health polling, bounded cache policies, and explicit
  production cost controls.
- Keep GitHub manual dispatch available until an accepted offload proof window
  and rollback review support schedule changes.

## Execution Queue

| Priority | Outcome | State | Gate | Done when |
| --- | --- | --- | --- | --- |
| P1 | Complete the trusted source-freshness offload pilot | In validation | Merge the public contract and private companion, provision a trusted runner, and configure protected credentials outside this repository | Manual scraper, watchdog, aggregate, and smoke checks pass; timers complete a clean 24-hour soak with fallback retained |
| P1 | Restore remaining scheduled workflow cadence | External prerequisite | Accept the offload proof window and value-free rollback evidence | Reviewed schedules run at the intended cadence and GitHub `workflow_dispatch` remains available |
| P1 | Resolve Ontario methodology representation | Decision required | Decide the composite start, qualifying-provider endpoint, historical migration or versioning, source metadata, divergence behavior, and frontend labels together | Runtime tags, historical treatment, public methodology text, and regression tests implement one reviewed decision |
| P1 | Extend public methodology artifacts | Decision required | Complete Ontario revalidation or verify another official methodology change | Case studies and export examples carry current definitions, provenance, limitations, and comparison warnings |
| P1 | Select public-health resource expansion | Decision required | Identify an official, reusable, product-relevant source with documented caveats | The source catalog, ingest path, freshness behavior, public limitations, and tests are merged |
| P2 | Evaluate additional provinces | External prerequisite | Find a stable official public source with sufficient methodology documentation | The source is represented with ontology, provenance, clinical-safety boundaries, monitoring, and tests |
| P2 | Explore smarter scheduling | Later | Establish safe low-activity bounds from sustained freshness evidence | Upstream requests decrease without breaching public freshness expectations and manual fallback remains available |
| P2 | Reassess external CI or full Forgejo migration | Later | The hybrid offload pilot fails documented reliability or cost objectives | A reviewed ADR selects a bounded migration or explicitly retains the hybrid model |
```

5. Replace `## Roadmap Operating Model` with a one-line link under the queue:

```markdown
Roadmap lifecycle and formatting rules are defined in
[`roadmap-process.md`](roadmap-process.md); operator and recurring triggers are
tracked in [`manual-tasks.md`](manual-tasks.md).
```

- [x] **Step 3: Update status parsing for the new snapshot heading**

Change `_extract_roadmap_status` to match:

```python
r"## Current Snapshot \(Updated ([^)]+)\)\s*\n\s*\*\*Progress:\*\* (.+?)(?=\n\n|\*\*|\Z)"
```

Update synthetic test roadmaps from `## Current Status` to
`## Current Snapshot`, rename affected test names and messages from “status” to
“snapshot” where they describe the roadmap heading, and keep README's own
`Current Status` heading unchanged.

- [x] **Step 4: Type the manual task ledger**

Rewrite `docs/planning/manual-tasks.md` using these headings and retain the
existing safety review checklist:

```markdown
## Decision Required

- [ ] Resolve the Ontario methodology representation before changing runtime
  tags or treating paused Ontario research artifacts as current. Use the exact
  decision scope in the roadmap execution queue.

## External Operations

- [ ] Complete the trusted source-freshness offload pilot using
  `docs/operations/heartbeat-offload-pilot.md`; keep GitHub manual dispatch as
  fallback.
- [ ] After the first complete 24-hour proof window, compare workflow history,
  `/api/status`, and `/api/data-quality` with the accepted cadence.
- [ ] Restore remaining scheduled workflows only after the proof window and
  rollback evidence are accepted.

## Recurring Reviews

- [ ] Quarterly: review public source links and update stale provenance URLs.
- [ ] After each completed milestone: align README, roadmap, and planning
  indexes.

## Conditional Follow-Ups

- [ ] Before a major release: re-run the public documentation boundary review.
- [ ] After a provincial reporting change: re-run methodology documentation
  review and update affected artifacts.
- [ ] After a major frontend change: capture updated demo screenshots.
- [ ] After source methodology or displayed examples change: refresh affected
  public case studies.
- [ ] After a new data flow or third-party service is introduced: review
  `/privacy` and `/terms`.

## Completed Repository Prerequisites

- [x] Runner isolation, secret handling, log retention, failure-summary, and
  rollback requirements are documented in the public offload contract, with
  the concrete value-free operator procedure retained in the private/shared
  operations source of truth.
```

- [x] **Step 5: Align the roadmap process document**

Replace `docs/planning/roadmap-process.md` with:

```markdown
# Roadmap Process

`docs/planning/roadmap.md` is the single public source of truth for project
status and strategic direction. `docs/planning/manual-tasks.md` is its companion
for human decisions, external operations, recurring reviews, and conditional
follow-ups.

## Canonical Structure

Keep roadmap sections in this order:

1. `Current Snapshot`
2. `Completed Foundations`
3. `Continuous Guardrails`
4. `Execution Queue`
5. `Completed Milestones`
6. architecture, ADR, schema, and historical implementation references

Do not add a second active-priority list or repeat the execution queue in
README. Historical session chronology belongs in maintenance records, closed
plans, and Git history.

## Current Snapshot

Update the snapshot only when public project state changes. Keep it concise,
mention the latest completed milestone, and align its `YYYY-MM-DD` date with
README's roadmap baseline and Current Status dates. Do not append session logs.

## Continuous Guardrails

Guardrails are permanent invariants, not finite tasks. Use ordinary bullets,
never task-list checkboxes. Preserve clinical safety, ontology comparability,
source provenance, freshness visibility, retention, cost controls, and the
public/private documentation boundary.

## Execution Queue

Use one Markdown table with columns in this exact order:

| Priority | Outcome | State | Gate | Done when |
| --- | --- | --- | --- | --- |

Allowed priorities are `P0`, `P1`, and `P2`. Every row must name a finite
outcome, its current state, the dependency or decision gate, and an observable
completion condition.

Allowed states:

- `Ready`: repository work can start without a missing decision or external prerequisite.
- `Decision required`: an owner-approved product, methodology, legal, or data decision is missing.
- `External prerequisite`: credentials, infrastructure, an official source, or another external state is missing.
- `In validation`: implementation exists and an observation or acceptance window is active.
- `Later`: the trigger for reconsideration has not occurred.

Do not invent owner names or dates when work is gated. Use state and gate to
make the dependency explicit.

## Manual Task Ledger

Group manual tasks under `Decision Required`, `External Operations`, `Recurring
Reviews`, `Conditional Follow-Ups`, or `Completed Repository Prerequisites`.
State the trigger for recurring and conditional work. Link to the roadmap
outcome or public contract rather than restating a competing backlog.

## Lifecycle

- When a finite outcome is completed, move its durable result to Completed
  Foundations, Completed Milestones, or the appropriate historical record.
- Keep operator work open until its observable acceptance evidence exists.
- Archive closed implementation plans that are no longer living records.
- Update README status dates only when the roadmap's public baseline changes.
- Run `backend/scripts/verify_roadmap_consistency.py` and
  `scripts/check-docs.sh` for every roadmap change.

## Public Alignment

Every roadmap update must preserve non-medical-advice and non-triage boundaries,
the four-field direct-comparison rule, official-source attribution, methodology
limitations, and separation of public reproducible guidance from private
operations detail.
```

- [x] **Step 6: Remove README's duplicate backlog**

Replace README's `## 💡 Future Roadmap` checkbox lists with:

```markdown
## 💡 Future Roadmap

Wait Time Canada is in a stewardship and selective-expansion phase. Finite
outcomes currently cover source-freshness offload validation, Ontario
methodology resolution, carefully selected research/resource expansion,
evidence-bounded scheduling, and conditional province or CI expansion.

The canonical dependency, state, and completion criteria for this work live in
the [`docs/planning/roadmap.md`](docs/planning/roadmap.md) execution queue.
```

- [x] **Step 7: Run focused RED/GREEN verification**

```bash
cd backend
uv run --locked --extra dev pytest tests/unit/test_verify_roadmap_consistency.py -q
uv run --locked --extra dev python scripts/verify_roadmap_consistency.py
```

Expected: 23 focused tests pass and the CLI prints `All roadmap consistency checks passed!`.

- [x] **Step 8: Run documentation verification**

```bash
cd ..
bash scripts/check-docs.sh
make docs-build
git diff --check
```

Expected: all 11 documentation gates, the locked strict MkDocs build, and the whitespace check pass.

- [x] **Step 9: Commit the optimized planning surfaces**

```bash
git add README.md \
  backend/scripts/verify_roadmap_consistency.py \
  backend/tests/unit/test_verify_roadmap_consistency.py \
  docs/planning/roadmap.md \
  docs/planning/manual-tasks.md \
  docs/planning/roadmap-process.md
git commit -m "docs: optimize roadmap execution model"
```

Expected: pre-commit checks pass and the commit contains no secret or non-human authorship attribution.

---

### Task 3: Full Verification, Review, And Stacked Delivery

**Status:** Implementation verified; awaiting broad review.

**Files:**
- Modify: `docs/superpowers/plans/2026-07-10-roadmap-optimization.md`

**Interfaces:**
- Consumes: the complete Task 1 and Task 2 diff stacked on PR #89.
- Produces: exact validation evidence, independent review results, and a ready stacked pull request targeting `docs/waittime-offload-operations-hardening`.

- [x] **Step 1: Run the full backend quality suite**

```bash
cd backend
uv run --locked --extra dev ruff format --check .
uv run --locked --extra dev ruff check .
uv run --locked --extra dev mypy src
uv run --locked --extra dev bandit -r src -ll
uv run --locked --extra dev pytest -q
```

Expected: formatting, lint, type checking, security scanning, and all prerequisite-independent tests pass; record the exact pass and skip counts.

- [x] **Step 2: Re-run repository documentation gates**

```bash
cd ..
bash scripts/check-docs.sh
make docs-build
git diff --check 3c2f363c12965bd2b5cb28d2c14610176483f904...HEAD
git status --short --branch
```

Expected: docs checks and strict build pass, the diff has no whitespace errors,
and only this plan's final evidence update remains uncommitted.

**Pre-review verification evidence (2026-07-10):**

- Full `ruff format --check .` reproduced the unchanged stacked-base exception:
  `tests/unit/test_docs_toolchain.py` would be reformatted and 132 files were
  already formatted on both `HEAD` and
  `3c2f363c12965bd2b5cb28d2c14610176483f904`. The scoped check for the two
  changed Python files passed with `2 files already formatted`; no unrelated
  file was rewritten.
- Full `ruff check .` likewise reproduced the same unchanged base-file `I001`
  import-order issue on both `HEAD` and the stacked base. The scoped check for
  `scripts/verify_roadmap_consistency.py` and
  `tests/unit/test_verify_roadmap_consistency.py` passed with
  `All checks passed!`.
- `mypy src` passed with no issues in 49 source files. `bandit -r src -ll`
  reported no issues across 11,435 lines. `pytest -q` collected 650 tests and
  finished with **623 passed, 27 skipped in 32.11s**.
- `bash scripts/check-docs.sh` passed all 11 documentation gates, including
  roadmap consistency. The locked strict MkDocs build completed in 2.20s.
  `git diff --check
  3c2f363c12965bd2b5cb28d2c14610176483f904...HEAD` produced no output, and
  the pre-update status was clean on `codex/roadmap-optimization`.
- Independent review, plan closure, push, PR creation, exact-head remote
  verification, rebase, merge, and post-merge verification remain pending.

- [ ] **Step 3: Request independent review**

Review the complete base-to-head diff for:

- loss of PR #89's completed hardening state;
- private operational detail leakage;
- missing or misleading execution dependencies;
- continuous safeguards presented as finite tasks;
- duplicated backlog between roadmap, README, and manual tasks;
- validator false positives/false negatives;
- clinical-safety or ontology weakening; and
- test, documentation, and scope completeness.

Fix every Critical or Important finding, rerun affected checks, and record the
review result in this plan.

- [ ] **Step 4: Close the plan record**

Mark all completed implementation and verification boxes, set status to
`Ready for stacked delivery`, and add exact RED/GREEN, full-suite, docs-build,
review, and changed-surface evidence. Keep merge/post-merge actions unchecked
until they actually occur.

- [ ] **Step 5: Commit the plan record**

```bash
git add docs/superpowers/plans/2026-07-10-roadmap-optimization.md
git commit -m "docs: record roadmap optimization verification"
```

- [ ] **Step 6: Push and open the stacked pull request**

```bash
git push -u origin codex/roadmap-optimization
gh pr create \
  --repo jerdaw/waittimecanada \
  --base docs/waittime-offload-operations-hardening \
  --head codex/roadmap-optimization \
  --title "docs: optimize roadmap execution model" \
  --body "Summarize the concise snapshot, guardrails, execution queue, typed manual ledger, README deduplication, structural tests, verification, and explicit dependency on PR #89."
```

Expected: a ready, mergeable stacked PR is created against PR #89's branch.

- [ ] **Step 7: Verify the exact stacked head**

Use `gh pr view` and `gh pr checks` to confirm the remote head equals local
`HEAD` and every required check passes. Do not merge while PR #89 remains open.

- [ ] **Step 8: Rebase after PR #89 merges**

After PR #89 is merged, update this branch onto the resulting `origin/main`
without force-pushing unless the user explicitly authorizes it. If a history
rewrite would be required, use a merge commit or ask for authorization. Rerun
Tasks 2 Step 7, Task 2 Step 8, and Task 3 Steps 1-3 on the final base.

- [ ] **Step 9: Merge and verify only with authorization**

After the final exact-head checks pass and explicit merge/publication
authorization is available, merge without deleting any unmerged branch. Verify
all triggered post-merge checks and documentation publication before marking
the plan fully complete.
