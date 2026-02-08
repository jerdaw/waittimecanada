# 0008. Two-Tier Aggregation Pipeline

Date: 2026-02-06

Status: Accepted

Deciders: Jeremy Dawson

## Context and Problem Statement

Raw measurements have a 30-day retention window to manage storage costs on Neon's free tier. How do we enable longitudinal analysis (90-day, 6-month, 1-year trends) when the raw data is deleted after 30 days?

## Decision Drivers

* 30-day raw data retention policy (storage constraint)
* Need for long-range trend analysis (Scholar narrative)
* Research-grade data export requires extended date ranges
* Must preserve ontology metadata for comparability analysis

## Considered Options

* Keep all raw data indefinitely
* Pre-computed materialized views
* Two-tier architecture: raw measurements + permanent aggregates

## Decision Outcome

Chosen option: "Two-tier architecture", because it balances storage constraints with analytical depth. Raw measurements provide operational freshness (last 30 days), while permanent aggregates enable longitudinal research.

### Positive Consequences

* Enables 90d/6m/1y trend visualization
* Data export supports extended date ranges with granularity selector
* Ontology tags denormalized into aggregates preserve historical methodology context
* Backfill CLI allows recomputing aggregates from existing raw data

### Negative Consequences

* Aggregates lose individual measurement granularity
* Two-step query pattern (check aggregates first, fall back to raw)
* Requires scheduled aggregation step before cleanup

## Implementation Details

**Table:** `measurement_aggregates` with period types: hourly, daily, weekly, monthly.

**Statistics per aggregate:** mean, median, p90, min, max, std_dev, sample_count.

**CLI:** `python -m waittime.cli.aggregate` with `--backfill`, `--incremental`, `--dry-run` flags.

**Frontend integration:** TrendChart extended with 90d/6m/1y buttons; DataExport extended with granularity selector.

## Links

* [Related to] [ADR-0002](0002-metric-ontology.md) (ontology tags denormalized into aggregates)
* Implementation plan: `docs/planning/archive/milestone-13-aggregation.md`
