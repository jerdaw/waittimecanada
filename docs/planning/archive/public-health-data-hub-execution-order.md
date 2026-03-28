# Public Health Data Hub Batch A Execution Order

**Created:** 2026-03-27
**Status:** Archived after Batch A delivery
**Related:** `docs/planning/implementation/archived/public-health-data-hub-batch-a-plan.md`

---

## Summary

This document records the final pre-implementation decisions for Public Health Data Hub Batch A so the implementation phase can proceed without reopening planning questions.

These decisions are execution constraints, not suggestions.

---

## Locked Preconditions

### Approved source set

Batch A implementation is locked to the source set already approved in:

- `docs/research/public-health-data-hub-batch-a-legal-review.md`

That means:

- allowed:
  - MOHSERLO
  - ODHF
  - OpenStreetMap AED fallback
  - Health Canada recalls dataset and RSS
  - Drug Product Database API
  - AQHI GeoMet
- excluded from Batch A:
  - AED Foundation direct ingestion without separate permission/access
  - Drug Shortages Canada
  - Ontario naloxone map
  - any new source not already reviewed

### Public-facing copy posture

Batch A uses the conservative caveat and stale/unavailable copy approved in chat and grounded in:

- `docs/planning/public-health-data-hub-freshness-safety-rules.md`

Locked wording set:

- facility directory:
  `Reference directory data. This is not a live operational status feed.`
- AED:
  `Crowdsourced AED data. Locations may be incomplete or outdated. In an emergency, call 911 immediately.`
- alerts:
  `Official recall and safety alert data from Health Canada. Last refreshed {timestamp}.`
- AQHI:
  `Official AQHI forecast from Environment and Climate Change Canada. Conditions may change.`
- stale state:
  `This information may be outdated. Last refreshed {timestamp}.`
- temporarily unavailable:
  `This source is temporarily unavailable right now.`
- suppressed state:
  `This information is currently hidden because freshness or source requirements are not being met.`
- AED labels:
  - badge: `Crowdsourced`
  - completeness label: `Incomplete coverage`

Any material deviation from this wording requires human sign-off.

---

## Execution Order

Implementation proceeds package-by-package in this exact order:

1. `Foundation`
2. `Facilities`
3. `Alerts`
4. `AQHI`
5. `AED`
6. `Final page integration / navigation`

This order is chosen to:

- establish schema, validation, and shared API primitives first
- land the lowest-risk approved public sources before the most caution-heavy one
- keep AED work later because it carries the strongest caveat and sign-off burden
- let tests validate each layer before later packages depend on it

The authoritative package definitions remain in:

- `docs/planning/archive/public-health-data-hub-agent-execution-readiness.md`

---

## Merge Rule

Batch A should be developed incrementally, but merged with discipline.

Locked merge rule:

- internal foundation work may merge once stable and tested
- public-facing work may merge only when the `/resources` route remains coherent and tested

Practical effect:

- it is acceptable to merge internal schema, persistence, validation, and non-user-facing foundations on their own
- it is not acceptable to expose a half-formed public module that fails the freshness, caveat, or degraded-state expectations

---

## Implementation Start Condition

Implementation may begin when:

1. the approved source set remains accepted as written
2. the conservative copy posture remains accepted
3. the package-by-package execution order is followed
4. the merge rule above is preserved

If any of those conditions change, update this document and the governing Batch A planning artifacts before coding continues.
