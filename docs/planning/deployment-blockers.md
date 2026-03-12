# Deployment Blockers (Updated 2026-03-12)

## Critical Blockers

### 1. Custom Domain TLS / Redirect Validation
- **Status:** **ACTIVE**
- **Impact:** `wait-time.ca` serves the app but presents the default Netlify certificate instead of a certificate valid for `wait-time.ca`, so the canonical production URL is not launch-ready.
- **Resolution:** Complete Netlify custom-domain validation for `wait-time.ca` / `www.wait-time.ca`, reissue the certificate if needed, and rerun production smoke + redirect checks.
- **Workaround:** Use the verified Netlify deployment URL `https://earnest-pavlova-73674e.netlify.app` for smoke checks and temporary demo sharing.

## Resolved Blockers
- **Netlify Credit Exhaustion:** Netlify deployments are active again.
- **Mapbox Cost:** Mitigated by `scraper-cron` throttling (`0 */4 * * *` temporary cadence).
- **Neon Transfer:** Mitigated by strict `heartbeat --max-age 250` limits.
