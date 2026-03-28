# Ontario Public Health Data Hub Pre-Plan

**Created:** 2026-03-27
**Status:** Archived after Batch A delivery
**Scope:** Decision framework and planning funnel for evaluating whether and how Wait Time Canada should expand into an Ontario-first public health data hub.

> Roadmap note: `docs/planning/roadmap.md` remains the canonical source of truth for committed work. This document is a pre-plan for deciding what should become a real implementation plan later.

---

## Purpose

This document does **not** commit the repository to building a public health data hub now.

Its purpose is to reduce ambiguity before any milestone plan is written by answering:

1. What belongs inside the hub concept and what does not
2. Which data domains are actually reusable, safe, and strategically worth pursuing
3. How viable domains should be grouped into batches and dependencies
4. Whether this should remain inside Wait Time Canada or evolve into a broader product surface

This is a planning framework for a **12-month strategic initiative**, not a roadmap and not an implementation spec.

The first planning package generated from this pre-plan now exists in:

- `docs/planning/archive/public-health-data-hub-decision-brief.md`
- `docs/research/public-health-data-hub-source-shortlist.md`
- `docs/research/public-health-data-hub-scoring-matrix.md`
- `docs/planning/archive/public-health-data-hub-identity-memo.md`
- `docs/planning/archive/public-health-data-hub-batch-a-handoff.md`

The implementation-ready preflight bundle now also includes:

- `docs/research/public-health-data-hub-batch-a-legal-review.md`
- `docs/planning/public-health-data-hub-metadata-contract.md`
- `docs/planning/public-health-data-hub-freshness-safety-rules.md`
- `docs/adr/0023-public-health-hub-module-boundary.md`
- `docs/planning/implementation/archived/public-health-data-hub-batch-a-plan.md`

---

## Working Thesis

The strongest version of this direction is:

**Wait Time Canada evolves into an Ontario-first public health access and systems data hub, starting with emergency-care-adjacent public datasets and expanding only where provenance, access, freshness, and public utility remain strong.**

That implies the following:

- Ontario-first remains the default organizing principle
- map-first and provenance-first design remain central
- public, location-aware, operational health data is the target
- private clinical data and medical-advice workflows stay out of scope

---

## Non-Goals

This pre-plan explicitly avoids:

- turning the project into a generic "everything health" directory
- committing to a full product rebrand before identity review
- assuming publicly viewable data is automatically reusable
- building on brittle dashboard scraping as a foundational dependency
- adding partner-gated datasets without a realistic access path
- weakening the current observatory thesis with unrelated wellness or lifestyle features

---

## Planning Outputs

The next planning pass should produce these outputs in order.

### 1. Decision Brief

Define the hub thesis, intended audiences, success criteria, non-goals, and planning assumptions.

This brief must lock:

- target user groups
- target problem types
- what "public health data hub" means in this repo
- what should stay outside the product boundary

### 2. Validated Source Catalog

Start from:

- `docs/research/ai-deep-research/deep-research-report.md`
- `docs/research/ai-deep-research/Ontario Health Data Scan.md`

Treat both as research leads only.

Every shortlisted source must be re-validated manually from primary sources and captured with a consistent schema:

- `domain`
- `source_name`
- `scope`
- `jurisdiction_level`
- `access_route`
- `connector_type`
- `cost_access_class`
- `license_reuse_status`
- `update_cadence`
- `freshness_sensitivity`
- `operational_risk`
- `app_usability`
- `recommended_usage_mode`
- `primary_source_proof`
- `notes`

`recommended_usage_mode` must be one of:

- `live_ui`
- `scheduled_ingest`
- `analytics_only`
- `research_only`
- `do_not_use`

### 3. Opportunity Scoring Matrix

Score each domain and major source cluster using a fixed rubric.

Minimum scoring dimensions:

- user value
- narrative fit with Wait Time Canada
- legal clarity
- machine readability
- freshness
- maintenance burden
- safety risk
- geographic coverage
- differentiation
- employer signal

The same rubric must be applied to all candidate domains so batching decisions are comparable.

### 4. Batching Framework

Group viable work into:

- `Batch A: foundation now`
- `Batch B: conditional next`
- `Batch C: defer or avoid`

Batching should happen at the domain level first and at the source level second.

### 5. Identity Gate Memo

Make identity a formal planning gate.

Compare:

- module inside Wait Time Canada
- broader information architecture inside Wait Time Canada
- separate broader product surface later

This decision must evaluate:

- narrative coherence
- maintainability
- user comprehension
- risk of brand dilution
- employer and portfolio signal

### 6. Roadmap Handoff Brief

End the planning pass with a short recommendation that says:

- which batch should receive the first real milestone plan
- which 1-2 domains are highest leverage
- which ideas should remain parked

---

## Planning Sequence

### Phase 1: Boundary and Evaluation Setup

Lock the product boundary before discussing specific datasets.

Default in-scope themes:

- emergency access
- safety alerts and consumer protection
- environmental health overlays
- provider and facility context
- selected health-system context

Default out-of-scope themes:

- medical advice
- private or authenticated clinical data
- quantified-self or wellness content
- partner-only workflows with no realistic access path
- scraping-first foundations for safety-critical features

### Phase 2: Source Validation

Re-validate the strongest candidates first rather than the entire long tail.

Validation priority order:

1. provider and facility directories
2. AED sources and registry options
3. drug recalls, safety alerts, and shortages
4. environmental health APIs and alert feeds
5. municipal inspection and public safety open data
6. EMS and system-performance datasets

Each source must be classified into one connector type:

- official API
- open data portal dataset
- structured downloadable file
- dashboard or map only
- periodic report
- request-based access
- partner-only access
- crowdsourced or user-submitted registry

### Phase 3: Domain Prioritization

Rank domains into:

- `Tier 1: plan now`
- `Tier 2: keep warm`
- `Tier 3: avoid or defer`

Default Tier 1 candidates to evaluate first:

- provider and facility directories
- AED locations
- drug recalls, safety alerts, and shortages
- environmental health overlays
- selected EMS and system-performance data

Naloxone access should be treated as a special-case domain: likely high value, but not promoted into Batch A unless access stability and reuse posture are validated.

### Phase 4: Batch Design

Design batches using dependency logic, not just topic grouping.

Default batch shape:

- `Batch A: platform foundation`
  source catalog model, connector taxonomy, provenance and freshness metadata, facility directory baseline
- `Batch B: public utility launch set`
  AED strategy, safety alerts, environmental overlays
- `Batch C: local public health and system context`
  inspections, EMS/system metrics, selected surveillance and context layers
- `Batch D: conditional expansion`
  only for domains that survive licensing, freshness, and narrative-fit review

Each batch should explain:

- why it exists
- what user problem it solves
- what data classes it needs
- why it is safe enough to ship
- what would disqualify it

### Phase 5: Identity Gate

Run the identity decision only after Batch A and Batch B are defined.

The default assumption until that gate is completed is:

**keep this as a strategic module inside Wait Time Canada, not a separate branded product.**

### Phase 6: Planning Handoff

The final handoff from the next planning pass should make the next step obvious:

- either write a milestone plan for the winning batch
- or stop and defer the hub track because the validation case is too weak

---

## Candidate Domains To Evaluate

These are the current domains worth evaluating through the source catalog and scoring matrix.

### Tier 1 Candidates

- provider and facility directories
- AED locations
- drug recalls, safety alerts, and shortages
- drug and health-product reference data
- environmental health overlays
- municipal inspection and compliance data
- EMS and system-performance data

### Tier 2 Candidates

- naloxone access locations
- infectious disease surveillance
- immunization coverage and vaccine safety summaries
- substance use and overdose harms
- long-term care profiles and inspections
- organ donation and transplant public reporting
- mental health and crisis service directories
- chronic disease and equity indicator systems

### Tier 3 Candidates

- primary care attachment or accepting-patients data
- partner-only mental health interoperability feeds
- institution-oriented maternal/newborn dashboards
- hospital microsites without clear reuse rights
- professional registers without bulk or durable access

---

## Acceptance Criteria

This pre-plan is considered successfully executed when the follow-on planning pass produces:

- a validated shortlist instead of a brainstorm
- an explicit product boundary
- a ranked domain funnel with reasons
- a batch structure with dependency logic
- an identity decision gate
- a short handoff that identifies what deserves a true implementation plan

If those outputs are not present, the planning effort is not complete enough to justify roadmap commitment.

---

## Defaults and Assumptions

- This pre-plan is focused on the **public health data hub track only**
- It is intended primarily for **strategic decision-making**
- It should stop at **framework + prioritized funnel**, not full milestone design
- It assumes a **12-month program horizon**
- It assumes the exploratory source-scan outputs are **inputs, not source-of-truth evidence**
- It assumes Ontario-first remains the default scope unless later validation strongly supports expansion
