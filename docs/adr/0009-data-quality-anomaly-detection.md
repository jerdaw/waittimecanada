# 0009. Data Quality and Anomaly Detection

Date: 2026-02-06

Status: Accepted

Deciders: Jeremy Dawson

## Context and Problem Statement

How do we ensure research-grade data trust when scraping provincial health data that may contain errors, gaps, or silent methodology changes? A Health Systems Observatory must self-audit its own data pipeline.

## Decision Drivers

* Research credibility requires transparent data quality metrics
* Provincial sources may silently change measurement methodology
* Outlier measurements (data entry errors, unit changes) must be flagged but not excluded
* Need to detect scraper reliability degradation early

## Considered Options

* Manual quality review
* Exclude outliers automatically
* Flag anomalies transparently (audit-only approach)

## Decision Outcome

Chosen option: "Flag anomalies transparently", because excluding data would undermine the observatory's audit mission. Anomalous measurements are flagged with `is_anomaly=TRUE` and `anomaly_reason` but remain in all displays and exports.

### Positive Consequences

* Full data transparency (nothing hidden)
* Researchers can filter anomalies themselves
* Methodology changes detected automatically across all hospitals in a province
* Data quality metrics visible on dedicated `/data-quality` dashboard

### Negative Consequences

* Anomaly flags may produce false positives with insufficient baseline data
* Methodology change detection requires minimum 5 hospitals per source
* Quality snapshots add a caching table that needs periodic computation

## Implementation Details

**Anomaly Detection:** Dual approach using z-score (threshold: 3.0) and IQR (multiplier: 1.5x) against a 7-day rolling baseline. Minimum 20 samples required; insufficient data defaults to "not anomalous".

**Data Quality:** This ADR established the quality-snapshot and anomaly-detection model. The live cadence assumptions were later updated as production scheduling changed. Current production quality KPIs use the active live source set with an hourly expectation model (24 expected runs/day, 60-minute interval, gap detection at 1.5x interval = 90 minutes). Historical notes about the earlier 15-minute model should be read as implementation history, not the current live contract.

**Methodology Change Detection:** Compares week-over-week province-wide means. Flags shifts exceeding 20% across minimum 5 hospitals.

**New tables:** `data_quality_snapshots`, `methodology_change_events`. New columns on `measurements`: `is_anomaly`, `anomaly_reason`.

**Scraper integration:** Anomaly checking runs in `BaseScraper.run()` with try/except — failures never break scraping.

## Links

* [Related to] [ADR-0008](0008-aggregation-pipeline.md) (depends on aggregation infrastructure)
* Implementation plan: `docs/planning/archive/milestone-14-data-quality.md`
