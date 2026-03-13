# Wait Time Backend Systemd Templates

These templates are meant to be installed onto the VPS under
`/etc/systemd/system/` for the Wait Time Canada backend worker path.

They assume:

1. release root: `/srv/apps/waittime-backend`
2. current symlink: `/srv/apps/waittime-backend/current`
3. backend working directory: `/srv/apps/waittime-backend/current/backend`
4. backend env file: `/etc/projects-merge/env/waittime-backend.env`
5. Playwright browser cache: `/srv/apps/waittime-backend/shared/playwright-browsers`

Installed timers:

1. `waittime-backend-scraper.timer`
   - runs all scrapers every 4 hours
2. `waittime-backend-heartbeat.timer`
   - checks scraper freshness every 30 minutes
3. `waittime-backend-quality-snapshot.timer`
   - writes daily quality snapshots and runs drift monitoring

Optional timer:

1. `waittime-backend-database-cleanup.timer`
   - weekly retention cleanup

Use the installer:

```bash
sudo ./scripts/install-vps-backend-systemd.sh --enable
```

To also enable the cleanup timer:

```bash
sudo ./scripts/install-vps-backend-systemd.sh --enable --enable-cleanup
```
