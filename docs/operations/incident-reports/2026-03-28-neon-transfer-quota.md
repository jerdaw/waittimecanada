# 2026-03-28 Neon Transfer Quota Exhaustion

**Date:** 2026-03-28
**Severity:** High
**Status:** Open external blocker
**Scope:** Production database connectivity, live API availability, heartbeat monitoring

## Summary

On the evening of **2026-03-28**, production verification revealed that Neon
was rejecting database connections for the live project with the error:

`Your project has exceeded the data transfer quota. Upgrade your plan to increase limits.`

This is not a scraper/parser bug or a frontend deploy bug. It is an external
production database quota failure.

## User-Facing Impact

At the time of verification:

- `https://wait-time.ca/api/health` returned `healthy: false`
- the database status reported as `disconnected`
- DB-backed routes returned `500`, including:
  - `/api/hospitals`
  - `/api/resources`
  - `/api/status`
  - `/api/data-quality`
- the public frontend remained up behind Caddy, but key live data surfaces were
  functionally unavailable

## Detection

The issue was discovered during roadmap/documentation closeout after a docs-only
push, while checking current CI and live operational state rather than assuming
the earlier day’s green runs still reflected the live platform.

## Evidence

### Live endpoint checks

Observed on 2026-03-28:

- `https://wait-time.ca/api/health`
  - returned `{"healthy":false,"database":{"status":"disconnected"...}}`
- `https://wait-time.ca/api/hospitals?province=ON&limit=3`
  - returned `500`
- `https://wait-time.ca/api/resources?kind=facility&province=ON&limit=3`
  - returned `500`
- `https://wait-time.ca/api/status`
  - returned `500`
- `https://wait-time.ca/api/data-quality`
  - returned `500`

Representative error message:

`Your project has exceeded the data transfer quota. Upgrade your plan to increase limits.`

### Workflow evidence

Recent `Heartbeat Monitor (Dead Man's Switch)` failures:

- run `23693923403`
- run `23694326251`

Both failed in `check_heartbeat` when `psycopg2.connect(...)` attempted to
connect to Neon and received the same transfer-quota error.

## What Still Worked

- the public frontend container and host Caddy path were still serving pages
- docs CI and docs deploy were unaffected
- earlier in the day, recent `Scraper Cron Job` and `Public Health Hub Ingest`
  runs had still succeeded before the quota block became visible

## Root Cause

The immediate root cause is external quota exhaustion at the managed Neon
database layer.

The repository/workflow implication is that the platform still depends on live
database access for:

- all core public APIs
- `/resources`
- heartbeat monitoring
- public status/data-quality surfaces

So when the managed database path becomes unavailable for quota reasons, the
live site loses most of its operational value even though the frontend host
itself remains healthy.

## Mitigation Taken

- recorded the incident in repo docs and the canonical roadmap
- updated the restart point in the roadmap so future work resumes from recovery,
  not from unrelated roadmap items
- paused further feature work pending external resolution

## Required Recovery Step

One of the following must happen before roadmap execution resumes:

1. the Neon quota window resets
2. the Neon plan/transfer quota is increased
3. production moves to a different database/runtime path that restores
   connectivity

## Recovery Verification Checklist

When external remediation is complete:

1. confirm `https://wait-time.ca/api/health` reports the database as connected
2. confirm `/api/hospitals`, `/api/resources`, `/api/status`, and
   `/api/data-quality` no longer return `500`
3. rerun production smoke/readiness
4. confirm `Heartbeat Monitor (Dead Man's Switch)` has recovered
5. then resume the next open engineering item on the roadmap

## Follow-Up

This incident should inform later cost/architecture work, especially:

- tighter transfer-budget awareness for Neon-backed production reads
- possible first-party VPS/log-derived telemetry instead of extra third-party
  services
- eventual reconsideration of the production database/runtime path if quota
  pressure remains recurring
