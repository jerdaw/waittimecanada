# Deployment Blockers (Updated 2026-04-24)

## Critical Blockers
- None currently active.

## Known Constraints
- **WaitTime Backend VPS Cutover:** Deferred. The frontend is live on the shared VPS, but the backend scheduler remains on GitHub Actions because the Ontario upstream is not reliably reachable from that VPS.

## Resolved Blockers
- **Custom Domain TLS / Redirect Validation:** `wait-time.ca` now presents a valid certificate, `www.wait-time.ca` redirects to the canonical host, and production smoke passes against the canonical URL.
- **Netlify Credit Exhaustion:** Resolved, but Netlify remains rollback-only
  for the frontend. The live deployment path is the shared VPS.
- **Mapbox / CI Cost Control:** Mitigated by the current hourly `scraper-cron` cadence plus targeted local verification before pushing.
- **Heartbeat Noise:** Resolved by state-change alerting with a `120` minute stale threshold instead of repeated duplicate stale/error notifications.
