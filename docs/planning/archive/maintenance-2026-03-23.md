# Maintenance Session - 2026-03-23

## Summary

Repository maintenance pass after the production raw-retention rollback and
cleanup-runtime investigation. This session focused on reconciling active docs
with the live behavior, recording the new cleanup posture in ADRs/roadmap
artifacts, verifying human-only authorship, and confirming CI/branch hygiene.

## Tasks Completed

### 1. Production cleanup verification ✅

- Confirmed the March 23 production cleanup run deleted `207,059` measurements
  older than 30 days and reduced the live row count from `314,943` to `108,262`.
- Confirmed the follow-up run found `0` remaining measurements older than 30
  days.

### 2. Cleanup runtime hardening ✅

- Verified the initial runtime bottleneck was the pre-delete aggregate refresh,
  not the delete query itself.
- Shipped a bounded cleanup path that:
  - deletes in batches
  - skips aggregate refresh in the GitHub Actions maintenance workflow
  - caps per-run delete work for predictable maintenance windows
- Confirmed the updated production workflow completed in `22s` instead of
  `5m48s`.

### 3. Documentation and ADR reconciliation ✅

- Updated active docs to describe the live cleanup posture:
  - 30-day raw retention remains the policy
  - GitHub Actions cleanup skips aggregate refresh intentionally
  - storage cleanup is bounded and observable
- Superseded ADR-0020 with ADR-0021 so the repository no longer presents
  indefinite raw retention as current policy.
- Updated the roadmap current status and completed ops items accordingly.

### 4. Repository hygiene ✅

- Confirmed there were no temp/junk files requiring deletion.
- Confirmed `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`.
- Confirmed the only remote branches are `main` and `gh-pages`; there were no
  open PRs or stale jerdaw/dependabot branches requiring action.

### 5. Authorship and CI verification ✅

- Confirmed reachable git history lists only Jeremy Dawson as commit author.
- Confirmed the repository still contains explicit documentation/commit
  guardrails against non-human authorship attribution.
- Confirmed recent `main` CI and workflow runs were green after the maintenance
  commits.

## Verification

- `bash scripts/check-docs.sh`
- `cd backend && pytest tests/unit/test_cleanup_cli.py tests/unit/test_database_cleanup.py tests/unit/services/test_database_service.py -q`
- GitHub Actions `Scraper CI` for commit `54060cc`: passed
- GitHub Actions `Database Cleanup` for run `23423448059`: passed in 22s
