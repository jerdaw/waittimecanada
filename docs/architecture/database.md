# Database Architecture

## Overview

- Engine: PostgreSQL
- Migration source: `backend/migrations/`
- Core strategy: strict ontology metadata + verifiable provenance + 30-day raw retention + permanent aggregate summaries

## Schema Components

## Ontology enums

Created in `001_create_enums.sql`:

- `metric_family_enum`
- `start_event_enum`
- `end_event_enum`
- `statistic_type_enum`
- `patient_scope_enum`
- `scraper_status_enum`

## Core operational tables

From `002_create_tables.sql`:

- `sources`: provincial source metadata + telehealth routing metadata
- `hospitals`: facility metadata with verification/visibility gates
- `measurements`: raw wait measurements + ontology tags + payload hash/snippet
- `scraper_status`: heartbeat and scraper execution status
- `scraper_alert_state`: current per-source incident state for stale/error deduplication and recovery tracking

## Analytics and quality extensions

- `measurement_aggregates` (`006_create_measurement_aggregates.sql`)
- `data_quality_snapshots` (`007_create_data_quality_snapshots.sql`)
- anomaly flags on `measurements` (`008_add_anomaly_columns.sql`)
- `methodology_change_events` (`009_create_methodology_change_events.sql`)
- `regions` and `hospital_regions` (`010_create_regions_tables.sql`)
- scraper observability metadata on `scraper_status` (`013_add_scraper_observability_columns.sql`)
- public-health-hub tables (`018_create_public_health_hub_tables.sql`)
- public-health-hub alert-state tracking (`019_add_public_health_source_alert_state.sql`)

## Scraper observability fields (M30)

`scraper_status` now persists both last-known-good and structured failure state:

- last success: `last_success_run`, `last_success_measurements_count`
- last error: `last_error_run`, `last_error_category`, `last_error_stage`, `error_message`
- reliability state: `consecutive_failures`, `last_run_duration_ms`

These fields support deterministic triage in `check_heartbeat --verbose`, workflow alerts, and `/api/health`.

## Alert state tracking

`scraper_alert_state` stores at most one active operational incident per source:

- `active_incident_kind` (`stale` or `error`)
- `active_incident_fingerprint`
- `opened_at`
- `last_notified_at`
- `last_resolved_at`

This lets the heartbeat monitor send one incident alert when a source becomes unhealthy and one recovery notice when it returns to healthy, instead of repeating the same alert every run.

## Public health hub tables

The Ontario-first `/resources` module now uses five dedicated database tables:

- `public_data_sources`: source metadata, provenance, legal posture, and last refresh timestamps
- `resource_locations`: normalized `facility` and `aed` rows for public search/map use
- `public_health_alerts`: normalized Health Canada recall and safety alert items
- `public_health_system_metrics`: analytics-only Ontario EMS system-context rows for `/resources/system-context`
- `public_health_source_alert_state`: incident deduplication state for hard-fail public-health ingest sources

These tables are operationally separate from the wait-time observatory schema.
AQHI and the ISC drinking-water advisory layer remain live-proxied and are
intentionally not persisted in the database. The source catalog metadata
exposed by `/resources`, `/api/resources/alerts`, and
`/api/resources/system-context` is DB-backed; the live-proxied `/api/resources/aqhi`
and `/api/resources/water-advisories` routes ship the equivalent source
metadata contract directly from the route layer.

## Data Model Rules

- Do not normalize incompatible methodologies into a single synthetic metric.
- Use ontology tags to drive comparability logic.
- Keep verification gate: new hospitals are not auto-published.
- Store payload hash/snippet, not full source HTML.
- Delete raw measurements older than 30 days via bounded cleanup runs; trigger aggregate refresh separately when needed.

## Migration and Bootstrap

Primary commands:

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
```

`bootstrap_analytics` applies migrations (idempotent), seeds regional mappings, and backfills aggregates.

## Query Patterns

- Map and list views pull latest measurement per hospital.
- Trends and benchmarks prefer aggregate tables (`measurement_aggregates`) for daily/weekly/monthly views.
- Intra-day patterns and bounded hourly exports derive from raw `measurements` for fidelity.
- Data quality and anomalies rely on quality snapshot + anomaly flags.
- Region analytics depend on `regions` + `hospital_regions` mapping coverage.

## References

- API architecture: `docs/architecture/api.md`
- Public API contracts: `docs/API.md`
- Roadmap status: `docs/planning/roadmap.md`
