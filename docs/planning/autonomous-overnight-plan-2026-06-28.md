# Autonomous Overnight Work Plan - 2026-06-28

This is a planning artifact for a long unattended repository maintenance run.
No product, source, or test files were changed while preparing it.

## Chosen Artifact Path

Path: `docs/planning/autonomous-overnight-plan-2026-06-28.md`

Rationale: `docs/planning/` is the repository's documented planning control
plane, with `docs/planning/README.md` listing roadmap, manual tasks, active
planning docs, and archived maintenance logs. This file is public, reviewable,
non-secret planning documentation and is outside protected, generated, vendor,
ignored, and runtime directories.

## Inspection Summary

Instructions and context inspected:

- `AGENTS.md`; no `AGENTS.override.md` or nested AGENTS files were discovered.
- `CLAUDE.md` and `GEMINI.md` are covered by the docs check as relative
  symlinks to `AGENTS.md`.
- `README.md`, `CONTRIBUTING.md`, `SECURITY.md`.
- `docs/planning/README.md`, `docs/planning/index.md`,
  `docs/planning/roadmap-process.md`, `docs/planning/roadmap.md`,
  `docs/planning/manual-tasks.md`.
- `docs/development/setup.md`, `docs/development/testing-guidelines.md`,
  `docs/development/documentation-guidelines.md`.
- `docs/architecture/index.md`, `docs/architecture/data-flow.md`,
  `docs/architecture/api.md`, `docs/architecture/database.md`.
- `backend/pyproject.toml`, `frontend/package.json`,
  `frontend/vitest.config.ts`, `frontend/playwright.config.ts`, `Makefile`,
  `.pre-commit-config.yaml`, `.github/workflows/README.md`, and workflow
  command references.
- Main source/test directories under `backend/src`, `backend/tests`,
  `frontend/app`, `frontend/components`, `frontend/utils`, `frontend/tests`,
  and `scripts`.

Secret handling: secret files were not opened or printed. File discovery listed
some ignored or local environment file names, but no secret file contents were
inspected.

## 1. Repo Facts

### Stack

- Backend: Python 3.12+, `uv`-managed package in `backend/`, psycopg2,
  pytest, ruff, mypy, Bandit.
- Database: PostgreSQL with SQL migrations in `backend/migrations/`.
- Frontend: Next.js 15 App Router, TypeScript, React 18, Mapbox GL JS,
  Vitest/React Testing Library, Playwright for browser verification.
- Docs: MkDocs 1.x path, active docs quality gate via `scripts/check-docs.sh`.
- CI: GitHub Actions for docs, frontend, backend, operational manual-dispatch
  workflows, and selected advisory security scans.

### Major Components

- Backend scrapers: Ontario, Quebec, Alberta, British Columbia.
- Backend services: database persistence, aggregation, data quality, anomaly
  detection, heartbeat/source-health, methodology-change detection, public
  health resource ingestion.
- Frontend routes: map/list, `/analytics`, `/data-quality`, `/methods`,
  `/resources`, `/status`, `/faq`, API routes under `frontend/app/api`.
- Public health hub: Ontario-first facilities, AED fallback, alerts, AQHI,
  water advisories, and EMS system context with source-catalog metadata.

### Important Project Rules

- Do not directly inspect `.env`, `.env.local`, keys, certs, private key files,
  or any credential-bearing file.
- Do not list non-human tools as authors, co-authors, or contributors.
- Keep `CLAUDE.md` and `GEMINI.md` as relative symlinks to `AGENTS.md`.
- Preserve the strict metric ontology. Direct comparisons are valid only when
  metric family, start event, end event, and statistic type match.
- Do not claim to normalize or fix inconsistent health data; expose and audit
  methodology differences.
- Do not provide medical advice or hospital-choice recommendations.
- Preserve source provenance, public documentation boundaries, and
  non-triage/emergency disclaimers.
- Store payload hashes/snippets, not full source HTML.
- Avoid deployments, credential use, live production operations, migrations,
  broad rewrites, major dependency changes, or destructive git operations during
  unattended work.

### Discovered Commands

Install/setup:

- Backend documented setup: `cd backend && python -m pip install "uv==0.11.23" && uv sync --locked --extra dev`
- Frontend setup: `cd frontend && npm install`
- Playwright browser install when explicitly needed: `cd frontend && npx playwright install --with-deps chromium`

Backend validation:

- `cd backend && uv run ruff check src tests scripts`
- `cd backend && uv run ruff format --check src tests scripts`
- `cd backend && uv run mypy src`
- `cd backend && uv run python scripts/check_migration_sequence.py`
- `cd backend && uv run pytest tests`
- Local fallback used in this baseline because `uv` was not on `PATH`:
  `cd backend && .venv/bin/python -m pytest tests`

Frontend validation:

- `cd frontend && npm run lint`
- `cd frontend && npm run format:check`
- `cd frontend && npm run type-check`
- `cd frontend && npm run type-check:test`
- `cd frontend && npm run test:unit`
- `cd frontend && npm audit --audit-level=high`
- `cd frontend && npm run build` exists, but it may load local frontend env
  during framework build and should be reserved for final verification when
  needed.

Docs/security:

- `bash scripts/check-docs.sh`
- `cd backend && uv run bandit -r src -f json -o bandit-results.json --exit-zero`
- Local advisory fallback used in this baseline: `cd backend && .venv/bin/bandit -r src -q`
- Pre-commit includes `detect-private-key` and `detect-secrets`, but do not run
  any broad scan that reads ignored local secret files. Use filename-only checks
  first and only scan changed non-secret tracked files.

Database and E2E:

- `cd backend && uv run python run_migrations.py` requires `DATABASE_URL`.
- `bash scripts/run-disposable-db-checks.sh` exists for disposable DB checks,
  but it requires Docker and may run Playwright unless configured otherwise.
- `cd frontend && npm run test:e2e` is documented as CI-first/manual-dispatch,
  not part of the default local merge-readiness gate.

## 2. Baseline State

### Branch and Worktree

- Branch: `main`.
- WSL git status: `main...origin/main` with no tracked content changes shown.
- Windows/PowerShell git status: mode-only change shown for
  `scripts/run-disposable-db-checks.sh` (`100755 => 100644`).
- Treat the script mode discrepancy as pre-existing worktree state. Do not
  modify, revert, chmod, stage, or otherwise touch it during the unattended
  queue unless the user explicitly asks.

### Environment Assumptions

- Python: `3.12.3`.
- Backend virtualenv available at `backend/.venv`.
- Repo-local backend tools available in that virtualenv:
  ruff `0.14.14`, mypy `1.19.1`, pytest `9.0.2`.
- Node: `v24.17.0`.
- npm: `11.13.0`.
- Frontend `package.json` declares `node >=22 <23`, so the local Node version is
  outside the declared engine range even though the validation commands passed.
  Prefer Node 22 for future unattended runs if it is already available.
- `uv` is not on the WSL `PATH`; `uv --version` failed with
  `bash: uv: command not found`.
- One parallel WSL validation attempt failed with `Wsl/Service/E_UNEXPECTED`,
  then WSL recovered on a sequential command. Run heavy WSL validation commands
  sequentially during unattended work.
- No database credentials, production access, or live services were used.

### Commands Run Before Changes

| Command | Result |
| --- | --- |
| `rg --files` for AGENTS/override/docs/config/source/test discovery | Passed |
| `git branch --show-current`, `git status --short`, `git diff --summary` | Passed; see mode-only script discrepancy above |
| `bash scripts/check-docs.sh` | Passed |
| `cd backend && uv run ...` backend checks | Blocked: `uv` not on `PATH` |
| `cd backend && .venv/bin/ruff check src tests scripts` | Passed |
| `cd backend && .venv/bin/ruff format --check src tests scripts` | Passed |
| `cd backend && .venv/bin/python scripts/check_migration_sequence.py` | Passed |
| `cd backend && .venv/bin/mypy src` | Passed |
| `cd backend && .venv/bin/python -m pytest tests` | Passed: 553 passed, 27 skipped |
| `cd backend && .venv/bin/bandit -r src -q` | Passed |
| `cd frontend && npm run type-check` | Passed |
| `cd frontend && npm run type-check:test` | Passed |
| `cd frontend && npm run lint` | Passed |
| `cd frontend && npm run test:unit` | Passed: 77 files, 422 tests |
| `cd frontend && npm run format:check` | Passed |
| `cd frontend && npm audit --audit-level=high` | Passed: 0 vulnerabilities |

Notes from passing tests:

- Frontend unit tests emit expected error-path logs for mocked failures.
- `frontend/tests/components/TrendChart.test.tsx` currently emits React
  `act(...)` warnings during period-switch tests.
- `frontend/tests/api/geolocation.test.ts` prints a response payload to stdout.
- `frontend/utils/rate-limit.integration.test.ts` is a placeholder assertion.

## 3. Candidate Work Inventory

### AOW-01 - Align Active Docs With Manual-Dispatch Cadence

- Objective: Remove or update stale active-doc wording that says ingestion
  currently runs hourly via GitHub Actions when the roadmap says operational
  workflows are manual-dispatch while quota is constrained.
- Likely files/areas: `docs/architecture/data-flow.md`,
  `.github/workflows/README.md`, `README.md` if similar stale wording is found.
- Risk: Low; docs-only factual alignment.
- Acceptance criteria: active docs describe scheduled/manual cadence without
  contradicting `docs/planning/roadmap.md`; docs still preserve freshness
  caveats and public documentation boundary.
- Validation commands: `bash scripts/check-docs.sh`.
- Rollback plan: revert only the docs edited for this item.
- Blocker: Stop if deciding the future operational cadence would require a
  maintainer/product decision instead of documenting current state.

### AOW-02 - Align Public Status and Test Count Wording

- Objective: Audit public docs for stale fixed test counts or milestone status
  wording and align them with the current source-of-truth style.
- Likely files/areas: `README.md`, `backend/README.md`, `frontend/README.md`,
  `docs/planning/roadmap.md` only if status is demonstrably stale.
- Risk: Low; docs-only.
- Acceptance criteria: docs avoid conflicting fixed snapshots unless dated;
  no emergency, non-triage, comparability, or public-boundary wording is
  weakened.
- Validation commands: `bash scripts/check-docs.sh`.
- Rollback plan: revert only docs touched for this item.
- Blocker: Do not update milestone status unless the work was actually
  completed and verified.

### AOW-03 - Add Focused `/api/methodology` Route Tests

- Objective: Add unit tests for the existing methodology route response shape,
  source filtering, limit clamping, success cache headers, and error no-store
  headers.
- Likely files/areas: `frontend/app/api/methodology/route.test.ts`,
  `frontend/app/api/methodology/route.ts` only if a test exposes an obvious
  safe validation bug.
- Risk: Low to medium; prefer test-only, but route validation may need a small
  fix if non-numeric limits are currently unsafe.
- Acceptance criteria: tests cover all-source and `source_id` paths, mapped
  period/mean fields, max limit behavior, and database failure response.
- Validation commands: `cd frontend && npm run test:unit -- app/api/methodology/route.test.ts`
  and then `cd frontend && npm run test:unit`.
- Rollback plan: remove the new test file and any narrow route change from the
  item diff.
- Blocker: If invalid limit semantics are ambiguous, document the issue instead
  of changing public behavior.

### AOW-04 - Add Focused `/api/anomalies` Route Tests

- Objective: Cover anomaly route success, `source_id` filtering, validation
  errors, cache headers, and database failure response.
- Likely files/areas: `frontend/app/api/anomalies/route.test.ts`,
  `frontend/app/api/anomalies/route.ts` only if tests reveal a narrow bug.
- Risk: Low; mostly test-only.
- Acceptance criteria: tests assert anomaly mapping, `total_count`, 400
  validation behavior, public cache on success, and no-store on errors.
- Validation commands: `cd frontend && npm run test:unit -- app/api/anomalies/route.test.ts`
  and then `cd frontend && npm run test:unit`.
- Rollback plan: remove the new test file and any narrow route change from the
  item diff.
- Blocker: Stop if a fix would require changing anomaly API contract fields.

### AOW-05 - Replace Rate-Limit Placeholder Integration Test

- Objective: Replace the trivial placeholder in
  `frontend/utils/rate-limit.integration.test.ts` with meaningful coverage for
  request-header IP selection and handler-facing 429 behavior.
- Likely files/areas: `frontend/utils/rate-limit.integration.test.ts`,
  `frontend/utils/rate-limit.ts` only if testability requires a very small
  exported helper.
- Risk: Low.
- Acceptance criteria: no `expect(true).toBe(true)` placeholder remains; tests
  verify `x-forwarded-for`, `x-real-ip`, and `cf-connecting-ip` precedence or
  documented fallback behavior.
- Validation commands: `cd frontend && npm run test:unit -- utils/rate-limit.integration.test.ts utils/rate-limit.test.ts`.
- Rollback plan: restore the previous test file content for this item only.
- Blocker: Do not spin up a Next server or add dependencies for this.

### AOW-06 - Complete Rate-Limit TTL Reset Regression

- Objective: Turn the existing non-asserting TTL reset test into a deterministic
  assertion that a request is allowed again after the cache TTL expires.
- Likely files/areas: `frontend/utils/rate-limit.test.ts`,
  `frontend/utils/rate-limit.ts` if a test-only reset helper is needed.
- Risk: Low to medium; cache singleton test isolation must remain reliable.
- Acceptance criteria: test fails before the TTL behavior is working and passes
  after; tests remain deterministic without real waiting.
- Validation commands: `cd frontend && npm run test:unit -- utils/rate-limit.test.ts`.
- Rollback plan: revert the test/helper changes from this item only.
- Blocker: If the LRU library cannot be driven deterministically with fake
  timers without exposing internals, document the limitation and leave runtime
  code unchanged.

### AOW-07 - Tighten Geolocation API Tests

- Objective: Remove noisy `console.log` output and add assertions for no-store
  headers, forwarded-IP lookup URL, loopback fallback lookup, and upstream error
  fallback.
- Likely files/areas: `frontend/tests/api/geolocation.test.ts`,
  `frontend/app/api/geolocation/route.ts` only for a narrow no-store/header bug.
- Risk: Low.
- Acceptance criteria: geolocation tests assert current fallback behavior and no
  longer print payloads during normal test runs.
- Validation commands: `cd frontend && npm run test:unit -- tests/api/geolocation.test.ts`.
- Rollback plan: revert only the geolocation test/route changes.
- Blocker: Do not add live network calls; keep fetch mocked.

### AOW-08 - Reduce TrendChart Test Warnings

- Objective: Make `TrendChart` tests wait for state updates after period
  changes and handle the intentional error-path log without React `act(...)`
  warnings.
- Likely files/areas: `frontend/tests/components/TrendChart.test.tsx`,
  `frontend/components/TrendChart.tsx` only if a real runtime race is found.
- Risk: Low to medium; primarily test hygiene.
- Acceptance criteria: targeted test passes and period-switch assertions wait
  for the post-click fetch call; no intentional error-path console output leaks
  unexpectedly.
- Validation commands: `cd frontend && npm run test:unit -- tests/components/TrendChart.test.tsx`.
- Rollback plan: revert only TrendChart test/component changes from this item.
- Blocker: If the fix requires changing user-visible chart behavior, stop and
  document the finding.

### AOW-09 - Add TrendChart Stale-Response Regression Test

- Objective: Verify a slower response from an old period selection does not
  overwrite the most recent period's displayed data.
- Likely files/areas: `frontend/tests/components/TrendChart.test.tsx`,
  possibly `frontend/components/TrendChart.tsx` if the regression currently
  fails.
- Risk: Medium; may expose a real race requiring a small effect guard.
- Acceptance criteria: deterministic test covers out-of-order fetch resolution;
  any runtime fix is limited to ignoring stale responses.
- Validation commands: `cd frontend && npm run test:unit -- tests/components/TrendChart.test.tsx`.
- Rollback plan: revert the stale-response test and any associated component
  guard from this item.
- Blocker: Do not change chart labels, periods, API shape, or visual design.

### AOW-10 - Add SystemStatus Polling and Visibility Tests

- Objective: Cover the documented low-frequency health polling behavior:
  five-minute interval, polling only while visible, and refetch on visibility
  return.
- Likely files/areas: `frontend/tests/components/SystemStatus.test.tsx`.
- Risk: Low.
- Acceptance criteria: fake-timer tests verify polling cadence without real
  waiting; no runtime code change unless tests reveal a narrow bug.
- Validation commands: `cd frontend && npm run test:unit -- tests/components/SystemStatus.test.tsx`.
- Rollback plan: revert only SystemStatus test changes.
- Blocker: Do not change the five-minute polling interval without explicit
  product/ops approval.

### AOW-11 - Clarify SystemStatus Threshold Tests

- Objective: Make tests explicit that `down` status is based on `healthy=false`
  or age greater than twice the API-provided stale threshold.
- Likely files/areas: `frontend/tests/components/SystemStatus.test.tsx`.
- Risk: Low; test-only clarification.
- Acceptance criteria: tests cover default threshold and custom
  `stale_threshold_minutes`; misleading test names such as fixed `>120 min`
  are corrected if present.
- Validation commands: `cd frontend && npm run test:unit -- tests/components/SystemStatus.test.tsx`.
- Rollback plan: revert only SystemStatus test changes.
- Blocker: Do not change public status labels or threshold policy.

### AOW-12 - Add API Cache Header Regression Coverage

- Objective: Extend route tests so shared read-heavy success paths use public
  cache headers and validation/error paths use no-store where the code already
  intends that behavior.
- Likely files/areas: `frontend/app/api/anomalies/route.test.ts`,
  `frontend/app/api/methodology/route.test.ts`, selected existing route tests.
- Risk: Low.
- Acceptance criteria: assertions cover success and error cache-control headers
  for routes touched in the queue.
- Validation commands: `cd frontend && npm run test:unit`.
- Rollback plan: revert only cache-header assertions and any narrow header fix.
- Blocker: Do not change cache TTL values without an explicit route contract
  reason.

### AOW-13 - Add Public Health Resource UI Regression Tests

- Objective: Add focused tests for existing `/resources` UI caveats around
  source freshness, incomplete AED fallback coverage, and source-catalog
  provenance display.
- Likely files/areas: `frontend/tests/components/ResourceList.test.tsx`,
  `frontend/tests/pages/resources.test.tsx`, `frontend/components/ResourceList.tsx`
  only if a narrow existing-state rendering bug is found.
- Risk: Low to medium; avoid new copy decisions.
- Acceptance criteria: tests assert currently displayed caveats and source
  labels without changing resource scope.
- Validation commands: `cd frontend && npm run test:unit -- tests/components/ResourceList.test.tsx tests/pages/resources.test.tsx`.
- Rollback plan: revert only this item's tests/component fix.
- Blocker: Do not add new public-health sources, new upstream calls, or new
  product copy without approval.

### AOW-14 - Add Backend Runtime Config Tests

- Objective: Cover `get_heartbeat_stale_threshold_minutes` default and env
  override behavior without reading env files.
- Likely files/areas: `backend/tests/unit/test_runtime_config.py`,
  `backend/src/waittime/services/runtime_config.py` only if an obvious invalid
  value handling bug is found.
- Risk: Low.
- Acceptance criteria: tests use `monkeypatch` and do not inspect `.env` files;
  default is 120 minutes and override behavior is explicit.
- Validation commands: `cd backend && .venv/bin/python -m pytest tests/unit/test_runtime_config.py`.
- Rollback plan: remove the new test file and any narrow helper change.
- Blocker: Do not add local env auto-loading.

### AOW-15 - Add QualityDiff Edge-Case Tests

- Objective: Extend `QualityDiffService` coverage for stable deltas, null gap
  values, and zero baseline values.
- Likely files/areas: `backend/tests/unit/test_quality_diff.py`,
  `backend/src/waittime/services/quality_diff.py` only if a narrow bug is
  exposed.
- Risk: Low.
- Acceptance criteria: tests assert stable summary behavior and no crash when
  nullable aggregate fields are returned by the database.
- Validation commands: `cd backend && .venv/bin/python -m pytest tests/unit/test_quality_diff.py`.
- Rollback plan: revert only the test/service changes for this item.
- Blocker: Do not change data-quality scoring semantics without a documented
  contract reason.

### AOW-16 - Add Heartbeat Critical-Only Recovery Positive Test

- Objective: Add coverage that critical-only mode sends a recovery notification
  when a prior incident actually paged at `P0` or `P1`.
- Likely files/areas: `backend/tests/unit/test_check_heartbeat_cli.py`.
- Risk: Low; test-only.
- Acceptance criteria: existing suppression test remains, and new positive case
  verifies recovery is sent for prior critical notified tier.
- Validation commands: `cd backend && .venv/bin/python -m pytest tests/unit/test_check_heartbeat_cli.py`.
- Rollback plan: revert only heartbeat test changes.
- Blocker: Do not change notification tier policy in this item.

### AOW-17 - Add Heartbeat Dry-Run State-Mutation Test

- Objective: Verify `reconcile_incident_state(..., dry_run=True)` does not send
  alerts or mutate incident state for new unhealthy observations.
- Likely files/areas: `backend/tests/unit/test_check_heartbeat_cli.py`,
  `backend/src/waittime/cli/check_heartbeat.py` only if a narrow dry-run bug is
  exposed.
- Risk: Low.
- Acceptance criteria: test asserts no alert calls and no database
  open/resolve calls when dry-run is true.
- Validation commands: `cd backend && .venv/bin/python -m pytest tests/unit/test_check_heartbeat_cli.py`.
- Rollback plan: revert only heartbeat test/CLI changes for this item.
- Blocker: Do not change CLI exit-code semantics without approval.

### AOW-18 - Extend AlertService Notification Policy Tests

- Objective: Add tests for critical-only notification gating so P0/P1 are
  allowed and P2/P3 are suppressed according to current policy.
- Likely files/areas: `backend/tests/unit/services/test_alert_service.py`,
  `backend/src/waittime/services/alerts.py` only if a narrow bug is exposed.
- Risk: Low.
- Acceptance criteria: tests cover normal mode and critical-only mode without
  network calls or real alert credentials.
- Validation commands: `cd backend && .venv/bin/python -m pytest tests/unit/services/test_alert_service.py`.
- Rollback plan: revert only alert-service test/service changes.
- Blocker: Do not alter actual alert destinations, credentials, or operational
  notification defaults.

### AOW-19 - Add Docs Checker Regression for Active Cadence Drift

- Objective: Add a lightweight docs check or unit test that prevents active docs
  from claiming scheduled/hourly GitHub ingestion while the roadmap says manual
  dispatch is active.
- Likely files/areas: `scripts/check-docs.sh`,
  `backend/tests/unit/test_check_docs_script.py`, active docs if needed.
- Risk: Medium; changes docs tooling and may be too policy-specific.
- Acceptance criteria: checker catches the exact stale active-doc pattern while
  preserving historical/archive exclusions.
- Validation commands: `bash scripts/check-docs.sh` and
  `cd backend && .venv/bin/python -m pytest tests/unit/test_check_docs_script.py`.
- Rollback plan: revert checker/test changes and keep any pure docs fixes if
  they are independently correct.
- Blocker: Skip if the rule would be brittle or would require broad historical
  doc rewrites.

### AOW-20 - Document Local Toolchain Fallbacks

- Objective: Add a short troubleshooting note for the observed `uv` PATH
  blocker and local virtualenv fallback, without weakening the documented
  locked `uv` workflow.
- Likely files/areas: `docs/development/setup.md`,
  `docs/development/testing-guidelines.md`, maybe `CONTRIBUTING.md`.
- Risk: Low; docs-only.
- Acceptance criteria: docs still recommend locked `uv`; fallback wording is
  clearly local troubleshooting and does not instruct reading env files.
- Validation commands: `bash scripts/check-docs.sh`.
- Rollback plan: revert only docs touched for this item.
- Blocker: Do not add environment-specific paths, private hostnames, or personal
  machine details.

## 4. Safe Overnight Work Queue

All queued items are intended to be safe, reviewable, reversible, and testable
without credentials, production access, deployments, destructive operations,
database migrations, broad rewrites, major dependency changes, or ambiguous
product decisions.

### A. Core Queue

Run these first, in order:

1. AOW-04 - Add focused `/api/anomalies` route tests.
2. AOW-03 - Add focused `/api/methodology` route tests.
3. AOW-05 - Replace rate-limit placeholder integration test.
4. AOW-06 - Complete rate-limit TTL reset regression.
5. AOW-07 - Tighten geolocation API tests.
6. AOW-08 - Reduce TrendChart test warnings.
7. AOW-10 - Add SystemStatus polling and visibility tests.
8. AOW-16 - Add heartbeat critical-only recovery positive test.

Core queue validation cadence:

- After each frontend item: run the targeted `npm run test:unit -- ...` command
  listed in that item.
- After each backend item: run the targeted `.venv/bin/python -m pytest ...`
  command listed in that item.
- After the Core Queue: run `cd frontend && npm run test:unit` and
  `cd backend && .venv/bin/python -m pytest tests/unit/test_check_heartbeat_cli.py`.

### B. Extension Queue

Continue with these only after the Core Queue passes:

1. AOW-09 - Add TrendChart stale-response regression test.
2. AOW-11 - Clarify SystemStatus threshold tests.
3. AOW-14 - Add backend runtime config tests.
4. AOW-15 - Add QualityDiff edge-case tests.
5. AOW-17 - Add heartbeat dry-run state-mutation test.
6. AOW-18 - Extend AlertService notification policy tests.
7. AOW-12 - Add API cache header regression coverage.
8. AOW-13 - Add public health resource UI regression tests.
9. AOW-01 - Align active docs with manual-dispatch cadence.
10. AOW-02 - Align public status and test count wording.
11. AOW-20 - Document local toolchain fallbacks.
12. AOW-19 - Add docs checker regression for active cadence drift.

Extension queue validation cadence:

- Run targeted checks after each item.
- After extension frontend items: `cd frontend && npm run test:unit`.
- After extension backend items: `cd backend && .venv/bin/python -m pytest tests`.
- After docs/tooling items: `bash scripts/check-docs.sh`.

## 5. Do Not Do Overnight

- Do not inspect, print, copy, summarize, or transform `.env`, `.env.local`,
  key, certificate, private key, or credential files.
- Do not use production credentials, live production databases, deployment
  workflows, live smoke checks, or notification/alert endpoints.
- Do not run scrapers against live persistence or perform database cleanup.
- Do not create, edit, or run database migrations.
- Do not add provinces, new public-health sources, upstream data integrations,
  or product scope.
- Do not change medical/emergency/disclaimer copy in a way that weakens safety
  boundaries.
- Do not change ontology comparability semantics.
- Do not change cache TTLs, polling intervals, alert thresholds, or operational
  notification policy unless an item explicitly defines and validates the
  intended behavior.
- Do not run broad dependency upgrades, lockfile refreshes, or major dependency
  changes.
- Do not weaken, skip, delete, or lower tests/checks.
- Do not run Playwright/E2E unless a queued item specifically requires browser
  diagnosis and the reason is recorded.
- Do not run disposable database checks unless Docker availability and the
  existing script mode discrepancy are understood and the user approves touching
  that area.
- Do not modify `scripts/run-disposable-db-checks.sh` or its file mode during
  this queue.
- Do not touch ignored `private/` convenience copies or local backup folders.
- Do not stage, commit, push, create branches, or open PRs unless the user
  explicitly asks.
- Do not use broad git resets or checkout operations. Roll back item-specific
  changes by reversing only the files in that item diff.

## 6. Implementation Status

Status artifact path: `docs/planning/autonomous-overnight-plan-2026-06-28.md`

Current baseline before implementation:

- Branch: `main`.
- Existing unrelated worktree state: PowerShell-visible mode-only change on
  `scripts/run-disposable-db-checks.sh` (`100755 => 100644`). This is not part
  of the queue and must not be touched.
- New planning/status artifact: this file.
- Status updates must be recorded here before each queued item is edited.

| Item | Status | Files Changed | Validation | Risks / Rollback / Follow-up |
| --- | --- | --- | --- | --- |
| AOW-04 | Done | `frontend/app/api/anomalies/route.test.ts` | Initial WSL test attempt failed with `Wsl/Service/E_UNEXPECTED`; Windows `npm` was unavailable; after `wsl --shutdown`, `cd frontend && npm run test:unit -- app/api/anomalies/route.test.ts` passed (1 file, 4 tests). | Added test-only route coverage for success mapping, source filtering, validation no-store, and DB failure no-store. Roll back by removing the new test file. |
| AOW-03 | Done | `frontend/app/api/methodology/route.test.ts` | `cd frontend && npm run test:unit -- app/api/methodology/route.test.ts` passed (1 file, 3 tests). | Added test-only route coverage for mapping, source filtering, limit clamping, success cache headers, and DB failure no-store. Invalid nonnumeric limit behavior left unchanged as ambiguous. Roll back by removing the new test file. |
| AOW-05 | Done | `frontend/utils/rate-limit.integration.test.ts` | `cd frontend && npm run test:unit -- utils/rate-limit.integration.test.ts utils/rate-limit.test.ts` passed (2 files, 6 tests). | Replaced placeholder assertion with concrete proxy-header precedence and 429 response coverage. Expected rate-limit warning logs remain from blocked-request tests. Roll back by restoring the prior test file. |
| AOW-06 | Done | `frontend/utils/rate-limit.ts`, `frontend/utils/rate-limit.test.ts`, `frontend/utils/rate-limit.integration.test.ts` | First TTL assertion failed because `lru-cache` used a clock not advanced by the original fake timers; after making the one-minute window explicit with `Date.now()`, `cd frontend && npm run test:unit -- utils/rate-limit.test.ts utils/rate-limit.integration.test.ts` passed (2 files, 6 tests). | Preserved the one-minute limit window and bounded LRU storage; added test cache reset helper. Expected blocked-request warning logs remain. Roll back by reverting these rate-limit changes. |
| AOW-07 | Done | `frontend/tests/api/geolocation.test.ts` | `cd frontend && npm run test:unit -- tests/api/geolocation.test.ts` passed (1 file, 4 tests). | Removed stdout payload logging; added mocked no-store, forwarded IP, x-real-ip, loopback/default lookup, and upstream fallback coverage. Roll back by restoring the previous test file. |
| AOW-08 | Done | `frontend/tests/components/TrendChart.test.tsx` | `cd frontend && npm run test:unit -- tests/components/TrendChart.test.tsx` passed (1 file, 9 tests) without the prior observed error/act warning output. | Test-only synchronization cleanup; component behavior unchanged. Roll back by reverting the TrendChart test changes. |
| AOW-10 | Done | `frontend/tests/components/SystemStatus.test.tsx` | First attempt timed out under fake timers with `waitFor`; after switching to explicit `act` microtask flushing, `cd frontend && npm run test:unit -- tests/components/SystemStatus.test.tsx` passed (1 file, 8 tests). | Added low-frequency polling, hidden-tab suppression, and visibility-return refetch coverage. Component behavior unchanged. Roll back by reverting the SystemStatus test changes. |
| AOW-16 | Done | `backend/tests/unit/test_check_heartbeat_cli.py` | `cd backend && .venv/bin/python -m pytest tests/unit/test_check_heartbeat_cli.py` passed (12 tests). | Added test-only coverage for critical-only recovery after a prior P1 page. Roll back by reverting the heartbeat test change. |
| AOW-09 | Done | `frontend/tests/components/TrendChart.test.tsx` | First focused run timed out while WSL was unstable; direct `npx vitest run tests/components/TrendChart.test.tsx --reporter=verbose --testTimeout=10000 --hookTimeout=10000` passed (1 file, 10 tests); exact validation `cd frontend && npm run test:unit -- tests/components/TrendChart.test.tsx` passed (1 file, 10 tests). | Added test-only stale-response coverage with deferred period fetches; component behavior unchanged. Roll back by reverting the TrendChart test changes from this item. |
| AOW-11 | Done | `frontend/tests/components/SystemStatus.test.tsx` | `cd frontend && npm run test:unit -- tests/components/SystemStatus.test.tsx` passed (1 file, 9 tests). | Added test-only default/custom stale-threshold down-status coverage and corrected misleading fixed-threshold wording. Component behavior unchanged. Roll back by reverting the SystemStatus test changes from this item. |
| AOW-14 | Done | `backend/tests/unit/test_runtime_config.py` | `cd backend && .venv/bin/python -m pytest tests/unit/test_runtime_config.py` passed (2 tests). | Added monkeypatch-only coverage for the 120-minute default and process env override. No env files inspected or loaded. Roll back by removing the new test file. |
| AOW-15 | Done | `backend/tests/unit/test_quality_diff.py` | `cd backend && .venv/bin/python -m pytest tests/unit/test_quality_diff.py` passed (9 tests). | Added test-only stable-delta, null worst-gap, and zero-baseline coverage. Quality scoring semantics unchanged. Roll back by reverting the QualityDiff test changes from this item. |
| AOW-17 | Done | `backend/tests/unit/test_check_heartbeat_cli.py` | `cd backend && .venv/bin/python -m pytest tests/unit/test_check_heartbeat_cli.py` passed (13 tests). | Added test-only dry-run coverage asserting no alert dispatch and no open/resolve state mutation for a new unhealthy observation. CLI behavior unchanged. Roll back by reverting the heartbeat test change from this item. |
| AOW-18 | Done | `backend/tests/unit/services/test_alert_service.py` | `cd backend && .venv/bin/python -m pytest tests/unit/services/test_alert_service.py` passed (20 tests). | Added network-free notification policy matrix coverage: normal mode allows P0-P3; critical-only allows P0/P1 and suppresses P2/P3. Alert behavior unchanged. Roll back by reverting the alert-service test changes from this item. |
| AOW-12 | Done | `frontend/app/api/data-quality/route.test.ts` | Focused route validation `cd frontend && npm run test:unit -- app/api/data-quality/route.test.ts app/api/anomalies/route.test.ts app/api/methodology/route.test.ts` passed (3 files, 19 tests). Required validation `cd frontend && npm run test:unit` passed (79 files, 437 tests). | Added cache-header assertions for data-quality success, validation, and query-failure paths; anomalies/methodology cache coverage from AOW-03/AOW-04 remained passing. TTL values and route behavior unchanged. Expected existing stderr logs from mocked failure paths and rate-limit tests remain. Roll back by reverting data-quality test changes from this item. |
| AOW-13 | Done | `frontend/tests/components/ResourceList.test.tsx`, `frontend/tests/pages/resources.test.tsx` | `cd frontend && npm run test:unit -- tests/components/ResourceList.test.tsx tests/pages/resources.test.tsx` passed (2 files, 5 tests). | Added test-only assertions for current/hidden freshness labels, AED incompleteness caveats, source-catalog source names, attribution, official-source links, and facility source provenance after gated search. UI behavior and copy unchanged. Roll back by reverting the public resource test changes from this item. |
| AOW-01 | Done | `docs/architecture/data-flow.md` | `bash scripts/check-docs.sh` passed. | Replaced stale active-doc wording that ingestion currently runs hourly via GitHub Actions with the current scheduled/manual dispatch quota posture. Roll back by reverting the data-flow docs sentence from this item. |
| AOW-02 | Done | None | Audited `README.md`, `backend/README.md`, `frontend/README.md`, `docs/planning/roadmap.md`, `docs/development`, and `docs/architecture` for stale fixed test counts/status wording; no public-doc fixed test-count snapshot required editing. `bash scripts/check-docs.sh` passed. | README already points readers to the roadmap instead of a fixed test-count snapshot. No rollback needed. |
| AOW-20 | Done | `docs/development/setup.md` | `bash scripts/check-docs.sh` passed. | Added local troubleshooting note for missing `uv` on `PATH` that preserves the locked `uv sync --locked` workflow, limits `.venv/bin/...` use to temporary local fallback, and repeats the no-env-file-inspection boundary. Roll back by reverting the setup-docs bullet from this item. |
| AOW-19 | Done | `docs/API.md`, `scripts/check-docs.sh`, `backend/tests/unit/test_check_docs_script.py` | First docs-check attempt hit local `Wsl/Service/E_UNEXPECTED`; after WSL reset, redirected `bash scripts/check-docs.sh` passed and showed the new `[8/11]` cadence guard. `cd backend && .venv/bin/python -m pytest tests/unit/test_check_docs_script.py` passed (14 tests). | Added an active-doc cadence drift guard for stale hourly GitHub Actions ingestion claims, preserved archive maintenance-log exclusions, and updated API docs to describe the hourly expectation model without claiming GitHub Actions is the current scheduler. Roll back by reverting the checker/test/API docs changes from this item. |

Final inventory:

- Done: AOW-01, AOW-02, AOW-03, AOW-04, AOW-05, AOW-06, AOW-07,
  AOW-08, AOW-09, AOW-10, AOW-11, AOW-12, AOW-13, AOW-14, AOW-15,
  AOW-16, AOW-17, AOW-18, AOW-19, AOW-20.
- Partially Done: none.
- Blocked: none.
- Not Started: none.

Final validation summary:

- `bash scripts/check-docs.sh` passed with the new active-doc cadence guard.
- Backend final checks passed: `.venv/bin/ruff check src tests scripts`,
  `.venv/bin/ruff format --check src tests scripts`,
  `.venv/bin/python scripts/check_migration_sequence.py`, `.venv/bin/mypy src`,
  `.venv/bin/python -m pytest tests` (570 passed, 27 skipped), and
  `.venv/bin/bandit -r src -q`.
- Frontend final checks passed: `npm run format:check`, `npm run lint`,
  `npm run type-check`, `npm run type-check:test`, `npm run test:unit`
  (79 files, 437 tests), and `npm audit --audit-level=high` (0
  vulnerabilities).
- `git diff --check` passed before the final inventory update; filename-only
  secret guard returned no matches.
- Final diff review found no unexpected product behavior changes, no placeholder
  assertions, no weakened checks, and no accidental secret paths.
- Local WSL instability recurred during the run (`Wsl/Service/E_UNEXPECTED` and
  intermittent wrapper stalls); each affected validation command was rerun
  successfully after resetting WSL.
- Windows-side git status still shows the pre-existing mode-only change on
  `scripts/run-disposable-db-checks.sh` (`100755 => 100644`). It was not
  modified, staged, or included in queue work.

## 7. Final Completion Checklist

Run final commands sequentially because WSL showed instability during parallel
heavy validation:

```bash
bash scripts/check-docs.sh
```

```bash
cd backend
.venv/bin/ruff check src tests scripts
.venv/bin/ruff format --check src tests scripts
.venv/bin/python scripts/check_migration_sequence.py
.venv/bin/mypy src
.venv/bin/python -m pytest tests
.venv/bin/bandit -r src -q
cd ..
```

```bash
cd frontend
npm run format:check
npm run lint
npm run type-check
npm run type-check:test
npm run test:unit
npm audit --audit-level=high
cd ..
```

Final review requirements:

- Run `git status --short` and identify every changed/untracked file.
- Confirm the pre-existing mode-only status on
  `scripts/run-disposable-db-checks.sh` was not modified as part of the queue.
- Run `git diff --check`.
- Run filename-only secret guard:
  `git status --short | rg '(^|/)(\.env|\.env\.local|key\.txt|.*\.(pem|key))$'`
  and stop immediately if any secret-like path appears.
- Review `git diff --stat` and `git diff --name-only` for unexpected breadth.
- Review each changed file diff for dead code, placeholder assertions,
  accidental console output, weakened checks, or behavior changes outside the
  item scope.
- For frontend test-hygiene items, rerun the targeted tests and check that new
  test output does not introduce avoidable warnings.
- For docs items, verify wording remains public, reproducible, and free of
  environment-specific operations details.
- Summarize completed item IDs, skipped item IDs with blockers, commands run,
  pass/fail results, and residual risks.
