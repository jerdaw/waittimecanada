# Deployment Blockers (Updated 2026-03-12)

## Critical Blockers
- None currently active.

## Resolved Blockers
- **Custom Domain TLS / Redirect Validation:** `wait-time.ca` now presents a valid certificate, `www.wait-time.ca` redirects to the canonical host, and production smoke passes against the canonical URL.
- **Netlify Credit Exhaustion:** Netlify deployments are active again.
- **Mapbox Cost:** Mitigated by `scraper-cron` throttling (`0 */4 * * *` temporary cadence).
- **Neon Transfer:** Mitigated by strict `heartbeat --max-age 250` limits.
