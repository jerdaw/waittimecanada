# Maintenance Log — 2026-04-23

## Scope

Ontario public-health-hub production closeout, roadmap and planning-doc
reconciliation, frontend deploy-runbook hardening, attribution/branch hygiene
verification, and final cleanup after the Ontario selective-expansion pass.

## Completed

- Reconciled the active roadmap to the live Ontario state:
  - Ontario Public Health Hub Phase 2 remains closed and delivered
  - the first selective-expansion pass (Ontario reserve-system drinking water
    advisories) is recorded as live
  - ODHF is now back in the live ingest/status path and the public-health-hub
    source baseline is healthy again
  - the frontend deploy helper now waits for localized page readiness before
    post-deploy smoke
- Reclassified Batch A-only public-health planning baselines as historical
  planning references rather than active living plans:
  - `docs/planning/public-health-data-hub-metadata-contract.md`
  - `docs/planning/public-health-data-hub-freshness-safety-rules.md`
- Updated active operational/docs entry points:
  - `README.md`
  - `backend/README.md`
  - `frontend/README.md`
  - `docs/README.md`
  - `docs/planning/README.md`
  - `docs/planning/index.md`
  - `docs/planning/manual-tasks.md`
  - `docs/operations/direct-vps-frontend.md`
  - `.github/workflows/README.md`
- Removed the stale non-human extension recommendation from the historical
  repository-structure snapshot so no non-human tooling is presented as a
  contributor/developer default
- Verified GitHub hygiene:
  - no open PRs remained
  - no lingering local feature branches remained
  - only `origin/main` and the intentional docs-publish `origin/gh-pages`
    branch remained on the remote
  - merged PR titles that still carried agent tags were renamed to neutral,
    human-only titles
- Verified commit-author hygiene:
  - commit author identities in history are human accounts or allowed bots
    (`dependabot[bot]`, `github-actions[bot]`)
  - no non-human co-author trailers were present in repo text surfaces checked
    by docs validation

## Verified Current State

Observed on **2026-04-23**:

- production `wait-time.ca` serves the Ontario EMS system-context route and the
  Ontario water-advisory route successfully
- production smoke passes after the latest frontend rollout
- `public_health_hub_status` is overall `healthy`
- the roadmap/manual-task/planning entry points now match the shipped Ontario
  scope and remaining deferred work

## Remaining Follow-Up

- Monitor the active **2026-04-16 → 2026-05-01** Neon Launch billing window.
- Keep Playwright browser verification CI-first/manual-dispatch to conserve
  GitHub Actions free-tier minutes.
- Keep backend cutover deferred until an Ontario-compatible runtime path is
  proven outside the current shared-VPS blocker.
- Keep blocked Ontario domains parked until their external gates change:
  official AED registry integration, native naloxone ingestion, and municipal
  inspection/compliance work.
- Continue the admissions-strengthening plan items that still require explicit
  user go-ahead or external outreach.

## Verification

- `bash scripts/check-docs.sh`
- `python3 backend/scripts/verify_roadmap_consistency.py`
- `git log --all --format='%H%x09%an%x09%ae'`
- `gh pr list --state open --limit 50`
- `gh pr list --state all --search 'claude in:title OR gemini in:title OR codex in:title OR copilot in:title OR chatgpt in:title' --limit 100`
