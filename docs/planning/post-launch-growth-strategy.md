# Post-Launch Growth Strategy

**Created:** 2026-03-27
**Status:** Active strategy document
**Scope:** Large-scope directions to make Wait Time Canada more useful, more impressive, and more appealing to future employers without diluting the project's core identity.

> Roadmap note: `docs/planning/roadmap.md` remains the canonical source of truth for committed delivery work. This document captures strategic options, ranking, and sequencing for the next major growth phase.

---

## Purpose

Wait Time Canada has already achieved broad proof of concept:

- 4 provinces active (ON, QC, AB, BC)
- 380+ hospitals visible
- 821+ passing tests locally
- production frontend live at `https://wait-time.ca`
- ontology, divergence warnings, analytics, data quality, and occupancy trends already shipped

The next ceiling is **not** simple breadth expansion. Adding a fifth province is lower-leverage than deepening the observatory into a stronger data product, research asset, and standards-aware health technology platform.

This document records the current recommendation:

1. Prioritize **depth over additional province count**
2. Build on the project's strongest differentiator: **methodology transparency**
3. Convert the platform into something other people can **reuse, cite, and integrate**
4. Choose large-scope work that increases both **real utility** and **career signal**

---

## Strategic Principles

1. **Do not abandon the observatory thesis.** The project wins by exposing heterogeneity, not by pretending all wait times are equivalent.
2. **Do not chase province count for optics.** New provinces should be added only when they introduce meaningful methodological novelty or clear public value.
3. **Do not ship prediction-first features on thin foundations.** Forecasting should follow richer metrics, better release discipline, and explicit uncertainty reporting.
4. **Do not drift into medical advice.** Navigation and alerting features must stay operational and logistical, not triage-like.
5. **Do not expand equity analysis casually.** Ontario's rigor should be the minimum bar for any province extension.

---

## Ranked Strategic Bets

| Priority | Strategic Bet | Usefulness | Impressiveness | Employer Signal | Effort | Rationale |
|----------|---------------|------------|----------------|-----------------|--------|-----------|
| P1 | National ED Methodology Registry | High | Very High | High | Medium | Strongest moat; extends the ontology into a reusable public artifact |
| P2 | Multi-Metric ED Operations Observatory | Very High | High | High | Large | Biggest user-value jump; moves beyond a single wait-time lens |
| P3 | Research-Grade Open Data Product | High | Very High | Very High | Medium | Turns the repo into something others can cite, analyze, and build on |
| P4 | FHIR / OMOP / Provenance Bridge | Medium | Very High | Very High | Large | Highest interoperability and health-tech credibility signal |
| P5 | Navigation + Alerting Layer | Very High | Medium | Medium | Medium | Strong consumer utility without needing a new province |
| P6 | Forecasting With Uncertainty | High | High | High | Large | Powerful if done carefully; risky if done too early |
| P7 | Policy / Newsroom / Researcher Workbench | High | High | High | Medium | Improves reuse by journalists, students, and policy researchers |
| P8 | Data Platform Refactor | Medium | Medium | Very High | Large | Lower user-facing value, strong signal for platform/data roles |
| P9 | External Validation Layer | Medium | High | High | Medium | Needed because engineering maturity currently exceeds public proof of use |

---

## Recommended Direction

If only one major direction is pursued, the highest-upside combination is:

1. **Methodology Registry**
2. **Multi-Metric Observatory**
3. **Research-Grade Data Product**
4. **FHIR / OMOP Interoperability**

This sequence preserves the current identity while making the project:

- more useful to patients, researchers, journalists, and policy observers
- more impressive as a distinct health systems observatory
- more legible to future employers in health-tech, data, platform, and civic-tech roles

---

## Public Health Data Hub Expansion

An additional strategic direction emerged from the internal exploratory source scans in
`docs/research/source-discovery-scans/`.

The initial planning funnel for that track is now archived in
`docs/planning/archive/public-health-data-hub-preplan.md`, and the first
delivery wave is no longer hypothetical: Batch A is live at `/resources` with
Ontario facilities, OSM-backed AED fallback data, Health Canada alerts, and
AQHI.

The core idea is to expand beyond emergency wait times into a broader **public health data hub**
for Ontario first, while preserving Wait Time Canada's current strengths in:

- transparent provenance
- methodology-aware interpretation
- freshness and operational visibility
- safety-oriented communication

This does **not** mean turning the project into a generic "everything health" directory.
The stronger version is a curated, modular platform focused on **publicly useful, operational,
location-aware health data**.

### Why this is attractive

- It increases real user utility without abandoning the current observatory identity.
- It creates a stronger civic-tech and public-interest software story.
- It opens more app-usable categories than real-time hospital wait times alone.
- It creates a path toward a reusable multi-domain health data platform.

### Best-fit framing

The cleanest version of this expansion is:

**"Wait Time Canada evolves into an Ontario-first public health access and systems data hub,
starting with emergency care, then adding adjacent operational health datasets that are public,
location-aware, and safety-relevant."**

That framing keeps the product coherent. It also avoids drifting into private clinical data,
medical advice, or an unmaintainable catalogue of weakly related datasets.

---

## Public Health Data Hub Thesis

The internal research outputs suggest a practical split:

1. Some health data is truly app-ready:
   official APIs, open-data portals, CSV/XLSX releases, ArcGIS endpoints, and RSS or feed-based alerts.
2. Some high-interest health data is only publicly viewable:
   dashboards, search pages, hospital microsites, and HTML tables with unclear reuse terms.
3. Some of the most attractive data is gated:
   partner-only portals, request-based APIs, institutional registries, or operational systems designed
   for professionals rather than the public.

The implication is that this expansion should be built around a **data catalog + connector model**
rather than around one-off feature ideas.

### Recommended product boundary

Prioritize categories that are:

- publicly useful
- operational or access-oriented
- location-aware when possible
- meaningfully updateable
- legally and technically reusable

Avoid categories that are:

- highly clinical without a strong public interpretation layer
- partner-gated unless a real collaboration path exists
- available only through brittle scraping with high safety risk
- so broad that they dilute the project's identity

---

## Candidate Data Domains

### Tier 1: Strongest Near-Term Expansion Domains

These look like the best fit for an Ontario-first public health data hub because they are useful,
often public, and usually operational enough to support app features.

1. **AED locations**
   Best acquisition pattern: official registry partnership if possible, otherwise municipal open data,
   OpenStreetMap, and a verified submission flow.
2. **Naloxone access locations**
   Strong public-health value, though current Ontario access may be HTML-first rather than API-first.
3. **Drug recalls, safety alerts, and shortages**
   Strong federal availability, strong consumer value, and better structured access than many local datasets.
4. **Drug and health-product reference data**
   Good API posture and useful for medication verification, alerts, and context features.
5. **Provider and facility directories**
   Strong foundation layer for any map or navigation surface.
6. **Environmental health overlays**
   AQHI, smoke, heat, weather-health alerts, beach water quality, and drinking water advisories.
7. **Inspection and compliance data**
   Restaurant, pool, spa, beach, and similar safety signals where official open datasets exist.
8. **EMS and system-performance data**
   Ambulance response time reporting, paramedic incident datasets, and related public system metrics.

### Tier 2: Promising But More Fragmented Domains

These can add value, but likely require more normalization effort, more limited UX claims, or more
careful sourcing.

1. Infectious disease surveillance
2. Immunization coverage and vaccine safety summaries
3. Substance use and overdose harms
4. Long-term care profiles and inspections
5. Organ donation and transplant public reporting
6. Mental health and crisis service directories
7. Chronic disease and equity indicator systems

### Tier 3: High Value But Usually Gated Or Weakly Reusable

These may still matter strategically, but they should not be treated as easy product inputs.

1. Primary care attachment / accepting-patients data
2. Partner-only mental health interoperability APIs
3. Institution-oriented maternal/newborn dashboards
4. Many hospital-specific wait-time microsites
5. Regulatory registers without official bulk access

---

## Data Acquisition Archetypes

The research outputs suggest that future expansion should explicitly classify each source into one of
these connector types:

1. **Official API**
   Lowest-friction and highest-confidence option.
2. **Open data portal dataset**
   Usually good for scheduled ingest and reproducible refreshes.
3. **Structured downloadable files**
   CSV/XLSX/XML/PDF-based releases that support batch refresh rather than live queries.
4. **Dashboard or map only**
   Publicly viewable, but often poor candidates for direct product dependence.
5. **Periodic reports**
   Useful for background analytics and context, not for live consumer workflows.
6. **Request-based or partner-only access**
   Valuable only when there is a realistic partnership path.
7. **Crowdsourced / user-submitted registries**
   Useful for gaps like AEDs, but require verification and freshness controls.

### Product implication

If the project expands into a multi-domain hub, every source should have explicit metadata for:

- connector type
- legal/reuse status
- update cadence
- freshness expectations
- operational risk
- whether the source is suitable for live UI, periodic analytics, or research-only use

This is likely a reusable platform feature, not just documentation.

---

## Most Promising Ontario-First Hub Themes

If this broader expansion is pursued, the cleanest product themes appear to be:

### 1. Emergency Access Layer

Extend the current emergency-care surface with:

- AED locations
- naloxone access locations
- hospital and urgent-care locations
- telehealth and crisis-routing resources
- system-status context such as wait times and occupancy where available

### 2. Safety And Alerts Layer

Add public safety and consumer protection features such as:

- drug recalls and safety alerts
- drug shortages
- heat, smoke, air quality, and weather-health alerts
- drinking water advisories
- beach water testing and recreational water advisories

### 3. Local Public Health Map Layer

Build a map and directory experience around:

- inspections and compliance
- local environmental exposures and advisories
- municipal and regional public health datasets
- neighborhood or regional health-system context

### 4. Health System Context Layer

Provide broader context without pretending to offer live operational control:

- CIHI indicator feeds and downloadable tables
- ambulance response-time datasets
- long-term care reporting
- regional burden, utilization, or trend summaries

---

## Recommended Expansion Shape

If Wait Time Canada grows into a broader hub, the strongest product shape is likely:

1. **Ontario-first**
   Ontario already has the deepest project context, user relevance, and supporting operational work.
2. **Map-first and provenance-first**
   Users should be able to see what exists nearby and where the information came from.
3. **Modular by data domain**
   Each domain should be able to ship independently without forcing a full-platform rewrite.
4. **Public-utility first**
   Focus on access, safety, and practical navigation rather than quantified self or wellness content.

This points toward a future platform that still feels like a public-interest observatory, not a
consumer health lifestyle app.

---

## What To Build First If This Track Is Chosen

If the public-health-hub direction becomes active, the best first expansion package is probably:

1. **Provider / facility directory hardening**
   Build a stronger facility and service directory foundation using open location datasets.
2. **AED strategy**
   Research partnership path plus fallback ingestion from municipal open data and OpenStreetMap.
3. **Safety alerts ingestion**
   Add a federal recalls / alerts / shortage pipeline.
4. **Environmental health overlays**
   Add AQHI and one or two Ontario municipal environmental safety datasets.
5. **Source catalog infrastructure**
   Create a first-class metadata table or config layer for source type, cadence, terms, and connector mode.

This would let the project test the "public health data hub" concept without overcommitting to a
full rebrand.

---

## Risks Specific To The Data Hub Direction

1. **Identity dilution**
   Too many unrelated datasets could weaken the observatory thesis.
2. **Connector sprawl**
   Public-health data is fragmented across governments, hospitals, municipalities, and nonprofits.
3. **False reusability assumptions**
   Publicly visible is not the same as app-usable.
4. **Staleness risk**
   Some categories are safety-critical enough that stale data becomes actively harmful.
5. **Maintenance burden**
   Dashboard scraping and fragmented municipal portals can become an operational trap.

### Mitigation

Use a strict filter before adopting any new domain:

- clear public value
- clear provenance
- acceptable legal/reuse posture
- stable enough refresh path
- low enough safety risk if delayed or unavailable
- a coherent narrative fit with the existing platform

---

## Strategic Bet Details

### 1. National ED Methodology Registry

Promote methodology metadata from an app implementation detail into a first-class public registry.

**What it includes:**
- machine-readable per-source methodology definitions
- update cadence and reporting lag metadata
- evidence links to official methodology pages
- methodology version history and source diff events
- field-by-field pairwise comparability verdicts
- auto-generated "why comparison is invalid" briefs

**Why this matters:**
- strongest extension of the ontology thesis
- immediately useful for researchers and journalists
- defensible, distinctive, and hard to fake

### 2. Multi-Metric ED Operations Observatory

Grow from a methodology-aware wait-time platform into a broader patient-flow observatory.

**Candidate metric areas:**
- physician initial assessment
- total ED length of stay
- admitted-patient boarding / inpatient-bed-related waits
- visit volume or demand pressure metrics
- occupancy and over-capacity measures
- annual or periodic context metrics when real-time data does not exist

**Why this matters:**
- largest jump in actual utility
- aligns with how serious ED dashboards are structured
- creates richer context for within-province interpretation

### 3. Research-Grade Open Data Product

Make the project useful even for people who never touch the website.

**What it includes:**
- monthly frozen releases
- Parquet and DuckDB-friendly exports
- checksums, manifests, and release notes
- citation metadata and DOI-backed releases
- starter notebooks and reproducible figure examples

**Why this matters:**
- transforms the repo into a reusable data asset
- increases external citations, references, and portfolio strength
- provides a strong bridge into academic, analytics, and data engineering audiences

### 4. FHIR / OMOP / Provenance Bridge

Add interoperability and audit semantics that are legible to health-tech employers.

**What it includes:**
- FHIR-based measurement exposure for facility-level observations
- provenance metadata tied to source and parser history
- audit-style event representations for scraper and data events
- optional OMOP-compatible export or mapping layer
- subscription or webhook patterns for downstream consumers

**Why this matters:**
- very strong employer signal
- moves the project closer to modern health data infrastructure
- pairs naturally with the project's existing provenance posture

### 5. Navigation + Alerting Layer

Add higher-utility product features without drifting into medical advice.

**What it includes:**
- saved hospitals and regions
- threshold-based alerts
- drive/transit travel-time context
- pediatric/adult and service-context labels where defensible
- after-hours alternatives and telehealth escalation links

**Why this matters:**
- clear user value
- strong product-thinking signal
- can be implemented without expanding province count

### 6. Forecasting With Uncertainty

Add short-horizon forecasting only after the metric and release foundation is stronger.

**What it includes:**
- 6h/24h/72h nowcasts
- uncertainty intervals
- calibration and backtesting dashboards
- forecast quality disclosures

**Why this matters:**
- highly visible and compelling
- useful to users and operations-minded audiences
- strongest when coupled to richer metrics and honest evaluation

### 7. Policy / Newsroom / Researcher Workbench

Build a surface for external reuse, not just internal display.

**What it includes:**
- saved comparisons and citation-ready charts
- embeddable cards or widgets
- province and region briefing exports
- "what changed this month?" reports

**Why this matters:**
- increases the chance of external links and references
- broadens the audience beyond patients and admissions reviewers
- deepens the project's civic-tech value

### 8. Data Platform Refactor

Evolve the backend from a mature app data pipeline into a more explicit platform.

**What it includes:**
- stronger data contracts
- asset or lineage-oriented orchestration
- clearer freshness SLAs and backfill ergonomics
- metric-definition centralization
- improved observability for derived datasets

**Why this matters:**
- very strong employer signal for data and platform roles
- makes larger-scale downstream products easier to support

### 9. External Validation Layer

Engineering maturity is already strong. Evidence of real-world review and reuse now matters more.

**What it includes:**
- stakeholder review logs
- methodology reviewer acknowledgements
- monthly operational transparency reports
- case studies and post-mortems
- public adoption or reuse examples

**Why this matters:**
- closes the credibility gap between system maturity and visible uptake
- improves both admissions narrative and employer perception

---

## Synthesis From Internal Source Scans

The internal scans in `docs/research/source-discovery-scans/` are directionally useful but should be treated
as **research leads, not final source-of-truth validation**.

The strongest takeaways from those scans are:

- federal APIs and open-data programs are generally more reusable than hospital or provincial dashboards
- Ontario and municipal data is often fragmented but still buildable through connector-by-connector ingestion
- AEDs, provider directories, environmental health, recalls, and EMS-style public reporting are stronger
  candidates than many highly attractive but partner-gated clinical datasets
- a data-catalog architecture is likely more important than any single new feature

Any source chosen from those research notes should still go through manual validation for:

- primary-source confirmation
- licensing / terms review
- access path confirmation
- update cadence verification
- safety and freshness implications

---

## Recommended Sequence

### Quick Wins (1-3 Weeks)

1. Create a public methodology registry page and schema
2. Upgrade `/methods` into a pairwise comparability engine
3. Add a "By the Numbers" section grounded in real measurement and ontology counts
4. Publish monthly data snapshots with a manifest and checksums
5. Add a researcher starter kit with one notebook and one DuckDB example
6. Review the exploratory source-scan outputs and convert the best data-hub candidates into a validated source shortlist

### 6-Week Bets

1. Expand toward a multi-metric observatory
2. Build a policy/newsroom/researcher workbench
3. Add saved hospitals, regions, and threshold alerts
4. Formalize the public data product with release notes and citation metadata
5. Introduce stronger data-platform conventions for contracts and lineage
6. Prototype the first Ontario-first public-health-hub package:
   facility directories + AED strategy + safety alerts + environmental overlays

### Big 6-Month Bets

1. Ship a FHIR + provenance API surface
2. Add an OMOP-compatible export path
3. Launch forecasting with uncertainty and backtesting
4. Publish recurring transparency or methodology drift reports
5. Extend equity analysis province-by-province only when each new rollout matches Ontario's rigor
6. Decide whether the public-health-hub track should remain a module inside Wait Time Canada or become a
   broader product surface with its own IA and branding

---

## Candidate Milestone Framing

If this strategy is turned into roadmap work, a plausible milestone framing is:

- **M34:** Methodology Registry + Pairwise Comparability Engine
- **M35:** Research-Grade Snapshot Releases + Starter Kit
- **M36:** Multi-Metric ED Operations Observatory
- **M37:** Policy / Researcher Workbench
- **M38:** FHIR / Provenance API
- **M39:** Navigation + Alerting Layer
- **M40:** Forecasting With Uncertainty
- **M41:** Data Platform Contracts / Lineage / Backfills
- **M42:** Ontario Public Health Data Hub Foundations
- **M43:** Safety Alerts + Environmental Health Layer

These are candidate milestone labels, not committed roadmap items.

---

## Explicit Non-Goals

- Adding provinces for optics alone
- Rebranding the project into a generic "fastest ER" finder
- Shipping predictions before uncertainty and evaluation are ready
- Building symptom-triage or medical-advice UX
- Expanding equity claims without province-specific validation

---

## External Research Notes

The strategy above was informed by the following external references:

- CIHI wait time metadata and ED indicators
- NHS England A&E quality indicators
- UK ONS guidance on cross-jurisdiction A&E comparability
- HL7 FHIR resources and SMART on FHIR ecosystem docs
- OHDSI OMOP common data model references
- FAIR data principles and Frictionless data packaging guidance
- CDC dashboard examples for public health data reuse

These references support the core inference that the strongest next move is **deeper metric breadth, stronger methodology visibility, and better interoperability**, not just more geographic coverage.
