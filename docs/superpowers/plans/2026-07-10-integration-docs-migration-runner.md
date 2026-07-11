# Integration Guide Migration Runner Correction Plan

**Goal:** Replace the integration testing guide's nonexistent
`backend/scripts/migrate-structure.sh` reference with the maintained,
checksum-backed migration runner and prevent the stale instruction from
returning.

**Status:** Complete; PR #86 merged on 2026-07-10

**Base:** `main` at `18dbcfef4e3c44695c2433b763d7f48e15deb124`

## Evidence

- `backend/docs/integration-testing.md` currently directs contributors to
  `/backend/scripts/migrate-structure.sh` when database relations are missing.
- That path does not exist.
- The maintained runner is `backend/run_migrations.py`.
- `backend/tests/unit/test_run_migrations.py` covers checksum recording,
  matching-checksum skips, checksum mismatch rejection, and safe adoption of
  known duplicate objects.
- Baseline focused tests passed: 14 docs-checker tests plus 4 migration-runner
  tests.

## Scope

- Add: `backend/tests/unit/test_integration_testing_docs.py`
- Modify: `backend/docs/integration-testing.md`
- Modify: this plan

## Non-Goals

- Do not run or modify the historical root `scripts/migrate-structure.sh`; its
  ownership remains a separate maintenance decision.
- Do not modify migration SQL, the migration runner, schema, data, or
  production systems.
- Do not provision a database or change the prerequisite-dependent integration
  lane.
- Do not deploy, release, publish, or inspect secrets.

## Task 1: Add The Failing Repository Contract

- [x] Add a test that reads the tracked integration guide and requires the
  current command `uv run python run_migrations.py`.
- [x] Require the obsolete nonexistent path to be absent.
- [x] Run the new test and record the expected failure.

```bash
cd backend
uv run pytest tests/unit/test_integration_testing_docs.py -q
```

## Task 2: Correct The Guide

- [x] Replace the stale reference with a repository-relative instruction to
  run the maintained command from `backend/`.
- [x] Link to `../run_migrations.py` so documentation link validation covers
  the target.
- [x] State that the command uses the checksum ledger and refuses silently
  changed applied migrations.
- [x] Update the guide's last-reviewed date without changing unrelated future
  improvement checkboxes.

## Task 3: Verify, Review, And Deliver

- [x] Run the new contract test and migration-runner unit tests.
- [x] Run Ruff format/check for the new test.
- [x] Run the full backend suite.
- [x] Run `bash scripts/check-docs.sh`.
- [x] Run `git diff --check` and confirm only the planned surfaces changed.
- [x] Request independent review and address critical or important findings.
- [x] Commit the plan and RED/GREEN implementation in
  reviewable steps.
- [x] Push `codex/integration-docs-migration-runner` and open a ready PR.
- [x] Preserve the no-merge boundary until explicit authorization. The user
  later authorized the merge and automatic documentation deployment.
- [x] Verify GitHub checks on the exact pushed implementation head; verify the
  final plan-record head again before handoff.

## Completion Record

### TDD And Commits

- Baseline: 14 docs-checker tests and 4 migration-runner tests passed.
- RED: the new repository-contract test failed because the maintained command
  was absent from the guide.
- GREEN: the new contract plus all 4 migration-runner tests passed (5 total).
- Plan commit: `b3e7e026`.
- Implementation/test commit: `645fc7f4`.

### Full Local Verification

- `uv run ruff format --check .`: passed; 131 files already formatted.
- `uv run ruff check .`: passed.
- `uv run mypy src`: passed with no issues in 49 source files.
- `uv run bandit -r src -ll`: passed with zero issues at every severity.
- `uv run pytest -q`: 580 passed and 27 prerequisite-dependent skips in 25.81
  seconds.
- `bash scripts/check-docs.sh`: all 11 groups passed, including the corrected
  repository-relative link.
- `git diff --check main...HEAD`: passed.
- Pre-commit hooks passed, including Ruff, secret scanning, and authorship
  guardrails.
- Independent review approved the correction with no critical or important
  issues. Its only minor note was to close the plan state; the verification
  record commit `828073df` and this update resolve that housekeeping item.

### Scope Boundary

Only the plan, integration guide, and one repository-contract test changed. No
migration SQL, migration runner, schema, data, production system, secret,
deployment, or release action occurred. Ownership of the obsolete root
`scripts/migrate-structure.sh` remains intentionally unchanged.

### Delivery And GitHub Actions

- Pre-merge pull-request evidence: [#86](https://github.com/jerdaw/waittimecanada/pull/86)
  was open, ready, and mergeable while awaiting deployment authorization.
- Exact reviewed implementation head:
  `d77109dd127762f1afddb29362d4ae2fcaa8e990`.
- Scraper CI run `29120060224`: Ruff, migration guard, mypy, Bandit, and pytest
  passed; pytest reported 580 passed and 27 prerequisite-dependent skips in
  31.07 seconds.
- Docs CI run `29120063211`: `docs-quality` passed.
- The final plan-record commit will receive a fresh exact-head CI rerun. Its
  immutable run IDs belong in the PR delivery record so recording them does not
  create an endless plan-only CI cycle.

## Post-Merge Verification

After explicit user authorization, PR #86 was squash-merged as
`7c0473832e9cf27e838b0144b0c2a63dc2840235`. Post-merge Scraper CI run
`29135530184`, Deploy Docs run `29135530183`, and Docs CI run `29135530181`
all completed successfully.
