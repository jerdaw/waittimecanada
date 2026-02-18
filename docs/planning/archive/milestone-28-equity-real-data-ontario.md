# Milestone 28: Enhanced Equity Layer - Real StatsCan Census Tract Overlays (Ontario First)

**Version:** 1.3
**Date:** 2026-02-18
**Status:** Complete (Ontario Real Data Generated and Verified)

---

## Summary

Milestone 28 upgrades the existing equity scaffold from placeholder tract linkage to real Statistics Canada 2021 census tract income data, starting with Ontario only. This is intentionally staged to match project operating principles ("one province at a time"), preserve reliability, and keep claims methodologically defensible.

This plan replaces the prior multi-province-first draft with an Ontario-first rollout and a province-template path for later expansion.

---

## Implementation Progress (Live)

- [x] Phase 1 code updates: backend processing hardening, optional `equity` dependencies, raw-data staging docs, ignore rules.
- [x] Ontario raw input acquisition complete (local staging in `backend/data/census/boundaries/on` and `backend/data/census/income/on`).
- [x] Phase 2 code updates: ON file-backed linkage in API routes, placeholder ON path removed, quintile `0` handling corrected.
- [x] Phase 3 code updates: map toggle/legend wired, tract detail interaction added (hover + click/tap), EN/FR i18n strings added.
- [x] Phase 4 documentation updates: ADR-0015 added, ADR-0011 supersession note added, roadmap updated for M28 in-progress.
- [x] Phase 4 verification complete: targeted frontend/backend tests run and passing.
- [x] Ontario real-data artifact refresh complete: processing script run against local StatsCan ON raw inputs and produced ON GeoJSON + manifest.
- [x] Post-closeout validation complete: full frontend Vitest suite and full backend pytest suite run; backend Alberta scraper wait-text regression fixed (`wait_span` NameError) and suites re-run green.

---

## Baseline Snapshot (At Milestone Kickoff)

### At Kickoff

- `frontend/app/api/equity-layer/route.ts`
  - Ontario-only endpoint (`SUPPORTED_PROVINCES = ["ON"]`).
  - Reads `backend/data/layers/ontario-equity-layer.geojson`.
  - Returns metadata with `is_placeholder: false`.
- `frontend/app/api/analytics/equity-summary/route.ts`
  - Ontario DB query + placeholder feature linkage via `buildPlaceholderEquityFeatureCollection`.
  - Non-ON returns `not_available_yet`.
- `frontend/components/Map.tsx`
  - Equity state/load logic and map `Source`/`Layer` already exist.
  - `EquityLayerToggle` and `EquityLegend` imports are commented out and not rendered.
- `frontend/utils/equity.ts`
  - Placeholder types + ON demo feature builder still present.
- `backend/scripts/prepare_equity_layer.py`
  - Basic `--dummy` and real-data merge path exists, but lacks robust schema normalization, simplification controls, provenance manifest, and QA gates.
- `backend/data/layers/ontario-equity-layer.geojson`
  - Dummy/randomized tract-like geometry (not real StatsCan census tracts).

### Key Unknowns

1. Exact Ontario StatsCan download format and field names in selected CSV export.
2. Final ON layer size after simplification tolerance tuning.
3. Proportion of ON tracts with suppressed/missing income values in selected source files.

### Working Assumptions

1. StatsCan 2021 census tract boundary and income tables are available under Open Government Licence - Canada.
2. Ontario-only can be delivered without DB schema changes.
3. Heavy geospatial dependencies are acceptable when isolated to an optional backend dependency group.

---

## Scope Decision (Locked)

### In Scope for M28

- Ontario real-data equity layer productionization end-to-end.
- Removal of placeholder linkage from Ontario summary responses.
- Equity map controls fully wired (toggle + legend + tract detail UX).
- EN/FR string updates required by new UI copy.
- Provenance and reproducibility manifest for ON processing run.

### Out of Scope for M28

- QC/AB/BC real-data onboarding.
- Vector tileset migration.
- New database tables.

---

## Ontario Raw Input Acquisition Record (2026-02-18)

Local staged files are documented in:

- `backend/data/census/README.md`

Source pages and required selectors used:

1. Boundary files page: `https://www12.statcan.gc.ca/census-recensement/2021/geo/sip-pis/boundary-limites/index2021-eng.cfm?year=21`
2. Census Profile download page: `https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/details/download-telecharger.cfm?Lang=E`

The exact downloaded file names, extracted file names, and SHA256 verification hashes are recorded in `backend/data/census/README.md` for reproducibility and audit traceability.

Ontario output artifacts generated from these inputs:

- `backend/data/layers/ontario-equity-layer.geojson` (2533 features, 20,020,007 bytes, SHA256 `3cfed11edfd4b4e409ee8ea051cb2f11538bcc61ec574ccba87895712c8a2e71`)
- `backend/data/layers/equity-manifest-on.json` (SHA256 `b6b4f5370e83df685104119edd22a0f1012bc9a07cb4e0d0603f06d4e625b29a`, `script_version: 1.2`)

---

## Architecture and Data Contract

### Canonical Ontario Layer File

- Output file remains: `backend/data/layers/ontario-equity-layer.geojson`
- Keep this filename for compatibility with existing API/tests during M28.

### Required Feature Properties (normalized contract)

Each feature served to frontend must provide:

- `tract_id: string` (from CTUID)
- `tract_name: string` (from CTNAME, fallback CTUID)
- `income_quintile: 0 | 1 | 2 | 3 | 4 | 5`
- `median_household_income: number | null`
- `population_2021: number | null` (optional source availability)
- `is_placeholder: boolean` (`false` for processed real outputs; conservative fallback may be `true` when flag is absent)

### Critical Logic Rule

- Low-income tract definition for linkage remains quintiles `1` and `2` only.
- Quintile `0` ("No Data") must never be counted as low-income.

---

## Phased Implementation Plan

## Phase 1: Data Ingestion and Processing Hardening (Backend)

### Goal

Generate reproducible, validated Ontario real-data GeoJSON from StatsCan downloads.

### Changes

- **Modify** `backend/scripts/prepare_equity_layer.py`
  - Add explicit Ontario mode and input validation.
  - Normalize common StatsCan field variants (`CTUID`, `GEO_ID`, etc.).
  - Parse income robustly (numeric cleanup, suppression handling).
  - Add geometry simplification tolerance flag (`--tolerance`, default `0.001`).
  - Add output size warning threshold.
  - Add `--include-no-data` behavior mapping missing/suppressed income to quintile `0`.
  - Emit `backend/data/layers/equity-manifest-on.json` with:
    - source URLs / file names
    - run timestamp (UTC)
    - input file hashes (SHA256)
    - feature counts (total, with income, no-data count)
    - quintile distribution
    - simplification tolerance
    - output file size bytes
- **Add** backend docs for local data placement:
  - `backend/data/census/README.md`
- **Update** ignore rules:
  - `backend/.gitignore` to ignore raw census input directories under `backend/data/census/`.

### Dependency Strategy

- **Modify** `backend/pyproject.toml`
  - Add optional dependency group `equity` for geospatial stack (`geopandas`, `pyproj`, `fiona`, `shapely`).
  - Do not add these to base dependencies.

### Validation Gate (must pass before Phase 2)

1. Processing command succeeds locally from clean inputs.
2. Output layer exists and parses as valid FeatureCollection.
3. Manifest generated with complete provenance fields.
4. Manual spot-check of sample CTUID rows against source CSV values.

---

## Phase 2: API and Linkage Truthfulness (Frontend API Routes)

### Goal

Serve and summarize real Ontario tract data without placeholder fallback.

### Changes

- **Modify** `frontend/app/api/equity-layer/route.ts`
  - Keep ON-only support in M28.
  - Validate and normalize served properties into frontend contract fields.
  - Keep `is_placeholder: false`.
  - Keep CDN caching headers.
- **Modify** `frontend/app/api/analytics/equity-summary/route.ts`
  - Replace placeholder builder with file-backed ON tract load.
  - Return `is_placeholder: false` for ON success paths.
  - Keep non-ON behavior as `not_available_yet` and setup guidance.
- **Modify** `frontend/utils/equityInsights.ts`
  - Ensure low-income filter excludes quintile `0` explicitly.

### Validation Gate

1. API tests pass with updated ON responses.
2. ON summary reports non-placeholder data path.
3. Non-ON behavior remains explicit and unchanged.

---

## Phase 3: Map UX Wiring, i18n, and Accessibility

### Goal

Make the equity layer usable and transparent on desktop and mobile.

### Changes

- **Modify** `frontend/components/Map.tsx`
  - Wire `EquityLayerToggle` into map controls.
  - Render `EquityLegend` when equity layer active and data loaded.
  - Add tract detail interaction:
    - Hover behavior for pointer devices.
    - Click/tap behavior fallback for touch devices.
  - Add visible error state text when equity layer load fails/unavailable.
  - Keep hospitals visually above tract fill layer.
- **Modify** `frontend/components/EquityLegend.tsx`
  - Add quintile `0` row ("No Data").
  - Remove scaffold warning for ON real data path.
  - Show StatsCan attribution text.
- **Modify** `frontend/components/EquityLayerToggle.tsx`
  - Move labels to i18n keys and ensure clear ARIA labels.
- **Modify** `frontend/messages/en.json` and `frontend/messages/fr.json`
  - Add map/equity toggle labels, legend labels, no-data label, tract popup labels.
- **Modify** `frontend/utils/equity.ts`
  - Expand `IncomeQuintile` to include `0`.
  - Remove ON placeholder feature generator once route migration is complete.

### Validation Gate

1. Toggle/legend interactions work in EN and FR locales.
2. Tract details accessible on mouse and touch.
3. Mobile viewport usability verified at 375px width.

---

## Phase 4: Testing, Documentation, and Rollout Controls

### Goal

Close M28 with defensible evidence, clear documentation, and safe rollback.

### Changes

- **Update tests**
  - `frontend/tests/api/equity-layer.test.ts`
  - `frontend/tests/api/analytics-equity-summary.test.ts`
  - `frontend/tests/components/EquityLegend.test.tsx`
  - `frontend/tests/components/AccessInsightsSummary.test.tsx`
  - `frontend/tests/components/insights/AccessInsightsSummary.test.tsx`
  - Add targeted unit tests for `prepare_equity_layer.py` if practical with fixtures.
- **Documentation**
  - Add new ADR: `docs/adr/0015-real-equity-layer-ontario.md`.
  - Update `docs/adr/0011-equity-layer-scaffold.md` status to superseded-by/partially superseded context.
  - Update roadmap entries after merge completion (`docs/planning/roadmap.md`).
  - Update `AGENTS.md` milestone status only after implementation is merged and verified.

### Validation Gate

1. Frontend and backend test suites pass.
2. Manual map walkthrough complete.
3. Documentation and ADR updates merged with implementation.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| StatsCan schema drift | Medium | Field normalization map + clear error messages + manifest capture |
| Quintile logic misclassification (`0` treated as low-income) | High | Explicit filter rule in linkage utility + dedicated test |
| Layer size/performance degradation | Medium | Simplification tolerance tuning + size warning + future tileset path |
| i18n regressions | Medium | Add EN/FR keys and component tests |
| Dependency bloat in standard dev setup | Medium | Geospatial stack as optional `equity` extra |
| Overclaiming from stale assumptions | High | Keep source year and limitations visible in UI and ADR |

---

## Verification Plan

### Automated

```bash
# Frontend
cd frontend && npx vitest run

# Backend
cd backend && python -m pytest
```

### Manual

1. Run ON processing script from local StatsCan files.
2. Inspect output and manifest values.
3. Launch frontend and enable income overlay on Ontario.
4. Verify legend, tract details, load errors, and locale behavior.
5. Verify Access Insights equity card no longer shows placeholder copy for ON.

---

## Timeline and Milestones

- Phase 1: 3-5h (includes data prep QA and manifest)
- Phase 2: 2-3h
- Phase 3: 3-5h (i18n + interaction + accessibility checks)
- Phase 4: 2-3h

**Estimated total:** 10-16h

---

## Rollout and Rollback

### Rollout

1. Merge behind ON-only API support.
2. Keep non-ON routes in explicit `not_available_yet`.
3. Validate manually before marking roadmap milestone complete.

### Rollback

1. Revert ON equity summary route to placeholder builder path.
2. Disable map equity toggle rendering in `Map.tsx` if needed.
3. Restore previous `ontario-equity-layer.geojson` and remove manifest-driven assertions.

---

## Post-M28 Expansion Template (Not part of this milestone)

After ON stabilization, apply the same pipeline to QC/AB/BC in a follow-up milestone using:

- same normalized contract,
- same provenance manifest schema,
- same test matrix,
- province-by-province rollout gates.
