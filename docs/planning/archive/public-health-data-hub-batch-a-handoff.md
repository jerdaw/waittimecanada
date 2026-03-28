# Public Health Data Hub Batch A Handoff Brief

**Created:** 2026-03-27
**Status:** Archived after Batch A delivery
**Related:** `docs/planning/archive/public-health-data-hub-preplan.md`

---

## Summary

The planning package supports writing a real milestone plan for **Batch A**.

**Recommended Batch A scope:**

1. provider and facility baseline
2. AED source strategy
3. recalls and safety alerts
4. AQHI environmental overlay

This should be planned as a **module inside Wait Time Canada**, not as a separate product surface.

---

## Why This Batch Wins

This batch has the best overall mix of:

- public value
- source legitimacy
- machine readability
- acceptable freshness posture
- manageable maintenance burden
- strong narrative fit with the current project

It also avoids the biggest traps identified in the validation pass:

- HTML-only naloxone dependence
- slow-cadence EMS reporting as a first consumer feature
- partner-gated data without a real access path

---

## What The Next Milestone Plan Should Cover

### 1. Source catalog foundation

The milestone plan should begin by defining the product-side metadata model for public data sources:

- connector type
- provenance URL
- update cadence
- reuse / license flag
- freshness sensitivity
- operational risk
- intended usage mode

This is the enabling layer for every later domain.

### 2. Provider and facility baseline

Use:

- MOHSERLO as the Ontario-first facility baseline
- ODHF as secondary cross-check and future-expansion baseline

The milestone plan should treat this as directory and map infrastructure, not as live operational status.

### 3. AED strategy

The milestone plan should treat AEDs as a **dual-track work package**:

- Track A: investigate AED Foundation of Ontario partnership or acceptable registry access
- Track B: define the OpenStreetMap fallback path with explicit crowdsourced-data labeling

The plan should avoid promising an “official Ontario AED map” unless Track A is resolved.

### 4. Recalls and safety alerts

Use:

- recalls/safety alerts daily data feeds
- recalls RSS feeds
- DPD API for enrichment

The milestone plan should explicitly exclude drug shortages from the first live scope unless a stronger structured access path is confirmed.

### 5. Environmental overlay

Use:

- AQHI via GeoMet as the first environmental overlay

The milestone plan should avoid bundling in multiple environmental overlays at once. AQHI is enough to validate the pattern.

---

## Explicit Exclusions From Batch A

Do not include in the first milestone plan:

- naloxone location ingestion as a committed live feature
- EMS/system metrics as a primary user-facing feature
- inspections and municipal compliance data
- infectious disease and immunization tools
- long-term care or organ donation reporting
- any partner-gated clinical or professional data

These can remain in research or later batching.

---

## Resulting Next Document

The resulting implementation-oriented milestone plan is:

- `docs/planning/implementation/archived/public-health-data-hub-batch-a-plan.md`
- `docs/planning/archive/public-health-data-hub-agent-execution-readiness.md` for delegation-safe execution boundaries

That milestone plan includes:

- intended user-facing outcomes
- domain-specific data flows
- source metadata model and connector expectations
- failure modes and freshness communication
- rollout boundaries
- acceptance criteria per Batch A domain
