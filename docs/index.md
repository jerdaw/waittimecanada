# Wait Time Canada Documentation

Wait Time Canada is a clinically defensible Health Systems Observatory for auditing Canadian emergency department wait time data and methodology differences across provinces.

## Start Here

- Project overview: `README.md` (repo root)
- Roadmap (source of truth): `docs/planning/roadmap.md`
- API reference: `docs/API.md`
- Architecture overview: `docs/architecture/index.md`

## Deployment Status

As of **2026-03-28**, the frontend is live on the shared VPS at `https://wait-time.ca`, `https://www.wait-time.ca` redirects to the canonical host, and the backend scheduler path remains on GitHub Actions. However, the current production pause point is an external Neon transfer-quota incident that is leaving live DB-backed routes unavailable until quota/reset or DB-path changes restore connectivity. See `docs/operations/direct-vps-frontend.md`, `docs/planning/roadmap.md`, and `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`.

## Current Operations Artifacts

- Monthly operations review: `docs/operations/reports/2026-03-operational-report.md`
- Current incident report: `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`

## Safety

This project does **not** provide medical advice. For emergencies, call **911**.
