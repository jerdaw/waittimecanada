# ADR 0012: Occupancy Availability Contract

## Status
Accepted (2026-02-08)

## Context
Milestone 12 includes occupancy statistics as an optional capability. Current provincial wait-time
feeds do not consistently expose `patients_waiting` and `patients_in_treatment` fields.

Without an explicit contract, users may misinterpret missing occupancy values as system failure
instead of true source unavailability.

## Decision
Implement a dedicated occupancy analytics endpoint with explicit status semantics:

- Endpoint: `GET /api/analytics/occupancy?province=ON`
- Status `not_available_yet` when required source fields are absent
- Status `no_reporting_data` when fields exist but recent rows are empty
- Status `available` when occupancy metrics are present and reportable

The analytics UI must display a clear "not available yet" state rather than generic error text.

## Consequences

### Positive
- Makes data availability constraints explicit and auditable.
- Prevents overclaiming occupancy intelligence when source fields do not exist.
- Preserves a stable API/UX contract for future occupancy ingestion.

### Tradeoff
- Adds an additional endpoint and state handling branch in analytics UI.

## Follow-Up
1. Extend scraper/database ingestion once occupancy fields become available.
2. Add methodological notes for occupancy comparability before cross-site interpretation.
3. Backfill occupancy aggregates after schema rollout.
