# Operations Quick Start

This page covers safe local operations for contributors. Deployment details,
credentials, monitoring configuration, private operational notes, and
environment-specific production paths are intentionally excluded from public
documentation.

## Prerequisites

```bash
cd backend
python -m pip install "uv==0.11.23"
uv sync --locked --no-dev
export DATABASE_URL="postgresql://localhost:5432/waittimecanada"
```

Use a local or disposable PostgreSQL database for development and testing.

## Run Scrapers

```bash
uv run python -m waittime.cli.scraper --all
uv run python -m waittime.cli.scraper --source quebec-msss
uv run python -m waittime.cli.scraper --source ontario-health
uv run python -m waittime.cli.scraper --source alberta-ahs
uv run python -m waittime.cli.scraper --source bc-phsa
uv run python -m waittime.cli.scraper --all --dry-run
uv run python -m waittime.cli.scraper --list
```

## Check Source Freshness

```bash
uv run python -m waittime.cli.check_heartbeat --dry-run
uv run python -m waittime.cli.check_heartbeat --source quebec-msss --dry-run
uv run python -m waittime.cli.check_heartbeat --dry-run --verbose
```

## Common Issues

### `No module named 'waittime'`

```bash
cd backend
uv sync --locked --no-dev
```

### `DATABASE_URL` is not set

Set `DATABASE_URL` in the current shell before running backend commands. Do not
commit database connection strings or local env files.

### Playwright browsers not found

```bash
uv run playwright install chromium
```

## See Also

- Methodology documentation: `backend/docs/methodologies/`
- Data dictionary: `docs/reference/data-dictionary.md`
- Environment variables: `docs/reference/environment-variables.md`
