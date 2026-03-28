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

**Trigger:** push/PR affecting `frontend/**` or `codecov.yml`.

**Purpose:** Keep frontend quality gates strict while reducing redundant runtime.

**Jobs:**
- `changes` (path-aware scope detection)
- `lint` (ESLint + Prettier check)
- `type-check` (TypeScript)
- `test-unit` (Vitest + coverage)
- `test-e2e` (Playwright Chromium only, manual dispatch while the suite is being stabilized)
- `build` (Next.js production build, diff-gated)

**Optimization controls:**
- Branch-level concurrency cancellation.
- Changed-path gating for heavy E2E/build steps.
- Playwright E2E is currently manual-dispatch only while the suite is being stabilized; routine push/PR CI relies on lint, type-check, unit tests, and build.
- Explicit failures (no permissive "skip on error" fallbacks).
- Unit-test coverage uploads to Codecov with the `frontend` flag.

---

### 3. `scraper-ci.yml` - Backend/Scraper CI

**Trigger:** push/PR affecting `backend/**` or `codecov.yml`.

**Jobs:**
- `lint` (ruff)
- `type-check` (mypy, advisory)
- `test` (pytest + coverage)
- `security` (Bandit, advisory)

**Optimization controls:**
- Branch-level concurrency cancellation.
- Coverage uploads to Codecov with the `scrapers` flag.

---

### 4. `scraper-cron.yml` - Scheduled Scraper Execution

**Trigger:** cron `0 * * * *` (hourly) + manual dispatch.

**Purpose:** Run all provincial scrapers against production DB and emit classified operational alerts.

**Optimization controls:**
- Serialized concurrency group to avoid overlapping cron runs.

---

### 5. `heartbeat-monitor.yml` - Dead Man's Switch

**Trigger:** cron `*/30 * * * *` (every 30 minutes) + manual dispatch.

**Purpose:** Ensure scraper heartbeat freshness remains within threshold and report consecutive/classified failures.

**Optimization controls:**
- Serialized concurrency group to avoid overlapping checks.

---

### 6. `database-cleanup.yml` - Database Cleanup

**Trigger:** currently manual dispatch only (scheduled cron temporarily paused due to GitHub Actions quota exhaustion).

**Purpose:** Provide an operator-run retention cleanup entry point. The workflow skips aggregate refresh, deletes raw measurements older than 30 days in bounded batches, and reports `measurements` storage growth.

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

**Trigger:** currently manual dispatch only (scheduled cron temporarily paused due to GitHub Actions quota exhaustion).

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

**Purpose:** Apply database migrations to the live Neon PostgreSQL database using `backend/run_migrations.py`.

**Optimization controls:**
- Serialized concurrency per ref.
- Installs the editable backend package before running migrations so `waittime` imports resolve correctly in CI.
- Failure email is best-effort and runs only when alert secrets are configured.

---

### 11. `public-health-hub-cron.yml` - Public Health Hub Ingest

**Trigger:** cron `15 */6 * * *` (every 6 hours) + manual dispatch.

**Purpose:** Refresh Batch A public-health-hub datasets from approved live upstreams:
- MOHSERLO via the Ontario ArcGIS feature service
- Ontario AED fallback via the approved Overpass query
- Health Canada recalls via the approved RSS feed

**Optimization controls:**
- Serialized concurrency group to avoid overlapping ingest runs.
- Reuses the existing `DATABASE_URL` secret; no new secrets required.
- MOHSERLO and Health Canada alerts remain hard-fail paths; the Overpass AED
  fallback runs in its own best-effort step so transient AED mirror failures do
  not block the rest of the batch.
- Each run appends a GitHub Actions job summary with per-step outcomes plus the
  current source refresh timestamps, normalized row counts, and explicit
  `healthy` / `partial` / `degraded` operator classifications from the database
  state.
- Hard-fail public-health sources (`mohserlo`, `health-canada-recalls`) now use
  transition-aware alerting via persisted incident state so operators receive
  one degraded alert and one recovery alert instead of repeat duplicates. The
  best-effort AED fallback is intentionally excluded from paging.

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
- `ALERT_EMAIL_USER`
- `ALERT_EMAIL_PASSWORD`
- `ALERT_EMAIL_TO`

## Operational Notes

- Playwright E2E is GitHub-CI-only and manual-dispatch while stabilization work is outstanding.
- `frontend-ci.yml` keeps strict quality gates while avoiding heavy jobs when changes do not affect user-facing frontend runtime behavior.
- `production-readiness.yml` and `production-smoke.yml` are the operational preflight/postflight checks for live deployment confidence.
