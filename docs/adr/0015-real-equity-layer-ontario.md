# ADR 0015: Real Equity Layer Integration (Ontario, StatsCan 2021)

## Status
Accepted (2026-02-18)

## Context
ADR-0011 delivered a scaffold-first equity layer to validate UI/API contracts without claiming real socioeconomic inference.
Milestone 28 requires upgrading Ontario to real census tract income overlays while preserving methodological transparency and rollout safety.

## Decision
For Ontario, replace placeholder tract linkage with processed Statistics Canada 2021 census tract data:

1. Use a reproducible local processing script with manifest output.
2. Normalize served feature properties to a stable frontend contract:
   - `tract_id`
   - `tract_name`
   - `income_quintile` (`0-5`, where `0 = No Data`)
   - `median_household_income`
   - `population_2021` (optional)
3. Exclude quintile `0` from low-income linkage calculations (`low-income := quintiles 1-2`).
4. Keep rollout Ontario-only for M28; other provinces remain explicit `not_available_yet`.
5. Preserve attribution and limitations in API metadata and UI copy.

## Rationale
- Aligns with "one province at a time" reliability discipline.
- Improves claim defensibility for Scholar/Advocate narrative by replacing placeholder linkage.
- Avoids schema churn and operational risk by using static processed layer files.
- Maintains transparency where data is absent/suppressed via explicit quintile `0`.

## Consequences

### Positive
- Ontario equity overlay and linkage metrics are based on real tract data.
- Processing provenance is captured via manifest output.
- API/UI behavior is explicit for unsupported provinces.

### Tradeoff
- Data reflects 2021 census period, not current income distribution.
- Census tracts are administrative geographies and not equivalent to lived neighborhoods.
- Cross-province equity comparisons remain deferred until each province is onboarded.

## Follow-Up
1. Apply the same ingestion/manifest/test template to QC, AB, and BC in a follow-up milestone.
2. Reassess GeoJSON size/performance after additional provinces and move to vector tiles if required.
