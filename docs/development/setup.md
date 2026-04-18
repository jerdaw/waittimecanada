# Development Setup

This guide documents the supported local development workflow for Wait Time Canada.

## Prerequisites

- Python 3.12+
- Node.js 22+
- npm
- Neon PostgreSQL connection string (`DATABASE_URL`)
- Mapbox public token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

## Recommended Hosted Database

The default documented database path for this project is Neon PostgreSQL:

1. create a Neon project
2. copy the pooled Postgres connection string
3. export it in your shell as `DATABASE_URL` before backend commands

The application and migrations use standard Postgres, so this remains portable,
but Neon is the supported quick-start path.

## 1. Clone and Configure Environment Files

```bash
git clone https://github.com/jerdaw/waittimecanada.git
cd waittimecanada

cp frontend/.env.example frontend/.env.local
export DATABASE_URL="postgresql://user:pass@host:5432/dbname" # pragma: allowlist secret
```

Populate required frontend values in `frontend/.env.local`. The backend runtime
reads `DATABASE_URL` from the process environment directly; `backend/.env.local`
is optional as a personal template only.

## 2. Python Environment and Backend Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'
```

If you are already inside `backend/`, use:

```bash
python -m pip install -e '.[dev]'
```

## 3. Frontend Dependencies

```bash
cd frontend
npm install
cd ..
```

## 4. Database Migrations and Analytics Bootstrap

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
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
python -m pytest backend/tests

# Backend quality
ruff check backend/src backend/tests
ruff format backend/src backend/tests
mypy backend/src

# Frontend quality
cd frontend
npm run type-check
npm run lint
npm run test:unit

# Docs quality (run from repo root)
bash scripts/check-docs.sh
```

## Troubleshooting Notes

- `zsh: no matches found: backend[dev]`:
  use single quotes: `python -m pip install -e 'backend[dev]'`.
- Analytics regions setup warnings on `/analytics`:
  run `python -m waittime.cli.bootstrap_analytics --days 180`.
- Missing map rendering:
  confirm `NEXT_PUBLIC_MAPBOX_TOKEN` is set in `frontend/.env.local`.
