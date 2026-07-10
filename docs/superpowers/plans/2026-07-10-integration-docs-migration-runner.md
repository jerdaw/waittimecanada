# Integration Guide Migration Runner Correction Plan

**Goal:** Replace the integration testing guide's nonexistent
`backend/scripts/migrate-structure.sh` reference with the maintained,
checksum-backed migration runner and prevent the stale instruction from
returning.

**Status:** In progress

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

- [ ] Add a test that reads the tracked integration guide and requires the
  current command `uv run python run_migrations.py`.
- [ ] Require the obsolete nonexistent path to be absent.
- [ ] Run the new test and record the expected failure.

```bash
cd backend
uv run pytest tests/unit/test_integration_testing_docs.py -q
```

## Task 2: Correct The Guide

- [ ] Replace the stale reference with a repository-relative instruction to
  run the maintained command from `backend/`.
- [ ] Link to `../run_migrations.py` so documentation link validation covers
  the target.
- [ ] State that the command uses the checksum ledger and refuses silently
  changed applied migrations.
- [ ] Update the guide's last-reviewed date without changing unrelated future
  improvement checkboxes.

## Task 3: Verify, Review, And Deliver

- [ ] Run the new contract test and migration-runner unit tests.
- [ ] Run Ruff format/check for the new test.
- [ ] Run the full backend suite.
- [ ] Run `bash scripts/check-docs.sh`.
- [ ] Run `git diff --check` and confirm only the planned surfaces changed.
- [ ] Request independent review and address critical or important findings.
- [ ] Commit the plan, RED/GREEN implementation, and completion record in
  reviewable steps.
- [ ] Push `codex/integration-docs-migration-runner` and open a ready PR.
- [ ] Do not merge because documentation paths trigger deployment on `main`.
- [ ] Verify GitHub checks on the exact final PR head.

## Completion Record

Record the RED/GREEN evidence, exact test counts, commit SHAs, review outcome,
PR URL, final SHA, and CI run IDs here. No database, migration, deployment,
release, secret, or production action is authorized by this batch.
