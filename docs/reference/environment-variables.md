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

## Frontend

Required:

- `NEXT_PUBLIC_MAPBOX_TOKEN`: Mapbox token for the map UI
- `DATABASE_URL`: database connection used by server-side API routes

Recommended:

- `NEXT_PUBLIC_BASE_URL`: canonical base URL for sitemap/robots/metadata (for example, `https://wait-time.ca`)
