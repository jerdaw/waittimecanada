# Wait Time Canada Frontend

Next.js 14 App Router frontend for map visualization, methodology transparency, and analytics dashboards.

## Stack

- Next.js 14 + TypeScript
- Tailwind CSS
- React Map GL / Mapbox GL
- PostgreSQL client (`postgres`) for server routes
- Vitest + React Testing Library

## Setup

```bash
cd frontend
npm install
cp .env.example .env.local
```

Required environment variables:

- `DATABASE_URL`
- `NEXT_PUBLIC_MAPBOX_TOKEN`

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
npm run test:unit
```

`npm run test:e2e` exists but is generally CI-only for this repo and is
normally run from GitHub Actions manual dispatch rather than as a routine local
check.

## Key Routes

Pages:

- `/` map + hospital list
- `/methods` methodology and comparability
- `/data-quality` quality and anomalies
- `/analytics` benchmarking, trends, regions, occupancy/equity insights
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

## Notes

- Only verified + visible hospitals are shown publicly.
- Occupancy and equity routes include explicit availability states when source data is not ready.
- Map layer equity geometry is scaffolded placeholder data until StatsCan integration is completed.
- The direct-VPS frontend packaging path is `frontend/Dockerfile`; service-local deploy and rollback steps live in `docs/operations/direct-vps-frontend.md`.
- The backend worker/timer migration path is documented separately in `docs/operations/direct-vps-backend.md`.
- The production frontend now runs on the shared VPS at `https://wait-time.ca`.

## Netlify Deploy Guard

This repo is configured to avoid accidental Netlify credit burn:

- `frontend/netlify.toml` uses `frontend/scripts/netlify-ignore.sh` as the build ignore rule.
- Non-production branches are skipped by default.
- Production branch builds require explicit release intent via commit message containing `[release]` or `[deploy]`.
- This prevents new accidental usage while keeping the old Netlify path available as rollback-only infrastructure.

Example release commit:

```bash
git commit -m "[release] deploy milestone 15 analytics update"
git push origin main
```

## Runtime Usage Controls

- `SystemStatus` polls `/api/health` every 5 minutes (not every minute) and only while the browser tab is visible.
- Read-heavy API routes use shared cache headers from `frontend/utils/cache.ts`.
- The direct-VPS runtime also applies short-lived in-process response caching via `frontend/utils/server-cache.ts` for repeated anonymous reads.
- Typical cache windows:
  - `120s` for `/api/health`
  - `300s` for hospitals, resources, data-quality, anomalies, compare, and analytics endpoints
  - `60s` for methodology change events
  - `600s` for hospital trend timelines
- Admin, geolocation, and export endpoints are explicitly `Cache-Control: no-store`.

## Related Docs

- `docs/API.md`
- `docs/architecture/api.md`
- `docs/planning/manual-tasks.md`
