# 0010. Region Mapping Coverage Heuristics

Date: 2026-02-07

Status: Accepted

Deciders: Jeremy Dawson

## Context and Problem Statement

Regional analytics requires complete hospital-to-region mappings. Initial Ontario seed mappings covered only a small subset of hospitals, resulting in low coverage and weak regional representativeness.

## Decision Drivers

* Regional dashboards must communicate system-level signals, not sparse subsets
* Mapping maintenance must be operationally practical for iterative updates
* Manual-only mapping does not scale to full Ontario inventory
* Assignment logic must remain transparent and auditable

## Considered Options

* Manual mapping only
* External geospatial boundary service for every assignment
* Heuristic auto-assignment with explicit override precedence and coverage auditing

## Decision Outcome

Chosen option: "Heuristic auto-assignment with explicit overrides and audit tooling."

The system introduces:

* `python -m waittime.cli.region_mapping` for coverage audit and assignment workflows
* deterministic assignment order:
  1. explicit hospital overrides
  2. city/name token rules
  3. coordinate fallbacks
* JSON coverage reports for repeatable operational verification
* coverage telemetry exposed via `/api/analytics/regions`

### Positive Consequences

* Ontario mapping coverage can be raised to full coverage quickly
* Regional analytics endpoint reports mapping completeness explicitly
* Known misclassifications can be corrected safely via overrides
* Assignment process is reproducible, testable, and auditable

### Negative Consequences

* Heuristics can still misclassify edge-case hospitals
* Overrides file requires ongoing maintenance as data inventory evolves
* Region definitions remain project-level approximations unless official boundaries are integrated

## Implementation Details

* New CLI: `backend/src/waittime/cli/region_mapping.py`
* Overrides file: `backend/data/regions/ontario-region-overrides.json`
* API telemetry: `frontend/app/api/analytics/regions/route.ts` (`mapping_coverage`)
* UI status badge: `frontend/components/RegionDashboard.tsx`
* Coverage report artifact path: `backend/data/regions/coverage-report.json` (gitignored)

## Links

* [Related to] [ADR-0008](0008-aggregation-pipeline.md)
* [Related to] [ADR-0009](0009-data-quality-anomaly-detection.md)
* Archived implementation plan: `docs/planning/archive/milestone-15-analytics.md`
