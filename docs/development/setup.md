# Development Setup

This guide documents the supported local development workflow for Wait Time Canada.

## Prerequisites

- Python 3.12+
- Node.js 22+
- npm
- PostgreSQL connection string (`DATABASE_URL`)
- Mapbox public token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

## Recommended Database

The documented database path for this project is standard PostgreSQL:

1. create or choose a PostgreSQL database for development
2. copy the connection string
3. export it in your shell as `DATABASE_URL` before backend commands

The application and migrations use standard PostgreSQL features, so local and
hosted development databases are both supported.

## 1. Clone and Configure Environment Files

```bash
git clone https://github.com/jerdaw/waittimecanada.git
cd waittimecanada

cp frontend/.env.example frontend/.env.local
export DATABASE_URL="postgresql://user:pass@host:5432/dbname" # pragma: allowlist secret
```

Populate required frontend values in `frontend/.env.local`. The backend runtime
reads `DATABASE_URL` from the process environment directly and does not
auto-load local env files.

## 2. Python Environment and Backend Dependencies

```bash
cd backend
python -m pip install "uv==0.11.23"
uv sync --locked --extra dev
cd ..
```

For runtime-only installs, use:

```bash
cd backend
uv sync --locked --no-dev
cd ..
```

## 3. Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## 4. Database Migrations and Analytics Bootstrap

```bash
cd backend
uv run python run_migrations.py
uv run python -m waittime.cli.bootstrap_analytics --days 180
cd ..
```

## 5. Run the App

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Common Dev Commands

```bash
# Backend tests
cd backend
uv run pytest tests

# Backend quality
uv run ruff check src tests scripts
uv run ruff format src tests scripts
uv run mypy src
uv run python scripts/check_migration_sequence.py

# Frontend quality
cd frontend
npm run type-check
npm run type-check:test
npm run lint
npm run test:unit

# Docs quality (run from repo root)
bash scripts/check-docs.sh
```

## Troubleshooting Notes

- `uv sync --locked` fails after dependency edits:
  refresh `backend/uv.lock` intentionally and include that lockfile change.
- Analytics regions setup warnings on `/analytics`:
  run `uv run python -m waittime.cli.bootstrap_analytics --days 180` from `backend/`.
- Missing map rendering:
  confirm `NEXT_PUBLIC_MAPBOX_TOKEN` is set in `frontend/.env.local`.
