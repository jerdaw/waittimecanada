# Milestone 20: Reliability & Verification Implementation Plan

## Goal Description
Enhance the reliability and observability of the Wait Time Canada platform by implementing API response time tracking, backend end-to-end pipeline testing, and visual regression testing. This milestone aims to close key verification gaps identified in the roadmap.

## Proposed Changes

### Backend
#### [NEW] `backend/tests/e2e/test_pipeline.py`
- Implements an end-to-end smoke test that:
    1. Generates a unique test hospital payload.
    2. Inserts it directly into the database using `DatabaseService`.
    3. Polls the local API (`/api/hospitals`) until the data appears.
    4. Verifies the returned data matches the inserted payload.

### Frontend
#### [MODIFY] `frontend/middleware.ts`
- Modifies the middleware to capture request duration.
- Adds `X-Response-Time` and `Server-Timing` headers to API responses.
- Implements structured JSON logging for API requests.

#### [NEW] `frontend/tests/e2e/visual.spec.ts`
- Creates Playwright visual regression tests.
- Captures snapshots of the landing page and hospital detail page.

### Tools
#### [MODIFY] `Makefile`
- Adds `test-e2e` target to run the backend pipeline test.
- Adds `test-visual` target to run frontend visual regression tests.

## Verification Plan

### Automated Tests
- **Backend E2E:** Run `make test-e2e` to verify the full data pipeline from insertion to API response.
- **Visual Regression:** Run `make test-visual` to verify UI stability against baseline snapshots.

### Manual Verification
- Verify API response headers using `curl -I http://localhost:3000/api/hospitals`.
- Inspect server logs for structured JSON output.
