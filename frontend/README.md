# WaitTime Canada Frontend

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

`npm run test:e2e` exists but is generally CI-only for this repo.

## Key Routes

Pages:

- `/` map + hospital list
- `/methods` methodology and comparability
- `/data-quality` quality and anomalies
- `/analytics` benchmarking, trends, regions, occupancy/equity insights
- `/faq`
- `/admin/verify`

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

## Related Docs

- `docs/API.md`
- `docs/architecture/api.md`
- `docs/planning/manual-tasks.md`
