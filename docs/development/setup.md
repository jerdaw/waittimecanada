# Development Setup

This guide documents the supported local development workflow for WaitTime Canada.

## Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Neon PostgreSQL connection string (`DATABASE_URL`)
- Mapbox public token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

## 1. Clone and Configure Environment Files

```bash
git clone https://github.com/jerdaw/waittimecanada.git
cd waittimecanada

cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

Populate required values in both files.

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
