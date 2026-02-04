# Testing Guidelines

We prioritize high-quality, clinically-defensible code through rigorous testing.

## Frameworks

- **Backend**: `pytest`
- **Frontend**: `Vitest` + `React Testing Library`
- **E2E**: `Playwright` (CI only)

## Test Categories

### 1. Unit Tests (Fast, No I/O)
- Test individual functions, models, and logic.
- Target: 90% coverage for core logic (ComparisonService, Scrapers).
- Run: `pytest -m unit` (Backend) or `npm run test:unit` (Frontend).

### 2. Integration Tests (Database, External APIs)
- Test interactions between components.
- Use mocks for external APIs when possible, or specialized fixtures.
- Run: `pytest -m integration`.

### 3. E2E Tests (Browser-based)
- Test full user flows in the browser.
- **Rule**: Do NOT run these locally unless specifically debugging. They are run automatically in GitHub CI.

## Standards

- **Coverage**: Minimum 80% overall coverage required for any new feature.
- **Naming**: Files should end in `.test.tsx` (Frontend) or start with `test_` (Backend).
- **Fixtures**: Use `conftest.py` for shared backend fixtures and `frontend/tests/fixtures/` for frontend data.

## Attribution

- Only humans should be credited with writing or maintaining tests.
