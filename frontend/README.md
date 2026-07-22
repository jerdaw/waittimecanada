# Wait Time Canada Frontend

Next.js 15 App Router frontend for map visualization, methodology transparency, and analytics dashboards.

## Stack

- Next.js 15 + TypeScript
- Tailwind CSS
- React Map GL / Mapbox GL
- PostgreSQL client (`postgres`) for server routes
- Vitest + React Testing Library

## Setup

```bash
cd frontend
npm ci
cp .env.example .env.local
```

Required environment variables:

- `DATABASE_URL`
- `NEXT_PUBLIC_MAPBOX_TOKEN`

Optional:

- `NEXT_PUBLIC_BASE_URL`
- `DATABASE_SSL_MODE` (`require`, `disable`, `false`, `off`, or `0`)

Run local app:

```bash
npm run dev
```

Open `http://localhost:3000`.

## Scripts

```bash
npm run dev
npm run build
npm run start
npm run type-check
npm run lint
npm run format:check
npm run type-check:test
npm run test:unit
```

`npm run test:e2e` exists but is generally CI-only for this repo and is
normally run from GitHub Actions manual dispatch rather than as a routine local
check. It is not part of the default push/PR merge gate.

## Key Routes

Pages:

- `/` map + hospital list
- `/methods` methodology and comparability
- `/data-quality` quality and anomalies
- `/analytics` benchmarking, trends, regions, occupancy/equity insights
- `/resources` Ontario public-health resources, provenance, and source catalog
- `/faq`

API routes (selected):

- `/api/hospitals`
- `/api/hospitals/[slug]/trends`
- `/api/compare`
- `/api/data-quality`
- `/api/anomalies`
- `/api/analytics/benchmarks`
- `/api/analytics/trends`
- `/api/analytics/regions`
- `/api/analytics/patterns`
- `/api/analytics/occupancy`
- `/api/analytics/equity-summary`
- `/api/equity-layer`
- `/api/export`
- `/api/resources`
- `/api/resources/alerts`
- `/api/resources/system-context`
- `/api/resources/water-advisories`
- `/api/resources/aqhi`

## Notes

- Only verified + visible hospitals are shown publicly.
- Occupancy and equity routes include explicit availability states when source data is not ready.
- The equity layer now ships a real Ontario StatsCan-based geometry/metadata path; other provinces remain explicitly unavailable until equivalent source work is completed.
- `/resources` now keeps Ontario public-health access data provenance-first, including source-catalog metadata, analytics-only EMS context, and Ontario reserve-system water advisories.
- Production deployment details, rollback runbooks, monitoring configuration, and environment-specific host paths are intentionally excluded from public documentation.

## Runtime Usage Controls

- `SystemStatus` polls `/api/health` every 5 minutes and only while the browser tab is visible.
- The homepage server-renders database-derived national coverage, refreshes the selected province and coverage every 5 minutes while visible, and refreshes immediately when the tab becomes visible.
- Read-heavy API routes use shared cache headers from `frontend/utils/cache.ts`.
- Server-side routes can also use short-lived in-process response caching via `frontend/utils/server-cache.ts` for repeated anonymous reads.
- Typical cache windows:
  - `60s` in-process and `no-store` for `/api/health`
  - `300s` for hospitals, resources, data-quality, anomalies, compare, and analytics endpoints
  - `60s` for methodology change events
  - `600s` for hospital trend timelines
- Admin, geolocation, and export endpoints are explicitly `Cache-Control: no-store`.

## Related Docs

- `docs/API.md`
- `docs/architecture/api.md`
- `docs/planning/manual-tasks.md`
