# Public Health Data Hub Source Shortlist

**Created:** 2026-03-27
**Status:** Validated shortlist for planning
**Related:** `docs/planning/archive/public-health-data-hub-preplan.md`

> This is a shortlist-first validation pass. It is intentionally not exhaustive. The goal is to validate only the strongest candidates needed to decide whether a real Batch A milestone plan should be written.
>
> Follow-on validation for deferred domains now lives in `docs/research/public-health-data-hub-batch-b-source-review.md`. That later review supersedes the original naloxone and inspection assumptions captured here.

---

## Summary

This shortlist validates the source classes most relevant to a first Ontario-first hub batch:

- provider and facility directories
- AED sourcing
- recalls and safety alerts
- one environmental overlay
- a small number of nearby Batch B candidates for comparison

### Usage Mode Definitions

- `live_ui`: suitable for direct consumer-facing use with normal freshness controls
- `scheduled_ingest`: suitable for periodic backend ingestion and display after refresh
- `analytics_only`: suitable for context or background reporting, not live consumer workflows
- `research_only`: useful for planning or partner evaluation, not ready for product dependence
- `do_not_use`: should not be used as a product dependency

---

## Shortlist

| Domain | Source | Scope | Access route | Connector type | Reuse status | Update cadence | Freshness sensitivity | Operational risk | App usability | Recommended usage mode | Gate status | Why shortlisted | Primary source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Provider / facility baseline | Ministry of Health Service Provider Locations (MOHSERLO) | Ontario-wide | Ontario Data Catalogue `WEB` geospatial resource | Open data portal dataset | Open Government Licence - Ontario | Yearly | Medium | Low | High | `scheduled_ingest` | Pass | Strong Ontario facility baseline with broad service coverage and clear open-data posture | https://data.ontario.ca/dataset/ministry-of-health-service-provider-locations-mohserlo |
| Provider / facility baseline | Open Database of Healthcare Facilities (ODHF) | Canada-wide | Open data download | Structured downloadable file | Open Government Licence - Canada | Periodic | Medium | Low | High | `scheduled_ingest` | Pass | Strong national facility directory; useful as fallback, cross-check, and future expansion layer | https://www.statcan.gc.ca/en/lode/databases/odhf |
| AED strategy | AED Foundation of Ontario registry | Ontario-wide | Public website and registry; partnership path implied | Request-based / partner-oriented registry | Unclear for direct reuse; official registrar status is clear | Unclear publicly; registry maintained continuously | High | Medium to High | Medium | `research_only` | Conditional | Best legitimacy and likely best Ontario coverage, but direct product access path is not yet validated | https://www.aedfoundationontario.ca/ |
| AED strategy | OpenStreetMap AED data (`emergency=defibrillator`) | Global / Ontario subset possible | OpenStreetMap data extraction | Crowdsourced registry / structured dataset | OSM open-data ecosystem | Continuous community updates | High | Medium | Medium to High | `scheduled_ingest` | Pass | Best permissionless fallback for AED mapping; must be clearly labeled as crowdsourced and incomplete | https://wiki.openstreetmap.org/wiki/Tag:emergency=defibrillator |
| Safety alerts | Recalls, advisories and safety alerts database | Canada-wide | Public web app plus daily CSV/JSON feeds | Mixed: dataset + dashboard | Public federal source; daily feeds explicitly offered | Daily | High | Low | High | `scheduled_ingest` | Pass | Strongest consumer alert surface; direct fit for safety module | https://recalls-rappels.canada.ca/en |
| Safety alerts | Recalls and safety alerts RSS feeds | Canada-wide | RSS | Feed | Public federal source | Ongoing / near real-time posting | High | Low | High | `live_ui` | Pass | Simple alert ingestion path for notifications or freshness-aware feeds | https://recalls-rappels.canada.ca/en/rss-feeds |
| Health-product reference | Drug Product Database (DPD) API | Canada-wide | JSON/XML API | Official API | Public federal API for reuse | Ongoing; not stated as nightly on the guide page | Medium | Low | High | `live_ui` | Pass | Useful enrichment layer for medication and product reference data tied to alerts | https://health-products.canada.ca/api/documentation/dpd-documentation-en.html |
| Safety / supply context | Drug Shortages Canada website | Canada-wide | Public website with search and account-based notifications | Dashboard / website only | Public viewing is clear; structured reuse path is not confirmed | Ongoing website updates | High | Medium to High | Low to Medium | `research_only` | Conditional | High public value but weaker machine-access posture than recalls data | https://www.canada.ca/en/health-canada/services/drugs-health-products/drug-products/drug-shortages.html |
| Environmental overlay | AQHI forecasts via GeoMet | Canada-wide | GeoJSON/JSON API surface | Official API | Public federal open-data service | Real-time | High | Low | High | `live_ui` | Pass | Best first environmental overlay: official, machine-readable, current, and consumer-legible | https://api.weather.gc.ca/collections/aqhi-forecasts-realtime?f=html |
| Environmental overlay | ISC long-term drinking water advisories map/data | Canada-wide; Ontario subset available | Public map with download link | Mixed map + downloadable data | Public federal source | Current operational updates | High | Medium | Medium | `scheduled_ingest` | Pass | Strong public-interest overlay, but narrower audience than AQHI; better Batch B/C candidate than first overlay | https://www.sac-isc.gc.ca/eng/1620925418298/1620925434679 |
| EMS / system context | Land Ambulance Response Time Standard - Response Times | Ontario-wide | Ontario Data Catalogue CSV/JSON/XML | Open data portal dataset | Open Government Licence - Ontario | Annual public reporting cycle | Low to Medium | Low | Medium | `analytics_only` | Pass | Good system context layer, but weaker for first consumer batch than facilities/AED/alerts/AQHI | https://data.ontario.ca/dataset/land-ambulance-response-time-standard-response-times |
| Naloxone access | Ontario naloxone kit location map | Ontario-wide | Public Ontario page backed by ArcGIS Web Map and public `FeatureServer` layer | Public web map + ArcGIS feature service | Public source is clear; explicit open-data licence for the layer is not confirmed | Unclear | High | Medium | Medium | `research_only` | Conditional | Strong public-health value and real technical access path, but reuse posture still needs explicit review before product dependence | https://www.ontario.ca/page/where-get-free-naloxone-kit |

---

## Primary-Source Proof Notes

- **MOHSERLO:** Ontario Data Catalogue describes this as the locations of health service providers in Ontario, lists yearly updates, and marks the resource under the Open Government Licence - Ontario.
- **ODHF:** Statistics Canada describes ODHF as open data containing names, types, and locations of healthcare facilities across Canada and releases it under the Open Government Licence - Canada.
- **AED Foundation of Ontario:** The foundation states that it is the official AED Registrar under the Defibrillator Registration and Public Access Act and maintains Ontario’s provincial AED registry with Ministry of Health support.
- **OpenStreetMap AED data:** the OSM wiki documents `emergency=defibrillator` as the approved tag for AED mapping and notes it as a data use pattern for defibrillator locations.
- **Recalls database:** the federal recalls site explicitly says that researchers can access recall and alert data in CSV and JSON formats updated daily.
- **Recalls RSS:** the recalls RSS page explicitly offers category RSS feeds, including health products and medical devices.
- **DPD API:** the API guide explicitly states that developers can access Drug Product Database information in JSON and XML for reuse in their own applications.
- **Drug shortages:** Health Canada’s drug shortages page clearly supports public website access and user notifications, but the current validation pass did not confirm a reusable open-data feed on the public page.
- **AQHI GeoMet:** the GeoMet AQHI collection exposes JSON, schema, queryables, and GeoJSON item endpoints for real-time forecasts.
- **ISC drinking water advisories:** the ISC map page states that the map and table include long-term drinking water advisories on reserve systems and provides a “Download map data” route.
- **Land ambulance response times:** the Ontario Data Catalogue resource page exposes CSV/TSV/JSON/XML and CKAN Data API access under the Open Government Licence - Ontario.
- **Ontario naloxone map:** the Ontario page explicitly presents a public map of pickup locations and is backed by an Ontario-hosted ArcGIS Web Map plus a public `FeatureServer` layer, but this pass still did not confirm an explicit open-data licence for ingestion/reuse.

---

## Shortlist Outcome

### Strong Batch A candidates

- MOHSERLO
- ODHF
- OSM AED fallback
- Recalls database + RSS
- DPD API
- AQHI

### Conditional / not ready for Batch A dependence

- AED Foundation of Ontario registry
- Drug Shortages Canada
- Ontario naloxone map

### Better fit for later context layers than initial launch set

- ISC drinking water advisories
- Land ambulance response-time reporting
