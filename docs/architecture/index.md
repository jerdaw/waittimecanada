# Architecture Overview

WaitTime Canada is structured as a data observatory pipeline:

1. Provincial source pages are scraped by backend jobs.
2. Measurements are stored with strict ontology metadata in Neon PostgreSQL.
3. Aggregation and quality services derive analytics-ready summaries.
4. Next.js server routes expose read APIs for map, methods, data-quality, and analytics views.

## Core Principles

- Preserve semantic meaning; do not normalize incomparable measurements.
- Make uncertainty explicit (divergence warnings, data-quality status, availability states).
- Keep provenance and operational health first-class.
- Enforce manual verification before hospital publication.

## Architecture Documents

- API architecture: `docs/architecture/api.md`
- Database architecture: `docs/architecture/database.md`
- Public API reference: `docs/API.md`
- Metric ontology ADR: `docs/adr/0002-metric-ontology.md`

## Runtime Components

- Backend package: `backend/src/waittime/`
- Frontend app/API: `frontend/app/`
- Migrations: `backend/migrations/`
- CI/ops workflows: `.github/workflows/`
