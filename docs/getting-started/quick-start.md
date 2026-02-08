# Quick Start

## 1. Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Neon `DATABASE_URL`
- Mapbox token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

## 2. Initialize Local Environment

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

Populate required values in both files.

## 3. Install Backend + Frontend Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'

cd frontend
npm install
cd ..
```

## 4. Apply Migrations and Seed Analytics Prereqs

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
```

## 5. Start the App

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## 6. Optional Validation

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
