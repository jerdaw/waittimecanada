# 2026-03 Operational Report

**Date:** 2026-03-28
**Scope:** Core emergency wait-time platform operations
**Status:** Historical snapshot for the daytime March 28 review. A later same-day
production incident left Neon database connectivity blocked by transfer quota;
see `docs/operations/incident-reports/2026-03-28-neon-transfer-quota.md`.

## Executive Summary

Wait Time Canada's live production posture in late March 2026 is operationally stable but intentionally split:

- the public frontend is served from the shared VPS behind host Caddy
- the authoritative backend scheduler path remains GitHub Actions
- the VPS backend worker cutover remains deferred because the Ontario upstream is not reliably reachable from that VPS

In the recent sample reviewed for this report, the operational signals were broadly healthy:

- **19 of 19** most recent completed `Scraper Cron Job` runs succeeded
- **20 of 20** most recent completed `Heartbeat Monitor (Dead Man's Switch)` runs succeeded
- the most recent public status snapshot showed all four active live provincial scrapers with fresh heartbeats and `healthy` last-run state
- no methodology drift events were reported in the last 30 days by the public status endpoint snapshot used here

The main operational caveat is not a failing scraper. It is a **reporting-metric mismatch**: the public `/api/status` and `/api/data-quality` endpoints still score source performance against an older **15-minute expected cadence** (`96` expected scrapes/day), even though the live scheduler currently runs **hourly** on GitHub Actions. Those public "uptime" / "success rate" fields therefore understate actual reliability and should not currently be read as literal uptime KPIs.

## Evidence Basis

This report was compiled on **2026-03-28** using live read surfaces that are backed by the platform's operational tables:

- `https://wait-time.ca/api/status`
- `https://wait-time.ca/api/data-quality`
- recent GitHub Actions workflow history via `gh run list`

This means the report is grounded in the same `scraper_status` and `data_quality_snapshots` paths used by the application, without requiring direct database access in this pass.

## Runtime Posture

### Frontend

- Public runtime: shared VPS behind host Caddy
- Canonical domain: `https://wait-time.ca`
- Current posture: live and stable

### Backend scheduler

- Live scheduler path: GitHub Actions
- Current cadence: hourly scraper cron
- Heartbeat checks: every 30 minutes
- VPS backend worker path: still deferred because the Ontario upstream is not reliably reachable from that host

This split production model remains the correct short-term posture. It keeps the public site on the VPS while avoiding an unstable backend move.

## Recent Workflow Reliability

### Scraper cron

Sample reviewed:

- workflow: `Scraper Cron Job`
- recent sample: **20** most recent runs
- completed runs in sample: **19**
- successful completed runs in sample: **19**

Interpretation:

- the recent completed sample was clean
- one run was in progress during observation and was not counted as either success or failure
- no immediate evidence of active scheduler instability was visible in this sample

### Heartbeat monitor

Sample reviewed:

- workflow: `Heartbeat Monitor (Dead Man's Switch)`
- recent sample: **20** most recent runs
- completed runs in sample: **20**
- successful completed runs in sample: **20**

Interpretation:

- the dead-man's-switch path is currently behaving as intended
- the alerting path appears operational in the recent sample, with no active stale-source incident visible

## Current Public Status Snapshot

Public status snapshot used:

- generated at: `2026-03-28T17:13:43.821Z`
- source: `/api/status`

Key observations from that snapshot:

- `alberta-ahs`: `healthy`, heartbeat age `0` minutes
- `bc-phsa`: `healthy`, heartbeat age `0` minutes
- `ontario-health`: `healthy`, heartbeat age `0` minutes
- `quebec-msss`: `healthy`, heartbeat age `59` minutes
- drift events in last 30 days reported by the endpoint: `0`

This is the operational signal that matters most for the current report: the active live sources were reporting fresh heartbeats and healthy last-run state at the time of review.

## Current Public Data-Quality Snapshot

Public data-quality snapshot used:

- source: `/api/data-quality`
- same observation window as above

Reported values:

- total measurements in the last 24 hours: `8,976`
- total hospitals reporting in the last 24 hours: `273`
- overall status returned by endpoint: `critical`

These counts are useful operationally. The overall `critical` label is **not** a trustworthy standalone summary right now, for two reasons:

1. the route still assumes `96` expected scrapes/day, which matches a 15-minute cadence rather than the current hourly scheduler path
2. the source inventory still includes dormant or legacy rows such as `manitoba-shared-health` and `on-health`, which drag down public roll-ups even though they are not active live scraper paths

## Important Reliability Caveat

The current public `/api/status` and `/api/data-quality` routes are useful for transparency, but their aggregate percentages need interpretation.

### Why the reported rates are misleading right now

The route logic currently uses:

- `EXPECTED_SCRAPES_PER_DAY = 96`

That implies a scrape every 15 minutes. The live scheduler is currently hourly. As a result:

- a healthy hourly source can appear to have very low "uptime"
- Quebec can appear artificially stronger because it publishes more than one live measurement type per hospital in the current platform
- dormant legacy source rows lower overall averages even when the active live sources are healthy

This does **not** mean the public status endpoints are useless. It means their aggregate percentages are currently closer to a legacy proxy than a clean reliability KPI.

## Incidents and Recoveries

No new active incident was visible in the recent sampled workflow history used for this report.

The most important ongoing operational constraint remains the previously established one:

- the Ontario upstream is not reliably reachable from the shared VPS
- therefore GitHub Actions remains the live backend scheduler path

That is an accepted production constraint, not a newly discovered March incident.

## Public Health Hub Operational Note

The `/resources` module is live and has its own workflow/monitoring surfaces, but this report is focused on the core emergency wait-time platform. The public-health-hub ingest path should continue to be treated as a related but separate operational lane when reviewing alerts and summary health.

## Recommended Follow-Up

### 1. Align public status/data-quality KPI math with the live scheduler contract

This is the clearest operational follow-up from the March review.

The public status and data-quality routes should be updated so they:

- reflect the **hourly** live scheduler cadence instead of the older 15-minute expectation
- scope "overall" roll-ups to the actually active live sources
- distinguish heartbeat freshness from measurement-density expectations more clearly

### 2. Keep the split production posture

Do not force VPS backend cutover while the Ontario reachability issue remains unresolved. The current split model is operationally defensible.

### 3. Continue monthly review behavior

The value of this report is not just the numbers. It is the practice of doing the review, recording caveats honestly, and leaving a paper trail for future operational decisions.

## Bottom Line

The platform is operationally healthy enough to support the current public site, but its public reliability roll-ups need calibration to the actual live scheduler model. March's main stewardship finding is not "scrapers are failing." It is "our public ops summary still reflects an older cadence assumption and should be corrected."
