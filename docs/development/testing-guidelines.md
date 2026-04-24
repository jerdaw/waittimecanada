# Testing Guidelines

This project treats testing as a reliability control for clinical data interpretation.

## Test Stack

- Backend: `pytest` (`backend/tests`)
- Frontend unit/component: `Vitest` + React Testing Library
- Frontend E2E: `Playwright` (manual-dispatch CI lane; local only when debugging; not part of the default push/PR merge gate)

## Core Principles

- Test behavior, not implementation details.
- Keep assertions tied to ontology/comparability contracts.
- Prefer deterministic fixtures over live external dependencies.
- Add regression tests when fixing bugs.

## Backend Test Types

### Unit (`@pytest.mark.unit`)

Use for isolated logic without network/database I/O.

```bash
python -m pytest -m unit backend/tests
```

### Integration (`@pytest.mark.integration`)

Use for DB interactions, scraper parsing integration, and service composition.
These tests require `DATABASE_URL` and will skip when that prerequisite is not
present.

```bash
python -m pytest -m integration backend/tests
```

### Full backend suite

```bash
python -m pytest backend/tests
```

Note:
`backend/tests/e2e/test_pipeline.py` is an opt-in local smoke path layered into
the pytest tree. It also expects `DATABASE_URL` plus a local frontend server on
`http://localhost:3000`, and it will skip if those prerequisites are missing.

## Frontend Test Types

### Unit/component suite

```bash
cd frontend
npm run test:unit
```

### E2E suite (CI)

```bash
cd frontend
npm run test:e2e
```

Default rule: do not run E2E locally unless investigating a specific
browser-flow bug. Use GitHub Actions manual dispatch for routine browser
verification; the suite was repo-side stabilized on 2026-04-09, but heavy
browser coverage remains CI-first to conserve GitHub Actions free-tier minutes
and is not the default merge-readiness gate.

## Coverage and Quality Expectations

- Coverage should not regress for changed modules.
- New API routes/services should include happy-path and error-path tests.
- Comparability, divergence warnings, and data-quality logic must remain explicitly tested.
- If a change is hard to test directly, document rationale in PR notes.
- CI retains split frontend/backend coverage artifacts for inspection, but does not depend on a third-party coverage gate.
- Avoid brittle whole-repo coverage gates in local commands when the baseline is intentionally being raised over time.

## Naming and Organization

- Backend: `test_*.py` under `backend/tests/unit` or `backend/tests/integration`
- Frontend: `*.test.ts` or `*.test.tsx` in `frontend/tests`
- Shared backend fixtures: `backend/tests/conftest.py`
- Shared frontend test utilities: `frontend/tests/test-utils.tsx`

## Local Verification Matrix

Use this as a minimal baseline before opening a PR:

```bash
# Backend
ruff check backend/src backend/tests
mypy backend/src
python -m pytest backend/tests

# Frontend
cd frontend
npm run lint
npm run type-check
npm run test:unit
```

## CI Alignment

- CI is the source of truth for merge readiness.
- Treat local runs as fast preflight to reduce CI churn.
- If local and CI disagree, prioritize reproducing and fixing CI conditions.
- Frontend and backend coverage artifacts are produced from separate path-scoped workflows and kept as short-lived build artifacts for debugging.
- Playwright remains manual-dispatch in GitHub Actions even after the 2026-04-09 stabilization pass; default merge readiness relies on lint, type-check, unit tests, and build, with browser E2E reserved for explicit verification runs.
- Backend integration coverage exists, but DB-backed integration and local smoke assertions are still prerequisite-dependent rather than universally enforced in every local or CI context.

## Free-Tier CI Conservation (Temporary)

When GitHub Actions minutes are constrained:

- Run targeted backend/frontend tests locally before pushing.
- Prefer focused test commands for touched modules during iteration.
- Avoid local Playwright runs unless diagnosing a browser-specific defect.
- Reserve full CI-heavy runs (especially manual-dispatch Playwright) for final verification pushes or targeted browser regressions.
