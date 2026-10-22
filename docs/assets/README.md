# Downloadable Assets

This directory contains generated methodology-comparison assets used for
research, documentation, and `/methods` support material.

## Files

- `methodology-comparison.csv`
- `methodology-comparison.html`
- `methodology-pairwise-comparability.csv`
- `methodology-pairwise-comparability.html`

## Registered Ontology Tags and Scope Evidence

| Province | Source ID | Project Start Tag | Project End Tag | Project Statistic Tag | Patient Scope Evidence |
|----------|-----------|-------------------|-----------------|-----------------------|------------------------|
| Ontario | `ontario-health` | `TRIAGE` | `PHYSICIAN` | `MEAN` | `ALL` (existing mapping; not independently verified) |
| Alberta | `alberta-ahs` | `TRIAGE` | `PHYSICIAN` | `POINT_ESTIMATE` | `ALL` (existing mapping; not independently verified) |
| British Columbia | `bc-phsa` | `TRIAGE` | `PHYSICIAN` | `P90` | `ALL` (existing mapping; not independently verified) |
| Quebec | `quebec-msss` | `REGISTRATION` (legacy) | `PHYSICIAN` (legacy) | `ROLLING_AVG` (legacy) | `NON_PRIORITY` (published page) |

Québec's published page confirms a non-priority wait estimate, but does not
specify its clock events or statistic. Its event/statistic values above are
legacy project tags, not source-confirmed methodology. The Ontario, Alberta,
and British Columbia `ALL` values are existing project source mappings, not
independent source-population evidence. Existing Québec measurements remain
tagged `ALL`; no stored data or producer was changed.

These generated assets use curated scope/evidence notes from
`backend/scripts/generate_methodology_comparison.py`; scope is intentionally
not added to the source-seeding JSON because the database `Source` contract
does not yet support it. The live `/methods` page therefore treats source scope
as unknown until a separately reviewed schema/reader change.

## Interpretation

- Matching all five recorded ontology dimensions is a necessary screening
  condition, not proof that source methods are identical or scientifically
  comparable.
- Ontario, Alberta, and British Columbia share `TRIAGE -> PHYSICIAN` event
  boundaries but still diverge on statistic type.
- Québec pairwise method comparability is not established because the public
  page does not document its clock events or statistic.

The pairwise asset uses the repository's shorthand comparability labels:

- `Yes`: all five recorded ontology tags match; source definitions still need review
- `Partial`: some, but not all, recorded tags match
- `No`: few recorded tags match
- `Not established`: source documentation is incomplete for a required dimension

## Generation

Regenerate the assets with:

```bash
python3 backend/scripts/generate_methodology_comparison.py
```

The generator reads existing project tags from `backend/data/sources/*.json`
and uses curated scope/evidence and refresh notes from
`backend/scripts/generate_methodology_comparison.py`. Do not add
`default_patient_scope` to the seed JSON until a separately reviewed database
contract can persist and serve it. Regenerate these assets after changing the
source tags or curated evidence notes.

## CSV Example

```csv
province,province_code,source_id,metric_family,start_event,end_event,statistic_type,patient_scope,tag_basis,update_frequency,data_source,notes
Quebec,QC,quebec-msss,TIME_TO_PROVIDER,REGISTRATION,PHYSICIAN,ROLLING_AVG,NON_PRIORITY,Published page identifies non-priority cases,Published page confirms patient scope only; other tags are legacy and unverified,Periodic,MSSS Emergency Room Situation Portal,Published page identifies an estimated wait for non-priority cases; it does not confirm the legacy event or statistic tags shown here.
```

## Related Docs

- [backend/docs/methodologies/README.md](../../backend/docs/methodologies/README.md)
- [backend/docs/methodologies/ontario-methodology.md](../../backend/docs/methodologies/ontario-methodology.md)
