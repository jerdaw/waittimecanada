# 0008. Two-Tier Aggregation Pipeline

Date: 2026-02-06

Status: Accepted

Deciders: Jeremy Dawson

> Update (2026-03-13): the aggregate architecture in this ADR remains active,
> but the original assumption of automatic 30-day raw-data deletion is no
> longer the default operating policy. Raw measurements are now preserved by
> default, and aggregates remain the efficient long-range analytics layer.

## Context and Problem Statement

How do we enable longitudinal analysis (90-day, 6-month, 1-year trends)
without forcing every analytics query to scan the full raw measurement table?

## Decision Drivers

* Need efficient long-range analytics even when raw measurements are preserved
* Need for long-range trend analysis (Scholar narrative)
* Research-grade data export requires extended date ranges
* Must preserve ontology metadata for comparability analysis

## Considered Options

* Keep all raw data indefinitely
* Pre-computed materialized views
* Two-tier architecture: raw measurements + permanent aggregates

## Decision Outcome

Chosen option: "Two-tier architecture", because it balances analytical depth
with query efficiency. Raw measurements remain available for high-granularity
analysis, while permanent aggregates enable longitudinal research and cheaper
read paths.

### Positive Consequences

* Enables 90d/6m/1y trend visualization
* Data export supports extended date ranges with granularity selector
* Ontology tags denormalized into aggregates preserve historical methodology context
* Backfill CLI allows recomputing aggregates from existing raw data

### Negative Consequences

* Aggregates lose individual measurement granularity
* Two-step query pattern (check aggregates first, fall back to raw)
* Requires scheduled aggregation maintenance even when no purge is planned

## Implementation Details

**Table:** `measurement_aggregates` with period types: hourly, daily, weekly, monthly.

**Statistics per aggregate:** mean, median, p90, min, max, std_dev, sample_count.

**CLI:** `python -m waittime.cli.aggregate` with `--backfill`, `--incremental`, `--dry-run` flags.

**Frontend integration:** TrendChart extended with 90d/6m/1y buttons; DataExport extended with granularity selector.

## Links

* [Related to] [ADR-0002](0002-metric-ontology.md) (ontology tags denormalized into aggregates)
* Implementation plan: `docs/planning/archive/milestone-13-aggregation.md`
