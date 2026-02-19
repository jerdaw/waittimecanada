# M9 Remaining User Actions - Implementation Walkthrough

**Status:** All technical work complete - 4 manual actions remain
**Last Updated:** 2026-02-09

## Overview

All automated technical work for Milestone 9 (Portfolio Launch) is complete. The following 4 items require manual user action and cannot be automated:

1. ✋ Deploy frontend to public hosting
2. ✋ Conduct stakeholder interview
3. ✋ Capture curated screenshots
4. ✋ Publish LinkedIn post

## Action 1: Deploy Frontend to Public Hosting

**When:** When ready to make the site publicly accessible again
**Time:** ~30 minutes
**Tools:** Netlify dashboard

### Steps:

1. **Re-enable Netlify hosting:**
   - Log into Netlify dashboard
   - Navigate to your site settings
   - Re-enable automatic deployments from `main` branch
   - Or: Manually trigger a deploy from the Deploys tab

2. **Verify deployment:**
   - Wait for build to complete (~3-5 minutes)
   - Visit your production URL
   - Verify:
     - ✅ Homepage loads with map
     - ✅ About section appears below Hero
     - ✅ /methods page loads
     - ✅ /data-quality page loads
     - ✅ /analytics page loads
     - ✅ Dark mode toggle works

3. **Enable production smoke workflow:**
   - Edit `.github/workflows/production-smoke.yml`
   - Uncomment the schedule trigger
   - Set `PRODUCTION_BASE_URL` secret in GitHub repo settings
   - Trigger manual workflow run to verify

4. **Verify scraper cron:**
   - Check GitHub Actions "Scraper Cron" workflow
   - Verify it's running every 15 minutes
   - Check recent runs for success

### Success Criteria:
- [ ] Site accessible at production URL
- [ ] All pages load without errors
- [ ] Database queries return data
- [ ] Production smoke workflow passing
- [ ] Scraper cron running successfully

---

## Action 2: Conduct Stakeholder Interview

**When:** Within 1-2 weeks for portfolio freshness
**Time:** ~1 hour (outreach + 15-min interview)
**Tools:** Email, video call, interview template

### Steps:

1. **Identify potential interviewees:**
   - Use prepared outreach template: `docs/stakeholder-interviews/outreach-template.md`
   - Target: 1-2 ER nurses or physicians
   - Channels:
     - Personal network (family/friends in healthcare)
     - LinkedIn connections
     - Medical school pre-med clubs
     - Local hospital volunteer coordinators

2. **Send outreach email:**
   ```
   Subject: Quick feedback on ER wait time transparency project?

   Hi [Name],

   I'm a pre-medical student building a project called Wait Time Canada—a
   tool that helps people understand ER wait times while being transparent
   about the limitations of provincial data.

   Unlike other wait time apps, this one warns users when comparing hospitals
   that use different measurement methodologies (e.g., Ontario's 90th
   percentile vs Quebec's rolling average).

   Would you have 15 minutes for a quick call to share your perspective?

   [Include link to deployed site]

   Best,
   Jeremy
   ```

3. **Conduct interview:**
   - Use prepared questions: `docs/stakeholder-interviews/interview-template.md`
   - Show deployed site during interview
   - Key questions:
     1. When patients ask about ER wait times, what do they most often misunderstand?
     2. Does this methodology warning make sense? Would it help patients?
     3. What information would you want patients to know before choosing an ER?
     4. Do you think the "Access Burden Estimator" (travel cost) is helpful or harmful?
     5. Any features that would make this tool more useful?

4. **Document feedback:**
   - Fill in participant intake: `docs/stakeholder-interviews/participant-intake-template.md`
   - Add to: `docs/stakeholder-feedback.md`
   - Note any suggested improvements
   - **Request testimonial quote** (if interview goes well)

5. **If testimonial obtained:**
   - Get written approval via email
   - Add to `frontend/content/stakeholderTestimonials.ts`:
     ```typescript
     {
       id: "001",
       quote: "[Their quote]",
       displayName: "[Name, Role]",
       role: "[Role]",
       organization: "[Hospital]",
       published: true,
       publishedAt: "2026-02-XX",
       approvalReference: "email-2026-02-XX",
     }
     ```
   - Component will automatically display it on homepage

### Success Criteria:
- [ ] At least 1 interview completed
- [ ] Feedback documented in `docs/stakeholder-feedback.md`
- [ ] Testimonial obtained and added (if provided)
- [ ] Any suggested improvements noted for future work

---

## Action 3: Capture Curated Screenshots

**When:** After frontend deployment is live
**Time:** ~30 minutes
**Tools:** Browser DevTools, screenshot tool

### Baseline Screenshots (Automated):

Already captured via workflow:
- ✅ Landing page view
- ✅ Map with pins
- ✅ Methods page
- ✅ Data quality dashboard
- ✅ Analytics page

### Manual Screenshots Needed:

**1. Methodology Warning (Comparison Modal)**
- Navigate to map
- Click on two hospitals from different provinces
- Click "Compare" button
- Capture divergence warning screenshot
- Save as: `docs/screenshots/divergence-warning.png`

**2. Mobile Responsive View**
- Open DevTools (F12)
- Toggle device toolbar (Ctrl+Shift+M)
- Select iPhone 12 Pro or similar
- Capture homepage view
- Capture expanded About section
- Save as: `docs/screenshots/mobile-responsive.png`

**3. Access Insights Panel**
- Enable location access (or use IP location)
- Scroll to Access Insights section
- Capture the summary cards showing:
  - ERs within 30km
  - Average access cost
  - Nearest ER
- Save as: `docs/screenshots/access-insights.png`

**4. Dark Mode**
- Toggle dark mode
- Capture landing page with dark theme
- Save as: `docs/screenshots/dark-mode.png`

### Organization:
```
docs/screenshots/
├── automated/          # From workflow
├── divergence-warning.png
├── mobile-responsive.png
├── access-insights.png
└── dark-mode.png
```

### Success Criteria:
- [ ] All 4 manual screenshots captured
- [ ] High quality (1920x1080 or similar)
- [ ] Organized in docs/screenshots/
- [ ] Ready for LinkedIn post and applications

---

## Action 4: Publish LinkedIn Post

**When:** After deployment + interview + screenshots are complete
**Time:** ~15 minutes
**Tools:** LinkedIn, draft post, screenshots

### Steps:

1. **Review draft:**
   - Read prepared post: `docs/linkedin-launch-post.md`
   - Customize if needed based on interview feedback
   - Ensure it reflects current project state

2. **Prepare assets:**
   - Select 3-4 best screenshots to attach
   - Recommended:
     1. Landing page (shows brand)
     2. Divergence warning (shows unique value)
     3. Methods page (shows rigor)
     4. Access insights (shows innovation)

3. **Publish on LinkedIn:**
   - Copy post from draft
   - Attach screenshots
   - Add hashtags:
     - #HealthTech
     - #CanadianHealthcare
     - #DataTransparency
     - #PreMed
     - #HealthInformatics
   - Tag relevant connections (if appropriate)

4. **Share in appropriate groups:**
   - Medical student communities
   - Health tech groups
   - Canadian healthcare groups

5. **Monitor engagement:**
   - Respond to comments
   - Answer questions
   - Note feedback for future improvements

### Success Criteria:
- [ ] Post published on LinkedIn
- [ ] Screenshots attached
- [ ] Appropriate hashtags included
- [ ] Engagement monitored for first 48 hours
- [ ] Link to post saved for portfolio/applications

---

## Timeline Recommendation

**Week 1:**
- Day 1: Re-enable frontend deployment (Action 1)
- Day 2-3: Reach out to potential interviewees (Action 2)
- Day 4-5: Capture screenshots (Action 3)

**Week 2:**
- Day 1: Conduct interview (Action 2)
- Day 2: Document feedback and testimonial (Action 2)
- Day 3: Review and finalize LinkedIn post (Action 4)
- Day 4: Publish LinkedIn post (Action 4)

**Total Time Commitment:** ~3-4 hours spread over 2 weeks

---

## Support Resources

**Technical Issues:**
- `docs/production-deployment-plan.md` - Deployment guide
- `scripts/verify-production-ops.sh` - Production readiness check
- `.github/workflows/production-smoke.yml` - Smoke test workflow

**Interview Support:**
- `docs/stakeholder-interviews/outreach-template.md` - Email template
- `docs/stakeholder-interviews/interview-template.md` - Question guide
- `docs/stakeholder-interviews/participant-intake-template.md` - Intake form

**Launch Materials:**
- `docs/linkedin-launch-post.md` - Post draft
- `docs/application-summary.md` - One-paragraph summary
- `docs/screenshots/automated/` - Baseline screenshots

---

## What's Already Done

You don't need to worry about:
- ✅ About section component (implemented and tested)
- ✅ Testimonial display system (ready for content)
- ✅ Production workflows (automated)
- ✅ Interview toolkit (prepared)
- ✅ LinkedIn draft (finalized)
- ✅ GitHub repo polish (complete)
- ✅ Application summary (written)
- ✅ Screenshot automation (baseline captured)

All technical infrastructure is ready. You just need to **execute the manual actions** to complete the portfolio launch.

---

## Questions?

If you encounter issues:
1. Check the specific guide in `docs/` for that action
2. Review the M9 milestone plan: `docs/planning/implementation/milestone-9-launch.md`
3. Verify automation status: `scripts/verify-production-ops.sh`

All technical foundations are solid and tested. You're ready to launch! 🚀
