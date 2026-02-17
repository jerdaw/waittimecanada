# Implementation Plan - Milestone 25: Reliability & Verification Phase 2

**Goal:** Achieve >85% backend test coverage, complete the API integration test suite, and harden operational reliability features.

## Current State
- **Backend Test Coverage:** 79% (Target: 85%+).
- **API Tests:** Partial coverage. Missing tests for `/api/hospitals`, `/api/health`, `/api/export`, `/api/geolocation`.
- **Health Check:** Basic latency check. `pool_status` is implemented as `unknown` placeholder.
- **E2E Test:** `test_pipeline.py` fails when local server is not running (CI/CD risk).

## Proposed Changes

### 1. Backend Code Coverage (Target: 85%+)
Focus on unit testing edge cases in services and scrapers.
- **`src/waittime/services/trends.py`**: Add tests for edge cases (empty data, different horizons).
- **`src/waittime/services/patterns.py`**: Add tests for missing branches.
- **`src/waittime/db.py` / `database.py`**: Verify error handling coverage.

### 2. Comprehensive API Integration Tests
Create new test files in `frontend/tests/api/` for missing endpoints.
- `hospitals.test.ts`: Verify list, filtering, and detail response structures.
- `health.test.ts`: Verify health check response and 500 handling.
- `export.test.ts`: Verify CSV/JSON export formats.
- `geolocation.test.ts`: Verify IP-based geolocation logic.

### 3. Reliability & Robustness
- **Enhanced Health Check**: Implement connection pool statistics in `frontend/app/api/health/route.ts` if possible (using `sql.unsafe` or similar if `postgres.js` supports it, otherwise clarify comment).
- **Robutst E2E Test**: Modify `backend/tests/e2e/test_pipeline.py` to:
  - Skip gracefullly if `localhost:3000` is unreachable (with a warning).
  - Or use a mock server if feasible (skip is better for this environment).
- **Rate Limit Verification**: Ensure `checkRateLimit` is applied to all new integration tests.

## Verification Plan

### Automated Tests
- Run `pytest --cov=src/waittime` to confirm >85% coverage.
- Run `npm test` in frontend to verify new API tests.
- Run `pytest tests/e2e/test_pipeline.py` to verify skip logic.

### Manual Verification
- Curl `/api/health` to see pool status (if implemented).
