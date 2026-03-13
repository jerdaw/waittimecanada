# Wait Time Canada API Reference

## Overview

Wait Time Canada APIs are served from Next.js route handlers in `frontend/app/api/`.

Base URL:

- Local: `http://localhost:3000/api`
- Production: `<PRODUCTION_BASE_URL>/api` (when deployed)

## Conventions

- Most routes use JSON responses.
- Many routes return `{ success, data }` for success and `{ success: false, error, message }` for errors.
- Some older routes use payload-first contracts (kept for compatibility).

## Endpoint Catalog

## Hospitals and comparability

- `GET /api/hospitals?province=ON`
- `GET /api/hospitals/[slug]/trends?period=24h|7d|30d|90d|6m|1y`
- `GET /api/compare?a=<hospital_id>&b=<hospital_id>`

## System and data quality

- `GET /api/health`
- `GET /api/data-quality?hospital_id=<id>&days=30`
- `GET /api/anomalies?source_id=<source_id>&days=7`

## Analytics

- `GET /api/analytics/benchmarks?province=ON&period=24h|7d|30d[&hospital_id=<id>]`
- `GET /api/analytics/trends?province=ON&period=weekly|monthly&lookback=3m|6m|1y`
- `GET /api/analytics/regions?province=ON&period=24h|7d|30d`
- `GET /api/analytics/patterns?hospital_id=<id>&type=hour_of_day|day_of_week|monthly`
- `GET /api/analytics/occupancy?province=ON`
- `GET /api/analytics/equity-summary?province=ON&period=24h|7d|30d`

## Equity layer

- `GET /api/equity-layer?province=ON`

## Export

- `GET /api/export?format=csv|json&granularity=raw|hourly|daily|weekly|monthly`
  - `granularity=hourly` is derived from raw measurements and limited to 30-day windows

Additional optional export params:

- `province`
- `start_date`
- `end_date`
- `include_methodology=true|false`

## Geolocation

- `GET /api/geolocation`

## Admin verification

- `GET /api/admin/hospitals/unverified`
- `POST /api/admin/hospitals/[id]/verify`
- `DELETE /api/admin/hospitals/[id]/verify`

## Key Contracts

## Health endpoint operational contract (M30)

`GET /api/health` remains backward-compatible and now includes structured scraper diagnostics.

Top-level fields:

- `healthy: boolean`
- `database: { status, latency_ms, pool_status }`
- `last_update: string | null`
- `stale_threshold_minutes: number`
- `sources: SourceHealth[]`

Per-source diagnostics (`SourceHealth`) include:

- Existing: `source_id`, `source_name`, `last_run`, `status`, `error_message`, `measurements_count`, `age_minutes`
- Added: `last_success_run`, `last_success_measurements_count`, `last_error_run`, `last_error_category`, `last_error_stage`, `consecutive_failures`, `last_run_duration_ms`

Failure categories currently emitted by backend heartbeat/classification logic:

- `upstream_unavailable`
- `parser_breakage`
- `infra_runtime`
- `persistence_failure`
- `unknown`

## Comparability endpoint

`GET /api/compare` returns:

- `comparable: boolean`
- `divergence_brief: string | null`
- methodology fields for both hospitals

## Occupancy availability contract

`GET /api/analytics/occupancy` returns one of:

- `status: "available"`
- `status: "no_reporting_data"`
- `status: "not_available_yet"`

This ensures missing source fields are explicit, not silently treated as zero.

## Equity availability contract

`GET /api/analytics/equity-summary` returns one of:

- `status: "ready"`
- `status: "no_reporting_data"`
- `status: "not_available_yet"`

When `status: "ready"`, the payload also includes:

- `sensitivity_analysis` (threshold table, default 10/20/30/40 km)
- `uncertainty` (bootstrap percentile 95% intervals, descriptive only)
- `methodology` metadata including:
  - `interpretation: "descriptive_association_only"`
  - `causal_inference: false`
  - `census_income_reference_year`
  - `wait_aggregation_period`
  - temporal alignment note

`GET /api/equity-layer` returns setup guidance when province data is not scaffolded yet, and for successful ON responses includes metadata:

- `reference_year`
- `interpretation`
- `causal_inference`
- `temporal_alignment_note`
- `source_file`
- `optimized_geometry`

Layer loading behavior is optimized-first with canonical fallback:

1. `ontario-equity-layer.optimized.geojson` (preferred when present)
2. `ontario-equity-layer.geojson` (fallback)

## Example Requests

```bash
# Hospitals in Ontario
curl "http://localhost:3000/api/hospitals?province=ON"

# Compare two hospitals
curl "http://localhost:3000/api/compare?a=ca-on-ottawa-general&b=ca-qc-chum"

# Benchmarks
curl "http://localhost:3000/api/analytics/benchmarks?province=ON&period=7d"

# Province trend
curl "http://localhost:3000/api/analytics/trends?province=ON&period=monthly&lookback=6m"

# Regions
curl "http://localhost:3000/api/analytics/regions?province=ON&period=7d"

# Export aggregated monthly data
curl "http://localhost:3000/api/export?format=json&granularity=monthly&province=ON"
```

## Data Use and Interpretation

- Use methodology tags when interpreting or comparing hospitals.
- Do not interpret cross-province comparisons as directly comparable unless ontology dimensions match.
- This platform is informational and operational; it is not a triage or medical advice service.
