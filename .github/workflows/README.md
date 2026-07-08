# GitHub Actions Workflows

This directory contains operational and CI workflows for Wait Time Canada.

## Workflow Catalog

### 1. `docs-ci.yml` - Documentation Quality CI

**Trigger:** push/PR affecting tracked text/source/data-artifact files covered
by public docs and authorship policy checks, plus the broader `docs/**` tree.

**Purpose:** Prevent stale/broken markdown by enforcing documentation hygiene checks.
It also keeps lightweight repository-policy checks active when source changes
could introduce non-human attribution markers. The checkout fetches full Git
history so the authorship metadata audit can inspect existing commits, not only
the latest shallow commit.

**Jobs:**
- `docs-quality` (runs `scripts/check-docs.sh`)

**Checks include:**
- ban `file://` links
- detect non-human authorship attribution markers in tracked public text/source/data-artifact files
- detect non-human author, committer, or authorship-trailer metadata in available Git history
- verify `CLAUDE.md` and `GEMINI.md` remain relative symlinks to `AGENTS.md`
- verify `AGENTS.md` ontology constants match the implemented backend enums
- verify Docs CI keeps path filters aligned with tracked text/source checks
- block public-boundary marker terms for private operations or personal notes
- validate repository-relative markdown links across active docs
- preserve clinical-safety and ontology-comparability guardrail wording
- verify roadmap consistency against the latest completed milestone
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
- `test-e2e` (Playwright Chromium only, manual dispatch for CI-first browser verification)
- `build` (Next.js production build, diff-gated)

**Optimization controls:**
- Branch-level concurrency cancellation.
- Changed-path gating for heavy E2E/build steps.
- Playwright E2E remains manual-dispatch only to conserve free-tier minutes; the suite was repo-side stabilized on 2026-04-09, so routine push/PR CI continues to rely on lint, type-check, unit tests, and build.
- Manual Playwright verification uses a disposable `postgres:17` service and
  fake public Mapbox token, not production database or frontend secrets.
- Explicit failures (no permissive "skip on error" fallbacks).
- Unit-test coverage is retained as a short-lived GitHub Actions artifact.

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
- Backend dependencies are installed with pinned `uv` plus `uv sync --locked`
  so CI uses the checked-in lockfile instead of floating resolver output.
- The lint job checks `backend/src`, `backend/scripts`, and the migration
  filename/sequence guard.
- Coverage is retained as a short-lived GitHub Actions artifact.
- The security job runs Bandit directly on the runner and retains a JSON report
  artifact, avoiding the deprecated Node 20 path inside the old
  `PyCQA/bandit-action@v1` composite.

---

### 4. `scraper-cron.yml` - Scraper Execution

**Trigger:** hourly schedule plus manual dispatch.

**Purpose:** Run all provincial scrapers against the configured database and emit classified source-health state.

**Optimization controls:**
- Serialized concurrency group to avoid overlapping cron runs.

---

### 5. `heartbeat-monitor.yml` - Dead Man's Switch

**Trigger:** every 30 minutes plus manual dispatch.

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

**Trigger:** manual dispatch. Scheduled trigger is temporarily paused to conserve GitHub Actions free-tier minutes.

**Purpose:** Verify public production routes respond with expected markers, including the public-health-hub `/resources` surface, the additive source-catalog contract, the Ontario EMS system-context API, and the Ontario water-advisories API.

**Optimization controls:**
- Single concurrency group with cancellation for stale overlapping runs.

---

### 9. `demo-screenshots.yml` - Demo Screenshot Artifact Generation

**Trigger:** manual dispatch.

**Purpose:** Build frontend, run scripted capture flow, upload screenshots artifact.

**Optimization controls:**
- Single concurrency group with cancellation.

---

### 10. `database-migrate.yml` - Database Migration Runner

**Trigger:** push to `main` for `database/migrations/**` + manual dispatch.

**Purpose:** Apply database migrations to the configured PostgreSQL database using `backend/run_migrations.py`.

**Optimization controls:**
- Serialized concurrency per ref.
- Installs locked backend dependencies before running migrations so `waittime`
  imports resolve correctly in CI.
- Failure email is best-effort and runs only when alert secrets are configured.

---

### 11. `public-health-hub-cron.yml` - Public Health Hub Ingest

**Trigger:** manual dispatch. Scheduled trigger is temporarily paused to conserve GitHub Actions free-tier minutes.

**Purpose:** Refresh shipped public-health-hub datasets from approved live upstreams:
- MOHSERLO via the Ontario ArcGIS feature service
- Statistics Canada ODHF via the official zipped CSV archive
- Ontario AED fallback via the approved Overpass query
- Health Canada recalls via the approved RSS feed
- Ontario land ambulance response times via approved Ontario Data Catalogue CSV downloads

**Optimization controls:**
- Serialized concurrency group to avoid overlapping ingest runs.
- Reuses the existing `DATABASE_URL` secret; no new secrets required.
- MOHSERLO, ODHF, Health Canada alerts, and Ontario EMS system context remain
  hard-fail paths; the Overpass AED fallback runs in its own best-effort step
  so transient AED mirror failures do not block the rest of the batch. AED
  mirror failures are recorded as explicit best-effort summary state rather
  than as a failing workflow annotation.
- ISC water advisories remain a live-proxied frontend route and are
  intentionally outside this scheduled DB-ingest workflow.
- Each run appends a GitHub Actions job summary with per-step outcomes plus the
  current source refresh timestamps, normalized row counts, and explicit
  `healthy` / `partial` / `degraded` operator classifications from the database
  state.
- Hard-fail public-health sources (`mohserlo`, `odhf`,
  `health-canada-recalls`, `ontario-land-ambulance-response-times`) now use
  transition-aware alerting via persisted incident state so operators receive
  one degraded alert and one recovery alert instead of repeat duplicates. The
  best-effort AED fallback is intentionally excluded from paging.

### 12. `deploy-docs.yml` - Documentation Publishing

**Trigger:** push to `main` affecting docs surfaces + manual dispatch.

**Purpose:** Publish the MkDocs site to the `gh-pages` branch.

**Authorship rule:**
- The workflow is configured to write docs-publish commits with the human repo
  author identity rather than `github-actions[bot]`, so published branch
  history remains aligned with the repository's human-authorship policy.

## Secrets Matrix

### Core production/runtime
- `DATABASE_URL` (required by scraper, readiness, cleanup, and operational smoke paths)
- `NEXT_PUBLIC_MAPBOX_TOKEN` (required by deployment/screenshot workflows; frontend CI uses a fake public token for validation)

### Alerting/observability
- `ALERT_API_URL`, `ALERT_USER_KEY`, `ALERT_API_TOKEN` if operational alerting is enabled
- `SENTRY_DSN` (optional)

### Production smoke
- `PRODUCTION_BASE_URL` (required for smoke checks)

### Database migration workflow
- Optional notification email credentials, if migration failure email is enabled

## Operational Notes

- Playwright E2E is GitHub-CI-only and manual-dispatch to conserve free-tier minutes, even though the current suite has been repo-side stabilized.
- The scraper and heartbeat workflows run on the public source-freshness
  cadence. Snapshot, public-health ingest, and smoke checks remain
  manual-dispatch while broader operational offload work continues.
- `frontend-ci.yml` keeps strict quality gates while avoiding heavy jobs when changes do not affect user-facing frontend runtime behavior.
- `production-readiness.yml` and `production-smoke.yml` are lightweight operational preflight/postflight checks.
- Production smoke now exercises `/api/status` and aggregate `/api/data-quality` directly and fails if dormant legacy source IDs such as `manitoba-shared-health` or `on-health` leak into the public payload.
