# 0025. Data-Quality Scrape-Window and Runtime Environment Contracts

Date: 2026-04-15

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` repo-maintenance follow-up for data-quality correctness, runtime bootstrap hardening, and heartbeat threshold alignment

## Context and Problem Statement

The quality stack originally treated each `measurements` row as if it were a
separate scraper run. That stopped being defensible once Quebec scraper passes
could emit multiple metric families in the same hour for the same hospital,
which inflated hospital/source quality scores and public hospital coverage
summaries. At the same time, backend runtime bootstrap still probed secret env
files directly, and heartbeat stale defaults had drifted away from the live
120-minute operational contract.

## Decision Drivers

* Keep quality metrics semantically tied to actual scraper coverage, not row shape
* Preserve explicit, auditable runtime configuration for secrets
* Align backend health defaults with the public and workflow-facing 120-minute posture
* Avoid unnecessary public API field churn while fixing the underlying math

## Considered Options

* Keep row-based quality counting and document the caveat
* Fix only the frontend hospital route and leave backend snapshots unchanged
* Define quality coverage as distinct UTC hourly scrape windows, require process env for backend runtime bootstrap, and centralize the live heartbeat threshold

## Decision Outcome

Chosen option: "Define quality coverage as distinct UTC hourly scrape windows,
require process-env `DATABASE_URL` for backend runtime bootstrap, and
centralize the 120-minute heartbeat default", because it fixes the semantic
error at the source, removes secret-file probing from runtime code, and keeps
health/status behavior aligned across backend, frontend, workflows, and docs.

### Positive Consequences

* Hospital and source quality metrics now reflect actual hourly scrape coverage
  even when one scraper pass emits multiple measurement rows
* `data_quality_snapshots` and public `/api/data-quality` hospital summaries use
  the same coverage semantics
* Invalid `/api/data-quality` parameter combinations fail fast with `400`
  instead of returning the wrong response shape
* Backend services now require `DATABASE_URL` from the process environment or an
  explicit constructor argument, which matches the repository secret-handling
  posture
* Heartbeat stale defaults now stay aligned with the live 120-minute
  operational threshold

### Negative Consequences

* Historical snapshot records from before this fix remain based on the older
  row-count semantics unless separately recomputed
* Local operators who relied on implicit `.env.local` loading must now export
  `DATABASE_URL` explicitly before backend runtime commands
* Quality response fields keep legacy names such as `actual_scrapes`, so
  documentation must carry the semantic clarification

## Pros and Cons of the Options

### Keep row-based quality counting and document the caveat

* Good, because no code or contract changes are required
* Bad, because the stored and public quality metrics remain incorrect
* Bad, because documentation cannot compensate for incorrect operational math

### Fix only the frontend hospital route and leave backend snapshots unchanged

* Good, because the user-facing hospital endpoint would improve quickly
* Good, because fewer backend tests and docs would need to change
* Bad, because backend snapshots, trends, and diffs would remain inflated
* Bad, because frontend and backend quality semantics would drift further apart

### Define quality coverage as distinct UTC hourly scrape windows and explicit runtime env contracts

* Good, because all quality surfaces share the same scrape-window semantics
* Good, because runtime secret handling becomes explicit and reviewable
* Good, because heartbeat/status behavior stays aligned across operational surfaces
* Bad, because operators lose the convenience of implicit runtime env-file loading

## Links

* [Related to] [0009](0009-data-quality-anomaly-detection.md)
* [Related to] [0018](0018-scraper-observability-and-reliability-hardening.md)

## Additional Information

Implementation artifacts:

* `backend/src/waittime/services/data_quality.py`
* `backend/src/waittime/services/database.py`
* `backend/src/waittime/services/heartbeat.py`
* `backend/src/waittime/services/runtime_config.py`
* `frontend/app/api/data-quality/route.ts`
* `frontend/utils/validations.ts`
* `docs/API.md`
