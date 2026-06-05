# Downloadable Assets

This directory contains generated methodology-comparison assets used for
research, documentation, and `/methods` support material.

## Files

- `methodology-comparison.csv`
- `methodology-comparison.html`
- `methodology-pairwise-comparability.csv`
- `methodology-pairwise-comparability.html`

## Current Active Province Semantics

| Province | Source ID | Start Event | End Event | Statistic Type |
|----------|-----------|-------------|-----------|----------------|
| Ontario | `ontario-health` | `TRIAGE` | `PHYSICIAN` | `MEAN` |
| Alberta | `alberta-ahs` | `TRIAGE` | `PHYSICIAN` | `POINT_ESTIMATE` |
| British Columbia | `bc-phsa` | `TRIAGE` | `PHYSICIAN` | `P90` |
| Quebec | `quebec-msss` | `REGISTRATION` | `PHYSICIAN` | `ROLLING_AVG` |

## Interpretation

- No active cross-province pair is directly comparable because no pair matches
  all four ontology dimensions.
- Ontario, Alberta, and British Columbia share `TRIAGE -> PHYSICIAN` event
  boundaries but still diverge on statistic type.
- Quebec remains distinct because it starts the clock at `REGISTRATION`.

The pairwise asset uses the repository's shorthand comparability labels:

- `Yes`: all four ontology dimensions match
- `Partial`: some alignment exists, but at least one ontology dimension differs
- `No`: very limited alignment across the ontology dimensions

## Generation

Regenerate the assets with:

```bash
python3 backend/scripts/generate_methodology_comparison.py
```

The generator now derives the province ontology rows from the canonical source
catalog in `backend/data/sources/*.json` and adds curated refresh/notes
metadata. If Ontario, Alberta, BC, or Quebec source definitions change, update
the canonical source JSON first and then regenerate the assets.

## CSV Example

```csv
province,province_code,source_id,metric_family,start_event,end_event,statistic_type,update_frequency,data_source,notes
Ontario,ON,ontario-health,TIME_TO_PROVIDER,TRIAGE,PHYSICIAN,MEAN,Quarterly,Health Quality Ontario,Historical mean TRIAGE → PHYSICIAN wait times from Ontario's official performance reporting.
```

## Related Docs

- [backend/docs/methodologies/README.md](../../backend/docs/methodologies/README.md)
- [backend/docs/methodologies/ontario-methodology.md](../../backend/docs/methodologies/ontario-methodology.md)
