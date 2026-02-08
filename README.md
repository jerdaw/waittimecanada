# WaitTime Canada

> A clinically defensible Health Systems Observatory for Canadian ER wait-time methodology and reporting quality.

[![Frontend CI](https://github.com/jerdaw/waittimecanada/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/jerdaw/waittimecanada/actions/workflows/frontend-ci.yml)
[![Scraper CI](https://github.com/jerdaw/waittimecanada/actions/workflows/scraper-ci.yml/badge.svg)](https://github.com/jerdaw/waittimecanada/actions/workflows/scraper-ci.yml)
[![Production Readiness](https://github.com/jerdaw/waittimecanada/actions/workflows/production-readiness.yml/badge.svg)](https://github.com/jerdaw/waittimecanada/actions/workflows/production-readiness.yml)

## What This Project Is

WaitTime Canada is not a simple wait-time leaderboard. It is an observatory that:

- audits methodology differences across provinces
- preserves source semantics instead of normalizing incomparable metrics
- surfaces divergence warnings when direct comparisons are invalid
- provides data-quality and anomaly visibility for operational trust
- supports analytics, benchmarking, and export for transparent interpretation

## Current Scope

- Frontend: Next.js 14 + TypeScript (`frontend/`)
- Backend: Python 3.12+ scraper/services package (`backend/`)
- Database: Neon PostgreSQL with strict metric ontology constraints
- Major delivered capabilities: comparability warnings, aggregation pipeline, data-quality dashboard, analytics benchmarks/trends/regions, occupancy availability contract, equity scaffold

Source-of-truth roadmap: `docs/planning/roadmap.md`

## Quick Start (Local)

### 1. Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- Neon `DATABASE_URL`
- Mapbox token (`NEXT_PUBLIC_MAPBOX_TOKEN`)

### 2. Create Environment Files

```bash
cp backend/.env.example backend/.env.local
cp frontend/.env.example frontend/.env.local
```

Populate values in both files (at minimum `DATABASE_URL`; frontend also needs `NEXT_PUBLIC_MAPBOX_TOKEN`).

### 3. Set Up Python Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e 'backend[dev]'
```

Note for `zsh`: keep quotes around `backend[dev]`.

### 4. Apply Migrations and Bootstrap Analytics

```bash
python backend/run_migrations.py
python -m waittime.cli.bootstrap_analytics --days 180
```

### 5. Set Up Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Common Commands

### Backend

```bash
source .venv/bin/activate

# Run all scrapers
python -m waittime.cli.scraper --all

# Run a single scraper
python -m waittime.cli.scraper --source ontario-health

# Run backend tests
python -m pytest backend/tests
```

### Frontend

```bash
cd frontend

# Type check + lint + unit tests
npm run type-check
npm run lint
npm run test:unit
```

Playwright E2E is CI-first in this project; avoid local E2E unless debugging.

## Repository Map

- `backend/README.md`: backend architecture, CLI, and testing
- `frontend/README.md`: frontend architecture, APIs, and testing
- `docs/README.md`: documentation index
- `docs/API.md`: API contracts and examples
- `docs/architecture/`: architecture overviews
- `docs/planning/roadmap.md`: active roadmap and milestone status
- `docs/planning/manual-tasks.md`: human-intervention queue

## Operational Workflows

Workflow reference and required secrets:

- `.github/workflows/README.md`
- `frontend/netlify.toml` + `frontend/scripts/netlify-ignore.sh` gate Netlify builds to explicit `[release]`/`[deploy]` commits only
- Netlify guardrails reduce future credit burn only; they do not automatically unsuspend a site already suspended for exceeded credits before billing reset on March 2, 2026
- `frontend/utils/cache.ts` standardizes API cache headers for read-heavy endpoints; admin/user-specific routes remain `no-store`

Quick production ops check:

```bash
./scripts/verify-production-ops.sh jerdaw/waittimecanada
```

Note: if frontend hosting is intentionally offline, `production-smoke.yml` may be disabled and this audit will report that as a warning.

## Guardrails

- Do not provide medical advice.
- Do not claim cross-province comparability unless ontology dimensions match.
- Do not store full HTML payloads in measurements.
- Keep verification gate intact (`is_verified` and `is_visible`) for hospital publishing.
