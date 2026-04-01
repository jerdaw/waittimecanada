# Wait Time Canada Documentation

Wait Time Canada is a clinically defensible Health Systems Observatory for auditing Canadian emergency department wait time data and methodology differences across provinces.

## Start Here

- Project overview: `README.md` (repo root)
- Roadmap (source of truth): `docs/planning/roadmap.md`
- API reference: `docs/API.md`
- Architecture overview: `docs/architecture/index.md`

## Deployment Status

As of **2026-04-01**, the frontend is live on the shared VPS at `https://wait-time.ca`, `https://www.wait-time.ca` redirects to the canonical host, and the backend scheduler path remains on GitHub Actions. Live verification on 2026-04-01 showed `/api/health` returning `healthy: true` with the database connected again, and DB-backed routes such as `/api/hospitals` and `/api/resources` responding normally. The remaining live follow-up is that `/api/status` and `/api/data-quality` still expose critical aggregate values and inactive legacy source IDs that do not match the healthy live source runs observed on 2026-04-01. See `docs/planning/roadmap.md` and `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`.

## Current Operations Artifacts

- Monthly operations review: `docs/operations/reports/2026-03-operational-report.md`
- Latest incident report: `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`
- Latest maintenance log: `docs/planning/archive/maintenance-2026-04-01.md`

## Safety

This project does **not** provide medical advice. For emergencies, call **911**.
