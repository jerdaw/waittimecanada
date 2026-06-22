# Milestone 29: Equity Layer Academic Rigor Hardening (Ontario)

**Version:** 1.3
**Date:** 2026-02-18
**Status:** Complete

---

## Summary

Milestone 29 strengthens the Ontario equity layer for academic defensibility.
M28 delivered real StatsCan tract overlays and linkage summaries; M29 addresses remaining validity and interpretability risks identified in the academic audit.

Primary goals:

1. Correct quintile calibration scope for Ontario.
2. Improve statistical and methodological transparency.
3. Add uncertainty/sensitivity outputs for linkage metrics.
4. Improve suppression provenance and reproducibility.
5. Reduce performance and environment fragility risk.

---

## Current State Snapshot

### Strengths already in place

- Real ON tract layer and manifest are generated and versioned.
- Low-income linkage logic excludes quintile `0` (`No Data`).
- ON-only rollout prevents unsupported province overclaiming.
- Full backend/frontend suites are currently green.

### Key gaps closed in M29

1. ON quintiles now derive from ON boundary-matched tract records only.
2. Equity summaries now include sensitivity outputs and bootstrap uncertainty intervals.
3. UI/API now include explicit non-causal and temporal mismatch framing.
4. Suppression provenance is preserved in outputs and manifest breakdowns.
5. Reproducibility is hardened through `equity` extra + setup documentation.
6. Optimized ON layer output is generated and preferred by API loader.

---

## Scope

### In Scope

- Ontario-only academic rigor hardening for equity ingestion, analytics, API metadata, and UI messaging.
- Uncertainty and sensitivity outputs for equity linkage summary.
- Suppression provenance and manifest enrichment.
- Reproducibility hardening for local processing setup.
- Performance controls for ON layer serving.

### Out of Scope

- Multi-province equity onboarding (QC/AB/BC).
- Database schema migrations for equity storage.
- Causal inference modeling.

---

## Audit Traceability Matrix

| Audit Finding | M29 Coverage |
|---|---|
| ON quintiles currently influenced by non-ON rows | Phase 1 (ON-boundary-matched quintile scope) |
| Centroid + fixed threshold is coarse | Phase 2 (multi-threshold sensitivity outputs) |
| No uncertainty reporting | Phase 2 (bootstrap uncertainty intervals) |
| Non-causal interpretation not explicit enough | Phase 3 (API/UI explicit non-causal language) |
| Suppression provenance not preserved | Phase 1 (suppression/missing breakdown fields) |
| Temporal mismatch under-communicated | Phase 3 (reference-year + temporal mismatch messaging) |
| Reproducibility friction in geospatial dependencies | Phase 4 (dependency strategy + setup docs hardening) |
| ON layer payload size risk | Phase 5 (optimized layer output + loader preference) |

---

## Implementation Progress (Live)

- [x] Phase 1 complete: ON-only quintile calibration and suppression provenance extraction implemented.
- [x] Phase 2 complete: equity summary sensitivity + uncertainty metrics implemented.
- [x] Phase 3 complete: non-causal + temporal mismatch messaging added to API/UI.
- [x] Phase 4 complete: geospatial dependency/reproducibility hardening implemented.
- [x] Phase 5 complete: performance controls and verification done; docs/ADR/roadmap updated.

### Output Snapshot (2026-02-18)

- `backend/data/layers/ontario-equity-layer.geojson`
  - SHA256: `6cbfa154f3580bfc322d76e938408aaf909094d24b340b7fa03b007097a2cc09`
  - Size bytes: `21339556`
  - Feature count: `2533`
- `backend/data/layers/ontario-equity-layer.optimized.geojson`
  - SHA256: `443e81b41cdbbab73f7d0d06157d40491a92b5241c7aa0fce7708d957035e39d`
  - Size bytes: `20179531`
  - Feature count: `2533`
- `backend/data/layers/equity-manifest-on.json`
  - SHA256: `3f91cc30070ccfe6e9338f6247eb301559793d63daf7bfca55c295b43cc658fa`
  - `script_version`: `1.4`
  - `processing.quintile_scope`: `ON_BOUNDARY_MATCHED`
  - `processing.optimized_tolerance`: `0.001`
  - `output.size_reduction_percent`: `0.05436`
  - `output.missing_income_breakdown`: `{"no_income_record":0,"suppressed_short":0,"suppressed_long":0,"suppressed_both":27,"missing_or_non_numeric":0}`

---

## Phase Plan

## Phase 1: Data Validity Hardening (Backend Processing)

### Goal

Ensure quintiles and no-data semantics are calibrated to Ontario study scope only.

### Changes

- **Modify** `backend/scripts/prepare_equity_layer.py`
  - Build ON CTUID allowlist from ON boundaries first, then derive quintile cut points from ON-matched records only.
  - Preserve and emit suppression provenance fields from profile export where available:
    - short/long-form suppression flags
    - suppressed/missing counters by reason
  - Add manifest fields:
    - `quintile_scope: "ON_BOUNDARY_MATCHED"`
    - `income_characteristic_id_used: 243`
    - `population_characteristic_id_used: 1`
    - suppression/missing breakdown counts
- **Update tests**
  - `backend/tests/unit/test_prepare_equity_layer.py`
  - Add explicit test proving non-ON rows cannot influence ON quintile cut points.

### Validation Gate

1. Manifest proves ON-only quintile scope.
2. Unit tests verify ON scope isolation and suppression breakdown.
3. Re-generated ON outputs pass schema contract checks.

---

## Phase 2: Quantitative Robustness (Summary Analytics)

### Goal

Move equity summary from single-point descriptive output to a sensitivity-aware descriptive output.

### Changes

- **Modify** `frontend/utils/equityInsights.ts`
  - Add threshold sensitivity output for `[10, 20, 30, 40]` km.
  - Add bootstrap uncertainty intervals (descriptive, non-causal) for:
    - `near_low_income_avg_wait`
    - `wait_gap_minutes`
  - Keep existing headline metrics for backward compatibility.
- **Modify** `frontend/app/api/analytics/equity-summary/route.ts`
  - Include sensitivity table and uncertainty block in JSON response.
  - Add explicit metadata fields declaring descriptive/associational interpretation.
- **Update tests**
  - `frontend/tests/utils/equityInsights.test.ts`
  - `frontend/tests/api/analytics-equity-summary.test.ts`

### Validation Gate

1. Sensitivity outputs present and monotonic sanity checks pass.
2. CI/interval fields are deterministic under seeded test fixtures.
3. Existing clients still work with backward-compatible base fields.

---

## Phase 3: Methods Communication Hardening (API + UI)

### Goal

Prevent causal overinterpretation at the exact points where users read equity results.

### Changes

- **Modify** `frontend/messages/en.json` and `frontend/messages/fr.json`
  - Add explicit non-causal language:
    - “associational/descriptive linkage only”
    - “not causal inference”
  - Add temporal mismatch language:
    - census income reference year vs recent wait aggregation period.
- **Modify** `frontend/components/insights/AccessInsightsSummary.tsx`
  - Render compact methodological limitations block when summary is ready.
- **Modify** `frontend/components/EquityLegend.tsx`
  - Add concise “interpretation limits” footnote under attribution.
- **Modify** `frontend/app/api/equity-layer/route.ts`
  - Include explicit reference year and interpretation notes in metadata.

### Validation Gate

1. UI displays limitations in EN and FR.
2. API metadata exposes reference year and non-causal framing.
3. Snapshot/component tests updated and passing.

---

## Phase 4: Reproducibility and Environment Hardening

### Goal

Make processing reproducible on dev machines without brittle geospatial dependency failure paths.

### Changes

- **Modify** `backend/pyproject.toml`
  - Split extras by use-case:
    - `dev` (tests/tools)
    - `equity` (processing stack)
  - Remove strict reliance on `fiona` where `pyogrio` path is sufficient.
- **Modify** `backend/data/census/README.md`
  - Add environment matrix and exact install commands per workflow:
    - `uv sync --locked --extra dev --extra equity`
  - Add troubleshooting section for GDAL/Fiona compatibility.
- **Update** `backend/uv.lock` after dependency changes.

### Validation Gate

1. Fresh venv setup on this dev machine reproduces processing script run.
2. Full backend suite runs without missing test deps.
3. Equity processing command and docs are consistent.

---

## Phase 5: Performance Controls + Closeout

### Goal

Control layer payload/perf risk and close milestone with auditable evidence.

### Changes

- **Modify** `backend/scripts/prepare_equity_layer.py`
  - Add optional dual-output mode:
    - canonical full output
    - map-optimized simplified output (same properties, tighter geometry)
  - Record both sizes and simplification settings in manifest.
- **Modify** `frontend/utils/equityLayerData.ts` and `frontend/app/api/equity-layer/route.ts`
  - Prefer optimized output when available; fallback to canonical.
- **Documentation**
  - Add ADR documenting methodological hardening decisions (new ADR after 0015).
  - Update roadmap and planning docs to mark M29 completion.

### Validation Gate

1. Frontend map loads optimized layer successfully.
2. Equity API and summary API tests pass.
3. Full test suites pass:
   - backend `pytest`
   - frontend `vitest run`
4. Manifest + docs capture final provenance and limitations.

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Added statistical complexity confuses users | Medium | Keep headline metrics; tuck advanced fields under structured `methodology` blocks |
| Bootstrap CI noise with small samples | Medium | Emit `null` intervals below minimum sample threshold |
| Dependency churn breaks local setup | High | Explicit extras, documented install path, lockfile update |
| Performance regression from extra metadata | Low | Keep metadata compact and cached |
| Misinterpretation persists despite messaging | High | Add repeated non-causal language in API + UI + ADR |

---

## Verification Plan

### Automated

```bash
# Backend
cd backend && .venv/bin/python -m pytest

# Frontend
cd frontend && npx vitest run
cd frontend && npm run type-check
```

Executed on 2026-02-18:

- Backend: `435 passed, 1 skipped` (`.venv/bin/python -m pytest`)
- Frontend: `60 files, 342 tests passed` (`npx vitest run`)
- Frontend type-check: passed (`npm run type-check`)

### Manual

1. Re-run ON processing and inspect manifest scope/suppression fields.
2. Open map and verify legend and tract popup limitations copy.
3. Open Access Insights and verify uncertainty/sensitivity rendering.
4. Validate API responses for new methodology metadata fields.

---

## Timeline

- Phase 1: 3-4h
- Phase 2: 4-6h
- Phase 3: 2-3h
- Phase 4: 2-3h
- Phase 5: 2-3h

**Estimated total:** 13-19h

---

## Rollout and Rollback

### Rollout

1. Merge phase-by-phase with tests green.
2. Regenerate ON artifacts once Phase 1 is complete.
3. Enable optimized layer selection only after parity checks pass.

### Rollback

1. Revert to prior `equityInsights` response shape (base fields only).
2. Revert API metadata additions if client breakage occurs.
3. Switch layer loader to canonical ON file only.
