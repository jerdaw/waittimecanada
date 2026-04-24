# Repo Audit Follow-Up Board (2026-04-23)

Status: audit-only. No fixes applied.

## Scope

Parallel audit across:

- code quality
- security
- privacy
- documentation quality and drift
- test quality and drift

## Current Setup

Wait Time Canada is split between a Python backend and a Next.js frontend:

- `backend/` owns scrapers, data services, and supporting CLI flows.
- `frontend/` owns the public map, search, and resource experience.
- The frontend is live on the shared VPS.
- The backend scheduler remains on GitHub Actions because Ontario remains
  unreachable from the VPS runtime.

## Current Entry Points

- `README.md`
- `docs/README.md`
- `docs/planning/roadmap.md`
- `docs/operations/direct-vps-frontend.md`
- `docs/operations/direct-vps-backend.md`
- `backend/README.md`
- `frontend/README.md`

## Findings By Area

### Code Quality

- `Medium`: the backend data-access layer continues to absorb new concerns, and
  the live frontend still lacks an automatic browser-regression gate despite its
  map-heavy interactive surface. Evidence:
  `backend/src/waittime/services/database.py`,
  `.github/workflows/frontend-ci.yml`.

### Security

- `Medium`: the frontend CSP is still report-only, and active CI/smoke coverage
  does not verify deployed header enforcement. Evidence:
  `frontend/next.config.js`,
  `.github/workflows/frontend-ci.yml`,
  `.github/workflows/production-smoke.yml`,
  `.github/workflows/scraper-ci.yml`.

### Privacy

- `Medium`: the privacy policy understates IP handling, geolocation behavior,
  request logging, and third-party processor usage. Evidence:
  `frontend/app/[locale]/privacy/page.tsx`,
  `frontend/app/api/geolocation/route.ts`,
  `frontend/app/[locale]/page.tsx`,
  `frontend/middleware.ts`.

### Documentation Quality And Drift

- `Medium`: start-here surfaces still elevate March snapshots, and one active
  planning file contradicts the repo's rollback-only Netlify posture instead of
  clearly centering the April VPS and Neon baseline. Evidence: `docs/README.md`,
  `docs/operations/direct-vps-frontend.md`,
  `docs/planning/roadmap.md`,
  `docs/planning/deployment-blockers.md`.

### Test Quality And Drift

- `High`: backend integration and E2E coverage are mostly documentary rather
  than enforced. Integration tests skip without `DATABASE_URL`, backend E2E
  skips without both a DB and local server, and the blocking backend workflow
  never provisions either dependency. Evidence:
  `backend/tests/integration/conftest.py`,
  `backend/tests/e2e/test_pipeline.py`,
  `.github/workflows/scraper-ci.yml`,
  `README.md`.

## Follow-Up Tracks

- Create a visitor-data inventory covering browser geolocation, IP-based
  geolocation fallback, API request logging, and third-party requests.
- Reconcile public privacy copy with actual runtime behavior for `ipapi.co`,
  Mapbox, Netlify-history references, and request metadata.
- Decide whether report-only CSP is a steady-state posture or a temporary phase
  with an exit criterion.
- Add deployed-header verification and an automatic browser-regression cadence
  appropriate for a live interactive frontend.
- Re-baseline README and planning claims about test counts, coverage, and
  backend integration depth against current automated evidence.
