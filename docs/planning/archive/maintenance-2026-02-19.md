# Maintenance Session - 2026-02-19

## Summary

Maintenance sweep focused on the `wait-time.ca` domain rebrand staging, documentation accuracy, and repository hygiene.

## Tasks Completed

### 1. Branding + Canonical Domain Staging ✅

- Standardized user-facing naming to **Wait Time Canada**
- Staged canonical domain as `https://wait-time.ca` across SEO metadata, sitemap/robots, and export citations
- Added legacy host redirect logic (effective once public hosting is unpaused)
- Documented the paused hosting posture and on-hold cutover target (**March 9, 2026**) in `docs/planning/roadmap.md`

### 2. Documentation + ADRs ✅

- Added `docs/adr/0017-domain-rebrand-wait-time-ca.md` to capture the rebrand decision and operational posture
- Updated MkDocs configuration to reference only existing pages and added missing index pages required for `mkdocs gh-deploy`

### 3. Cleanup ✅

- Removed committed frontend test run artifacts (`frontend/test-results*.json`) and added an ignore rule to prevent reintroduction
- Cleaned local ignored artifacts via `git clean -fdX` (no repo content impacted)

### 4. Tooling + Safety Checks ✅

- Unblocked pre-commit by hardening checks:
  - Excluded `mkdocs.yml` from YAML validation (Material config uses Python tags)
  - Constrained mypy pre-commit scope to `backend/src/` with explicit typecheck dependencies
  - Reduced false-positive secret scanning by removing credential-shaped examples and excluding generated hash manifests
- Renamed the Alberta debug script to avoid test-name collisions and removed full-HTML persistence from the helper

### 5. Attribution Policy ✅

- Verified repository policy remains human-authored only (no non-human co-author trailers detected by docs checks)
- CLAUDE/GEMINI instruction files remain symlinked to `AGENTS.md`

## Verification

- Documentation quality checks: `bash scripts/check-docs.sh`
- Frontend unit tests: `cd frontend && npm run test:unit`
- Backend tests: `python -m pytest -q backend/tests`
- Pre-commit hooks: `pre-commit run -a`

---

## Additional Session (M30 Closeout + Backlog Hygiene)

### 6. M30 Operational Rollout Validation ✅

- Confirmed migration `013_add_scraper_observability_columns.sql` applied successfully in target environment
- Confirmed scraper run + `check_heartbeat --verbose` surfaced structured failure diagnostics (including category/stage)
- Confirmed frontend health route/component tests pass with new health fields

### 7. Backlog and Planning Hygiene ✅

- Confirmed M30 implementation plan is archived and marked delivered:
  - `docs/planning/archive/milestone-30-scraper-visibility-reliability.md`
- Pruned completed checklist items from active roadmap queues to keep backlog focused on open work
- Added explicit open P0 item for Quebec zero-value parser handling discovered during post-rollout run

### 8. Documentation + Governance Maintenance ✅

- Added ADR for M30 architecture and operational contract:
  - `docs/adr/0018-scraper-observability-and-reliability-hardening.md`
- Updated API/database reference docs to include new health and `scraper_status` fields
- Verified repository human-authorship policy is present in `AGENTS.md` and shared through `CLAUDE.md`/`GEMINI.md` symlinks
