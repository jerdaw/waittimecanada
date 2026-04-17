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
- Key insight: `TIME_TO_PROVIDER`, `REGISTRATION -> PHYSICIAN`, `ROLLING_AVG`

## Cross-Province Summary

| Province | Source ID | Start Event | End Event | Statistic Type | Update Freq |
|----------|-----------|-------------|-----------|----------------|-------------|
| Ontario | `ontario-health` | `TRIAGE` | `PHYSICIAN` | `MEAN` | Quarterly |
| Alberta | `alberta-ahs` | `TRIAGE` | `PHYSICIAN` | `POINT_ESTIMATE` | ~2 min |
| British Columbia | `bc-phsa` | `TRIAGE` | `PHYSICIAN` | `P90` | ~5 min |
| Quebec | `quebec-msss` | `REGISTRATION` | `PHYSICIAN` | `ROLLING_AVG` | Periodic |

## Pairwise Comparability

No active cross-province pair is directly comparable under the repository rule
that all four ontology dimensions must match. Current pairwise shorthand:

| Pair | Verdict | Why |
|------|---------|-----|
| ON vs AB | Partial | Same metric and event boundaries, different statistic type (`MEAN` vs `POINT_ESTIMATE`) |
| ON vs BC | Partial | Same metric and event boundaries, different statistic type (`MEAN` vs `P90`) |
| ON vs QC | Partial | Different `start_event` and `statistic_type` |
| AB vs BC | Partial | Same metric and event boundaries, different statistic type (`POINT_ESTIMATE` vs `P90`) |
| AB vs QC | Partial | Different `start_event` and `statistic_type` |
| BC vs QC | Partial | Different `start_event` and `statistic_type` |

Key takeaway:

1. No province pair is directly comparable.
2. Ontario, Alberta, and BC align on `TRIAGE -> PHYSICIAN` but still diverge on statistic type.
3. Quebec remains the most distinct current source because it starts the clock at `REGISTRATION`.

## Generated Assets

The downloadable comparison assets in [`docs/assets`](/home/jer/repos/waittimecanada/docs/assets/README.md)
are generated from `backend/data/sources/*.json` plus curated update-frequency
notes in `backend/scripts/generate_methodology_comparison.py`. Keep the source
catalog aligned before regenerating assets.

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

Two measurements are directly comparable if and only if:

```python
comparable = (
    measurement_a.metric_family == measurement_b.metric_family
    and measurement_a.start_event == measurement_b.start_event
    and measurement_a.end_event == measurement_b.end_event
    and measurement_a.statistic_type == measurement_b.statistic_type
)
```

If any dimension differs, the UI should generate a divergence brief and avoid
framing the values as a direct apples-to-apples comparison.

## Validation Checklist

Before publishing or revising a methodology document:

- confirm the source URLs still match the maintained source catalog
- confirm ontology tags match the scraper and seeded `sources` metadata
- confirm public copy matches the `/methods` page and generated assets
- confirm any comparability examples use current active province semantics

Last updated: 2026-04-16
