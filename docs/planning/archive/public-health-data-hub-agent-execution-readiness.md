# Public Health Data Hub Agent Execution Readiness

**Created:** 2026-03-27
**Status:** Archived after Batch A delivery
**Related:** `docs/planning/implementation/archived/public-health-data-hub-batch-a-plan.md`

---

## Summary

This document audits the public-health-data-hub Batch A planning bundle for autonomous execution by a coding agent.

The goal is not full autonomy at any cost. The goal is to maximize safe autonomous implementation while isolating the few decisions that still require human approval.

Default rule:

- agent can research, implement, and test against the approved Batch A source set
- human must sign off on legal/reuse acceptance, safety-posture wording classes, and any source or scope change outside the approved set

---

## Readiness Review

| Planning area | Status | What was missing | Resolution / gate |
|---|---|---|---|
| Product surface and route placement | `agent-ready` | none | Locked to `/[locale]/resources` inside the existing app shell |
| Data model and storage concepts | `agent-ready-after-doc-fix` | concrete table names and record shapes were implicit | Resolved by the Batch A plan and this execution packet |
| Backend ingestion posture | `agent-ready` | none | Scheduled ingest for DB-backed sources; live proxy only for AQHI and DPD enrichment |
| API surfaces | `agent-ready-after-doc-fix` | response shapes and validation schema names were not frozen | Resolved in the Batch A plan under concrete interface contracts |
| Provider/facility behavior | `agent-ready` | none | MOHSERLO primary, ODHF secondary, directory-only claims |
| AED behavior | `human-signoff-required` | final launch posture depends on approved copy and continued acceptance of OSM fallback | Agent can implement; human must sign off before merge/release |
| Alerts behavior | `agent-ready` | none | Official feeds only; DPD remains enrichment-only |
| AQHI behavior | `agent-ready` | none | Live proxy with cache and suppress-on-stale rules |
| Freshness and safety rules | `agent-ready` | none | Frozen in `public-health-data-hub-freshness-safety-rules.md` |
| Navigation and IA | `agent-ready` | none | Add one top-level `Resources` route without altering current app structure |

---

## Human Sign-Off Ledger

These are explicit stop points. A coding agent should not decide them on its own.

| Item | Sign-off owner | Why it is human-gated | Agent action before stop |
|---|---|---|---|
| Reconfirm Batch A legal/reuse review is still accepted at implementation start | `legal_reuse` | external-source terms may change | restate the approved source set and cite the legal review artifact |
| Final public-facing caveat copy for AED, alerts, and AQHI | `clinical_safety` | changes public safety posture and claim boundaries | implement the required caveat classes exactly as planned and present the final strings for approval |
| Replacing OSM AED fallback with an Ontario registry path | `product` + `legal_reuse` | changes source legitimacy, access path, and claim posture | keep the OSM fallback implementation modular and document the replacement seam |
| Expanding beyond the approved Batch A source set | `product` | changes scope and planning assumptions | stop and request a new source review rather than improvising |

---

## Execution Control Schema

Every Batch A work package and source should be classified with these fields:

- `automation_class`: `agent_autonomous` | `agent_with_human_signoff` | `human_only`
- `signoff_owner`: `product` | `legal_reuse` | `clinical_safety` | `none`
- `blocking_dependency`: short string or `none`
- `implementation_entrypoints`: concrete code areas the agent is expected to touch
- `verification_commands`: exact commands to run before handoff
- `completion_artifacts`: tests, docs, or evidence expected when the package is done

The Batch A packet below freezes those values.

---

## Batch A Execution Packet

### Package 1: Foundation

| Field | Value |
|---|---|
| `automation_class` | `agent_autonomous` |
| `signoff_owner` | `none` |
| `blocking_dependency` | `none` |
| `implementation_entrypoints` | `backend/migrations/018_create_public_health_hub_tables.sql`, `backend/src/waittime/services/database.py`, `frontend/utils/validations.ts`, `frontend/utils/cache.ts`, `frontend/utils/server-cache.ts`, `docs/reference/data-dictionary.md` |
| `verification_commands` | `cd backend && pytest tests/unit/test_public_health_source_catalog.py tests/integration/test_public_health_hub_database.py`, `cd frontend && npm run test:unit -- app/api/resources/route.test.ts app/api/resources/alerts/route.test.ts app/api/resources/aqhi/route.test.ts` |
| `completion_artifacts` | schema migration, source metadata persistence, shared validation schemas, data dictionary update, passing route/migration tests |

Implementation expectations:

- create tables `public_data_sources`, `resource_locations`, and `public_health_alerts`
- preserve the frozen metadata-contract field names exactly
- add Zod schemas `ResourceKindSchema`, `ResourcesQuerySchema`, `ResourceAlertsQuerySchema`, and `ResourceAQHIQuerySchema`
- treat `frontend/utils/server-cache.ts` as the only cache layer for live proxy calls

### Package 2: Facilities

| Field | Value |
|---|---|
| `automation_class` | `agent_autonomous` |
| `signoff_owner` | `none` |
| `blocking_dependency` | `Foundation complete` |
| `implementation_entrypoints` | `backend/src/waittime/services/`, `backend/src/waittime/cli/`, `frontend/app/api/resources/route.ts`, `frontend/app/[locale]/resources/page.tsx`, `frontend/tests/pages/resources.test.tsx` |
| `verification_commands` | `cd backend && pytest tests/unit/test_resource_location_ingest.py tests/integration/test_public_health_hub_database.py -k facility`, `cd frontend && npm run test:unit -- app/api/resources/route.test.ts tests/pages/resources.test.tsx` |
| `completion_artifacts` | MOHSERLO ingest path, ODHF cross-check path, facility API coverage, directory-only caveat rendering, fixture-backed tests |

Implementation expectations:

- MOHSERLO is the only primary facility feed in Batch A
- ODHF is used for cross-checks and future expansion only
- facility records must never imply live availability or operational status

### Package 3: AED

| Field | Value |
|---|---|
| `automation_class` | `agent_with_human_signoff` |
| `signoff_owner` | `clinical_safety` |
| `blocking_dependency` | `Foundation complete and current legal review accepted` |
| `implementation_entrypoints` | `backend/src/waittime/services/`, `backend/src/waittime/cli/`, `frontend/app/api/resources/route.ts`, `frontend/app/[locale]/resources/page.tsx`, `frontend/tests/components/ResourceList.test.tsx` |
| `verification_commands` | `cd backend && pytest tests/unit/test_resource_location_ingest.py tests/integration/test_public_health_hub_database.py -k aed`, `cd frontend && npm run test:unit -- app/api/resources/route.test.ts tests/components/ResourceList.test.tsx tests/pages/resources.test.tsx` |
| `completion_artifacts` | OSM ingest path, provenance labeling, stale/incomplete warnings, suppressed-state behavior, screenshots or rendered evidence for sign-off |

Implementation expectations:

- every AED record in Batch A is treated as OSM-backed fallback data
- API and UI must expose crowdsourced/incomplete status
- human sign-off is required on final warning copy before merge or release

### Package 4: Alerts

| Field | Value |
|---|---|
| `automation_class` | `agent_autonomous` |
| `signoff_owner` | `none` |
| `blocking_dependency` | `Foundation complete` |
| `implementation_entrypoints` | `backend/src/waittime/services/alerts.py`, `backend/src/waittime/cli/`, `frontend/app/api/resources/alerts/route.ts`, `frontend/app/[locale]/resources/page.tsx`, `frontend/tests/components/AlertFeed.test.tsx` |
| `verification_commands` | `cd backend && pytest tests/unit/test_alert_feed_ingest.py tests/integration/test_public_health_hub_database.py -k alert`, `cd frontend && npm run test:unit -- app/api/resources/alerts/route.test.ts tests/components/AlertFeed.test.tsx tests/pages/resources.test.tsx` |
| `completion_artifacts` | recall ingest, normalized alert storage, DPD enrichment fallback, freshness behavior, passing route and UI tests |

Implementation expectations:

- only approved recalls/safety feeds are in scope
- DPD failures must degrade to alert-only rendering
- no drug shortages integration in Batch A

### Package 5: AQHI

| Field | Value |
|---|---|
| `automation_class` | `agent_autonomous` |
| `signoff_owner` | `none` |
| `blocking_dependency` | `Foundation complete` |
| `implementation_entrypoints` | `frontend/app/api/resources/aqhi/route.ts`, `frontend/utils/server-cache.ts`, `frontend/utils/cache.ts`, `frontend/app/[locale]/resources/page.tsx`, `frontend/tests/components/AQHICard.test.tsx` |
| `verification_commands` | `cd frontend && npm run test:unit -- app/api/resources/aqhi/route.test.ts tests/components/AQHICard.test.tsx tests/pages/resources.test.tsx` |
| `completion_artifacts` | AQHI proxy, cache policy, stale/suppress behavior, passing route and UI tests |

Implementation expectations:

- AQHI stays out of the database in Batch A
- route-level cache and UI freshness state must match the frozen freshness rules exactly

### Package 6: Navigation And Shell

| Field | Value |
|---|---|
| `automation_class` | `agent_autonomous` |
| `signoff_owner` | `none` |
| `blocking_dependency` | `Facilities, AED, Alerts, and AQHI APIs exist` |
| `implementation_entrypoints` | `frontend/components/Header.tsx`, `frontend/app/[locale]/resources/page.tsx`, `frontend/tests/pages/resources.test.tsx` |
| `verification_commands` | `cd frontend && npm run test:unit -- tests/pages/resources.test.tsx tests/components/ResourceList.test.tsx tests/components/AlertFeed.test.tsx tests/components/AQHICard.test.tsx`, `cd frontend && npm run type-check` |
| `completion_artifacts` | top-level navigation entry, complete resources page, integrated degraded states, page-level tests |

Implementation expectations:

- keep the route inside the current application shell
- do not redesign the homepage or create a separate product shell

---

## Source Autonomy Matrix

| Source | Automation class | Sign-off owner | Blocking dependency | Lane |
|---|---|---|---|---|
| MOHSERLO | `agent_autonomous` | `none` | `none` | `lane_a_agent` |
| ODHF | `agent_autonomous` | `none` | `none` | `lane_a_agent` |
| OpenStreetMap AED fallback | `agent_with_human_signoff` | `clinical_safety` | `legal review accepted` | `lane_b_agent_then_human_signoff` |
| Health Canada recalls dataset and RSS | `agent_autonomous` | `none` | `none` | `lane_a_agent` |
| DPD API enrichment | `agent_autonomous` | `none` | `none` | `lane_a_agent` |
| AQHI GeoMet | `agent_autonomous` | `none` | `none` | `lane_a_agent` |
| Ontario AED registry or partner feed | `human_only` | `legal_reuse` | `partnership or explicit permission` | `lane_c_human_first` |

---

## Stop Conditions For Agents

An implementation agent should stop and request human input if any of the following occur:

1. upstream terms, headers, or landing pages suggest that a previously approved source has materially changed
2. the implementation requires a new source not listed in the approved Batch A source set
3. the required caveat class cannot be expressed truthfully with the available data
4. the only workable path becomes scraping an HTML/dashboard surface that is not already approved
5. the intended UI would imply real-time certainty where freshness cannot be proven

---

## Minimum Handoff Packet For A New Agent

Another agent should be able to start Batch A implementation with only these documents:

1. `docs/planning/implementation/archived/public-health-data-hub-batch-a-plan.md`
2. `docs/planning/archive/public-health-data-hub-agent-execution-readiness.md`
3. `docs/planning/archive/public-health-data-hub-execution-order.md`
4. `docs/planning/public-health-data-hub-metadata-contract.md`
5. `docs/planning/public-health-data-hub-freshness-safety-rules.md`
6. `docs/research/public-health-data-hub-batch-a-legal-review.md`

If one of those documents needs to change during implementation, the planning artifact should be updated first rather than silently diverging in code.
