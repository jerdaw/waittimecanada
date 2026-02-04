# ADR 0003: Manual Geocoding Override

## Status
Accepted

## Context
Automated geocoding (Nominatim, Mapbox) often fails for specific hospital branch names or newly opened facilities. In Ontario, approximately 53% (82 hospitals) failed automated geocoding during the initial run, returning placeholder coordinates (0.0, 0.0).

While improving fuzzy matching or adding premium APIs (Google Places) are options, they are either non-deterministic or incur ongoing costs. We need a reliable, deterministic way to ensure 100% geocoding accuracy for known facilities.

## Decision
We will implement a manual override system using a CSV file (`backend/data/ontario_hospital_coordinates.csv`).

The `GeocodingService` will:
1. Load this CSV during initialization.
2. Check if a `hospital_id` exists in the manual override map *before* attempting external geocoding.
3. If an override exists, return it immediately with 100% confidence.

The `scraper.py` CLI will be updated to pass the `hospital_id` to the geocoding service.

## Consequences
- **Pros**:
  - Deterministic 100% accuracy for manual entries.
  - Zero ongoing API costs for known hospitals.
  - No dependency on external service availability for overridden facilities.
  - Easy for non-technical contributors to fix geocoding issues via CSV.
- **Cons**:
  - Requires manual effort to populate the CSV.
  - Manual data can become stale if a hospital moves (rare for medical facilities).
