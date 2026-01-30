# GitHub Actions Workflows

This directory contains CI/CD workflows for the WaitTime Canada project.

## Workflows Overview

### 1. `scraper-cron.yml` - Production Scraper Execution

**Trigger:** Every 15 minutes (cron: `*/15 * * * *`)
**Purpose:** Runs all provincial scrapers in production
**Secrets Required:**
- `SUPABASE_URL`
- `SUPABASE_SERVICE_KEY`
- `SENTRY_DSN` (optional)
- `ALERT_EMAIL_USER` (for failure notifications)
- `ALERT_EMAIL_PASSWORD`
- `ALERT_EMAIL_TO`

**What it does:**
1. Installs Python dependencies
2. Runs `python -m src.main` to execute all scrapers
3. Sends email alert on failure (Dead Man's Switch)

### 2. `scraper-ci.yml` - Scraper Code Quality

**Trigger:** Push/PR to `scrapers/` directory
**Purpose:** Lint, type-check, and test scraper code
**Jobs:**
- **lint**: Ruff linter + formatter check
- **type-check**: mypy static type analysis
- **test**: pytest with coverage
- **security**: Bandit security scan

### 3. `frontend-ci.yml` - Frontend Code Quality

**Trigger:** Push/PR to `frontend/` directory
**Purpose:** Lint, type-check, test, and build frontend
**Jobs:**
- **lint**: ESLint + Prettier
- **type-check**: TypeScript compiler
- **test-unit**: Vitest with coverage
- **test-e2e**: Playwright E2E tests
- **build**: Next.js production build

**Secrets Required:**
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

### 4. `database-migrate.yml` - Database Schema Updates

**Trigger:** Push to `main` when `database/migrations/` changes
**Purpose:** Apply database migrations automatically
**Secrets Required:**
- `SUPABASE_ACCESS_TOKEN`
- `SUPABASE_PROJECT_ID`
- `SUPABASE_URL`

**Manual Trigger:** Can specify individual migration file

### 5. `heartbeat-monitor.yml` - Health Check (Dead Man's Switch)

**Trigger:** Every hour (cron: `0 * * * *`)
**Purpose:** Verify scrapers are running
**What it does:**
1. Queries `scraper_status` table
2. Checks if last run was < 60 minutes ago
3. Sends email alert if stale

**Secrets Required:** Same as `scraper-cron.yml`

## Required GitHub Secrets

Configure these in Settings → Secrets and variables → Actions:

```bash
# Supabase
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...        # Service role key
SUPABASE_ACCESS_TOKEN=sbp_...          # For Supabase CLI
SUPABASE_PROJECT_ID=xxxxx              # Project ref

# Frontend (public keys)
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...

# Error Tracking
SENTRY_DSN=https://xxxxx@sentry.io/xxxxx

# Email Alerts (for Dead Man's Switch)
ALERT_EMAIL_USER=monitoring@example.com
ALERT_EMAIL_PASSWORD=app_password_here
ALERT_EMAIL_TO=admin@example.com
```

## Deployment Strategy

### Scrapers
- Run serverlessly via GitHub Actions every 15 minutes
- No dedicated server required
- Utilizes GitHub Actions free tier (2000 minutes/month)

### Frontend
- Auto-deployed to Vercel on push to `main`
- Vercel GitHub integration handles deployment
- No GitHub Action needed (Vercel CLI can be added if needed)

### Database
- Migrations applied automatically on merge to `main`
- Manual rollback via workflow dispatch

## Monitoring

### Success Metrics
- Scraper runs complete in < 10 minutes
- Frontend builds complete in < 5 minutes
- All tests pass with > 80% coverage

### Failure Alerts
- Email sent on scraper failure (immediate)
- Email sent on heartbeat failure (hourly check)
- GitHub Actions notifications in Slack (optional setup)

## Local Testing

Test workflows locally with [act](https://github.com/nektos/act):

```bash
# Install act
brew install act  # macOS
# or: https://github.com/nektos/act#installation

# Test scraper workflow
act -j run-scrapers --secret-file .env

# Test frontend CI
act -j lint -W .github/workflows/frontend-ci.yml
```

## Troubleshooting

### Scraper cron not running
1. Check GitHub Actions tab for failed runs
2. Verify secrets are set correctly
3. Check Supabase service key has not expired
4. Review logs in failed workflow run

### Database migration failed
1. **DO NOT** re-run automatically
2. Review SQL syntax errors in logs
3. Test migration locally: `psql $SUPABASE_URL -f database/migrations/XXX.sql`
4. Fix and create new migration (never edit existing)

### E2E tests failing
1. Check Playwright browser installation
2. Verify test environment has network access
3. Review screenshots in workflow artifacts
4. Run locally: `pnpm test:e2e`

## Future Enhancements

- [ ] Add staging environment workflow
- [ ] Implement blue-green deployment for DB migrations
- [ ] Add performance benchmarking to frontend CI
- [ ] Set up automatic dependency updates (Dependabot)
- [ ] Add Slack notifications for failures
- [ ] Implement canary deployments for scrapers
