# Public Health Data Hub Batch B Source Review

**Created:** 2026-03-27
**Status:** Active research artifact
**Scope:** Revalidation of deferred Batch B source domains before any expansion beyond `/resources`
**Related:** `docs/research/public-health-data-hub-source-shortlist.md`, `docs/research/public-health-data-hub-scoring-matrix.md`, `docs/planning/roadmap.md`

> This document revalidates the deferred Batch B domains named in the roadmap: naloxone access, EMS/system-context data, and inspection/compliance datasets. It is a source-validation artifact, not an implementation plan.

---

## Summary

This revalidation changes the public-health-hub picture in three useful ways:

1. **Naloxone access is technically stronger than the original shortlist captured.**
   The Ontario public page is backed by a public ArcGIS Web Map and a queryable public `FeatureServer` layer. The technical access path is real. The remaining blocker is **reuse clarity**, not machine readability.

2. **EMS/system-context remains valid but is still weak as a consumer-facing live feature.**
   The Ontario land-ambulance response-time dataset remains official, open-licensed, and structured. Its cadence and reporting grain still make it a **context/analytics** layer rather than a first-order public utility surface.

3. **Inspection/compliance data is stronger at the municipal level than the earlier planning docs assumed.**
   Toronto exposes machine-readable DineSafe and BodySafe datasets through the open-data portal and CKAN API. The real blocker is **fragmentation**, not raw availability.

### Recommendation

- **Do not reopen Batch B implementation yet.**
- **Promote naloxone from “weak map-only lead” to “conditional Batch B candidate pending legal/reuse review.”**
- **Keep EMS/system-context as a later analytics/context layer.**
- **Treat inspection/compliance as a Toronto-first pilot option, not an Ontario-wide Batch B default.**

> Decision update (2026-03-28): the current product posture is now recorded in `docs/adr/0024-ontario-naloxone-link-out-posture.md`. Wait Time Canada should link out to the official Ontario naloxone source for now rather than ingesting or republishing the dataset.

---

## Revalidated Sources

| Domain | Source | Geographic scope | Current access route | Technical route quality | Reuse posture | Recommended usage mode | Recommendation |
|---|---|---|---|---|---|---|---|
| Naloxone access | Ontario naloxone kit locations page | Ontario-wide | Public Ontario page with embedded ArcGIS map | Strong | Public page is clear; explicit open-data licence for the underlying layer was not confirmed in this pass | `research_only` until legal review, then likely `scheduled_ingest` | Keep warm as the strongest Batch B utility candidate |
| Naloxone access | Ontario naloxone ArcGIS Web Map + FeatureServer | Ontario-wide | Public ArcGIS Web Map item and queryable `FeatureServer` layer | Strong | Technically reusable, but licensing/reuse rights need explicit confirmation | `research_only` until legal review | Real connector path exists; not a dashboard-only dead end |
| EMS / system context | Ontario Land Ambulance Response Time Standard - Response Times | Ontario-wide | Ontario Data Catalogue dataset page with downloadable files | Medium to strong | Open Government Licence - Ontario | `analytics_only` | Viable for context cards or dashboards, not live utility routing |
| Inspection / compliance | Toronto DineSafe | Municipal (Toronto) | Open Toronto dataset page backed by CKAN package/resources | Strong | Inference: intended for open-data reuse via portal licence, but package metadata omits a dataset-specific licence title | `scheduled_ingest` for a Toronto-only pilot after legal review | Strong pilot candidate, weak Ontario-wide fit |
| Inspection / compliance | Toronto BodySafe | Municipal (Toronto) | Open Toronto dataset page backed by CKAN package/resources | Strong | Inference: intended for open-data reuse via portal licence, but package metadata omits a dataset-specific licence title | `scheduled_ingest` for a Toronto-only pilot after legal review | Useful proof of municipal inspection integration, but fragmented outside Toronto |

---

## Source Findings

### 1. Naloxone access

**What changed**

The original shortlist treated Ontario naloxone access as a public map/table with no durable structured route confirmed. That is no longer accurate.

**What was validated**

- The Ontario page explicitly says it provides a map of locations for naloxone kits and says the page is not for emergencies.
- The page embeds an Ontario-hosted ArcGIS iframe:
  - `/libraries/arcgis-map/static/arcGIS-map-en.html?tableId=2d66941cc2354da68059afa6621a5713...`
- That map is backed by a public ArcGIS Web Map item:
  - `https://www.arcgis.com/sharing/rest/content/items/2d66941cc2354da68059afa6621a5713?f=json`
- The Web Map item data exposes a public operational layer:
  - `https://services1.arcgis.com/KxfxGiBWqJQX6S7x/arcgis/rest/services/moh_naloxone_locations_2021/FeatureServer/0`
- The layer answers public queries successfully, including:
  - public metadata requests
  - count queries
  - sample feature queries

**What this means**

- The technical connector path is **not speculative**.
- The remaining issue is **legal/reuse posture**, because the Ontario public page does not present this as an open-data catalogue asset with an explicit reuse licence.

**Recommendation**

- Do not implement ingestion yet.
- Create a small legal/reuse review item if naloxone is chosen as the next serious Batch B candidate.
- If reuse is cleared, naloxone becomes the strongest non-implemented public-health-hub utility domain after Batch A.

### 2. EMS / system context

**What was revalidated**

- Ontario’s Land Ambulance Response Time Standard dataset remains on the Ontario Data Catalogue.
- The dataset page describes municipal/CACC response-time reporting.
- The page includes Open Government Licence - Ontario metadata.
- The page exposes structured downloads, including CSV.

**What this means**

- Access and reuse are solid.
- The limiting factor is still **product fit**, not technical feasibility.
- This is better used for:
  - municipality context cards
  - policy/research views
  - “system context” framing around emergency access

It is still weak for:

- freshness-sensitive nearby tools
- public “what should I do right now?” experiences

**Recommendation**

- Keep this as `analytics_only`.
- Do not prioritize it over naloxone if the goal is near-term public utility.

### 3. Inspection / compliance

**What changed**

The earlier planning funnel treated inspection data mostly as a fragmented later-scan category. Toronto’s public sources are stronger than that.

**What was validated**

- Toronto Open Data hosts dataset pages for DineSafe and BodySafe.
- The public dataset pages initialize against the City’s CKAN API configuration.
- The CKAN package endpoint returns real package metadata and downloadable resources.
- `dinesafe` currently exposes daily-refresh CSV, JSON, XML, and historical ZIP resources.
- `bodysafe` currently exposes daily-refresh GeoJSON, CSV, and SHP resources.
- Toronto’s general Open Data Licence permits reuse with attribution.

**Inference**

Because the package metadata for DineSafe and BodySafe omits a dataset-specific licence title, but the datasets are served from the official Toronto open-data portal under the portal’s licence framework, these sources appear usable with attribution. That is a reasonable inference, not an explicit per-package licence statement.

**What this means**

- The technical path is strong enough for a pilot.
- The strategic problem is **scope fragmentation**:
  - Toronto is strong
  - Ontario-wide inspection coverage is not yet validated
  - a province-wide inspection module would quickly become uneven

**Recommendation**

- Do not make inspections the default Batch B expansion.
- If pursued, treat it as a **Toronto-only pilot** with explicit scope labeling.

---

## Updated Batch B Ranking

1. **Naloxone access**
   Strongest user-value candidate after Batch A, but blocked on reuse review.
2. **Municipal inspection/compliance pilot**
   Strong Toronto data path, but weak Ontario-wide coherence.
3. **EMS/system context**
   Strong access path, weak consumer urgency; best kept for later context work.

---

## Product-Fit Recommendation

### Best candidate to reopen first

**Naloxone access**, if and only if reuse/legal review comes back acceptable.

Why:

- Ontario-wide
- publicly useful
- location-aware
- operationally adjacent to the current `/resources` thesis
- technically much more real than the earlier shortlist indicated

### Best candidate to keep parked

**EMS/system context** should remain parked as a background/context layer until there is a stronger reason to build policy-oriented or municipality-level public dashboards.

### Best candidate for a narrow pilot

**Toronto inspection/compliance** is the best “small but interesting” pilot if a Toronto-only public-health sidecar ever becomes strategically useful. It is not yet a clean Ontario-first hub expansion.

---

## Suggested Roadmap Follow-Ons

If the roadmap is updated after this review, the strongest follow-on items are:

1. **Naloxone legal/reuse review**
   Validate whether the Ontario public ArcGIS-backed source can be ingested or proxied without overclaiming rights.
2. **Municipal inspection pilot decision**
   Decide whether a Toronto-only inspection pilot fits the product identity well enough to justify fragmented scope.
3. **No Batch B implementation until one of those passes**
   This review improves the evidence base, but does not by itself justify immediate expansion work.

---

## Primary Sources

- Ontario naloxone page: <https://www.ontario.ca/page/where-get-free-naloxone-kit>
- Ontario naloxone program page: <https://www.ontario.ca/page/ontario-take-home-naloxone-programs>
- Ontario ArcGIS Web Map item: <https://www.arcgis.com/sharing/rest/content/items/2d66941cc2354da68059afa6621a5713?f=json>
- Ontario ArcGIS Web Map item data: <https://www.arcgis.com/sharing/rest/content/items/2d66941cc2354da68059afa6621a5713/data?f=json>
- Ontario naloxone FeatureServer metadata: <https://services1.arcgis.com/KxfxGiBWqJQX6S7x/arcgis/rest/services/moh_naloxone_locations_2021/FeatureServer/0?f=json>
- Ontario naloxone FeatureServer query endpoint: <https://services1.arcgis.com/KxfxGiBWqJQX6S7x/arcgis/rest/services/moh_naloxone_locations_2021/FeatureServer/0/query?where=1%3D1&returnCountOnly=true&f=json>
- Ontario ambulance response-time dataset: <https://data.ontario.ca/dataset/land-ambulance-response-time-standard-response-times>
- Toronto DineSafe dataset page: <https://open.toronto.ca/dataset/dinesafe/>
- Toronto BodySafe dataset page: <https://open.toronto.ca/dataset/bodysafe/>
- Toronto CKAN package API (`dinesafe`): <https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=dinesafe>
- Toronto CKAN package API (`bodysafe`): <https://ckan0.cf.opendata.inter.prod-toronto.ca/api/3/action/package_show?id=bodysafe>
- Toronto Open Data Awards page: <https://open.toronto.ca/announcing-the-2024-toronto-open-data-award-winners/>
- Toronto Open Data Licence: <https://open.toronto.ca/open-data-licence/>

**Last verified:** 2026-03-27
