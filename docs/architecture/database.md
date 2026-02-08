# Database Architecture

## Overview

- Engine: PostgreSQL (Neon)
- Migration source: `backend/migrations/`
- Core strategy: strict ontology metadata + verifiable provenance + aggregate summaries

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

## Analytics and quality extensions

- `measurement_aggregates` (`006_create_measurement_aggregates.sql`)
- `data_quality_snapshots` (`007_create_data_quality_snapshots.sql`)
- anomaly flags on `measurements` (`008_add_anomaly_columns.sql`)
- `methodology_change_events` (`009_create_methodology_change_events.sql`)
- `regions` and `hospital_regions` (`010_create_regions_tables.sql`)

## Data Model Rules

- Do not normalize incompatible methodologies into a single synthetic metric.
- Use ontology tags to drive comparability logic.
- Keep verification gate: new hospitals are not auto-published.
- Store payload hash/snippet, not full source HTML.

## Migration and Bootstrap

Primary commands:

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
```

`bootstrap_analytics` applies migrations (idempotent), seeds regional mappings, and backfills aggregates.

## Query Patterns

- Map and list views pull latest measurement per hospital.
- Trends and benchmarks prefer aggregate tables (`measurement_aggregates`).
- Data quality and anomalies rely on quality snapshot + anomaly flags.
- Region analytics depend on `regions` + `hospital_regions` mapping coverage.

## References

- API architecture: `docs/architecture/api.md`
- Public API contracts: `docs/API.md`
- Roadmap status: `docs/planning/roadmap.md`
