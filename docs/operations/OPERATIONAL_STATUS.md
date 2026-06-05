# Operational Status

This public status document summarizes the project’s source coverage and
operational posture without exposing private deployment details.

## Public Coverage

| Province | Source ID | Public Methodology Summary |
|----------|-----------|----------------------------|
| Quebec | `quebec-msss` | Registration-to-physician rolling average; stretcher occupancy where published |
| Ontario | `ontario-health` | Triage-to-physician mean |
| Alberta | `alberta-ahs` | Triage-to-physician point estimate |
| British Columbia | `bc-phsa` | Triage-to-physician P90 |

## Public Reliability Posture

- Scrapers write source status records after collection attempts.
- Freshness checks use those records to identify stale or failed source updates.
- Data-quality snapshots and anomaly detection provide additional public context.
- Raw measurement rows follow the project retention policy; aggregates are kept
  for long-term trend analysis.

## Public Documentation Boundary

This repository contains public project documentation and reproducible
development information. Deployment details, credentials, monitoring
configuration, private operational notes, and environment-specific production
paths are intentionally excluded from public documentation.

## See Also

- Roadmap: `docs/planning/roadmap.md`
- Data dictionary: `docs/reference/data-dictionary.md`
- Methodology docs: `backend/docs/methodologies/`
