# Deployment Blockers (Updated 2026-02-16)

## Critical Blockers

### 1. Netlify Credit Exhaustion
- **Status:** **ACTIVE**
- **Impact:** All deployments (Production & Preview) are paused.
- **Resolution:** Wait for monthly credit reset (March 1, 2026).
- **Workaround:** Local verification (`npm run build && npm start`).

## Resolved Blockers
- **Mapbox Cost:** Mitigated by `scraper-cron` throttling (*/30).
- **Neon Transfer:** Mitigated by strict `heartbeat --max-age 90` limits.
