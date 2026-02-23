# Implementation Roadmap

## Current Status (Updated 2026-02-23)

**Progress:** M33 Complete (Historical Occupancy Trends) | M32 Complete (Deployment Readiness & CSV Divergence) | M31 Complete (Divergence Briefs & Quality Drift UI) | M30 Complete (Scraper Visibility & Reliability Hardening) | M29 Complete (Equity Academic Rigor Hardening) | M23 Complete (Quality & Standardization) | M19 Complete (Governance & Quality) | M18 Complete (Occupancy Frontend UI) | M17 Complete (Quebec Occupancy Implementation) | M16 Complete (Multi-Province Operationalization) | CI/Tooling Maintenance Complete (2026-02-23) | Test Stabilization Complete | Milestone 15 Complete & Archived | Milestone 14 Complete & Archived

**Strategic Direction:** **CI tooling maintenance complete (2026-02-23).** Resolved all mypy and pytest CI failures from the scraper-ci workflow. Upgraded ruff (v0.14.14), mypy (v1.19.0), react-map-gl (v8), playwright (1.58.2), and date-fns (v4). All 359 frontend and 454+ backend tests passing. Pre-commit hooks fully aligned across hook env, venv, and CI.

**Deployment Note (2026-02-23):** Frontend public hosting is currently unavailable because the Netlify project is paused (cost control / credit exhaustion). The `wait-time.ca` domain cutover is staged in-repo but should be treated as **on hold** until the project is unpaused (target: **March 9, 2026**).

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
| **M28: Ontario Real-Data Equity Layer** | Replaced scaffold linkage with real StatsCan CT overlays for ON; added acquisition provenance, processing manifest, ON-only rollout contract, and map/API integration |
| **M29: Equity Academic Rigor Hardening (ON)** | ON-scoped quintiles, suppression provenance, sensitivity + uncertainty outputs, non-causal/temporal messaging, reproducibility hardening (`equity` extras/docs), optimized layer output + API loader preference |
| **M30: Scraper Visibility & Reliability Hardening** | Added structured failure taxonomy + heartbeat metadata (`last_success`, `last_error`, `consecutive_failures`, run duration), standardized retry/backoff for ON/AB/BC/QC fetch paths, enhanced `/api/health` + `check_heartbeat --verbose`, and updated workflow/runbook operations |
| **M31: Divergence Briefs & Quality Drift UI** | Scheduled daily data quality snapshots (cron + CLI), added methodology divergence context to analytics trends API, added 7-Day Quality Drift UI panel to `/data-quality` page |
| **M32: Deployment Readiness & CSV Divergence** | Injected methodology divergence warnings into raw and aggregated CSV exports, fixed `netlify-ignore.sh` to enforce `[release]` gate logic on `main`, and implemented `release.yml` GitHub Actions workflow for automated version releases |
| **M33: Historical Occupancy Trends** | Extended aggregation pipeline to include `STRETCHER_OCCUPANCY`, added `metric_family` filtering to analytics trends API and `SystemTrendChart`, collapsible occupancy trend panel on analytics page, DB migration `015`, ADR-0019 |

---

## Next Steps

CI tooling maintenance complete (2026-02-23). Netlify unpause target is **March 9, 2026** — plan to reactivate production hosting and run production smoke verification at that time. Beyond that: M34 (multi-province equity layer) when StatsCan CT data is available; M35 (Nova Scotia scraper) when bandwidth allows.

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

### Release and Cost Policy (Updated 2026-02-19)
- **Netlify Deploys:** Paused due to credit exhaustion. Public hosting remains unavailable until the project is unpaused (target: **March 9, 2026**).
- **Public Hosting:** Offline until unpause.
- Scraper reliability workflows (`scraper-cron`, heartbeat monitor, readiness checks) remain active on GitHub Actions.
- Temporary cost-control mode is active: `scraper-cron` at `*/30` and heartbeat `--max-age 90`.
- Post-unpause target (review on **March 9, 2026**): Reactivate deploys and move to `scraper-cron: */20`.

### Focus Shift (2026-02-15)
Per recent direction, the roadmap has been refocused on **Core Functionality, Features, and Code**. Peripheral items (portfolio artifacts, academic integrations, advanced documentation, and non-critical expansions) have been moved to "Deferred / On Hold".

## Active Roadmap (Now / Deferred / Later)

### Now (0-2 weeks) — CORE ENGINEERING & VERIFICATION
(Production Deployment Blocked until March 9, 2026)

**PRIORITY 0: Active Reliability Fixes (Local)**
- [x] **P0 / Ops: Quebec parser zero-value guard** — MSSS occupancy occasionally returns `0`, which currently fails `Measurement.value > 0` validation and classifies as `parser_breakage/parse`; update parser handling to treat zero-value occupancy as explicit non-reporting/suppressed signal rather than hard failure, with regression tests.

**PRIORITY 1: Engineering Reliability (Local)**
- [x] **P1 / Performance: Cache & polling audit** — Verify cache headers/TTLs for shared read-heavy routes; enforce `no-store` for user-specific and export endpoints; keep SystemStatus polling at 5m and tab-visible only (4-8h)
- [x] **P1 / Ops: CI quota conservation (temporary)** — Minimize free-tier GitHub Actions burn until reset (favor local preflight + targeted workflow triggers, defer non-critical heavy jobs such as Playwright to essential runs only).
- [x] **P1 / Ops: CI/tooling maintenance (2026-02-23)** — Resolved all mypy/pytest CI failures; upgraded ruff, mypy, react-map-gl v8, playwright, date-fns; aligned pre-commit hook env with venv and CI; pruned stale remote-tracking branch.

### Deferred / On Hold (Non-Core / Too Reaching)

**Deployment / Domain Cutover (On Hold):**
- [ ] **P1 / Ops: Unpause Netlify + verify `wait-time.ca` cutover** — Confirm TLS/cert, redirects, `NEXT_PUBLIC_BASE_URL`, and re-enable `production-smoke` (target **March 9, 2026**)
- [x] **P1 / Ops: Harden Netlify release gate** — Assert `netlify-ignore.sh` blocks non-release commits and add a minimal CI check to prevent accidental credit burn (M32 Complete)

**Advanced Documentation (Deferred):**
- [ ] **P2 / Add contributor onboarding guide** (#40) — Paperwork

**Advanced Testing & Monitoring (Deferred):**
- [ ] **P2 / Add Lighthouse CI** (#14) — Optimization metrics
- [ ] **P2 / Add uptime/status history page** (#37) — Public transparency page

**Project Management (Deferred):**
- [ ] **P2 / Add GitHub Project board** (#47) — Process overhead

### Next (2-6 weeks) — Core Engineering & Reliability

**Priority 1: System Reliability & Correctness**
- [x] **P1 / Divergence Briefs in analytics + export** — When ontology mismatches, generate a structured “divergence brief” (why non-comparable) and surface it in UI + export metadata (M32 Complete - CSV and analytics coverage complete)

### Later (6+ weeks) — Strategic Enhancements

**Future Feature Development:**
- [x] **P2 / Historical occupancy trends** — Daily/weekly patterns for Quebec stretcher occupancy (M33 Complete)
- [ ] **P2 / Enhanced equity layer (multi-province rollout)** — Apply Ontario template to QC/AB/BC (M34 — blocked on StatsCan CT data manual download)
- [ ] **P2 / Additional provinces** — Nova Scotia scraper with methodology documentation (M35 — pre-research done)
- [ ] **P2 / Occupancy-based recommendations** — Smart hospital suggestions based on current occupancy
- [ ] **P2 / Portfolio launch** — Complete stakeholder interview and publish launch communications when public hosting is re-enabled
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
- none currently open.

Archived (delivered):
- `docs/planning/archive/maintenance-2026-02-23.md` — CI/tooling maintenance (2026-02-23)
- `docs/planning/archive/maintenance-2026-02-19.md` — Domain rebrand staging, M30 closeout (2026-02-19)
- `docs/planning/archive/milestone-32-deployment-readiness.md` — Deployment Readiness & CSV Divergence (M32)
- `docs/planning/archive/milestone-33-historical-occupancy-trends.md` — M33-M35 planning doc (M33 delivered)
- `docs/planning/archive/milestone-31-divergence-drift.md` — Divergence Briefs & Quality Drift UI (M31)
- `docs/planning/archive/milestone-28-equity-real-data-ontario.md` — Ontario real-data equity layer rollout (M28)
- `docs/planning/archive/milestone-29-equity-academic-rigor-hardening.md` — Ontario equity methodology hardening and academic defensibility improvements (M29)
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
| [0015](../adr/0015-real-equity-layer-ontario.md) | Ontario real-data equity layer |
| [0016](../adr/0016-equity-academic-rigor-hardening-ontario.md) | Ontario equity academic rigor hardening |
| [0017](../adr/0017-domain-rebrand-wait-time-ca.md) | Domain rebrand to wait-time.ca |
| [0018](../adr/0018-scraper-observability-and-reliability-hardening.md) | Scraper observability & reliability hardening |
| [0019](../adr/0019-occupancy-trend-aggregation.md) | Include STRETCHER_OCCUPANCY in aggregation pipeline |

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
| 20 | Add database migration documentation | S | ✅ Complete |
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
| 42 | Add data quality drift monitoring | M | ✅ Complete |

### CI/CD & Automation (5 items)
| # | Item | Effort | Status |
|---|------|--------|--------|
| 14 | Add Lighthouse CI to GitHub Actions | M | ✅ Complete |
| 17 | Add GitHub Releases with tagged versions | M | ✅ Complete |
| 27 | Expand automated screenshot generation | M | ✅ Complete |
| 31 | Add data freshness badge (dynamic) | M | ✅ Complete |
| 37 | Add uptime/status history page | M | ✅ Complete |

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
