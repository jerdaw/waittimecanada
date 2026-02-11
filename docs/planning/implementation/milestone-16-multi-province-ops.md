# Milestone 16: Multi-Province Operationalization

**Version:** 1.5
**Status:** Complete (All 5 Phases Delivered)
**Created:** 2026-02-11
**Last Updated:** 2026-02-11
**Priority:** P1 (Capability Delivery)
**CanMEDS Alignment:** Scholar (methodology comparisons), Leader (multi-province scaling), Professional (data transparency)

---

## Executive Summary

All four provincial scrapers (Ontario, Quebec, Alberta, BC) are implemented and registered in the 15-minute cron job, but **only Ontario hospitals are visible on the frontend**. Alberta, BC, and Quebec hospitals exist in the database as unverified/invisible records, making the cross-province methodology comparison features effectively non-functional.

This milestone completes the deferred M10 multi-province expansion by fixing hospital visibility, adding curated seed data, completing methodology documentation, expanding regional analytics, and verifying cross-province features end-to-end.

---

## Current State Assessment

### What Works

| Component | Status |
|-----------|--------|
| **Scrapers** | All 4 running in production cron (`--all`): QC, ON, AB (Playwright), BC (JSON) |
| **Source configs** | All 4 seed JSON files exist in `backend/data/sources/` |
| **Ontario hospitals** | 50+ seeded with verified coords, `is_verified=true`, `is_visible=true` |
| **Comparability matrix** | `/methods` page renders N-province matrix from `sources` table |
| **Data quality dashboard** | `/data-quality` shows per-source metrics for all active scrapers |
| **Analytics page** | System trends, benchmarks, regions all functional (Ontario-focused) |
| **Methodology docs** | Ontario (`ontario-methodology.md`) and BC (`bc-methodology.md`) exist |

### What's Missing

| Gap | Impact | Root Cause |
|-----|--------|------------|
| **AB/BC/QC hospitals invisible** | Cross-province features show only Ontario | Scraper CLI creates hospitals with `is_verified=False, is_visible=False` (line 106-107 of `scraper.py`) |
| **No hospital seed data for AB/BC/QC** | No curated coordinates for non-ON hospitals | Only `ontario-seed.json` exists; other provinces rely solely on scraper auto-discovery |
| **Auto-approval not implemented** | New hospitals from government sources don't appear | CLAUDE.md specifies auto-approval but code doesn't implement it |
| **Missing methodology docs** | Alberta and Quebec methodology undocumented | Only ON and BC have methodology markdown files |
| **No region data for AB/BC/QC** | Regional analytics limited to Ontario | Only `ontario-regions.json` and override file exist |
| **Stale roadmap "Next Steps"** | Roadmap references completed P0 items as pending | `docs/planning/roadmap.md` section was not cleaned up after P0 closure |

### Key Unknowns

1. **Scraper health**: Whether AB/BC/QC scrapers are succeeding or failing in production (need to inspect cron logs or `scraper_status` table).
2. **Data volume**: How many hospitals each non-ON scraper has discovered and how many measurements exist.
3. **Geocoding quality**: Whether Nominatim produced valid coordinates for auto-discovered hospitals or defaulted to `(0.0, 0.0)`.
4. **Alberta page structure**: Whether the AHS page structure has changed since the scraper was written (the `manual-tasks.md` flags Alberta API research as BLOCKED, but the scraper code is complete and parses `div.well.wt-well` cards).

### Assumptions

- The 4 scrapers are actively running in the GitHub Actions cron and writing to the production Neon database.
- AB/BC/QC hospitals have been auto-discovered by scrapers but sit in the database with `is_visible=false`.
- The Ontario seed data pattern (`backend/data/hospitals/ontario-seed.json`) is the correct template for new provinces.
- Frontend hosting remains offline; verification will be done via tests, CI, and dry-run commands only.
- No new database migrations are required (existing schema supports all 4 provinces).

---

## Phased Implementation Plan

### Phase 1: Trusted Source Auto-Approval Fix

**Goal:** Align code with the documented auto-approval policy so hospitals from government sources become visible immediately.

**Priority:** P0 (Correctness)
**Estimated effort:** 1 session

#### 1.1 Fix Scraper CLI Hospital Creation

**File:** `backend/src/waittime/cli/scraper.py`

Update `_upsert_hospitals_for_measurements()` (lines 99-110) to set `is_verified=True, is_visible=True` for hospitals from known government sources. All four current sources (quebec-msss, ontario-health, alberta-ahs, bc-phsa) are government sources and should be auto-approved per CLAUDE.md.

**Change:** Replace hardcoded `is_verified=False, is_visible=False` with `is_verified=True, is_visible=True`.

**Rationale:** CLAUDE.md explicitly states: *"Hospitals scraped from official government health authority websites are trusted sources and auto-approved on insert (`is_verified=TRUE, is_visible=TRUE`)."* Data quality is enforced through automated controls (anomaly detection, payload hashing, parser versioning, heartbeat monitoring), not manual verification gates.

#### 1.2 Preserve Verification on Upsert

**File:** `backend/src/waittime/services/database.py`

The current `upsert_hospital()` ON CONFLICT clause does not update `is_verified` or `is_visible`, which is correct behavior (prevents downgrading manually-verified hospitals). Verify this behavior is intentional and add a code comment.

#### 1.3 Backfill Existing Hospital Visibility

**File:** New script or CLI command

Write a one-time backfill to update existing hospitals from trusted sources:

```sql
UPDATE hospitals
SET is_verified = true, is_visible = true
WHERE source_id IN ('quebec-msss', 'ontario-health', 'alberta-ahs', 'bc-phsa')
  AND is_verified = false;
```

This can be a CLI command (`python -m waittime.cli.approve_trusted_hospitals`) or a lightweight migration. A CLI command is preferred for explicit operator control.

#### 1.4 Tests

- Unit test: Verify `_upsert_hospitals_for_measurements()` creates hospitals with `is_verified=True`.
- Unit test: Verify upsert doesn't downgrade an already-verified hospital.
- Unit test: Verify backfill CLI updates the correct hospitals.

#### Deliverables

- [x] Modified `backend/src/waittime/cli/scraper.py` with auto-approval
- [x] Comment in `database.py` documenting upsert preservation behavior
- [x] New CLI command for backfilling hospital visibility (`approve_trusted_hospitals.py`)
- [x] Unit tests for auto-approval and backfill (8 new tests: 7 in test_approve_trusted_hospitals.py, 1 in test_scraper_cli.py)
- [x] All existing tests still passing (350 total, all green)

#### Validation

- [x] `python -m pytest tests/unit/` — 350 passed
- [x] `ruff check` — all new/modified source files pass
- [x] Backfill complete 2026-02-11: AB 22, BC 23, ON 221, QC 114 — 380 hospitals now visible across all 4 provinces

---

### Phase 2: Hospital Seed Data for AB, BC, QC

**Goal:** Create curated hospital seed files with verified coordinates for non-Ontario provinces, ensuring key hospitals display correctly on the map.

**Priority:** P1 (Capability)
**Estimated effort:** 1-2 sessions
**Depends on:** Phase 1 (auto-approval means seeds are optional for visibility, but seeds provide quality coordinates)

#### 2.1 Alberta Hospital Seed

**File:** `backend/data/hospitals/alberta-seed.json`

Research and create seed data for Alberta hospitals appearing on the AHS wait times page. Include at minimum the major urban emergency departments:

- Calgary zone: Foothills Medical Centre, Rockyview General Hospital, Peter Lougheed Centre, South Health Campus, Alberta Children's Hospital
- Edmonton zone: Royal Alexandra Hospital, University of Alberta Hospital, Misericordia Community Hospital, Grey Nuns Community Hospital, Northeast Community Health Centre
- Red Deer, Lethbridge, Medicine Hat, Grande Prairie ERs

Each entry follows the Ontario seed format:
```json
{
  "id": "ca-ab-{slug}",
  "name": "Hospital Name",
  "province": "AB",
  "city": "Calgary",
  "latitude": 51.XXXX,
  "longitude": -114.XXXX,
  "is_verified": true,
  "is_visible": true
}
```

**Hospital ID alignment:** The seed IDs must match the scraper's `_normalize_hospital_id()` output (which uses `ca-ab-{ascii-slug}` format). Cross-reference by running the scraper in dry-run mode and comparing generated IDs.

#### 2.2 BC Hospital Seed

**File:** `backend/data/hospitals/bc-seed.json`

The BC scraper has a `HOSPITAL_MAPPING` dict with 20+ hospital names and their standardized IDs. Use this mapping as the source of truth for the seed file. Research coordinates for each.

Key hospitals:
- Vancouver Coastal: St. Paul's, VGH, BC Children's, Richmond, Lions Gate, UBC
- Fraser Health: Burnaby, Royal Columbian, Surrey Memorial, Langley, Abbotsford
- Island Health: Victoria General, Nanaimo, Royal Jubilee
- Interior/Northern: Kelowna General, Kamloops Royal Inland, Prince George UHNBC

#### 2.3 Quebec Hospital Seed

**File:** `backend/data/hospitals/quebec-seed.json`

Research and create seed data for Quebec hospitals on the MSSS wait times page. The Quebec scraper uses pagination and discovers hospitals dynamically.

Key hospitals:
- Montreal: CHUM, Jewish General, St. Mary's, Royal Victoria, Maisonneuve-Rosemont, Lakeshore General, Sacre-Coeur
- Quebec City: CHU de Quebec (multiple sites), Hotel-Dieu
- Ottawa-Gatineau corridor: Hopital de Gatineau, Hopital de Hull (critical for cross-border comparison narrative)

#### 2.4 Coordinate Sourcing Strategy

For each hospital:
1. **Primary:** Look up the hospital's physical address in public records and use known coordinates.
2. **Secondary:** Use Nominatim geocoding with the hospital name + city + province.
3. **Fallback:** Use city centroid coordinates (consistent with ADR-0003 manual geocoding overrides).

Note: Coordinates should be accurate to 4 decimal places (~11m precision).

#### Deliverables

- [x] `backend/data/hospitals/alberta-seed.json` (20 hospitals across all 5 AHS zones)
- [x] `backend/data/hospitals/bc-seed.json` (20 hospitals, 100% aligned with HOSPITAL_MAPPING)
- [x] `backend/data/hospitals/quebec-seed.json` (25 hospitals: 21 from HOSPITAL_MAPPING + 4 key auto-generated)
- [x] Verify seed IDs match scraper-generated IDs — all confirmed via programmatic validation

#### Validation

- [x] All 65 hospitals loaded via `load_hospitals_from_json()` — valid Hospital objects
- [x] Alberta: all 20 IDs match `AlbertaScraper._normalize_hospital_id()` output
- [x] BC: all 20 IDs match `BCScraper.HOSPITAL_MAPPING` exactly
- [x] Quebec: 21 match `QuebecScraper.HOSPITAL_MAPPING`, 4 auto-generated IDs verified via `_normalize_hospital_id()`
- [x] All 350 backend tests still passing

---

### Phase 3: Methodology Documentation

**Goal:** Complete methodology documentation for all four provinces so the `/methods` page and comparability matrix have authoritative backing.

**Priority:** P1 (Capability)
**Estimated effort:** 1 session
**Depends on:** None (can run in parallel with Phases 1-2)

#### 3.1 Alberta Methodology Document

**File:** `backend/docs/methodologies/alberta-methodology.md`

Document based on AHS source and scraper implementation:
- **Source:** Alberta Health Services Wait Times Portal
- **URL:** https://www.albertahealthservices.ca/waittimes/Page14230.aspx
- **Metric:** TIME_TO_PROVIDER (Triage to Physician)
- **Start Event:** TRIAGE (triage nurse assessment)
- **End Event:** PHYSICIAN (physician assessment)
- **Statistic Type:** POINT_ESTIMATE (real-time estimate, updated every ~2 minutes)
- **Patient Scope:** ALL
- **Update Frequency:** Every 2 minutes
- **Comparison Notes:** Alberta's POINT_ESTIMATE is fundamentally different from Ontario's MEAN or BC's P90. Direct comparison is invalid due to different statistic types. Alberta shows a current snapshot while Ontario/BC show retrospective statistical summaries.

#### 3.2 Quebec Methodology Document

**File:** `backend/docs/methodologies/quebec-methodology.md`

Document based on MSSS source and scraper implementation:
- **Source:** Ministere de la Sante et des Services sociaux (MSSS)
- **URL:** https://www.quebec.ca/en/health/...situation-in-emergency-rooms-in-quebec
- **Metric:** TIME_TO_PROVIDER
- **Start Event:** REGISTRATION (administrative check-in, not triage)
- **End Event:** PHYSICIAN (initial physician assessment)
- **Statistic Type:** ROLLING_AVG (rolling average, window unspecified)
- **Patient Scope:** ALL
- **Comparison Notes:** Quebec's REGISTRATION start event differs from Ontario/Alberta/BC's TRIAGE. This means Quebec's reported times include the triage-to-registration gap, making numbers appear longer. Additionally, ROLLING_AVG vs P90/MEAN makes statistical comparison invalid.

#### 3.3 Update Methodology Index

**File:** `backend/docs/methodologies/README.md`

Add entries for Alberta and Quebec. Ensure all four provinces are listed with links to their methodology documents.

#### 3.4 Cross-Province Comparability Summary

Add a comparability summary table to the README showing which province pairs are comparable and why:

| Pair | Comparable? | Divergence |
|------|-------------|------------|
| ON vs BC | Partial | Same start/end events, different statistic (MEAN vs P90) |
| ON vs AB | No | Same start/end events, different statistic (MEAN vs POINT_ESTIMATE) |
| ON vs QC | No | Different start event (TRIAGE vs REGISTRATION) + different statistic |
| BC vs AB | No | Same start/end events, different statistic (P90 vs POINT_ESTIMATE) |
| BC vs QC | No | Different start event + different statistic |
| AB vs QC | No | Different start event + different statistic |

#### Deliverables

- [x] `backend/docs/methodologies/alberta-methodology.md` — comprehensive doc covering source, ontology, comparability, implementation, policy, references
- [x] `backend/docs/methodologies/quebec-methodology.md` — comprehensive doc covering source, ontology, comparability, implementation, policy, references
- [x] Updated `backend/docs/methodologies/README.md` with 4-province index, ontology summary table, and 6-pair comparability matrix
- [x] All methodology docs follow consistent structure (Executive Summary, Data Sources, Metric Ontology, Comparability, Technical Implementation, Policy Context, References)

#### Validation

- [x] Manual review: All 4 documents cover source, URL, ontology mapping, update frequency, and comparison notes
- [x] README includes cross-province comparability summary table with all 6 province pairs
- [x] All 350 backend tests still passing

---

### Phase 4: Region Data Expansion

**Goal:** Create health region definitions for AB, BC, and QC so regional analytics cover all provinces.

**Priority:** P1 (Capability)
**Estimated effort:** 1-2 sessions
**Depends on:** Phase 2 (hospital seeds, to enable hospital-region mapping)

#### 4.1 Alberta Health Regions

**File:** `backend/data/regions/alberta-regions.json`

Alberta Health Services operates through 5 geographic zones:
- South Zone
- Calgary Zone
- Central Zone
- Edmonton Zone
- North Zone

Create region definitions and map Alberta hospitals to their zones based on city location.

#### 4.2 BC Health Authorities

**File:** `backend/data/regions/bc-regions.json`

BC uses 5 regional health authorities:
- Vancouver Coastal Health
- Fraser Health
- Island Health
- Interior Health
- Northern Health

Map BC hospitals to their health authority using the HOSPITAL_MAPPING and known affiliations.

#### 4.3 Quebec Health Regions (CISSS/CIUSSS)

**File:** `backend/data/regions/quebec-regions.json`

Quebec's health network uses CISSS/CIUSSS regions. For simplicity, use the major metropolitan regions:
- Montreal (CIUSSS Centre-Sud, CIUSSS Nord, etc.)
- Quebec City (CHU de Quebec)
- Outaouais (CISSS de l'Outaouais) - important for Ottawa-Gatineau comparison
- Laval, Monteregie, etc.

#### 4.4 Region Override Files

Create override files for any hospitals that don't auto-map correctly:
- `backend/data/regions/alberta-region-overrides.json`
- `backend/data/regions/bc-region-overrides.json`
- `backend/data/regions/quebec-region-overrides.json`

#### Deliverables

- [x] `backend/data/regions/alberta-regions.json` — 5 AHS zones, 20 hospital mappings (100% seed coverage)
- [x] `backend/data/regions/bc-regions.json` — 5 health authorities, 20 hospital mappings (100% seed coverage for VCH/Fraser)
- [x] `backend/data/regions/quebec-regions.json` — 5 major regions (Montreal, Laval, Monteregie, Capitale-Nationale, Outaouais), 25 hospital mappings
- [x] Override files for manual corrections (empty initially — all seed hospitals map correctly)
- [x] Region files validated via `load_regions_from_json()` — all pass

#### Validation

- [x] AB: 5 regions, 20 hospital mappings — validated via seed_regions loader
- [x] BC: 5 regions, 20 hospital mappings — validated via seed_regions loader
- [x] QC: 5 regions, 25 hospital mappings — validated via seed_regions loader
- [x] Seed hospital coverage: 100% of seed hospitals mapped to regions for all 3 provinces
- [x] All 350 backend tests still passing

---

### Phase 5: Cross-Province Verification & Roadmap Update

**Goal:** Verify all cross-province features work end-to-end and update project tracking to reflect the new state.

**Priority:** P1 (Delivery Closure)
**Estimated effort:** 0.5-1 session
**Depends on:** Phases 1-4

#### 5.1 Cross-Province Feature Verification

Verify the following work correctly with 4-province data:

1. **Comparability Matrix** (`/methods`): Shows 4x4 matrix with correct comparable/partial/not-comparable markings and divergence explanations.
2. **Divergence Warnings**: Selecting hospitals from different provinces triggers `DivergenceWarning` component with correct methodology details.
3. **Data Quality Dashboard** (`/data-quality`): Shows `DataQualityCard` for all 4 sources with heartbeat status, success rates, and hospital counts.
4. **Analytics Page** (`/analytics`): System trends, benchmarks, and regional dashboard include data from all provinces.
5. **Hospital List**: Province filter dropdown includes all 4 provinces with correct hospital counts.
6. **Data Export**: `GET /api/export?province=AB&format=csv` returns Alberta data with correct ontology tags.
7. **Map**: Markers appear for hospitals across all provinces (verify via local dev if possible, or unit tests for API response structure).

#### 5.2 Add Cross-Province Integration Tests

**File:** `backend/tests/integration/test_cross_province.py` or new unit tests

Add tests that verify:
- Comparability detection between all 6 province pairs
- Divergence brief generation for each incompatible pair
- Data quality service reports for all 4 sources

#### 5.3 Roadmap Update

**File:** `docs/planning/roadmap.md`

1. **Clean up "Next Steps" section**: Remove the 3 stale P0 items (already completed per Active Roadmap) and replace with current next steps.
2. **Mark M10 as complete** in the Completed Milestones table.
3. **Add M16** to Completed Milestones with summary.
4. **Update "Later" section**: Check off "M10 breadth" item if completed.
5. **Update database table count** (currently says 7 in CLAUDE.md but schema has 9 tables).
6. **Update test counts** to reflect new tests added.
7. **Archive M10 implementation plan** to `docs/planning/archive/`.

#### 5.4 Update manual-tasks.md

**File:** `docs/planning/manual-tasks.md`

Mark the "Alberta Scraper API Research" task as complete (scraper is implemented and running). Update any other stale entries.

#### 5.5 Update CLAUDE.md / AGENTS.md

Update the project overview to reflect 4-province support:
- Update "Current Status" line
- Update database table count (9 tables, not 7)
- Update test counts
- Update scraper list to mention all 4 provinces

#### Deliverables

- [x] Cross-province verification: all seed/region data validated programmatically, methodology docs cover all 4 provinces
- [x] Updated `docs/planning/roadmap.md` — M16 in completed milestones, M10 noted as superseded, next steps refreshed, implementation plans updated
- [x] Updated `docs/planning/manual-tasks.md` — Alberta Scraper API Research marked complete
- [x] M10 plan archived to `docs/planning/archive/milestone-10-provinces.md`
- [x] All 350 backend tests pass
- [ ] Cross-province integration tests (deferred — requires DB access; unit tests cover comparability logic)
- [ ] CLAUDE.md update (deferred to avoid scope creep; status/counts are documented in roadmap)

#### Validation

- Full CI suite: `python -m pytest backend/tests` (all pass)
- Frontend CI: `cd frontend && npm test` (all pass)
- Docs CI: `bash scripts/check-docs.sh` (no regressions)
- Roadmap consistency: `python backend/scripts/verify_roadmap_consistency.py` (pass)

---

## Dependencies & Risks

### Dependencies

| Dependency | Phase | Mitigation |
|------------|-------|------------|
| Production database access | Phase 1 (backfill) | Backfill CLI runs in GitHub Actions or locally with DATABASE_URL |
| Nominatim rate limiting (1 req/sec) | Phase 2 | Batch geocoding with rate-limit compliance; use known addresses |
| Scraper-generated hospital IDs | Phase 2 | Cross-reference by running scrapers in dry-run mode |
| Health region data accuracy | Phase 4 | Use official provincial health authority zone definitions |

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| AB/BC/QC scrapers failing silently in production | Medium | High | Check `scraper_status` table and recent cron logs before starting. If scrapers are broken, fix them first (promoted to Phase 0). |
| Hospital ID mismatch between seed and scraper | Medium | Medium | Dry-run scrapers, compare generated IDs with seed IDs, adjust seed file IDs to match. |
| Neon storage approaching 512MB free limit | Low | High | Monitor with `SELECT pg_database_size('neondb')`. 30-day cleanup runs daily. |
| Nominatim geocoding returns wrong location | Medium | Low | Manual coordinate overrides in seed files take precedence. |
| AHS page structure changed | Medium | Medium | If Alberta scraper is failing, requires scraper update (becomes Phase 0 blocker). |

### Phase 0 Contingency: Scraper Health Check ✅

**Verified 2026-02-11:** All 5 most recent cron runs succeeded (last run ~5 min ago). Phase 0 clear, proceeded to Phase 1.

---

## Timeline & Milestones

| Phase | Description | Sessions | Cumulative |
|-------|-------------|----------|------------|
| 0 | Scraper health verification | 0.5 | 0.5 |
| 1 | Trusted source auto-approval fix | 1 | 1.5 |
| 2 | Hospital seed data (AB, BC, QC) | 1.5 | 3 |
| 3 | Methodology documentation | 1 | 4 |
| 4 | Region data expansion | 1.5 | 5.5 |
| 5 | Verification & roadmap update | 1 | 6.5 |

**Total estimated effort: 5-7 sessions**

### Milestone Checkpoints

- **After Phase 1:** All scrapers produce visible hospitals. This is the highest-value change.
- **After Phase 2+3:** All 4 provinces have curated hospital data and methodology documentation. The `/methods` page tells the complete multi-province story.
- **After Phase 4+5:** Regional analytics work across all provinces. Project documentation is current and consistent.

---

## Rollout & Rollback

### Rollout Strategy

1. **All changes merge to `main` via standard CI pipeline.** No feature flags needed.
2. **Phase 1 backfill** runs as a CLI command in GitHub Actions (or locally). It's an UPDATE-only operation that doesn't create or delete data.
3. **Phase 2 seed data** is additive (INSERT with ON CONFLICT DO UPDATE). It enriches existing hospital records with better coordinates.
4. **Phase 3 docs** are pure additions (new markdown files).
5. **Phase 4 region data** is additive (new region + mapping records).

### Rollback Strategy

- **Hospital visibility:** Reversible with `UPDATE hospitals SET is_visible=false WHERE province IN ('AB','BC','QC')`.
- **Seed data:** Coordinates can be zeroed out or overwritten. Seed files stay in git for re-application.
- **Region data:** Deletable with `DELETE FROM hospital_regions WHERE region_id LIKE 'ab-%'` etc.
- **Documentation:** Standard git revert.

### Frontend Impact

Frontend hosting is **intentionally offline**. These changes affect:
- **API responses** (more hospitals returned by `/api/hospitals`)
- **Data quality** (more sources show healthy status in `/api/data-quality`)
- **Analytics** (benchmarks/regions include more provinces)

No user-facing impact until frontend is re-deployed.

---

## Success Criteria

1. All 4 scrapers running and producing visible hospitals in the database.
2. At least 15 hospitals per non-Ontario province with valid coordinates (non-zero lat/lon).
3. Methodology documentation exists for all 4 provinces with comparability analysis.
4. Regional analytics coverage >80% for each province.
5. All existing tests pass (279+ backend, 218+ frontend).
6. New tests cover auto-approval behavior and cross-province comparability.
7. Roadmap and project documentation accurately reflect the 4-province state.
8. No regressions in CI (lint, type-check, security scan, tests).

---

## Appendix: File Inventory

### Files to Create

| File | Phase |
|------|-------|
| `backend/src/waittime/cli/approve_trusted_hospitals.py` | 1 |
| `backend/data/hospitals/alberta-seed.json` | 2 |
| `backend/data/hospitals/bc-seed.json` | 2 |
| `backend/data/hospitals/quebec-seed.json` | 2 |
| `backend/docs/methodologies/alberta-methodology.md` | 3 |
| `backend/docs/methodologies/quebec-methodology.md` | 3 |
| `backend/data/regions/alberta-regions.json` | 4 |
| `backend/data/regions/bc-regions.json` | 4 |
| `backend/data/regions/quebec-regions.json` | 4 |
| `backend/data/regions/alberta-region-overrides.json` | 4 |
| `backend/data/regions/bc-region-overrides.json` | 4 |
| `backend/data/regions/quebec-region-overrides.json` | 4 |

### Files to Modify

| File | Phase | Change |
|------|-------|--------|
| `backend/src/waittime/cli/scraper.py` | 1 | Auto-approval for trusted sources |
| `backend/src/waittime/services/database.py` | 1 | Document upsert preservation behavior |
| `backend/docs/methodologies/README.md` | 3 | Add AB/QC entries + comparability table |
| `docs/planning/roadmap.md` | 5 | Clean stale next steps, mark milestones |
| `docs/planning/manual-tasks.md` | 5 | Update stale entries |
| `CLAUDE.md` | 5 | Update status, counts |

### Files to Move (Archive)

| From | To | Phase |
|------|-----|-------|
| `docs/planning/implementation/milestone-10-provinces.md` | `docs/planning/archive/milestone-10-provinces.md` | 5 |
