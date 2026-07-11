# Implementation Roadmap

## Current Snapshot (Updated 2026-07-10)

**Progress:** Milestone 33 is complete. Wait Time Canada is in a stewardship
and selective-expansion phase.

The observatory covers Ontario, Quebec, Alberta, and British Columbia while
preserving each source's methodology and exposing invalid direct comparisons.
Historical occupancy aggregation and the Ontario-first public-health resources
module are live. Repository-side reliability, documentation, migration, and
offloaded-operations contracts are implemented.

The immediate delivery focus is the trusted source-freshness offload pilot.
Runner provisioning, protected credential configuration, live command
validation, schedule cutover, and the 24-hour proof window remain external
operator work. GitHub manual dispatch remains the fallback until that evidence
is accepted.

## Completed Foundations

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
- Public offloaded-operations acceptance controls for runner isolation, secret
  handling, log retention, bounded failure summaries, and schedule-level
  rollback, paired with a private operator procedure
- ADR-0027 strategy, public source-freshness offload contract, and
  copy/adapt-only trusted-runner examples for scraper, watchdog, and aggregate
  adoption
- ADR-0028 critical-only operational notification mode with persisted
  notified-tier state for scraper and public-health source incidents
- Backend `uv.lock` setup and CI alignment, migration sequence validation, and
  frontend test-file type checking

## Continuous Guardrails

- Keep emergency, non-triage, and non-medical-advice boundaries prominent.
- Do not provide hospital-choice recommendations.
- Compare measurements directly only when metric family, start event, end event,
  and statistic type match.
- Keep source freshness, data-quality state, and official-source attribution
  visible without exposing private monitoring configuration.
- Retain raw measurements for 30 days while preserving permanent aggregates.
- Keep public documentation free of credentials, private hostnames, private
  paths, monitoring routes, and environment-specific deployment details.
- Preserve low-frequency health polling, bounded cache policies, and explicit
  production cost controls.
- Keep GitHub manual dispatch available until an accepted offload proof window
  and rollback review support schedule changes.

## Execution Queue

| Priority | Outcome | State | Gate | Done when |
| --- | --- | --- | --- | --- |
| P1 | Complete the trusted source-freshness offload pilot | External prerequisite | Merge the public contract and private companion, provision a trusted runner, and configure protected credentials outside this repository | Manual scraper, watchdog, aggregate, and smoke checks pass; timers complete a clean 24-hour soak with fallback retained |
| P1 | Restore remaining scheduled workflow cadence | External prerequisite | Accept the offload proof window and value-free rollback evidence | Reviewed schedules run at the intended cadence and GitHub `workflow_dispatch` remains available |
| P1 | Resolve Ontario methodology representation | Decision required | Decide the composite start, qualifying-provider endpoint, historical migration or versioning, source metadata, divergence behavior, and frontend labels together | Runtime tags, historical treatment, public methodology text, and regression tests implement one reviewed decision |
| P1 | Extend public methodology artifacts | Decision required | Complete Ontario revalidation or verify another official methodology change | Case studies and export examples carry current definitions, provenance, limitations, and comparison warnings |
| P1 | Select public-health resource expansion | Decision required | Identify an official, reusable, product-relevant source with documented caveats | The source catalog, ingest path, freshness behavior, public limitations, and tests are merged |
| P2 | Evaluate additional provinces | External prerequisite | Find a stable official public source with sufficient methodology documentation | The source is represented with ontology, provenance, clinical-safety boundaries, monitoring, and tests |
| P2 | Explore smarter scheduling | Later | Establish safe low-activity bounds from sustained freshness evidence | Upstream requests decrease without breaching public freshness expectations and manual fallback remains available |
| P2 | Reassess external CI or full Forgejo migration | Later | The hybrid offload pilot fails documented reliability or cost objectives | A reviewed ADR selects a bounded migration or explicitly retains the hybrid model |

Roadmap lifecycle and formatting rules are defined in
[`roadmap-process.md`](roadmap-process.md); operator and recurring triggers are
tracked in [`manual-tasks.md`](manual-tasks.md).

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

## Implementation Plan References

Existing public historical plans retained for context:

- `docs/superpowers/plans/2026-07-10-public-api-error-hardening.md`
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
