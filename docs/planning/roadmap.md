# Implementation Roadmap

## Current Status (Updated 2026-02-08)

**Progress:** Milestone 14 Complete | Milestone 15 Closed & Archived (Analytics + Operationalization + Region Coverage) | M9 production smoke + readiness automation implemented | M9 repo polish + launch copy artifacts completed | M9 screenshot automation implemented | M9 testimonial governance hardening implemented | M11 equity layer scaffold + linkage summary implemented | M12 occupancy availability contract implemented | CI optimization pass implemented

**Strategic Direction:** Ontario-focused depth over multi-province breadth. The platform is
transitioning from a real-time snapshot tool into a Health Systems Observatory with longitudinal
analysis, data quality transparency, and research-grade analytics.

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
| **M10: Multi-Province** (partial) | Alberta scraper skeleton, BC scraper (ADR-0007) |
| **M11: Access & Equity** (partial) | Access Burden Estimator with fuel + parking cost (ADR-0005, 21 tests) |
| **M12: Research Infra** (partial) | Citation-ready data export (19 tests), Dead Man's Switch alerts (7 tests), SystemStatus component, occupancy availability endpoint/UI state |
| **M13: Aggregation Pipeline** | Permanent hourly/daily/weekly/monthly aggregates, backfill CLI, enhanced trends (90d/6m/1y), extended data export (ADR-0008) |
| **M14: Data Quality & Anomaly Detection** | DataQualityService, AnomalyDetectionService, MethodologyChangeDetector, /data-quality dashboard, 3 new DB tables (ADR-0009) |
| **M15: Analytics & Benchmarking** | Peer benchmarking, temporal pattern analysis, regional intelligence mapping, system trend dashboard, dedicated /analytics page |

---

## Next Steps

### Immediate: M9 Production Completion
- [ ] Deploy frontend to Render/Vercel with production `DATABASE_URL`
- [ ] Set required production GitHub Secrets (`DATABASE_URL`, optional alert keys) and run readiness verification
- [ ] Run production smoke workflow against live URL for `/`, `/methods`, `/data-quality`, `/analytics`

### Recently Closed: M15 Analytics & Benchmarking
**Status:** CLOSED (archived) | **Delivered:** 2026-02-07 | **Depends On:** M13
**Archived Plan:** `docs/planning/archive/milestone-15-analytics.md`

Delivered scope:
- Peer benchmarking (`/api/analytics/benchmarks` + UI integration)
- Temporal patterns (`/api/analytics/patterns`)
- Regional analytics (`regions` + `hospital_regions`, seed CLI, `/api/analytics/regions`)
- System trends (`/api/analytics/trends`, `/analytics`)
- Operational hardening (schema-aware setup guidance, daily-rollup fallback)
- Region coverage expansion (audit CLI, auto-assignment, overrides, coverage telemetry)

### Short-Term: Complete Partial Milestones

**M9: Portfolio Launch** — remaining items:
- [ ] Deploy frontend to Render/Vercel with production DATABASE_URL
- [ ] Set required production GitHub Secrets (DATABASE_URL, optional alert keys)
- [ ] Run `Production Readiness` workflow and confirm heartbeat freshness pass
- [ ] Set `PRODUCTION_BASE_URL` GitHub Actions secret and run smoke workflow
- [ ] Stakeholder interview (1 ER nurse/physician)
- [ ] Publish LinkedIn post

### Autonomous Backlog (No Human Intervention Required)

Completed in this cycle:
- M11: Equity layer foundation scaffolding (toggle, legend, placeholder GeoJSON flow)
- M12: Occupancy endpoint + explicit "not available yet" UI state
- Governance hardening for testimonial content validation (single published quote guardrails)
- CI optimization pass for developer velocity (keep checks strict, reduce redundant runtime)

Current open autonomous backlog:
- None (remaining open work is currently human/external dependency-bound)

**M11: Equity Layer** — remaining items:
- [ ] Research Canadian socioeconomic shapefiles (StatsCan census data)
- [ ] Replace placeholder equity GeoJSON with processed census tract layer

**M12: Research Infra** — remaining items:
- [ ] Occupancy ingestion/parser rollout when provincial source fields become available
- [ ] Proactive notification system (future)

### Deferred
- **M10: Multi-Province** — Alberta API endpoint research, additional provinces

---

## Strategic Context

Each feature maps to CanMEDS competencies for medical school admissions:

| Competency | Features |
|------------|----------|
| **Scholar** | Metric ontology, comparability matrix, citation export, aggregation pipeline, anomaly detection, methodology change detection |
| **Professional** | Clinical defensibility, divergence warnings, verification queue, data quality transparency, peer benchmarking |
| **Health Advocate** | Access Burden Estimator, equity layer, temporal access patterns |
| **Leader** | Multi-province scaling, systems architecture, regional dashboards, data quality monitoring |
| **Collaborator** | Province-aware telehealth routing, stakeholder interviews |

---

## Implementation Plans

Active milestone plans in `docs/planning/implementation/`:
- `milestone-9-launch.md` — Production deployment & stakeholder validation
- `milestone-10-provinces.md` — Alberta scraper & multi-province support
- `milestone-11-equity.md` — Access Burden Estimator & equity layer
- `milestone-12-research.md` — Citation export & alert system

Archived (delivered):
- `docs/planning/archive/milestone-15-analytics.md` — Analytics & benchmarking (M15)
- `milestone-13-aggregation.md` — Aggregation pipeline (M13)
- `milestone-14-data-quality.md` — Data quality & anomaly detection (M14)

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
| [0010](../adr/0010-region-mapping-coverage-heuristics.md) | Region mapping coverage audit and heuristic auto-assignment |
| [0011](../adr/0011-equity-layer-scaffold.md) | Equity layer scaffold-first delivery |
| [0012](../adr/0012-occupancy-availability-contract.md) | Occupancy availability contract and UI behavior |
| [0013](../adr/0013-testimonial-governance-guardrails.md) | Testimonial publication guardrails and fail-closed rendering |

---

## Dependencies & Integrations

| Service | Purpose | Tier |
|---------|---------|------|
| Neon PostgreSQL | Database hosting | Free (512 MB) |
| Mapbox | Map tiles | Free (50k loads/month) |
| Nominatim (OSM) | Geocoding | Free (1 req/sec) |
| Render | Frontend hosting | Free |
| GitHub Actions | CI/CD + scrapers | Free (2000 min/month) |
