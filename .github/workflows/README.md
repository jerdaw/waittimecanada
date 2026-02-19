# GitHub Actions Workflows

This directory contains operational and CI workflows for Wait Time Canada.

## Workflow Catalog

### 1. `docs-ci.yml` - Documentation Quality CI

**Trigger:** push/PR affecting docs and README surfaces.

**Purpose:** Prevent stale/broken markdown by enforcing documentation hygiene checks.

**Jobs:**
- `docs-quality` (runs `scripts/check-docs.sh`)

**Checks include:**
- ban `file://` links
- detect non-human co-author trailers
- validate repository-relative markdown links across active docs
- exclude designated historical snapshot docs from strict link checks

---

### 2. `frontend-ci.yml` - Frontend CI

**Trigger:** push/PR affecting `frontend/**`.

**Purpose:** Keep frontend quality gates strict while reducing redundant runtime.

**Jobs:**
- `changes` (path-aware scope detection)
- `lint` (ESLint + Prettier check)
- `type-check` (TypeScript)
- `test-unit` (Vitest + coverage)
- `test-e2e` (Playwright Chromium only, diff-gated)
- `build` (Next.js production build, diff-gated)

**Optimization controls:**
- Branch-level concurrency cancellation.
- Changed-path gating for heavy E2E/build steps.
- Explicit failures (no permissive "skip on error" fallbacks).

---

### 3. `scraper-ci.yml` - Backend/Scraper CI

**Trigger:** push/PR affecting `backend/**`.

**Jobs:**
- `lint` (ruff)
- `type-check` (mypy, advisory)
- `test` (pytest + coverage)
- `security` (Bandit, advisory)

**Optimization controls:**
- Branch-level concurrency cancellation.

---

### 4. `scraper-cron.yml` - Scheduled Scraper Execution

**Trigger:** every 15 minutes + manual dispatch.

**Purpose:** Run all provincial scrapers against production DB and emit failure alerts.

**Optimization controls:**
- Serialized concurrency group to avoid overlapping cron runs.

---

### 5. `heartbeat-monitor.yml` - Dead Man's Switch

**Trigger:** every 30 minutes + manual dispatch.

**Purpose:** Ensure scraper heartbeat freshness remains within threshold.

**Optimization controls:**
- Serialized concurrency group to avoid overlapping checks.

---

### 6. `database-cleanup.yml` - Measurement Retention Cleanup

**Trigger:** daily + manual dispatch.

**Purpose:** Enforce retention policy for old measurement rows.

**Optimization controls:**
- Serialized concurrency group.

---

### 7. `production-readiness.yml` - Production Readiness Gate

**Trigger:** manual dispatch.

**Purpose:** Validate secrets + heartbeat, optionally run smoke checks.

**Optimization controls:**
- Branch-level concurrency cancellation.

---

### 8. `production-smoke.yml` - Live Route Smoke Checks

**Trigger:** every 6 hours + manual dispatch.

**Purpose:** Verify public production routes respond with expected markers.

**Optimization controls:**
- Single concurrency group with cancellation for stale overlapping runs.

---

### 9. `portfolio-screenshots.yml` - Portfolio Screenshot Artifact Generation

**Trigger:** manual dispatch.

**Purpose:** Build frontend, run scripted capture flow, upload screenshots artifact.

**Optimization controls:**
- Single concurrency group with cancellation.

---

### 10. `database-migrate.yml` - Database Migration Runner

**Trigger:** push to `main` for `database/migrations/**` + manual dispatch.

**Purpose:** Apply database migrations through Supabase tooling.

Note: the current production database is Neon PostgreSQL. Treat this workflow as
legacy/optional unless your environment is explicitly configured for Supabase CLI.
Default local migration path remains `python backend/run_migrations.py`.

**Optimization controls:**
- Serialized concurrency per ref.

## Secrets Matrix

### Core production/runtime
- `DATABASE_URL` (required by scraper, readiness, cleanup, frontend build paths)
- `NEXT_PUBLIC_MAPBOX_TOKEN` (required by frontend build/test/screenshot workflows)

### Alerting/observability
- `PUSHOVER_USER_KEY` (optional but recommended)
- `PUSHOVER_API_TOKEN` (optional but recommended)
- `SENTRY_DSN` (optional)

### Production smoke
- `PRODUCTION_BASE_URL` (required for scheduled smoke checks and optional readiness smoke)

### Database migration workflow
- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_PROJECT_ID`
- `SUPABASE_URL`
- `ALERT_EMAIL_USER`
- `ALERT_EMAIL_PASSWORD`
- `ALERT_EMAIL_TO`

## Operational Notes

- Playwright E2E is CI-only for normal development flow.
- `frontend-ci.yml` keeps strict quality gates while avoiding heavy jobs when changes do not affect runtime behavior.
- `production-readiness.yml` and `production-smoke.yml` are the operational preflight/postflight checks for live deployment confidence.
