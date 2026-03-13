# Environment Variables

This project uses environment variables for local development and CI.

## Rules

- Never commit secrets.
- Use the example files as templates:
  - Backend: `backend/.env.example`
  - Frontend: `frontend/.env.example`

## Backend

Required:

- `DATABASE_URL`: Neon PostgreSQL connection string

Optional:

- `MAPBOX_TOKEN`: secret Mapbox token for backend geocoding
- `SENTRY_DSN`: error tracking (optional)
- `ENVIRONMENT`: `development` or `production`
- `LOG_LEVEL`: logging level
- `HEARTBEAT_STALE_THRESHOLD_MINUTES`: backend heartbeat/health threshold override
- `ALERTS_ENABLED`: set to `false` to suppress Pushover sends
- `PUSHOVER_USER_KEY`: Pushover user key for scraper alerts
- `PUSHOVER_API_TOKEN`: Pushover API token for scraper alerts
- `ALERTS_REFERENCE_URL`: optional alert deep link override; defaults to the current GitHub Actions view unless you point it at the VPS runbook or another operator URL
- `PLAYWRIGHT_BROWSERS_PATH`: shared Chromium cache path for VPS timers

## Frontend

Required:

- `NEXT_PUBLIC_MAPBOX_TOKEN`: Mapbox token for the map UI
- `DATABASE_URL`: database connection used by server-side API routes

Recommended:

- `NEXT_PUBLIC_BASE_URL`: canonical base URL for sitemap/robots/metadata (for example, `https://wait-time.ca`)
- `HEARTBEAT_STALE_THRESHOLD_MINUTES`: health endpoint stale threshold override for production/VPS runtime checks

Deployment notes:

- `NEXT_PUBLIC_MAPBOX_TOKEN` must be present at image build time for the direct-VPS frontend container.
- `NEXT_PUBLIC_BASE_URL` should be set explicitly in production so metadata, robots, and sitemap output stay canonical after cutover.
- The direct-VPS backend worker path expects its own env file at `/etc/projects-merge/env/waittime-backend.env`.
