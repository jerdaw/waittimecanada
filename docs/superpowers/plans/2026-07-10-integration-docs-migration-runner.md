# Integration Guide Migration Runner Correction Plan

**Goal:** Replace the integration testing guide's nonexistent
`backend/scripts/migrate-structure.sh` reference with the maintained,
checksum-backed migration runner and prevent the stale instruction from
returning.

**Status:** Implementation verified; independent review and delivery pending

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
- [ ] Request independent review and address critical or important findings.
- [x] Commit the plan and RED/GREEN implementation in
  reviewable steps.
- [ ] Push `codex/integration-docs-migration-runner` and open a ready PR.
- [ ] Do not merge because documentation paths trigger deployment on `main`.
- [ ] Verify GitHub checks on the exact final PR head.

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

### Scope Boundary

Only the plan, integration guide, and one repository-contract test changed. No
migration SQL, migration runner, schema, data, production system, secret,
deployment, or release action occurred. Ownership of the obsolete root
`scripts/migrate-structure.sh` remains intentionally unchanged.

Independent review, PR URL, final SHA, and CI run IDs remain to be recorded.
