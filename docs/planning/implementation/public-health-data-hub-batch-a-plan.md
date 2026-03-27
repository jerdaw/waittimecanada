# Public Health Data Hub Batch A Implementation Plan

**Created:** 2026-03-27
**Status:** Ready for implementation
**Scope:** Implement the first public-health-data-hub module inside Wait Time Canada using provider/facility baseline data, AED strategy, recalls/safety alerts, and AQHI.

> Strategic questions are already settled by the public-health-data-hub planning package. This document should be treated as the implementation source of truth for Batch A if the team decides to build it.

---

## Summary

Batch A adds a new module inside Wait Time Canada focused on public, location-aware access and safety data. The module should ship as a new locale route with supporting API routes and a small amount of new backend ingestion/storage infrastructure.

### Locked Batch A scope

1. provider/facility baseline from MOHSERLO with ODHF as cross-check/fallback
2. AED experience using an OSM-backed fallback path with strong crowdsourced labeling
3. recalls and safety alerts using official Health Canada feeds plus DPD enrichment
4. AQHI as the first environmental overlay

### Explicit non-goals for Batch A

- naloxone map ingestion
- EMS/system context as a primary user-facing feature
- inspections/compliance datasets
- infectious disease and immunization tools
- long-term care, organ donation, or partner-gated clinical datasets
- product rebrand or homepage rewrite

---

## Implementation Changes

### 1. Product surface

Add a new locale route:

- `/[locale]/resources`

This route should behave as a module inside Wait Time Canada rather than a standalone application.

The page should contain four user-facing sections:

1. **Nearby resources**
   facility and AED map/list with optional geolocation support
2. **Safety alerts**
   recent recalls and safety alerts feed
3. **AQHI**
   current air quality context for the user or selected region
4. **Source transparency**
   provenance, refresh timestamps, and domain-specific caveats

Do not redesign the homepage around this module in Batch A.

### 2. Data model and storage

Add three new persistence concepts:

1. **Public data sources catalog**
   stores the metadata contract frozen in `public-health-data-hub-metadata-contract.md`
2. **Resource locations**
   stores normalized location-based resources for:
   `facility` and `aed`
3. **Public health alerts**
   stores normalized recall/safety alert items

Do **not** add a persistent AQHI table in Batch A. AQHI should be proxied live through the Next.js API layer with server-side caching.

### 3. Backend ingestion posture

Use a mixed approach:

- **Scheduled ingest into DB**
  - MOHSERLO
  - ODHF cross-check data
  - OSM AED fallback
  - recalls/safety alerts feed records
- **Live proxy with server cache**
  - AQHI
  - DPD enrichment lookups

Batch A should not require a new always-on runtime. It should fit the existing project posture:

- scheduled backend/data jobs via the established backend operational path
- frontend/API delivery through existing Next.js API routes and server cache utilities

### 4. New API surfaces

Add these public API routes under `frontend/app/api`:

- `GET /api/resources`
  query: `kind=facility|aed`, optional `q`, `province`, `latitude`, `longitude`, `radius`, `limit`
- `GET /api/resources/alerts`
  query: optional `limit`
- `GET /api/resources/aqhi`
  query: `latitude`, `longitude`

Batch A does **not** need a dedicated public `sources` API route. Provenance data can be embedded in route responses.

### 5. Source metadata contract usage

Batch A implementation must use the frozen metadata fields from:

- `docs/planning/public-health-data-hub-metadata-contract.md`

No alternate naming is allowed in Batch A. If implementation pressure requires contract changes, the contract must be updated first.

### 6. Provider/facility baseline behavior

- Use MOHSERLO as the primary Ontario facility/provider directory baseline.
- Use ODHF for cross-checking, gap analysis, and future expansion, not as the primary Ontario source.
- Represent facilities as reference directory data only.
- Do not claim real-time operational availability, open/closed status, or wait times from this layer.

### 7. AED behavior

- Implement AED support assuming OSM-backed fallback is allowed.
- Label every OSM-backed AED result as crowdsourced and incomplete.
- Preserve provenance and last-refresh metadata in API responses and UI.
- Do not claim official Ontario completeness.
- If a direct Ontario registry access path becomes available later, treat it as a future source upgrade rather than a Batch A requirement.

### 8. Alerts behavior

- Ingest official recalls/safety alert feeds into normalized alert records.
- Use RSS plus feed data for freshness and recent-item coverage.
- Use DPD API only as optional detail enrichment.
- If DPD enrichment fails, the alert still renders without enrichment.
- Drug shortages remain out of live Batch A scope.

### 9. AQHI behavior

- Fetch AQHI through a server-side API proxy with caching.
- AQHI is the only environmental overlay in Batch A.
- If AQHI freshness exceeds the suppress threshold defined in the freshness rules, do not render a current AQHI card.

### 10. Freshness and safety rules

Batch A must implement the exact show/warn/suppress behavior in:

- `docs/planning/public-health-data-hub-freshness-safety-rules.md`

This applies to:

- provider/facility reference state
- AED OSM fallback
- recalls/safety alerts
- DPD enrichment fallback
- AQHI

### 11. Navigation and IA

- Add the module as a new top-level route reachable from the existing app shell.
- The route label should be **Resources** in English.
- Do not change existing analytics/methods/data-quality route structure.
- Do not create a separate product shell or new locale root.

---

## Test Plan

### Backend and data tests

- migration tests for new tables/constraints
- ingestion tests for:
  - MOHSERLO normalization
  - OSM AED normalization
  - recalls feed normalization
- source metadata contract tests to ensure required fields are present

### API tests

- validation tests for `/api/resources`, `/api/resources/alerts`, and `/api/resources/aqhi`
- tests that resource responses include provenance and freshness metadata
- tests that AQHI and DPD proxy failures degrade gracefully

### UI tests

- `/resources` route renders with all four sections
- provider/facility cards show reference-directory caveat
- AED cards show crowdsourced/incomplete warning when OSM-backed
- alerts list shows last refreshed time
- AQHI card shows or suppresses correctly based on freshness state

### Acceptance scenarios

1. User opens `/resources` with no geolocation permission:
   facilities render as browseable directory data, alerts render, AQHI can use selected/default location flow
2. User grants geolocation:
   facilities and AEDs sort by proximity where possible
3. AQHI upstream is stale:
   AQHI section warns or suppresses per rule without breaking the rest of the page
4. DPD enrichment fails:
   alert feed still renders normally
5. AED source sync is stale:
   AED results warn or suppress per rule, but facilities still render

---

## Assumptions

- ADR-0023 is accepted before implementation begins
- the legal/reuse review remains valid for the Batch A source set
- OSM attribution and incompleteness labeling are treated as mandatory
- the module remains inside Wait Time Canada for Batch A
- AQHI is live-proxied rather than stored persistently in v1
- Batch A uses only the approved source set from the legal review
