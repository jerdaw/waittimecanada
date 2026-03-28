# Implementation Roadmap

## Current Status (Updated 2026-03-27)

**Progress:** Public Health Hub Batch A Live (2026-03-27) | Production Domain Launch Complete (2026-03-12) | M33 Complete (Historical Occupancy Trends) | M32 Complete (Deployment Readiness & CSV Divergence) | M31 Complete (Divergence Briefs & Quality Drift UI) | M30 Complete (Scraper Visibility & Reliability Hardening) | M29 Complete (Equity Academic Rigor Hardening) | M23 Complete (Quality & Standardization) | M19 Complete (Governance & Quality) | M18 Complete (Occupancy Frontend UI) | M17 Complete (Quebec Occupancy Implementation) | M16 Complete (Multi-Province Operationalization) | Ontario Timeout Hardening Verified In Production (2026-03-21) | Bounded Cleanup Runtime Verified In Production (2026-03-23) | Frontend Neon Transfer Guardrails Deployed In Production (2026-03-26) | Codecov Coverage Rollout Complete (2026-03-16) | CI/Tooling Maintenance Complete (2026-02-23) | Test Stabilization Complete | Milestone 15 Complete & Archived | Milestone 14 Complete & Archived

**Strategic Direction:** **Admissions strengthening phase remains active (2026-03-27), with the frontend live on the shared VPS and the backend scheduler path still live on GitHub Actions.** Engineering foundation is mature (33 milestones, 4 provinces, public `/resources` module live). Focus remains on real-world engagement, external validation, public-facing artifacts, and keeping the VPS frontend path operationally cheap while backend cutover stays deferred until the Ontario source is reachable from the chosen runtime. The GitHub Actions Ontario fetch path has scraper-specific read-timeout hardening, the manual cleanup workflow enforces 30-day retention without turning maintenance into a 5-minute aggregate backfill, the live VPS frontend serves repeat anonymous reads from a short-lived in-process cache, and the public-health-hub Batch A module now has production smoke/readiness coverage plus source-specific ingest monitoring and alerting. See [`admissions-strengthening-plan.md`](implementation/admissions-strengthening-plan.md), `docs/operations/direct-vps-frontend.md`, and `docs/operations/direct-vps-backend.md`.

**Deployment Note (2026-03-13):** Frontend hosting is now live on the shared VPS, `https://wait-time.ca` presents a valid Let's Encrypt certificate from Caddy, `https://www.wait-time.ca` redirects to the canonical host, and production smoke passes against the canonical domain.

**Migration Note (2026-03-13):** The backend scheduler/runtime cutover was attempted on the shared VPS, but the Ontario source timed out repeatedly from this host:

- frontend via host Caddy + a loopback-bound Docker container is now live
- backend scrapers/heartbeat/quality jobs remain on GitHub Actions
- Neon remains the managed production database in this wave

Netlify should now be treated as rollback-only for the frontend, and GitHub Actions remains the live backend scheduler path until an Ontario-compatible worker runtime is proven.

---

## Completed Milestones

| Milestone | Summary |
|-----------|---------|
| **M1: Database Foundation** | Neon PostgreSQL schema, ontology enums, Quebec scraper, heartbeat monitoring |
| **M2: Ontario End-to-End** | Ontario HTTP/HTML scraper, Nominatim geocoding, Mapbox frontend, 160 hospitals |
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
| **M26: Strategic Documentation & Robustness** | Data Dictionary (10 tables), Data Flow Architecture, Property-based testing for comparability (Hypothesis), CONTRIBUTING guide updates |
| **M27: Operational Observability & Resilience** | Drift monitor script (`monitor_drift.py`) with 7 unit tests, public `/status` page with per-province uptime bars + drift event log, Lighthouse CI workflow, database migration guide |
| **M28: Ontario Real-Data Equity Layer** | Replaced scaffold linkage with real StatsCan CT overlays for ON; added acquisition provenance, processing manifest, ON-only rollout contract, and map/API integration |
| **M29: Equity Academic Rigor Hardening (ON)** | ON-scoped quintiles, suppression provenance, sensitivity + uncertainty outputs, non-causal/temporal messaging, reproducibility hardening (`equity` extras/docs), optimized layer output + API loader preference |
| **M30: Scraper Visibility & Reliability Hardening** | Added structured failure taxonomy + heartbeat metadata (`last_success`, `last_error`, `consecutive_failures`, run duration), standardized retry/backoff for ON/AB/BC/QC fetch paths, enhanced `/api/health` + `check_heartbeat --verbose`, and updated workflow/runbook operations |
| **M31: Divergence Briefs & Quality Drift UI** | Scheduled daily data quality snapshots (cron + CLI), added methodology divergence context to analytics trends API, added 7-Day Quality Drift UI panel to `/data-quality` page |
| **M32: Deployment Readiness & CSV Divergence** | Injected methodology divergence warnings into raw and aggregated CSV exports, fixed `netlify-ignore.sh` to enforce `[release]` gate logic on `main`, and implemented `release.yml` GitHub Actions workflow for automated version releases |
| **M33: Historical Occupancy Trends** | Extended aggregation pipeline to include `STRETCHER_OCCUPANCY`, added `metric_family` filtering to analytics trends API and `SystemTrendChart`, collapsible occupancy trend panel on analytics page, DB migration `015`, ADR-0019 |
| **Public Health Hub Batch A** | Delivered `/resources` with Ontario facility search, OSM-backed AED fallback, Health Canada alerts, AQHI, new public-health tables/migrations, ingest workflows, production smoke coverage, readiness coverage, and source-specific operational monitoring |

---

## Next Steps

**Admissions strengthening plan active (2026-03-26).** Production launch verification is complete. Immediate work now shifts to credibility artifacts and post-launch follow-through: A6/A7 (case study + quantified findings) and B2-B4 (analytics, launch post, walkthrough). A1 (README mission/equity/stewardship section) is now delivered. A3 (Zenodo DOI) and A4 (stakeholder outreach) remain in scope but are held until explicit user go-ahead. See [`admissions-strengthening-plan.md`](implementation/admissions-strengthening-plan.md) for full details.

**Parallel ops track (2026-03-26):** keep the VPS frontend stable, watch Neon transfer after the new read-cache guardrails, and treat backend migration as deferred pending an Ontario reachability investigation for the VPS path.

**Public health hub track (2026-03-28):** Batch A is now live. The deferred Batch B source review is complete, Ontario naloxone now has a formal interim link-out-only decision, and the Toronto-only municipal inspection pilot has been explicitly deferred on product-fit grounds. EMS/system-context remains analytics-only. Immediate follow-on work should stay in selective-expansion mode: keep `/resources` stable, avoid blind Batch B implementation, and only reopen expansion when legal/product gates are clearer or broader Ontario coverage emerges.

Beyond the admissions plan: M34 (multi-province equity layer) when StatsCan CT data is available; M35 (Nova Scotia scraper) when bandwidth allows. Both are Phase D (deferred) in the admissions plan. If Neon transfer remains tight after the March 26 guardrail deploy, the next optimization target is a more compact latest-snapshot path for `GET /api/hospitals`.

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

### Release and Cost Policy (Updated 2026-03-13)
- **Frontend Hosting:** Live on the shared VPS through host Caddy and a loopback Docker container.
- **Public Hosting:** `https://wait-time.ca` is live and has passed HTTPS, redirect, and production smoke verification.
- **Backend Scheduling:** still live on GitHub Actions because the Ontario source timed out from the shared VPS during backend cutover testing.
- Current production cadence is `hourly` on GitHub Actions with heartbeat checks every 30 minutes and a `120` minute stale threshold.
- Alerting is now state-change driven: one incident alert when a source becomes unhealthy, one recovery alert when it clears.
- If backend migration is revisited later, solve Ontario reachability first instead of re-running the same VPS timer cutover sequence blindly.

### Focus Shift (2026-02-25)
Engineering foundation is mature (33 milestones, 777+ tests, 4 provinces). The gap is in **real-world engagement, external validation, and public-facing artifacts**. See the [Admissions Strengthening Plan](implementation/admissions-strengthening-plan.md) for the full phased strategy including analytical rationale (original plan, devil's advocate, steelman, and final synthesis).

## Active Roadmap (Phase-Based)

### Completed Engineering (Reference)

- [x] **P0 / Ops: Quebec parser zero-value guard** — Zero-value occupancy as suppressed signal rather than hard failure
- [x] **P1 / Performance: Frontend read-cache + polling guardrails (2026-03-26)** — Deployed short-lived in-process response caching for read-heavy VPS routes, kept shared cache headers/TTLs, and reduced status polling to a 5-minute visible-tab cadence
- [x] **P1 / Public Health Hub: Batch A delivery (2026-03-27)** — Shipped `/resources`, Batch A APIs, public-health schema/migrations, live source ingest, source freshness/caveat UI, and production deployment on `wait-time.ca`
- [x] **P1 / Public Health Hub: Ops hardening (2026-03-27)** — Added public-health ingest summaries, stateful hard-fail alerting, best-effort AED noise suppression, and production smoke/readiness coverage for `/resources`
- [x] **P2 / D6: Public Health Hub Batch B source review (2026-03-27)** — Revalidated naloxone, EMS/system-context, and inspection datasets; naloxone now has a verified public ArcGIS connector path, EMS remains context-only, and Toronto inspections are strong but fragmented
- [x] **P2 / D8: Ontario naloxone interim posture (2026-03-28)** — Recorded ADR-0024: use an official link-out only, not native ingestion or republication, until reuse rights are clearer
- [x] **P2 / D9: Municipal inspection pilot decision (2026-03-28)** — Deferred a Toronto-only DineSafe/BodySafe pilot; the data is real, but the scope is too fragmented and the product fit is weaker than Ontario-wide or emergency-access-adjacent additions
- [x] **P1 / Ops: CI quota conservation (temporary)** — Minimized free-tier GitHub Actions burn
- [x] **P1 / Ops: Raw retention + alerting stabilization** — Duplicate suppression added, 30-day retention enforcement restored, and heartbeat alerts made state-change driven with a 120-minute threshold
- [x] **P1 / Ops: Bound database cleanup runtime (2026-03-23)** — Production cleanup deleted 207,059 rows older than 30 days, then the workflow/runtime was tightened to skip zero-yield aggregate refresh and finish in 22 seconds instead of 5m48s
- [x] **P1 / Ops: CI/tooling maintenance (2026-02-23)** — Resolved all mypy/pytest CI failures; upgraded ruff, mypy, react-map-gl v8, playwright, date-fns
- [ ] **P1 / Ops: Refresh GitHub Actions security workflow dependencies** — `Scraper CI` is green, but GitHub now warns that parts of the security scan still rely on Node 20-era actions and `github/codeql-action/upload-sarif@v3`; migrate these before the June/December 2026 deprecation deadlines
- [x] **P1 / Ops: Codecov coverage rollout (2026-03-16)** — Added quiet Codecov configuration with split frontend/backend flags, carryforward support, and patch-focused PR status checks
- [x] **P1 / Ops: Ontario timeout hardening (2026-03-21)** — Added Ontario-specific HTTP read-timeout fallback and verified a healthy post-deploy production scrape on GitHub Actions
- [ ] **P1 / Ops: Stabilize Playwright UI regression suite** — Main-branch Playwright currently times out on map/list interactions and footer landmark a11y assertions; tighten selectors/fixtures and keep heavy E2E focused on user-facing diffs
- [ ] **P2 / Ops: Batch frontend dependency refresh** — Closed Dependabot PRs #38, #39, #40, #41, and #42 rather than drip-merging them; revisit frontend package updates in one deliberate lockfile refresh with a coherent lockfile/tooling plan
- [x] **P0 / Ops: Production domain launch verification** — `wait-time.ca` HTTPS valid, `www.wait-time.ca` redirect verified, release deploy published, production smoke passing
- [x] **P1 / Ops: Harden Netlify release gate** — M32 Complete
- [x] **P1 / Divergence Briefs in analytics + export** — M32 Complete
- [x] **P2 / Historical occupancy trends** — M33 Complete

### Active Ops Track: VPS Frontend Live / Backend Follow-Up

- [x] **P1 / Add frontend VPS runtime packaging** — Frontend Dockerfile, standalone Next.js output, `.dockerignore`, and deploy/release helpers
- [x] **P1 / Add backend VPS runtime packaging** — Backend deploy/release helpers, systemd templates, and verification script
- [x] **P1 / Finalize VPS env contracts** — `/etc/projects-merge/env/waittime-frontend.env` and `/etc/projects-merge/env/waittime-backend.env` created on the shared VPS
- [x] **P1 / Host cutover preparation** — Caddy route, release roots, loopback bind target, backend timers, and Playwright runtime deps were staged on the shared VPS
- [ ] **P1 / Backend-compatible cutover verification** — Frontend private/public health and production smoke passed; backend verification exposed Ontario upstream timeouts from this VPS, so backend cutover is deferred until a compatible runtime path is proven

### Phase A: Immediate Credibility Cleanup
[Full details: admissions-strengthening-plan.md](implementation/admissions-strengthening-plan.md)

- [x] **P1 / A1: Mission, equity, and stewardship section in README** — Replace the maintainer blurb with a public-facing mission/equity/stewardship statement aligned to the site's official posture
- [x] **P1 / A2: Limitations section in README** — Specific, technical limitations demonstrating intellectual maturity (delivered in README + application summary)
- [ ] **P1 / A3: Fix placeholder Zenodo DOI** — Repo-side preparation is complete (`CITATION.cff`, `.zenodo.json`, current GitHub release). Remaining work is Zenodo account activation, publish, and then restoring the README badge once the DOI is real. `Hold until explicit user go-ahead.`
- [ ] **P1 / A4: Stakeholder interview outreach** — Send 10–15 outreach messages to ER professionals using existing templates (2–3 h outreach; interviews on their schedule). `Hold until explicit user go-ahead.`
- [ ] **P1 / A5: Private reflection document** — ABS/interview prep; motivation, decisions, surprises, ethical tensions (2 h; not committed to repo)
- [x] **P1 / A6: Ottawa–Gatineau case study** — Added the case study artifact, linked it from README/application summary, and verified the Ottawa/Gatineau pair against live production data on 2026-03-28
- [x] **P1 / A7: Quantified metrics & methodology findings** — Added a dated "By the Numbers" section to README using operational and ontology-level findings only, with no cross-province performance claims

### Phase B: Active Launch Cleanup
[Full details: admissions-strengthening-plan.md](implementation/admissions-strengthening-plan.md)

- [ ] **P1 / B2: Privacy-safe usage analytics** — Add Plausible Analytics; update /privacy page; do not publicize numbers (2 h)
- [ ] **P1 / B3: Publish LinkedIn launch post** — Draft refreshed for the live mission/equity/stewardship posture and current feature set; remaining work is manual publication using `https://wait-time.ca` (30 min)
- [ ] **P1 / B4: Video walkthrough** — Script 3–4 min; record with decent audio; upload unlisted YouTube (3 h)
- [ ] **P2 / B5: GitHub topics & discoverability** — Add topic tags; check 1–2 open data registries (30 min)

### Phase C: After Verified Launch — Scholarly Artifacts & External Validation
[Full details: admissions-strengthening-plan.md](implementation/admissions-strengthening-plan.md)

- [ ] **P1 / C1: Technical report** — 2–4 page “Methodological Heterogeneity in Canadian ED Wait-Time Reporting”; gate publication on external read-through (1–2 d)
- [ ] **P1 / C2: Targeted researcher outreach** — 3 specific researchers at ICES/INSPQ/university labs; share technical report (3 h + response time)
- [ ] **P1 / C3: Equity layer interpretive summary** — Section in technical report; limitations ARE the finding (merged with C1)
- [ ] **P2 / C4: Operational transparency report** — One monthly report from DB tables; honest about cost-control mode (2 h)
- [ ] **P2 / C5: Incident post-mortem** — Quebec zero-value parser incident; write for interview preparation (1–2 h)
- [ ] **P2 / C6: Named reviewer acknowledgement** — If A4 or C2 produces a willing reviewer, add Acknowledgements to README (30 min; conditional)

### Phase D: Deferred — If Time Permits
[Full details: admissions-strengthening-plan.md](implementation/admissions-strengthening-plan.md)

- [ ] **P2 / D1: Comparability matrix upgrade** — Explicit per-pair field-by-field verdicts on /methods (conditional on current state)
- [ ] **P2 / D2: Quebec equity layer extension (M34)** — Apply Ontario template to QC with full rigor (blocked on StatsCan CT data)
- [ ] **P2 / D3: Per-hospital data freshness indicators** — `last_updated` timestamp on hospital cards and export CSV
- [ ] **P2 / D4: Nova Scotia scraper (M35)** — Only if NS methodology is confirmed novel (pre-research done)
- [ ] **P2 / D5: Grant/competition application** — Opportunistic only; do not actively search
- [ ] **P2 / D7: Official Ontario AED registry path** — Pursue partnership or explicit permission only if it improves coverage without weakening reuse clarity
- [ ] **P2 / D10: Re-evaluate Ontario naloxone options** — Revisit link-out vs embed vs native ingestion only if reuse rights become clearer or explicit permission is obtained
- [ ] **P2 / D11: Revisit municipal inspection strategy** — Reopen inspection/compliance work only if broader Ontario multi-jurisdiction coverage or a deliberate Toronto-first sidecar strategy emerges
- [ ] **P2 / Occupancy-based recommendations** — Smart hospital suggestions based on current occupancy
- [ ] **P2 / Monitoring dashboard** — Prometheus/Grafana integration for operational visibility
- [ ] **P2 / Advanced analytics** — Predictive wait time modeling based on historical patterns
- [ ] **P2 / Add GitHub Project board** (#47) — Process overhead

---

## Strategic Context

Each feature maps to CanMEDS competencies for medical school admissions:

| Competency | Delivered | Admissions Plan (New) |
|------------|----------|----------------------|
| **Scholar** | Metric ontology, comparability matrix, citation export, aggregation pipeline, anomaly detection, methodology change detection, property-based testing, data dictionary, OpenAPI docs, Zenodo DOI | Technical report (C1), Ottawa–Gatineau case study (A6), quantified findings (A7), equity interpretive summary (C3), limitations section (A2) |
| **Professional** | Clinical defensibility, divergence warnings, data quality transparency, peer benchmarking, SECURITY.md, LICENSE, CODE_OF_CONDUCT, privacy policy, terms of use, error boundaries, security headers, uptime monitoring | Operational transparency report (C4), incident post-mortem (C5), README mission/equity/stewardship section (A1), reflection document (A5) |
| **Health Advocate** | Access Burden Estimator, equity layer (ON), temporal access patterns, accessibility testing (WCAG), French language support, mobile responsiveness | Stakeholder interview with ER professionals (A4), equity layer interpretation (C3) |
| **Leader** | Multi-province scaling, systems architecture, regional dashboards, data quality monitoring, release management, operational documentation | Live production URL (B1), video walkthrough (B4), LinkedIn launch (B3), usage analytics (B2) |
| **Collaborator** | Province-aware telehealth routing, issue/PR templates, CODE_OF_CONDUCT, CONTRIBUTING guidelines | Stakeholder interview (A4), researcher outreach (C2), named reviewer acknowledgement (C6) |

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

## Top 10 Highest-Impact Items for Admissions

Ranked by **defensible admissions value per hour of effort** (updated 2026-03-12 after production launch verification):

1. **A1: Mission/equity/stewardship section** — Clarifies the site's public-interest posture and barrier-reduction goals (30 min)
2. **A4: Stakeholder interview** — Unlocks Collaborator competency; transforms project category (2–3 h + scheduling)
3. **A6: Ottawa–Gatineau case study** — Most narratively compelling specific story; interview-ready (2–3 h)
4. **A3: Fix placeholder Zenodo DOI** — Eliminates fake-DOI credibility risk; third-party attestation (90 min)
5. **B3: LinkedIn launch post** — Public timestamp; asymmetric upside for 30 min of effort (30 min)
6. **B4: Video walkthrough** — Only format where committee hears your voice and command of material (3 h)
7. **C1: Technical report** — Anchor Scholar artifact; no other pre-med applicant will have this (1–2 d)
8. **A7: Quantified metrics** — Specificity is more credible than vagueness (3 h)
9. **B2: Privacy-safe usage analytics** — Starts the clock on real usage evidence (2 h)
10. **C4: Operational transparency report** — Demonstrates disciplined stewardship, not just shipping (2 h)

Completed from the prior ranking: **A2 (limitations)** and **B1 (production hosting)** are now done. The remaining gap is real-world engagement and public-facing artifacts.

---

## Implementation Plans

Active milestone plans in `docs/planning/implementation/`:
- [`admissions-strengthening-plan.md`](implementation/admissions-strengthening-plan.md) — Phased plan (A/B/C/D) for real-world credibility, external validation, and public-facing artifacts. Includes full analytical rationale from three-pass review (original → devil's advocate → steelman → synthesis).

Archived (delivered):
- `docs/planning/implementation/archived/public-health-data-hub-batch-a-plan.md` — Public Health Hub Batch A implementation plan (delivered)
- `docs/planning/archive/public-health-data-hub-preplan.md` — Ontario public health hub pre-plan (delivered and archived)
- `docs/planning/archive/public-health-data-hub-decision-brief.md` — Ontario public health hub decision brief (delivered and archived)
- `docs/planning/archive/public-health-data-hub-identity-memo.md` — Public health hub identity decision (delivered and archived)
- `docs/planning/archive/public-health-data-hub-batch-a-handoff.md` — Batch A planning handoff (delivered and archived)
- `docs/planning/archive/public-health-data-hub-agent-execution-readiness.md` — Agent execution packet for Batch A (delivered and archived)
- `docs/planning/archive/public-health-data-hub-execution-order.md` — Locked Batch A execution order (delivered and archived)
- `docs/planning/archive/maintenance-2026-02-23.md` — CI/tooling maintenance (2026-02-23)
- `docs/planning/archive/maintenance-2026-03-21.md` — Ontario timeout hardening + repository maintenance sweep (2026-03-21)
- `docs/planning/archive/maintenance-2026-03-27.md` — Public health hub Batch A maintenance, archive, and roadmap reconciliation
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
- Ontario upstream slowness on GitHub Actions (resolved: extended HTTP read-timeout fallback for Ontario fetches)
- Hospital verification (resolved: verification gate in place)

---

## Architecture

### Database Schema (14 tables)

| Table | Purpose |
|-------|---------|
| `sources` | Provincial data source metadata with telehealth routing |
| `hospitals` | Facility metadata with verification workflow |
| `measurements` | Audit log of scraped wait times with ontology tags |
| `scraper_status` | Heartbeat monitoring |
| `scraper_alert_state` | Active stale/error incident state for alert deduplication |
| `measurement_aggregates` | Permanent statistical summaries (M13) |
| `data_quality_snapshots` | Daily scraper reliability metrics (M14) |
| `methodology_change_events` | Detected methodology shifts (M14) |
| `regions` | Province region metadata for analytics segmentation (M15) |
| `hospital_regions` | Hospital-to-region mappings for regional benchmarking (M15) |
| `public_data_sources` | Public-health-hub source catalog with provenance, freshness, and reuse posture |
| `resource_locations` | Normalized facility and AED locations for `/resources` |
| `public_health_alerts` | Normalized Health Canada recall and safety alert records |
| `public_health_source_alert_state` | Stateful incident tracking for public-health ingest alert deduplication |

### Key ADRs

| ADR | Decision |
|-----|----------|
| [0002](../adr/0002-metric-ontology.md) | Strict metric ontology for comparability |
| [0003](../adr/0003-manual-geocoding-overrides.md) | Manual geocoding overrides |
| [0020](../adr/0020-raw-retention-and-stateful-alerting.md) | Historical alerting/retention decision later superseded by ADR-0021 |
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
| [0021](../adr/0021-bounded-retention-cleanup-operations.md) | Keep 30-day raw retention cleanup bounded and separate from aggregate refresh |
| [0022](../adr/0022-frontend-read-cache-for-neon-transfer-guardrails.md) | Use short-lived frontend response caching to reduce Neon public transfer |

---

## Dependencies & Integrations

| Service | Purpose | Tier |
|---------|---------|------|
| Shared VPS | Live frontend hosting via Caddy + Docker | Shared host allocation |
| Neon PostgreSQL | Database hosting | Free (512 MB) |
| Mapbox | Map tiles | Free (50k loads/month) |
| Nominatim (OSM) | Geocoding | Free (1 req/sec) |
| Netlify | Rollback-only frontend hosting path | Free (300 credits/month) |
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

**Infrastructure Progress: 36/50 original items completed.** All governance, testing, documentation, and CI/CD infrastructure is in place.

**Current Execution Plan:** [Admissions Strengthening Plan](implementation/admissions-strengthening-plan.md) — 4-phase approach (A/B/C/D) totaling ~5–6 days of focused work over 6 weeks.

| Phase | Timeline | Items | Effort |
|-------|----------|-------|--------|
| **A: Credibility Cleanup** | Active | A1–A7 (mission/equity/stewardship, limitations, Zenodo DOI, stakeholder outreach, reflection doc, case study, metrics) | ~12–15 h |
| **B: Launch Follow-Through** | Active | B2–B5 (analytics, LinkedIn, video, discoverability) | ~5–6 h remaining |
| **C: Scholarly Artifacts** | Weeks 2–4 post-launch | C1–C6 (technical report, researcher outreach, equity interpretation, ops report, post-mortem, reviewer) | ~2–3 d |
| **D: If Time Permits** | Weeks 5–12 | D1–D5 (comparability matrix, QC equity, freshness indicators, NS scraper, grant/competition) | Variable |

**Next Action:** Keep A3 and A4 parked until explicitly activated. In the meantime, prioritize B3 (publish the launch post) and the remaining non-Zenodo credibility/communication items.
