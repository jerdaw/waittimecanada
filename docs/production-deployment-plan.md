# Production Deployment Plan - Milestone 3

**Status:** Planning - Decisions Required
**Date:** February 2, 2026

---

## Current State

### What's Already Built
- ✅ **Backend scrapers:** Python with GitHub Actions cron (15-min schedule configured)
- ✅ **Frontend:** Next.js 14 with SSR, ready to deploy
- ✅ **Database:** Neon PostgreSQL (already in production)
- ✅ **CI/CD:** GitHub Actions for scrapers, cleanup, and monitoring

### What Needs Deployment
1. **Frontend application** (Next.js)
2. **GitHub Secrets** (DATABASE_URL for scrapers)
3. **Monitoring alerts** (optional email notifications)

---

## Deployment Architecture Options

### Option A: Static/SSG Hosting (Recommended for MVP)

**Platforms:** Vercel, Netlify, Cloudflare Pages

**Pros:**
- Zero-config deployment for Next.js
- Automatic builds on git push
- Free tier generous (Vercel: 100GB bandwidth)
- Built-in CDN and edge functions
- Environment variable management in UI

**Cons:**
- Vendor lock-in to some extent
- SSR cold starts on free tier
- Limited control over infrastructure

**Best for:** Quick launch, portfolio project, low operational overhead

---

### Option B: Container Hosting

**Platforms:** Railway, Render, Fly.io, DigitalOcean App Platform

**Pros:**
- More control over environment
- Can run both frontend and backend services
- Docker-based (portable)
- Often includes database hosting

**Cons:**
- Requires Dockerfile configuration
- More setup complexity
- Potentially higher cost
- Need to manage container updates

**Best for:** Scaling beyond MVP, multiple services, specific runtime needs

---

### Option C: Self-Hosted (VPS)

**Platforms:** DigitalOcean Droplets, Linode, Hetzner

**Pros:**
- Complete control
- Lowest cost at scale
- Can run anything
- SSH access for debugging

**Cons:**
- Manual setup (nginx, SSL, etc.)
- Requires devops knowledge
- You manage security updates
- No automatic scaling

**Best for:** Cost optimization, learning infrastructure, high control needs

---

### Option D: Serverless Functions Only

**Platforms:** Vercel Functions, Netlify Functions, AWS Lambda

**Pros:**
- Pay per execution
- Auto-scaling
- No server management

**Cons:**
- Cold starts
- Execution time limits (10s on Vercel free)
- Not ideal for long scraper runs
- Would need to refactor scraper architecture

**Best for:** Micro-services architecture (not recommended for current setup)

---

## Recommended Approach (Option A)

For a portfolio project and MVP, **Option A (Static/SSG)** makes the most sense:

1. **Frontend on Vercel** (or Netlify/Cloudflare Pages)
   - Next.js native support
   - Free tier sufficient
   - Auto-deploy from GitHub
   - Environment variables: `NEXT_PUBLIC_MAPBOX_TOKEN`, `DATABASE_URL`

2. **Scrapers on GitHub Actions** (already configured)
   - Runs every 15 minutes
   - Connects to Neon PostgreSQL
   - No additional hosting cost

3. **Database on Neon** (already in production)
   - Free tier: 512MB storage
   - Auto-pause when idle

**Total Cost:** $0/month on free tiers

---

## Required User Decisions

Please confirm or adjust the following:

### 1. Frontend Hosting Platform
- [ ] **Option A:** Vercel (recommended - Next.js native)
- [ ] **Option B:** Netlify
- [ ] **Option C:** Cloudflare Pages
- [ ] **Option D:** Railway (container-based)
- [ ] **Option E:** Something else: _________________

### 2. Custom Domain
- [ ] Use default platform domain (e.g., `project-name.vercel.app`)
- [ ] Use custom domain: _________________
  - If yes, where is DNS managed? _________________

### 3. Email Alerts for Scraper Failures
- [ ] Yes, configure email notifications
  - Gmail address: _________________
  - Alert destination: _________________
- [ ] No, skip email alerts (monitor via GitHub Actions UI only)

### 4. Monitoring/Analytics
- [ ] Enable built-in platform analytics (Vercel Analytics, etc.)
- [ ] Set up Sentry error tracking (optional)
- [ ] No additional monitoring for now

---

## User Actions Required

Once decisions are made above:

### Step 1: Configure GitHub Secrets
Add to repository Settings → Secrets → Actions:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `DATABASE_URL` | Neon connection string | Yes |
| `ALERT_EMAIL_USER` | Gmail address | If email alerts |
| `ALERT_EMAIL_PASSWORD` | Gmail app password | If email alerts |
| `ALERT_EMAIL_TO` | Alert recipient | If email alerts |

### Step 2: Deploy Frontend
Instructions will depend on platform chosen (see platform-specific guides below).

### Step 3: Verify Deployment
- [ ] Frontend accessible at public URL
- [ ] Map displays with hospital markers
- [ ] `/methods` page loads
- [ ] `/admin/verify` page loads
- [ ] API routes returning data
- [ ] Scraper cron runs successfully

---

## Platform-Specific Deployment Instructions

### If Vercel Selected:

1. Go to [vercel.com](https://vercel.com) → Sign in
2. "Add New" → "Project" → Import GitHub repo
3. Set Root Directory: `frontend`
4. Add environment variables:
   - `NEXT_PUBLIC_MAPBOX_TOKEN` = (Mapbox token)
   - `DATABASE_URL` = (Neon connection string)
5. Deploy

**Configuration file needed:** `frontend/vercel.json`

---

### If Netlify Selected:

1. Go to [netlify.com](https://netlify.com) → Sign in
2. "Add new site" → Import from Git
3. Build settings:
   - Base directory: `frontend`
   - Build command: `npm run build`
   - Publish directory: `.next`
4. Add environment variables (same as Vercel)
5. Deploy

**Configuration file needed:** `frontend/netlify.toml`

---

### If Railway Selected:

1. Go to [railway.app](https://railway.app) → Sign in
2. "New Project" → Deploy from GitHub
3. Add service: Frontend
   - Root directory: `/frontend`
   - Build command: `npm run build`
   - Start command: `npm start`
4. Add environment variables (same as above)
5. Deploy

**Configuration file needed:** `frontend/Dockerfile` (optional but recommended)

---

### If Cloudflare Pages Selected:

1. Go to [dash.cloudflare.com](https://dash.cloudflare.com) → Pages
2. "Create a project" → Connect to Git
3. Build settings:
   - Framework preset: Next.js
   - Build command: `npm run build`
   - Build output directory: `.next`
   - Root directory: `frontend`
4. Add environment variables (same as above)
5. Deploy

**Note:** Cloudflare Pages requires Next.js Edge Runtime compatibility

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Scraper fails silently | Medium | High | Heartbeat monitor (already configured) |
| Database connection limit hit | Low | Medium | Neon free tier: 100 connections, should be sufficient |
| API rate limits exceeded | Low | Low | No external APIs except Mapbox (generous free tier) |
| Storage exceeds free tier | Low | Medium | 30-day retention policy (already implemented) |
| Bad data published | Medium | High | Verification queue (already implemented) |

---

## Post-Deployment Monitoring

After deployment, monitor for 24-48 hours:

1. **GitHub Actions**
   - Check scraper-cron runs every 15 minutes
   - Verify heartbeat-monitor passes hourly
   - Watch for failure notifications

2. **Frontend**
   - Test all pages load
   - Verify data displays correctly
   - Check browser console for errors

3. **Database**
   - Monitor connection count in Neon dashboard
   - Verify measurements are being inserted
   - Check cleanup job runs daily

---

## Rollback Plan

If deployment fails or has critical issues:

1. **Frontend:** Redeploy previous version via platform dashboard
2. **Scrapers:** Disable GitHub Actions workflow temporarily
3. **Database:** No changes needed (data persists)

---

## Next Steps After Deployment

1. Update README.md with live demo URL
2. Update LinkedIn post with actual screenshots
3. Monitor for 48 hours for stability
4. Consider custom domain setup
5. Begin planning Milestone 4 (Quebec expansion)

---

## Open Questions

Before proceeding, please clarify:

1. **Have you already deployed the frontend somewhere?**
   - If yes, where? What configuration exists?

2. **Do you have a hosting platform preference?**
   - Based on prior experience, cost concerns, or other factors?

3. **Is there existing infrastructure I should be aware of?**
   - Domains, hosting accounts, deployment pipelines?

4. **Timeline expectations?**
   - Immediate deployment needed or can wait for decisions?

---

*This planning document replaces premature deployment implementation. User decisions required before proceeding.*
