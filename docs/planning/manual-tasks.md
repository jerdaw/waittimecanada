# Manual Tasks Queue

This document tracks all tasks requiring significant human intervention, browser-based work, or external service configuration. These are batched here for efficient completion rather than doing them piecemeal.

**Status Key:**
- 🔴 **BLOCKED** - Implementation cannot proceed without this
- 🟡 **OPTIONAL** - Enhances features but not critical
- 🟢 **READY** - Can be done anytime, no dependencies

---

## ✅ COMPLETED: Alberta Scraper API Research

**Why:** Need to find the data API endpoint to complete Alberta scraper implementation
**Milestone:** M10 Phase 1 - Alberta Scraper
**Status:** Completed — Alberta scraper is implemented (Playwright-based, parses `div.well.wt-well` cards from rendered HTML), registered in scraper cron, and running in production. 22 Alberta hospitals active. Superseded by M16.

---

## 🟢 READY: Upgrade Production Neon Project To Launch

**Why:** The free tier has already proven too fragile for production use. The
project hit a real transfer-quota outage on 2026-03-28 and a storage warning at
89% of the free allocation on 2026-03-31.
**Milestone:** Active ops follow-up
**Estimated Time:** 5-10 minutes
**Priority:** HIGH

### Steps:
1. Open the Neon project billing/plan page for `waittimecanada`.
2. Upgrade the production project to the Launch plan.
3. Verify the plan change and current monthly usage dashboard.
4. Record the date of the billing change in `docs/planning/roadmap.md` if it
   is completed outside a normal maintenance pass.

**Result:** Production no longer depends on the free tier's `0.5 GB` storage
and `5 GB/month` public transfer ceilings.

---

## 🟡 OPTIONAL: Apply To The Neon Open Source Program

**Why:** Offset Launch-plan costs with credits now that the repo explicitly
documents Neon as the default hosted quick-start path.
**Milestone:** Active cost follow-up
**Estimated Time:** 10-15 minutes
**Priority:** MEDIUM

### Steps:
1. Open the Neon Open Source Program application page.
2. Submit:
   - Project URL: `https://github.com/jerdaw/waittimecanada`
   - Contact email: your preferred maintainer email
3. Use the current repository positioning:
   - MIT-licensed open-source project
   - runs on PostgreSQL
   - Neon is the default documented hosted quick-start path
4. If accepted, record the outcome in `docs/planning/roadmap.md`.

**Result:** Potential credits/support without changing the project's current
managed-Postgres posture.

---

## 🟡 OPTIONAL: Pushover Alert Configuration

**Why:** Enable push notifications for scraper health alerts
**Milestone:** M12 Phase 2 - Dead Man's Switch (already implemented, just needs config)
**Estimated Time:** 5 minutes
**Priority:** MEDIUM (nice-to-have monitoring)

### Steps:
1. **Create Pushover Account:**
   - Go to https://pushover.net
   - Create free account
   - Note your **User Key** (shown on dashboard)

2. **Create Application Token:**
   - Click "Create an Application/API Token"
   - Name: "Wait Time Canada Heartbeat Monitor"
   - Note the **API Token/Key**

3. **Add to GitHub Actions encrypted values:**
   - Go to: https://github.com/jerdaw/waittimecanada/settings/secrets/actions
   - Add `PUSHOVER_USER_KEY` = your user key
   - Add `PUSHOVER_API_TOKEN` = your API token

**Result:** GitHub Actions will automatically send push notifications when scrapers fail.

---

## 🟡 OPTIONAL: StatsCan Census Data Download

**Why:** Required for Equity Layer (socioeconomic overlays on map)
**Milestone:** M11 Phase 2 - Equity Layer
**Estimated Time:** 20-30 minutes
**Priority:** MEDIUM (strong Health Advocate feature)
**Current State:** Map/API scaffold and tract-linkage summary are live with placeholder geometry; this task unlocks real-data replacement.

### Steps:
1. **Download Census Data:**
   - Go to: https://www12.statcan.gc.ca/census-recensement/2021/dp-pd/prof/index.cfm
   - Select: Income statistics by census tract
   - Download GeoJSON or shapefile format
   - Focus on: Median household income, Low-income measure (LIM)

2. **Save Files:**
   - Create directory: `frontend/public/data/census/`
   - Save files with clear names: `census-income-2021.geojson`

3. **Document Metadata:**
   ```
   Data Source: StatsCan Census 2021
   Variables Included: __________________
   File Format: GeoJSON / Shapefile
   File Size: ____ MB
   Last Updated: __________________
   ```

**Next Steps After Completion:**
- Replace placeholder payload in `/api/equity-layer`
- Keep legend attribution synchronized with final StatsCan source metadata
- Extend equity insights summary using tract-level linkage

---

## ✅ COMPLETED: Production Deployment

**Why:** Get live URL for portfolio/applications
**Milestone:** M9 Phase 1 - Portfolio Launch
**Estimated Time:** 45-60 minutes
**Priority:** CRITICAL (needed for applications)

### Production Outcome:
- **Platform:** Shared VPS frontend via Caddy + Docker loopback runtime
- **Canonical URL:** `https://wait-time.ca`
- **Redirects:** `https://www.wait-time.ca` → `https://wait-time.ca/`
- **Latest verified production release:** `main@85ed19d`

### GitHub Actions (Already Configured):
✅ Scraper cron already set up in `.github/workflows/scraper-cron.yml`
✅ Heartbeat monitor already set up
✅ Production smoke workflow set up in `.github/workflows/production-smoke.yml`
✅ Production readiness workflow set up in `.github/workflows/production-readiness.yml`
✅ `DATABASE_URL` secret is configured
✅ `PRODUCTION_BASE_URL` is configured
✅ Canonical-domain smoke checks have passed

**Document Live URL:**
```
Production URL: https://wait-time.ca
Deployment Date: 2026-03-12
```

### Production Smoke Verification:
1. Add GitHub Actions secret:
   - `PRODUCTION_BASE_URL` = your live site URL
2. Run workflow manually:
   - GitHub Actions → `Production Smoke` → Run workflow
3. Confirm all checks pass for:
   - `/`
   - `/methods`
   - `/data-quality`
   - `/analytics`
   - `/resources`
   - `/api/resources/alerts?limit=1`
   - `/api/resources?kind=aed&province=ON&limit=1`
   - `/api/resources?kind=facility&province=ON&q=Toronto%20General&limit=1`
   - `/api/resources/aqhi?latitude=43.6532&longitude=-79.3832`

### Production Readiness Verification:
1. Configure required/recommended secrets:
   - Required: `DATABASE_URL`
   - Recommended: `PUSHOVER_USER_KEY`, `PUSHOVER_API_TOKEN`
2. Run workflow manually:
   - GitHub Actions → `Production Readiness` → Run workflow
3. Confirm heartbeat freshness passes.
4. Optional local audit with GitHub CLI:
   - `./scripts/verify-production-ops.sh`

---

## 🟡 OPTIONAL: Stakeholder Interviews

**Why:** Get real-world validation from ER professionals
**Milestone:** M9 Phase 3 - Stakeholder Validation
**Estimated Time:** 2-3 hours (prep + interviews)
**Priority:** MEDIUM (strong Collaborator narrative)

### Interview Targets:
- 1-2 ER nurses
- 1-2 ER physicians
- Focus on: Ontario/Quebec hospitals (since we have their data)

### Interview Questions (15-minute format):
1. "When you look at wait time data, what methodology details matter most to you?"
2. "How would you react if you saw this warning: 'Ontario uses P90 triage-to-doctor, Quebec uses average registration-to-doctor'?"
3. "Would a tool showing these methodology differences be useful in your work?"
4. "What concerns would you have about patients comparing wait times across provinces?"

### Outreach Template:
```
Subject: Quick input on ER wait time transparency tool (medical student project)

Hi [Name],

I'm a medical student building a tool that audits Canadian ER wait time
methodologies. I'm looking for 15 minutes of your time to validate whether
exposing methodology differences (P90 vs averages, triage vs registration)
would be useful for professionals or patients.

Would you be available for a brief call/coffee chat?

Thanks,
[Your name]
```

**Document Results:**
- Save interview notes in `docs/stakeholder-interviews/`
- Extract 1-2 testimonial quotes (with permission)
- If publishing a quote, include `publishedAt` + `approvalReference` metadata in `frontend/content/stakeholderTestimonials.ts`
- Keep at most one `published: true` testimonial entry (guardrail-enforced)

**Toolkit Status:**
- [x] Outreach template prepared (`docs/stakeholder-interviews/outreach-template.md`)
- [x] Intake template prepared (`docs/stakeholder-interviews/participant-intake-template.md`)
- [x] Interview script prepared (`docs/stakeholder-interviews/interview-template.md`)
- [x] Feedback log template prepared (`docs/stakeholder-feedback.md`)
- [x] Testimonial UI/data pipeline prepared (`frontend/components/Testimonial.tsx`, `frontend/content/stakeholderTestimonials.ts`)

**Current posture:** Parked until explicit user go-ahead.

---

## 🟢 READY: Screenshot Capture for Portfolio

**Why:** Need high-quality screenshots for LinkedIn, applications, README
**Milestone:** M9 Phase 4 - Launch Materials
**Estimated Time:** 30 minutes
**Priority:** HIGH (needed for applications)

**Reference Guide:** `docs/screenshot-guide.md` (already created)

**Automation Status:**
- [x] Baseline screenshot workflow implemented (`.github/workflows/portfolio-screenshots.yml`)
- [x] Automated captures generated as CI artifact (`portfolio-screenshots`)
- [ ] Curated manual captures still needed for divergence warning/modal storytelling shots

### Priority Screenshots:
1. **Hero landing page** - Full page view
2. **Interactive map** with markers - Zoomed to Toronto/Ottawa area
3. **Hospital comparison modal** - Showing methodology divergence warning
4. **Methods page** - Comparability matrix
5. **Data export UI** - Download component

### Specifications:
- **LinkedIn:** 1200x627px
- **Twitter:** 1200x675px
- **GitHub:** 1280x640px
- **High-DPI:** 2x resolution for retina displays

**Save to:** `docs/screenshots/` (create directory)

---

## ⏸️ PARKED: LinkedIn Launch Post

**Why:** Announce project to network, potential admissions committees
**Milestone:** M9 Phase 4 - Launch Materials
**Estimated Time:** 15 minutes (review and publish)
**Priority:** HIGH (visibility for applications)

**Draft Ready:** `docs/linkedin-launch-post.md` (final recommended post prepared; publish only when explicitly activated)

### Steps:
1. [x] Refresh publish-ready copy in `docs/linkedin-launch-post.md` to match the live mission/equity/stewardship posture
2. [x] Set live demo URL to `https://wait-time.ca`
3. [ ] Add 2-3 screenshots
4. [ ] Publish

**Hashtags:** #HealthInformatics #EmergencyMedicine #PublicHealth #OpenData #HealthSystems #Canada

---

## ✅ COMPLETED: Application Summary Artifact

**Milestone:** M9 Phase 4 - Launch Materials
**Status:** Completed 2026-02-08

**File:** `docs/application-summary.md`

Contains:
- Primary application paragraph
- 60-second interview version
- Technical summary
- CanMEDS mapping summary

---

## 🟢 READY: GitHub Repository Polish

**Why:** First impression for technical reviewers
**Milestone:** M9 Phase 4 - Launch Materials
**Estimated Time:** 10 minutes
**Priority:** MEDIUM

### Checklist:
- [x] Add repository description
- [x] Add topics/tags: `healthcare`, `wait-times`, `canada`, `data-visualization`, `postgresql`, `nextjs`
- [ ] Pin repository to profile
- [ ] Add website URL (once deployed)
- [x] Verify README badges are accurate
- [ ] Add social preview image (use screenshot)

---

## 🟡 OPTIONAL: Occupancy Statistics Research

**Why:** Determine if "patients waiting" data is available
**Milestone:** M12 Phase 3 - Occupancy Statistics
**Estimated Time:** 15-20 minutes
**Priority:** LOW (nice-to-have feature)

### Research Questions:
1. Does Ontario Health provide "patients waiting" or "patients in treatment" counts?
2. Does Quebec MSSS provide similar data?
3. Are these counts in the same data source or separate?
4. What is the update frequency?

### Where to Look:
- Ontario: https://www.hqontario.ca/System-Performance/Time-Spent-in-Emergency-Departments
- Quebec: https://www.msss.gouv.qc.ca/professionnels/statistiques-donnees-services-sante/
- Check browser network tab when viewing wait times
- Look for additional API endpoints

**Document Findings:**
```
Province: _______
Data Available: Yes / No
Fields: _______________________
Update Frequency: _______
API Endpoint (if any): _______________________
```

---

## Batch Completion Workflow

When ready to knock out manual tasks:

1. **Sort by Priority:** Start with 🔴 BLOCKED, then 🟢 READY, then 🟡 OPTIONAL
2. **Time-box:** Set aside 2-3 hours for efficient batch processing
3. **Document:** Fill in all the blanks as you complete each task
4. **Update Status:** Mark completed tasks with ✅
5. **Notify:** Let me know which tasks are complete so I can proceed with implementation

---

**Last Updated:** 2026-02-11
**Tasks Pending:** Tracked inline
**Tasks Completed:** Tracked inline
