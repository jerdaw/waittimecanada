# 0021. Bounded 30-Day Retention Cleanup Operations

Date: 2026-03-23

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` operations follow-up after a storage alert, raw-retention rollback, and cleanup runtime investigation

## Context and Problem Statement

Wait Time Canada restored its 30-day raw-measurement retention policy after a storage alert exposed the cost of preserving raw history indefinitely. The first corrective cleanup run succeeded, but it also showed that the maintenance workflow was spending most of its runtime in a zero-yield aggregate refresh rather than in the actual delete path.

## Decision Drivers

* Keep storage growth bounded
* Preserve state-change-driven alerting and the current GitHub Actions production posture
* Keep maintenance runs fast enough that CI remains helpful instead of blocking routine development
* Avoid folding expensive, often-no-op aggregate work into every storage cleanup invocation

## Considered Options

* Preserve raw history indefinitely and keep cleanup lightweight
* Keep 30-day raw retention and refresh aggregates on every cleanup run
* Keep 30-day raw retention, delete in bounded batches, and make aggregate refresh an explicit/separate path

## Decision Outcome

Chosen option: "Keep 30-day raw retention, delete in bounded batches, and make aggregate refresh an explicit/separate path", because it restores storage safety while keeping maintenance predictable under free-tier CI constraints.

### Positive Consequences

* Production cleanup once again enforces a rolling 30-day raw-measurement window
* The maintenance workflow stays fast and observable because deletes are batched and aggregate refresh is skipped
* Aggregate refresh can still be triggered deliberately through the existing aggregation tooling when it is actually needed
* State-change-driven heartbeat alerting from ADR-0020 remains intact

### Negative Consequences

* Raw measurements older than 30 days are no longer available for future re-aggregation without backups
* Table/index bloat and storage accounting may still lag immediately after large deletes
* Operators now need to think about aggregate refresh and retention cleanup as separate concerns

## Pros and Cons of the Options

### Preserve raw history indefinitely and keep cleanup lightweight

* Good, because long-range raw analysis remains possible
* Good, because maintenance stays simple
* Bad, because storage growth becomes intentional and expensive on the free tier
* Bad, because the production storage alert showed the policy was no longer acceptable

### Keep 30-day raw retention and refresh aggregates on every cleanup run

* Good, because raw storage remains bounded automatically
* Good, because aggregate freshness is coupled to cleanup by default
* Bad, because the first production remediation run spent most of its runtime in a zero-yield aggregate refresh
* Bad, because maintenance latency becomes dominated by the wrong work

### Keep 30-day raw retention, delete in bounded batches, and separate aggregate refresh

* Good, because storage safety is restored without turning routine cleanup into a long-running workflow
* Good, because batched deletes give operators bounded, observable maintenance behavior
* Good, because aggregate refresh remains available via explicit aggregation commands when needed
* Bad, because the operator story is slightly less "one command does everything"

## Links

* [Supersedes] [0020](0020-raw-retention-and-stateful-alerting.md)
* [Related to] [0008](0008-aggregation-pipeline.md)
* [Related to] [0018](0018-scraper-observability-and-reliability-hardening.md)

## Additional Information

Implementation artifacts:

* Bounded cleanup runtime: `backend/src/waittime/services/database.py`
* Cleanup CLI flags: `backend/src/waittime/cli/cleanup.py`
* Manual cleanup workflow: `.github/workflows/database-cleanup.yml`
* Private deployment timer templates are intentionally excluded from public documentation.
