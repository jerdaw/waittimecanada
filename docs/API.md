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
- Shared anonymous read routes use short cache windows to reduce repeated Neon reads on the production VPS path.

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

## Public health resources

- `GET /api/resources?kind=facility|aed[&q=<term>&province=ON&latitude=<lat>&longitude=<lng>&radius=<km>&limit=<n>]`
- `GET /api/resources/alerts?limit=<n>`
- `GET /api/resources/aqhi?latitude=<lat>&longitude=<lng>`

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

## Response caching and transfer guardrails

These routes are intentionally cache-friendly on the public frontend path:

- `GET /api/health` and `GET /api/status`: 2-minute shared cache window
- `GET /api/hospitals`, `GET /api/resources`, `GET /api/resources/alerts`, `GET /api/data-quality`, `GET /api/anomalies`, `GET /api/compare`, `GET /api/analytics/benchmarks`, `GET /api/analytics/trends`, `GET /api/analytics/regions`, `GET /api/analytics/occupancy`, `GET /api/analytics/equity-summary`, and `GET /api/analytics/patterns`: 5-minute shared cache window
- `GET /api/methodology`: 1-minute shared cache window
- `GET /api/hospitals/[slug]/trends`: 10-minute shared cache window

Operational note:

- On the shared VPS runtime, these same read-heavy routes also use short-lived in-process response caching to cut repeat public transfer from Neon without changing data collection or storage policy.
- `GET /api/geolocation` and `GET /api/export` remain `Cache-Control: no-store`.
- `GET /api/resources/aqhi` uses a 15-minute shared cache window with a live upstream fetch behind the server cache.

## Health endpoint operational contract (M30)

`GET /api/health` remains backward-compatible and now includes structured scraper diagnostics.

Top-level fields:

- `healthy: boolean`
- `database: { status, latency_ms, pool_status }`
- `last_update: string | null`
- `stale_threshold_minutes: number`
- `sources: SourceHealth[]`

Operational note:

- The live stale threshold is currently `120` minutes, supplied by environment/config but exposed directly in the response so operators and clients can stay aligned.

Per-source diagnostics (`SourceHealth`) include:

- Existing: `source_id`, `source_name`, `last_run`, `status`, `error_message`, `measurements_count`, `age_minutes`
- Added: `last_success_run`, `last_success_measurements_count`, `last_error_run`, `last_error_category`, `last_error_stage`, `consecutive_failures`, `last_run_duration_ms`

Failure categories currently emitted by backend heartbeat/classification logic:

- `upstream_unavailable`
- `parser_breakage`
- `infra_runtime`
- `persistence_failure`
- `unknown`

## Status and data-quality KPI cadence (D12)

`GET /api/status` and the aggregate `GET /api/data-quality` view now compute
public KPI percentages against the active live scraper set only:

- `quebec-msss`
- `ontario-health`
- `alberta-ahs`
- `bc-phsa`

Operational note:

- these aggregate percentages now reflect the current hourly GitHub Actions
  scraper cadence (`24` expected runs/day), not the older 15-minute expectation
  model
- aggregate measurement counts are returned as actual counts, not reconstructed
  from percentage estimates
- historical `view=trend` / `view=diff` responses now include
  `historical_annotation` metadata when the requested snapshot range spans both
  the legacy 15-minute expectation model (`96` expected runs/day) and the
  current hourly model (`24` expected runs/day)
- the public `/data-quality` page renders that annotation directly instead of
  implying long-range snapshot comparability that the historical records do not
  fully support

## Comparability endpoint

`GET /api/compare` returns:

- `comparable: boolean`
- `divergence_brief: string | null`
- methodology fields for both hospitals

## Public health resource contracts

`GET /api/resources` returns:

- `success`
- `count`
- `data`
- `meta.kind`
- `meta.query`
- `meta.source_status`

`GET /api/resources/alerts` returns:

- `success`
- `count`
- `data`
- `meta.limit`
- `meta.source_status`

`GET /api/resources/aqhi` returns:

- `success`
- `data` (`AQHIRecord | null`)
- `meta.latitude`
- `meta.longitude`
- `meta.source_status`

Each `source_status` row includes:

- `source_id`
- `source_name`
- `provenance_url`
- `last_refreshed_at`
- `freshness_state` (`show | warn | suppress`)

Operational note:

- Facility rows are reference-directory data only and should not be interpreted as live operational availability.
- AED rows are OSM-backed fallback data and remain explicitly crowdsourced/incomplete.
- AQHI responses may intentionally return `data: null` when the upstream source freshness state is `suppress`.

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

## Analytics freshness notes

- `GET /api/analytics/patterns?type=hour_of_day` derives its hourly view from bounded raw measurements rather than precomputed hourly aggregates.
- `GET /api/export?granularity=hourly` is intended for bounded recent windows only and returns an error for oversized hourly requests.

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
