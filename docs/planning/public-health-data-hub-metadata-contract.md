# Public Health Data Hub Source Metadata Contract

**Created:** 2026-03-27
**Status:** Historical planning baseline. Batch A is delivered and later Ontario additions are live; use `docs/API.md` and `docs/architecture/*` for the current shipped contract.
**Related:** [Batch A implementation plan](implementation/archived/public-health-data-hub-batch-a-plan.md), [decision brief](archive/public-health-data-hub-decision-brief.md)

---

## Summary

This document preserves the v1 metadata contract that locked the original
public-health source-catalog field names for Batch A planning.

The goal is to prevent the Batch A implementation plan from inventing schema names, field meanings, or enum values ad hoc.

This contract is a historical planning interface. It informed implementation,
migrations, API responses, and tests without renaming fields, but it is no
longer the living implementation spec.

---

## Required Fields

| Field | Type | Meaning |
|---|---|---|
| `source_id` | string | Stable internal identifier, kebab-case |
| `domain` | enum | High-level domain owning the source |
| `source_name` | string | Public display name |
| `scope` | enum | Geographic coverage scope |
| `jurisdiction_level` | enum | Institutional level that publishes the source |
| `connector_type` | enum | How data is accessed technically |
| `access_route` | string | Human-readable access route summary |
| `license_reuse_status` | enum | Legal/reuse posture for implementation |
| `attribution_requirement` | string | Required attribution or source-labeling note |
| `update_cadence` | string | Upstream update rhythm as known publicly |
| `freshness_sensitivity` | enum | How harmful stale data would be |
| `operational_risk` | enum | Operational fragility of this source in product use |
| `recommended_usage_mode` | enum | Intended usage in the app |
| `provenance_url` | string | Canonical source or feed URL |
| `last_verified_at` | string (ISO date) | Last manual verification date |

---

## Optional Fields

| Field | Type | Meaning |
|---|---|---|
| `notes` | string | Short planner or operator note |
| `fallback_source_id` | string | Alternate source when the primary source is unavailable |
| `public_methodology_note` | string | Human-facing caveat about interpretation or data meaning |

---

## Enums

### `domain`

- `provider_facility`
- `aed`
- `safety_alert`
- `health_product_reference`
- `environmental_overlay`
- `system_context`

### `scope`

- `canada`
- `ontario`
- `regional`
- `municipal`
- `institution`

### `jurisdiction_level`

- `federal`
- `provincial`
- `municipal`
- `regional`
- `institution`
- `nonprofit_other`

### `connector_type`

- `api`
- `feed`
- `open_data_portal`
- `file_download`
- `dashboard_only`
- `request_based`
- `partner_only`
- `crowdsourced_registry`

### `license_reuse_status`

- `approved`
- `approved_with_conditions`
- `blocked`

### `freshness_sensitivity`

- `low`
- `medium`
- `high`

### `operational_risk`

- `low`
- `medium`
- `high`

### `recommended_usage_mode`

- `live_ui`
- `scheduled_ingest`
- `analytics_only`
- `research_only`
- `do_not_use`

---

## Batch A Defaults

The Batch A milestone plan should assume these default source records:

- MOHSERLO: `provider_facility`, `open_data_portal`, `approved_with_conditions`, `scheduled_ingest`
- ODHF: `provider_facility`, `file_download`, `approved_with_conditions`, `scheduled_ingest`
- OSM AED fallback: `aed`, `crowdsourced_registry`, `approved_with_conditions`, `scheduled_ingest`
- Recalls feeds: `safety_alert`, `feed` or `open_data_portal`, `approved_with_conditions`, `scheduled_ingest`
- DPD API: `health_product_reference`, `api`, `approved_with_conditions`, `live_ui`
- AQHI: `environmental_overlay`, `api`, `approved_with_conditions`, `live_ui`

---

## Contract Rules

1. `source_id` must stay stable once introduced.
2. `license_reuse_status` is implementation-gating metadata, not decorative documentation.
3. `recommended_usage_mode` determines whether stale-data rules can show, warn, or suppress output.
4. `provenance_url` is required for every public-facing Batch A source.
5. Optional fields must not be upgraded to required in Batch A implementation without updating this contract first.

---

## Immediate Implementation Implications

- Database and API work for Batch A must preserve these field names.
- UI surfaces that show public provenance should use `source_name`, `provenance_url`, `last_verified_at`, and freshness status derived from `update_cadence` plus runtime sync state.
- Test fixtures for Batch A should include at least one source record per Batch A domain using this exact shape.
