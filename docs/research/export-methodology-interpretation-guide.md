# Export Methodology Interpretation Guide

**Status:** Public research guide
**Date:** 2026-06-12
**Scope:** CSV and JSON exports from `/api/export`

This guide explains how to interpret exported Wait Time Canada data without
discarding the project's methodology safeguards. It is intended for researchers,
journalists, civic technologists, and policy users who need a reproducible
dataset but must avoid invalid cross-system comparisons.

## Core Rule

For raw records, all five recorded ontology dimensions are a necessary
screening condition:

1. `metric_family`
2. `start_event`
3. `end_event`
4. `statistic_type`
5. `patient_scope`

Matching all five tags is not proof that source methods are identical or that a
scientific comparison is valid. Review the original source definitions,
limitations, and population metadata before interpreting differences. If a
field differs or patient scope is unknown, use the export for audit,
provenance, or methodology analysis rather than ranking hospitals or provinces.

## Export Shapes

The export endpoint supports raw and aggregate views:

- `granularity=raw`: recent raw measurement rows, subject to the raw
  measurement retention policy.
- `granularity=hourly`: bounded hourly aggregates derived from recent raw
  measurements and limited to 30-day windows.
- `granularity=daily`, `weekly`, or `monthly`: permanent aggregate rows from
  `measurement_aggregates`.

The current aggregate schema does not retain patient scope, and the export
homogeneity summary groups on four legacy ontology fields. Therefore
`is_homogeneous=true` is not evidence that patient scope matches. Raw exports
include the stored `patient_scope`; aggregate exports cannot support
scope-stratified comparisons until a separately reviewed aggregate/reader
contract is implemented. Québec wait-time rows currently carry the legacy
`ALL` tag even though the published page specifies non-priority cases; this
guide does not relabel those rows.

Exports use `Cache-Control: no-store` so downloadable datasets are not served
from stale shared caches.

Example request:

```bash
curl "http://localhost:3000/api/export?format=json&granularity=monthly&include_methodology=true"
```

## JSON Interpretation

JSON exports include a `metadata.methodology_homogeneity` object. Treat that
object as a first-pass comparability warning.

Example shape:

```json
{
  "methodology_homogeneity": {
    "is_homogeneous": false,
    "distinct_methodology_groups": 2,
    "divergence_note": "This export contains measurements from 2 distinct methodology groups. Direct comparison across groups is scientifically invalid. See methodology_url per record for details.",
    "groups": [
      {
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "MEAN",
        "record_count": 120
      },
      {
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "REGISTRATION",
        "end_event": "PHYSICIAN",
        "statistic_type": "ROLLING_AVG",
        "record_count": 95
      }
    ]
  }
}
```

Recommended interpretation:

- `is_homogeneous=true`: the exported rows share the four fields used by the
  current summary. Patient scope is not part of that summary; inspect raw-row
  scope where available and review source documentation.
- `is_homogeneous=false`: do not rank or compare exported values across the
  listed groups as if they measure the same operational quantity.
- `distinct_methodology_groups`: use this as a grouping variable before any
  descriptive analysis.
- `methodology_url`: preserve this field in downstream datasets and figures so
  source-specific interpretation remains auditable.

## CSV Interpretation

CSV exports expose the same warning in two ways:

- HTTP headers:
  - `X-Methodology-Divergence`
  - `X-Methodology-Groups`
- A leading comment row when the export contains mixed methodology groups:

```csv
# METHODOLOGY DIVERGENCE WARNING: This export contains measurements from 2 distinct methodology groups. Direct comparison across groups is scientifically invalid. See methodology_url per record for details.
period_start,period_end,hospital_id,hospital_name,province,city,latitude,longitude,mean_wait_minutes,median_wait_minutes,p90_wait_minutes,min_wait_minutes,max_wait_minutes,sample_count,std_dev,metric_family,start_event,end_event,statistic_type,source_id,methodology_url
```

When `include_methodology=true`, raw CSV rows include ontology fields for
grouping before analysis. Aggregate exports do not preserve patient scope. If a
CSV parser drops leading comment rows, consumers should still inspect the
methodology headers and ontology columns.

## Safe Analytical Uses

Appropriate uses include:

- showing how provincial reporting methods differ
- filtering to a single methodology group before descriptive summaries
- documenting source provenance and public reporting limitations
- auditing source freshness, coverage, and aggregation windows
- building methodology-aware visualizations that label the metric definition

Inappropriate uses include:

- ranking hospitals from different methodology groups
- claiming one province is faster based only on exported wait values
- treating a `MEAN`, `P90`, `POINT_ESTIMATE`, and `ROLLING_AVG` as
  interchangeable
- treating Quebec `REGISTRATION`-started waits and triage-started waits as the
  same clock
- using the export as medical advice, triage guidance, or care-site
  recommendation logic

## Practical Workflow

1. Export with `include_methodology=true`.
2. Inspect `methodology_homogeneity`.
3. If the export is mixed, group by `metric_family`, `start_event`, `end_event`,
   and `statistic_type`.
4. Preserve `source_id` and `methodology_url` in any derived dataset.
5. Label charts with the metric definition, aggregation level, date window, and
   source limitations.
6. State that the platform audits public reporting, not internal hospital
   operations.

## Related Artifacts

- [API reference](../API.md)
- [Four-province methodology audit draft](methodological-heterogeneity-four-province-audit-draft.md)
- [Ottawa-Gatineau divergence case study](../case-studies/ottawa-gatineau-divergence.md)
- [Metric ontology ADR](../adr/0002-metric-ontology.md)
