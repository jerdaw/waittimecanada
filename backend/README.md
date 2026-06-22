# Wait Time Canada Backend

Python backend for scraping, ontology enforcement, aggregation, and operational health checks.

## Stack

- Python 3.12+
- PostgreSQL
- `psycopg2-binary`, `pydantic`, `structlog`, `tenacity`
- `uv`, `pytest`, `ruff`, `mypy`

## Setup

From repository root:

```bash
cd backend
python -m pip install "uv==0.11.23"
uv sync --locked --extra dev
```

For runtime-only installs, omit the dev extra:

```bash
uv sync --locked --no-dev
```

Required backend runtime configuration:

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname" # pragma: allowlist secret
```

The backend runtime reads it from the current process environment rather than
auto-loading `.env.local`.

## Database Initialization

```bash
uv run python run_migrations.py
uv run python -m waittime.cli.bootstrap_analytics --days 180
```

## Core CLI Commands

```bash
# List scraper sources
uv run python -m waittime.cli.scraper --list

# Run all scrapers
uv run python -m waittime.cli.scraper --all

# Run one scraper
uv run python -m waittime.cli.scraper --source ontario-health

# Heartbeat check
uv run python -m waittime.cli.check_heartbeat --max-age 120

# Seed source/hospital data
uv run python -m waittime.cli.seed_sources data/sources/ontario-health.json
uv run python -m waittime.cli.seed data/hospitals/ontario-seed.json

# Region mapping audit / auto-assign
uv run python -m waittime.cli.region_mapping --province ON
uv run python -m waittime.cli.region_mapping --province ON --auto-assign

# Public-health-hub ingest/status
uv run python -m waittime.cli.seed_public_health_resources --fetch-mohserlo-live
uv run python -m waittime.cli.seed_public_health_system_context --fetch-live
uv run python -m waittime.cli.public_health_hub_status --format markdown
```

## Testing and Quality

```bash
# All backend tests
uv run pytest tests

# Unit only
uv run pytest -m unit tests

# Lint / format / typing
uv run ruff check src tests scripts
uv run ruff format src tests scripts
uv run mypy src
uv run python scripts/check_migration_sequence.py
```

## Schema Highlights

Primary tables:

- `sources`
- `hospitals`
- `measurements`
- `scraper_status`
- `scraper_alert_state`
- `measurement_aggregates`
- `data_quality_snapshots`
- `methodology_change_events`
- `regions`
- `hospital_regions`
- `public_data_sources`
- `resource_locations`
- `public_health_alerts`
- `public_health_system_metrics`
- `public_health_source_alert_state`

Migrations live in `backend/migrations/`.

## Related Docs

- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/planning/roadmap.md`
- `docs/adr/0002-metric-ontology.md`
- `docs/operations/QUICK_START.md`
- `docs/operations/scraper-scheduling.md`
