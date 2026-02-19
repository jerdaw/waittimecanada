# 0018. Scraper Observability and Reliability Hardening

Date: 2026-02-19

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` P1 ops items ("scraper reliability hardening" + "scraper failure visibility")

## Context and Problem Statement

Scraper failures were previously represented as free-text errors with limited metadata, and retry/timeout behavior was inconsistent across provincial implementations. This created risk of silent data decay and slowed triage when upstream sources changed or became unavailable.

## Decision Drivers

* Prevent silent scraper failure and stale data exposure
* Standardize retry/backoff/timeout policy across ON/QC/AB/BC
* Preserve backward compatibility for existing health consumers
* Keep implementation lightweight within current infrastructure and budget limits

## Considered Options

* Keep existing heartbeat fields and rely on log inspection only
* Add a dedicated per-run event table plus external observability stack
* Extend `scraper_status` with structured failure and last-success metadata, and enforce shared reliability helpers

## Decision Outcome

Chosen option: "Extend `scraper_status` with structured metadata and standardize reliability behavior in shared scraper helpers", because it delivers immediate operational visibility with minimal infrastructure overhead and safe additive schema changes.

### Positive Consequences

* Operators can distinguish `upstream_unavailable` vs `parser_breakage` vs `infra_runtime` vs `persistence_failure`
* `/api/health` and CLI now expose last-known-good and last-error in one view
* Alerting can gate on `consecutive_failures` instead of a single noisy failure
* Rollback remains low risk because legacy heartbeat fields remain intact

### Negative Consequences

* Additional schema and contract surface area to maintain
* Classification heuristics can still misclassify edge-case failures as `unknown`
* Retry policies can increase run duration if not monitored

## Pros and Cons of the Options

### Keep existing heartbeat model

* Good, because no migration or contract changes required
* Bad, because triage remains manual and slow
* Bad, because silent decay risk remains high

### Add external observability/event-history stack now

* Good, because deeper analytics and audit trail become possible
* Bad, because it increases cost and operational complexity
* Bad, because it exceeds current project resource constraints

### Extend existing heartbeat + shared reliability helpers

* Good, because additive schema preserves compatibility
* Good, because it delivers immediate observability in existing CLI/API paths
* Bad, because detailed per-run historical analytics remain limited

## Additional Information

Implemented artifacts include:

- Migration: `backend/migrations/013_add_scraper_observability_columns.sql`
- Shared classification + retry constants: `backend/src/waittime/scrapers/observability.py`
- Heartbeat metadata read/write: `backend/src/waittime/services/database.py`, `backend/src/waittime/services/heartbeat.py`
- Operator surfaces: `backend/src/waittime/cli/check_heartbeat.py`, `frontend/app/api/health/route.ts`

Failure category contract:

- `upstream_unavailable`
- `parser_breakage`
- `infra_runtime`
- `persistence_failure`
- `unknown`
