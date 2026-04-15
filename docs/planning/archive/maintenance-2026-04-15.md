# Maintenance Log — 2026-04-15

## Scope

Data-quality correctness verification, runtime env/bootstrap hardening follow-up,
heartbeat threshold alignment verification, docs/roadmap/ADR reconciliation,
artifact cleanup, and Git/GitHub hygiene.

## Completed

- Removed local compile junk artifacts created during verification:
  - Python `__pycache__` directories
  - Python `*.pyc` files
- Re-verified the repo-side consistency pass:
  - backend quality logic now counts distinct UTC hourly scrape windows rather
    than raw measurement rows
  - hospital `/api/data-quality` coverage now uses the same distinct-hour model
  - invalid `/api/data-quality` query combinations now return `400`
  - backend runtime bootstrap no longer auto-loads `.env.local` / `.env`
  - backend heartbeat defaults now align to the live 120-minute threshold
- Added ADR-0025 to record the scrape-window semantics and explicit runtime env
  contract decision.
- Updated active docs so setup/runtime guidance matches the code:
  - `README.md`
  - `backend/README.md`
  - `docs/development/setup.md`
  - `docs/getting-started/quick-start.md`
  - `docs/reference/environment-variables.md`
  - `docs/API.md`
  - `docs/architecture/api.md`
- Reconciled the active roadmap to mark this repo-side consistency pass
  delivered and archived this maintenance session.
- Verified repository authorship guardrails remain active:
  - `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`
  - active docs still state the human-only authorship rule
- Verified GitHub cleanup state:
  - no open pull requests
  - no lingering remote feature branches beyond `main` and `gh-pages`

## Verified Current State

Observed on **2026-04-15**:

- repo-side data-quality semantics/runtime bootstrap/heartbeat alignment work is
  implemented and documented
- the remaining operational gap is still live VPS frontend release/verification
  for `/api/status` and aggregate `/api/data-quality`
- the production Neon upgrade remains a manual external task
- historical git author output still includes earlier Dependabot-authored
  commits; no history rewrite was performed during this maintenance pass

## Remaining Follow-Up

- Deploy the latest VPS frontend release from a workstation with a reachable
  shared-host SSH target, then re-run production smoke against `wait-time.ca`.
- Upgrade the production Neon project off the free tier.
- Keep Playwright browser verification CI-first and manual-dispatch in GitHub
  Actions to conserve free-tier minutes.
- If the repository owner wants historical git history rewritten to remove old
  bot authors entirely, treat that as a separate explicit force-push decision
  rather than routine maintenance.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
- `python3 -m pytest backend/tests/unit/test_heartbeat_service.py backend/tests/unit/test_data_quality_service.py backend/tests/unit/services/test_database_service.py backend/tests/unit/services/test_data_quality_correctness.py`
- `cd frontend && npm run lint`
- `cd frontend && npm run type-check`
- `cd frontend && npx -y node@20 ./node_modules/vitest/vitest.mjs run app/api/data-quality/route.test.ts utils/validations.test.ts`
- `git log --format='%an <%ae>' | sort -u`
- `gh pr list --state open`
- `gh api repos/jerdaw/waittimecanada/branches --paginate --jq '.[].name'`
