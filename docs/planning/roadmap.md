# Implementation Roadmap

## Current Status (Updated 2026-01-30)

**Progress:** Week 1 infrastructure complete ✓

- ✅ Repository modernized with proper Python package structure
- ✅ Database schema created on Neon PostgreSQL
- ✅ Core models with metric ontology implemented
- ✅ Quebec scraper MVP with 3 parsing strategies
- ✅ Database service layer (psycopg2)
- ✅ CLI tool for running scrapers
- ✅ 24 unit tests passing (56% coverage)

**Next:** Additional provincial scrapers, frontend initialization

---

## Overview

This roadmap breaks down the 4-week implementation plan into granular, actionable tasks with clear dependencies and acceptance criteria.

**Timeline:** 4 weeks (20 working days)
**Approach:** Agile sprint with daily stand-ups (optional for solo dev)
**Priorities:** Data integrity > Feature completeness > Visual polish

## Pre-Implementation (Week 0)

### Environment Setup

**Duration:** 1-2 days before Week 1 starts

- [ ] Create GitHub repository
  - Initialize with `.gitignore` (Python, Node.js, .env)
  - Add LICENSE (MIT recommended)
  - Create initial README
- [ ] Set up Supabase account
  - Create new project: "waittime-canada"
  - Note project URL and API keys
  - Enable database extensions: PostGIS
- [ ] Configure GitHub Secrets
  - Add all required secrets (see `.github/workflows/README.md`)
- [ ] Set up development machine
  - Install Python 3.12+
  - Install Node.js 20.x LTS
  - Install pnpm 8.x
  - Install PostgreSQL client tools (psql)
- [ ] Clone repo and verify setup
  - `git clone` repository
  - Create `.env` files from `.env.example`
  - Verify connection to Supabase

**Acceptance Criteria:**
- [ ] Can connect to Supabase via psql
- [ ] GitHub Actions workflows validate successfully
- [ ] Local development environment configured

---

## Week 1: Data Foundation (The "Audit" MVP)

**Goal:** Establish database schema and basic scraping infrastructure

### Day 1: Database Schema

**Tasks:**
- [ ] Create database enums
  - [ ] Write `database/types/enums.sql`
  - [ ] Create all 5 enum types (metric_family, start_event, end_event, statistic_type, patient_scope)
  - [ ] Apply to Supabase: `psql $SUPABASE_URL -f database/types/enums.sql`

- [ ] Create core tables
  - [ ] Write `database/migrations/001_initial_schema.sql`
  - [ ] Create `sources` table with CHECK constraints
  - [ ] Create `hospitals` table with coordinates validation
  - [ ] Create `measurements` table with ontology enums
  - [ ] Apply migration

- [ ] Add indexes
  - [ ] Write `database/migrations/002_add_indexes.sql`
  - [ ] Create performance indexes (see DATABASE.md)
  - [ ] Apply migration

- [ ] Enable Row-Level Security
  - [ ] Write `database/migrations/003_enable_rls.sql`
  - [ ] Create RLS policies for all tables
  - [ ] Test with anon key vs service key
  - [ ] Apply migration

**Acceptance Criteria:**
- [ ] All tables created without errors
- [ ] Enums enforce valid values (test invalid insert)
- [ ] RLS policies prevent anon writes
- [ ] Service key can write, anon key can read

**Estimated Time:** 6 hours

---

### Day 2: Scraper Core Infrastructure

**Tasks:**
- [ ] Set up Python project structure
  - [ ] Create `scrapers/pyproject.toml` with dependencies
  - [ ] Create `scrapers/src/` directory structure
  - [ ] Install dependencies: `pip install -e ".[dev]"`

- [ ] Implement Pydantic models
  - [ ] Create `src/core/models.py`
  - [ ] Define `Measurement` model with enum validation
  - [ ] Define `Hospital` and `Source` models
  - [ ] Add unit tests: `tests/test_models.py`

- [ ] Implement database client
  - [ ] Create `src/core/database.py`
  - [ ] Supabase client initialization
  - [ ] Insert/upsert helper functions
  - [ ] Error handling and retries (tenacity)

- [ ] Implement utility functions
  - [ ] Create `src/core/utils.py`
  - [ ] SHA256 hash function for payloads
  - [ ] Structured logging setup (structlog)
  - [ ] Environment variable loader

**Acceptance Criteria:**
- [ ] Pydantic models reject invalid enum values
- [ ] Can insert measurement to database
- [ ] SHA256 hashing works correctly
- [ ] Structured logs output JSON

**Estimated Time:** 6 hours

---

### Day 3: Base Scraper Class

**Tasks:**
- [ ] Create abstract base scraper
  - [ ] Create `src/scrapers/base.py`
  - [ ] Define `BaseScraper` abstract class
  - [ ] Implement `fetch_with_backoff()` with retry logic
  - [ ] Implement `parse()` abstract method
  - [ ] Implement `run()` orchestration method

- [ ] Add HTTP session management
  - [ ] Configure requests with timeout
  - [ ] Add user-agent header
  - [ ] Respect robots.txt (1 req/sec rate limit)

- [ ] Create test fixtures
  - [ ] Create `tests/fixtures/` directory
  - [ ] Add sample HTML files for testing
  - [ ] Create `tests/conftest.py` with pytest fixtures

**Acceptance Criteria:**
- [ ] Base scraper can fetch URL with retries
- [ ] Exponential backoff works on 503 errors
- [ ] Rate limiting enforced (1 req/sec)
- [ ] Mock HTTP requests work in tests

**Estimated Time:** 5 hours

---

### Day 4: Quebec Scraper Implementation

**Tasks:**
- [ ] Implement Quebec scraper
  - [ ] Create `src/scrapers/quebec.py`
  - [ ] Extend `BaseScraper`
  - [ ] Parse Quebec HTML table
  - [ ] Extract hospital names and wait times
  - [ ] Tag with correct ontology: `start_event=REGISTRATION`

- [ ] Seed Quebec sources
  - [ ] Create `database/seed/sources.sql`
  - [ ] Insert Quebec source record with telehealth info
  - [ ] Apply: `psql $SUPABASE_URL -f database/seed/sources.sql`

- [ ] Test Quebec scraper
  - [ ] Create `tests/test_quebec_scraper.py`
  - [ ] Test parsing with fixture HTML
  - [ ] Test ontology tagging is correct
  - [ ] Test payload hashing

**Acceptance Criteria:**
- [ ] Scraper successfully parses Quebec HTML
- [ ] Measurements inserted with correct ontology
- [ ] Tests pass with 80%+ coverage
- [ ] No hospitals auto-published (is_verified=false)

**Estimated Time:** 7 hours

---

### Day 5: Heartbeat System & First Production Run

**Tasks:**
- [ ] Implement heartbeat system
  - [ ] Create `database/migrations/004_add_heartbeat.sql`
  - [ ] Create `scraper_status` table
  - [ ] Apply migration

- [ ] Implement heartbeat logic
  - [ ] Create `src/core/heartbeat.py`
  - [ ] `write_heartbeat()` upsert function
  - [ ] Update `BaseScraper.run()` to write heartbeat
  - [ ] Add error tracking to heartbeat

- [ ] Create main orchestrator
  - [ ] Create `src/main.py`
  - [ ] Import all scrapers (currently just Quebec)
  - [ ] Run each scraper with error isolation
  - [ ] Log summary statistics

- [ ] First production run
  - [ ] Run manually: `python -m src.main`
  - [ ] Verify measurements in Supabase dashboard
  - [ ] Verify heartbeat written
  - [ ] Check for errors

**Acceptance Criteria:**
- [ ] Scraper completes without errors
- [ ] Measurements visible in database
- [ ] Heartbeat status = "healthy"
- [ ] No duplicate measurements (idempotency works)

**Estimated Time:** 6 hours

---

### Week 1 Deliverables

- ✅ PostgreSQL schema with strict ontology enforcement
- ✅ Quebec scraper running successfully
- ✅ Heartbeat monitoring system
- ✅ 50+ measurements in database
- ✅ All tests passing

---

## Week 2: Multi-Province Heterogeneity

**Goal:** Prove comparability logic works with different methodologies

### Day 6: Alberta Scraper

**Tasks:**
- [ ] Research Alberta data source
  - [ ] Find official AHS wait time page
  - [ ] Document methodology (likely TRIAGE start, not REGISTRATION)
  - [ ] Save sample HTML to fixtures

- [ ] Implement Alberta scraper
  - [ ] Create `src/scrapers/alberta.py`
  - [ ] Parse AHS data format
  - [ ] Tag with `start_event=TRIAGE` (key difference!)
  - [ ] Handle multiple hospitals

- [ ] Seed Alberta sources
  - [ ] Add Alberta source to `database/seed/sources.sql`
  - [ ] Include "Health Link 811" telehealth info

- [ ] Test Alberta scraper
  - [ ] Create `tests/test_alberta_scraper.py`
  - [ ] Verify ontology differences from Quebec
  - [ ] Test parsing edge cases

**Acceptance Criteria:**
- [ ] Alberta scraper parses successfully
- [ ] Ontology differs from Quebec (start_event)
- [ ] Tests pass
- [ ] Measurements inserted

**Estimated Time:** 6 hours

---

### Day 7: Manitoba Scraper

**Tasks:**
- [ ] Research Manitoba data source
  - [ ] Find official WRHA wait time page
  - [ ] Document methodology (likely ALGORITHMIC statistic_type)
  - [ ] Save sample HTML

- [ ] Implement Manitoba scraper
  - [ ] Create `src/scrapers/manitoba.py`
  - [ ] Parse WRHA format
  - [ ] Tag with unique ontology combination

- [ ] Seed Manitoba sources
  - [ ] Add to sources.sql

- [ ] Update main orchestrator
  - [ ] Add Alberta and Manitoba to `src/main.py`
  - [ ] Test running all 3 scrapers sequentially

**Acceptance Criteria:**
- [ ] 3 scrapers run successfully
- [ ] Each province has different ontology signature
- [ ] No crashes or data corruption

**Estimated Time:** 6 hours

---

### Day 8: Comparability Logic (Auto-Researcher)

**Tasks:**
- [ ] Implement comparability function
  - [ ] Create `src/auto_researcher.py`
  - [ ] `are_comparable(measurement_a, measurement_b)` function
  - [ ] Compare all 4 ontology fields
  - [ ] Return boolean + explanation

- [ ] Generate divergence briefs
  - [ ] `generate_divergence_brief()` function
  - [ ] Return structured explanation of differences
  - [ ] Example: "Alberta uses Triage-to-Physician (P90), Quebec uses Registration-to-Physician (Avg)"

- [ ] Test comparability logic
  - [ ] Create `tests/test_auto_researcher.py`
  - [ ] Test identical ontologies return True
  - [ ] Test different start_events return False
  - [ ] Test divergence brief formatting

**Acceptance Criteria:**
- [ ] Comparability logic correctly identifies incomparable data
- [ ] Divergence briefs explain differences clearly
- [ ] Tests cover all edge cases

**Estimated Time:** 5 hours

---

### Day 9: Verification Queue System

**Tasks:**
- [ ] Create verification queue query
  - [ ] Write SQL query for unverified hospitals
  - [ ] Include measurement count per hospital
  - [ ] Order by first_seen_at

- [ ] Build simple admin CLI tool
  - [ ] Create `src/admin/verify_hospitals.py`
  - [ ] List unverified hospitals
  - [ ] Prompt for approval (y/n/skip)
  - [ ] Update `is_verified` and `is_visible` flags

- [ ] Verify all existing hospitals
  - [ ] Run verification tool
  - [ ] Review Quebec, Alberta, Manitoba hospitals
  - [ ] Approve legitimate facilities
  - [ ] Flag any anomalies

**Acceptance Criteria:**
- [ ] All real hospitals marked verified + visible
- [ ] No false positives in public data
- [ ] Verification workflow documented

**Estimated Time:** 5 hours

---

### Day 10: Multi-Province Testing & Polish

**Tasks:**
- [ ] End-to-end testing
  - [ ] Run all 3 scrapers multiple times
  - [ ] Verify no duplicates created
  - [ ] Check measurement counts are reasonable
  - [ ] Verify heartbeat updated for each scraper

- [ ] Add Ontario scraper (if time permits)
  - [ ] Ontario has good structured data
  - [ ] Adds 4th province for comparability matrix

- [ ] Update documentation
  - [ ] Document each scraper's ontology
  - [ ] Add troubleshooting guide
  - [ ] Update CLAUDE.md with learnings

- [ ] Set up scraper cron
  - [ ] Verify GitHub Actions workflow works
  - [ ] Enable 15-minute cron schedule
  - [ ] Monitor first few automated runs

**Acceptance Criteria:**
- [ ] 3+ provinces scraping successfully
- [ ] Automated cron running without failures
- [ ] Comparability logic generates correct briefs
- [ ] Documentation up to date

**Estimated Time:** 8 hours

---

### Week 2 Deliverables

- ✅ 3+ provincial scrapers with different methodologies
- ✅ Comparability logic working
- ✅ Verification queue functional
- ✅ Automated scraping every 15 minutes
- ✅ 500+ measurements in database

---

## Week 3: Frontend "Scholar" UI

**Goal:** Build interface that prioritizes truth and transparency

### Day 11: Next.js Project Setup

**Tasks:**
- [ ] Initialize Next.js project
  - [ ] `cd frontend && pnpm create next-app@latest .`
  - [ ] Choose: TypeScript, App Router, Tailwind CSS
  - [ ] Configure `tsconfig.json` for strict mode

- [ ] Install dependencies
  - [ ] Mapbox GL: `pnpm add mapbox-gl react-map-gl`
  - [ ] Supabase: `pnpm add @supabase/supabase-js`
  - [ ] React Query: `pnpm add @tanstack/react-query`
  - [ ] Zod: `pnpm add zod`
  - [ ] Date utilities: `pnpm add date-fns`

- [ ] Configure environment
  - [ ] Create `.env.local.example`
  - [ ] Add Supabase URL and anon key
  - [ ] Add Mapbox access token

- [ ] Set up project structure
  - [ ] Create `src/lib/` for utilities
  - [ ] Create `src/components/` for UI
  - [ ] Create `src/types/` for TypeScript types
  - [ ] Create `src/hooks/` for custom hooks

**Acceptance Criteria:**
- [ ] Next.js dev server runs: `pnpm dev`
- [ ] TypeScript strict mode enabled
- [ ] Can import Supabase client

**Estimated Time:** 4 hours

---

### Day 12: Data Layer & Type Safety

**Tasks:**
- [ ] Create TypeScript types
  - [ ] Create `src/types/index.ts`
  - [ ] Define all database types (Hospital, Measurement, Source, etc.)
  - [ ] Match PostgreSQL enums exactly

- [ ] Set up Supabase client
  - [ ] Create `src/lib/supabase.ts`
  - [ ] Initialize with anon key
  - [ ] Export typed client

- [ ] Create API functions
  - [ ] Create `src/lib/api.ts`
  - [ ] `fetchHospitals(province?: string)`
  - [ ] `fetchHospitalById(id: string)`
  - [ ] `fetchMeasurements(hospitalId: string, timeRange: string)`
  - [ ] `fetchScraperStatus()`

- [ ] Create React Query hooks
  - [ ] Create `src/hooks/useHospitals.ts`
  - [ ] Create `src/hooks/useMeasurements.ts`
  - [ ] Create `src/hooks/useHeartbeat.ts`
  - [ ] Configure caching (5 min stale time)

**Acceptance Criteria:**
- [ ] Can fetch hospitals from Supabase
- [ ] TypeScript autocomplete works
- [ ] React Query caching works

**Estimated Time:** 6 hours

---

### Day 13: Map Implementation

**Tasks:**
- [ ] Create Map component
  - [ ] Create `src/components/Map.tsx`
  - [ ] Initialize Mapbox with Canada center
  - [ ] Add hospital markers as GeoJSON
  - [ ] Enable clustering for dense areas

- [ ] Style hospital markers
  - [ ] Color by wait time (green < 2h, yellow < 4h, red > 4h)
  - [ ] Size by facility_type
  - [ ] Add hover tooltip

- [ ] Add map controls
  - [ ] Zoom in/out buttons
  - [ ] Geolocation button (find nearest hospital)
  - [ ] Province filter dropdown

- [ ] Create homepage layout
  - [ ] Create `src/app/page.tsx`
  - [ ] Full-screen map
  - [ ] Floating header with title
  - [ ] Sidebar for filters (collapsible on mobile)

**Acceptance Criteria:**
- [ ] Map loads with all verified hospitals
- [ ] Markers colored by wait time
- [ ] Clustering works in dense areas
- [ ] Mobile responsive

**Estimated Time:** 8 hours

---

### Day 14: Hospital Detail Modal

**Tasks:**
- [ ] Create HospitalCard component
  - [ ] Create `src/components/HospitalCard.tsx`
  - [ ] Modal/drawer that opens on marker click
  - [ ] Display hospital name, address, phone
  - [ ] Show latest wait time prominently

- [ ] Add ontology disclosure
  - [ ] Show metric_family, start_event, end_event, statistic_type
  - [ ] Explain what each means in plain language
  - [ ] Example: "Registration to Physician (Average)"

- [ ] Add Province-Aware Banner
  - [ ] Create `src/components/ProvinceAwareBanner.tsx`
  - [ ] Query `sources` table for telehealth info
  - [ ] Display: "For medical advice, call [Info-Santé 811]"
  - [ ] Different text per province

- [ ] Add time series chart (optional)
  - [ ] Use Recharts or Chart.js
  - [ ] Show last 24 hours of measurements
  - [ ] Display trend (increasing/decreasing)

**Acceptance Criteria:**
- [ ] Modal opens on marker click
- [ ] All hospital info displayed
- [ ] Province-specific telehealth shown
- [ ] Chart updates with real data

**Estimated Time:** 8 hours

---

### Day 15: Methodology Warning & Methods Page

**Tasks:**
- [ ] Implement comparability logic in frontend
  - [ ] Create `src/lib/comparability.ts`
  - [ ] Port Python logic to TypeScript
  - [ ] `areComparable(measurementA, measurementB)`

- [ ] Create MethodologyWarning component
  - [ ] Create `src/components/MethodologyWarning.tsx`
  - [ ] Show prominent warning when comparing incomparable data
  - [ ] Example: "⚠️ These hospitals use different methodologies"
  - [ ] Link to /methods page

- [ ] Create Methods page
  - [ ] Create `src/app/methods/page.tsx`
  - [ ] Display comparability matrix table
  - [ ] Show all provinces with their ontology signatures
  - [ ] Explain what makes data comparable
  - [ ] Link to official provincial methodology pages

- [ ] Add HeartbeatMonitor component
  - [ ] Create `src/components/HeartbeatMonitor.tsx`
  - [ ] Show "Last Audit: X mins ago"
  - [ ] Color code: green < 30min, yellow < 60min, red > 60min
  - [ ] Display in header

**Acceptance Criteria:**
- [ ] Warning shows when comparing AB vs QC
- [ ] Methods page explains ontology clearly
- [ ] Heartbeat monitor updates live
- [ ] All links work

**Estimated Time:** 8 hours

---

### Week 3 Deliverables

- ✅ Interactive map with hospital markers
- ✅ Hospital detail modal with wait times
- ✅ Province-aware telehealth directory
- ✅ Methodology divergence warnings
- ✅ /methods page with comparability matrix
- ✅ Heartbeat monitor showing scraper health
- ✅ Mobile responsive design

---

## Week 4: Polish & Launch

**Goal:** Professional finish and deployment

### Day 16: Access Burden Estimator

**Tasks:**
- [ ] Create AccessBurdenEstimator component
  - [ ] Create `src/components/AccessBurdenEstimator.tsx`
  - [ ] Collapsible accordion (hidden by default)
  - [ ] Input: user location (lat/long or postal code)
  - [ ] Calculate distance to hospital

- [ ] Add cost calculation
  - [ ] Distance × gas price per km
  - [ ] Add parking estimate (fetch from Google Places API or static)
  - [ ] Show total cost estimate

- [ ] Add disclaimer
  - [ ] Prominent: "Logistical estimate only. Never delay care for cost."
  - [ ] Link to telehealth as free alternative

**Acceptance Criteria:**
- [ ] Calculator works for test coordinates
- [ ] Disclaimer always visible
- [ ] Opt-in (not shown by default)

**Estimated Time:** 6 hours

---

### Day 17: Mobile Optimization

**Tasks:**
- [ ] Mobile UX improvements
  - [ ] Test on real mobile devices
  - [ ] Ensure touch targets are 44×44px minimum
  - [ ] Bottom sheet for hospital details (better than modal on mobile)
  - [ ] Swipe gestures for navigation

- [ ] Performance optimization
  - [ ] Add loading skeletons
  - [ ] Lazy load chart library
  - [ ] Optimize images (use Next.js Image)
  - [ ] Reduce initial bundle size

- [ ] Progressive Web App setup
  - [ ] Add manifest.json
  - [ ] Add service worker for offline map tiles (optional)
  - [ ] Add app icons

**Acceptance Criteria:**
- [ ] Lighthouse score: Performance > 90, Accessibility > 95
- [ ] Works offline (cached data)
- [ ] Installable as PWA

**Estimated Time:** 8 hours

---

### Day 18: Testing & Quality Assurance

**Tasks:**
- [ ] Write unit tests
  - [ ] Test comparability logic
  - [ ] Test API functions
  - [ ] Test utility functions
  - [ ] Target 80%+ coverage

- [ ] Write component tests
  - [ ] Test ProvinceAwareBanner shows correct info
  - [ ] Test MethodologyWarning displays for incomparable data
  - [ ] Test HeartbeatMonitor color coding

- [ ] Write E2E tests
  - [ ] Test map loads hospitals
  - [ ] Test clicking hospital opens modal
  - [ ] Test province filter works
  - [ ] Test /methods page loads

- [ ] Manual QA
  - [ ] Test all user flows
  - [ ] Check cross-browser (Chrome, Firefox, Safari)
  - [ ] Check accessibility (keyboard nav, screen reader)

**Acceptance Criteria:**
- [ ] All tests pass
- [ ] No console errors
- [ ] WCAG 2.1 AA compliance

**Estimated Time:** 8 hours

---

### Day 19: Documentation & Stakeholder Engagement

**Tasks:**
- [ ] Update documentation
  - [ ] Finalize README.md with screenshots
  - [ ] Update IMPLEMENTATION.md with lessons learned
  - [ ] Create user guide (how to read the data)

- [ ] Stakeholder interview
  - [ ] Reach out to 1 ER nurse or physician
  - [ ] Demo the site
  - [ ] Gather feedback on usability
  - [ ] Ask about data accuracy
  - [ ] Document feedback

- [ ] Content writing
  - [ ] Write About page
  - [ ] Write FAQ page
  - [ ] Write disclaimer/legal notice
  - [ ] Write data sources attribution

**Acceptance Criteria:**
- [ ] 1 stakeholder interviewed
- [ ] Feedback incorporated
- [ ] All content pages written

**Estimated Time:** 8 hours

---

### Day 20: Deployment & Launch

**Tasks:**
- [ ] Deploy to Vercel
  - [ ] Connect GitHub repo to Vercel
  - [ ] Configure environment variables
  - [ ] Deploy production build
  - [ ] Test production site

- [ ] Configure custom domain (optional)
  - [ ] Register domain (e.g., waittimecanada.ca)
  - [ ] Configure DNS
  - [ ] Enable SSL

- [ ] Final checks
  - [ ] Verify all scrapers running
  - [ ] Verify data is current
  - [ ] Check heartbeat monitor
  - [ ] Test on multiple devices

- [ ] Launch communications
  - [ ] Write LinkedIn post (physician-innovator narrative)
  - [ ] Share on relevant healthcare forums
  - [ ] Submit to Canadian health tech communities

- [ ] Set up monitoring
  - [ ] Configure Sentry for error tracking
  - [ ] Set up Vercel Analytics
  - [ ] Configure email alerts for downtime

**Acceptance Criteria:**
- [ ] Site live at production URL
- [ ] All features working
- [ ] Monitoring configured
- [ ] Launch post published

**Estimated Time:** 8 hours

---

### Week 4 Deliverables

- ✅ Access Burden Estimator feature
- ✅ Mobile-optimized design
- ✅ Full test coverage
- ✅ Stakeholder validation
- ✅ Production deployment
- ✅ Public launch

---

## Post-Launch (Week 5+)

### Immediate Follow-Up

- [ ] Monitor error rates (Sentry)
- [ ] Track usage metrics (Vercel Analytics)
- [ ] Respond to user feedback
- [ ] Fix any critical bugs within 24 hours

### Future Enhancements

**Phase 2: Advanced Features**
- [ ] Historical trends (30-day, 90-day charts)
- [ ] Email/SMS alerts when wait time drops below threshold
- [ ] Equity layer (income shapefiles overlay)
- [ ] Predictive modeling (ML for wait time forecasts)

**Phase 3: Scale**
- [ ] Add remaining provinces (BC, ON, NS, etc.)
- [ ] Add urgent care centers
- [ ] Add walk-in clinics
- [ ] Public API for researchers

**Phase 4: Sustainability**
- [ ] Apply for grants (CIHR, NSERC)
- [ ] Partner with provincial health authorities
- [ ] Present at conferences (CAEP, CSHP)
- [ ] Publish methodology paper

---

## Risk Mitigation Checklist

### Technical Risks

- [ ] **Scraper Failure:** Heartbeat monitor + email alerts configured
- [ ] **Data Corruption:** Idempotency enforced + database constraints
- [ ] **Performance Issues:** Indexes created + query optimization
- [ ] **Security Breach:** RLS policies + environment secrets

### Product Risks

- [ ] **Misinterpretation:** Methodology warnings everywhere
- [ ] **Liability:** Disclaimers + telehealth directory (no medical advice)
- [ ] **Scope Creep:** Strict feature freeze after Week 3

### Execution Risks

- [ ] **Timeline Slip:** Daily progress tracking, cut scope if needed
- [ ] **Burnout:** Build in buffer time, Week 4 Day 19-20 are lighter

---

## Success Metrics

### Technical Metrics
- Scraper uptime: > 95%
- Database query time: < 100ms (p95)
- Frontend Lighthouse score: > 90
- Test coverage: > 80%

### Product Metrics
- Hospital coverage: 50+ facilities across 3+ provinces
- Data freshness: < 30 minutes old
- User engagement: > 100 unique visitors in Week 1
- Stakeholder validation: Positive feedback from 1+ healthcare professional

### Portfolio Metrics
- LinkedIn post engagement: > 50 reactions
- GitHub stars: > 10 stars
- Code quality: All CI/CD passing
- Documentation: Complete and accurate

---

## Daily Stand-Up Template

**What I did yesterday:**
- [ ] List completed tasks

**What I'm doing today:**
- [ ] List planned tasks

**Blockers:**
- [ ] Any issues preventing progress

**Risks:**
- [ ] Emerging risks or concerns

---

## When Things Go Wrong

### Scraper Breaks
1. Check GitHub Actions logs
2. Verify source website hasn't changed HTML structure
3. Update parser logic
4. Add test fixture for new format
5. Deploy fix

### Database Migration Fails
1. **DO NOT** re-run automatically
2. Review error message
3. Test migration locally
4. Fix SQL syntax
5. Create new migration (never edit existing)
6. Document in CHANGELOG

### Frontend Bug in Production
1. Check Sentry for stack trace
2. Reproduce locally
3. Create hotfix branch
4. Test thoroughly
5. Deploy via Vercel
6. Monitor for 1 hour

### Time Running Out
**Priority Order:**
1. Database + Quebec scraper (Week 1)
2. Alberta/Manitoba scrapers (Week 2)
3. Map + hospital details (Week 3)
4. Methods page (Week 3)
5. Access burden estimator (Week 4 - CAN BE CUT)
6. Equity layer (Week 4 - CAN BE CUT)

---

## Final Notes

This roadmap is intentionally detailed to maximize execution speed. Feel free to adjust based on:
- Real-world constraints (data availability, API changes)
- Personal strengths (if you're a frontend expert, spend less time on Week 3)
- Portfolio priorities (if Week 4 features don't add narrative value, cut them)

**Remember:** The goal is not perfection, but demonstrable competency across:
- **Scholar:** Comparability logic and methods page
- **Professional:** Province-aware telehealth directory
- **Advocate:** Access burden estimator (optional)
- **Leader:** Heartbeat monitoring and system resilience

Good luck! 🚀
