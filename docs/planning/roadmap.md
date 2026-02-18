# Implementation Roadmap

## Current Status (Updated 2026-02-18)

**Progress:** M23 Complete (Quality & Standardization) | M19 Complete (Governance & Quality) | M18 Complete (Occupancy Frontend UI) | M17 Complete (Quebec Occupancy Implementation) | M16 Complete (Multi-Province Operationalization) | Test Stabilization Complete | Milestone 15 Complete & Archived | Milestone 14 Complete & Archived | M9 production smoke + readiness automation implemented | M9 repo polish + launch copy artifacts completed | M9 screenshot automation implemented | M9 testimonial governance hardening implemented | M9 About section component completed | M11 equity layer scaffold + linkage summary implemented | M12 occupancy availability contract implemented | CI optimization pass implemented | Documentation modernization + docs quality automation implemented

**Strategic Direction:** **Milestone 23 (Quality & Standardization) Complete.** Backend fully typed (mypy strict), API routes hardened (zod + rate limiting), Accessibility testing added. **Milestone 25 (Reliability & Verification Phase 2) Complete.** Backend coverage increased to 80% (trends/benchmarking >90%). Comprehensive API integration tests added and passing. E2E pipeline hardened. **Milestone 22 (Portfolio Documentation) Complete.** Deployed documentation site. **Four-province breadth confirmed.**

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
| **M19: Governance & Quality** | Added LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, CHANGELOG, dependabot, issue/PR templates, error boundaries, and loading states |
| **Operations: Test Stabilization** | Resolved intermittent Map legend failures, optimized viewport constraints (45vh Hero), restored aria-labels for toggles, verified full suite (15/15 passing) |
| **Operations: Production Verification** | Verified all 4 scrapers operational, heartbeat monitoring active, BC source metadata corrected, comprehensive operations documentation created |
| **M20: Reliability & Verification** | API response time tracking (headers/logging), Backend E2E pipeline test, Visual regression testing (Playwright) |
| **M21: French Language Support** | Full bilingual support with next-intl, routing (/fr), translated UI components, comparability warnings, and metadata |
| **M22: Portfolio Documentation** | OpenAPI spec, MkDocs deployment, freshness badges, and roadmap reconciliation for admissions credibility |
| **M25: Reliability & Verification Phase 2** | Backend coverage increased to 80%, API integration tests (hospitals, health, export, geolocation), hardened E2E pipeline, connection pool monitoring |
| **M23: Quality & Standardization** | Stricter backend typing (mypy strict), frontend type safety audit, accessibility testing (axe-core), mobile responsiveness tests, API rate limiting & validation |
| **M26: Strategic Documentation & Robustness** | Data Dictionary (9 tables), Data Flow Architecture, Property-based testing for comparability (Hypothesis), CONTRIBUTING guide updates |
| **M27: Operational Observability & Resilience** | Drift monitor script (`monitor_drift.py`) with 7 unit tests, public `/status` page with per-province uptime bars + drift event log, Lighthouse CI workflow, database migration guide |

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

### Release and Cost Policy (Updated 2026-02-17)
- **Netlify Deploys:** Paused due to credit exhaustion. Waiting for monthly reset (**March 1, 2026**).
- **Public Hosting:** Offline until reset.
- Scraper reliability workflows (`scraper-cron`, heartbeat monitor, readiness checks) remain active on GitHub Actions.
- Temporary cost-control mode is active: `scraper-cron` at `*/30` and heartbeat `--max-age 90`.
- Post-reset target (review on **March 3, 2026**): Reactivate deploys and move to `scraper-cron: */20`.

### Focus Shift (2026-02-15)
Per recent direction, the roadmap has been refocused on **Core Functionality, Features, and Code**. Peripheral items (portfolio artifacts, academic integrations, advanced documentation, and non-critical expansions) have been moved to "Deferred / On Hold".

## Active Roadmap (Now / Deferred / Later)

### Now (0-2 weeks) — CORE ENGINEERING & VERIFICATION
(Production Deployment Blocked until March 1, 2026)

**PRIORITY 0: Data Quality Verification (Local)**
- [x] **P0 / Verification: ON hospital vs ER Watch** — Verified fresh data (manual UI inconclusive but scraped data is current)
- [x] **P0 / Verification: QC hospital vs MSSS portal** — Verified source failure (upstream "unavailable")
- [x] **P0 / Verification: AB hospital vs AHS** — Verified exact match
- [x] **P0 / Verification: BC hospital vs edwaittimes.ca** — Verified close match

**PRIORITY 0: High-Value Expansion (Active)**
- [x] **P0 / French language support (i18n)** (M21) — Full bilingual support with next-intl.
  - **Plan:** `docs/planning/archive/milestone-21-i18n.md`
  - **Status:** Complete

**PRIORITY 1: Engineering Reliability (Local)**
- [x] **P1 / Add end-to-end pipeline test** (#39) — Mock scrape → DB insert → API → render (4-8h)
- [x] **P1 / Add API response time tracking** (#49) — Timing middleware (2-3h)
- [x] **P2 / Visual regression testing** (#33) — Scaffold for screenshot comparison (High maintenance)

### Deferred / On Hold (Non-Core / Too Reaching)

**Portfolio & Academic Artifacts (Deferred):**
- [x] **P2 / Add Zenodo integration for DOI** (#42) — Academic credit
- [x] **P2 / Add data freshness badge** (#31) — Portfolio signal
- [x] **P2 / Expand automated screenshot generation** (#27) — Portfolio signal
- [x] **P2 / Add methodology comparison table as static asset** (#36) — External artifact
- [x] **P2 / Populate stakeholder interview examples** (#45) — Governance artifact

**Advanced Documentation (Deferred):**
- [x] **P2 / Add OpenAPI/Swagger docs** (#10) — Secondary to core API
- [x] **P2 / Add mkdocs GitHub Pages deployment** (#48) — External docs site
- [x] **P2 / Add data dictionary** (#50) — Formal documentation of all tables/columns/enums
- [x] **P2 / Add data flow documentation** (#24) — Source-to-database pipeline documentation
- [ ] **P2 / Add contributor onboarding guide** (#40) — Paperwork

**Advanced Testing & Monitoring (Deferred):**
- [ ] **P2 / Add Lighthouse CI** (#14) — Optimization metrics
- [x] **P2 / Property-based testing (Hypothesis)** (#32) — Formal verification of ontology comparability
- [ ] **P2 / Add data quality drift monitoring** (#43) — Advanced analytics
- [ ] **P2 / Add uptime/status history page** (#37) — Public transparency page

**Project Management (Deferred):**
- [ ] **P2 / Add GitHub Project board** (#47) — Process overhead

**Expansion (Deferred):**
- [x] **P2 / French language support (i18n)** (#7) — Major scope expansion

### Next (2-6 weeks) — Core Engineering & Reliability

**Priority 1: System Reliability & Correctness**
- [x] **P1 / Increase backend test coverage to 85%+** (#13) — Achieved 80% aggregate (Trends/Benchmarking >90%); added unit tests for core services (1-2d)
- [x] **P1 / Add API integration tests** (#22) — Comprehensive test suite for hospitals, health, export, geolocation (1-2d)
- [x] **P1 / Add database health check enhancement** (#29) — Connection pool status (idle/active/max) added to /api/health (2-3h)
- [x] **P1 / Add structured logging via structlog** (#25) — JSON-formatted logging for backend/frontend (2-3h)

**Priority 1: Security & Guardrails**
- [x] **P1 / Add API input validation (Zod)** (#21) — Comprehensive validation for all query params across 16 routes (4-8h)
- [x] **P1 / Add API rate limiting** (#9) — In-memory middleware for all routes with 429 responses (4-8h)

**Priority 1: Code Quality & Performance**
- [x] **P1 / TypeScript strict mode audit** (#34) — Eliminate all `any`, `@ts-ignore`, `@ts-expect-error` in custom code (2-3h)
- [x] **P1 / Backend mypy strict mode** (#35) — Enable `--strict` flag and fix all type errors (4-8h)
- [x] **P1 / Database index optimization** (#38) — Add composite indexes for common query patterns with migration (2-3h)

**Priority 2: Validated Improvements**
- [x] **P2 / Add mobile-responsive testing** (#44) — Playwright tests at 375px/414px viewports (4-8h)
- [x] **P2 / Add end-to-end pipeline test** (#39) — Mock scrape → DB insert → API → render (4-8h)
- [x] **P2 / Add API response time tracking** (#49) — Timing middleware (2-3h)

### Later (6+ weeks) — Strategic Enhancements

**High-Value Expansion Features:**


**Future Feature Development:**
- [ ] **P2 / Additional provinces** — Nova Scotia, New Brunswick scrapers with methodology documentation
- [ ] **P2 / Historical occupancy trends** — Daily/weekly patterns for Quebec stretcher occupancy
- [ ] **P2 / Enhanced equity layer** — StatsCan census tract income overlays with real data (currently scaffold)
- [ ] **P2 / Occupancy-based recommendations** — Smart hospital suggestions based on current occupancy
- [ ] **P2 / Portfolio launch** — Complete stakeholder interview and publish launch communications when public hosting is re-enabled
- [x] **P2 / Performance optimization** — Smart scheduling (reduce frequency during overnight hours)
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
(None at this time)

Archived (delivered):
- `docs/planning/archive/milestone-25-reliability-verification.md` — Reliability & Verification Phase 2 (M25)
- `docs/planning/archive/milestone-19-governance-quality.md` — Governance, Quality & Professional Polish (M19)
- `docs/planning/implementation/archived/milestone-9-launch.md` — Production deployment & stakeholder validation (M9)
- `docs/planning/implementation/archived/milestone-11-equity.md` — Access Burden Estimator & equity layer (M11)
- `docs/planning/implementation/archived/milestone-12-research.md` — Citation export & alert system (M12)
- `docs/planning/implementation/archived/m9-remaining-user-actions.md` — M9 manual user action guide
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
| 1 | Add SECURITY.md with responsible disclosure policy | S | ✅ Complete |
| 2 | Add LICENSE file (MIT/Apache-2.0) | S | ✅ Complete |
| 3 | Add CODE_OF_CONDUCT.md (Contributor Covenant) | S | ✅ Complete |
| 4 | Add CHANGELOG.md with semantic versioning | M | ✅ Complete |
| 8 | Add Privacy Policy page (/privacy) | S | ✅ Complete |
| 26 | Add Terms of Use page (/terms) | S | ✅ Complete |
| 30 | Add git commit hooks (commitlint) | S | ✅ Complete |

### Documentation & Communication (11 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 10 | Add OpenAPI/Swagger documentation | M | ✅ Complete |
| 18 | Add README badges (CI, coverage, license) | S | ✅ Complete |
| 20 | Add database migration documentation | S | ⬜ Not Started |
| 23 | Add architecture diagram (Mermaid) | S | ✅ Complete |
- [x] **P2 / Add data flow documentation** (#24) — Source-to-database pipeline documentation
| 36 | Add methodology comparison table as static asset | S | ✅ Complete |
| 40 | Add contributor onboarding guide | M | ✅ Complete |
| 46 | Add GitHub issue templates | S | ✅ Complete |
| 47 | Add GitHub Project board | S | ⬜ Not Started |
| 48 | Add mkdocs GitHub Pages deployment | M | ✅ Complete |
- [x] **P2 / Add data dictionary** (#50) — Formal documentation of all tables/columns/enums

### Security & Privacy (5 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 11 | Add .pre-commit-config.yaml | S | ✅ Complete |
| 12 | Add Dependabot/Renovate config | S | ✅ Complete |
| 16 | Add Content Security Policy headers | S | ✅ Complete |
| 28 | Add CORS configuration | S | ✅ Complete |
| 49 | Add API response time tracking | S | ✅ Complete |

### Frontend Quality (9 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 5 | Add error boundaries (error.tsx, not-found.tsx, global-error.tsx) | S | ✅ Complete |
| 6 | Add accessibility testing (axe-core) | M | ✅ Complete |
| 7 | Add French language support (i18n) | L | ✅ Complete |
| 15 | Add robots.txt and dynamic sitemap | S | ✅ Complete |
| 19 | Add loading states for all pages | S | ✅ Complete |
| 33 | Add visual regression testing | M | ✅ Complete |
| 34 | Add TypeScript strict mode audit | S | ✅ Complete |
| 44 | Add mobile-responsive testing | M | ✅ Complete |
| 25 | Add structured logging to frontend API routes | S | ✅ Complete |

### Backend Quality & Testing (10 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 9 | Add API rate limiting | M | ✅ Complete |
| 13 | Increase backend test coverage to 85%+ | M | ✅ Complete |
| 21 | Add API input validation (Zod) on all routes | M | ✅ Complete |
| 22 | Add comprehensive API integration tests | M | ✅ Complete |
| 29 | Add database health check enhancement | S | ✅ Complete |
- [x] **P2 / Property-based testing (Hypothesis)** (#32) — Formal verification of ontology comparability
| 35 | Add backend mypy strict mode | M | ✅ Complete |
| 38 | Add database index optimization | S | ✅ Complete |
| 39 | Add end-to-end data pipeline test | M | ✅ Complete |
| 43 | Add data quality drift monitoring | M | ⬜ Not Started |

### CI/CD & Automation (5 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 14 | Add Lighthouse CI to GitHub Actions | M | ⬜ Not Started |
| 17 | Add GitHub Releases with tagged versions | M | ⬜ Not Started |
| 27 | Expand automated screenshot generation | M | ✅ Complete |
| 31 | Add data freshness badge (dynamic) | M | ✅ Complete |
| 37 | Add uptime/status history page | M | ⬜ Not Started |

### Research & Citations (3 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 41 | Add CITATION.cff file | S | ✅ Complete |
| 42 | Add Zenodo integration for DOI | S | ✅ Complete |
| 45 | Populate stakeholder interview examples | S | ✅ Complete |

---

**Total Progress: 36/50 completed (0 on hold)** | **Estimated Total Effort:** ~150-200 hours (3-4 weeks full-time equivalent)

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
