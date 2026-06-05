# Environment Variables

This project uses environment variables for local development and CI.

## Rules

- Never commit secrets.
- Use the example files as templates:
  - Backend: `backend/.env.example`
  - Frontend: `frontend/.env.example`

## Backend

Required:

- `DATABASE_URL`: PostgreSQL connection string

Backend runtime note:

- Backend services and CLI commands read `DATABASE_URL` from the current
  process environment directly.
- `backend/.env.local` may still be used as a personal template or by
  human-invoked tooling that explicitly sources it, but backend runtime code
  does not auto-load secret env files.

Optional:

- `MAPBOX_TOKEN`: secret Mapbox token for backend geocoding
- `SENTRY_DSN`: error tracking (optional)
- `ENVIRONMENT`: `development` or `production`
- `LOG_LEVEL`: logging level
- `HEARTBEAT_STALE_THRESHOLD_MINUTES`: backend heartbeat/health threshold override
- `ALERT_API_URL`: optional notification provider endpoint
- `ALERT_USER_KEY`: optional notification recipient/user key
- `ALERT_API_TOKEN`: optional notification provider token
- `ALERTS_ENABLED`: set to `false` to suppress outbound operational notifications
- `ALERTS_REFERENCE_URL`: optional alert deep link override for operator-facing context
- `PLAYWRIGHT_BROWSERS_PATH`: optional shared Chromium cache path for scheduled browser-based jobs

## Frontend

Required:

- `NEXT_PUBLIC_MAPBOX_TOKEN`: Mapbox token for the map UI
- `DATABASE_URL`: database connection used by server-side API routes

Recommended:

- `NEXT_PUBLIC_BASE_URL`: canonical base URL for sitemap/robots/metadata (for example, `https://wait-time.ca`)
- `HEARTBEAT_STALE_THRESHOLD_MINUTES`: health endpoint stale threshold override

Deployment notes:

- `NEXT_PUBLIC_MAPBOX_TOKEN` must be present when building frontend assets that render the map.
- `NEXT_PUBLIC_BASE_URL` should be set explicitly in production so metadata, robots, and sitemap output stay canonical.
- Environment-specific deployment files, host paths, and alerting credentials are intentionally excluded from public documentation.
