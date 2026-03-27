# Public Health Data Hub Batch A Legal And Reuse Review

**Created:** 2026-03-27
**Status:** Pre-implementation gate
**Related:** `docs/research/public-health-data-hub-source-shortlist.md`

> This review is a hard gate for Batch A. No source moves into implementation unless it is explicitly marked `approved` or `approved_with_conditions`.

---

## Gate Outcomes

| Source | Proposed use | Basis for use | Required conditions | Gate |
|---|---|---|---|---|
| MOHSERLO | Ingest Ontario facility/provider location baseline into local DB | Official Ontario Data Catalogue resource with Open Government Licence - Ontario | Preserve provenance URL; comply with OGL-O attribution in docs/UI where source lists are surfaced | `approved_with_conditions` |
| ODHF | Secondary cross-check and future-expansion facility baseline | Statistics Canada open data resource under Open Government Licence - Canada | Preserve provenance URL; comply with OGL-Canada attribution when surfaced | `approved_with_conditions` |
| OpenStreetMap AED fallback | Scheduled ingest of AED points when no official Ontario registry feed is available | OSM data is licensed under ODbL and explicitly allows copying/adapting with attribution and share-alike conditions | Show OSM attribution; disclose ODbL availability; avoid implying official completeness; label crowdsourced/incomplete | `approved_with_conditions` |
| Recalls and safety alerts data feeds | Ingest recall and alert records into local DB and display in UI | Health Canada provides official CSV/JSON data access and RSS feeds for the recalls system | Use only official feeds; preserve provenance and refresh timestamp; do not alter alert meaning | `approved_with_conditions` |
| Recalls RSS feeds | Feed-based freshness path for alerts | Official Health Canada RSS feed surface | Use official feed URLs only; preserve source attribution and last-refreshed time | `approved_with_conditions` |
| Drug Product Database API | On-demand enrichment of alert/product detail | API guide explicitly states developers can access JSON/XML for reuse in their own applications | Use official API only; cache responses conservatively; preserve source attribution in documentation | `approved_with_conditions` |
| AQHI GeoMet | Live environmental overlay via API proxy | Official ECCC GeoMet API surface for AQHI forecasts | Preserve source labeling and publication time; do not present as more current than upstream payload | `approved_with_conditions` |

---

## Blocked Or Deferred Inputs

| Source | Why it is not allowed into Batch A dependency scope | Gate |
|---|---|---|
| AED Foundation of Ontario registry direct ingestion | Official registrar status is strong, but direct reuse, export, or API terms are not yet validated for product dependence | `blocked_pending_permission` |
| Drug Shortages Canada website | Public viewing is clear, but this validation pass did not confirm a reusable structured feed suitable for Batch A | `blocked_for_batch_a` |
| Ontario naloxone map | Public map/table route is clear, but structured reuse path was not validated and freshness risk is high for live consumer display | `blocked_for_batch_a` |

---

## Conditions That Must Be Carried Into Implementation

### Attribution

- OGL Ontario and OGL Canada sources must keep clear provenance and attribution in source-facing UI or documentation.
- OSM usage must comply with OpenStreetMap attribution and ODbL disclosure requirements.
- Federal feed/API usage must keep source labeling and provenance visible in the app and docs.

### Provenance

- Every Batch A record shown publicly must resolve back to a stored `provenance_url`.
- UI surfaces must show the effective source and last refresh timestamp for alerts and AQHI.

### Claims Discipline

- OSM AED fallback data must never be described as official or complete.
- Provider/facility baseline data must be described as reference directory data, not live operational status.
- Alert summaries must preserve source meaning and avoid interpretive rewriting that changes regulatory intent.

---

## Implementation Gate Decision

Batch A may proceed to implementation **only** on the following source basis:

1. MOHSERLO
2. ODHF
3. OSM AED fallback
4. Recalls dataset + RSS feeds
5. DPD API
6. AQHI GeoMet

Anything outside that set remains out of scope until a separate source review changes its gate status.

---

## Review Notes

- This review is sufficient to support implementation planning, not to replace ordinary release diligence.
- If any source terms materially change before launch, the gate must be re-opened for that source.
- If the implementation cannot satisfy the required conditions above, the source must be downgraded or removed rather than shipped with weak compliance posture.
