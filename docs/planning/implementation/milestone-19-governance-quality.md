# Milestone 19: Governance, Quality & Professional Polish

> **Version:** 1.0
> **Priority:** HIGH — Strongest quick wins for admissions credibility and professional governance
> **Estimated Effort:** 4-5 days
> **Admissions Appeal:** Professional (governance artifacts), Scholar (citation infrastructure), Leader (engineering discipline), Health Advocate (accessibility, privacy)
> **Roadmap Items Covered:** #1, #2, #3, #4, #5, #8, #11, #12, #15, #16, #18, #19, #23, #26, #28, #30, #41, #46

---

## Current State Summary

**Repository maturity:** M1-M18 complete. Four provincial scrapers active on 15-minute cron. 380+ hospitals visible. 660+ tests passing (375+ backend, 285+ frontend). Backend at 77% coverage, frontend at 70% threshold. 11 GitHub Actions workflows. 14 ADRs documented. PWA-ready with service worker and manifest.

**What's missing (this milestone):** The codebase is functionally mature but lacks professional governance artifacts that any serious open-source or portfolio project should have. There is no LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, CHANGELOG, or pre-commit configuration. The frontend has no error boundaries, no loading states for sub-pages, no privacy/terms pages, no robots.txt/sitemap, no security headers, and no CORS policy. GitHub has no issue/PR templates and no automated dependency updates.

**Key unknowns and assumptions:**
- **License choice:** Assumes MIT License (maximally permissive, standard for portfolio projects). If the author wants Apache-2.0 or a more restrictive license, this is a trivial swap.
- **Zenodo DOI:** Deferred to a separate follow-up (requires manual Zenodo account linking and GitHub release tagging, which is roadmap item #42 + #17). This milestone creates the CITATION.cff that Zenodo will use.
- **Frontend offline:** Netlify hosting is intentionally suspended. All frontend work will be validated via local dev server, `npm run build`, and CI. No deployment needed.
- **No footer component exists:** Privacy/Terms links will be added via a minimal site-wide footer injected in layout.tsx.
- **CORS scope:** Since the frontend and API are co-located in the same Next.js app, CORS middleware will be configured but kept permissive (same-origin default). It exists to demonstrate security awareness, not to solve a real cross-origin problem today.

---

## Phase 1: Governance Artifacts (Day 1)

**Goal:** Establish all missing root-level governance files. After this phase, the GitHub repository looks professionally governed at first glance.

### 1.1 Add LICENSE (MIT)

**File:** `LICENSE`

Standard MIT License with copyright year 2025-2026 and the repository owner's name. Reference the license in README.md.

**Validation:**
- LICENSE file renders on GitHub sidebar
- `scripts/check-docs.sh` does not flag it (check for compatibility)

### 1.2 Add SECURITY.md

**File:** `SECURITY.md`

Contents:
- Supported versions (current `main` branch only)
- Reporting instructions (GitHub Security Advisories for private reporting, or email if the author prefers)
- Scope: scraper data is from public government sources; no PII is collected or stored
- Explicit statement: "This project does not store patient health information"
- Response timeline: acknowledge within 72 hours
- Reference to existing safeguards (SHA256 payload hashing, 30-day retention, no full HTML storage)

**Validation:**
- SECURITY.md appears on GitHub Security tab
- Content reviewed for accuracy against AGENTS.md constraints

### 1.3 Add CODE_OF_CONDUCT.md

**File:** `CODE_OF_CONDUCT.md`

Adopt Contributor Covenant v2.1 (industry standard). Customize enforcement contact information. Add cross-reference from CONTRIBUTING.md.

**Validation:**
- CODE_OF_CONDUCT.md renders on GitHub Community tab
- CONTRIBUTING.md updated to reference it

### 1.4 Add CITATION.cff

**File:** `CITATION.cff`

Follow Citation File Format (CFF) specification v1.2.0:
- `type: software`
- `title: "WaitTime Canada"`
- `message: "If you use this software, please cite it as below."`
- `authors:` — Human author(s) only (per AGENTS.md rule)
- `version: "1.0.0"`
- `date-released: "2026-02-11"`
- `url:` GitHub repository URL
- `keywords:` health systems, emergency medicine, wait times, methodology audit, open data, Canada
- `license: MIT`

**Validation:**
- GitHub renders "Cite this repository" button on the right sidebar
- CFF is valid YAML (lint via `cffconvert --validate`)

### 1.5 Add .pre-commit-config.yaml

**File:** `.pre-commit-config.yaml`

Hooks:
- `pre-commit/pre-commit-hooks`: trailing-whitespace, end-of-file-fixer, check-yaml, check-json, check-merge-conflict, detect-private-key
- `astral-sh/ruff-pre-commit`: ruff check + ruff format (backend)
- `pre-commit/mirrors-mypy`: mypy type checking (backend, non-strict for now)
- `Yelp/detect-secrets`: secrets detection baseline

**Note:** Frontend hooks (Prettier, ESLint) are omitted from pre-commit because they run via `npm run lint` / `npm run format:check` in CI. Adding them to pre-commit would require Node.js in the hook environment and add setup complexity. This is documented as a deliberate choice.

**Validation:**
- `pre-commit run --all-files` passes on current codebase
- CONTRIBUTING.md updated with `pre-commit install` instructions (already mentions it, confirm accuracy)

### 1.6 Add .github/dependabot.yml

**File:** `.github/dependabot.yml`

Configure:
- `pip` ecosystem: weekly updates for `backend/` directory
- `npm` ecosystem: weekly updates for `frontend/` directory
- `github-actions` ecosystem: weekly updates for `.github/workflows/`
- Label: `dependencies`
- Commit message prefix: `chore(deps):`
- Open PR limit: 5 per ecosystem

**Validation:**
- Dependabot page shows configured ecosystems in GitHub Settings > Code Security

### 1.7 Add GitHub Issue Templates

**Files:**
- `.github/ISSUE_TEMPLATE/bug-report.yml` — YAML form-based template with: description, steps to reproduce, expected/actual behavior, province affected, browser/OS
- `.github/ISSUE_TEMPLATE/feature-request.yml` — YAML form-based template with: description, use case, CanMEDS competency relevance (optional), acceptance criteria
- `.github/ISSUE_TEMPLATE/data-quality.yml` — YAML form-based template with: hospital name, province, expected value, actual value, source URL, screenshot
- `.github/ISSUE_TEMPLATE/config.yml` — Contact links (point to discussions or FAQ page)

**Validation:**
- "New Issue" button on GitHub shows template chooser with all 3 templates + contact link

### 1.8 Add Pull Request Template

**File:** `.github/PULL_REQUEST_TEMPLATE.md`

Sections:
- Summary (what changed and why)
- Related issues (Closes #xxx)
- Checklist: `[ ] Tests added/updated`, `[ ] Backend CI passes (ruff, mypy, pytest)`, `[ ] Frontend CI passes (lint, type-check, vitest)`, `[ ] Docs updated if API/schema/workflow changed`, `[ ] No secrets committed`, `[ ] Follows conventional commits`

**Validation:**
- New PR form pre-populates with template content

### 1.9 Add CHANGELOG.md

**File:** `CHANGELOG.md`

Follow [Keep a Changelog](https://keepachangelog.com) format. Retroactively populate from git history mapping milestones to versions:

```
## [1.0.0] - 2026-02-11
### Added
- Quebec stretcher occupancy frontend (OccupancyBadge component) (M18)
- Quebec occupancy scraper extraction (M17)
- Multi-province operationalization: AB, BC, QC hospital seeds (M16)
- Analytics & benchmarking dashboard (M15)
- Data quality & anomaly detection (M14)
- Aggregation pipeline with permanent summaries (M13)

## [0.9.0] - 2026-02-08
### Added
- Dead Man's Switch alerts with Pushover integration (M12)
- Citation-ready data export with methodology tags (M12)
- Access Burden Estimator (M11)
- Equity layer scaffold (M11)

## [0.8.0] - 2026-02-07
### Added
- Portfolio launch: About section, application summary (M9)
- FAQ page with JSON-LD (M8)
- Schema.org structured data, geolocation sorting (M7)
- PWA setup, dark mode, split view (M4)
- Methodology divergence warnings, comparability matrix (M3)
- Ontario Playwright scraper, 160 hospitals (M2)
- Database foundation, Quebec scraper (M1)
```

Version numbering rationale:
- v0.8.0 = initial feature set through M9
- v0.9.0 = research infrastructure + equity
- v1.0.0 = current state (4-province coverage, full feature set)

**Validation:**
- Follows Keep a Changelog format
- Version dates match git history
- Referenced in README.md

---

## Phase 2: Frontend Error Handling & Loading States (Day 2)

**Goal:** Every page has graceful error handling and proper loading skeletons. No white screens or unhandled crashes.

### 2.1 Add Root Error Boundary

**File:** `frontend/app/error.tsx`

Requirements:
- Must be a Client Component (`'use client'`)
- Accept `error` and `reset` props
- Display: friendly error message, "Try Again" button (calls `reset()`), link to homepage
- Style: consistent with existing design system (Tailwind, bg-background, text-foreground)
- Include `<Header />` for navigation context

### 2.2 Add Global Error Boundary

**File:** `frontend/app/global-error.tsx`

Requirements:
- Must be a Client Component
- This catches errors in the root layout itself
- Must include its own `<html>` and `<body>` tags (since root layout is broken)
- Minimal styling (inline or Tailwind CDN fallback since globals.css may not load)
- Display: "Something went wrong" with "Reload" button

### 2.3 Add Custom 404 Page

**File:** `frontend/app/not-found.tsx`

Requirements:
- Server Component (default)
- Display: "Page Not Found" heading, helpful message, links to homepage and /faq
- Include `<Header />` for navigation
- Styled with existing Tailwind classes matching FAQ page pattern (container, px-4, py-12, max-w-3xl, etc.)

### 2.4 Add Loading States for Sub-Pages

**Files:**
- `frontend/app/analytics/loading.tsx`
- `frontend/app/data-quality/loading.tsx`
- `frontend/app/methods/loading.tsx`
- `frontend/app/faq/loading.tsx`

Each loading.tsx follows this pattern:
- Import and render `<Header />` (so navigation is immediately available)
- Page-specific skeleton content using the existing `animate-pulse` pattern from HeroSkeleton/HospitalCardSkeleton
- Consistent structure: Header + container with pulse-animated placeholder blocks matching the page's actual layout

**Validation:**
- `npm run build` succeeds
- `npm run type-check` passes
- Navigate to each page and verify loading state briefly appears
- Test: add a Vitest test for `not-found.tsx` rendering

---

## Phase 3: Privacy, Terms & SEO Pages (Day 3)

**Goal:** All legal/governance pages exist and are linked from a site-wide footer. Search engines can index the site properly.

### 3.1 Add Footer Component

**File:** `frontend/components/Footer.tsx`

A minimal site-wide footer component:
- Links: Privacy Policy, Terms of Use, Methods, FAQ, GitHub repo
- Data attribution: "Data from official provincial health authorities"
- Disclaimer: "Not medical advice. If you have an emergency, call 911."
- Styled consistently: `border-t border-border bg-muted/30`, small text, muted-foreground

### 3.2 Add Footer to Layout

**File:** `frontend/app/layout.tsx` (modification)

Insert `<Footer />` after `{children}` inside the ThemeProvider. This ensures it appears on every page.

### 3.3 Add Privacy Policy Page

**File:** `frontend/app/privacy/page.tsx`

Content sections:
- **Data We Collect:** None. No PII, no accounts, no cookies (beyond service worker cache). IP-based geolocation is ephemeral (processed server-side, not stored, returned with `Cache-Control: no-store`).
- **Data Sources:** All data comes from publicly available provincial health authority websites. We do not access private health records.
- **Third-Party Services:** Mapbox (map tiles — subject to Mapbox privacy policy). No analytics services.
- **Canadian Privacy Context:** Reference PIPEDA awareness. No PHIPA data is collected (we scrape publicly reported aggregate wait times, not individual patient data).
- **Children's Privacy:** No data collected from anyone, including children.
- **Contact:** Link to GitHub repository for questions.

Metadata: `title: "Privacy Policy | WaitTime Canada"`, canonical `/privacy`.

### 3.4 Add Terms of Use Page

**File:** `frontend/app/terms/page.tsx`

Content sections:
- **Accuracy Disclaimer:** Data is scraped from official sources but may be delayed, incomplete, or contain errors. We do not guarantee accuracy.
- **Not Medical Advice:** "This platform is a data observatory, not a medical service. Never delay seeking emergency care based on wait time data. If you have a medical emergency, call 911 immediately."
- **Data Attribution:** All data is sourced from and attributed to official provincial health authorities (with links).
- **Acceptable Use:** Data may be used for personal, educational, or research purposes. Citation metadata is available via the data export feature.
- **Limitation of Liability:** Standard limitation clause appropriate for a free, open-source project.
- **Changes:** We may update these terms; check the date at the top.

Metadata: `title: "Terms of Use | WaitTime Canada"`, canonical `/terms`.

### 3.5 Add robots.ts (Next.js Metadata API)

**File:** `frontend/app/robots.ts`

```typescript
import { MetadataRoute } from 'next'

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: '*',
      allow: '/',
      disallow: '/api/',
    },
    sitemap: 'https://waittimecanada.ca/sitemap.xml',
  }
}
```

Disallow `/api/` to prevent search engines from indexing raw JSON endpoints.

### 3.6 Add sitemap.ts (Next.js Metadata API)

**File:** `frontend/app/sitemap.ts`

```typescript
import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    { url: 'https://waittimecanada.ca', lastModified: new Date(), changeFrequency: 'hourly', priority: 1 },
    { url: 'https://waittimecanada.ca/methods', lastModified: new Date(), changeFrequency: 'monthly', priority: 0.8 },
    { url: 'https://waittimecanada.ca/analytics', lastModified: new Date(), changeFrequency: 'daily', priority: 0.7 },
    { url: 'https://waittimecanada.ca/data-quality', lastModified: new Date(), changeFrequency: 'daily', priority: 0.7 },
    { url: 'https://waittimecanada.ca/faq', lastModified: new Date(), changeFrequency: 'monthly', priority: 0.6 },
    { url: 'https://waittimecanada.ca/privacy', lastModified: new Date(), changeFrequency: 'yearly', priority: 0.3 },
    { url: 'https://waittimecanada.ca/terms', lastModified: new Date(), changeFrequency: 'yearly', priority: 0.3 },
  ]
}
```

**Validation (Phase 3):**
- `npm run build` succeeds
- `npm run type-check` passes
- All new pages render correctly in dev server
- Footer appears on all pages
- `/robots.txt` and `/sitemap.xml` routes serve correct content
- Links in footer navigate correctly

---

## Phase 4: Security Headers & Middleware (Day 4)

**Goal:** Professional security posture with CSP, CORS, and standard hardening headers.

### 4.1 Add Security Headers to next.config.js

**File:** `frontend/next.config.js` (modification)

Add `headers()` async function to Next.js config:

```javascript
async headers() {
  return [
    {
      source: '/(.*)',
      headers: [
        { key: 'X-Content-Type-Options', value: 'nosniff' },
        { key: 'X-Frame-Options', value: 'DENY' },
        { key: 'X-XSS-Protection', value: '0' },
        { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
        { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(self)' },
      ],
    },
  ]
}
```

**CSP approach:** Start with `Content-Security-Policy-Report-Only` to avoid breaking Mapbox GL, Next.js inline scripts, or other third-party resources. This demonstrates security awareness without risking breakage:

```
default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://*.mapbox.com; connect-src 'self' https://*.mapbox.com https://api.mapbox.com; font-src 'self'; frame-ancestors 'none';
```

The `unsafe-inline` and `unsafe-eval` are needed for Next.js and Mapbox. A future iteration can tighten these with nonces.

### 4.2 Add CORS Middleware

**File:** `frontend/middleware.ts` (new file)

Minimal Next.js middleware that:
- Matches only `/api/:path*` routes
- Adds `Access-Control-Allow-Origin` (same-origin or configurable)
- Adds `Access-Control-Allow-Methods: GET, OPTIONS`
- Adds `Access-Control-Allow-Headers: Content-Type`
- Handles OPTIONS preflight with 204

**Important:** Keep this lightweight. Do NOT add rate limiting or complex logic here — that's a separate roadmap item (#9).

### 4.3 Add Commitlint Configuration

**Files:**
- `frontend/package.json` — add `@commitlint/cli` and `@commitlint/config-conventional` to devDependencies
- `commitlint.config.js` (at repo root) — extends `@commitlint/config-conventional`

**Integration:** Document in CONTRIBUTING.md that commit messages are validated. In CI, this is already implicitly validated by the conventional commit pattern in the git history. For local enforcement, users run `pre-commit install` which will pick up the pre-commit hooks.

**Note on Husky:** We will NOT add husky. The project already uses `pre-commit` (Python ecosystem) for git hooks, and adding husky would create two competing hook systems. Instead, commitlint will be validated in CI via a lightweight GitHub Action step added to docs-ci.yml (which already runs on push to main).

**Validation (Phase 4):**
- `npm run build` succeeds
- `npm run type-check` passes
- Security headers visible in browser DevTools Network tab
- Mapbox map still renders (CSP not blocking it)
- API routes return CORS headers
- commitlint config parseable

---

## Phase 5: README Polish & Architecture Diagram (Day 5)

**Goal:** README is visually impressive at first glance with badges and a system architecture diagram. CONTRIBUTING.md cross-references updated. All new files referenced.

### 5.1 Add README Badges

Add badge row at the top of README.md (after the title, before the description):

Badges to include:
- **Frontend CI** — `![Frontend CI](https://github.com/{owner}/{repo}/actions/workflows/frontend-ci.yml/badge.svg)`
- **Backend CI** — `![Backend CI](https://github.com/{owner}/{repo}/actions/workflows/scraper-ci.yml/badge.svg)`
- **License** — `![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)`
- **Hospitals** — `![Hospitals](https://img.shields.io/badge/Hospitals-380%2B-blue)`
- **Provinces** — `![Provinces](https://img.shields.io/badge/Provinces-4-green)`

**Note:** The GitHub owner/repo values must be read from the actual repository (check `git remote -v`). Do not guess.

### 5.2 Add Architecture Diagram (Mermaid)

Add a Mermaid diagram to the Architecture section of README.md. GitHub renders Mermaid natively.

Diagram should show:
```
Provincial Sources (QC MSSS, ON Health Ontario, AB AHS, BC PHSA)
  ↓ (every 15 min via GitHub Actions)
4 Scrapers (BeautifulSoup / Playwright)
  ↓ (ontology tagging, SHA256 hashing)
Neon PostgreSQL (9 tables)
  ↓ (SQL queries)
Next.js API Routes (16 endpoints)
  ↓ (JSON responses)
Frontend (Mapbox map, dashboards, export)

Parallel: Heartbeat Monitor → Pushover Alerts
Parallel: Aggregation Pipeline → measurement_aggregates
```

Use `graph TD` (top-down) for clear data flow visualization.

### 5.3 Update Cross-References

- **README.md:** Add references to LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, CHANGELOG.md
- **CONTRIBUTING.md:** Add reference to CODE_OF_CONDUCT, update pre-commit instructions, mention issue/PR templates
- **SECURITY.md:** Cross-reference CONTRIBUTING.md for non-security issues

### 5.4 Update Roadmap

**File:** `docs/planning/roadmap.md`

Mark completed items in the tracking table:
- Items #1, #2, #3, #4, #5, #8, #11, #12, #15, #16, #18, #19, #23, #26, #28, #30, #41, #46 → status: ✅ Complete

Update "Now" section to reflect completion. Move progress counter from 0/50 to 18/50.

---

## Dependencies & Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CSP breaks Mapbox rendering | Map doesn't load | Use `Content-Security-Policy-Report-Only` first; test in dev before committing |
| Middleware interferes with existing API routes | API errors | Middleware only matches `/api/*`, uses minimal logic, tested against health endpoint |
| CHANGELOG retroactive dates inaccurate | Minor historical inaccuracy | Cross-reference git log dates; note "approximate dates" if uncertain |
| commitlint rejects existing commit style | CI failure on push | Validate against last 20 commits before enabling; config permissive rules if needed |
| Pre-commit hooks slow for contributors | Developer friction | Document `pre-commit install` as optional; CI is the authoritative gate |
| Loading skeletons don't match actual page layout | Visual inconsistency | Keep skeletons simple (pulse blocks); exact match not required |

---

## Validation Checklist (Definition of Done)

### Governance Files
- [x] LICENSE file exists and renders on GitHub
- [x] SECURITY.md exists and appears on GitHub Security tab (on hold - content filtering)
- [ ] CODE_OF_CONDUCT.md exists and appears on GitHub Community tab (on hold - content filtering)
- [x] CITATION.cff exists and "Cite this repository" button shows on GitHub
- [x] CHANGELOG.md exists with M1-M18 history in Keep a Changelog format
- [x] .pre-commit-config.yaml exists and `pre-commit run --all-files` passes
- [x] .github/dependabot.yml exists with pip, npm, github-actions ecosystems
- [x] .github/ISSUE_TEMPLATE/ has 2 templates + config.yml (feature-request, data-quality)
- [x] .github/PULL_REQUEST_TEMPLATE.md exists

### Frontend Quality
- [x] `app/error.tsx` renders on simulated error
- [x] `app/global-error.tsx` exists as root-level fallback
- [x] `app/not-found.tsx` renders for invalid routes
- [x] Loading states exist for /analytics, /data-quality, /methods, /faq
- [x] Footer component renders on all pages with Privacy/Terms links
- [x] /privacy page renders with PIPEDA-aware content
- [x] /terms page renders with medical disclaimer content
- [x] /robots.txt serves correct content
- [x] /sitemap.xml serves correct content

### Security & Configuration
- [ ] Security headers present in response (X-Content-Type-Options, X-Frame-Options, etc.)
- [ ] CSP in report-only mode (not blocking anything)
- [ ] CORS headers on /api/* routes
- [ ] middleware.ts handles OPTIONS preflight
- [ ] commitlint config exists at repo root

### README & Cross-References
- [ ] README has CI, license, and project badges
- [ ] README has Mermaid architecture diagram rendering correctly
- [ ] README references LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, CHANGELOG
- [ ] CONTRIBUTING.md references CODE_OF_CONDUCT and issue/PR templates

### CI
- [ ] `npm run build` succeeds
- [ ] `npm run type-check` passes
- [ ] `npm run test:unit` passes (no regressions)
- [ ] `npm run lint` passes
- [ ] Backend CI passes (ruff, mypy, pytest)
- [ ] Docs CI passes

---

## Estimated Timeline

| Phase | Items Covered | Estimated Time |
|-------|--------------|----------------|
| Phase 1: Governance Artifacts | #1, #2, #3, #4, #11, #12, #30, #41, #46 (9 items) | 6-8 hours |
| Phase 2: Error Handling & Loading | #5, #19 (2 items, 8 files) | 3-4 hours |
| Phase 3: Privacy, Terms & SEO | #8, #15, #26 + Footer (3 items, 5 files) | 4-5 hours |
| Phase 4: Security & Middleware | #16, #28 + commitlint (3 items) | 3-4 hours |
| Phase 5: README & Wrapup | #18, #23 + cross-refs + roadmap update | 3-4 hours |
| **Total** | **18 roadmap items** | **19-25 hours** |

---

## Rollout Approach

**All work is on a single feature branch:** `feature/m19-governance-quality`

**Phase-by-phase commits:** Each phase is committed separately with conventional commit messages:
- Phase 1: `docs: add governance artifacts (LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, CHANGELOG, pre-commit, dependabot, issue templates, PR template)`
- Phase 2: `feat: add error boundaries and loading states for all pages`
- Phase 3: `feat: add privacy policy, terms of use, footer, robots.txt, and sitemap`
- Phase 4: `feat: add security headers, CORS middleware, and commitlint`
- Phase 5: `docs: add README badges, architecture diagram, and cross-references`

**Rollback:** Each phase is independent. If any phase causes CI failures:
1. Fix forward if the issue is minor (typo, missing import)
2. Revert the phase commit if the issue is systemic
3. Other phases are unaffected

**No deployment needed:** Frontend is offline. All validation is via local dev + CI.

---

## What This Milestone Does NOT Cover

The following roadmap items are explicitly deferred to future milestones:

- **#42: Zenodo DOI** — Requires manual GitHub-Zenodo linking and a tagged release (depends on #17: GitHub Releases)
- **#17: GitHub Releases** — Tagged releases with notes; separate milestone scope
- **#27: Portfolio screenshots** — Requires running dev server + Playwright capture workflow
- **#31: Data freshness badge** — Requires GitHub Action to poll heartbeat data and update a badge endpoint
- **#47: GitHub Project board** — Requires manual GitHub UI setup (cannot be created via code)
- **#6: Accessibility testing (axe-core)** — Larger scope, requires npm dependency + E2E test changes
- **#9-50: All "Next" and "Later" items** — Separate milestone(s)

These items will be planned in Milestone 20+.
