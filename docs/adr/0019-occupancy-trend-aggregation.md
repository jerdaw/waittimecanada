# 0019. Include STRETCHER_OCCUPANCY in the Aggregation Pipeline

Date: 2026-02-19

Status: Accepted

Deciders: Project owner

Technical Story: M33 — Historical Occupancy Trends & Scraper Hardening

## Context and Problem Statement

Quebec's MSSS-sourced scraper captures stretcher occupancy rates (`STRETCHER_OCCUPANCY` metric family) alongside wait-time measurements. These occupancy readings were being stored in the `measurements` table but were not passed through the `AggregationService` pipeline. As a result, no aggregate statistics (mean, median, P90) were computed for occupancy, making it impossible to surface historical occupancy trends in the analytics dashboard.

Should `STRETCHER_OCCUPANCY` be included in the same aggregation pipeline as `TIME_TO_PROVIDER` / `TOTAL_LOS` metrics, and if so, how should the pipeline handle periods that mix metric families?

## Decision Drivers

* QC stretcher occupancy data is already collected; surfacing it as a trend adds material value without new scraper work.
* Occupancy (`%`) and wait times (`minutes`) are incommensurable — mixing them in a single aggregate would produce a meaningless number.
* The ontology tagging system already carries `metric_family`; the aggregation pipeline should respect it.
* Missing days (e.g., source outages) must be handled gracefully without producing misleading carry-forward values.

## Considered Options

* **Option A:** Exclude `STRETCHER_OCCUPANCY` from aggregation (status quo).
* **Option B:** Include `STRETCHER_OCCUPANCY` in aggregation but compute a single cross-family aggregate per period.
* **Option C:** Group measurements by `metric_family` before aggregation, producing one aggregate per family per period (chosen).

## Decision Outcome

Chosen option: **C — group by metric_family**, because grouping within the existing ontology framework ensures each aggregate row is internally homogeneous, and the unique constraint on `measurement_aggregates(hospital_id, period_type, period_start, metric_family)` prevents cross-family conflicts.

### Positive Consequences

* `AggregationService.aggregate_period` now returns a `list[MeasurementAggregate]`, one per distinct ontology group, enabling multi-family periods in a single call.
* The `trends/route.ts` API accepts a `metric_family` query parameter, allowing the frontend to request occupancy trends independently of wait-time trends.
* The analytics page conditionally renders a collapsible "Historical Occupancy Trend" panel only when `STRETCHER_OCCUPANCY` data is confirmed available for the selected province.
* Database migration `015_add_metric_family_to_aggregates.sql` updates the unique constraint to include `metric_family`.

### Negative Consequences

* Callers of `aggregate_period` that previously expected a single `MeasurementAggregate` return must be updated to handle a list — this was a breaking internal API change, reflected in unit tests.
* Backfill runs for periods already aggregated without the `metric_family` constraint may produce duplicate-key conflicts; the `ON CONFLICT DO NOTHING` clause mitigates this silently.

## Pros and Cons of the Options

### Option A — Exclude (status quo)

* Good, because no code change required.
* Bad, because QC occupancy data sits unused in the database.
* Bad, because it forgoes a unique analytical dimension that distinguishes this platform.

### Option B — Single cross-family aggregate

* Good, because simpler pipeline code.
* Bad, because meaningless: averaging minutes and percentages yields a scientifically invalid result.

### Option C — Group by metric_family (chosen)

* Good, because respects the ontology; each aggregate is internally homogeneous.
* Good, because leverages the existing `metric_family` column in `measurement_aggregates`.
* Good, because minimal schema change (unique constraint extension only).
* Bad, because introduces a breaking internal API change (list return type).

## Missing Data Handling

Periods with zero occupancy measurements produce no aggregate row for that family (the loop skips empty groups). Missing days are represented as **gaps** (no row), not as carry-forward estimates. The frontend chart renders gaps as discontinuities, which is preferable to false smoothing.

## Links

* [Refines] [ADR-0008](0008-aggregation-pipeline.md) — Original aggregation pipeline decision
* [Refines] [ADR-0002](0002-metric-ontology.md) — Strict Metric Ontology
* [Related to] [ADR-0012](0012-occupancy-availability-contract.md) — Occupancy availability contract
