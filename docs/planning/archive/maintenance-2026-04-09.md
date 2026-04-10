# Maintenance Log — 2026-04-09

## Scope

Frontend regression-suite stabilization follow-up, docs/roadmap reconciliation,
artifact cleanup, attribution/agent-file verification, and GitHub PR/branch
maintenance.

## Completed

- Removed local junk artifacts:
  - `backend/.pytest_cache`
  - `frontend/.next`
  - `frontend/playwright-report`
  - `frontend/test-results`
- Verified the repo still enforces human-only attribution:
  - `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`
  - `git log --format='%an <%ae>' | sort -u` returned only Jeremy Dawson
- Closed stale Dependabot PR `#49` and deleted its remote branch because the
  roadmap still keeps frontend dependency work on a deliberate batch-refresh
  path rather than drip-merging a failing major lint-stack update.
- Stabilized the repo-side Playwright suite:
  - added shared homepage E2E fixtures for hospitals, analytics, trends,
    geolocation, and Mapbox
  - removed brittle waits/selectors from the active homepage/map/mobile specs
  - fixed the footer landmark accessibility regression
  - added stable map marker test IDs
  - deferred region analytics until the landing hero is dismissed so the
    browser-entry state is deterministic
- Reconciled active docs to reflect that Playwright stabilization is complete,
  while browser E2E remains CI-first and manual-dispatch to conserve GitHub
  Actions free-tier minutes:
  - `docs/planning/roadmap.md`
  - `docs/development/testing-guidelines.md`
  - `.github/workflows/README.md`
  - `frontend/README.md`
  - `README.md`
  - `docs/planning/manual-tasks.md`
  - `docs/index.md`
  - `docs/README.md`
  - `docs/planning/README.md`
  - `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`
  - `AGENTS.md`

## Verified Current State

Observed on **2026-04-09**:

- `https://wait-time.ca/api/health` returned `healthy: true`
- `bash scripts/production-smoke.sh https://wait-time.ca` still failed on:
  - `/api/status`
  - `/api/data-quality`
- live `/api/status` and aggregate `/api/data-quality` still exposed legacy
  source IDs, confirming the shared-VPS frontend release step remains undone
- the current shell could not reach a usable shared-VPS SSH target, so the
  release step could not be completed during this maintenance pass

## Remaining Follow-Up

- Deploy the latest VPS frontend release from a workstation with a reachable
  shared-host SSH target, then re-run production smoke against `wait-time.ca`.
- Upgrade the production Neon project off the free tier.
- Keep Playwright browser verification manual-dispatch in GitHub Actions until
  free-tier pressure is less sensitive; the suite itself is now repo-side
  stabilized.
- The admissions-strengthening plan remains active and should not be archived.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
- `npm run lint`
- `npm run format:check`
- `npm run type-check`
- `npm run test:unit`
- `npm run build`
- `git log --format='%an <%ae>' | sort -u`
- `gh pr list --state open`
- `gh api repos/jerdaw/waittimecanada/branches --paginate --jq '.[].name'`
- `curl -fsS https://wait-time.ca/api/health`
- `curl -fsS https://wait-time.ca/api/status`
- `curl -fsS https://wait-time.ca/api/data-quality`
- `bash scripts/production-smoke.sh https://wait-time.ca`
