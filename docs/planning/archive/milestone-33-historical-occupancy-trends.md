# Wait Time Canada: Next Milestone Batch Implementation Plan

**Version:** 1.2.0-plan
**Milestone Sequence:** M33 → M34 → M35
**Date:** 2026-02-19
**Status:** Draft — Pending Review

---

## Current State Summary

### What's Done (as of v1.1.0 / M32)

All 32 prior milestones are complete and archived. The system is operationally mature:

| Layer | State |
|---|---|
| **Scrapers** | 4 active provinces (ON, QC, AB, BC), 380+ hospitals, structured retry/backoff, failure taxonomy, heartbeat metadata |
| **Backend services** | 14 services: DB, aggregation, anomaly detection, benchmarking, comparison, data quality, geocoding, alerts, methodology change, patterns, trends, quality diff, heartbeat, observability |
| **Database** | 9-table Neon PostgreSQL schema; 30-day raw data retention, permanent aggregates |
| **Frontend** | Next.js 14 App Router + TypeScript; 7 page routes (`/`, `/analytics`, `/data-quality`, `/methods`, `/status`, `/terms`, `/privacy`); 11 API routes |
| **Testing** | 350+ backend (pytest), 218+ frontend (Vitest); mypy strict, axe-core, mobile, visual regression, property-based |
| **CI/CD** | GitHub Actions for scraper cron (≈every 30min in cost-control mode), Lighthouse CI, release gate, heartbeat monitor, docs-CI |
| **Hosting** | **Netlify paused** (credit exhaustion). Target unpause: **March 9, 2026**. Scrapers remain live via GitHub Actions |
| **Equity layer** | Ontario-only real StatsCan CT overlays live; other provinces still scaffold |

### Key Unknowns & Assumptions

> [!IMPORTANT]
> - **Netlify/deployment.** Frontend is intentionally offline until ≥ March 9, 2026. Plans for M33–M35 are scoped to be frontend-testable locally (unit + vitest), with production validation deferred to the unpause window.
> - **GitHub Actions quota.** Still in cost-control mode (`*/30` scraper, deferred Playwright E2E). Milestones below avoid adding heavy GA workflows without clear ROI.
> - **StatsCan CT data for QC/AB/BC.** The Ontario equity layer was built from manually acquired 2021 Census CT GeoJSON. QC/AB/BC census tract files require the same manual download step (see `docs/planning/manual-tasks.md`). M34 cannot be fully automated until those files are present.
> - **Nova Scotia source.** NS Health Authority publishes wait times at `https://www.nshealth.ca/`. Page structure needs verification before scraper can be scoped. Treated as a research pre-condition for M35.
> - **Test suite baseline.** Recent maintenance noted 4 pre-existing test failures (M27 verification). These should be triaged as a pre-work item before adding milestone-specific tests.

---

## Proposed Milestone Batch

The roadmap's **"Later"** backlog lists these open items as the most valuable remaining work:

| Priority | Item | Mapped Milestone |
|---|---|---|
| P2 | Historical occupancy trends (QC stretcher data) | **M33** |
| P2 | Enhanced equity layer — multi-province rollout (QC/AB/BC) | **M34** |
| P2 | Additional provinces (Nova Scotia) | **M35** |
| P2 | Occupancy-based hospital recommendations | M36 (future) |
| P2 | Portfolio launch + stakeholder interview | Post-unpause (manual) |

---

## Milestone Definitions

---

### M33: Historical Occupancy Trends & Scraper Hardening

**Theme:** Scholar · Leader
**Goal:** Surface Quebec's stretcher occupancy data in the trend/analytics pipeline, close remaining test-suite gaps, and ensure the scraper cron is configured correctly for post-unpause.

**Why now:** Quebec occupancy data is being scraped (`STRETCHER_OCCUPANCY` metric family) and stored but is not yet fed through the aggregation pipeline or visualized as a trend. This is a high-signal Scholar feature — time-series occupancy gives the project a unique analytical dimension that raw wait times do not.

#### Deliverables

**Backend**

| File | Change |
|---|---|
| `backend/src/waittime/services/aggregation.py` | Extend aggregate pipeline to include `STRETCHER_OCCUPANCY` metric family — currently the aggregation logic may filter or skip this family. Add explicit coverage. |
| `backend/src/waittime/services/trends.py` | Expose occupancy trend data via the internal trends service (daily/weekly patterns for QC occupancy percentages). |
| `backend/tests/unit/services/test_aggregation.py` | Tests for STRETCHER_OCCUPANCY aggregate path. |
| `backend/tests/unit/services/test_trends.py` | Tests for occupancy trend queries. |

**Frontend**

| File | Change |
|---|---|
| `frontend/app/api/analytics/route.ts` (or sub-route) | Extend analytics API to return occupancy trend series when `metric_family=STRETCHER_OCCUPANCY` is requested. |
| `frontend/app/[locale]/analytics/page.tsx` | Add a collapsible "Occupancy Trends" panel showing 30-day/90-day Quebec hospital stretcher utilization charts alongside the existing wait time trend charts. |
| `frontend/tests/` | Vitest unit tests for new analytics panel state and occupancy data rendering. |

**Ops / CI**

| File | Change |
|---|---|
| `.github/workflows/scraper-cron.yml` | Document post-unpause target schedule (`*/20`); add an inline comment marking `*/30` as cost-control temporary so the intended cadence is not lost. |
| `docs/planning/roadmap.md` | Update "Now" queue on completion; note post-unpause scraper cron target. |

**ADR**

| File | Change |
|---|---|
| `docs/adr/0019-occupancy-trend-aggregation.md` | New ADR capturing the decision to include `STRETCHER_OCCUPANCY` in the aggregation pipeline and how to handle missing data days (forward-fill vs gap). |

#### Dependencies & Risks

- **Dependency:** Quebec scraper must be writing `STRETCHER_OCCUPANCY` measurements reliably (confirmed in M17/M18; verified via `check_heartbeat --verbose`).
- **Risk:** Sparse data — Quebec occupancy scrapes may have gaps (holidays, source downtime). The aggregation strategy must gracefully handle sparse input. Recommended: treat missing days as `NULL` rather than carry-forward.
- **Risk:** Chart complexity — adding a second metric family to the analytics page risks UI clutter. Mitigation: collapsible panel, initially collapsed.

#### Validation Plan

```bash
# Backend
python -m pytest backend/tests/unit/services/test_aggregation.py -v
python -m pytest backend/tests/unit/services/test_trends.py -v
python -m pytest backend/tests/ -q  # full suite, no regressions

# Frontend
cd frontend && npm run test:unit
```

---

### M34: Multi-Province Equity Layer Rollout (QC / AB / BC)

**Theme:** Health Advocate · Scholar
**Goal:** Extend the Ontario real-data equity overlay to Quebec, Alberta, and British Columbia using the same StatsCan 2021 Census CT methodology.

**Why now:** The Ontario equity layer (M28–M29) was hardened with academic rigor including quintile suppression, non-causal messaging, reproducibility documentation, and uncertainty annotations. QC/AB/BC still run on the scaffold. Completing multi-province rollout directly supports the "Health Advocate" CanMEDS narrative and is the most meaningful remaining content feature.

> [!IMPORTANT]
> **Blocking manual prerequisite:** StatsCan 2021 Census CT GeoJSON files for QC, AB, and BC must be downloaded manually before M34 backend work can proceed. See `docs/planning/manual-tasks.md → OPTIONAL: StatsCan Census Data Download`. The download takes 20–30 minutes but cannot be automated. This should happen *before* or *in parallel with* M34 Phase 1.

#### Deliverables

**Phase 1 — Data Acquisition & Processing (human + backend)**

| File | Change |
|---|---|
| `docs/planning/manual-tasks.md` | Mark StatsCan QC/AB/BC CT download as in-progress/complete and document file locations. |
| `backend/scripts/process_equity_data.py` (new or extend existing) | Re-use/extend ON processing script to generate QC/AB/BC equity layer GeoJSON with CT-level median income quintiles and LIM suppression. |
| `frontend/public/data/census/` | Add `equity-qc-2021.geojson`, `equity-ab-2021.geojson`, `equity-bc-2021.geojson` (processed output, ≤ 2 MB each with geometry simplification). |

**Phase 2 — API & Backend**

| File | Change |
|---|---|
| `frontend/app/api/equity-layer/route.ts` | Extend to return QC/AB/BC data based on `province` query param; preserve ON data path unchanged. |
| `backend/src/waittime/services/` | If equity linkage is computed server-side, extend linkage service to handle QC/AB/BC source IDs and hospital-CT matching logic. |
| `backend/tests/` | Unit tests for QC/AB/BC equity linkage (hospital → CT → income quintile). |

**Phase 3 — Frontend**

| File | Change |
|---|---|
| `frontend/app/[locale]/page.tsx` (map) | Enable equity layer toggle for QC/AB/BC hospitals (currently ON-only). |
| `frontend/components/EquityLayer*` | Update layer component to handle multi-province equity data and display province-scoped legends. |
| `frontend/tests/` | Vitest tests for QC/AB/BC equity layer rendering and multi-province legend. |

**Phase 4 — Documentation & ADR**

| File | Change |
|---|---|
| `docs/adr/0020-equity-layer-multi-province-rollout.md` | Document the decision to apply the ON CT methodology to QC/AB/BC, including data vintage, suppression rules, and province-specific caveats. |
| `docs/reference/data-dictionary.md` | Update equity layer section with multi-province fields. |

#### Dependencies & Risks

- **Dependency:** M28/M29 equity layer (ON) as template — complete ✅
- **Dependency:** StatsCan CT GeoJSON files (manual download — blocking)
- **Risk:** File size. Census CT geometry for large provinces (BC, AB) can be large. Aggressive simplification (`mapshaper` or equivalent) required to stay under static asset budget. Target: ≤ 2 MB per province after simplification.
- **Risk:** CT-to-hospital matching accuracy for QC. Quebec hospital IDs were seeded from MSSS; some CTs near provincial borders may not have matching hospitals. Graceful `null` rendering required.
- **Risk:** French-language CT labels for QC. Equity quintile legend copy may need French variants for QC, as the project supports bilingual routing.

#### Validation Plan

```bash
# Backend processing scripts
python backend/scripts/process_equity_data.py --province QC --dry-run
python backend/scripts/process_equity_data.py --province AB --dry-run
python backend/scripts/process_equity_data.py --province BC --dry-run

# Backend unit tests
python -m pytest backend/tests/ -q

# Frontend unit tests
cd frontend && npm run test:unit

# Manual: Load map locally and toggle equity layer for QC, AB, BC hospitals
# npm run dev → open http://localhost:3000 → enable equity overlay → pan to QC/AB/BC
```

---

### M35: Nova Scotia Scraper (5th Province)

**Theme:** Leader · Scholar
**Goal:** Add Nova Scotia as the fifth province, demonstrating systematic expansion capability and giving the project cross-Canada reach (Atlantic representation).

**Why now:** NS is feasible because NS Health Authority publishes structured wait time data online. Adding a 5th province with minimal overlap to existing work delivers strong "Leader" narrative value (multi-province systems architecture, regional data governance across 5 distinct health authorities). It also keeps the project progressing visibly after the equity layer completion.

> [!IMPORTANT]
> **Pre-condition:** Verify NS Health Authority data URL and structure before starting scraper development. The NS scraper approach (Playwright vs BeautifulSoup vs JSON) depends on the source page. This is a 30-minute research task that determines scope.

#### Deliverables

**Phase 1 — Research (pre-work)**

| File | Change |
|---|---|
| `docs/planning/manual-tasks.md` or `docs/data-sources/nova-scotia.md` | Document NS Health Authority source URL, methodology (what metric family, start/end events, statistic type), update frequency, and scraper approach. |
| `docs/adr/0021-nova-scotia-scraper.md` | ADR capturing NS methodology classification — particularly the `statistic_type` enum value (`POINT_ESTIMATE` vs `ROLLING_AVG`) and any divergence from ON/AB CIHI standard. |

**Phase 2 — Backend Scraper**

| File | Change |
|---|---|
| `backend/src/waittime/scrapers/nova_scotia.py` [NEW] | NS scraper inheriting `BaseScraper`, following the existing pattern (retry/backoff, payload hash, structured failure taxonomy, heartbeat metadata). |
| `backend/src/waittime/scrapers/__init__.py` | Register `nova_scotia` scraper in the registry. |
| `backend/tests/unit/scrapers/test_nova_scotia.py` [NEW] | Unit tests for NS scraper parser (≥ 80% coverage of scraper module). Mock the HTTP response using fixture data captured from real NS source. |
| `backend/tests/fixtures/nova_scotia_sample.html` (or `.json`) [NEW] | Fixture HTML/JSON snapshot for deterministic unit tests. |

**Phase 3 — Database Seed**

| File | Change |
|---|---|
| `backend/scripts/seed_hospitals.py` (or new migration) | Add NS source record to `sources` table and seed known NS hospitals (target: 5–10 hospitals covering Halifax and regional centres). |
| `docs/migrations/` | New migration SQL file for NS source/hospital seed. |

**Phase 4 — CI/CD**

| File | Change |
|---|---|
| `.github/workflows/scraper-cron.yml` | Add `nova_scotia` to the scraper cron job matrix. |
| `.github/workflows/scraper-ci.yml` | Add NS scraper to the CI test matrix. |

**Phase 5 — Frontend**

| File | Change |
|---|---|
| `frontend/app/api/hospitals/route.ts` | NS hospitals already returned if seeded (no change needed unless province filter logic is hardcoded). Verify. |
| Map markers | NS hospitals should auto-appear once seeded and visible. Confirm map bounds accommodate Atlantic Canada. |
| `frontend/app/[locale]/methods/page.tsx` | Add NS methodology row to the comparability matrix table. |

**Phase 6 — Docs**

| File | Change |
|---|---|
| `README.md` | Update province count and list to include Nova Scotia. |
| `docs/planning/roadmap.md` | Add M35 to completed milestones on closeout. |
| `CHANGELOG.md` | Log M35 under a new v1.3.0 entry. |

#### Dependencies & Risks

- **Dependency:** `BaseScraper` with retry/backoff pattern is well-established ✅
- **Dependency:** NS source URL research (pre-condition, 30 min)
- **Risk:** NS source may be JavaScript-rendered (like Ontario). If so, a Playwright scraper is needed; this adds setup overhead and GA minutes. Mitigation: assess up front and decide before coding.
- **Risk:** Small hospital count. NS is a small province; if only 2–3 hospitals report publicly, the admissions value of this province decreases. Confirm hospital count > 5 before investing M3+ of scraper work.
- **Risk:** Test fixture staleness. NS page structure may change post-launch. Follow the same fixture-versioning convention as ON/AB/BC.

#### Validation Plan

```bash
# Dry-run (local only, no DB writes)
python -m waittime scrape nova_scotia --dry-run

# Unit tests
python -m pytest backend/tests/unit/scrapers/test_nova_scotia.py -v
python -m pytest backend/tests/ -q   # full suite, no regressions

# Frontend
cd frontend && npm run test:unit

# Integration (manual): trigger scraper, verify heartbeat row written
python -m waittime scrape nova_scotia
python -m waittime check_heartbeat --verbose
```

---

## High-Level Timeline & Milestones

> All dates assume frontend hosting remains offline and work continues local. Post-unpause production smoke is flagged separately.

| Period | Milestone | Key Deliverable |
|---|---|---|
| **Week 1–2** | **M33: Historical Occupancy Trends** | QC occupancy in aggregation pipeline, analytics trend panel, ADR-0019 |
| **Week 2–3** | **M34 Phase 1** | StatsCan data download (manual), QC/AB/BC equity processing scripts |
| **Week 3–5** | **M34 Phases 2–4** | Multi-province equity API + frontend + ADR-0020 |
| **Week 5–6** | **M35 Phase 1** | NS source research, ADR-0021, methodology doc |
| **Week 6–8** | **M35 Phases 2–6** | NS scraper + seed + CI + frontend + docs |
| **Week 9 (≥ March 9)** | **Post-unpause ops** | Resume Netlify, move to `*/20` scraper cron, run production smoke, do LinkedIn launch |

### Version Tags

| Version | Contents |
|---|---|
| `v1.2.0` | M33 (occupancy trends) |
| `v1.2.1` | M34 Phase 1 (equity data processing) |
| `v1.3.0` | M34 complete (multi-province equity UI) |
| `v1.4.0` | M35 (Nova Scotia) |

---

## Rollout & Rollback Approach

### Rollout
- Each milestone is independently deployable; no breaking schema changes are expected.
- M33 and M34 Phase 2 may require a database migration if equity layer linkage is moved server-side. Migrations follow the existing convention in `docs/development/database-migrations.md`.
- New frontend pages/panels are additive (no removal of existing routes).
- Release commits follow the `[release]` gate convention so Netlify's ignore script only deploys intentionally.

### Rollback
- **Backend:** All new services are additive. Rolling back is done by reverting the commit; no destructive DB changes are planned. If a migration is needed, a matching down-migration file will be written alongside the up-migration.
- **Frontend:** New analytics panels and equity layer province extensions are feature-flag-friendly by nature (data-conditional rendering — if data is absent, the panel is hidden). No existing routes are modified destructively.
- **Scraper (M35):** NS scraper is added to the cron matrix. If it fails repeatedly, removing it from `scraper-cron.yml` matrix is a 2-line rollback with no DB side effects (nil heartbeat entries are inert).

---

## Pre-Work Items (Before M33 Begins)

1. **Triage the 4 pre-existing backend test failures** noted in M27 verification (`399/403 passed`). Identify if they are legitimate bugs, fixture issues, or stale tests. Resolve or explicitly mark as known-skipped.
2. **Confirm QC occupancy measurement frequency** — verify the aggregation service receives at least a few weeks of `STRETCHER_OCCUPANCY` rows before building the trend view. Run: `SELECT COUNT(*) FROM measurements WHERE metric_family='STRETCHER_OCCUPANCY' GROUP BY DATE(timestamp_utc) ORDER BY 1 DESC LIMIT 14;`
3. **Research NS Health Authority source URL** — 30-minute browser task. Needed before M35 scope can be finalized.

---

## Strategic Alignment

| CanMEDS | M33 | M34 | M35 |
|---|---|---|---|
| **Scholar** | Occupancy time-series, ADR-0019 | Multi-province equity rigor, ADR-0020 | NS methodology classification, ADR-0021 |
| **Health Advocate** | — | 3× equity layer coverage | Atlantic Canada access data |
| **Leader** | — | — | 5-province systems architecture |
| **Professional** | Non-causal messaging for occupancy trends | Suppression provenance + uncertainty (extended) | Province-aware telehealth (NS) |

---

## Open Questions (Non-Blocking)

These do not block execution but are worth deciding:

1. **M33 chart type:** Line chart vs heatmap for occupancy trends? A 7-day heatmap (days × hours) is more clinically intuitive for occupancy but harder to implement. A simple time-series line chart is faster and still valid.
2. **M34 geometry budget:** Should equity layer GeoJSON be served from the Next.js static public folder (current pattern for ON) or from the API route to enable server-side simplification on the fly? The static approach is simpler but may be large for QC.
3. **M35 scraper approach:** Playwright (JS-rendered, heavier) vs BeautifulSoup (static HTML, lighter)? Depends on NS source — let research determine this.
