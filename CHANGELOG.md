# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- Netlify deploys now release-gated for cost control
- Frontend hosting intentionally offline pending production release
- Production smoke workflow made optional in offline mode

### Fixed
- Runtime usage optimizations with API caching and polling guardrails
- Docs CI failures and roadmap consistency checks
- Ruff linting errors in scraper CI

## [0.9.0] - 2026-02-08

### Added
- Dead Man's Switch alerts with Pushover integration (M12)
- Citation-ready data export with methodology tags and granularity control (M12)
- Occupancy availability contract and API endpoints (M12)
- Access Burden Estimator with fuel and parking cost calculations (M11)
- Equity layer scaffold with linkage summary (M11)
- Heartbeat monitoring operational with stale data alerting

## [0.8.0] - 2026-02-07

### Added
- Portfolio launch artifacts: About section, application summary (M9)
- Production readiness automation and smoke tests (M9)
- Screenshot automation workflow for portfolio documentation (M9)
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
- Neon PostgreSQL schema with 9 tables (M1)
- Ontology enums for metric comparability (M1)
- Heartbeat monitoring system (M1)

## [0.1.0] - 2026-01-15

### Added
- Initial project structure
- Database foundation
- Basic scraper architecture
- Core ontology design

[1.0.0]: https://github.com/jerdaw/waittimecanada/compare/v0.9.0...v1.0.0
[0.9.0]: https://github.com/jerdaw/waittimecanada/compare/v0.8.0...v0.9.0
[0.8.0]: https://github.com/jerdaw/waittimecanada/compare/v0.1.0...v0.8.0
[0.1.0]: https://github.com/jerdaw/waittimecanada/releases/tag/v0.1.0
