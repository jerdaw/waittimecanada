# Implementation Roadmap

## Current Status (Updated 2026-02-11)

**Progress:** **M16 Complete** (Multi-Province Operationalization) | Milestone 15 Complete & Archived | M9 production smoke + readiness automation implemented | M9 repo polish + launch copy artifacts completed | M9 screenshot automation implemented | M9 testimonial governance hardening implemented | M9 About section component completed | M11 equity layer scaffold + linkage summary implemented | M12 occupancy availability contract implemented | CI optimization pass implemented | Documentation modernization + docs quality automation implemented

**Strategic Direction:** **Four-province breadth achieved** (ON, QC, AB, BC). All four scrapers active in production, 380+ hospitals visible across all provinces, methodology documentation complete for all provinces, regional analytics data seeded for 15 regions.

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

---

## Next Steps (1-2 Sessions)

- [x] **M16 Phase 1:** Fix trusted source auto-approval so scraper-discovered hospitals are visible.
- [x] **M16 Phase 2:** Create hospital seed data for AB, BC, QC with verified coordinates.
- [x] **M16 Phase 3:** Complete methodology documentation for Alberta and Quebec.
- [x] **M16 Phase 4:** Expand region data to AB, BC, QC for regional analytics.
- [x] **M16 Phase 5:** Cross-province verification and roadmap cleanup.

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

## Active Roadmap (Now / Next / Later)

### Now (P0, 0-2 weeks)
- [x] **P0 / Data correctness:** Correct data-quality metric math so totals are query-backed counts (not inferred from success-rate approximations).
- [x] **P0 / Ontology safety:** Enforce ontology-safe analytics grouping so aggregates are never mixed across incompatible methodologies.
- [x] **P0 / Source consistency:** Resolve ontology/source metadata drift across migrations, seed JSON, and scraper factories.
- [x] **P0 / Ops reliability:** Replace hardcoded source lists in heartbeat checks with dynamic source discovery from `sources`.
- [x] **P0 / Methodology monitoring:** Wire methodology change detection into scheduled ops and expose change events in API/UI.

Success criteria for `Now`:
- Data-quality totals match direct SQL count validation in tests.
- Analytics endpoints reject or separate incompatible ontology dimensions.
- Heartbeat checks automatically adapt to source table updates without code changes.

### Next (P1, 2-6 weeks)
- [x] **P1 / Equity:** Replace placeholder equity layer payload with processed tract dataset pipeline and production Ontario load.
- [x] **P1 / Occupancy:** Implement occupancy schema columns + scraper ingestion path + validations/backfill.
- [x] ~~**P1 / Admin security:**~~ Removed — admin verification queue was over-engineered for trusted government data sources; automated quality controls (anomaly detection, data quality monitoring) provide better assurance.
- [x] **P1 / Methods UX:** Add methodology timeline, deep-linkable comparisons, and comparability matrix CSV export.
- [x] **P1 / CI hardening:** Remove non-blocking CI fallbacks and make quality/security gates strict after remediation.
- [x] **P1 / Security debt:** Resolve Bandit finding in synthetic test data generator.

Success criteria for `Next`:
- Equity and occupancy endpoints serve real production-backed values (not scaffold-only payloads).
- ~~Admin verification actions are fully authenticated and auditable.~~ (Removed — not needed for trusted government sources.)
- CI gates fail hard for lint/type/security once remediation is complete.

### Now (P1, 0-2 weeks) — M16: Multi-Province Operationalization
- [x] **M16 Phase 1 / Auto-approval:** Fix hospital visibility for trusted government sources (scraper + backfill CLI).
- [x] **M16 Phase 2 / Hospital seed data:** Create curated seed files for AB, BC, QC with verified coordinates (65 hospitals total).
- [x] **M16 Phase 3 / Methodology docs:** Complete Alberta and Quebec methodology documentation + 4-province comparability index.
- [x] **M16 Phase 4 / Region expansion:** Create health region definitions for AB, BC, QC (15 regions, 65 mappings).
- [x] **M16 Phase 5 / Verification:** Cross-province verification, M10 archived, manual-tasks updated, roadmap cleanup.

Success criteria for `Now`:
- Hospitals from all 4 provinces visible in API/frontend.
- Methodology documentation complete for all 4 provinces.
- Regional analytics coverage >80% per province.

### Later (P2+, 6+ weeks)
- [x] **P2 / Test quality:** Eliminate React `act(...)` warnings in frontend unit tests.
- [x] **P2 / Docs integrity:** Add roadmap consistency checks so stale status summaries cannot regress.
- [ ] **P2 / Portfolio launch completion:** Complete stakeholder interview and publish launch communications when public hosting is re-enabled.

---

## Strategic Context

Each feature maps to CanMEDS competencies for medical school admissions:

| Competency | Features |
|------------|----------|
| **Scholar** | Metric ontology, comparability matrix, citation export, aggregation pipeline, anomaly detection, methodology change detection |
| **Professional** | Clinical defensibility, divergence warnings, data quality transparency, peer benchmarking |
| **Health Advocate** | Access Burden Estimator, equity layer, temporal access patterns |
| **Leader** | Multi-province scaling, systems architecture, regional dashboards, data quality monitoring |
| **Collaborator** | Province-aware telehealth routing, stakeholder interviews |

---

## Implementation Plans

Active milestone plans in `docs/planning/implementation/`:
- `docs/planning/implementation/milestone-16-multi-province-ops.md` — M16: Multi-Province Operationalization (COMPLETE)
- `docs/planning/implementation/milestone-9-launch.md` — Production deployment & stakeholder validation
- `docs/planning/implementation/milestone-11-equity.md` — Access Burden Estimator & equity layer
- `docs/planning/implementation/milestone-12-research.md` — Citation export & alert system
- `docs/planning/implementation/m9-remaining-user-actions.md` — M9 manual user action guide (active)

Archived (delivered):
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
