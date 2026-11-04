# Provincial Methodology Documentation

This directory contains the maintained methodology notes for the active
provincial emergency department wait-time sources.

## Purpose

These documents are used for:

1. methodology transparency on the public `/methods` surface
2. developer reference when tagging measurements with ontology fields
3. divergence-brief context when users compare unlike metrics
4. current-state documentation for operational and academic review

## Active Province Docs

### Ontario
- File: `ontario-methodology.md`
- Status: current
- Data source: Health Quality Ontario
- Key insight: `TIME_TO_PROVIDER`, `TRIAGE -> PHYSICIAN`, `MEAN`

### Alberta
- File: `alberta-methodology.md`
- Status: current
- Data source: Alberta Health Services Wait Times Portal
- Key insight: `TIME_TO_PROVIDER`, `TRIAGE -> PHYSICIAN`, `POINT_ESTIMATE`

### British Columbia
- File: `bc-methodology.md`
- Status: current
- Data source: PHSA / `edwaittimes.ca`
- Key insight: `TIME_TO_PROVIDER`, `TRIAGE -> PHYSICIAN`, `P90`

### Quebec
- File: `quebec-methodology.md`
- Status: current
- Data source: MSSS Emergency Room Situation Portal
- Verified source fact: estimated wait for non-priority cases to see a doctor
- Legacy project tags: `REGISTRATION -> PHYSICIAN`, `ROLLING_AVG`; the published page does not confirm these details

## Cross-Province Summary

| Province | Source ID | Project Start Tag | Project End Tag | Project Statistic Tag | Patient Scope Evidence | Update Freq |
|----------|-----------|-------------------|-----------------|-----------------------|------------------------|-------------|
| Ontario | `ontario-health` | `TRIAGE` | `PHYSICIAN` | `MEAN` | `ALL` (existing source mapping) | Quarterly |
| Alberta | `alberta-ahs` | `TRIAGE` | `PHYSICIAN` | `POINT_ESTIMATE` | `ALL` (existing source mapping) | ~2 min |
| British Columbia | `bc-phsa` | `TRIAGE` | `PHYSICIAN` | `P90` | `ALL` (existing source mapping) | ~5 min |
| Quebec | `quebec-msss` | `REGISTRATION` (legacy) | `PHYSICIAN` (legacy) | `ROLLING_AVG` (legacy) | `NON_PRIORITY` (published page) | Periodic |

The Ontario, Alberta, and British Columbia `ALL` values above are the existing
project source mappings; they are not separately revalidated here as
independent source-population evidence. Québec's published page explicitly
labels the estimated wait as non-priority, but does not specify the clock
events or statistic. Its other table values are legacy project tags, not
source-confirmed methodology.

Patient scope is currently available in the source documentation and generated
assets, but not in the database `Source` model/table or the source-seeding
contract. The live `/methods` page therefore reports source scope as unknown
until a separately reviewed metadata-schema and reader change. The Québec
scraper remains unchanged and its existing wait measurements retain the
legacy `ALL` tag; that tag must not be described as corrected.

### Deferred Scope-Metadata Activation Gate

This is a prerequisite record, not an active implementation queue. Scope must
not be activated in the Québec producer until all of the following are
reviewed together:

- [ ] Add `default_patient_scope` to the database source model/table, seed and
  upsert contract, and `/methods` reader; unknown source metadata remains
  unknown until then.
- [ ] Add patient scope to the aggregate grain and every aggregate reader/export
  that could combine measurements with different scopes.
- [ ] Only then change the Québec wait-time producer to `NON_PRIORITY`; preserve
  existing rows and aggregates without silent historical relabeling.

## Pairwise Comparability

Matching all five recorded ontology dimensions is a necessary screening
condition, not proof that source methodologies are identical or scientifically
comparable. Current pairwise shorthand:

| Pair | Verdict | Why |
|------|---------|-----|
| ON vs AB | Partial | Same metric and event boundaries, different statistic type (`MEAN` vs `POINT_ESTIMATE`) |
| ON vs BC | Partial | Same metric and event boundaries, different statistic type (`MEAN` vs `P90`) |
| ON vs QC | Not established | Québec clock-event and statistic tags are legacy and unverified |
| AB vs BC | Partial | Same metric and event boundaries, different statistic type (`POINT_ESTIMATE` vs `P90`) |
| AB vs QC | Not established | Québec clock-event and statistic tags are legacy and unverified |
| BC vs QC | Not established | Québec clock-event and statistic tags are legacy and unverified |

Key takeaway:

1. Equal recorded tags do not establish scientific comparability; source definitions and limitations still require review.
2. Ontario, Alberta, and BC have partial recorded-tag alignment and differ on their statistic tags.
3. Québec pairs remain methodologically unestablished because the published page confirms the patient scope but not the clock events or statistic.

## Generated Assets

The downloadable comparison assets in [`docs/assets`](../../../docs/assets/README.md)
are generated from `backend/data/sources/*.json` plus curated evidence and
update-frequency notes in `backend/scripts/generate_methodology_comparison.py`.
The patient-scope values are intentionally kept out of the source-seeding JSON
until the database contract supports them.

## Ontology Quick Reference

### Metric Families

- `TIME_TO_PROVIDER`: time until first physician/provider assessment
- `TOTAL_LOS`: full emergency department length of stay
- `STRETCHER_OCCUPANCY`: occupancy/capacity signal rather than a patient wait

### Start Events

- `TRIAGE`: clock starts after triage assessment
- `REGISTRATION`: clock starts at administrative registration
- `DOOR`: clock starts on arrival
- `UNKNOWN`: source method is unclear or mixed

### End Events

- `PHYSICIAN`: first physician assessment
- `PROVIDER`: first provider assessment
- `DISCHARGE`: discharge from the ED
- `FIRST_ASSESSMENT`: first documented clinical assessment

### Statistic Types

- `MEAN`: arithmetic average
- `POINT_ESTIMATE`: current snapshot / instantaneous estimate
- `P90`: 90th percentile
- `ROLLING_AVG`: moving average over a recent window
- `MEDIAN`: 50th percentile
- `ALGORITHMIC`: model-derived estimate

## Comparability Rule

The recorded-ontology screening check requires all five tags to match:

```python
comparable = (
    measurement_a.metric_family == measurement_b.metric_family
    and measurement_a.start_event == measurement_b.start_event
    and measurement_a.end_event == measurement_b.end_event
    and measurement_a.statistic_type == measurement_b.statistic_type
    and measurement_a.patient_scope == measurement_b.patient_scope
)
```

Unknown patient scope is not a match. Matching recorded tags are necessary,
but do not prove source methods are identical or that a scientific comparison
is valid; review source definitions, populations, and limitations.

If a recorded dimension differs, the UI should generate a divergence brief and
avoid framing the values as a direct apples-to-apples comparison.

## Validation Checklist

Before publishing or revising a methodology document:

- confirm the source URLs still match the maintained source catalog
- confirm ontology tags match the scraper and seeded `sources` metadata
- confirm public copy matches the `/methods` page and generated assets
- confirm comparability examples distinguish recorded tags from source-verified methodology

Last updated: 2026-04-16
