# ADR 0003: Manual Geocoding Overrides

## Status
Accepted

## Context
Automated geocoding services (Nominatim, Mapbox) frequently fail to resolve specific hospital sites, especially those within larger health networks or with ambiguous names (e.g., "Main Site" vs "General Site"). 

In Ontario, approximately 53% (82 hospitals) failed automated geocoding during the initial run, returning placeholder coordinates (0.0, 0.0). While improving fuzzy matching or adding premium APIs (Google Places) are options, they are either non-deterministic or incur ongoing costs. We need a reliable, deterministic way to ensure 100% geocoding accuracy for known facilities.

## Decision
We will implement a manual override system using a CSV file (`backend/data/ontario_hospital_coordinates.csv`) as the primary source of truth for hospital coordinates.

1. The `GeocodingService` will look up a hospital ID in the manual overrides file *before* attempting any automated geocoding.
2. If an override exists, it is used immediately with 100% confidence.
3. Automated services (Mapbox, Nominatim) serve only as fallback mechanisms for newly discovered hospitals.
4. Maintenance of coordinates is now a data quality task (manual population) rather than a software engineering task (improving scrapers).

The `scraper.py` CLI will pass the `hospital_id` to the geocoding service to enable this lookup.

## Consequences

| Impact | Category | Rationale |
| --- | --- | --- |
| **Positive** | Data Quality | 100% locational accuracy for verified hospitals. |
| **Positive** | Reliability | Decouples map display from external API rate limits or downtime. |
| **Positive** | Cost | Zero ongoing API costs for known hospitals. |
| **Negative** | Overhead | Requires manual research for new hospital facilities. |
| **Neutral** | Process | Shifting responsibility from geocoding logic to geocoding data. |
