# Public Health Data Hub Freshness And Safety Rules

**Created:** 2026-03-27
**Status:** Frozen for Batch A planning
**Related:** `docs/planning/public-health-data-hub-metadata-contract.md`

---

## Summary

Batch A contains public, user-facing data with different freshness and safety profiles. This document freezes the minimum show/warn/suppress rules and the mandatory caveat language classes the implementation must support.

The implementation may be stricter than these rules, but it must not be looser.

---

## Cross-Domain Rules

1. Every freshness-sensitive surface must show a last-refreshed timestamp.
2. If freshness cannot be determined, the UI must not imply real-time certainty.
3. If the source sync state is degraded beyond the suppress threshold, the data should be hidden and replaced with a source-unavailable state.
4. Provenance must be visible on detail surfaces and easy to access on list or card surfaces.
5. Any crowdsourced fallback source must be labeled as such in the UI, not just in docs.

---

## Domain Rules

### Provider / Facility Baseline

**Purpose:** directory and map reference, not live operational status.

| State | Rule |
|---|---|
| Show | last successful sync is within 18 months |
| Warn | last successful sync is older than 18 months but within 30 months |
| Suppress | last successful sync is older than 30 months, or provenance is missing |

**Required caveat class:**
`Reference directory data. Not a live operational status feed.`

### AED Data (OSM fallback)

**Purpose:** nearby AED awareness with explicit incompleteness caveat.

| State | Rule |
|---|---|
| Show | last successful sync is within 30 days and provenance is present |
| Warn | last successful sync is older than 30 days but within 90 days |
| Suppress | last successful sync is older than 90 days, provenance is missing, or legal gate is unresolved |

**Required caveat class:**
`Crowdsourced AED data. Incomplete and may be outdated. In an emergency call 911 immediately.`

If an official Ontario registry path is later approved, this rule set may be revised in a new planning artifact or ADR.

### Recalls / Safety Alerts

**Purpose:** current official public alerts.

| State | Rule |
|---|---|
| Show | last successful sync is within 24 hours |
| Warn | last successful sync is older than 24 hours but within 48 hours |
| Suppress | last successful sync is older than 48 hours |

**Required caveat class:**
`Official recall and safety alert data. Last refreshed [timestamp].`

### Drug Product Reference Enrichment

**Purpose:** enrich alert or product detail, not act as a standalone emergency signal.

| State | Rule |
|---|---|
| Show | API response returns successfully and provenance is present |
| Warn | upstream API degraded; render alert without enrichment |
| Suppress | enrichment block does not render at all if unavailable |

**Required caveat class:**
`Reference data from the official Drug Product Database.`

### AQHI Environmental Overlay

**Purpose:** current air quality health context.

| State | Rule |
|---|---|
| Show | last upstream publication is within 6 hours |
| Warn | last upstream publication is older than 6 hours but within 12 hours |
| Suppress | last upstream publication is older than 12 hours or missing |

**Required caveat class:**
`Official AQHI forecast from Environment and Climate Change Canada. Conditions may change.`

---

## Degraded States

The implementation must support a consistent degraded-state pattern:

- source available and fresh
- source available with stale warning
- source temporarily unavailable
- source intentionally suppressed due to freshness or legal gate

Degraded states should preserve module usability. For example:

- AQHI being unavailable must not break facilities or alerts
- alert sync failure must not remove provider baseline results
- AED suppression must not remove the overall resources page

---

## Immediate Implementation Implications

- API responses for Batch A must carry enough freshness metadata for the UI to apply these rules.
- Tests must cover show/warn/suppress behavior for each Batch A domain.
- No Batch A milestone task should ship without the matching caveat class and freshness state behavior.
