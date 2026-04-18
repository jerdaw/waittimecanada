# Maintenance Log — 2026-04-18

## Scope

Neon production-upgrade runbook creation, active ops-doc reconciliation, roadmap
/manual-task cleanup after the VPS release and Node 22 dependency refresh pass,
and final confirmation that the production Neon project was already on Launch.

## Completed

- Added a current manual runbook for the remaining production Neon follow-up:
  - `docs/operations/neon-production-upgrade.md`
- Reconciled active roadmap/manual-task language so the next production cost
  step is explicit:
  - Neon Launch is the recommended production posture
  - the Open Source Program remains optional and sequenced after Launch
- Confirmed on **2026-04-18** that the production Neon dashboard already shows
  **Launch** active, with the current billing period beginning on
  **2026-04-16**
- Reconciled the active docs again so the Launch upgrade is now marked
  completed rather than still pending
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
- the production Neon Launch upgrade is already complete
- active docs now consistently treat Neon free tier as a local/evaluation path,
  not a preferred steady-state production posture
- the remaining Neon follow-up is only first-billing-window monitoring plus the
  optional Open Source Program application

## Remaining Follow-Up

- Monitor one billed month on Launch before revisiting any deeper
  production DB-path changes.
- Optionally apply to the Neon Open Source Program after the Launch confirmation
  confirmed.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
- `curl -fsS https://wait-time.ca/api/health`
- `bash ./scripts/production-smoke.sh https://wait-time.ca`
