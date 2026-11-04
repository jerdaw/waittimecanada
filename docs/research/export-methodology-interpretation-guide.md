# Export Methodology Interpretation Guide

**Status:** Public research guide
**Date:** 2026-06-12
**Scope:** CSV and JSON exports from `/api/export`

This guide explains how to interpret exported Wait Time Canada data without
discarding the project's methodology safeguards. It is intended for researchers,
journalists, civic technologists, and policy users who need a reproducible
dataset but must avoid invalid cross-system comparisons.

## Core Rule

For raw records, the export's methodology grouping uses all five recorded
ontology dimensions as a necessary screening condition:

1. `metric_family`
2. `start_event`
3. `end_event`
4. `statistic_type`
5. `patient_scope`

The grouping key is the exact tuple
`(metric_family, start_event, end_event, statistic_type, patient_scope)`; scope
values are not normalized or inferred. Matching all five tags does not prove
that source methods are identical or that a scientific comparison is valid.
Review the original source definitions, limitations, and population metadata
before interpreting differences. If a field differs or scope is unknown, use
the export for audit, provenance, or methodology analysis rather than ranking
hospitals or provinces.

## Export Shapes

The export endpoint supports raw and aggregate views:

- `granularity=raw`: recent raw measurement rows, subject to the raw
  measurement retention policy.
- `granularity=hourly`: bounded hourly aggregates derived from recent raw
  measurements and limited to 30-day windows.
- `granularity=daily`, `weekly`, or `monthly`: permanent aggregate rows from
  `measurement_aggregates`.

Raw JSON rows include the stored `patient_scope`. For methodology summaries,
each group includes `patient_scope` and `patient_scope_status`, and the summary
includes `unknown_patient_scope_records`. `is_homogeneous` is true only when
there is at most one group and every row has a recorded patient scope. A
missing or null scope is emitted as JSON `null`, marked `unknown`, and forces
`is_homogeneous=false` even if there is only one group. Do not interpret an
unknown scope as `ALL`.

The current permanent aggregate schema has no patient-scope column. Aggregate
exports therefore emit `patient_scope: null`, report the scope as unknown, and
cannot establish homogeneity; this is not scope-stratified support. The hourly
export query also does not select or group by patient scope. It reports scope
as unknown and non-homogeneous, but its numeric hourly summaries may already
combine rows from different scopes. That warning does not unmix those values;
do not use hourly results for scope-specific comparisons until a separate
scope-aware query is implemented.

The public Québec source labels the wait estimate “Estimated waiting time for
non-priority cases to see a doctor” ([source note](../data-sources/quebec-research.md)).
The current scraper does not set scope explicitly, so its measurements inherit
the model default `ALL`. This guide does not relabel historical rows. Any
prospective scope change must preserve existing rows as recorded and requires
matching scope support in aggregation and readers before permanent aggregate
results can be interpreted by scope.

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
    "unknown_patient_scope_records": 0,
    "divergence_note": "This export contains 2 distinct methodology groups. Patient scope differs across exported records. Direct comparison across groups is scientifically invalid. See methodology_url per record for details.",
    "groups": [
      {
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "MEAN",
        "patient_scope": "ALL",
        "patient_scope_status": "recorded",
        "record_count": 120
      },
      {
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "REGISTRATION",
        "end_event": "PHYSICIAN",
        "statistic_type": "ROLLING_AVG",
        "patient_scope": "NON_PRIORITY",
        "patient_scope_status": "recorded",
        "record_count": 95
      }
    ]
  }
}
```

When scope is absent from an aggregate result, the route reports one unknown
group rather than treating it as a recorded scope:

```json
{
  "data": [{ "patient_scope": null }],
  "metadata": {
    "methodology_homogeneity": {
      "is_homogeneous": false,
      "distinct_methodology_groups": 1,
      "unknown_patient_scope_records": 1,
      "divergence_note": "Patient scope is missing or unknown for 1 record(s); homogeneity cannot be established. See methodology_url per record for details.",
      "groups": [
        {
          "metric_family": "TIME_TO_PROVIDER",
          "start_event": "TRIAGE",
          "end_event": "PHYSICIAN",
          "statistic_type": "MEAN",
          "patient_scope": null,
          "patient_scope_status": "unknown",
          "record_count": 1
        }
      ]
    }
  }
}
```

Recommended interpretation:

- `is_homogeneous=true`: there is at most one methodology group and every
  included row has a recorded patient scope. This is only a screening result;
  matching tags do not establish identical source methods or remove other
  limitations.
- `is_homogeneous=false`: do not rank or compare exported values across the
  listed groups as if they measure the same operational quantity.
- `distinct_methodology_groups`: use the groups, including their exact
  `patient_scope`, before any descriptive analysis. Scope is one of the five
  grouping dimensions.
- `unknown_patient_scope_records`: if nonzero, scope-based homogeneity cannot
  be established. Keep those records unknown rather than assigning a scope.
- `patient_scope_status="unknown"`: this marks a group whose scope is missing
  or null. Aggregate and hourly exports currently have this status because
  their queries do not supply patient scope.
- `methodology_url`: preserve this field in downstream datasets and figures so
  source-specific interpretation remains auditable.

## CSV Interpretation

CSV exports expose the same warning in two ways:

- HTTP headers:
  - `X-Methodology-Divergence`
  - `X-Methodology-Groups`
- A leading comment row when scope is unknown or the export has multiple
  methodology groups:

```csv
# METHODOLOGY DIVERGENCE WARNING: This export contains 2 distinct methodology groups. Patient scope differs across exported records. Direct comparison across groups is scientifically invalid. See methodology_url per record for details.
timestamp_utc,hospital_id,hospital_name,province,city,latitude,longitude,wait_time_minutes,metric_family,start_event,end_event,statistic_type,patient_scope,source_id,source_name,methodology_url,raw_payload_hash,parser_version
```

When `include_methodology=true`, CSV rows include the ontology fields, including
`patient_scope`. Known values are preserved exactly; null/missing scope is
rendered as `UNKNOWN` and the summary warning prevents it from being treated as
homogeneous. `UNKNOWN` is a display marker, not a stored ontology value. For
permanent aggregate and hourly CSVs, `UNKNOWN` reflects the current absence of
scope in those query results. For example, an aggregate export with one row of
unknown scope currently has this warning and methodology header:

```csv
# METHODOLOGY DIVERGENCE WARNING: Patient scope is missing or unknown for 1 record(s); homogeneity cannot be established. See methodology_url per record for details.
period_start,period_end,hospital_id,hospital_name,province,city,latitude,longitude,mean_wait_minutes,median_wait_minutes,p90_wait_minutes,min_wait_minutes,max_wait_minutes,sample_count,std_dev,metric_family,start_event,end_event,statistic_type,patient_scope,source_id,methodology_url
```

The corresponding `patient_scope` cell is `UNKNOWN`. If a CSV parser drops
leading comment rows, consumers should still inspect the methodology headers
and scope values.

An aggregate or hourly CSV with one unknown-scope row currently reports
`X-Methodology-Divergence: true` and `X-Methodology-Groups: 1`; the leading
comment explains that homogeneity cannot be established. The group count is
not a count of unknown rows; use `unknown_patient_scope_records` in JSON for
that count.

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
3. For raw records with recorded scope, group by `metric_family`, `start_event`,
   `end_event`, `statistic_type`, and the exact `patient_scope` value. Do not
   merge `ALL` with `NON_PRIORITY` or substitute `ALL` when scope is unknown.
4. For hourly or permanent aggregate exports, treat `patient_scope: null` /
   `UNKNOWN` as unknown and do not interpret them as scope-specific groups. The
   current hourly warning does not prevent its numeric summaries from mixing
   scopes.
5. Preserve `source_id` and `methodology_url` in any derived dataset.
6. Label charts with the metric definition, aggregation level, date window, and
   source limitations.
7. State that the platform audits public reporting, not internal hospital
   operations.

## Related Artifacts

- [API reference](../API.md)
- [Four-province methodology audit draft](methodological-heterogeneity-four-province-audit-draft.md)
- [Ottawa-Gatineau divergence case study](../case-studies/ottawa-gatineau-divergence.md)
- [Metric ontology ADR](../adr/0002-metric-ontology.md)
