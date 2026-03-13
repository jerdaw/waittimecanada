# Direct VPS Backend Deployment

**Status:** Active migration target, not yet the live production scheduler path
**Last Updated:** 2026-03-13

This document defines the app-local deployment path for moving the Wait Time
Canada backend scheduler/runtime from GitHub Actions onto the shared VPS.

Shared-VPS ownership note:

1. Shared host topology, ingress ownership, release-root conventions, and live
   cross-project inventory are canonical in `/home/jer/repos/platform-ops`.
2. Use `/home/jer/repos/platform-ops/docs/standards/PLAT-009-shared-vps-documentation-boundary.md`
   for the documentation boundary.
3. This repo remains canonical for Wait Time Canada's backend packaging,
   scheduler units, deploy, verify, and rollback steps.

## Current State

As of 2026-03-13:

1. production scraper scheduling still runs on GitHub Actions
2. heartbeat monitoring still runs on GitHub Actions
3. the managed Neon database remains the production data plane
4. the direct-VPS backend path described here is the next deployment target, but it is not live until the VPS timers are installed, enabled, and verified

## Target Runtime Shape

The VPS target is a Python worker release with systemd timers:

1. release root: `/srv/apps/waittime-backend`
2. current symlink: `/srv/apps/waittime-backend/current`
3. backend working directory: `/srv/apps/waittime-backend/current/backend`
4. env file: `/etc/projects-merge/env/waittime-backend.env`
5. shared Playwright browser cache: `/srv/apps/waittime-backend/shared/playwright-browsers`
6. timers:
   - `waittime-backend-scraper.timer`
   - `waittime-backend-heartbeat.timer`
   - `waittime-backend-quality-snapshot.timer`
7. optional timer:
   - `waittime-backend-database-cleanup.timer`

The database remains managed in Neon for this wave.

## Required Env Contract

Required:

1. `DATABASE_URL`

Recommended:

1. `ENVIRONMENT=production`
2. `LOG_LEVEL=INFO`
3. `HEARTBEAT_STALE_THRESHOLD_MINUTES=250`
4. `ALERTS_ENABLED=true`
5. `PUSHOVER_USER_KEY`
6. `PUSHOVER_API_TOKEN`
7. `PLAYWRIGHT_BROWSERS_PATH=/srv/apps/waittime-backend/shared/playwright-browsers`

Optional:

1. `MAPBOX_TOKEN` for geocoding enrichment when new hospitals are discovered
2. `SENTRY_DSN`
3. `ALERTS_REFERENCE_URL` if alert notifications should point to a VPS-specific runbook or dashboard instead of the current GitHub Actions view

## Host Prerequisites

Install runtime dependencies on the VPS before the first backend deploy:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential
```

Playwright note:

1. the deploy script installs Chromium into the shared Playwright cache
2. the host still needs the Chromium runtime libraries that Playwright expects
3. if they are missing, run:

```bash
cd /srv/apps/waittime-backend/current/backend
PLAYWRIGHT_BROWSERS_PATH=/srv/apps/waittime-backend/shared/playwright-browsers \
  ./.venv/bin/playwright install --with-deps chromium
```

## Packaging Files

The direct-VPS backend path uses:

1. `scripts/deploy-vps-backend.sh`
2. `scripts/release-vps-backend.sh`
3. `scripts/install-vps-backend-systemd.sh`
4. `scripts/verify-vps-backend.sh`
5. `backend/systemd/`

## Local Preflight

Before preparing a backend release:

```bash
cd /home/jer/repos/waittimecanada/backend
python -m pytest tests/unit/test_scraper_cli.py \
  tests/unit/test_check_heartbeat_cli.py \
  tests/unit/test_cleanup_cli.py \
  tests/unit/test_snapshot_quality_cli.py
ruff check src tests
mypy src
```

## Deploy On The VPS

From the checked-out release on the VPS:

```bash
cd /srv/apps/waittime-backend/current
./scripts/deploy-vps-backend.sh /etc/projects-merge/env/waittime-backend.env
sudo ./scripts/install-vps-backend-systemd.sh --enable
```

The deploy script:

1. creates or refreshes `backend/.venv`
2. installs the backend package into that venv
3. installs Chromium into the shared Playwright cache
4. applies database migrations using the provided env file

The systemd installer:

1. installs the timer/service templates from `backend/systemd/`
2. substitutes the runtime user and group
3. reloads systemd
4. enables scraper, heartbeat, and quality snapshot timers
5. optionally enables the cleanup timer with `--enable-cleanup`

## Stage And Release From A Workstation

```bash
cd /home/jer/repos/waittimecanada
./scripts/release-vps-backend.sh user@your-vps --deploy
```

Defaults:

1. app root: `/srv/apps/waittime-backend`
2. env file: `/etc/projects-merge/env/waittime-backend.env`

## Verification

After deploy and timer installation:

```bash
sudo ./scripts/verify-vps-backend.sh
sudo systemctl list-timers 'waittime-backend-*' --all
sudo journalctl -u waittime-backend-scraper.service -n 50 --no-pager
sudo journalctl -u waittime-backend-heartbeat.service -n 50 --no-pager
```

Expected outcome:

1. scraper, heartbeat, and quality snapshot timers are enabled and active
2. the heartbeat dry-run completes successfully
3. recent scraper runs write fresh `scraper_status` rows
4. alerting is configured if `PUSHOVER_*` vars are present

## Rollback

Rollback is release-based:

1. identify the previous release in `/srv/apps/waittime-backend/releases`
2. repoint `/srv/apps/waittime-backend/current`
3. rerun `./scripts/deploy-vps-backend.sh /etc/projects-merge/env/waittime-backend.env`
4. reload systemd and restart the timers:

```bash
sudo systemctl daemon-reload
sudo systemctl restart \
  waittime-backend-scraper.timer \
  waittime-backend-heartbeat.timer \
  waittime-backend-quality-snapshot.timer
```

## Cutover Rule

Do not disable the GitHub Actions backend schedulers until:

1. the VPS scraper timer has completed successfully at least once
2. the heartbeat timer verifies fresh rows on the VPS path
3. rollback to GitHub Actions remains straightforward
