# ADR 0016: Equity Academic Rigor Hardening (Ontario)

## Status
Accepted (2026-02-18)

## Context
ADR-0015 replaced placeholder equity linkage with real Ontario census tract inputs, but an academic audit identified remaining validity and interpretation risks:

- Quintile calibration scope could be influenced by non-ON rows.
- API/UI messaging did not consistently prevent causal overinterpretation.
- Equity linkage outputs lacked uncertainty/sensitivity context.
- Reproducibility and geospatial dependency setup needed clearer controls.
- ON layer payload size created performance risk for map loading.

## Decision
For Ontario equity analytics and map serving:

1. Calibrate income quintiles using Ontario boundary-matched tract records only (`quintile_scope=ON_BOUNDARY_MATCHED`).
2. Preserve suppression provenance in processed outputs (`short_income_suppressed`, `long_income_suppressed`) and manifest missing-income breakdowns.
3. Extend equity summary analytics with:
   - fixed-threshold sensitivity outputs (`10/20/30/40km` + requested threshold),
   - bootstrap percentile uncertainty intervals (95% CI) for descriptive metrics.
4. Enforce explicit interpretation limits in API/UI:
   - descriptive/associational only,
   - no causal inference,
   - temporal mismatch warning (Census 2021 income vs recent wait aggregates).
5. Harden reproducibility with explicit dependency groups (`dev`, `equity`) and documented setup (`uv sync --extra dev --extra equity`) using `pyogrio` path.
6. Generate dual layer artifacts:
   - canonical output,
   - optimized geometry output,
   with frontend/API preference for optimized and fallback to canonical.

## Rationale
- Reduces bias risk in quintile assignment by constraining scope to study geography.
- Improves interpretive safety for users and reviewers.
- Improves statistical transparency without implying causal claims.
- Makes local processing repeatable on developer workstations.
- Reduces map payload risk while preserving canonical artifact lineage.

## Consequences

### Positive
- Stronger methodological defensibility for ON equity outputs.
- Better transparency for suppressed/missing tract income data.
- Better map performance posture through optimized geometry serving.
- Explicit, repeated non-causal framing across API and UI surfaces.

### Tradeoffs
- Additional output/metadata complexity in APIs and manifests.
- Bootstrap intervals are descriptive and may be unstable with very small samples.
- Canonical+optimized artifact management adds minor maintenance overhead.

## Follow-Up
1. Apply the same hardening template when onboarding QC/AB/BC equity layers.
2. Reassess vector-tile migration if multi-province payloads exceed acceptable API/map latency.
