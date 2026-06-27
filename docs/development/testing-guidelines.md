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
cd backend
uv run pytest -m unit tests
```

### Integration (`@pytest.mark.integration`)

Use for DB interactions, scraper parsing integration, and service composition.
These tests require `DATABASE_URL` and will skip when that prerequisite is not
present.

```bash
cd backend
uv run pytest -m integration tests
```

For a disposable local PostgreSQL database, start the test compose service from
the repository root and point backend commands at the exposed port:

```bash
docker compose -f docker-compose.test.yml up -d postgres-test
export DATABASE_URL="postgresql://waittime:waittime@127.0.0.1:54329/waittimecanada_test" # pragma: allowlist secret
```

### Full backend suite

```bash
cd backend
uv run pytest tests
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

### Disposable DB verification

Use the disposable Postgres helper when you need the database-backed integration
lane plus browser and pipeline smoke checks without using production secrets:

```bash
bash scripts/run-disposable-db-checks.sh
```

The helper starts `postgres:17` on `127.0.0.1:54329`, exports a non-secret test
`DATABASE_URL`, runs migrations, runs backend integration tests, runs Playwright
Chromium, starts a local Next server on `localhost:3000`, and runs the backend
pipeline smoke test. It uses `uv` from `PATH`, `UV_BIN`, or the default mise
shim path.

Lean WSL images may need browser system libraries before Playwright can launch:

```bash
cd frontend
npx playwright install --with-deps chromium
```

If those system dependencies are not available and you only need to verify the
database-backed backend and pipeline smoke portions, run:

```bash
SKIP_PLAYWRIGHT=1 bash scripts/run-disposable-db-checks.sh
```

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
cd backend
uv run ruff check src tests scripts
uv run mypy src
uv run python scripts/check_migration_sequence.py
uv run pytest tests

# Frontend
cd frontend
npm run lint
npm run type-check
npm run type-check:test
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
