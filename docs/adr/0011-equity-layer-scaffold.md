# ADR 0011: Equity Layer Scaffold-First Delivery

## Status
Partially Superseded by ADR-0015 (2026-02-18)

## Context
Milestone 11 requires an income-overlay equity layer, but full census-tract integration depends on
external StatsCan datasets that may not be immediately available during autonomous implementation.

## Decision
Deliver an end-to-end scaffold first:

1. Add a dedicated API route (`/api/equity-layer`) with province-aware responses.
2. Return Ontario placeholder GeoJSON with explicit metadata that it is scaffold data.
3. Integrate map toggle + legend + attribution rendering now.
4. Keep unsupported provinces explicit with setup instructions in API responses.

## Rationale
This keeps the product honest while unblocking UX, API contracts, and testing:

- Enables immediate validation of map-layer plumbing and UI affordances.
- Prevents misleading claims by labeling placeholder data clearly.
- Reduces merge risk when replacing placeholder payloads with real StatsCan data later.

## Consequences

### Positive
- Equity overlay feature path is functional and test-covered.
- Future data replacement is isolated to the API/data layer.
- Roadmap progress can distinguish scaffold completion from data completion.

### Tradeoff
- Current overlay does not yet represent real socioeconomic conditions.

## Follow-Up

1. Ingest real StatsCan census tract boundaries + income variables.
2. Replace placeholder GeoJSON payload with processed provincial datasets.
3. Keep attribution and methodology notes synchronized with final data source/version.

## Supersession Notes

- Ontario real-data integration is now governed by ADR-0015.
- Scaffold-first behavior remains relevant for provinces not yet onboarded with real tract datasets.
