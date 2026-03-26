# 0022. Frontend Read Cache for Neon Transfer Guardrails

Date: 2026-03-26

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` Neon public-transfer follow-up after the shared-VPS frontend launch

## Context and Problem Statement

The shared-VPS frontend now serves the public `wait-time.ca` traffic directly,
but the production database remains on Neon. A March 2026 public-transfer alert
showed that repeated anonymous reads from the same API routes could exhaust the
free-tier network budget even when scraper cadence, raw-retention policy, and
aggregate storage were all behaving as intended.

## Decision Drivers

* Reduce public transfer from Neon without reducing data collection or storage fidelity
* Keep the live direct-VPS frontend path simple to operate
* Avoid new infrastructure such as Redis or CDN-only cache dependencies
* Preserve explicit freshness windows for health, hospital, and analytics routes

## Considered Options

* Reduce scraper cadence and accept less-fresh public data
* Upgrade Neon immediately for more transfer headroom
* Add an external shared cache layer
* Add short-lived in-process response caching for read-heavy anonymous routes

## Decision Outcome

Chosen option: "Add short-lived in-process response caching for read-heavy
anonymous routes", because it cuts repeated Neon reads on the live VPS path
without changing data collection/storage policy or adding another service to
operate.

### Positive Consequences

* Repeat reads for `/api/health`, `/api/status`, `/api/hospitals`,
  `/api/hospitals/[slug]/trends`, and the main analytics routes no longer hit
  Neon every time on the shared VPS path
* Existing shared cache-header TTLs remain the route-level freshness contract
* No database migration, schema change, or scraper cadence change was required
* The production fix is deploy-only and easy to verify through the normal VPS
  release flow

### Negative Consequences

* Cache state is per-process and disappears on container restart
* The cache does not help route patterns that remain intrinsically expensive on
  their first miss
* Operators still need to watch Neon transfer trends and be ready to optimize
  the `/api/hospitals` data shape further if growth continues

## Pros and Cons of the Options

### Reduce scraper cadence and accept less-fresh public data

* Good, because it reduces write and read pressure together
* Good, because it needs little application work
* Bad, because it compromises the freshness contract unnecessarily
* Bad, because the alert was about transfer, not storage loss or scraper cost

### Upgrade Neon immediately for more transfer headroom

* Good, because it creates immediate budget headroom
* Good, because behavior stays unchanged
* Bad, because it treats spend as the first response instead of fixing obvious
  repeated reads
* Bad, because it weakens free-tier cost discipline

### Add an external shared cache layer

* Good, because cache state would survive process restarts and scale beyond one
  container
* Good, because cache hit ratios could be shared across instances
* Bad, because it adds infrastructure and operational complexity the project
  does not currently need
* Bad, because the live frontend path only has one public container today

### Add short-lived in-process response caching for read-heavy anonymous routes

* Good, because it addresses the repeated-read problem directly
* Good, because it keeps the production architecture simple
* Good, because it preserves the existing data collection and retention model
* Bad, because first-hit latency and per-process cache limits still matter

## Links

* [Related to] [0017](0017-domain-rebrand-wait-time-ca.md)
* [Related to] [0021](0021-bounded-retention-cleanup-operations.md)

## Additional Information

Implementation artifacts:

* `frontend/utils/server-cache.ts`
* `frontend/app/api/health/route.ts`
* `frontend/app/api/status/route.ts`
* `frontend/app/api/hospitals/route.ts`
* `frontend/app/api/hospitals/[slug]/trends/route.ts`
* `frontend/app/api/analytics/benchmarks/route.ts`
* `frontend/app/api/analytics/trends/route.ts`
* `frontend/app/api/analytics/regions/route.ts`
* `frontend/app/api/analytics/occupancy/route.ts`
* `frontend/app/[locale]/status/page.tsx`
