# ADR-005: Use Manual Overrides as Primary Geocoding Source

### Status

Accepted

### Context

Accurate geographic coordinates are critical for the hospital map. Automated geocoding services (Nominatim, Mapbox) frequently fail to resolve specific hospital sites, especially those within larger health networks or with ambiguous names (e.g., "Main Site" vs "General Site"). 

Initial automated geocoding resulted in ~50% of Ontario hospitals having incorrect or missing (0,0) coordinates.

### Decision

Implement a manual override system using a CSV file (`backend/data/ontario_hospital_coordinates.csv`) as the primary source of truth for hospital coordinates. 

1. The `GeocodingService` will look up a hospital ID in the manual overrides file before attempting any automated geocoding.
2. If an override exists, it is used immediately.
3. Automated services (Mapbox, Nominatim) serve only as fallback mechanisms for newly discovered hospitals.
4. Maintenance of coordinates is now a data quality task (manual population) rather than a software engineering task (improving scrapers).

### Consequences

| Impact | Category | Rationale |
| --- | --- | --- |
| **Positive** | Data Quality | 100% locational accuracy for verified hospitals. |
| **Positive** | Reliability | Decouples map display from external API rate limits or downtime. |
| **Negative** | Overhead | Requires manual research for new hospital facilities. |
| **Neutral** | Process | Shifting responsibility from geocoding logic to geocoding data. |
