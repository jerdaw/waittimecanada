# Implementation Roadmap

## Current Status (Updated 2026-02-14)

**Progress:** M18 Complete (Occupancy Frontend UI) | M17 Complete (Quebec Occupancy Implementation) | M16 Complete (Multi-Province Operationalization) | Milestone 15 Complete & Archived | Milestone 14 Complete & Archived | M9 production smoke + readiness automation implemented | M9 repo polish + launch copy artifacts completed | M9 screenshot automation implemented | M9 testimonial governance hardening implemented | M9 About section component completed | M11 equity layer scaffold + linkage summary implemented | M12 occupancy availability contract implemented | CI optimization pass implemented | Documentation modernization + docs quality automation implemented

**Strategic Direction:** **Four-province breadth achieved** (ON, QC, AB, BC). All four scrapers active in production via GitHub Actions, 380+ hospitals visible across all provinces, methodology documentation complete for all provinces, regional analytics data seeded for 15 regions. **Quebec stretcher occupancy fully operational end-to-end** - scraper extraction, API endpoint, and visual indicators on hospital cards. **Heartbeat monitoring operational** with Pushover alerting for stale data. **Temporary cost-control cadence is active as of February 14, 2026** (`scraper-cron: */30`, heartbeat `--max-age 90`) due to Neon transfer usage. **All 662 tests passing** (375 backend + 287 frontend) with 77% backend coverage.

**Deployment Note (2026-02-08):** Frontend public hosting is intentionally offline for now to avoid unnecessary free-tier credit usage. Production smoke workflow is disabled until a public URL is intentionally re-enabled.

---

## Completed Milestones

| Milestone | Summary |
|-----------|---------|
| **M1: Database Foundation** | Neon PostgreSQL schema, ontology enums, Quebec scraper, heartbeat monitoring |
| **M2: Ontario End-to-End** | Ontario Playwright scraper, Nominatim geocoding, Mapbox frontend, 160 hospitals |
| **M3: Methodology Warnings** | DivergenceWarning component, /methods comparability matrix, hospital detail modal |
| **M4: Polish & Launch** | 911 banner, dark mode, split view, trend charts, hero section, PWA setup |
| **M7: UX Polish & SEO** | Schema.org structured data, skeleton loading, search/filter, geolocation, live indicators |
| **M8: UX Enhancements** | Expandable cards, FAQ page, quick actions, landing page architecture, distance sorting |
| **M9: Portfolio Launch** (partial) | About section, LinkedIn post draft, screenshot guide, application summary |
| **M10: Multi-Province** (partial) | Alberta scraper skeleton, BC scraper (ADR-0007). Superseded by M16. |
| **M11: Access & Equity** (partial) | Access Burden Estimator with fuel + parking cost (ADR-0005, 21 tests) |
| **M12: Research Infra** (partial) | Citation-ready data export (19 tests), Dead Man's Switch alerts (7 tests), SystemStatus component, occupancy availability endpoint/UI state |
| **M13: Aggregation Pipeline** | Permanent hourly/daily/weekly/monthly aggregates, backfill CLI, enhanced trends (90d/6m/1y), extended data export (ADR-0008) |
| **M14: Data Quality & Anomaly Detection** | DataQualityService, AnomalyDetectionService, MethodologyChangeDetector, /data-quality dashboard, 3 new DB tables (ADR-0009) |
| **M15: Analytics & Benchmarking** | Peer benchmarking, temporal pattern analysis, regional intelligence mapping, system trend dashboard, dedicated /analytics page |
| **M16: Multi-Province Operationalization** | Trusted source auto-approval, hospital seed data (65 hospitals for AB/BC/QC), methodology docs for all 4 provinces, region data (15 regions), 380+ hospitals visible |
| **M17: Quebec Occupancy Implementation** | Quebec scraper extracts stretcher occupancy percentages, API endpoint returns real-time occupancy data, 17 unit tests, STRETCHER_OCCUPANCY metric family |
| **M18: Occupancy Frontend UI** | OccupancyBadge component with color-coded indicators, hospital API includes occupancy data, visual display on Quebec hospital cards, methodology note, 15 unit tests |
| **Operations: Production Verification** | Verified all 4 scrapers operational, heartbeat monitoring active, BC source metadata corrected, comprehensive operations documentation created |

---

## Next Steps

All planned milestones through M18 and Operations verification are complete. Future work items are tracked in the "Later" section below.

## Roadmap Operating Model

### Planning Standards
- **Single source of truth:** This file is the canonical roadmap status. Detailed execution plans live in milestone docs.
- **Horizon-based planning:** Work is prioritized as `Now` (0-2 weeks), `Next` (2-6 weeks), and `Later` (6+ weeks).
- **Priority discipline:** `P0` = correctness/reliability blockers, `P1` = capability delivery, `P2` = polish.
- **Review cadence:** Refresh this roadmap at least weekly and after any milestone closeout or major ops decision.

### Definition of Done (Roadmap Items)
- Code merged to `main` with tests passing in CI.
- Required docs/ADRs updated if architecture or policy changed.
- Operational impact confirmed (alerts, workflows, secrets, deployment posture).
- Item status reflected in this roadmap and no duplicate open tasks remain.

### Release and Cost Policy (Current)
- Netlify deploys are intentionally release-gated and frontend public hosting is intentionally offline.
- Production smoke workflow remains disabled until a public frontend URL is intentionally re-enabled.
- Scraper reliability workflows (`scraper-cron`, heartbeat monitor, readiness checks) remain active.
- Temporary cost-control mode is active from **February 14, 2026** through post-reset review: `scraper-cron` at `*/30` and heartbeat `--max-age 90`.
- Post-reset target (review on **March 3, 2026**): move to less aggressive but still cost-saving defaults `scraper-cron: */20` and heartbeat `--max-age 75`.

## Active Roadmap (Now / Deferred / Later)

### Now (0-2 weeks) — CRITICAL PATH TO DEPLOYMENT

**PRIORITY 0: Deploy and Validate Core Product**

This section focuses on **making the product work and accessible** before polishing.

- [ ] **P0 / Deploy frontend to production** — Re-enable Netlify or deploy to Vercel free tier for public access (2-4h)
  - **Blocker:** Cost concern resolved or alternative found
  - **Deliverables:** Live URL, environment variables configured, deployment automated
  - **Why Critical:** Cannot validate product, capture screenshots, or test with users without deployment

- [ ] **P0 / Verify scrapers working in production** — Manual verification that all 4 scrapers run and populate database (1-2h)
  - **Verification:** Check `scraper_status` table, verify measurements inserted in last 24h, confirm no errors in logs
  - **Why Critical:** Core functionality may be broken and we don't know it

- [ ] **P0 / Spot-check data quality against official sources** — Manually compare 5-10 hospitals per province to source websites (2-3h)
  - **Verification:** ON hospital vs ER Watch, QC hospital vs MSSS portal, AB hospital vs AHS, BC hospital vs edwaittimes.ca
  - **Why Critical:** Methodology tags and values may be incorrect

- [ ] **P0 / End-to-end smoke test** — Test complete user journey: homepage → map → hospital detail → methodology comparison (30min)
  - **Verification:** All pages load, no console errors, data displays correctly, divergence warnings show when expected
  - **Why Critical:** Basic usability validation

- [ ] **P0 / Post-reset scraper cadence adjustment (due March 3, 2026)** — Replace temporary throttle with balanced cost-saving settings (30min)
  - **Current temporary mode:** `scraper-cron */30`, heartbeat `--max-age 90`
  - **Target mode:** `scraper-cron */20`, heartbeat `--max-age 75`
  - **Verification:** Monitor Neon transfer trend for 48h after change; ensure no stale-heartbeat alerts

- [x] **P0 / Document deployment blockers** — Comprehensive assessment of deployment readiness completed (1h)
  - **Deliverables:** `docs/planning/deployment-blockers.md` with full analysis, priority matrix, deployment sequence
  - **Status:** Product 85% ready for deployment - main blocker is hosting platform decision
  - **Finding:** Frontend and backend codebases complete and tested, scrapers configured, monitoring active

### Deferred - Waiting for Deployment & Validation

**These items are valuable but BLOCKED until core product is deployed and validated.**

**Prerequisite: Frontend deployed and accessible to public**

- [ ] **P1 / Expand portfolio screenshots** — Capture all 10+ views (light/dark, mobile, occupancy, divergence warnings) (4-8h)
  - 🚫 **Blocked by:** Frontend offline, no public URL to screenshot
  - ⏸️ **Defer until:** Frontend deployed and stable for 48+ hours

- [ ] **P1 / Add data freshness badge** — Dynamic README badge showing "Last scrape: X mins ago" (4-6h)
  - 🚫 **Blocked by:** Frontend offline, no live API to query
  - ⏸️ **Defer until:** Frontend deployed and scrapers verified working

**Prerequisite: Product validated by real users**

- [ ] **P1 / Add GitHub Project board** — Public roadmap with Backlog/In Progress/Done columns (1-2h)
  - 🚫 **Blocked by:** Don't know real priorities until users test product
  - ⏸️ **Defer until:** Product deployed and initial user feedback received

- [ ] **P1 / Populate stakeholder interview examples** — 2-3 example summaries demonstrating consent workflow (1-2h)
  - 🚫 **Blocked by:** No stakeholders to interview until product is public
  - ⏸️ **Defer until:** Product deployed and users identified

**Prerequisite: Schema and architecture stable**

- [ ] **P1 / Add mkdocs GitHub Pages deployment** — Live documentation site with `docs-deploy.yml` workflow (4-6h)
  - 🚫 **Blocked by:** Documentation may change after deployment validation
  - ⏸️ **Defer until:** Core functionality validated and stable

- [ ] **P1 / Add data dictionary** — Document all 9 tables, columns, enums, constraints with ER diagram (4-6h)
  - 🚫 **Blocked by:** Schema may change after production validation
  - ⏸️ **Defer until:** Database schema stable (no migrations for 2+ weeks)

- [ ] **P1 / Add contributor onboarding guide** — Architecture walkthrough, how to add scraper/API/page (4-6h)
  - 🚫 **Blocked by:** Architecture may change after deployment issues found
  - ⏸️ **Defer until:** Architecture proven stable in production

- [ ] **P1 / Add data flow documentation** — Per-scraper docs: source URL, format, parsing, ontology mapping, limitations (4-8h)
  - 🚫 **Blocked by:** Scrapers may need fixes after validation
  - ⏸️ **Defer until:** Scrapers verified accurate in production

**Prerequisite: No critical bugs or performance issues**

- [ ] **P1 / Add uptime/status history page** — `/status` page with 30/90-day scraper uptime metrics (4-8h)
  - 🚫 **Blocked by:** No uptime data until scrapers verified working
  - ⏸️ **Defer until:** Scrapers stable for 30+ days

- [ ] **P1 / Add data quality drift monitoring** — Weekly GitHub Action tracking measurement count, anomaly rate, success rate over time (4-8h)
  - 🚫 **Blocked by:** Need baseline data quality first
  - ⏸️ **Defer until:** Data quality validated and baseline established

### Completed - Already Done (But Maybe Premature)

**These were completed but may have been done too early:**

- [x] **P1 / Add LICENSE file** — Done, but doesn't matter if product not deployed
- [x] **P1 / Add CITATION.cff** — Done, but can't cite until product is public
- [x] **P1 / Add Zenodo DOI integration** — Automated setup done, but deferred activation
- [x] **P1 / Add README badges** — Done, but less valuable without live product
- [x] **P1 / Add architecture diagram** — Done, but may change after deployment
- [x] **P1 / Add error boundaries** — Done, good defensive coding
- [x] **P1 / Add loading states** — Done, good UX practice
- [x] **P1 / Add Privacy Policy** — Done, legally required
- [x] **P1 / Add Terms of Use** — Done, legally required
- [x] **P1 / Add robots.txt and sitemap** — Done, but useless without deployment
- [x] **P1 / Add CSP and security headers** — Done, good security practice
- [x] **P1 / Add .pre-commit-config.yaml** — Done, good dev practice
- [x] **P1 / Add Dependabot** — Done, good maintenance
- [x] **P1 / Add CORS configuration** — Done, needed for API
- [x] **P1 / Add git commit hooks** — Done, good dev practice
- [x] **P1 / Add GitHub Releases** — Done, but premature (not deployed yet)
- [x] **P1 / Add CHANGELOG.md** — Done, but premature
- [x] **P1 / Add GitHub issue templates** — Done, but no users to file issues yet
- [x] **P1 / Add PR template** — Done, but no contributors yet
- [x] **P1 / Add database migration documentation** — Done, good ops practice
- [x] **P1 / Add methodology comparison table asset** — Done, but can't share without deployment

⏸️ **On hold - Content filtering:**
- [ ] **P1 / Add SECURITY.md** — Blocked by Claude content policy
- [ ] **P1 / Add CODE_OF_CONDUCT.md** — Blocked by Claude content policy

### Next (2-6 weeks) — Medium-Impact Quality Improvements

**Category: Testing & Reliability**
- [ ] **P1 / Add accessibility testing (axe-core)** — WCAG compliance testing in Playwright E2E with CI checks (1-2d)
- [ ] **P1 / Increase backend test coverage to 85%+** — Focus on anomaly detection, methodology change detector, comparison service (1-2d)
- [ ] **P1 / Add Lighthouse CI** — Performance, accessibility, SEO scoring with GitHub Actions integration (4-8h)
- [ ] **P1 / Add mobile-responsive testing** — Playwright tests at 375px/414px viewports (4-8h)
- [ ] **P1 / Add visual regression testing** — Playwright visual comparison for homepage, /methods, /data-quality (4-8h)
- [ ] **P1 / Add property-based testing (Hypothesis)** — Formal verification of ontology comparability logic (4-8h)
- [ ] **P1 / Add end-to-end pipeline test** — Mock scrape → DB insert → API query → frontend render (4-8h)
- [ ] **P1 / Add API integration tests** — Hit actual/mocked database for all 16 endpoints with error cases (1-2d)

**Category: API & Backend Quality**
- [ ] **P1 / Add API rate limiting** — In-memory or Upstash Redis middleware for all 16 routes with 429 responses (4-8h)
- [ ] **P1 / Add OpenAPI/Swagger docs** — OpenAPI 3.0 spec for all endpoints with Swagger UI at `/api-docs` (1-2d)
- [ ] **P1 / Add API input validation (Zod)** — Comprehensive validation for all query params across 16 routes (4-8h)
- [ ] **P1 / Add structured logging to frontend** — JSON-formatted logging for all API routes (method, path, duration, status) (2-3h)
- [ ] **P1 / Add API response time tracking** — Timing middleware with P50/P95/P99 latency metrics (2-3h)
- [ ] **P1 / Add database health check enhancement** — Connection pool status, query latency, per-source freshness (2-3h)

**Category: Type Safety & Code Quality**
- [ ] **P1 / TypeScript strict mode audit** — Eliminate all `any`, `@ts-ignore`, `@ts-expect-error` in custom code (2-3h)
- [ ] **P1 / Backend mypy strict mode** — Enable `--strict` flag and fix all type errors (4-8h)
- [ ] **P1 / Database index optimization** — Add composite indexes for common query patterns with migration (2-3h)

**Category: Documentation & Onboarding**
- [ ] **P1 / Add mkdocs GitHub Pages deployment** — Live documentation site with `docs-deploy.yml` workflow (4-6h)
- [ ] **P1 / Add data dictionary** — Document all 9 tables, columns, enums, constraints with ER diagram (4-6h)
- [ ] **P1 / Add contributor onboarding guide** — Architecture walkthrough, how to add scraper/API/page (4-6h)
- [x] **P1 / Add database migration documentation** — `backend/migrations/README.md` with history and rollback procedures (2-3h)
- [ ] **P1 / Add data flow documentation** — Per-scraper docs: source URL, format, parsing, ontology mapping, limitations (4-8h)
- [x] **P1 / Add methodology comparison table asset** — Downloadable CSV/HTML of cross-province comparison matrix (2-3h)

**Category: Monitoring & Operations**
- [ ] **P1 / Add uptime/status history page** — `/status` page with 30/90-day scraper uptime metrics (4-8h)
- [ ] **P1 / Add data quality drift monitoring** — Weekly GitHub Action tracking measurement count, anomaly rate, success rate over time (4-8h)

**Category: GitHub Project Governance**
- [x] **P1 / Add GitHub issue templates** — Bug report, feature request, data quality issue templates (1-2h)
- [x] **P1 / Add PR template** — `.github/PULL_REQUEST_TEMPLATE.md` with testing/docs checklists (1-2h)
- [ ] **P1 / Add GitHub Project board** — Public roadmap with Backlog/In Progress/Done columns (1-2h)
- [ ] **P1 / Populate stakeholder interview examples** — 2-3 example summaries demonstrating consent workflow (1-2h)

### Later (6+ weeks) — Strategic Enhancements

**High-Value Expansion Features:**
- [ ] **P1 / French language support (i18n)** — next-intl with bilingual methodology warnings, emergency disclaimers, UI chrome (1-2w)
  - **Category:** Impact/Adoption | **CanMEDS:** Health Advocate, Collaborator
  - **Why:** Quebec hospitals serve French-speaking populations; demonstrates cultural competency
  - **Deliverables:** `/fr` route prefix, bilingual methodology warnings, language toggle, translated emergency banner

**Future Feature Development:**
- [ ] **P2 / Additional provinces** — Nova Scotia, New Brunswick scrapers with methodology documentation
- [ ] **P2 / Historical occupancy trends** — Daily/weekly patterns for Quebec stretcher occupancy
- [ ] **P2 / Enhanced equity layer** — StatsCan census tract income overlays with real data (currently scaffold)
- [ ] **P2 / Occupancy-based recommendations** — Smart hospital suggestions based on current occupancy
- [ ] **P2 / Portfolio launch** — Complete stakeholder interview and publish launch communications when public hosting is re-enabled
- [ ] **P2 / Performance optimization** — Smart scheduling (reduce frequency during overnight hours)
- [ ] **P2 / Monitoring dashboard** — Prometheus/Grafana integration for operational visibility
- [ ] **P2 / Advanced analytics** — Predictive wait time modeling based on historical patterns

---

## Strategic Context

Each feature maps to CanMEDS competencies for medical school admissions:

| Competency | Features |
|------------|----------|
| **Scholar** | Metric ontology, comparability matrix, citation export, aggregation pipeline, anomaly detection, methodology change detection, property-based testing, data dictionary, OpenAPI documentation, methodology comparison assets, Zenodo DOI |
| **Professional** | Clinical defensibility, divergence warnings, data quality transparency, peer benchmarking, SECURITY.md, LICENSE, CODE_OF_CONDUCT, privacy policy, terms of use, error boundaries, security headers, uptime monitoring |
| **Health Advocate** | Access Burden Estimator, equity layer, temporal access patterns, accessibility testing (WCAG), French language support, mobile responsiveness |
| **Leader** | Multi-province scaling, systems architecture, regional dashboards, data quality monitoring, GitHub Project board, contributor onboarding, release management, operational documentation |
| **Collaborator** | Province-aware telehealth routing, stakeholder interviews, issue/PR templates, CODE_OF_CONDUCT, CONTRIBUTING guidelines |

---

## Roadmap Item Categories & Admissions Value

All 50 roadmap items are categorized by their primary OMSAS/CanMEDS impact:

### Impact/Adoption (Evidence of Real-World Reach)
- **#7: French i18n** — Demonstrates cultural competency and expands genuine reach to Quebec FQN populations

### Leadership/Collaboration (Governance & Team Readiness)
- **#3: CODE_OF_CONDUCT.md** — Community governance
- **#46: GitHub issue templates** — Structured contribution workflow
- **#47: GitHub Project board** — Visible project management
- **#40: Contributor onboarding** — Architecture walkthrough for new contributors
- **#45: Stakeholder interview examples** — Demonstrates governance framework

### Communication/Documentation (Clarity & Professionalism)
- **#4: CHANGELOG.md** — Release history and semantic versioning
- **#10: OpenAPI/Swagger docs** — API reference for researchers
- **#18: README badges** — CI, coverage, license signals
- **#23: Architecture diagram** — Visual system design (Mermaid)
- **#27: Automated screenshots** — Portfolio artifacts (10+ views)
- **#36: Methodology comparison table** — Downloadable research artifact
- **#48: mkdocs GitHub Pages** — Live documentation site
- **#50: Data dictionary** — Formal documentation of all tables/columns/enums
- **#24: Data flow per-scraper** — Source-to-database pipeline documentation

### Professionalism/Governance (Legal & Ethical Standards)
- **#1: SECURITY.md** — Responsible disclosure policy
- **#2: LICENSE** — Legal clarity (MIT/Apache-2.0)
- **#8: Privacy Policy** — PIPEDA/PHIPA awareness
- **#26: Terms of Use** — Data disclaimers, no medical advice
- **#17: GitHub Releases** — Versioned release management
- **#20: Migration documentation** — Database evolution tracking
- **#30: Commitlint** — Enforced conventional commits

### Privacy/Security/Ethics (Responsible Data Handling)
- **#16: Content Security Policy** — XSS prevention, OWASP best practices
- **#11: .pre-commit-config.yaml** — Secrets detection, code quality gates
- **#12: Dependabot/Renovate** — Automated security updates
- **#28: CORS configuration** — Explicit origin policy

### Reliability/Quality (Engineering Excellence)
- **#5: Error boundaries** — Graceful failure handling (error.tsx, not-found.tsx)
- **#6: Accessibility testing (axe-core)** — WCAG compliance
- **#9: Rate limiting** — Abuse prevention
- **#13: Increase backend coverage to 85%+** — Thorough testing
- **#14: Lighthouse CI** — Performance/accessibility scoring
- **#15: robots.txt & sitemap** — SEO fundamentals
- **#19: Loading states** — Skeleton UX for all pages
- **#21: API input validation (Zod)** — All 16 routes validated
- **#22: API integration tests** — Database-backed E2E tests
- **#25: Structured logging (frontend)** — Professional log format
- **#29: Database health check** — Connection pool monitoring
- **#31: Data freshness badge** — Live "Last scrape: X mins ago"
- **#33: Visual regression testing** — Playwright pixel-diff
- **#34: TypeScript strict audit** — Zero `@ts-ignore` in custom code
- **#35: mypy strict mode** — Full backend type coverage
- **#38: Database index optimization** — Query performance tuning
- **#39: End-to-end pipeline test** — Scrape → DB → API → render
- **#44: Mobile-responsive testing** — 375px/414px viewport tests
- **#49: API response time tracking** — P50/P95/P99 latency monitoring

### Scholarship/Evaluation (Research Infrastructure)
- **#32: Property-based testing (Hypothesis)** — Formal verification of ontology comparability
- **#37: Uptime/status history page** — 30/90-day operational transparency
- **#41: CITATION.cff** — "Cite this repository" button
- **#42: Zenodo DOI** — Permanent citation link
- **#43: Data quality drift monitoring** — Weekly trend tracking

---

## Top 10 Highest-Impact Items for Admissions (Quick Wins)

Ranked by **admissions credibility per hour of effort**:

1. **#42: Zenodo DOI** — Instant research-grade artifact (1-2h)
2. **#41: CITATION.cff** — GitHub cite button (30min)
3. **#2: LICENSE** — Legal clarity (30min)
4. **#1: SECURITY.md** — Professional governance (1-2h)
5. **#18: README badges** — Visual credibility signals (1h)
6. **#23: Architecture diagram** — System clarity (1-2h)
7. **#31: Data freshness badge** — Proof of live system (4-6h)
8. **#3: CODE_OF_CONDUCT** — Community readiness (30min)
9. **#4: CHANGELOG.md** — Release discipline (4-6h)
10. **#48: mkdocs site** — Professional docs (4-6h)

---

## Implementation Plans

Active milestone plans in `docs/planning/implementation/`:
- `docs/planning/implementation/milestone-19-governance-quality.md` — **M19: Governance, Quality & Professional Polish (18 items: #1-5, #8, #11-12, #15-16, #18-19, #23, #26, #28, #30, #41, #46)**
- `docs/planning/implementation/milestone-9-launch.md` — Production deployment & stakeholder validation
- `docs/planning/implementation/milestone-11-equity.md` — Access Burden Estimator & equity layer
- `docs/planning/implementation/milestone-12-research.md` — Citation export & alert system
- `docs/planning/implementation/m9-remaining-user-actions.md` — M9 manual user action guide (active)

Archived (delivered):
- `docs/planning/archive/operations-production-verification.md` — Production verification & operational documentation
- `docs/planning/archive/milestone-18-occupancy-frontend.md` — Occupancy Frontend UI (M18)
- `docs/planning/archive/milestone-17-quebec-occupancy.md` — Quebec Occupancy Implementation (M17)
- `docs/planning/archive/milestone-16-multi-province-ops.md` — Multi-Province Operationalization (M16)
- `docs/planning/archive/milestone-15-analytics.md` — Analytics & benchmarking (M15)
- `docs/planning/archive/milestone-14-data-quality.md` — Data quality & anomaly detection (M14)
- `docs/planning/archive/milestone-13-aggregation.md` — Aggregation pipeline (M13)
- `docs/planning/archive/milestone-10-provinces.md` — Alberta scraper & multi-province support (M10, superseded by M16)
- `docs/planning/archive/task-er-watch-features.md` — ER Watch feature execution checklist (completed)
- `docs/planning/archive/methods-ux-implementation.md` — Methodology timeline, CSV export, deep-linking (P1)
- `docs/planning/archive/ci-hardening-implementation.md` — CI hardening & quality gates (P1)
- `docs/planning/archive/test-quality-implementation.md` — React act warning elimination (P2)
- `docs/planning/archive/docs-integrity-implementation.md` — Roadmap consistency checks (P2)
- `docs/planning/archive/about-section-verification.md` — About section implementation verification (M9)

---

## Risk Register

### Active Risks

**Mapbox Cost** — Free tier allows 50k map loads/month. Monitoring; unlikely concern for portfolio project.

**Silent Scraper Failure** — Heartbeat monitor + Dead Man's Switch alerts implemented (M12). Frontend displays "Last Audit" indicator.

**Data Misinterpretation** — Methodology divergence warnings implemented (M3). /methods page shows comparability matrix.

### Resolved Risks

- Geocoding accuracy (resolved: Nominatim + city centroids)
- JavaScript rendering (resolved: Playwright for Ontario)
- Hospital verification (resolved: verification gate in place)

---

## Architecture

### Database Schema (9 tables)

| Table | Purpose |
|-------|---------|
| `sources` | Provincial data source metadata with telehealth routing |
| `hospitals` | Facility metadata with verification workflow |
| `measurements` | Audit log of scraped wait times with ontology tags |
| `scraper_status` | Heartbeat monitoring |
| `measurement_aggregates` | Permanent statistical summaries (M13) |
| `data_quality_snapshots` | Daily scraper reliability metrics (M14) |
| `methodology_change_events` | Detected methodology shifts (M14) |
| `regions` | Province region metadata for analytics segmentation (M15) |
| `hospital_regions` | Hospital-to-region mappings for regional benchmarking (M15) |

### Key ADRs

| ADR | Decision |
|-----|----------|
| [0002](../adr/0002-metric-ontology.md) | Strict metric ontology for comparability |
| [0003](../adr/0003-manual-geocoding-overrides.md) | Manual geocoding overrides |
| [0004](../adr/0004-landing-page-ux-optimization.md) | Landing page UX optimization |
| [0005](../adr/0005-access-burden-estimator.md) | Access Burden Estimator design |
| [0006](../adr/0006-dead-mans-switch-monitoring.md) | Dead Man's Switch monitoring |
| [0007](../adr/0007-bc-scraper-implementation.md) | BC scraper implementation |
| [0008](../adr/0008-aggregation-pipeline.md) | Two-tier aggregation pipeline |
| [0009](../adr/0009-data-quality-anomaly-detection.md) | Data quality & anomaly detection |
| [0010](../adr/0010-region-mapping-coverage-heuristics.md) | Region mapping coverage heuristics |
| [0011](../adr/0011-equity-layer-scaffold.md) | Equity layer scaffold-first delivery |
| [0012](../adr/0012-occupancy-availability-contract.md) | Occupancy availability contract |
| [0013](../adr/0013-testimonial-governance-guardrails.md) | Testimonial governance guardrails |
| [0014](../adr/0014-unified-scraper-runtime-pipeline.md) | Unified scraper runtime pipeline |

---

## Dependencies & Integrations

| Service | Purpose | Tier |
|---------|---------|------|
| Neon PostgreSQL | Database hosting | Free (512 MB) |
| Mapbox | Map tiles | Free (50k loads/month) |
| Nominatim (OSM) | Geocoding | Free (1 req/sec) |
| Netlify | Frontend hosting (release-gated; intentionally offline) | Free (300 credits/month) |
| GitHub Actions | CI/CD + scrapers | Free (2000 min/month) |

---

## Complete Item Tracking (All 50 Improvements)

**Legend:** S = Small (1-3h), M = Medium (1-2d), L = Large (1-4w)

### Governance & Legal (7 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 1 | Add SECURITY.md with responsible disclosure policy | S | ⏸️ On hold - Claude content filtering issue |
| 2 | Add LICENSE file (MIT/Apache-2.0) | S | ✅ Complete |
| 3 | Add CODE_OF_CONDUCT.md (Contributor Covenant) | S | ⏸️ On hold - potential content filtering issue |
| 4 | Add CHANGELOG.md with semantic versioning | M | ✅ Complete |
| 8 | Add Privacy Policy page (/privacy) | S | ✅ Complete |
| 26 | Add Terms of Use page (/terms) | S | ✅ Complete |
| 30 | Add git commit hooks (commitlint) | S | ✅ Complete |

### Documentation & Communication (11 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 10 | Add OpenAPI/Swagger documentation | M | ⬜ Not Started |
| 18 | Add README badges (CI, coverage, license) | S | ⬜ Not Started |
| 20 | Add database migration documentation | S | ⬜ Not Started |
| 23 | Add architecture diagram (Mermaid) | S | ⬜ Not Started |
| 24 | Add data flow documentation per scraper | M | ⬜ Not Started |
| 36 | Add methodology comparison table as static asset | S | ⬜ Not Started |
| 40 | Add contributor onboarding guide | M | ⬜ Not Started |
| 46 | Add GitHub issue templates | S | ✅ Complete |
| 47 | Add GitHub Project board | S | ⬜ Not Started |
| 48 | Add mkdocs GitHub Pages deployment | M | ⬜ Not Started |
| 50 | Add data dictionary with ER diagram | M | ⬜ Not Started |

### Security & Privacy (5 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 11 | Add .pre-commit-config.yaml | S | ✅ Complete |
| 12 | Add Dependabot/Renovate config | S | ✅ Complete |
| 16 | Add Content Security Policy headers | S | ✅ Complete |
| 28 | Add CORS configuration | S | ✅ Complete |
| 49 | Add API response time tracking | S | ⬜ Not Started |

### Frontend Quality (9 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 5 | Add error boundaries (error.tsx, not-found.tsx, global-error.tsx) | S | ✅ Complete |
| 6 | Add accessibility testing (axe-core) | M | ⬜ Not Started |
| 7 | Add French language support (i18n) | L | ⬜ Not Started |
| 15 | Add robots.txt and dynamic sitemap | S | ✅ Complete |
| 19 | Add loading states for all pages | S | ✅ Complete |
| 33 | Add visual regression testing | M | ⬜ Not Started |
| 34 | Add TypeScript strict mode audit | S | ⬜ Not Started |
| 44 | Add mobile-responsive testing | M | ⬜ Not Started |
| 25 | Add structured logging to frontend API routes | S | ⬜ Not Started |

### Backend Quality & Testing (10 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 9 | Add API rate limiting | M | ⬜ Not Started |
| 13 | Increase backend test coverage to 85%+ | M | ⬜ Not Started |
| 21 | Add API input validation (Zod) on all routes | M | ⬜ Not Started |
| 22 | Add comprehensive API integration tests | M | ⬜ Not Started |
| 29 | Add database health check enhancement | S | ⬜ Not Started |
| 32 | Add property-based testing (Hypothesis) | M | ⬜ Not Started |
| 35 | Add backend mypy strict mode | M | ⬜ Not Started |
| 38 | Add database index optimization | S | ⬜ Not Started |
| 39 | Add end-to-end data pipeline test | M | ⬜ Not Started |
| 43 | Add data quality drift monitoring | M | ⬜ Not Started |

### CI/CD & Automation (5 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 14 | Add Lighthouse CI to GitHub Actions | M | ⬜ Not Started |
| 17 | Add GitHub Releases with tagged versions | M | ⬜ Not Started |
| 27 | Expand automated screenshot generation | M | ⬜ Not Started |
| 31 | Add data freshness badge (dynamic) | M | ⬜ Not Started |
| 37 | Add uptime/status history page | M | ⬜ Not Started |

### Research & Citations (3 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 41 | Add CITATION.cff file | S | ✅ Complete |
| 42 | Add Zenodo integration for DOI | S | ⬜ Not Started |
| 45 | Populate stakeholder interview examples | S | ⬜ Not Started |

---

**Total Progress: 14/50 completed (2 on hold)** | **Estimated Total Effort:** ~150-200 hours (3-4 weeks full-time equivalent)

**Recommended Execution Order (Week-by-Week):**

**Week 1 (Quick Wins - 20h):**
Items #2, #3, #1, #41, #42, #18, #23, #11, #12, #30 → LICENSE, CODE_OF_CONDUCT, SECURITY.md, CITATION.cff, Zenodo DOI, badges, architecture diagram, pre-commit hooks, Dependabot, commitlint

**Week 2 (Frontend & Docs - 20h):**
Items #5, #8, #26, #15, #19, #16, #28, #4, #20, #46, #47 → Error boundaries, Privacy/Terms pages, robots/sitemap, loading states, CSP, CORS, CHANGELOG, migration docs, issue templates, project board

**Week 3 (Quality & Testing - 25h):**
Items #6, #13, #14, #21, #22, #29, #38, #39, #44, #34, #35 → Accessibility testing, backend coverage, Lighthouse CI, Zod validation, API integration tests, health check, DB indexes, E2E pipeline, mobile testing, TS/mypy strict

**Week 4 (Documentation & Advanced - 25h):**
Items #10, #24, #36, #40, #48, #50, #25, #9, #27, #31, #37, #43, #45 → OpenAPI docs, scraper docs, methodology table, onboarding, mkdocs site, data dictionary, structured logging, rate limiting, screenshots, freshness badge, status page, drift monitoring, interview examples

**Week 5-8 (Strategic - variable):**
Item #7 (French i18n) → Full bilingual support with next-intl, methodology warnings, emergency disclaimers, UI translations

---

**Next Action:** Review and approve this roadmap, then begin execution with Week 1 quick wins for immediate admissions credibility boost.
