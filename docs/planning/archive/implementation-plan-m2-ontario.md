# Implementation Plan: Milestone 2 - Ontario End-to-End

**Document Version:** 1.0.0
**Date:** 2026-01-30
**Status:** Implementation Complete ✅ - Milestone Delivered
**Owner:** Jeremy Dawson
**Milestone:** M2 - Ontario End-to-End (First Provincial Vertical Slice)

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-01-30 | Jeremy Dawson | Initial implementation plan |

---

## Executive Summary

This implementation plan details the complete end-to-end delivery of the **first provincial data pipeline** for WaitTime Canada, focusing exclusively on **Ontario**. This milestone represents our first complete vertical slice through the entire system architecture: data acquisition → storage → presentation.

**Strategic Importance:**
- Validates core architectural assumptions (metric ontology, database schema)
- Establishes repeatable patterns for future provincial expansions
- Delivers first shippable increment with real user value
- De-risks technical unknowns before scaling to other provinces

**Expected Duration:** 2-3 weeks (depending on data source availability)

**Success Definition:** A user can visit a webpage and see real-time Ontario hospital wait times on an interactive map, with clear methodology labeling.

---

## Goals and Objectives

### Primary Goals

1. **Validate Data Availability**: Confirm Ontario health authority publishes accessible ED wait time data
2. **Prove Scraper Architecture**: Demonstrate BaseScraper pattern works with real-world HTML/API
3. **Establish Data Pipeline**: End-to-end flow from scraper → Neon PostgreSQL → Next.js frontend
4. **Create Frontend Foundation**: Minimal viable map interface that can scale to other provinces

### Secondary Goals

1. Map 10+ Ontario hospitals (Ottawa + Toronto focus)
2. Achieve >80% test coverage on Ontario scraper
3. Document Ontario-specific implementation quirks
4. Establish local development workflow

### Non-Goals (Explicitly Out of Scope)

- ❌ Multi-province support (Quebec remains dormant until Ontario stable)
- ❌ User accounts or authentication
- ❌ Mobile app or mobile optimization
- ❌ Historical trends or data visualization
- ❌ Production deployment (Milestone 3)
- ❌ Admin verification UI (Milestone 5)

---

## Prerequisites and Dependencies

### Technical Prerequisites

**Completed (Milestone 1):**
- [x] Neon PostgreSQL database with schema
- [x] Python backend package structure (`backend/src/waittime/`)
- [x] BaseScraper abstract class
- [x] DatabaseService with psycopg2
- [x] Core models with Pydantic validation
- [x] Unit test framework (pytest)
- [x] CLI tool for running scrapers

**Required Before Starting:**
- [x] Git repository initialized and pushed to GitHub
- [x] DATABASE_URL configured in `.env.local`
- [x] All Milestone 1 tests passing (24/24 ✓)

### Knowledge Prerequisites

**Research Required (Phase 0):**
- Ontario health authority data source URL
- Ontario wait time methodology (start_event, end_event, statistic_type)
- HTML/API structure of Ontario portal
- List of target hospitals with official names

---

## Architecture and Design Decisions

### Data Flow Architecture

```
┌─────────────────┐
│ Ontario Health  │
│ Portal (HTML)   │
└────────┬────────┘
         │ HTTP GET (every 15 min in prod)
         ▼
┌─────────────────┐
│ OntarioScraper  │
│  - parse()      │
│  - tag with     │
│    ontology     │
└────────┬────────┘
         │ Measurement objects
         ▼
┌─────────────────┐
│ DatabaseService │
│  - insert_      │
│    measurements │
└────────┬────────┘
         │ PostgreSQL
         ▼
┌─────────────────┐
│ Neon Database   │
│  - measurements │
│  - hospitals    │
└────────┬────────┘
         │ SQL query
         ▼
┌─────────────────┐
│ Next.js API     │
│  /api/hospitals │
└────────┬────────┘
         │ JSON
         ▼
┌─────────────────┐
│ Map Component   │
│  - Mapbox GL    │
│  - Markers      │
└─────────────────┘
```

### Key Design Decisions

**Decision 1: Ontario First (vs Multi-Province)**
- **Rationale:** Vertical slice validates architecture; avoid premature optimization
- **Trade-off:** Delays Quebec comparison feature, but reduces risk
- **Reference:** See ADR-0001 (if created) or expansion-roadmap.md

**Decision 2: Direct HTML Parsing (vs API)**
- **Rationale:** Most provincial portals don't offer public APIs
- **Assumption:** Ontario portal will be HTML-based like Quebec
- **Fallback:** If API exists, create OntarioAPIClient variant

**Decision 3: Minimal Frontend (Static Map)**
- **Rationale:** Prove data pipeline before investing in UI polish
- **Scope:** Single page, map-only, no routing or complex state
- **Future:** Add features in Milestone 5 (polish phase)

**Decision 4: Local Development Only**
- **Rationale:** Production deployment introduces complexity (secrets, cron, monitoring)
- **Milestone 3:** Production deployment is separate, deliberate milestone
- **Testing:** Manual local testing sufficient for M2

---

## Implementation Phases

### Phase 0: Research & Discovery (Est: 2-4 hours)

**Purpose:** Understand Ontario data source before writing code

**Tasks:**

**0.1 Locate Ontario Health Portal**
- [ ] Search for official Ontario ED wait time portal
- [ ] Test URLs:
  - https://www.ontariohealth.ca/
  - https://health.gov.on.ca/en/pro/programs/waittimes/
  - https://www.hqontario.ca/
- [ ] Verify data is publicly accessible (not behind login)
- [ ] Document actual URL in findings doc

**0.2 Analyze Data Structure**
- [ ] View page source, inspect HTML structure
- [ ] Check for embedded JSON (look for `<script type="application/json">`)
- [ ] Check for API endpoints (Network tab in DevTools)
- [ ] Identify hospital list structure (table, cards, list?)
- [ ] Identify wait time format (minutes, hours, text?)
- [ ] Screenshot HTML structure for reference

**0.3 Document Methodology**
- [ ] Find methodology documentation (if available)
- [ ] Determine start_event (TRIAGE, REGISTRATION, or DOOR?)
- [ ] Determine end_event (PHYSICIAN, PROVIDER, or FIRST_ASSESSMENT?)
- [ ] Determine statistic_type (P90, MEAN, MEDIAN, POINT_ESTIMATE?)
- [ ] Document in `docs/ontario-methodology.md`

**0.4 Map Target Hospitals**
- [ ] List 10+ hospitals from portal
- [ ] Create standardized IDs (ca-on-{slug} format)
- [ ] Document official names for HOSPITAL_MAPPING
- [ ] Prioritize Ottawa (3-5) + Toronto (5-7) hospitals

**Deliverables:**
- `docs/ontario-research-findings.md` - Data source analysis
- `docs/ontario-methodology.md` - Methodology documentation
- `backend/ontario-hospital-mapping.txt` - Hospital name → ID mapping

**Success Criteria:**
- ✅ Can access Ontario portal without errors (not 404/403)
- ✅ Can identify wait time data in HTML
- ✅ Understand methodology enough to tag with ontology
- ✅ Have 10+ hospitals mapped

**Risks:**
- 🔴 **High Risk:** Portal doesn't exist or is paywalled → Fallback to Quebec
- 🟡 **Medium Risk:** Methodology unclear → Tag as "UNKNOWN" temporarily
- 🟢 **Low Risk:** Only 5 hospitals available → Proceed with 5

---

### Phase 1: Ontario Scraper Implementation (Est: 6-8 hours)

**Purpose:** Build scraper that extracts Ontario data

**Tasks:**

**1.1 Create Scraper File Structure**
- [ ] Create `backend/src/waittime/scrapers/ontario.py`
- [ ] Copy Quebec scraper as template
- [ ] Create `OntarioScraper` class extending `BaseScraper`
- [ ] Define `HOSPITAL_MAPPING` dict from Phase 0 research

**1.2 Implement Parsing Strategy**
- [ ] Implement `parse(html: str)` method
- [ ] Based on Phase 0 findings, choose strategy:
  - Table-based (like Quebec table parser)
  - JSON-based (like Quebec JSON parser)
  - API-based (create new pattern)
- [ ] Extract hospital names
- [ ] Extract wait times (handle formats: "120 min", "2h 30m", "2:30")
- [ ] Match hospitals to IDs using HOSPITAL_MAPPING

**1.3 Apply Ontario Methodology Tags**
- [ ] Set `metric_family` based on Phase 0 findings
- [ ] Set `start_event` (likely TRIAGE for Ontario)
- [ ] Set `end_event` (likely PHYSICIAN)
- [ ] Set `statistic_type` (likely P90 - CIHI standard)
- [ ] Set `source_id = "ontario-health"`

**1.4 Payload Handling**
- [ ] Hash payload with SHA256 (`raw_payload_hash`)
- [ ] Store snippet (first 200 chars for debugging)
- [ ] Set `parser_version = "v1.0"`

**1.5 Create Source Factory**
- [ ] Implement `create_ontario_source()` function
- [ ] Return `Source` object with correct metadata
- [ ] Update telehealth info: "Health811" + "811"

**1.6 Register in CLI**
- [ ] Add to `backend/src/waittime/scrapers/__init__.py`
- [ ] Add to SCRAPERS registry in `cli/scraper.py`
- [ ] Test: `python -m waittime.cli.scraper --list` shows ontario

**Deliverables:**
- `backend/src/waittime/scrapers/ontario.py` - Complete scraper
- Updated `__init__.py` and `cli/scraper.py`

**Success Criteria:**
- ✅ Scraper imports without errors
- ✅ Appears in `--list` output
- ✅ Can instantiate `OntarioScraper` object

**Risks:**
- 🟡 **Medium Risk:** HTML structure unexpected → Iterate on parsing logic
- 🟡 **Medium Risk:** Hospital names don't match → Improve fuzzy matching

---

### Phase 2: Testing (Est: 3-4 hours)

**Purpose:** Ensure scraper works reliably

**Tasks:**

**2.1 Create Unit Test Suite**
- [ ] Create `backend/tests/unit/test_ontario_scraper.py`
- [ ] Copy Quebec test structure as template
- [ ] Test `_extract_wait_time()` with various formats
- [ ] Test `_normalize_hospital_id()` exact and fuzzy matching
- [ ] Test `parse()` with sample HTML (from Phase 0)

**2.2 Test Parsing Strategies**
- [ ] Create mock HTML fixtures (table/JSON/card formats)
- [ ] Test each parsing strategy independently
- [ ] Verify correct hospital_id mapping
- [ ] Verify correct wait time extraction
- [ ] Test edge cases: N/A, Unknown, missing data

**2.3 Test Ontology Tagging**
- [ ] Verify `metric_family` correct
- [ ] Verify `start_event` correct
- [ ] Verify `end_event` correct
- [ ] Verify `statistic_type` correct
- [ ] Verify `source_id = "ontario-health"`

**2.4 Test Payload Handling**
- [ ] Verify SHA256 hash is 64 characters
- [ ] Verify snippet is ≤200 chars
- [ ] Verify parser_version set

**2.5 Run Test Suite**
- [ ] Run: `pytest tests/unit/test_ontario_scraper.py -v`
- [ ] Aim for >80% coverage on ontario.py
- [ ] Fix any failing tests
- [ ] Run full suite: `pytest tests/unit/ -v` (all should pass)

**Deliverables:**
- `backend/tests/unit/test_ontario_scraper.py` - 10-15 tests
- Coverage report showing >80% on ontario.py

**Success Criteria:**
- ✅ All Ontario scraper tests passing
- ✅ No regression in existing tests (24 Quebec + models tests)
- ✅ >80% coverage on ontario.py

**Risks:**
- 🟢 **Low Risk:** Tests fail → Debug and fix (expected iteration)

---

### Phase 3: Integration with Database (Est: 2-3 hours)

**Purpose:** Verify data flows to database correctly

**Tasks:**

**3.1 Update Source Seed Data (if needed)**
- [ ] Check if `sources` table has "ontario-health" row
- [ ] If not, update `backend/migrations/004_seed_sources.sql`
- [ ] Verify methodology fields match Phase 0 findings
- [ ] Re-run migration if updated

**3.2 Dry-Run Test**
- [ ] Run: `python -m waittime.cli.scraper --source ontario-health --dry-run`
- [ ] Verify console output shows parsed hospitals
- [ ] Verify wait times look reasonable (not NaN, not negative)
- [ ] Check for warnings/errors in output

**3.3 Live Scraper Test**
- [ ] Run: `python -m waittime.cli.scraper --source ontario-health`
- [ ] Verify "X measurements collected" message
- [ ] Verify "Wrote X measurements to database" message
- [ ] Check heartbeat updated

**3.4 Database Verification**
- [ ] Query measurements: `SELECT * FROM measurements WHERE source_id = 'ontario-health' LIMIT 10;`
- [ ] Verify values look correct
- [ ] Verify timestamp is recent
- [ ] Verify hospital_id format correct (ca-on-*)
- [ ] Verify ontology fields populated

**3.5 Scraper Status Check**
- [ ] Query: `SELECT * FROM scraper_status WHERE source_id = 'ontario-health';`
- [ ] Verify `last_run` is recent
- [ ] Verify `status = 'healthy'`
- [ ] Verify `measurements_count` matches

**Deliverables:**
- Database with Ontario measurements
- Verified heartbeat monitoring

**Success Criteria:**
- ✅ Scraper runs without errors
- ✅ Database contains Ontario measurements
- ✅ Heartbeat shows "healthy" status

**Risks:**
- 🟡 **Medium Risk:** Live URL structure differs from research → Update parser
- 🟡 **Medium Risk:** Database constraint violation → Check ontology enum values

---

### Phase 4: Frontend Foundation (Est: 8-10 hours)

**Purpose:** Create minimal map interface showing Ontario data

**Tasks:**

**4.1 Initialize Next.js Project**
- [ ] Run: `cd frontend && npx create-next-app@latest . --typescript --tailwind --app`
- [ ] Select App Router (not Pages Router)
- [ ] Configure for TypeScript
- [ ] Install Mapbox: `npm install mapbox-gl @types/mapbox-gl`
- [ ] Install database client: `npm install postgres`

**4.2 Environment Configuration**
- [ ] Create `frontend/.env.local.example`
- [ ] Add `DATABASE_URL` (Neon connection)
- [ ] Add `NEXT_PUBLIC_MAPBOX_TOKEN` (get from mapbox.com)
- [ ] Copy to `.env.local` with real values
- [ ] Add `.env.local` to `.gitignore`

**4.3 Database Types**
- [ ] Create `frontend/lib/types.ts`
- [ ] Define TypeScript interfaces:
  ```typescript
  interface Hospital {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
  }
  interface Measurement {
    hospital_id: string;
    value: number;
    timestamp_utc: string;
    metric_family: string;
    start_event: string;
    end_event: string;
    statistic_type: string;
  }
  ```

**4.4 API Route for Hospitals**
- [ ] Create `frontend/app/api/hospitals/route.ts`
- [ ] Query Neon for Ontario hospitals (verified + visible)
- [ ] Join with latest measurement
- [ ] Return JSON: `{ hospitals: [...], measurements: [...] }`
- [ ] Test: `curl http://localhost:3000/api/hospitals`

**4.5 Map Component**
- [ ] Create `frontend/components/Map.tsx`
- [ ] Initialize Mapbox GL map
- [ ] Center on Ontario (lat: 45.4, lon: -75.7)
- [ ] Set appropriate zoom level (6-7)
- [ ] Add navigation controls

**4.6 Hospital Markers**
- [ ] Fetch data from `/api/hospitals`
- [ ] Add marker for each hospital at (lat, lon)
- [ ] Color markers by wait time:
  - Green: <60 min
  - Yellow: 60-120 min
  - Red: >120 min

**4.7 Marker Popups**
- [ ] On marker click, show popup with:
  - Hospital name
  - Current wait time
  - Methodology tags (badge UI)
  - "Last updated: X mins ago"
- [ ] Style with Tailwind CSS

**4.8 Main Page**
- [ ] Update `frontend/app/page.tsx`
- [ ] Render `<Map />` component
- [ ] Add simple header: "WaitTime Canada - Ontario"
- [ ] Add footer: "Data from Ontario Health"

**Deliverables:**
- `frontend/` - Complete Next.js app
- Working map at `http://localhost:3000`

**Success Criteria:**
- ✅ Map loads and displays Ontario
- ✅ Hospital markers appear
- ✅ Clicking marker shows wait time
- ✅ Data reflects latest scraper run

**Risks:**
- 🟡 **Medium Risk:** Mapbox token required → Sign up for free tier
- 🟡 **Medium Risk:** CORS issues → Configure Next.js API routes properly
- 🟢 **Low Risk:** Styling takes longer → Use default styles, polish later

---

### Phase 5: Local Validation (Est: 2-3 hours)

**Purpose:** Verify entire system works end-to-end locally

**Tasks:**

**5.1 End-to-End Workflow Test**
- [ ] Step 1: Clear measurements table (fresh start)
- [ ] Step 2: Run Ontario scraper
- [ ] Step 3: Verify database has data
- [ ] Step 4: Start frontend: `npm run dev`
- [ ] Step 5: Verify map shows hospitals

**5.2 Data Freshness Test**
- [ ] Note current wait time for one hospital
- [ ] Wait 5 minutes (simulate stale data)
- [ ] Run scraper again
- [ ] Refresh frontend
- [ ] Verify timestamp updated

**5.3 Error Handling Test**
- [ ] Test scraper with invalid URL (expect error)
- [ ] Test frontend with empty database (should show no markers)
- [ ] Test frontend with Mapbox token missing (should show error)

**5.4 Consistency Test**
- [ ] Run scraper 3 times in a row
- [ ] Verify measurements are consistent (same hospitals, similar values)
- [ ] Check for duplicates in database
- [ ] Verify no crashes or exceptions

**5.5 Documentation**
- [ ] Document any Ontario-specific quirks in `docs/ontario-quirks.md`
- [ ] Document local dev workflow in README
- [ ] Update ROADMAP.md to mark Phase 2A-2D as complete

**Deliverables:**
- Validated end-to-end system
- Updated documentation

**Success Criteria:**
- ✅ Can run scraper → see results on map (full cycle)
- ✅ System handles errors gracefully
- ✅ Data stays consistent across multiple runs

**Risks:**
- 🟢 **Low Risk:** Minor bugs found → Fix and retest

---

## Testing Strategy

### Test Levels

**Unit Tests:**
- Ontario scraper parsing logic
- Wait time extraction
- Hospital ID normalization
- All edge cases (N/A values, missing data)

**Integration Tests:**
- Scraper → Database writes
- Database → Frontend reads
- API route functionality

**End-to-End Tests:**
- Full workflow: scraper → database → frontend → user sees data
- Manual testing (no Playwright for M2)

### Coverage Goals

- Ontario scraper: >80%
- Overall backend: >60%
- Frontend: Manual testing only (no coverage target for M2)

### Testing Tools

- pytest (backend)
- Manual browser testing (frontend)
- SQL queries (database validation)

---

## Risk Assessment

### Critical Risks (Must Mitigate)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Ontario portal doesn't exist | High - blocks entire milestone | Medium | **Fallback:** Switch to Quebec as primary, find real URL |
| Portal requires authentication | High - can't scrape | Low | **Fallback:** Contact Ontario Health, request API access |
| Database schema issues | Medium - requires migration changes | Low | **Mitigation:** Schema already validated in M1 |

### Medium Risks (Monitor)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| HTML structure changes frequently | Medium - scraper breaks | Medium | **Mitigation:** Add version detection, alerting |
| Only 3-5 hospitals available | Low - still proves concept | Medium | **Mitigation:** Proceed with fewer hospitals |
| Mapbox free tier limits | Low - frontend delays | Low | **Mitigation:** Mapbox allows 50k free loads/month |

### Low Risks (Accept)

- Frontend styling takes longer than expected
- Some tests are flaky
- Local dev setup varies by machine

---

## Success Criteria

### Milestone 2 Complete When:

**Technical Success:**
1. ✅ Ontario scraper runs without errors
2. ✅ >80% test coverage on Ontario scraper
3. ✅ Database contains Ontario measurements
4. ✅ Frontend map shows Ontario hospitals with wait times
5. ✅ Can click hospital marker and see methodology tags

**Business Success:**
1. ✅ Validates core architectural assumptions
2. ✅ Proves metric ontology system works
3. ✅ Establishes repeatable pattern for other provinces
4. ✅ Delivers first user-facing value (can see wait times)

**Quality Gates:**
- All tests passing (35+ tests total)
- No console errors in frontend
- Scraper completes in <30 seconds
- Frontend loads in <3 seconds

---

## Timeline and Effort Estimates

### Optimistic (Best Case): 12-15 hours
- Phase 0: 2 hours (data source easily found)
- Phase 1: 5 hours (HTML structure simple)
- Phase 2: 2 hours (tests straightforward)
- Phase 3: 1 hour (no issues)
- Phase 4: 6 hours (frontend smooth)
- Phase 5: 1 hour (minimal bugs)

### Realistic (Expected): 20-25 hours
- Phase 0: 3 hours (some research required)
- Phase 1: 7 hours (parsing requires iteration)
- Phase 2: 3 hours (comprehensive tests)
- Phase 3: 2 hours (minor database issues)
- Phase 4: 9 hours (Mapbox setup, styling)
- Phase 5: 2 hours (bug fixes)

### Pessimistic (Worst Case): 35-40 hours
- Phase 0: 6 hours (portal hard to find, methodology unclear)
- Phase 1: 10 hours (complex HTML, API instead of HTML)
- Phase 2: 4 hours (many edge cases)
- Phase 3: 3 hours (database constraint violations)
- Phase 4: 12 hours (CORS issues, Mapbox complexity)
- Phase 5: 4 hours (multiple bugs, integration issues)

**Recommended Calendar Time:** 2-3 weeks (assuming 2-3 hours/day of focused work)

---

## Rollback Plan

### If Milestone 2 Fails:

**Option 1: Switch to Quebec** (if Ontario portal doesn't exist)
- Quebec scraper already exists
- Find real Quebec URL
- Skip to Phase 3 (database integration)

**Option 2: Use Mock Data** (if no real data source available)
- Create mock scraper with hardcoded values
- Build frontend with fake data
- Prove UI/UX before finding real data source

**Option 3: Descope Frontend** (if frontend too complex)
- Skip Phase 4 (frontend)
- Focus on scraper + database
- Use SQL queries to verify data
- Add frontend in separate milestone

---

## Post-Milestone Review

### After M2 Complete:

**Required Actions:**
1. Update ROADMAP.md (mark M2 complete, M3 current)
2. Document lessons learned in `docs/lessons-learned-m2.md`
3. Update expansion-roadmap.md with Ontario-specific notes
4. Create ADR for any major design decisions made during implementation
5. Review test coverage, aim for >60% overall

**Decision Point:**
- ✅ Ontario stable for 3 days? → Proceed to M3 (Production Deployment)
- ❌ Ontario unstable? → Debug and stabilize before M3

---

## Appendices

### A. Command Reference

```bash
# Phase 1: Development
cd backend && source .venv/bin/activate
python -m waittime.cli.scraper --list
python -m waittime.cli.scraper --source ontario-health --dry-run

# Phase 2: Testing
pytest tests/unit/test_ontario_scraper.py -v
pytest tests/unit/ -v --cov=src/waittime

# Phase 3: Database
psql $DATABASE_URL -c "SELECT * FROM measurements WHERE source_id = 'ontario-health';"
psql $DATABASE_URL -c "SELECT * FROM scraper_status WHERE source_id = 'ontario-health';"

# Phase 4: Frontend
cd frontend
npm run dev
# Visit http://localhost:3000

# Phase 5: Validation
python -m waittime.cli.scraper --source ontario-health
# Refresh frontend, verify data updated
```

### B. File Structure

```
backend/
├── src/waittime/scrapers/
│   ├── ontario.py          # Phase 1
│   └── __init__.py         # Phase 1 (updated)
├── tests/unit/
│   └── test_ontario_scraper.py  # Phase 2
└── migrations/
    └── 004_seed_sources.sql     # Phase 3 (maybe updated)

frontend/
├── app/
│   ├── page.tsx            # Phase 4
│   └── api/hospitals/
│       └── route.ts        # Phase 4
├── components/
│   └── Map.tsx             # Phase 4
├── lib/
│   └── types.ts            # Phase 4
└── .env.local.example      # Phase 4

docs/
├── ontario-research-findings.md  # Phase 0
├── ontario-methodology.md        # Phase 0
└── ontario-quirks.md             # Phase 5
```

### C. Data Source Candidates

**Ontario Health:**
- https://www.ontariohealth.ca/our-work/programs/ontario-wait-times
- https://health.gov.on.ca/en/pro/programs/waittimes/

**Health Quality Ontario:**
- https://www.hqontario.ca/System-Performance/Emergency-Department-Wait-Times

**Alternative (if official sources unavailable):**
- Individual hospital websites (e.g., Ottawa Hospital, Toronto General)
- Note: Less reliable, no standard format

---

## Approval and Sign-Off

**Prepared By:** Jeremy Dawson
**Date:** 2026-01-30

**Status:** ⏸️ Awaiting review and approval to proceed with implementation

**Next Action:** Review this plan, approve, then begin Phase 0 (Research)

---

**End of Implementation Plan v1.0.0**
