# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-03-28

### Added
- Public Health Hub Batch A on `/resources`, including Ontario facility search, OSM-backed AED fallback, Health Canada alerts, AQHI, and an official Ontario naloxone link-out
- Ottawa–Gatineau methodology divergence case study
- Quantified "By the Numbers" methodology and operations findings in README

### Changed
- Reframed public-facing project language around mission, equity, EDIA, barrier reduction, and stewardship
- Updated citation metadata and Zenodo preparation for a current public release
- Added source-specific public-health ingest observability, smoke coverage, and readiness coverage

### Fixed
- Corrected the compare API to use the latest `TIME_TO_PROVIDER` measurement rather than accidentally comparing against a different latest metric such as Quebec occupancy
- Improved public `/resources` degraded-state behavior, facility relevance, and search-result compression
- Hardened public-health ingest reliability and best-effort AED failure handling

## [1.2.1] - 2026-02-23

### Changed
- Upgraded react-map-gl 7→8; migrated import path to `react-map-gl/mapbox`
- Upgraded date-fns 3→4
- Upgraded playwright / `@playwright/test` 1.40→1.58.2
- Bumped ruff pre-commit hook to v0.14.14 (matches venv and CI)
- Bumped mirrors-mypy pre-commit hook to v1.19.0; added `playwright` and `tenacity` to hook `additional_dependencies` for consistent stub resolution

### Fixed
- Removed stale `# type: ignore[misc]` from `@retry` decorators in all scrapers (redundant with mypy v1.19.0)
- Corrected `# type: ignore[assignment,misc]` placement in optional Playwright import fallback (`observability.py`)
- Removed redundant `cast(str, ...)` in Alberta scraper
- Fixed pytest match string in `test_database_service.py` to match actual error message
- Fixed E2E fixture to skip gracefully when `DATABASE_URL` is absent
- Fixed 41 ruff I001 import-sort violations across backend test files
- Updated Map.tsx event handler types for react-map-gl v8 API
- Pruned stale remote-tracking branch after dependabot PR squash-merge

## [1.2.0] - 2026-02-19

### Added
- **M33: Historical Occupancy Trends**
  - Extended aggregation pipeline to include `STRETCHER_OCCUPANCY` metric family.
  - Added metric-family-aware filtering to analytics trends API.
  - Added collapsible "Historical Occupancy Trend" panel to Analytics dashboard.
  - Refactored `SystemTrendChart` to be generic for both wait times and occupancy.
  - Documented aggregation grouping decision in ADR-0019.
  - Updated operational cadence targets in `scraper-cron.yml`.

## [1.1.0] - 2026-02-19

### Added
- Divergence Briefs & Quality Drift UI (M31)
- Scraper Visibility & Reliability Hardening (M30)
- Equity Academic Rigor Hardening (M29)
- Ontario Real-Data Equity Layer (M28)
- Operational Observability: Drift monitor, `/status` page, Lighthouse CI (M27)
- Strategic Documentation: Data dictionary, data flow architecture, property-based testing (M26)
- Reliability & Verification Phase 2: 80% backend coverage, API integration tests (M25)
- Quality & Standardization: `mypy strict`, axe-core, mobile responsive tests, rate limiting (M23)
- Public documentation: OpenAPI spec and MkDocs site (M22)
- French Language Support (`next-intl` bilingual routing) (M21)
- Reliability & Verification: API response time tracking, E2E pipeline, visual regression (M20)
- Governance & Quality: LICENSE, SECURITY.md, CODE_OF_CONDUCT, CITATION.cff, issue templates (M19)

### Fixed
- Quebec parser zero-value guard (`ge=0`)
- Cache & polling audit (tight TTLs, `no-store` on user-specific routes)
- Legacy deploy gate hardening

## [1.0.0] - 2026-02-11

### Added
- Quebec stretcher occupancy frontend with OccupancyBadge component (M18)
- Quebec occupancy scraper extraction with real-time percentages (M17)
- Multi-province operationalization: AB, BC, QC hospital seed data (M16)
- Analytics & benchmarking dashboard with peer comparisons (M15)
- Data quality & anomaly detection services with monitoring dashboard (M14)
- Aggregation pipeline with permanent hourly/daily/weekly/monthly summaries (M13)
- Four-province breadth achieved (ON, QC, AB, BC)
- 380+ hospitals visible across all provinces
- 15 health regions mapped with analytics segmentation

### Changed
- Legacy deploy path now release-gated for cost control
- Frontend hosting intentionally offline pending production release
- Production smoke workflow made optional in offline mode

### Fixed
- Runtime usage optimizations with API caching and polling guardrails
- Docs CI failures and roadmap consistency checks
- Ruff linting errors in scraper CI

## [0.9.0] - 2026-02-08

### Added
- Dead Man's Switch alerts with state-change notifications (M12)
- Citation-ready data export with methodology tags and granularity control (M12)
- Occupancy availability contract and API endpoints (M12)
- Access Burden Estimator with fuel and parking cost calculations (M11)
- Equity layer scaffold with linkage summary (M11)
- Heartbeat monitoring operational with stale data alerting

## [0.8.0] - 2026-02-07

### Added
- Public launch artifacts: About section and governance updates (M9)
- Production readiness automation and smoke tests (M9)
- Screenshot automation workflow for public documentation (M9)
- FAQ page with JSON-LD structured data (M8)
- Expandable hospital cards with quick actions (M8)
- Schema.org structured data for SEO (M7)
- Geolocation-based distance sorting (M7)
- Skeleton loading states for improved UX (M7)
- PWA setup with service worker and manifest (M4)
- Dark mode support with theme toggle (M4)
- Split view with map and list components (M4)
- Trend charts with 90d/6m/1y aggregate visualization (M4)
- Methodology divergence warnings component (M3)
- Comparability matrix on /methods page (M3)
- Hospital detail modal with methodology display (M3)
- Ontario Playwright scraper with 160+ hospitals (M2)
- Nominatim geocoding service (M2)
- Mapbox frontend with interactive map (M2)
- Quebec BeautifulSoup scraper (M1)
- PostgreSQL schema with 9 tables (M1)
- Ontology enums for metric comparability (M1)
- Heartbeat monitoring system (M1)

## [0.1.0] - 2026-01-15

### Added
- Initial project structure
- Database foundation
- Basic scraper architecture
- Core ontology design

[1.2.1]: https://github.com/jerdaw/waittimecanada/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/jerdaw/waittimecanada/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/jerdaw/waittimecanada/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/jerdaw/waittimecanada/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/jerdaw/waittimecanada/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jerdaw/waittimecanada/compare/v0.1.0...v0.8.0
[0.1.0]: https://github.com/jerdaw/waittimecanada/releases/tag/v0.1.0
