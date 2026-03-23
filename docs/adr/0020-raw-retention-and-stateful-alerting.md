# 0020. Raw Retention and Stateful Alerting Operations

Date: 2026-03-13

Status: Superseded

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` ops maintenance follow-up after the VPS frontend cutover, alert storm cleanup, and historical-data retention hardening

Superseded on 2026-03-23 by `docs/adr/0021-bounded-retention-cleanup-operations.md`.

## Context and Problem Statement

Wait Time Canada now needs to preserve raw measurements for long-term historical analysis, while still operating within a free-tier-aware GitHub Actions and Neon footprint. At the same time, the previous stateless heartbeat alerting model produced repeated stale/error notifications during disruption windows, and broad maintenance/backfill jobs were timing out.

## Decision Drivers

* Preserve the full raw audit trail for future historical analysis
* Reduce operational noise from repeated stale/error alerts
* Keep production operations reliable within GitHub Actions and Neon constraints
* Avoid recomputing broad historical aggregates as part of routine maintenance

## Considered Options

* Keep 30-day raw retention and stateless heartbeat alerting
* Preserve raw history indefinitely but continue broad aggregate refresh in maintenance
* Preserve raw history indefinitely, make alerting state-change driven, and keep routine maintenance lightweight

## Decision Outcome

Chosen option: "Preserve raw history indefinitely, make alerting state-change driven, and keep routine maintenance lightweight", because it keeps the full research-grade audit trail while reducing alert storms and avoiding fragile maintenance workflows.

### Positive Consequences

* Raw measurements remain available for longitudinal analysis and future re-aggregation
* Exact duplicate observations are suppressed without deleting legitimate later measurements
* Stale/error alerts fire once per incident and emit a single recovery notice when healthy again
* Weekly maintenance can finish quickly because it no longer tries to recompute broad aggregate windows
* Hourly collection and a 120-minute stale threshold match the live GitHub Actions operating posture

### Negative Consequences

* Database growth is now intentional and must be monitored
* Aggregate freshness requires a dedicated incremental path rather than a one-size-fits-all maintenance job
* Historical ADRs that mention older thresholds remain valid as historical context, not live posture

## Pros and Cons of the Options

### Keep 30-day retention and stateless alerts

* Good, because storage growth remains bounded automatically
* Good, because the original maintenance flow is conceptually simple
* Bad, because historical raw analysis is artificially limited
* Bad, because repeated stale/error notifications create alert fatigue

### Preserve raw history but keep broad aggregate maintenance

* Good, because aggregate tables stay refreshed from one routine workflow
* Good, because it reuses existing aggregation logic
* Bad, because the broad maintenance path timed out against the live production footprint
* Bad, because routine operations become more fragile than the project needs

### Preserve raw history, stateful alerts, lightweight maintenance

* Good, because raw data becomes the canonical long-term evidence layer
* Good, because alerting reflects incident transitions instead of repeating the same noise
* Good, because routine maintenance becomes fast and predictable again
* Bad, because aggregate refresh needs a separate bounded path

## Links

* [Related to] [0006](0006-dead-mans-switch-monitoring.md)
* [Related to] [0008](0008-aggregation-pipeline.md)
* [Related to] [0018](0018-scraper-observability-and-reliability-hardening.md)

## Additional Information

Implementation artifacts:

* Raw retention hardening: `backend/migrations/016_add_measurement_retention_efficiency_guards.sql`
* Stateful alerting: `backend/migrations/017_add_scraper_alert_state.sql`
* Lightweight maintenance: `backend/src/waittime/cli/cleanup.py`
* Storage reporting: `backend/src/waittime/cli/storage_stats.py`
* Stateful heartbeat checks: `backend/src/waittime/cli/check_heartbeat.py`
