# Wait Time Canada Backend

Python backend for scraping, ontology enforcement, aggregation, and operational health checks.

## Stack

- Python 3.12+
- Neon PostgreSQL
- `psycopg2-binary`, `pydantic`, `structlog`, `tenacity`
- `pytest`, `ruff`, `mypy`

## Setup

From repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'
```

From `backend/` directly:

```bash
python -m pip install -e '.[dev]'
```

Create local env file:

```bash
cp backend/.env.example backend/.env.local
```

Required env var: `DATABASE_URL`.

## Database Initialization

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
```

## Core CLI Commands

```bash
# List scraper sources
python -m waittime.cli.scraper --list

# Run all scrapers
python -m waittime.cli.scraper --all

# Run one scraper
python -m waittime.cli.scraper --source ontario-health

# Heartbeat check
python -m waittime.cli.check_heartbeat --max-age 60

# Seed source/hospital data
python -m waittime.cli.seed_sources backend/data/sources/ontario-health.json
python -m waittime.cli.seed backend/data/hospitals/ontario-seed.json

# Region mapping audit / auto-assign
python -m waittime.cli.region_mapping --province ON
python -m waittime.cli.region_mapping --province ON --auto-assign
```

## Testing and Quality

```bash
# All backend tests
python -m pytest backend/tests

# Unit only
python -m pytest -m unit backend/tests

# Lint / format / typing
ruff check backend/src backend/tests
ruff format backend/src backend/tests
mypy backend/src
```

## Schema Highlights

Primary tables:

- `sources`
- `hospitals`
- `measurements`
- `scraper_status`
- `measurement_aggregates`
- `data_quality_snapshots`
- `methodology_change_events`
- `regions`
- `hospital_regions`

Migrations live in `backend/migrations/`.

## Related Docs

- `docs/architecture/database.md`
- `docs/architecture/api.md`
- `docs/planning/roadmap.md`
- `docs/adr/0002-metric-ontology.md`
- `docs/operations/direct-vps-backend.md`
- `backend/systemd/README.md`
