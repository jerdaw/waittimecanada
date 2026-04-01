# Maintenance Log — 2026-04-01

## Scope

Post-Neon-recovery maintenance sweep covering docs/state reconciliation,
roadmap/manual-task updates, branch and PR cleanup, junk artifact removal, and
lightweight verification.

## Completed

- Removed the local junk artifact `backend/tests/__pycache__`.
- Verified the repo still enforces human-only attribution:
  - `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`
  - recent `main` history remains human-authored only
- Closed open Dependabot PRs `#43` through `#48` and deleted their remote
  branches to keep frontend dependency maintenance on the planned batch-refresh
  path.
- Confirmed the only remaining remote branches are `main` and `gh-pages`.
- Added Neon-first hosted quick-start guidance in the active setup docs:
  - `README.md`
  - `docs/getting-started/quick-start.md`
  - `docs/development/setup.md`
- Reconciled active docs that still described the March 28 quota outage as the
  current blocker:
  - `docs/planning/roadmap.md`
  - `docs/index.md`
  - `docs/README.md`
  - `docs/operations/OPERATIONAL_STATUS.md`
  - `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`
  - `AGENTS.md`
  - `.github/workflows/README.md`
- Added manual-task entries for the remaining Neon cost follow-up:
  - upgrade the production project to Neon Launch
  - optionally apply to the Neon Open Source Program

## Verified Live State

Observed on **2026-04-01**:

- `https://wait-time.ca/api/health` returned `healthy: true` with the database
  connected
- `https://wait-time.ca/api/hospitals?province=ON&limit=1` returned live data
- `https://wait-time.ca/api/resources?kind=facility&province=ON&limit=1`
  returned live data
- recent scheduled `Heartbeat Monitor (Dead Man's Switch)` runs were succeeding
- recent scheduled `Production Smoke` runs were succeeding

## Remaining Follow-Up

- The March 28 Neon transfer-quota outage is no longer the live blocker.
- A separate public-surface mismatch remains: `/api/status` and
  `/api/data-quality` still expose critical aggregate values and inactive legacy
  source IDs (`manitoba-shared-health`, `on-health`) that do not match the
  healthy live source runs observed on 2026-04-01.
- Frontend dependency maintenance remains intentionally batched rather than
  drip-merged from Dependabot.
- The admissions-strengthening plan remains active and should not be archived.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
- `git log origin/main --format='%an <%ae>' | sort -u`
- `gh pr list`
- `gh run list --limit 12`
- live route checks against:
  - `/api/health`
  - `/api/hospitals?province=ON&limit=1`
  - `/api/resources?kind=facility&province=ON&limit=1`
  - `/api/status`
  - `/api/data-quality`
