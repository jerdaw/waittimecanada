# API Architecture

## Overview

Wait Time Canada exposes server-side API routes through Next.js (`frontend/app/api/**`).

Characteristics:

- Read-heavy API surface for map + analytics consumption
- PostgreSQL queries executed server-side via `frontend/utils/db.ts`
- JSON responses with explicit success/error contracts
- Availability-state contracts where source data is incomplete (occupancy/equity)

## Route Groups

## Core hospital and comparison

- `GET /api/hospitals`
- `GET /api/hospitals/[slug]/trends`
- `GET /api/compare`
- `GET /api/geolocation`
- `GET /api/health`

## Quality and anomalies

- `GET /api/data-quality`
- `GET /api/anomalies`

## Analytics

- `GET /api/analytics/benchmarks`
- `GET /api/analytics/trends`
- `GET /api/analytics/regions`
- `GET /api/analytics/patterns`
- `GET /api/analytics/occupancy`
- `GET /api/analytics/equity-summary`

## Equity layer

- `GET /api/equity-layer`

## Export

- `GET /api/export`

## Response Patterns

## Success pattern

```json
{
  "success": true,
  "data": {}
}
```

Some legacy routes return payload-first structures without top-level `success`; this is being kept for backward compatibility.

## Error pattern

```json
{
  "success": false,
  "error": "Invalid period",
  "message": "Supported period values: 24h, 7d, 30d"
}
```

## Availability-state contracts

Certain analytics endpoints return explicit states instead of silent nulls:

- Occupancy: `available | no_reporting_data | not_available_yet`
- Equity summary: `ready | no_reporting_data | not_available_yet`

This avoids overclaiming when source fields or tract datasets are not yet integrated.

## Health route contract (M30 operational visibility)

`GET /api/health` exposes an additive operational contract for scraper triage:

- `stale_threshold_minutes` to keep frontend status logic aligned with ops policy.
- Per-source `last_success_*` fields for last-known-good visibility.
- Per-source `last_error_*` fields (timestamp/category/stage) for failure triage.
- `consecutive_failures` and `last_run_duration_ms` for alert sensitivity and runtime monitoring.

Route compatibility rules:

- Existing fields are preserved.
- New fields are additive only.
- Unknown/empty states remain explicit (`null` or `unknown`), never inferred as success.

## Equity contract notes (M29)

- `GET /api/analytics/equity-summary` emits descriptive-only methodology metadata and uncertainty/sensitivity fields.
- `GET /api/equity-layer` emits reference-year and interpretation metadata.
- Equity layer loading is optimized-first:
  - `ontario-equity-layer.optimized.geojson` preferred
  - canonical `ontario-equity-layer.geojson` fallback

## Data Flow

1. Frontend component requests Next API route.
2. Route validates parameters and queries Neon.
3. Route computes derived summaries where needed (e.g., percentiles, trends, linkage).
4. UI renders with explicit states (loading/success/setup-needed/error).

Analytics implementation note:

- `hour_of_day` patterns and bounded hourly exports derive from raw `measurements` for fidelity.
- Daily/weekly/monthly analytics continue to prefer `measurement_aggregates`.

## Related References

- Public endpoint contract details: `docs/API.md`
- Database schema and migrations: `docs/architecture/database.md`
- Workflow operations: `.github/workflows/README.md`
