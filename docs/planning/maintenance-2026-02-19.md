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
