# Maintenance Log — 2026-04-18

## Scope

Neon production-upgrade runbook creation, active ops-doc reconciliation, and
roadmap/manual-task cleanup after the VPS release and Node 22 dependency
refresh pass.

## Completed

- Added a current manual runbook for the remaining production Neon follow-up:
  - `docs/operations/neon-production-upgrade.md`
- Reconciled active roadmap/manual-task language so the next production cost
  step is explicit:
  - Neon Launch is the recommended production posture
  - the Open Source Program remains optional and sequenced after Launch
- Updated active operational docs to point to the new runbook:
  - `docs/operations/QUICK_START.md`
  - `docs/operations/scraper-scheduling.md`
  - `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`
  - `docs/operations/OPERATIONAL_STATUS.md`
- Updated active planning/documentation entry points:
  - `docs/planning/roadmap.md`
  - `docs/planning/manual-tasks.md`
  - `docs/planning/README.md`
- Updated the README deployment summary so it no longer presents Neon free tier
  as an acceptable steady-state production target.

## Verified Current State

Observed on **2026-04-18**:

- the shared-VPS frontend release and public summary verification remain
  complete
- the highest-priority remaining manual ops task is the Neon Launch upgrade
- active docs now consistently treat Neon free tier as a local/evaluation path,
  not a preferred steady-state production posture

## Remaining Follow-Up

- Run `docs/operations/neon-production-upgrade.md`.
- After Launch is active, monitor one billed month before revisiting any deeper
  production DB-path changes.
- Optionally apply to the Neon Open Source Program after the Launch upgrade is
  confirmed.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
