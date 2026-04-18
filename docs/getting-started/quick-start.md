# Quick Start

## 1. Prerequisites

- Python 3.12+
- Node.js 22+
- npm
- Neon `DATABASE_URL`
- Mapbox token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

## 2. Create a Neon Database

1. Create a Neon project.
2. Copy the project's pooled Postgres connection string.
3. Export that value in your shell as `DATABASE_URL`.

Wait Time Canada uses standard PostgreSQL migrations, so Neon is the default
hosted path, but the schema remains portable to other Postgres environments.

## 3. Initialize Local Environment

```bash
cp frontend/.env.example frontend/.env.local
export DATABASE_URL="postgresql://user:pass@host:5432/dbname" # pragma: allowlist secret
```

Populate required frontend values in `frontend/.env.local`. The backend runtime
expects `DATABASE_URL` in the process environment; `backend/.env.local` is
optional as a human-managed local template only.

## 4. Install Backend + Frontend Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'

cd frontend
npm install
cd ..
```

## 5. Apply Migrations and Seed Analytics Prereqs

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
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
python -m pytest backend/tests
```
