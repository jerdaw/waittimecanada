# ADR-0006: Source Freshness Monitoring

**Status:** Accepted
**Date:** 2026-02-05
**Related:** Source freshness and public data-quality reporting

---

## Context

Provincial wait-time scrapers can fail silently when source pages change,
network conditions degrade, or database writes fail. Silent failure is a core
risk for a health systems observatory because stale data can look current to
users unless freshness is explicit.

## Decision

Wait Time Canada uses a source freshness monitoring model:

1. Every scraper run writes a status record with source ID, timestamp, status,
   and failure context where available.
2. A heartbeat CLI checks source status records and classifies stale or failed
   sources.
3. Public API and UI surfaces expose freshness state rather than implying that
   all displayed data is current.
4. Operational notifications should be state-change aware so one unresolved
   condition does not repeatedly notify.

## Rationale

- Users need visible freshness context to interpret public wait-time data.
- A source-health table provides a simple audit trail for scraper runs.
- State-change handling reduces alert noise while preserving recovery signals.
- The public product can communicate degraded data quality without exposing
  private monitoring configuration.

## Consequences

### Positive

- Stale source data can be identified and displayed.
- Public data-quality pages can distinguish collection failures from normal
  source behavior.
- Backend tests can validate stale/error/recovery paths independently from any
  private alert provider.

### Negative

- The freshness model depends on successful database writes.
- Thresholds and notification routing remain operational policy and must be
  documented outside public runbooks.

## Public Contract

- `/api/health` returns overall and per-source health state.
- `scraper_status` stores last run and status details.
- `scraper_alert_state` stores stateful incident/recovery information.
- UI copy must treat freshness as a data-quality signal, not a guarantee of
  real-time source accuracy.

## Related Documents

- API documentation: `../API.md`
- Data dictionary: `../reference/data-dictionary.md`
- Public source-freshness notes: `../operations/scraper-scheduling.md`
