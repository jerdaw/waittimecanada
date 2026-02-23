# Maintenance Session - 2026-02-23

## Summary

CI/tooling maintenance pass following the M33 completion. Resolved all mypy and
pytest failures in the `scraper-ci` workflow, upgraded key dependencies, and
performed standard repository hygiene.

## Tasks Completed

### 1. Stale Branch Cleanup ✅

- Pruned stale remote-tracking ref
  `origin/dependabot/npm_and_yarn/frontend/tailwind-merge-3.5.0` after
  confirming PR #17 was already squash-merged and the branch contained nothing
  new.

### 2. CI Failure Resolution ✅

Resolved all mypy and pytest failures in `scraper-ci.yml`:

**mypy fixes:**
- Corrected `# type: ignore[assignment,misc]` placement in optional Playwright
  import fallback (`observability.py`). Previous approach added pre-block
  annotations which caused `[no-redef]` with mypy v1.19.0.
- Removed stale `# type: ignore[misc]` from `@retry` decorators across all
  scrapers (`base.py`, `bc.py`, `ontario.py`, `quebec.py`, `alberta.py`).
  These were no longer needed once `tenacity` stubs were properly installed.
- Removed redundant `cast(str, page.content())` and unused `cast` import in
  `alberta.py`.

**pytest fixes:**
- Fixed match string in `test_database_service.py`:
  `"Database URL required"` → `"Database URL or connection required."`
- Added `pytest.skip()` guard to E2E fixture in `test_pipeline.py` when
  `DATABASE_URL` is absent.

### 3. Dependency Upgrades ✅

**Pre-commit / tooling:**
- Bumped `astral-sh/ruff-pre-commit` from `v0.1.15` → `v0.14.14`
- Bumped `mirrors-mypy` from `v1.8.0` → `v1.19.0`
- Added `playwright` and `tenacity` to mypy hook `additional_dependencies` so
  all three environments (pre-commit hook, local venv, CI) resolve identical
  stubs.
- Auto-fixed 41 ruff I001 import-sort violations across backend test files.

**Frontend npm:**
- `react-map-gl`: `^7.1.0` → `^8.1.0`
- `date-fns`: `^3.0.0` → `^4.1.0`
- `playwright` / `@playwright/test`: `^1.40.0` → `^1.58.2`

### 4. react-map-gl v8 Migration ✅

react-map-gl v8 dropped the root `"react-map-gl"` import in favour of
provider-specific paths. Changes made:

- `frontend/components/Map.tsx`: import path changed to `"react-map-gl/mapbox"`;
  added explicit event handler types for v8 API (`e: unknown` on map
  click/mousemove, `e: { originalEvent: Event }` on marker click).
- `frontend/tests/components/Map.test.tsx`: updated `vi.mock` path.
- `frontend/tests/setup.ts`: updated `vi.mock` path.

### 5. Documentation & Archive Hygiene ✅

- Archived `docs/planning/maintenance-2026-02-19.md` →
  `docs/planning/archive/maintenance-2026-02-19.md`
- Archived `docs/planning/implementation/milestone-32-deployment-readiness.md`
  → `docs/planning/archive/milestone-32-deployment-readiness.md` (file was
  already marked "Completed and Archived" but was not moved)
- Updated `CHANGELOG.md` with `[1.2.1]` entry
- Updated `docs/planning/roadmap.md`: current status date, Next Steps, and
  added checked CI/tooling maintenance item to the Now section

### 6. Attribution Verification ✅

- Confirmed no AI co-author or attribution trailers in any commit in the last 20
  commits.
- `CLAUDE.md` and `GEMINI.md` remain symlinks to `AGENTS.md`.
- `AGENTS.md` attribution policy section is current and complete.

## Verification

- Backend tests: 454+ passing (`python -m pytest backend/tests`)
- Frontend unit tests: 359 passing (`cd frontend && npm run test:unit`)
- Pre-commit hooks: all passing (ruff, ruff-format, mypy, detect-secrets)
- Working tree: clean after commit `f2da747`

## Root Cause Note: mypy Version Split

The CI failures arose from a three-way split in mypy versions:
- Pre-commit hook: pinned to `v1.8.0`
- Local venv: `v1.19.1`
- CI: resolved `mypy>=1.7.0` → `v1.15.x`

The fix was to bump the pre-commit hook to `v1.19.0` and install the same
optional-dependency packages (`playwright`, `tenacity`) in the hook environment
so all three environments produce identical type-check results.
