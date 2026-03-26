# Maintenance Session - 2026-03-26

## Summary

Repository maintenance pass after the production rollout of the frontend Neon
transfer guardrails. This session reconciled active docs with the live VPS
runtime, added an ADR for the new read-cache posture, tightened test coverage
for the cache utility, and cleaned up open dependency PRs so repository state
matches the current roadmap.

## Tasks Completed

### 1. Documentation and roadmap reconciliation ✅

- Updated active docs to reflect the live shared-VPS frontend path instead of
  the older Netlify wording in the docs index.
- Added ADR-0022 to document the accepted decision to use short-lived
  in-process response caching for read-heavy anonymous frontend routes.
- Updated the roadmap current status, completed ops items, and key ADR table to
  reflect the March 26 production deploy.

### 2. Cache test coverage and workflow hygiene ✅

- Added direct unit coverage for `frontend/utils/server-cache.ts`, including
  stable key generation, test-environment bypass behavior, production-mode cache
  reuse, and in-flight request coalescing.
- Added `resetServerCacheForTests()` to keep cache-state tests deterministic.
- Updated `.github/workflows/database-migrate.yml` to use
  `dawidd6/action-send-mail@v16` in a human-authored mainline commit rather
  than merging a bot-authored branch.

### 3. Repository hygiene ✅

- Confirmed no temp or junk files needed removal.
- Confirmed `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`.
- Confirmed local and remote branches are already trimmed to `main` only.

### 4. Authorship and GitHub queue cleanup ✅

- Confirmed recent `main` history contains no `Co-Authored-By` trailers and no
  non-human authors.
- Closed Dependabot PRs `#37` through `#42` and deleted their remote branches.
- Kept the roadmap aligned with the deliberate batch-refresh strategy rather
  than drip-merging incompatible frontend package updates.

## Verification

- `bash scripts/check-docs.sh`
- `cd frontend && npm run format:check`
- `cd frontend && npm run lint`
- `cd frontend && npm run type-check`
- `cd frontend && npm run test:unit -- frontend/tests/utils/server-cache.test.ts frontend/tests/pages/StatusPage.test.tsx frontend/tests/api/health.test.ts frontend/tests/api/hospitals.test.ts frontend/tests/api/analytics-benchmarks.test.ts frontend/tests/api/analytics-regions.test.ts frontend/tests/api/analytics-occupancy.test.ts frontend/tests/api/trends.test.ts`
- `cd frontend && DATABASE_URL='<local-test-database-url>' NEXT_PUBLIC_MAPBOX_TOKEN='test-token' NEXT_PUBLIC_BASE_URL='https://wait-time.ca' npm run build`
