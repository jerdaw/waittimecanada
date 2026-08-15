# Operational Status

This public status document summarizes the project’s source coverage and
operational posture without exposing private deployment details.

## Public Coverage

| Province         | Source ID        | Public Methodology Summary                                                                                                                                   |
| ---------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Quebec           | `quebec-msss`    | Registration-to-physician rolling average; stretcher occupancy where published                                                                               |
| Ontario          | `ontario-health` | Monthly mean from triage or registration, whichever is earlier, to first qualifying-provider assessment; legacy runtime event tags remain under revalidation |
| Alberta          | `alberta-ahs`    | Triage-to-physician point estimate                                                                                                                           |
| British Columbia | `bc-phsa`        | Triage-to-physician P90                                                                                                                                      |

## Public Reliability Posture

- The scraper workflow is configured to check sources hourly; scheduled starts can be delayed or skipped and provincial publication timing varies.
- Scrapers write source status records after collection attempts.
- Twice-hourly freshness checks use those records to identify stale or failed source updates. One newly opened or changed incident can request one recovery when no scraper run is active; unchanged failures remain visible without recurring recovery dispatch.
- The public stale threshold is 120 minutes; status timestamps, not the scheduler label, are the freshness evidence.
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
