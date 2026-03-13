# Production Deployment Plan - Historical Netlify Baseline

**Status:** Historical reference; Netlify remains current live hosting until VPS cutover
**Date:** March 12, 2026
**Platform:** Netlify (release-gated; active)

> Update (March 12, 2026): Netlify deploys are active again, the application is serving successfully from the Netlify site, `https://wait-time.ca` is live with a valid Let's Encrypt certificate, `https://www.wait-time.ca` redirects to the canonical host, and production smoke passes against the canonical domain.
>
> Runtime usage controls implemented:
> - `/api/health` polling reduced to every 5 minutes and only while tab is visible.
> - Read-heavy API routes now send short CDN cache headers (typically 2-10 minutes).
> - Admin, geolocation, and export routes are `Cache-Control: no-store`.
>
> Direct-VPS note (March 13, 2026): the active migration target for future
> hosting is documented in `docs/operations/direct-vps-frontend.md`. Do not
> treat this file as the source of truth for the VPS path.

---

## Current State

### What's Already Built
- ✅ **Backend scrapers:** Python with GitHub Actions cron (4-hour cost-control schedule active)
- ✅ **Frontend:** Next.js 14 with SSR, deployed on Netlify
- ✅ **Database:** Neon PostgreSQL (already in production)
- ✅ **CI/CD:** GitHub Actions for scrapers, cleanup, and monitoring

### What Needs Deployment
1. **No blocking deployment tasks remain**
2. **Ongoing release discipline** via explicit `[release]` commits
3. **Launch-material follow-through** (LinkedIn post, screenshots, walkthrough)

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

## Historical Approach: Render (Superseded)

**Platform:** Render (container-based hosting)

1. **Frontend on Render**
   - Next.js support via Web Service
   - Free tier available (with limitations)
   - Auto-deploy from GitHub
   - Environment variables: `NEXT_PUBLIC_MAPBOX_TOKEN`, `DATABASE_URL`

2. **Scrapers on GitHub Actions** (already configured)
   - Runs every 4 hours in current cost-control mode
   - Connects to Neon PostgreSQL
   - No additional hosting cost

3. **Database on Neon** (already in production)
   - Free tier: 512MB storage
   - Auto-pause when idle

**Total Cost:** $0/month on free tiers (Render free tier has spin-down on inactivity)

---

## Decisions Made

### 1. Frontend Hosting Platform
- [x] **Render** (account created)

### 2. Custom Domain
- [x] Use default Render domain (`*.onrender.com`) for now
- Custom domain may be purchased later

### 3. Alerts for Scraper Failures
- [x] **Pushover notifications** (mobile push notifications)
- Required credentials: `PUSHOVER_USER_KEY`, `PUSHOVER_API_TOKEN`

### 4. Hosting Tier
- [x] **Free tier** (instances spin down after 15 min inactivity)
- First request after spin-down will be slow (~30s cold start)
- Upgrade to paid ($7/month) later if needed

### 5. Monitoring/Analytics
- [ ] Enable Render metrics dashboard (optional)
- [ ] Set up Sentry error tracking (optional)
- [x] Monitor via GitHub Actions + Pushover alerts for now

---

## User Actions Required

Once decisions are made above:

### Step 1: Configure GitHub Secrets
Add to repository Settings → Secrets → Actions:

| Secret Name | Value | Required |
|-------------|-------|----------|
| `DATABASE_URL` | Neon connection string | Yes |
| `PUSHOVER_USER_KEY` | Pushover user key | Yes |
| `PUSHOVER_API_TOKEN` | Pushover API token | Yes |

**Getting Pushover credentials:**
1. Create account at [pushover.net](https://pushover.net)
2. Install Pushover app on your phone
3. Your **User Key** is on the dashboard after login
4. Create an **Application** → get the **API Token**

### Step 2: Deploy Frontend
Instructions will depend on platform chosen (see platform-specific guides below).

### Step 3: Verify Deployment
- [ ] Frontend accessible at public URL
- [ ] Map displays with hospital markers
- [ ] `/methods` page loads
- [ ] API routes returning data
- [ ] Scraper cron runs successfully

---

## Platform-Specific Deployment Instructions

### Render (Selected)

1. Go to [dashboard.render.com](https://dashboard.render.com) → Sign in
2. "New" → "Web Service" → Connect GitHub repo
3. Configure service:
   - **Name:** `waittime-canada` (or preferred name)
   - **Root Directory:** `frontend`
   - **Environment:** Node
   - **Build Command:** `npm install && npm run build`
   - **Start Command:** `npm start`
4. Add environment variables:
   - `NEXT_PUBLIC_MAPBOX_TOKEN` = (Mapbox token)
   - `DATABASE_URL` = (Neon connection string)
5. Deploy

**Notes:**
- Free tier instances spin down after 15 minutes of inactivity (first request may be slow)
- Paid tier ($7/month) keeps instance running continuously
- Deploys are release-gated in this repo; production deploy requires commit message containing `[release]` or `[deploy]`

---

### If Vercel Selected (Alternative):

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
   - Check scraper-cron runs every 4 hours
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

## All Decisions Complete

All deployment decisions have been made. Ready to proceed with deployment:

1. ✅ **Platform:** Render (free tier)
2. ✅ **Domain:** Default `*.onrender.com`
3. ✅ **Alerts:** Pushover notifications
4. ✅ **Tier:** Free (with spin-down)

---

*All decisions made. Ready for deployment.*
