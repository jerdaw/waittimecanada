# Manual Tasks Queue

This document tracks all tasks requiring significant human intervention, browser-based work, or external service configuration. These are batched here for efficient completion rather than doing them piecemeal.

**Status Key:**
- 🔴 **BLOCKED** - Implementation cannot proceed without this
- 🟡 **OPTIONAL** - Enhances features but not critical
- 🟢 **READY** - Can be done anytime, no dependencies

---

## 🔴 BLOCKED: Alberta Scraper API Research

**Why:** Need to find the data API endpoint to complete Alberta scraper implementation
**Milestone:** M10 Phase 1 - Alberta Scraper
**Estimated Time:** 10-15 minutes
**Priority:** HIGH (proves multi-province methodology)

### Steps:
1. Open browser and go to: https://www.albertahealthservices.ca/waittimes/Page14230.aspx
2. Open Developer Tools (F12 or Cmd+Option+I)
3. Go to Network tab, filter by "Fetch/XHR"
4. Clear network log
5. Select a region from dropdown (e.g., "Calgary & area")
6. Look for network requests that return JSON data
7. Common patterns to look for:
   - `/api/` endpoints
   - `/GetWaitTimes`
   - `/waittimes.json`
   - Requests returning hospital names and wait times

### Document:
```
Request URL: _______________________
Request Method: GET / POST
Parameters (if any): _______________________
Response structure (sample JSON):
{
  ...paste example here...
}
```

**Next Steps After Completion:**
Provide the above information and I'll complete the Alberta scraper implementation.

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
   - Name: "WaitTime Canada Heartbeat Monitor"
   - Note the **API Token/Key**

3. **Add to GitHub Secrets:**
   - Go to: https://github.com/jerdaw/waittimecanada/settings/secrets/actions
   - Add secret: `PUSHOVER_USER_KEY` = your user key
   - Add secret: `PUSHOVER_API_TOKEN` = your API token

**Result:** GitHub Actions will automatically send push notifications when scrapers fail.

---

## 🟡 OPTIONAL: StatsCan Census Data Download

**Why:** Required for Equity Layer (socioeconomic overlays on map)
**Milestone:** M11 Phase 2 - Equity Layer
**Estimated Time:** 20-30 minutes
**Priority:** MEDIUM (strong Health Advocate feature)

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
I'll process the data, create Mapbox tilesets, and implement the overlay UI.

---

## 🔴 BLOCKED: Production Deployment

**Why:** Get live URL for portfolio/applications
**Milestone:** M9 Phase 1 - Portfolio Launch
**Estimated Time:** 45-60 minutes
**Priority:** CRITICAL (needed for applications)

### Frontend Deployment (Render):
1. **Create Render Account:**
   - Go to https://render.com
   - Sign up / Sign in with GitHub

2. **Deploy Frontend:**
   - New → Static Site
   - Connect repository: `jerdaw/waittimecanada`
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/out` or `frontend/.next`

3. **Configure Environment Variables:**
   - `DATABASE_URL` = (Neon connection string)
   - `NEXT_PUBLIC_MAPBOX_TOKEN` = (Mapbox token)

4. **Custom Domain (optional):**
   - Add custom domain if desired
   - Configure DNS

### GitHub Actions (Already Configured):
✅ Scraper cron already set up in `.github/workflows/scraper-cron.yml`
✅ Heartbeat monitor already set up
✅ Production smoke workflow set up in `.github/workflows/production-smoke.yml`
✅ Production readiness workflow set up in `.github/workflows/production-readiness.yml`
⚠️  Need to verify DATABASE_URL secret is set in GitHub
⚠️  Need to set `PRODUCTION_BASE_URL` secret and run smoke workflow once

**Document Live URL:**
```
Production URL: _______________________
Deployment Date: _______________________
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
- Add testimonial section to site if obtained

---

## 🟢 READY: Screenshot Capture for Portfolio

**Why:** Need high-quality screenshots for LinkedIn, applications, README
**Milestone:** M9 Phase 4 - Launch Materials
**Estimated Time:** 30 minutes
**Priority:** HIGH (needed for applications)

**Reference Guide:** `docs/screenshot-guide.md` (already created)

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

## 🟢 READY: LinkedIn Launch Post

**Why:** Announce project to network, potential admissions committees
**Milestone:** M9 Phase 4 - Launch Materials
**Estimated Time:** 15 minutes (review and publish)
**Priority:** HIGH (visibility for applications)

**Draft Ready:** `docs/linkedin-launch-post.md` (5 versions available)

### Steps:
1. Review draft posts in `docs/linkedin-launch-post.md`
2. Choose version (Scholar, Professional, Advocate, Leader, or Technical)
3. Customize with live URL once deployed
4. Add 2-3 screenshots
5. Publish

**Hashtags:** #HealthTech #MedEd #DataScience #HealthcareInnovation #MedicalStudent #CanMEDS

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

**Last Updated:** 2026-02-08
**Tasks Pending:** Tracked inline
**Tasks Completed:** Tracked inline
