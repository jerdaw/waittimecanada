# Implementation Roadmap

## Current Status (Updated 2026-02-04)

**Progress:** Milestone 8 (UX Enhancements) Complete ✓

**Recently Completed:**
- ✅ Aesthetic Refinement: Clean, spacious "Hero" landing page
- ✅ Layout Optimization: High-density "Scrolled" view for list/map
- ✅ Default Sorting: Enforced distance-based sorting (removed alphabetical override)
- ✅ Codebase Maintenance: Fixing Vitest/Playwright conflicts, symlink fixing
- ✅ Documentation Audit: ADRs updated and attribution verified

**Next Milestones:**
- **Milestone 9:** Portfolio-Ready Launch (MUST-DO before submission)
- **Milestone 10:** Multi-Province Expansion (Alberta/BC scrapers)
- **Milestone 11:** Access & Equity Features (Burden Estimator, Equity Layer)
- **Milestone 12:** Research Infrastructure (Citation export, Alerts, Occupancy)

---

## Strategic Context: Admissions Committee Appeal

Each feature maps to CanMEDS competencies that medical school admissions committees value:

| Competency | Features That Demonstrate It |
|------------|------------------------------|
| **Scholar** | Metric ontology, comparability matrix, citation export, methodology transparency |
| **Professional** | Clinical defensibility, divergence warnings, verification queue, data stewardship |
| **Health Advocate** | Access Burden Estimator, equity layer, socioeconomic overlays |
| **Leader** | Multi-province scaling, systems architecture, stakeholder engagement |
| **Collaborator** | Province-aware telehealth routing, stakeholder interviews, testimonials |

**Key Differentiators vs Competitors (e.g., ER Watch):**
1. We audit data, not just aggregate it
2. We expose methodology inconsistencies instead of hiding them
3. We provide clinical defensibility through the metric ontology
4. We think at the pan-Canadian system level

---

## Milestone Summary & Timeline

| Milestone | Priority | Est. Days | Key Deliverables | Admissions Appeal |
|-----------|----------|-----------|------------------|-------------------|
| **M9: Portfolio Launch** | CRITICAL | 3-4 | Live URL, About section, stakeholder interview, LinkedIn post | Leader, Collaborator |
| **M10: Multi-Province** | HIGH | 4-5 | Alberta scraper, province filter, cross-province warnings | Scholar, Leader |
| **M11: Equity Features** | HIGH | 5-6 | Access Burden Estimator, income overlay, equity insights | Health Advocate |
| **M12: Research Infra** | MEDIUM | 3-4 | Citation export, heartbeat alerts, API docs | Scholar, Leader |

**Recommended Order:** M9 → M10 → M11 → M12

**Total Estimated Effort:** 15-19 days

### Implementation Plans

Each milestone has a detailed implementation plan:
- `docs/planning/implementation/milestone-9-launch.md` - Production deployment & stakeholder validation
- `docs/planning/implementation/milestone-10-provinces.md` - Alberta scraper & multi-province support
- `docs/planning/implementation/milestone-11-equity.md` - Access Burden Estimator & equity layer
- `docs/planning/implementation/milestone-12-research.md` - Citation export & alert system

---

## Milestone Progress

### ✅ Milestone 1: Database Foundation (Week 1)
**Status:** Complete

**What We Built:**
- PostgreSQL schema with strict ontology enums
- `sources`, `hospitals`, `measurements`, `scraper_status` tables
- Row-Level Security (RLS) policies
- Quebec scraper (HTML table parsing)
- Database service with psycopg2
- CLI tool: `python -m waittime.cli.scraper`

**Deliverables:**
- 5 database tables with constraints
- Quebec scraper running successfully
- Heartbeat monitoring system
- 50+ Quebec measurements in database
- All tests passing

---

### ✅ Milestone 2: Ontario End-to-End (Partial Week 2 + Week 3)
**Status:** Complete

**What We Built:**
- Ontario scraper using Playwright for JavaScript-rendered HQOntario site
- Geocoding service using OpenStreetMap Nominatim (free, no API key)
  - Falls back to Mapbox if Nominatim fails
  - Rate-limited to 1 req/sec per Nominatim policy
- Automated hospital data collection via systematic research
- Import scripts for bulk hospital data
- Next.js frontend with:
  - Interactive Mapbox map
  - Hospital markers color-coded by wait time
  - API endpoint using postgres.js
  - 160 verified Ontario hospitals

**Key Technical Decisions:**
1. **Geocoding Strategy:** Used systematic research to gather city names, then Nominatim for coordinates (fully automated, $0 cost)
2. **Database Client Split:** Backend uses psycopg2, frontend uses postgres.js (both connect directly to Neon)
3. **Playwright for Dynamic Content:** HQOntario uses JavaScript rendering, BeautifulSoup insufficient

**Files Created:**
- `backend/src/waittime/scrapers/ontario.py` - HQOntario scraper
- `backend/src/waittime/services/geocoding.py` - Geocoding service
- `backend/scripts/import_hospitals.py` - Geocoding script
- `backend/scripts/import_hospitals_to_db.py` - Database import
- `frontend/components/Map.tsx` - Interactive map
- `frontend/app/api/hospitals/route.ts` - Hospital API
- `docs/hospitals-geocoded.csv` - 154 geocoded hospitals

**Deliverables:**
- Ontario scraper parsing 154 hospitals
- All 160 hospitals geocoded with valid coordinates
- Frontend map displaying all hospitals
- Color-coded markers (green/yellow/red by wait time)

---

### ✅ Milestone 3: Multi-Province & Methodology Warnings (Week 2)
**Status:** In Progress

**Planned Work:**
- [ ] Add Alberta scraper (different `start_event=TRIAGE`)
- [ ] Add Manitoba scraper (different `statistic_type=ALGORITHMIC`)
- [ ] Implement comparability logic in frontend
- [x] Build MethodologyWarning component (DivergenceWarning.tsx)
- [x] Create /methods page with comparability matrix
- [x] Hospital detail modal with ontology disclosure (Integrated in Map)

**Goal:** Demonstrate heterogeneity in provincial methodologies

---

### ✅ Milestone 4: Polish & Launch (Week 4)
**Status:** Complete

**Completed Work:**
- [x] 911 Emergency Banner & Dark Mode
- [x] Split View Layout (List + Map)
- [x] Historical Trend Charts (24h/7d/30d)
- [x] Hero Section with Live Preview
- [x] Mobile optimization and PWA setup (Manifest, Service Worker)
- [x] Testing (unit, component, E2E)
- [ ] Access Burden Estimator (Deferred)
- [ ] Stakeholder interview (1 ER nurse/physician)
- [ ] Production deployment to Vercel

**Goal:** Professional finish and public launch

---

### ✅ Milestone 7: UX Polish & SEO
**Status:** Complete

**Work Completed:**
- [x] FAQPage schema.org structured data for rich snippets
- [x] MedicalWebPage schema for healthcare classification
- [x] Organization schema with data source attribution
- [x] Geographic meta tags (geo.region, geo.placename, geo.position)
- [x] OpenGraph/Twitter card metadata enhancements
- [x] HowTo schema for hospital search usage guide
- [x] Skeleton loading components (HospitalCardSkeleton, HeroSkeleton)
- [x] Real-time hospital search/filter in list view
- [x] "Near Me" sorting with browser geolocation integration
- [x] Pulsing live indicators for data updated < 30m ago
- [x] Distance display (km/m) when location access granted
- [x] Auto-geolocation with server-side IP fallback

**Goal:** Improve discoverability via SEO and polish loading/search UX

---

### ✅ Milestone 8: UX Enhancements (Inspired by Market Leaders)
**Status:** Complete
**Reference:** Analysis document in `docs/planning/competitor-design-analysis.md`

**Phase 1: Expandable Hospital Cards (High Priority)**
- [x] Independent expand/collapse state for hospital cards
- [x] Expanded view shows methodology, last updated, telehealth info
- [x] Quick action buttons (Directions, Website, Call)
- [x] Chevron icon with rotation animation
- [x] Smooth height transition

**Phase 2: FAQ Page (High Priority)**
- [x] Create `/faq` route with accordion UI
- [x] Add common questions about wait times and methodology
- [x] Link to /methods for deeper info
- [x] FAQPage schema.org structured data for SEO
- [x] Add FAQ link to navigation header

**Phase 3: Quick Actions & Polish (Medium Priority)**
- [x] Quick action buttons in map popup (Directions, Call, Website)
- [x] "Live Data Only" toggle filter
- [x] Hospital count with live data subset

**Phase 4: Aesthetic Refinement & High-Density Layout**
- [x] Clean, spacious "Hero" landing page with background textures
- [x] Responsive "Scrolled" layout (traditional landing page flow)
- [x] Distance-based auto-sorting (removed manual alphabetical override)
- [x] Tighter vertical spacing for higher information density in app view
- [x] Faint dot grid textures for visual depth

**Goal:** Improve user experience with quick access to hospital details and modern "landing page" feel

---

### 🎯 Milestone 9: Portfolio-Ready Launch (CRITICAL)
**Status:** Not Started
**Priority:** MUST-DO before portfolio submission
**Estimated Effort:** 3-4 days
**Implementation Plan:** `docs/planning/implementation/milestone-9-launch.md`

This milestone ensures the project is presentable for medical school applications.

**Phase 1: Production Deployment**
- [ ] Deploy frontend to Render/Vercel with production DATABASE_URL
- [ ] Configure GitHub Actions for automated scraper runs (15-min cron)
- [ ] Set up Pushover/email alerts for heartbeat failures ("Dead Man's Switch")
- [ ] Verify all environment variables in production
- [ ] Test production site end-to-end

**Phase 2: About/Story Section**
- [ ] Add "About This Project" section to homepage (collapsible or dedicated route)
- [ ] Write physician-innovator narrative (why I built this)
- [ ] Add author bio with photo placeholder
- [ ] Link to LinkedIn/GitHub profiles
- [ ] Ensure story is visible without navigating away from main page

**Phase 3: Stakeholder Validation**
- [ ] Contact 1-2 ER nurses/physicians for 15-minute interview
- [ ] Prepare interview questions (methodology usefulness, UI feedback)
- [ ] Document feedback and incorporate suggestions
- [ ] Request testimonial quote for site (optional but high-value)
- [ ] Add testimonial section if obtained

**Phase 4: Launch Materials**
- [ ] Finalize LinkedIn launch post (draft exists in `docs/linkedin-launch-post.md`)
- [ ] Create 2-3 screenshots for social sharing
- [ ] Write GitHub repo description and topics
- [ ] Prepare 1-paragraph summary for applications

**Deliverables:**
- Live production URL
- "About" section with personal narrative
- At least 1 stakeholder interview documented
- LinkedIn post ready to publish
- Portfolio-ready screenshots

---

### 🎯 Milestone 10: Multi-Province Expansion
**Status:** Not Started
**Priority:** HIGH (proves methodology heterogeneity)
**Estimated Effort:** 4-5 days
**Implementation Plan:** `docs/planning/implementation/milestone-10-provinces.md`

This milestone proves the metric ontology works across provinces with different methodologies.

**Phase 1: Alberta Scraper**
- [ ] Research Alberta Health Services ER wait time portal
- [ ] Document Alberta's methodology (expected: `start_event=TRIAGE`, different from Quebec)
- [ ] Create `backend/src/waittime/scrapers/alberta.py`
- [ ] Add Alberta source to `sources` table with correct ontology tags
- [ ] Geocode Alberta hospitals (Nominatim pipeline)
- [ ] Write unit tests for Alberta scraper
- [ ] Verify divergence warnings trigger when comparing AB vs QC

**Phase 2: British Columbia Scraper (Optional)**
- [ ] Research BC ER wait time availability
- [ ] Document BC methodology if different from AB/ON
- [ ] Create scraper if data is accessible
- [ ] Add to sources table

**Phase 3: Frontend Updates**
- [ ] Add province filter dropdown to hospital list
- [ ] Update map to show multi-province data
- [ ] Ensure methodology cards on /methods page auto-populate from sources table
- [ ] Test cross-province comparison warnings

**Deliverables:**
- Alberta scraper running with correct ontology tags
- 50+ Alberta hospitals in database
- Divergence warnings working for AB vs QC/ON comparisons
- Province filter in UI
- Updated comparability matrix

---

### 🎯 Milestone 11: Access & Equity Features
**Status:** Not Started
**Priority:** HIGH (strongest "Health Advocate" features)
**Estimated Effort:** 5-6 days
**Implementation Plan:** `docs/planning/implementation/milestone-11-equity.md`

These features demonstrate awareness of healthcare access barriers.

**Phase 1: Access Burden Estimator**
- [ ] Design collapsible "Planning Lens" UI component
- [ ] Implement distance calculation (already have user location)
- [ ] Add gas price estimate (static provincial averages or API)
- [ ] Add parking cost field (manual input or hospital-specific defaults)
- [ ] Calculate total: `(Distance × Gas Price) + Parking`
- [ ] Add prominent disclaimer: "Logistical estimate only. Never delay care for cost."
- [ ] Write tests for calculation logic
- [ ] Add ADR documenting design decisions

**Phase 2: Equity Layer (Socioeconomic Overlays)**
- [ ] Research available Canadian socioeconomic shapefiles (StatsCan census data)
- [ ] Download income/deprivation index data by census tract
- [ ] Create Mapbox tileset or GeoJSON layer
- [ ] Add toggle: "Show Income Overlay"
- [ ] Color-code areas by income quintile
- [ ] Add legend explaining the overlay
- [ ] Write documentation explaining the equity analysis purpose

**Phase 3: Access Insights**
- [ ] Create summary statistics: "X hospitals within 30km of low-income areas"
- [ ] Add to /methods or new /insights page
- [ ] Document methodology for equity analysis

**Deliverables:**
- Working Access Burden Estimator with disclaimer
- Socioeconomic overlay on map
- Equity insights summary
- ADR for equity feature design

---

### 🎯 Milestone 12: Research Infrastructure
**Status:** Not Started
**Priority:** MEDIUM (enhances "Scholar" narrative)
**Estimated Effort:** 3-4 days
**Implementation Plan:** `docs/planning/implementation/milestone-12-research.md`

These features position the project as research infrastructure, not just a consumer app.

**Phase 1: Citation-Ready Data Export**
- [ ] Create `/api/export` endpoint with query params (province, date range)
- [ ] Return CSV with all methodology tags included
- [ ] Add citation format suggestion in download
- [ ] Create "Download Data" button on /methods page
- [ ] Add terms of use for data (attribution required)
- [ ] Document API in `docs/API.md`

**Phase 2: Dead Man's Switch Alerts**
- [ ] Enhance heartbeat monitoring in scraper_status table
- [ ] Create GitHub Action that checks heartbeat age
- [ ] If heartbeat > 60 minutes, send Pushover notification
- [ ] Add "System Status" indicator to footer (green/yellow/red)
- [ ] Create `/api/health` endpoint for monitoring

**Phase 3: Occupancy Statistics (If Data Available)**
- [ ] Research if Ontario Health provides "patients waiting" / "in treatment" counts
- [ ] If available, add to scraper and measurements table
- [ ] Display as pills in hospital cards: "14 waiting | 26 in treatment"
- [ ] Add velocity context: "ER clearing fast" vs "ER backing up"

**Phase 4: Proactive Notifications (Future)**
- [ ] Design notification system architecture
- [ ] Create user preference storage (local or authenticated)
- [ ] Implement threshold-based alerts ("Toronto General > 4h")
- [ ] Add email/push notification delivery

**Deliverables:**
- CSV export with methodology tags
- Working heartbeat alerts
- System status indicator
- Occupancy stats (if data available)

---

## Implementation Details

### Database Schema

**Core Tables:**
1. **sources** - Provincial data source metadata
2. **hospitals** - Facility locations with verification workflow
3. **measurements** - Audit log of all scraped wait times
4. **scraper_status** - Heartbeat monitoring
5. **users** - (Future) for saved preferences

**Ontology Enums:**
- `metric_family`: TIME_TO_PROVIDER, TOTAL_LOS, STRETCHER_OCCUPANCY
- `start_event`: TRIAGE, REGISTRATION, DOOR, UNKNOWN
- `end_event`: PHYSICIAN, PROVIDER, DISCHARGE, FIRST_ASSESSMENT
- `statistic_type`: POINT_ESTIMATE, P90, ALGORITHMIC, ROLLING_AVG, MEAN
- `patient_scope`: ALL, MID_ACUITY, NON_PRIORITY

### Scraper Architecture

**Base Pattern:**
```python
class BaseScraper(ABC):
    @abstractmethod
    async def fetch(self) -> str:
        """Fetch raw HTML/JSON from source"""

    @abstractmethod
    def parse(self, content: str) -> list[Measurement]:
        """Parse content into measurements"""

    def run(self):
        """Orchestrate: fetch → parse → save → heartbeat"""
```

**Ontario Scraper Notes:**
- Uses Playwright for JavaScript rendering
- Filters out YYYYMM date values (regex: `^\d{6}$`)
- Creates placeholder hospitals with `is_verified=FALSE`
- Ontology: `TIME_TO_PROVIDER | TRIAGE | PHYSICIAN | MEAN | ALL`

**Quebec Scraper Notes:**
- Uses BeautifulSoup (static HTML table)
- 3 parsing strategies for different table structures
- Ontology: `TIME_TO_PROVIDER | REGISTRATION | PHYSICIAN | ROLLING_AVG | ALL`

### Geocoding Strategy

**Problem:** HQOntario only provides hospital names, not addresses or coordinates.

**Solution:** Multi-stage geocoding pipeline
1. **Data Collection:** Used systematic research to gather city names and addresses for all 154 Ontario hospitals
2. **Geocoding:** Nominatim API with query: `"{address}, {city}, Ontario, Canada"`
3. **Fallback:** For 3 failed lookups, used city centroids
4. **Cost:** $0 (Nominatim is free, Mapbox only for optional fallback)

**Rate Limiting:** 1 request/second per Nominatim usage policy

### Frontend Architecture

**Stack:**
- Next.js 14 (App Router)
- Mapbox GL JS for map rendering
- postgres.js for direct database access
- TypeScript strict mode

**Key Components:**
- `Map.tsx` - Interactive map with hospital markers
- `HospitalCard.tsx` - (Planned) Modal with wait time details
- `MethodologyWarning.tsx` - (Planned) Incomparable data warning
- `ProvinceAwareBanner.tsx` - (Planned) Telehealth directory

**Environment Variables:**
- `DATABASE_URL` - Neon PostgreSQL connection string
- `NEXT_PUBLIC_MAPBOX_TOKEN` - Mapbox access token (50k free loads/month)

---

## Risk Register

### Resolved Risks

**✅ Geocoding Accuracy**
- **Risk:** Manual coordinate lookup for 154 hospitals
- Mitigation: Automated via systematic research + Nominatim API
- **Status:** Resolved (151/154 geocoded accurately, 3 use city centroids)

**✅ JavaScript Rendering Detection**
- **Risk:** BeautifulSoup can't parse HQOntario page
- **Mitigation:** Switched to Playwright for browser automation
- **Status:** Resolved (scraper working)

**✅ Hospital Verification Workflow**
- **Risk:** Auto-publishing incorrect facilities
- **Mitigation:** `is_verified=FALSE` by default, manual approval required
- **Status:** Resolved (verification gate in place)

### Active Risks

**⚠️ Mapbox Cost Overrun**
- **Risk:** Free tier only allows 50k map loads/month
- **Mitigation:** Monitor usage, implement caching, consider self-hosted tiles
- **Status:** Monitoring (unlikely for portfolio project)

**⚠️ Silent Scraper Failure**
- **Risk:** Scraper breaks, no one notices for days
- **Mitigation:** Heartbeat monitor + frontend display "Last Audit: X mins ago"
- **Status:** Partially implemented (heartbeat exists, frontend display pending)

**⚠️ Data Misinterpretation**
- **Risk:** Users compare incomparable methodologies
- **Mitigation:** Methodology warnings everywhere, /methods page
- **Status:** Not yet implemented (Milestone 3)

---

## Testing Strategy

### Current Coverage
- 24 unit tests passing
- 56% code coverage
- Test files:
  - `tests/unit/test_models.py` - Pydantic model validation
  - `tests/unit/test_ontario_scraper.py` - Ontario scraper parsing
  - `tests/unit/test_quebec_scraper.py` - Quebec scraper parsing

### Planned Tests
- Component tests for React components
- E2E tests with Playwright (CI only, not local)
- Integration tests for database operations
- Geocoding service tests

### Test Guidelines
- Follow `testing-guidelines.md`
- Do NOT run Playwright tests locally (CI only)
- Target 80%+ coverage before launch

---

## Documentation Structure

### Completed
- ✅ `README.md` - Project overview and setup
- ✅ `AGENTS.md` - Agent instructions with security rules
- ✅ `docs/planning/roadmap.md` - This file
- ✅ `docs/geocoding-research-plan.md` - Systematic research plan

### Planned
- [ ] `docs/ARCHITECTURE.md` - System design decisions
- [ ] `docs/METHODOLOGY.md` - Ontology explanation for users
- [ ] `docs/API.md` - Public API documentation
- [ ] ADRs for major decisions (geocoding, Playwright, etc.)

---

## Timeline Adjustments

**Original Plan:** 4 weeks (20 working days)

**Actual Progress:**
- Week 1: Database Foundation ✓ (5 days)
- Week 2-3: Ontario End-to-End ✓ (partial, 3 days)
  - Geocoding took longer than expected due to data collection
  - Frontend foundation complete, but details pending

**Revised Timeline:**
- Week 4: Multi-province scrapers + methodology warnings
- Week 5: Polish, testing, deployment
- Week 6: Launch

---

## Success Metrics

### Technical Metrics (Current)
- ✅ Scraper uptime: 100% (manual runs only)
- ✅ Database query time: < 50ms (tested manually)
- ⏳ Frontend Lighthouse score: Not yet measured
- ✅ Test coverage: 56% (target 80%)

### Product Metrics (Current)
- ✅ Hospital coverage: 160 Ontario hospitals
- ⏳ Data freshness: No automated scraping yet
- ⏳ User engagement: Not launched
- ⏳ Stakeholder validation: Not yet contacted

### Portfolio Metrics (Target)
- GitHub stars: > 10
- LinkedIn post engagement: > 50 reactions
- Code quality: All CI/CD passing
- Documentation: Complete and accurate

---

## Next Session Priorities

### Immediate (Milestone 9 - Portfolio Launch)
1. **Production Deployment** - Get live URL working
2. **About Section** - Add physician-innovator narrative to UI
3. **Stakeholder Interview** - Contact ER nurse/physician
4. **LinkedIn Post** - Finalize and publish

### Short-Term (Milestone 10 - Multi-Province)
5. **Alberta Scraper** - Research and implement
6. **Province Filter** - Add UI dropdown
7. **Cross-Province Warnings** - Verify divergence detection

### Medium-Term (Milestone 11 - Equity)
8. **Access Burden Estimator** - Distance + cost calculation
9. **Equity Layer** - Socioeconomic overlays

### Backlog (Milestone 12 - Research)
10. **Citation Export** - CSV with methodology tags
11. **Heartbeat Alerts** - Pushover notifications
12. **Occupancy Stats** - If data available

---

## Quick Start for New Sessions

```bash
# 1. Check current milestone status
cat docs/planning/roadmap.md | head -100

# 2. Read the implementation plan for current milestone
cat docs/planning/implementation/milestone-9-launch.md

# 3. Run tests to verify everything works
cd backend && pytest tests/ -v
cd frontend && npm run test:unit
```

---

## Lessons Learned

### What Went Well
- Nominatim geocoding worked perfectly (151/154 accurate)
- Systematic research was faster than manual data entry
- Playwright handled JavaScript rendering seamlessly
- Database schema design upfront avoided refactoring

### What Could Be Improved
- Should have checked HQOntario rendering earlier
- Geocoding service has indentation errors (needs cleanup)
- Frontend/backend environment variable separation could be clearer

### Technical Debt
- `geocoding.py` has indentation errors (not blocking)
- No retry logic for database writes yet
- Frontend needs error boundaries
- Tests need expansion (only 56% coverage)

---

## Dependencies & Integrations

### External Services (Free Tier)
- **Neon PostgreSQL** - Database hosting (512 MB free)
- **Mapbox** - Map tiles (50k loads/month free)
- **Nominatim (OSM)** - Geocoding (1 req/sec, no key required)
- **Vercel** - Frontend hosting (planned)
- **GitHub Actions** - CI/CD (2000 min/month free)

### Optional Paid Services (Not Used Yet)
- Mapbox Geocoding API - Backup if Nominatim fails
- Sentry - Error tracking (future)
- Vercel Analytics - Usage metrics (future)

---

## References

- Main specification: `er-times-plan.md` (deleted, content integrated here)
- AGENTS.md: Agent instructions with security rules
- Database migrations: `backend/database/migrations/`
- Test suite: `backend/tests/`
