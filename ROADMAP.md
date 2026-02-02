# WaitTime Canada - Project Roadmap

> **Philosophy:** Vertical slices, not horizontal layers. Each milestone delivers working, shippable functionality.

**Last Updated:** 2026-02-02
**Approach:** Iterative development, one province at a time
**Current Phase:** Infrastructure Complete ✓ → Ontario Implementation In Progress

---

## Progress Summary

| Component | Status | Tests | Coverage |
|-----------|--------|-------|----------|
| Backend Infrastructure | ✅ Complete | 143 tests | 57% |
| Frontend Infrastructure | ✅ Complete | 78 tests | 100% pass |
| Database Schema | ✅ Complete | Migrated | Full schema |
| Integration Tests | ✅ Complete | 21 tests | End-to-end |
| Documentation | ✅ Complete | Comprehensive | Methodology docs |

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

### In Progress

**2.1 Ontario Scraper Production** 🔄
- Ontario scraper functional with Playwright
- Needs: Real URL verification and testing
- Status: Code complete, awaiting production testing

---

## Milestone 3: Production Deployment (Pending)

**Goal:** Automated scraping and public frontend

### Tasks

- [ ] **3.1** Configure DATABASE_URL secret in GitHub
- [ ] **3.2** Update GitHub Actions for scraper cron (15-minute schedule)
- [ ] **3.3** Deploy frontend to Vercel
- [ ] **3.4** Configure environment variables (MAPBOX_TOKEN, DATABASE_URL)
- [ ] **3.5** Monitor first 24 hours for errors
- [ ] **3.6** Set up heartbeat stale checks
- [ ] **3.7** Configure failure notifications

---

## Milestone 4: Quebec Expansion (Pending)

**Goal:** Demonstrate methodology divergence across provinces

### Tasks

- [ ] **4.1** Find real Quebec health portal URL (current URL is 404)
- [ ] **4.2** Update Quebec scraper for actual HTML structure
- [ ] **4.3** Add Quebec hospitals to verification queue
- [ ] **4.4** Test Ottawa vs Gatineau comparison with divergence warning
- [ ] **4.5** Verify methodology differences are highlighted

---

## Milestone 5: Polish & Documentation (Pending)

**Goal:** Portfolio-ready presentation

### Tasks

- [ ] **5.1** Create public `/methods` page
- [ ] **5.2** Display comparability matrix
- [ ] **5.3** Add telehealth routing information
- [ ] **5.4** Update README with live site URL
- [ ] **5.5** Write LinkedIn launch post
- [ ] **5.6** Final review of all documentation

---

## Technical Debt & Improvements

### High Priority
- [ ] Increase geocoding service test coverage (currently 13%)
- [ ] Add CLI tool tests (currently 0% coverage)
- [ ] Add more frontend E2E tests

### Medium Priority
- [ ] Add batch operations to verification queue
- [ ] Implement search/filter in admin panel
- [ ] Add revision history for verification actions

### Low Priority
- [ ] Historical trends / charts
- [ ] User accounts / saved hospitals
- [ ] Email alerts for wait time changes

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
- Total: 78 tests passing
- Unit tests: 78 tests (includes Map and Comparison tests)
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
