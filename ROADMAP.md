# WaitTime Canada - Project Roadmap

> **Philosophy:** Vertical slices, not horizontal layers. Each milestone delivers working, shippable functionality.

**Last Updated:** 2026-01-30
**Approach:** Iterative development, one province at a time
**Current Phase:** Milestone 1 (Infrastructure) ✓ → Milestone 2 (Ontario End-to-End)

---

## Milestones Overview

| # | Milestone | Status | Description |
|---|-----------|--------|-------------|
| 1 | Infrastructure | ✅ Complete | Repository, database, core models |
| 2 | Ontario End-to-End | 🎯 **Current** | First province: scraper → database → frontend |
| 3 | Production Deployment | ⏳ Pending | GitHub Actions cron, Vercel frontend |
| 4 | Quebec Expansion | ⏳ Pending | Second province with methodology divergence |
| 5 | Polish & Launch | ⏳ Pending | Verification UI, methods page, documentation |

---

## Milestone 1: Infrastructure ✅

**Goal:** Foundation for all future development
**Status:** Complete (2026-01-30)

### Completed Tasks

- [x] **1.1** Initialize git repository with proper structure
- [x] **1.2** Modernize to `backend/src/waittime/` package layout
- [x] **1.3** Create Neon PostgreSQL database
- [x] **1.4** Run schema migrations (enums, tables, functions)
- [x] **1.5** Seed 5 provincial sources
- [x] **1.6** Implement core models with Pydantic validation
- [x] **1.7** Create DatabaseService with psycopg2
- [x] **1.8** Build BaseScraper abstract class
- [x] **1.9** Implement Quebec scraper MVP (template for others)
- [x] **1.10** Write unit tests (24 passing, 56% coverage)
- [x] **1.11** Create CLI tool (`python -m waittime.cli.scraper`)
- [x] **1.12** Document expansion strategy

**Artifacts:**
- `backend/` - Python package with scrapers, services, CLI
- `backend/migrations/` - 5 SQL migration files
- `backend/tests/` - Unit test suite
- `.env.local` - Database connection (gitignored)
- `docs/planning/expansion-roadmap.md` - Provincial strategy

---

## Milestone 2: Ontario End-to-End 🎯

**Goal:** First complete vertical slice - Ontario data visible on a map
**Status:** In Progress
**Success Criteria:** See Ontario hospital wait times on a live webpage

### Phase 2A: Ontario Scraper

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 2.1 | Research Ontario health portal URL and data format | 1h | ⬜ |
| 2.2 | Document Ontario methodology (start_event, statistic_type) | 30m | ⬜ |
| 2.3 | Create `scrapers/ontario.py` with hospital mappings | 2h | ⬜ |
| 2.4 | Implement parsing strategy (table/JSON/API) | 2h | ⬜ |
| 2.5 | Write unit tests (>80% coverage) | 2h | ⬜ |
| 2.6 | Test with dry-run mode | 30m | ⬜ |

**Acceptance:** `python -m waittime.cli.scraper --source ontario-health --dry-run` shows parsed data

**Dependencies:** Milestone 1 ✓

---

### Phase 2B: Data Pipeline

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 2.7 | Run Ontario scraper with real URL | 30m | ⬜ |
| 2.8 | Verify measurements in database | 30m | ⬜ |
| 2.9 | Add 5 Ontario hospitals to database (verified) | 30m | ⬜ |
| 2.10 | Verify heartbeat monitoring works | 15m | ⬜ |

**Acceptance:** Query returns Ontario measurements from database

**Dependencies:** 2.1-2.6 ✓

---

### Phase 2C: Minimal Frontend

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 2.11 | Initialize Next.js 14 project in `frontend/` | 30m | ⬜ |
| 2.12 | Install Mapbox GL JS | 30m | ⬜ |
| 2.13 | Create basic map component centered on Ontario | 1h | ⬜ |
| 2.14 | Create API route to fetch hospitals from Neon | 1h | ⬜ |
| 2.15 | Display hospitals as map markers | 1h | ⬜ |
| 2.16 | Show popup with wait time on marker click | 1h | ⬜ |
| 2.17 | Display methodology tags in popup | 30m | ⬜ |
| 2.18 | Add "Last updated" timestamp | 30m | ⬜ |

**Acceptance:** Can open browser and see Ontario hospitals with wait times

**Dependencies:** 2.7-2.10 ✓

---

### Phase 2D: Local Validation

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 2.19 | Run scraper manually 5 times, verify consistency | 30m | ⬜ |
| 2.20 | Verify frontend updates when new data arrives | 30m | ⬜ |
| 2.21 | Test error handling (what if scraper fails?) | 30m | ⬜ |
| 2.22 | Document any Ontario-specific quirks | 30m | ⬜ |

**Acceptance:** System works reliably in local development

**Dependencies:** 2.11-2.18 ✓

---

## Milestone 3: Production Deployment

**Goal:** Automated scraping and public frontend
**Status:** Pending
**Success Criteria:** System runs unattended, accessible via public URL

### Phase 3A: Backend Deployment

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 3.1 | Add DATABASE_URL secret to GitHub repository | 15m | ⬜ |
| 3.2 | Update GitHub Actions workflow for Ontario only | 30m | ⬜ |
| 3.3 | Enable 15-minute cron schedule | 15m | ⬜ |
| 3.4 | Test workflow with manual trigger | 30m | ⬜ |
| 3.5 | Monitor first 24 hours for errors | - | ⬜ |

**Acceptance:** Ontario scraper runs automatically every 15 minutes

**Dependencies:** Milestone 2 ✓

---

### Phase 3B: Frontend Deployment

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 3.6 | Create Vercel account (if needed) | 15m | ⬜ |
| 3.7 | Connect GitHub repository to Vercel | 15m | ⬜ |
| 3.8 | Configure environment variables (Neon, Mapbox) | 15m | ⬜ |
| 3.9 | Deploy to Vercel | 15m | ⬜ |
| 3.10 | Verify public URL works | 15m | ⬜ |

**Acceptance:** Can access site via public Vercel URL

**Dependencies:** 3.1-3.5 ✓

---

### Phase 3C: Monitoring

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 3.11 | Set up GitHub Actions failure notifications | 30m | ⬜ |
| 3.12 | Add heartbeat stale check (>60 min alert) | 30m | ⬜ |
| 3.13 | Create simple status page / health check endpoint | 1h | ⬜ |
| 3.14 | Monitor for 7 days, fix any issues | - | ⬜ |

**Acceptance:** 7 days of stable operation (>95% success rate)

**Dependencies:** 3.6-3.10 ✓

---

## Milestone 4: Quebec Expansion

**Goal:** Demonstrate methodology divergence with cross-border comparison
**Status:** Pending
**Success Criteria:** Ottawa vs Gatineau comparison shows divergence warning

### Phase 4A: Quebec Scraper Fixes

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 4.1 | Find real Quebec health portal URL | 1h | ⬜ |
| 4.2 | Update Quebec scraper for actual HTML structure | 2h | ⬜ |
| 4.3 | Update unit tests | 1h | ⬜ |
| 4.4 | Test with dry-run mode | 30m | ⬜ |
| 4.5 | Run with real data, verify measurements | 30m | ⬜ |

**Acceptance:** Quebec scraper produces valid measurements

**Dependencies:** Milestone 3 ✓ (Ontario stable first)

---

### Phase 4B: Methodology Divergence UI

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 4.6 | Add Quebec hospitals to frontend map | 1h | ⬜ |
| 4.7 | Implement `are_comparable()` check in frontend | 1h | ⬜ |
| 4.8 | Display divergence warning when comparing ON vs QC | 2h | ⬜ |
| 4.9 | Add methodology badges to hospital popups | 1h | ⬜ |
| 4.10 | Update GitHub Actions to run both scrapers | 30m | ⬜ |

**Acceptance:** Comparing Ottawa Hospital to Gatineau Hospital shows divergence warning

**Dependencies:** 4.1-4.5 ✓

---

## Milestone 5: Polish & Launch

**Goal:** Portfolio-ready presentation
**Status:** Pending
**Success Criteria:** Ready for medical school admissions review

### Phase 5A: Verification Queue

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 5.1 | Create admin route for hospital verification | 2h | ⬜ |
| 5.2 | Display unverified hospitals in admin panel | 1h | ⬜ |
| 5.3 | Add approve/reject buttons | 1h | ⬜ |
| 5.4 | Implement verification workflow | 1h | ⬜ |

**Acceptance:** New hospitals require manual approval

---

### Phase 5B: Methods & Governance Page

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 5.5 | Create `/methods` page | 2h | ⬜ |
| 5.6 | Display comparability matrix across provinces | 2h | ⬜ |
| 5.7 | Link to official provincial methodology docs | 1h | ⬜ |
| 5.8 | Add telehealth routing information | 1h | ⬜ |

**Acceptance:** Scholar narrative visible in UI

---

### Phase 5C: Documentation & Launch

| Task | Description | Est. | Status |
|------|-------------|------|--------|
| 5.9 | Update README with live site URL | 30m | ⬜ |
| 5.10 | Create MkDocs site (if not done) | 2h | ⬜ |
| 5.11 | Write LinkedIn launch post draft | 1h | ⬜ |
| 5.12 | Final review of all documentation | 1h | ⬜ |

**Acceptance:** Ready to show in portfolio

---

## Backlog (Future)

These items are explicitly **not** in scope for initial launch:

- [ ] Alberta scraper (after Quebec stable)
- [ ] Manitoba scraper
- [ ] British Columbia scraper
- [ ] Access Burden Estimator (gas + parking calculator)
- [ ] Mobile optimization
- [ ] User accounts / saved hospitals
- [ ] Email alerts for wait time changes
- [ ] Historical trends / charts
- [ ] Equity layer (income shapefiles)

---

## How to Use This Roadmap

### Starting a Task
1. Find the next ⬜ task in the current milestone
2. Read the description and acceptance criteria
3. Check dependencies are met
4. Start work, update status to 🔄

### Completing a Task
1. Verify acceptance criteria are met
2. Commit code with task number in message (e.g., `feat: implement 2.3 Ontario hospital mappings`)
3. Update status to ✅
4. Move to next task

### Status Legend
- ⬜ Not started
- 🔄 In progress
- ✅ Complete
- ⏸️ Blocked

### Rules
1. **One task at a time** - Finish before starting next
2. **Vertical slices** - Each phase delivers working functionality
3. **No skipping ahead** - Dependencies exist for a reason
4. **Test before proceeding** - Verify acceptance criteria
5. **Commit frequently** - Small, atomic commits

---

## Current Focus

**Next Task:** `2.1` Research Ontario health portal URL and data format

**Command to continue:**
```bash
# When ready to start Ontario research
cd backend
source .venv/bin/activate
# Then research Ontario URLs and document findings
```

---

## Notes

- **Quebec scraper exists** but URL is 404 - parked until Ontario is stable
- **Neon database** already has schema and seed data
- **24 unit tests** already passing for core models and Quebec scraper
- **GitHub Actions** workflows exist but not yet configured with secrets
