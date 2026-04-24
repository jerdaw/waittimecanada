# Maintenance Log — 2026-04-24

## Scope

Repo-audit closeout, planning lifecycle cleanup, deployment-truth reconciliation,
and workspace hygiene after the 2026-04-23 maintenance wave.

## Completed

- Archived the completed repo-audit follow-up/remediation docs and replaced the
  old active paths with archived stubs.
- Reconciled deployment-blocker wording with the real runtime:
  - the frontend is live on the shared VPS
  - Netlify is rollback-only, not an active deployment lane
  - the backend scheduler remains on GitHub Actions while Ontario is
    unreachable from the VPS
- Archived the completed municipal-inspection pilot decision and removed it
  from the active planning queue.
- Rebased the root README away from volatile March-only counts and fixed
  validation-language drift around test counts and backend integration depth.
- Reframed backend integration-testing docs so the optional GitHub Actions
  snippet is not presented as a default enforced CI lane.
- Removed local ignored build/test artifacts:
  - `.mypy_cache/`
  - `frontend/.next/`

## Verified Current State

Observed on **2026-04-24**:

- `wait-time.ca` remains frontend-live on the shared VPS
- the backend scheduler path remains on GitHub Actions
- Netlify remains rollback-only for the frontend
- active planning/docs entry points now point to the real split-runtime
  baseline without treating finished decision memos as live work

## Remaining Follow-Up

- Monitor the active **2026-04-16 → 2026-05-01** Neon Launch billing window.
- Keep Playwright browser verification CI-first/manual-dispatch to conserve
  GitHub free-tier minutes.
- Keep backend cutover deferred until an Ontario-compatible runtime path is
  proven outside the shared-VPS blocker.
- Keep blocked Ontario domains parked until their external gates change:
  official AED registry integration, native naloxone ingestion, and municipal
  inspection/compliance work.

## Verification

- `bash scripts/check-docs.sh`
- `python3 backend/scripts/verify_roadmap_consistency.py`
- `cd frontend && npm run lint`
- `cd frontend && npm run format:check`
