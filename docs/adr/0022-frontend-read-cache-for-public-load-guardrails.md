# 0022. Frontend Read Cache for Public Transfer Guardrails

Date: 2026-03-26

Status: Accepted

Deciders: Jeremy Dawson

## Context and Problem Statement

Public anonymous reads can repeatedly request the same health, hospital,
resource, and analytics payloads. Without caching, those repeated reads increase
database and network load even when scraper cadence, raw retention, and
aggregate storage are behaving as intended.

## Decision Drivers

* Reduce repeated database reads without reducing data collection fidelity
* Avoid adding infrastructure that is unnecessary for the current scale
* Preserve explicit freshness windows for health, hospital, resource, and
  analytics routes
* Keep user-specific and export routes uncached

## Considered Options

* Reduce scraper cadence and accept less-fresh public data
* Add an external shared cache layer
* Add short-lived in-process response caching for read-heavy anonymous routes

## Decision Outcome

Chosen option: "Add short-lived in-process response caching for read-heavy
anonymous routes." This reduces repeated reads for cacheable public routes
without changing scraper behavior, storage policy, or public freshness caveats.

### Positive Consequences

* Repeat reads for common anonymous API routes can be served from a short-lived
  server cache.
* Shared cache-header TTLs remain the route-level freshness contract.
* No database migration, schema change, or scraper cadence change is required.

### Negative Consequences

* Cache state is per process and disappears on restart.
* First-hit latency and expensive cache misses still matter.
* Operators still need private monitoring for database/network pressure.

## Route Policy

* Cacheable: anonymous read-heavy health, status, hospital, resource, and
  analytics routes.
* Not cacheable: user-specific routes, geolocation, exports, and any endpoint
  where stale output would violate the user contract.

## Links

* [Related to] [0017](0017-domain-rebrand-wait-time-ca.md)
* [Related to] [0021](0021-bounded-retention-cleanup-operations.md)

## Implementation Artifacts

* `frontend/utils/server-cache.ts`
* `frontend/utils/cache.ts`
* `frontend/app/api/health/route.ts`
* `frontend/app/api/status/route.ts`
* `frontend/app/api/hospitals/route.ts`
* `frontend/app/api/resources/route.ts`
* `frontend/app/api/analytics/benchmarks/route.ts`
* `frontend/app/api/analytics/trends/route.ts`
