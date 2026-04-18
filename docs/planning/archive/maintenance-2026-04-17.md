# Maintenance Log — 2026-04-17

## Scope

Frontend dependency refresh completion, Node 22 baseline alignment, VPS release
verification follow-up, docs/roadmap reconciliation, artifact cleanup, and
Git/GitHub hygiene.

## Completed

- Removed local frontend build artifacts created during verification:
  - `frontend/.next`
- Refreshed the frontend dependency tree within current major versions and
  regenerated `frontend/package-lock.json` under the Node 22 toolchain that
  matches the VPS/Docker runtime family.
- Added a repo-visible frontend Node baseline:
  - root `.nvmrc` set to `22.13.1`
  - `frontend/package.json` `engines.node` aligned to Node 22
- Updated frontend-facing GitHub Actions workflows to Node 22:
  - `.github/workflows/frontend-ci.yml`
  - `.github/workflows/lighthouse.yml`
  - `.github/workflows/portfolio-screenshots.yml`
- Tightened Dependabot so frontend npm updates are grouped for patch/minor
  refreshes and semver-major churn is ignored until a dedicated migration wave.
- Updated active setup/runtime docs to match the new frontend baseline:
  - `README.md`
  - `docs/development/setup.md`
  - `docs/getting-started/quick-start.md`
- Fixed a stale documentation link in
  `backend/docs/methodologies/README.md` so docs integrity checks pass again.
- Reconciled active planning docs:
  - marked the batch frontend dependency refresh complete in
    `docs/planning/roadmap.md`
  - updated `docs/planning/manual-tasks.md` to reflect the verified VPS release
    at `main@2eb0faf`
  - archived this maintenance session
- Re-verified repository guardrails:
  - `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`
  - active docs still state the human-only authorship rule
- Re-verified GitHub cleanup state:
  - no open pull requests
  - no lingering remote branches beyond `main` and `gh-pages`

## Verified Current State

Observed on **2026-04-17**:

- the shared-VPS frontend release and public status/data-quality verification
  are complete in production
- the frontend toolchain is now aligned on Node 22 across local guidance, CI,
  and the VPS/Docker runtime family
- the repo-side dependency refresh is implemented and validated without widening
  into framework-major migrations
- the remaining operational blocker is still the manual production Neon plan
  upgrade
- no git history rewrite was performed; visible historical authors remain human
  maintainers plus allowed platform bots only

## Remaining Follow-Up

- Upgrade the production Neon project off the free tier.
- Keep Playwright browser verification CI-first and manual-dispatch in GitHub
  Actions to conserve free-tier minutes; use that path for the post-refresh
  browser pass rather than local E2E.
- Keep backend cutover deferred until Ontario reachability is proven from a
  compatible runtime.
- Treat any future frontend framework-major upgrades as a separate tracked
  migration wave rather than extending this maintenance batch.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
- `cd frontend && mise exec node@22.13.1 -- npm ci`
- `cd frontend && mise exec node@22.13.1 -- npm run lint`
- `cd frontend && mise exec node@22.13.1 -- npm run format:check`
- `cd frontend && mise exec node@22.13.1 -- npm run type-check`
- `cd frontend && mise exec node@22.13.1 -- npm run test:unit`
- `cd frontend && mise exec node@22.13.1 -- npm run build`
- `gh pr list --state open`
- `gh api repos/jerdaw/waittimecanada/branches --paginate --jq '.[].name'`
