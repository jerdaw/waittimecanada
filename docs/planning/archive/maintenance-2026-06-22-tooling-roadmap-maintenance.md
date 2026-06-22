# Maintenance Log: Tooling and Roadmap Maintenance

**Date:** 2026-06-22
**Status:** Completed

## Summary

This maintenance pass kept repository setup, CI, tests, and planning records
aligned with the current Wait Time Canada operating model.

Completed work:

- Standardized backend setup and CI commands on the checked-in `uv.lock`
  workflow.
- Removed backend runtime assumptions that local env files are auto-loaded;
  backend scripts now rely on the process environment for `DATABASE_URL`.
- Added a migration sequence guard and unit coverage so future SQL migrations
  do not silently reuse numeric prefixes.
- Added a frontend test TypeScript project and CI step for test-file type
  checking.
- Kept generated API error responses from being cached where stale error data
  would be misleading.
- Archived completed 2026-04-23 repo-audit planning stubs from the active
  planning root.
- Removed ignored generated cache/build artifacts while preserving local
  dependencies, local env files, and private notes.

## Follow-Ups

- Complete the ADR-0027 trusted-runner heartbeat/status offload pilot outside
  this public repository before restoring scheduled secret-bearing workflows.
- Keep Playwright verification in GitHub Actions unless debugging a specific
  browser-flow regression locally.
- Continue using `docs/planning/roadmap.md` as the single public roadmap entry
  point.

## Local Validation

- `bash scripts/check-docs.sh` passed.
- `python scripts/check_migration_sequence.py` passed from the backend venv.
- `python -m pytest tests` passed: 543 passed, 27 skipped because database or
  local frontend prerequisites were absent.
- `ruff check src tests scripts` passed.
- `mypy src` passed.
- `npm run lint` passed.
- `tsc --noEmit` and `tsc --noEmit --project tsconfig.test.json` passed.
- `npm run test:unit` passed: 419 passed.
- `npm run build` passed.
