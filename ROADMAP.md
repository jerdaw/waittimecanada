# WaitTime Canada - Project Roadmap

> **Philosophy:** Vertical slices, not horizontal layers. Each milestone delivers working, shippable functionality.

**Last Updated:** 2026-02-04
**Milestone 5:** ✅ Complete - Ready for Production Deployment
**Milestone 3:** ✅ Complete - GitHub Actions Scrapers Running
**Milestone 4:** 🔄 In Progress - Quebec Scraper Rewrite
**Approach:** Iterative development, one province at a time
**Current Phase:** Ontario Live ✓ → Quebec Scraper Rewrite

---

## Progress Summary

| Component | Status | Tests | Coverage |
|-----------|--------|-------|----------|
| Backend Infrastructure | ✅ Complete | 143 tests | 57% |
| Frontend Infrastructure | ✅ Complete | 79 tests | 100% pass |
| Database Schema | ✅ Complete | Migrated | Full schema |
| Integration Tests | ✅ Complete | 21 tests | End-to-end |
| Documentation | ✅ Complete | Comprehensive | Methodology docs |
| **Ontario Scraper** | ✅ **Live** | 164 measurements | 154 hospitals |
| **Quebec Scraper** | ❌ **Broken** | 0 | URL changed |

### Live Scraper Status (2026-02-04)

| Province | Status | Hospitals | Geocoded | Notes |
|----------|--------|-----------|----------|-------|
| Ontario | ✅ Working | 154 | 72 (47%) | 82 need manual coordinates |
| Quebec | ❌ Broken | 0 | 0 | Government changed URL/format |

**Detailed Status:** [docs/planning/scraper-status-2026-02-04.md](docs/planning/scraper-status-2026-02-04.md)

---

## Completed Work

### ✅ Core Infrastructure (Complete)

**Backend**
- [x] Neon PostgreSQL 17 database with full schema
- [x] Core models with Pydantic validation (Hospital, Source, Measurement)
- [x] DatabaseService with CRUD operations
- [x] HeartbeatService for scraper health monitoring
- [x] ComparisonService for methodology divergence detection
- [x] BaseScraper abstract class with retry logic
- [x] Quebec scraper (BeautifulSoup-based)
- [x] Ontario scraper (Playwright-based for dynamic content)
- [x] CLI tools (scraper runner, database cleanup, seeding)
- [x] Data seeding system (sources, hospitals, test data)
- [x] Data retention policy (30-day cleanup)
- [x] Unit tests: 122 passing, 50% coverage
- [x] Integration tests: 14 passing, full stack verification

**Frontend**
- [x] Next.js 14 with App Router + TypeScript
- [x] Mapbox GL JS integration
- [x] Hospital map component with markers
- [x] Comparison modal with divergence warnings
- [x] Admin verification queue UI (`/admin/verify`)
- [x] API routes (hospitals, comparisons, admin operations)
- [x] Vitest + React Testing Library setup
- [x] Unit tests: 73 passing

**Documentation**
- [x] Ontario methodology documentation (comprehensive)
- [x] Machine-readable methodology JSON reference
- [x] Integration testing guide
- [x] Data retention policy documentation
- [x] Verification queue workflow documentation
- [x] 16 methodology validation tests

**DevOps**
- [x] GitHub Actions database cleanup workflow
- [x] Test suite running in CI
- [x] Playwright E2E tests configured

---

## Current Focus: Ontario Implementation

### Completed

**2.2 Hospital Data Seeding** ✅
- [x] Created seed data format (JSON)
- [x] Built CLI tools for seeding sources and hospitals
- [x] Seeded Ontario source (ontario-health)
- [x] Seeded 213 Ontario hospitals
- [x] Generated 530 test measurements
- [x] Added 9 unit tests for seeding functionality
- [x] Comprehensive seeding documentation
- Status: Complete with tooling and test data

**2.3 Frontend Map Integration** ✅
- [x] Enhanced hospitals API with methodology fields
- [x] Updated Map component to display methodology
- [x] Show metric family, start/end events, statistic type
- [x] User-friendly formatting (Triage → Physician, 90th percentile)
- [x] Tested with 213 seeded Ontario hospitals
- [x] Added Map component tests (78 frontend tests passing)
- [x] Verified end-to-end integration with real data
- Status: Complete with methodology display

**2.4 Comparison Feature Testing** ✅
- [x] Created 7 integration tests for comparison service
- [x] Tested with real Ontario hospital data (identical methodology)
- [x] Tested with test data (different methodologies)
- [x] Verified divergence brief generation
- [x] Verified error handling (hospital not found, unverified)
- [x] Created manual test script (test-comparison-api.js)
- [x] Verified end-to-end comparison workflow
- [x] All 143 backend tests passing (57% coverage)
- [x] All 78 frontend tests passing
- [x] ComparisonService: 100% coverage
- Status: Complete with comprehensive testing

### Pending Cleanup

**Uncommitted Working Files**
- `frontend/test-comparison-api.js` - Modified test script
- `frontend/test-telehealth-api.js` - Modified test script
- `scripts/migrate-structure.sh` - Modified migration script

**2.1 Ontario Scraper Production** ⏳
- Ontario scraper functional with Playwright
- Needs: Real URL verification in production environment
- Status: Code complete, awaiting production deployment to test with live data

---

## Milestone 3: Production Deployment ✅ (Complete - 2026-02-04)

**Goal:** Automated scraping and public frontend
**Platform:** GitHub Actions (scrapers) + Netlify (frontend)
**Status:** Ontario scraper running in production, frontend deployed

### Infrastructure Complete
- [x] **Scrapers:** GitHub Actions cron running every 15 minutes
- [x] **Monitoring:** Heartbeat monitor workflow configured
- [x] **Alerts:** Pushover notifications for scraper failures
- [x] **Database:** Neon PostgreSQL with 164 Ontario measurements
- [x] **Frontend:** Next.js deployed to Netlify
- [x] **Secrets:** DATABASE_URL, PUSHOVER keys configured

### Deployment Verification
- [x] **3.1** Add secrets to GitHub repository ✅
- [x] **3.2** Deploy frontend to Netlify ✅
- [x] **3.3** Configure environment variables ✅
- [x] **3.4** Configure Pushover notifications ✅
- [x] **3.5** Verify Ontario scraper working ✅ (164 measurements)
- [ ] **3.6** Verify 72 geocoded hospitals on map
- [ ] **3.7** Admin verification of hospitals in queue

### Known Issues (2026-02-04)
- Quebec scraper broken (URL changed) - see Milestone 4
- 82 Ontario hospitals have placeholder coordinates (0.0, 0.0)
- All hospitals need admin verification before public visibility

---

## Milestone 4: Quebec Scraper Rewrite 🔄 (In Progress)

**Goal:** Fix Quebec scraper after government website changes
**Blocking Issue:** Quebec government changed URL and page format in 2026
**Detailed Analysis:** [docs/planning/scraper-status-2026-02-04.md](docs/planning/scraper-status-2026-02-04.md)

### The Problem

| Attribute | Old (Broken) | New |
|-----------|--------------|-----|
| URL | `quebec.ca/sante/.../urgences` (404) | `quebec.ca/en/health/.../situation-in-emergency-rooms-in-quebec` |
| Format | HTML table | Dynamic searchable interface |
| Parser | BeautifulSoup | Requires Playwright or API |

### Implementation Options

**Option A: Playwright-based Scraper (Recommended)**
- Similar to Ontario scraper
- Wait for JavaScript to load facility cards
- Parse card content for wait times
- Effort: Medium | Reliability: High

**Option B: Find API Endpoint**
- Inspect network requests on the new page
- Call underlying JSON API directly
- Effort: Low (if found) | Reliability: Variable

**Option C: Provincial Open Data**
- Check MSSS data portal
- Look for official health data APIs
- Effort: High | Reliability: High

### Tasks

- [x] **4.1** Find new Quebec URL ✅ (URL updated in codebase)
- [ ] **4.2** Investigate new page structure (API vs JavaScript)
- [ ] **4.3** Rewrite QuebecScraper for new format
- [ ] **4.4** Update test fixtures for new HTML/JSON structure
- [ ] **4.5** Add Quebec hospitals to verification queue
- [ ] **4.6** Test Ottawa vs Gatineau comparison with divergence warning
- [ ] **4.7** Verify methodology differences are highlighted

### Files Requiring Changes

| File | Change |
|------|--------|
| `backend/src/waittime/scrapers/quebec.py` | Rewrite parser |
| `backend/tests/unit/scrapers/test_quebec_scraper.py` | Update fixtures |
| `backend/migrations/004_seed_sources.sql` | ✅ URL updated |

---

## Milestone 5: Polish & Documentation ✅ (Complete - Feb 2)

**Goal:** Portfolio-ready presentation

### Tasks

- [x] **5.1** Create public `/methods` page ✅ (Already implemented)
- [x] **5.2** Display comparability matrix ✅ (Already implemented)
- [x] **5.3** Add telehealth routing information ✅ (Complete - Feb 2)
- [x] **5.4** Update README with comprehensive documentation ✅ (Complete - Feb 2)
- [x] **5.5** Write LinkedIn launch post ✅ (Complete - Feb 2)
- [x] **5.6** Final review of all documentation ✅ (Complete - Feb 2)

**Status:** All 6 tasks complete. Project is portfolio-ready and approved for public release.

---

## Milestone 4.5: Geocoding Improvements (Pending)

**Goal:** Fix the 82 Ontario hospitals with placeholder coordinates
**Impact:** 53% of hospitals won't appear correctly on map

### Current Status

| Category | Count | Percentage |
|----------|-------|------------|
| Successfully geocoded | 72 | 47% |
| Placeholder coordinates (0,0) | 82 | 53% |

### Improvement Options

| Option | Effort | Cost | Expected Accuracy |
|--------|--------|------|-------------------|
| Manual coordinates CSV | Medium | Free | 100% |
| Add MAPBOX_TOKEN | Low | ~$5/month | 80%+ |
| Improve name parsing | Medium | Free | 60%+ |
| Google Places API | Low | Pay per use | 95%+ |

### Recommended Approach: Manual Coordinates CSV

Create `backend/data/ontario_hospital_coordinates.csv`:
```csv
hospital_id,latitude,longitude,city
ca-on-georgian-bay-general-hosp-midland-site,44.7457,-79.8829,Midland
ca-on-bluewater-health-charlotte-eleanor-englehart-petrolia,42.8778,-82.1363,Petrolia
```

### Tasks

- [ ] **4.5.1** Export list of hospitals with placeholder coordinates
- [ ] **4.5.2** Research correct coordinates for each hospital
- [ ] **4.5.3** Create CSV file with manual coordinates
- [ ] **4.5.4** Update scraper to check CSV before geocoding
- [ ] **4.5.5** Re-run geocoding for placeholder hospitals

---

## Technical Debt & Improvements

### High Priority
- [ ] Fix 82 Ontario hospitals with placeholder coordinates (see Milestone 4.5)
- [ ] Increase geocoding service test coverage (currently 13%)
- [ ] Add CLI tool tests (currently 0% coverage)
- [ ] Add more frontend E2E tests
- [ ] Make workflow tolerant of partial scraper failures

### Medium Priority
- [ ] Add batch operations to verification queue
- [ ] Implement search/filter in admin panel
- [ ] Add revision history for verification actions
- [ ] Add MAPBOX_TOKEN for better geocoding fallback

### Low Priority
- [ ] Historical trends / charts
- [ ] User accounts / saved hospitals
- [ ] Email alerts for wait time changes
- [ ] Access Burden Estimator (distance × gas price + parking with disclaimer)
- [ ] Equity layer overlay (income shapefiles)
- [ ] Mobile optimization

---

## Future Provinces (Backlog)

These are explicitly **not** in scope for initial launch:

- [ ] Alberta scraper
- [ ] Manitoba scraper
- [ ] British Columbia scraper
- [ ] Saskatchewan scraper
- [ ] Maritime provinces
- [ ] Territories

---

## Architecture Decisions

Key decisions made:

1. **Neon PostgreSQL** over Supabase
   - Better PostgreSQL 17 support
   - Simpler connection model
   - Cost-effective for MVP

2. **Playwright** for Ontario scraper
   - Required for dynamic content loading
   - More robust than requests + BeautifulSoup
   - Better error handling

3. **Integration Tests**
   - Verify full stack with real database
   - Transaction rollback for isolation
   - Catches issues unit tests miss

4. **Strict Ontology System**
   - Never normalize different methodologies
   - Tag every measurement with metadata
   - Generate divergence warnings automatically

5. **Manual Verification Queue**
   - Never auto-publish new hospitals
   - Admin approval required
   - Prevents incorrect data from going live

---

## Test Statistics

**Backend:**
- Total: 143 tests passing
- Unit tests: 122 tests (includes 9 seed CLI tests)
- Integration tests: 21 tests (includes 7 comparison tests)
- Coverage: 57% overall
  - ComparisonService: 100%
  - Core models: 96%
  - DatabaseService: 85%
  - Scrapers: 73-96%
  - Seed CLI: 46%

**Frontend:**
- Total: 79 tests passing
- Unit tests: 79 tests (includes Map, Comparison, and Telehealth tests)
- E2E tests: Configured for CI only
- Coverage: 100% pass rate

---

## How to Use This Roadmap

### Updating Progress
1. Mark completed items with ✅
2. Update status in "Current Focus" section
3. Move completed milestones to "Completed Work"
4. Add new technical debt to appropriate section

### Starting New Work
1. Check dependencies are met
2. Review acceptance criteria
3. Update status to 🔄 in progress
4. Commit with descriptive messages

### Status Legend
- ✅ Complete
- 🔄 In progress
- ⏳ Pending
- ⏸️ Blocked

---

## Quick Links

**Planning & Status:**
- [Scraper Status Report (2026-02-04)](docs/planning/scraper-status-2026-02-04.md) - Current scraper implementation status
- [Production Deployment Plan](docs/production-deployment-plan.md) - Original deployment planning

**Documentation:**
- [Integration Testing Guide](backend/docs/integration-testing.md)
- [Data Retention Policy](backend/docs/data-retention.md)
- [Ontario Methodology](backend/docs/methodologies/ontario-methodology.md)
- [Verification Queue](backend/docs/verification-queue.md)

**Code:**
- [Backend Tests](backend/tests/)
- [Frontend Tests](frontend/tests/)
- [Scrapers](backend/src/waittime/scrapers/)
- [Services](backend/src/waittime/services/)

---

*This roadmap reflects actual progress, not initial plans. Updated regularly as development continues.*
