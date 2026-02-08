# Milestone 9: Portfolio-Ready Launch

> **Priority:** CRITICAL - Must complete before portfolio submission
> **Estimated Effort:** 3-4 days
> **Admissions Appeal:** Leader, Collaborator, Professional

---

## Overview

This milestone transforms the project from "working code" to "portfolio-ready product." The goal is to have a live, presentable site with a compelling personal narrative and stakeholder validation.

---

## Phase 1: Production Deployment (Day 1)

### 1.1 Frontend Deployment

**Platform:** Render (already configured) or Vercel

**Steps:**
1. Verify `frontend/.env.example` has all required variables documented
2. Set production environment variables in Render dashboard:
   - `DATABASE_URL` - Neon connection string (pooled)
   - `NEXT_PUBLIC_MAPBOX_TOKEN` - Mapbox access token
3. Trigger deploy from `main` branch
4. Verify build succeeds and site loads

**Verification Checklist:**
- [ ] Homepage loads with map
- [ ] Hospital list populates
- [ ] Search/filter works
- [ ] /methods page loads with sources from database
- [ ] /faq page renders correctly
- [ ] Dark mode toggle works
- [ ] Mobile responsive layout works

### 1.2 Automated Scraper Setup

**Platform:** GitHub Actions

**File:** `.github/workflows/scraper-cron.yml`

```yaml
name: Scraper Cron

on:
  schedule:
    - cron: '*/15 * * * *'  # Every 15 minutes
  workflow_dispatch:  # Manual trigger for testing

jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e ".[dev]"
          playwright install chromium

      - name: Run Ontario scraper
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          cd backend
          python -m waittime.cli.scraper --source ontario-health

      - name: Check heartbeat age
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: |
          cd backend
          python -m waittime.cli.check_heartbeat --max-age 60
```

**Secrets to Add:**
- `DATABASE_URL` - Neon connection string
- `PUSHOVER_USER_KEY` - For alerts (Phase 2)
- `PUSHOVER_API_TOKEN` - For alerts (Phase 2)

### 1.3 Dead Man's Switch (Basic)

**File:** `backend/src/waittime/cli/check_heartbeat.py`

```python
"""Check scraper heartbeat and alert if stale."""
import argparse
import sys
from datetime import datetime, timedelta
from waittime.services.database import DatabaseService

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-age', type=int, default=60, help='Max heartbeat age in minutes')
    args = parser.parse_args()

    db = DatabaseService()
    latest = db.get_latest_heartbeat()

    if not latest:
        print("ERROR: No heartbeat found")
        sys.exit(1)

    age = datetime.utcnow() - latest.timestamp
    if age > timedelta(minutes=args.max_age):
        print(f"ALERT: Heartbeat is {age.total_seconds() / 60:.0f} minutes old")
        # TODO: Send Pushover notification
        sys.exit(1)

    print(f"OK: Heartbeat is {age.total_seconds() / 60:.0f} minutes old")
    sys.exit(0)

if __name__ == '__main__':
    main()
```

### 1.4 Production Smoke Verification Automation

**Status:** Implemented (automation), pending live URL execution

**Files:**
- `.github/workflows/production-smoke.yml`
- `scripts/production-smoke.sh`

**Behavior:**
1. Supports manual runs via `workflow_dispatch` with optional `base_url` input
2. Runs every 6 hours on schedule as a passive production sanity check
3. Verifies `200` + expected content marker for:
   - `/`
   - `/methods`
   - `/data-quality`
   - `/analytics`

**Required Secret:**
- `PRODUCTION_BASE_URL` - e.g., `https://waittimecanada.ca`

### 1.5 Production Readiness Verification Automation

**Status:** Implemented (automation), pending secret configuration + run execution

**Files:**
- `.github/workflows/production-readiness.yml`
- `scripts/verify-production-ops.sh`

**Behavior:**
1. Manual workflow validates required/recommended production secrets
2. Runs heartbeat freshness check (`python -m waittime.cli.check_heartbeat --dry-run`)
3. Optionally runs smoke checks in the same workflow when `PRODUCTION_BASE_URL` is configured
4. Local script audits secret presence, workflow state, and recent cron freshness via `gh`

**Runbook:**
1. Configure `DATABASE_URL` (required)
2. Configure `PUSHOVER_USER_KEY` + `PUSHOVER_API_TOKEN` (recommended)
3. Trigger workflow `Production Readiness` from GitHub Actions tab
4. Optionally run `./scripts/verify-production-ops.sh` locally for `gh`-based audit output

---

## Phase 2: About/Story Section (Day 2)

### 2.1 Design Decision

**Option A:** Collapsible section on homepage (recommended)
- Keeps user on main page
- Can be expanded/collapsed
- Visible to casual visitors

**Option B:** Dedicated `/about` route
- More space for narrative
- Separate from main functionality
- May be overlooked

**Recommendation:** Option A with link to expanded version

### 2.2 Component Implementation

**File:** `frontend/components/AboutSection.tsx`

```tsx
'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, Github, Linkedin, Mail } from 'lucide-react';

export function AboutSection() {
  const [expanded, setExpanded] = useState(false);

  return (
    <section className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-slate-800 dark:to-slate-900 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-full flex items-center justify-between text-left"
        >
          <div>
            <span className="text-sm font-medium text-blue-600 dark:text-blue-400 uppercase tracking-wide">
              About This Project
            </span>
            <h2 className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
              Why I Built WaitTime Canada
            </h2>
          </div>
          {expanded ? <ChevronUp className="w-6 h-6" /> : <ChevronDown className="w-6 h-6" />}
        </button>

        {expanded && (
          <div className="mt-6 space-y-4 text-slate-600 dark:text-slate-300 animate-in fade-in slide-in-from-top-4">
            <p>
              As a pre-medical student, I noticed something troubling: Canadian provinces
              report emergency room wait times using <strong>completely different methodologies</strong>.
              Ontario measures from triage to physician (90th percentile). Quebec measures from
              registration to physician (rolling average). These numbers can't be directly compared—but
              most apps present them side-by-side anyway.
            </p>

            <p>
              <strong>WaitTime Canada is different.</strong> Instead of pretending the data is
              comparable, we audit it. We tag every measurement with its methodology and warn
              users when direct comparison is statistically invalid. This is what I call a
              "Health Systems Observatory"—a tool that exposes the black box of healthcare
              reporting.
            </p>

            <p>
              This project demonstrates my approach to medicine: rigorous methodology,
              transparent limitations, and a commitment to helping patients make informed
              decisions—even when that means telling them what we <em>don't</em> know.
            </p>

            <div className="flex items-center gap-6 pt-4 border-t border-slate-200 dark:border-slate-700">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-slate-200 dark:bg-slate-700" />
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">Jeremy Dawson</p>
                  <p className="text-sm text-slate-500">Pre-Medical Student</p>
                </div>
              </div>
              <div className="flex gap-3">
                <a href="https://github.com/jerdaw" className="text-slate-500 hover:text-slate-700">
                  <Github className="w-5 h-5" />
                </a>
                <a href="https://linkedin.com/in/jeremyjdawson" className="text-slate-500 hover:text-slate-700">
                  <Linkedin className="w-5 h-5" />
                </a>
                <a href="mailto:jeremyjdawson@gmail.com" className="text-slate-500 hover:text-slate-700">
                  <Mail className="w-5 h-5" />
                </a>
              </div>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
```

### 2.3 Integration

Add to `frontend/app/page.tsx` after the Hero section:

```tsx
import { AboutSection } from '@/components/AboutSection';

// In the component, after Hero:
{showHero && <AboutSection />}
```

---

## Phase 3: Stakeholder Validation (Day 2-3)

**Status:** Interview toolkit completed 2026-02-08; interview execution still pending.

### 3.1 Finding Stakeholders

**Target:** 1-2 ER nurses or physicians (15-minute interview each)

**Outreach Channels:**
1. Personal network (family/friends in healthcare)
2. LinkedIn connections
3. Local hospital volunteer coordinators
4. Medical school pre-med clubs
5. Reddit r/nursing or r/emergencymedicine (careful with rules)

**Toolkit Files:**
- `docs/stakeholder-interviews/outreach-template.md`
- `docs/stakeholder-interviews/participant-intake-template.md`
- `docs/stakeholder-interviews/interview-template.md`
- `docs/stakeholder-feedback.md`

**Email Template:**

```
Subject: Quick feedback on ER wait time transparency project?

Hi [Name],

I'm a pre-medical student building a project called WaitTime Canada—a tool
that helps people understand ER wait times while being transparent about
the limitations of provincial data.

Unlike other wait time apps, this one warns users when comparing hospitals
that use different measurement methodologies (e.g., Ontario's 90th percentile
vs Quebec's rolling average).

Would you have 15 minutes for a quick call to share your perspective? I'd
love to hear:
- Whether the methodology warnings seem useful
- What information patients most often misunderstand about ER waits
- Any suggestions for making the tool more helpful

I'm happy to work around your schedule. Thanks for considering!

Best,
Jeremy Dawson
[LinkedIn profile]
```

### 3.2 Interview Questions

1. When patients ask about ER wait times, what do they most often misunderstand?
2. [Show screenshot] Does this methodology warning make sense? Would it help patients?
3. What information would you want patients to know before choosing an ER?
4. Do you think the "Access Burden Estimator" (showing travel cost) is helpful or harmful?
5. Any features that would make this tool more useful for healthcare workers?

### 3.3 Documenting Feedback

**File:** `docs/stakeholder-feedback.md`

```markdown
# Stakeholder Feedback

## Interview 1: [Name], [Role], [Date]

### Key Insights
- [Insight 1]
- [Insight 2]

### Suggestions Incorporated
- [ ] [Suggestion] - Status: [Implemented/Deferred/Rejected]

### Testimonial (if provided)
> "[Quote]" - [Name], [Role]
```

### 3.4 Testimonial Component (If Obtained)

**File:** `frontend/components/Testimonial.tsx`

```tsx
export function Testimonial() {
  return (
    <blockquote className="bg-white dark:bg-slate-800 rounded-xl p-6 shadow-sm border border-slate-200 dark:border-slate-700">
      <p className="text-slate-600 dark:text-slate-300 italic">
        "The methodology warnings are exactly what patients need. Most don't realize
        that a 2-hour wait in Ontario means something different than in Quebec."
      </p>
      <footer className="mt-4 flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-slate-200" />
        <div>
          <p className="font-semibold text-slate-900 dark:text-white">Jane Smith, RN</p>
          <p className="text-sm text-slate-500">Emergency Department, Toronto General</p>
        </div>
      </footer>
    </blockquote>
  );
}
```

---

## Phase 4: Launch Materials (Day 3-4)

### 4.1 LinkedIn Post

**Status:** Draft finalized 2026-02-08 (`docs/linkedin-launch-post.md`); publishing remains manual.

**Edit existing draft:** `docs/linkedin-launch-post.md`

**Key Elements:**
1. Hook: "ER wait times across Canada aren't comparable—here's why"
2. Problem statement: Provincial methodology differences
3. Solution: Metric ontology and divergence warnings
4. Personal angle: Pre-med student building research-grade tools
5. Call to action: Try it, feedback welcome
6. Hashtags: #HealthTech #CanadianHealthcare #DataTransparency #PreMed

### 4.2 Screenshots

Create screenshots showing:
1. **Hero view** - Clean landing page with map
2. **Methodology warning** - Divergence brief in comparison modal
3. **Methods page** - Comparability matrix
4. **Mobile view** - Responsive design

**Tool:** Browser DevTools device mode or actual mobile device

**Storage:** `docs/screenshots/` directory

### 4.3 GitHub Repo Polish

**Status:** Completed 2026-02-08 (description, topics, README badges)

**Update:**
- Repository description: "A clinically defensible Health Systems Observatory for Canadian ER wait times"
- Topics: `healthcare`, `canada`, `open-data`, `nextjs`, `postgresql`, `mapbox`, `wait-times`, `health-informatics`
- README badges: Build status, test coverage, license

### 4.4 Application Summary

**Status:** Completed 2026-02-08 (`docs/application-summary.md`)

**One-paragraph summary for applications:**

> WaitTime Canada is a Health Systems Observatory I built to audit Canadian emergency
> room wait time data. Unlike typical wait time aggregators, it uses a "metric ontology"
> to tag each measurement with its methodology (start event, end event, statistic type)
> and automatically warns users when comparing hospitals that use incompatible methods.
> The project demonstrates my approach to healthcare informatics: rigorous methodology,
> transparent limitations, and a commitment to helping patients make evidence-based
> decisions. The live site serves 200+ Ontario hospitals with plans to expand
> pan-Canadian.

---

## Verification Checklist

### Production
- [ ] Site loads at production URL
- [x] Automated smoke workflow exists for core routes (`/`, `/methods`, `/data-quality`, `/analytics`)
- [ ] Live smoke run has passed against production URL
- [x] Production readiness workflow exists for secrets + heartbeat verification
- [ ] Live readiness run has passed in GitHub Actions
- [ ] All pages work (/, /methods, /faq)
- [ ] Database queries return data
- [ ] Scraper cron job configured
- [ ] Heartbeat monitoring active

### Content
- [ ] About section added with narrative
- [ ] Author bio and social links included
- [x] Stakeholder interview toolkit prepared
- [ ] Stakeholder interview completed
- [ ] Feedback documented
- [ ] Testimonial added (if obtained)

### Launch
- [x] LinkedIn post finalized
- [ ] Screenshots captured
- [x] GitHub repo polished
- [x] Application summary written

---

## Success Criteria

1. **Live URL** accessible and functioning
2. **Personal narrative** visible in UI
3. **At least 1 stakeholder interview** documented
4. **LinkedIn post** published with engagement
5. **Screenshots** ready for applications

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Deployment fails | High | Test locally first, check all env vars |
| No stakeholder responds | Medium | Start outreach early, use multiple channels |
| Negative stakeholder feedback | Low | Treat as learning opportunity, document changes |
| Scraper breaks in production | Medium | Heartbeat monitoring + manual fallback |

---

## Time Estimate

| Task | Hours |
|------|-------|
| Production deployment | 2-3 |
| About section component | 2 |
| Stakeholder outreach | 1 |
| Stakeholder interview | 0.5-1 |
| LinkedIn post finalization | 1 |
| Screenshots and polish | 1 |
| **Total** | **7-9 hours** |
