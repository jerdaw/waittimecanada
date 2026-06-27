# Implementation Roadmap

## Current Status (Updated 2026-06-27)

**Progress:** Milestone 33 is complete. Wait Time Canada is now in a
stewardship and selective-expansion phase: the public roadmap emphasizes
methodology, limitations, local development, safe public use, source freshness,
careful public-health resource scope, and disciplined maintenance rather than
broad feature churn. The public documentation boundary cleanup is complete and
captured in ADR-0026. Roadmap wording avoids hospital-choice recommendation
framing and uses system-pressure terminology instead. ADR-0027's public
heartbeat offload scaffold is merged; remaining pilot work is private runner
provisioning and manual validation outside this repository. The 2026-06-22
maintenance pass aligned backend setup and CI with the checked-in `uv.lock`,
added migration sequence guardrails, added frontend test-file type checking,
and archived completed repo-audit planning stubs out of the active planning
root. The 2026-06-27 follow-up added a practical local-build secret-handling
policy, a checksum-backed migration ledger, disposable database verification,
frontend audit remediation through the Vitest 4 toolchain upgrade, and a
manual Playwright lane that no longer depends on production secrets.

Wait Time Canada is a four-province health systems observatory covering Ontario,
Quebec, Alberta, and British Columbia. The platform audits publicly reported
emergency department wait-time data, preserves methodology metadata, and exposes
where direct comparisons are invalid.

Completed foundations:

- PostgreSQL schema, ontology enums, and source provenance tracking
- Four provincial scraper lanes with source-health reporting
- Methodology divergence warnings and comparability matrix
- Data quality dashboard, anomaly detection, and methodology-change tracking
- Aggregation pipeline for raw, hourly, daily, weekly, and monthly summaries
- Analytics and benchmarking dashboard
- Quebec stretcher-occupancy capture and historical occupancy trends
- Ontario-first public-health resources module with source caveats
- Privacy, terms, citation metadata, security policy, and contributor guidance
- Public documentation boundary cleanup with private notes moved to the
  private/shared operations source of truth
- Documentation and CI guardrails for public-boundary checks, human-authorship
  policy, roadmap freshness, ontology drift, and Docs CI path coverage
- ADR-0027 strategy, public heartbeat offload contract, and copy/adapt-only
  Forgejo example for trusted runner adoption
- Backend `uv.lock` setup and CI alignment, migration sequence validation, and
  frontend test-file type checking

## Public Documentation Boundary

This repository contains public project documentation and reproducible
development information. Deployment details, credentials, monitoring
configuration, private operational notes, and environment-specific production
paths are intentionally excluded from public documentation.

## Active Priorities

### Now

- Keep the methodology ontology and comparability logic stable.
- Maintain source freshness, data-quality, and anomaly-detection behavior.
- Keep `/resources` Ontario-first, provenance-first, and explicit about source
  scope and freshness.
- Preserve the 30-day raw-measurement retention policy while keeping permanent
  aggregates for long-term analysis.
- Use manual-dispatch operational workflows while scheduled GitHub Actions
  triggers are paused for free-tier quota conservation.
- Complete the ADR-0027 heartbeat offload pilot with private runner
  provisioning and manual validation, using the public contract in
  `docs/operations/heartbeat-offload-pilot.md` and keeping GitHub manual
  dispatch as fallback.
- Preserve locked backend dependency, migration sequence, and frontend
  test-type-check guardrails during routine maintenance.
- Keep frontend dependency audit remediation current; the 2026-06-27 pass
  leaves `npm audit --audit-level=high` clean.

### Next

- Extend public research artifacts around methodology divergence and reporting
  limitations.
- Revisit multi-province equity layers only when province-specific source and
  tract validation are available.
- Continue selective public-health resource expansion only when the source is
  official, reusable, and product-relevant.
- Improve accessibility, localization, and mobile usability across high-traffic
  flows.

### Later

- Evaluate additional provinces where public data sources are stable enough for
  responsible ingestion.
- Explore smarter scrape scheduling that reduces unnecessary load while
  preserving freshness.
- Expand trend and export tooling for research and policy users.

## Active Roadmap

### Now

- [ ] **P0 / Preserve clinical safety boundaries:** Keep emergency, non-triage,
  and non-medical-advice disclaimers prominent across public surfaces.
- [ ] **P0 / Preserve ontology comparability:** Keep metric-family, start-event,
  end-event, and statistic-type matching as the direct-comparison rule.
- [ ] **P1 / Maintain source freshness:** Keep source status and data-quality
  reporting explicit without exposing private monitoring configuration.
- [ ] **P1 / Complete private heartbeat offload pilot:** Use the public
  contract in `docs/operations/heartbeat-offload-pilot.md` to validate a
  trusted offloaded runner manually before enabling a private schedule.
- [ ] **P1 / Restore scheduled workflow cadence:** Re-enable scraper,
  heartbeat, snapshot, public-health ingest, and smoke schedules incrementally
  after the heartbeat pilot succeeds, keeping GitHub manual dispatch as
  fallback.

### Next

- [ ] **P1 / Extend public methodology artifacts:** Maintain case studies and
  export examples with complete source attribution and limitations.
- [ ] **P1 / Select resource expansion carefully:** Add public-health resource
  sources only when official, reusable, and clearly caveated.
- [ ] **P1 / Harden offloaded operations:** Document runner isolation, secret
  handling, log retention, failure summaries, and rollback procedures before
  moving each secret-bearing workflow.
- [ ] **P2 / Maintain public docs boundary:** Keep local setup, API contracts,
  and methodology docs reproducible and free of private operational details.

### Later

- [ ] **P2 / Evaluate additional provinces:** Add provinces only when public
  source stability supports responsible ingestion.
- [ ] **P2 / Explore smarter scheduling:** Reduce unnecessary upstream load
  while preserving public freshness expectations.
- [ ] **P2 / Reassess external CI or full Forgejo migration:** Revisit broader
  CI migration only if the hybrid offload pilot does not meet cost, reliability,
  or operational-safety expectations.

## Roadmap Operating Model

- **Single source of truth:** this file summarizes active public roadmap state.
- **Priority discipline:** `P0` = correctness/reliability blockers, `P1` =
  capability delivery, `P2` = polish and documentation.
- **Definition of done:** code merged with relevant tests, public docs updated
  when behavior or methodology changes, and source limitations preserved.
- **Clinical safety:** no feature should provide medical advice, triage, or
  hospital-choice recommendations.

## Completed Milestones

| Milestone | Summary |
|-----------|---------|
| **M1: Database Foundation** | PostgreSQL schema, ontology enums, Quebec scraper, and source status tracking |
| **M2: Ontario End-to-End** | Ontario scraper, geocoding, Mapbox frontend, and hospital inventory |
| **M3: Methodology Warnings** | Divergence warnings, methods page, and comparison context |
| **M4: Polish and PWA** | Emergency banner, dark mode, split view, trend charts, and PWA setup |
| **M7: UX Polish and SEO** | Structured data, skeleton loading, search/filter, geolocation, and live indicators |
| **M8: UX Enhancements** | Expandable cards, FAQ, quick actions, and distance sorting |
| **M9: Public Launch Foundations** | Public about/governance surfaces and screenshot guidance |
| **M10: Multi-Province Groundwork** | Alberta and British Columbia scraper groundwork |
| **M11: Access and Equity** | Access Burden Estimator and equity scaffold |
| **M12: Research Infrastructure** | Citation-ready export and source freshness checks |
| **M13: Aggregation Pipeline** | Permanent hourly/daily/weekly/monthly aggregates |
| **M14: Data Quality and Anomaly Detection** | Data-quality service, anomaly detection, and methodology-change tracking |
| **M15: Analytics and Benchmarking** | Peer benchmarking, temporal patterns, and regional intelligence |
| **M16: Multi-Province Operationalization** | Four-province source inventory and methodology documentation |
| **M17: Quebec Occupancy Implementation** | Stretcher occupancy extraction and ontology support |
| **M18: Occupancy Frontend UI** | Occupancy display and availability messaging |
| **M19: Governance and Quality** | License, security policy, citation metadata, privacy, terms, and loading states |
| **M23: Quality Standardization** | Typing, accessibility, mobile, validation, and rate-limit hardening |
| **M28: Ontario Real-Data Equity Layer** | Ontario StatsCan tract integration and provenance |
| **M29: Ontario Equity Rigor Hardening** | Uncertainty, suppression, and non-causal interpretation safeguards |
| **M30: Scraper Visibility and Reliability** | Structured source failure metadata and status improvements |
| **M31: Divergence Briefs and Quality Drift** | Quality snapshots and divergence context |
| **M32: CSV Divergence Warnings** | Methodology warnings in exported datasets |
| **M33: Historical Occupancy Trends** | Occupancy aggregation and analytics trend support |

## Architecture Reference

| Area | Current Direction |
|------|-------------------|
| Data model | Strict ontology tags preserve source semantics rather than normalizing away differences |
| Comparability | Measurements are comparable only when metric family, start event, end event, and statistic type match |
| Storage | Raw measurement rows are retained briefly; permanent aggregates support long-term analysis |
| Public resources | Ontario-first, source-catalog-driven, and explicit about freshness and reuse limits |
| Safety | Emergency disclaimers and non-clinical interpretation limits must remain prominent |

### Database Schema (15 tables)

| Table | Purpose |
|-------|---------|
| `sources` | Provincial source metadata and methodology provenance |
| `hospitals` | Facility metadata and visibility controls |
| `measurements` | Raw measurement audit rows with ontology tags |
| `scraper_status` | Source freshness records |
| `scraper_alert_state` | Stateful source-health reconciliation |
| `measurement_aggregates` | Permanent trend aggregates |
| `data_quality_snapshots` | Data-quality summary windows |
| `methodology_change_events` | Detected reporting-method shifts |
| `regions` | Province/region metadata |
| `hospital_regions` | Hospital-to-region mapping |
| `public_data_sources` | Public-health resource source catalog |
| `resource_locations` | Normalized public-health resource locations |
| `public_health_alerts` | Public-health alert records |
| `public_health_system_metrics` | Public-health system context metrics |
| `public_health_source_alert_state` | Public-health ingest source-health state |

## Key ADRs

| ADR | Decision |
|-----|----------|
| [0002](../adr/0002-metric-ontology.md) | Strict metric ontology for comparability |
| [0005](../adr/0005-access-burden-estimator.md) | Access Burden Estimator design |
| [0008](../adr/0008-aggregation-pipeline.md) | Two-tier aggregation pipeline |
| [0009](../adr/0009-data-quality-anomaly-detection.md) | Data quality and anomaly detection |
| [0015](../adr/0015-real-equity-layer-ontario.md) | Ontario real-data equity layer |
| [0016](../adr/0016-equity-academic-rigor-hardening-ontario.md) | Ontario equity rigor hardening |
| [0019](../adr/0019-occupancy-trend-aggregation.md) | Include stretcher occupancy in aggregation |
| [0023](../adr/0023-public-health-hub-module-boundary.md) | Public Health Hub boundary |
| [0024](../adr/0024-ontario-naloxone-link-out-posture.md) | Ontario naloxone link-out posture |
| [0025](../adr/0025-data-quality-scrape-window-and-runtime-env-contracts.md) | Data-quality scrape-window and runtime env contracts |
| [0026](../adr/0026-public-documentation-boundary.md) | Public documentation boundary and private maintainer-note handling |
| [0027](../adr/0027-hybrid-ci-offload-strategy.md) | Hybrid CI/offload strategy for GitHub Actions quota pressure |

## Future Work

- Additional province evaluation: Nova Scotia, New Brunswick, Manitoba, and
  Saskatchewan only where public source stability supports responsible use.
- Multi-province equity methodology: defer until source acquisition,
  geographic linkage, and uncertainty communication can be province-specific.
- Public-health resources: avoid broad batch expansion; prefer narrow,
  source-validated additions with clear caveats.
- Research outputs: maintain case studies, export interpretation guidance, and
  exported datasets with complete methodology labels and source attribution.
- CI/runtime cost control: complete the ADR-0027 private heartbeat pilot, then
  offload trusted recurring operations incrementally while preserving GitHub as
  the public collaboration surface.
- Tooling maintenance: keep backend setup, GitHub Actions, and local
  verification commands aligned with the checked-in lockfiles and testing
  guidelines.

## Implementation Plan References

Existing public historical plans retained for context:

- `docs/planning/archive/maintenance-2026-06-22-tooling-roadmap-maintenance.md`
- `docs/planning/archive/maintenance-2026-06-04-public-docs-cleanup.md`
- `docs/planning/archive/maintenance-2026-06-12-autonomous-stewardship.md`
- `docs/planning/archive/2026-04-23-repo-audit-follow-up-board.md`
- `docs/planning/archive/2026-04-23-repo-audit-remediation-plan.md`
- `docs/planning/archive/heartbeat-offload-pilot-scaffold-2026-06-13.md`
- `docs/planning/archive/milestone-17-quebec-occupancy.md`
- `docs/planning/archive/milestone-18-occupancy-frontend.md`
- `docs/planning/archive/milestone-23-quality-standardization.md`
- `docs/planning/archive/milestone-28-equity-real-data-ontario.md`
- `docs/planning/archive/milestone-29-equity-academic-rigor-hardening.md`
- `docs/planning/archive/public-health-data-hub-decision-brief.md`
