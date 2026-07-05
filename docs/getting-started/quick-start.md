# Quick Start

This guide is for local development only. Production deployment details,
credentials, monitoring configuration, and environment-specific host paths are
intentionally excluded from public documentation.

## 1. Prerequisites

- Python 3.12+
- Node.js 22+
- npm
- PostgreSQL `DATABASE_URL`
- Mapbox token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

## 2. Create a PostgreSQL Database

1. Create or provision a PostgreSQL database.
2. Copy the connection string.
3. Export that value in your shell as `DATABASE_URL`.

Wait Time Canada uses standard PostgreSQL migrations, so the schema remains
portable across compatible Postgres environments.

## 3. Initialize Local Environment

```bash
cp frontend/.env.example frontend/.env.local
export DATABASE_URL="postgresql://user:pass@host:5432/dbname" # pragma: allowlist secret
```

Populate required frontend values in `frontend/.env.local`. The backend runtime
expects `DATABASE_URL` in the process environment and does not auto-load local
env files.

## 4. Install Backend + Frontend Dependencies

```bash
cd backend
python -m pip install "uv==0.11.23"
uv sync --locked --extra dev
cd ..

cd frontend
npm ci
cd ..
```

## 5. Apply Migrations and Seed Analytics Prereqs

```bash
cd backend
uv run python run_migrations.py
uv run python -m waittime.cli.bootstrap_analytics --days 180
cd ..
```

## 6. Start the App

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## 7. Optional Validation

```bash
# Frontend
cd frontend
npm run type-check
npm run lint
npm run test:unit

# Backend
cd ..
cd backend
uv run pytest tests
```
