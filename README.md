# Wait Time Canada

> A clinically defensible Health Systems Observatory for Canadian emergency department wait-time methodology and data quality.

[![Frontend CI](https://github.com/jerdaw/waittimecanada/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/jerdaw/waittimecanada/actions/workflows/frontend-ci.yml)
[![Scraper CI](https://github.com/jerdaw/waittimecanada/actions/workflows/scraper-ci.yml/badge.svg)](https://github.com/jerdaw/waittimecanada/actions/workflows/scraper-ci.yml)
[![Production Readiness](https://github.com/jerdaw/waittimecanada/actions/workflows/production-readiness.yml/badge.svg)](https://github.com/jerdaw/waittimecanada/actions/workflows/production-readiness.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 22+](https://img.shields.io/badge/node.js-22+-green.svg)](https://nodejs.org/)
[![Tests](https://img.shields.io/badge/tests-verified-success.svg)](https://github.com/jerdaw/waittimecanada)
[![Documentation](https://img.shields.io/badge/docs-deployed-blue.svg)](https://jerdaw.github.io/waittimecanada/)
[![Data Freshness](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fjerdaw%2Fwaittimecanada%2Fbadges%2Ffreshness.json&query=%24.message&label=Last%20Scrape&color=%24.color)](https://github.com/jerdaw/waittimecanada/actions/workflows/scraper-cron.yml)

---

## 📊 Overview

**Wait Time Canada is not a simple wait-time leaderboard.** It's a comprehensive health systems observatory that audits and exposes methodological inconsistencies in Canadian emergency department reporting across provinces.

### Current Coverage

- **4 Provinces:** Quebec, Ontario, Alberta, British Columbia
- **380+ Hospitals:** Near-real-time monitoring across all regions
- **Scheduled Updates:** Automated data collection from public provincial sources
- **First-in-Canada:** Real-time ED stretcher occupancy visualization (Quebec)
- **Ontario Public Resources Module:** `/resources` now serves facilities, OSM-backed AED fallback data, Health Canada recalls, AQHI, analytics-only Ontario EMS system context, Ontario reserve-system long-term drinking water advisories, and an official Ontario naloxone link-out with a first-class source catalog

### Why This Matters

Provincial health authorities report ER wait times using **fundamentally different methodologies**:
- Quebec starts the clock at **REGISTRATION** (administrative check-in)
- Ontario starts at **TRIAGE** (clinical assessment)
- Different statistical measures (P90 vs rolling averages)
- Different patient populations (all vs mid-acuity)

**Direct comparison without methodology awareness is clinically misleading.** This observatory makes those differences transparent.

### By the Numbers

As reflected in the current runtime and roadmap baseline on **2026-04-23**:

- **4 provinces** remain in the active audited source set: Quebec, Ontario,
  Alberta, and British Columbia
- **380+ hospitals** are represented across the current provincial inventories
- **4 distinct statistic types** are still present across the active provinces:
  `MEAN`, `ROLLING_AVG`, `POINT_ESTIMATE`, and `P90`
- **6 of 6 cross-province source pairs** still fail direct comparability on the
  current ontology tags
- **1 province** currently publishes live stretcher occupancy in the platform:
  Quebec

These are methodology and operations findings, not performance rankings. They describe what the system is auditing and how the data is structured, not which province or hospital is "better."

---

## Limitations

- Scraper freshness reflects scheduled ingestion rather than continuous real-time monitoring.
- Provincial methodology labels are inferred from public documentation and can lag unannounced reporting changes by source organizations.
- Reported wait times and occupancy values are limited to what provinces publish; the platform cannot surface unreported overcrowding or internal flow constraints.
- The equity layer is currently implemented for Ontario only and should not be generalized to other provinces without province-specific source and tract validation.

## Public Documentation Boundary

This repository contains public project documentation and reproducible development information. Deployment details, credentials, monitoring configuration, private operational notes, and environment-specific production paths are intentionally excluded from public documentation.

---

## ✨ Key Features

### 🎯 Methodology Transparency
- **Ontology-Based Architecture:** Every measurement tagged with start_event, end_event, statistic_type, patient_scope
- **Divergence Warnings:** Automatic alerts when comparing incompatible metrics
- **Comparability Matrix:** Visual display of cross-province methodology alignment
- **Deep Linking:** Share specific hospital comparisons with methodology context

### 📈 Data Quality & Freshness
- **Anomaly Detection:** Automated flagging of suspicious measurements
- **Data Quality Dashboard:** Real-time visibility into scraper health, measurement counts, staleness
- **Freshness Monitoring:** Heartbeat checks flag stale or failed source updates
- **Methodology Change Detection:** Tracks when provincial reporting methods change

### 🚑 Public Health Resources
- **Facilities & Services:** Ontario facility search grounded in MOHSERLO reference-directory data
- **AED Fallback Map:** OpenStreetMap-based AED locations with explicit crowdsourced/incomplete labeling
- **Safety Alerts:** Health Canada recalls and safety alerts with optional Drug Product Database enrichment
- **Ontario EMS Context:** Annual land-ambulance response-time summaries presented as background system context only
- **Ontario Water Advisories:** Official ISC long-term drinking water advisories for Ontario reserve systems with freshness-aware suppression
- **Official Naloxone Link-Out:** Ontario naloxone guidance is linked to the provincial source rather than republished until reuse rights are clearer
- **AQHI Overlay:** Cached GeoMet air-quality snapshots with freshness-aware suppression when upstream data is stale
- **Source Transparency:** Provenance links, last refresh timestamps, and domain-specific caveats on every public-health slice

### 🏥 Real-Time Occupancy (Quebec)
- **First-in-Canada:** Stretcher occupancy percentage visualization
- **Color-Coded Indicators:**
  - 🟢 Green (<90%): Below capacity
  - 🟡 Yellow (90-110%): Near capacity
  - 🔴 Red (>110%): Overcrowded with pulse animation
- **Clinical Context:** >100% indicates overcrowding and potential extended waits

### 📊 Analytics & Benchmarking
- **Peer Benchmarking:** Hospital performance vs regional/provincial averages
- **Temporal Patterns:** Hour-of-day, day-of-week, monthly trend analysis
- **Regional Intelligence:** 15 health regions mapped with analytics segmentation
- **System Trends:** Province-wide performance tracking with 90d/6m/1y views

### 🗺️ Interactive Map
- **Mapbox Integration:** Geographic visualization of all hospitals
- **Live Data Indicators:** Real-time updates highlighted
- **Distance Calculation:** User location-based sorting
- **Cluster Markers:** Efficient rendering of 380+ locations

### 📤 Data Export
- **Citation-Ready:** CSV/JSON export with methodology metadata
- **Granularity Control:** Raw measurements, hourly, daily, weekly, or monthly aggregates
- **Research-Grade:** Full audit trail with payload hashing and parser versioning

### 🔍 Access & Equity Insights
- **Access Burden Estimator:** Fuel + parking cost calculations for patient decision-making
- **Provincial Gas Price Awareness:** ON $1.55/L, QC $1.60/L, BC $1.75/L
- **Distance-Based Analysis:** Nearest hospital identification within radius
- **Equity Layer Scaffold:** Foundation for census tract income overlays (future)

---

## 🏗️ Technical Architecture

```mermaid
graph TD
    subgraph "Provincial Sources"
        QC[Quebec MSSS<br/>BeautifulSoup]
        ON[Ontario Health<br/>HTTP + HTML tables]
        AB[Alberta AHS<br/>Playwright]
        BC[BC PHSA<br/>JSON/__NEXT_DATA__]
    end

    subgraph "Scheduled Collection"
        CRON[Provincial Scrapers]
        HB[Freshness Checks]
    end

    subgraph "PostgreSQL Database"
        SOURCES[(sources)]
        HOSPITALS[(hospitals)]
        MEASUREMENTS[(measurements)]
        AGGREGATES[(measurement_aggregates)]
        QUALITY[(data_quality_snapshots)]
        STATUS[(scraper_status)]
    end

    subgraph "Next.js 14 Frontend"
        API[API Routes<br/>/api/hospitals<br/>/api/analytics<br/>/api/data-quality]
        PAGES[Pages<br/>Map View<br/>Analytics Dashboard<br/>Methods Page<br/>Resources]
        MAP[Mapbox GL JS<br/>380+ Hospital Markers]
    end

    subgraph "Services"
        DB_SVC[DatabaseService]
        AGG_SVC[AggregationService]
        DQ_SVC[DataQualityService]
        ANOM_SVC[AnomalyDetectionService]
    end

    QC --> CRON
    ON --> CRON
    AB --> CRON
    BC --> CRON

    CRON --> DB_SVC
    DB_SVC --> MEASUREMENTS
    DB_SVC --> STATUS

    HB --> STATUS
    HB -->|State changes| DQ_SVC

    MEASUREMENTS --> AGG_SVC
    AGG_SVC --> AGGREGATES

    MEASUREMENTS --> ANOM_SVC
    ANOM_SVC --> DQ_SVC
    DQ_SVC --> QUALITY

    SOURCES -.-> API
    HOSPITALS -.-> API
    MEASUREMENTS -.-> API
    AGGREGATES -.-> API
    QUALITY -.-> API

    API --> PAGES
    PAGES --> MAP

    style QC fill:#4A90E2
    style ON fill:#4A90E2
    style AB fill:#4A90E2
    style BC fill:#4A90E2
    style CRON fill:#F5A623
    style HB fill:#F5A623
    style MAP fill:#50E3C2
```

### Backend
- **Language:** Python 3.12+
- **Testing:** pytest with broad unit coverage plus database-backed integration tests; some backend integration and smoke checks require `DATABASE_URL`, and the local pipeline smoke path also expects a frontend server on `localhost:3000`
- **Scrapers:** 4 provincial scrapers (BeautifulSoup, HTTP/HTML parsing, Playwright, JSON extraction)
- **Database:** PostgreSQL with 15 tables, including the public-health-hub source/resource/alert/system-context lane
- **Services:**
  - DatabaseService, AggregationService, DataQualityService
  - AnomalyDetectionService, MethodologyChangeDetector
  - GeocodingService (Nominatim), HeartbeatService
- **CLI Tools:** Scraper runner, database cleanup, storage stats, seeding, aggregation, region mapping

### Frontend
- **Framework:** Next.js 14 App Router + TypeScript
- **Testing:** Vitest + React Testing Library for unit/component coverage, with Playwright browser verification kept CI-first, manual-dispatch, and outside the default push/PR merge gate
- **Mapping:** Mapbox GL JS
- **Components:** 30+ React components with targeted coverage across major user-facing flows
- **API Routes:** Hospitals/comparisons, analytics, data quality, and public resources endpoints
- **Pages:** Home (map + list), /data-quality, /analytics, /methods, /resources, /about

### Database Schema (15 Tables)
- `sources` - Provincial data source metadata
- `hospitals` - Facility metadata with verification workflow
- `measurements` - Audit log with ontology tags (payload hashing, not full HTML)
- `scraper_status` - Scraper freshness state
- `scraper_alert_state` - Stateful source-health tracking and recovery suppression
- `measurement_aggregates` - Permanent statistical summaries (hourly/daily/weekly/monthly)
- `data_quality_snapshots` - Daily scraper reliability metrics
- `methodology_change_events` - Detected methodology shifts
- `regions` - Province region metadata for analytics
- `hospital_regions` - Hospital-to-region mappings
- `public_data_sources` - Public-health-hub source catalog and freshness metadata
- `resource_locations` - Normalized facilities and AED locations for `/resources`
- `public_health_alerts` - Health Canada recall and safety alert records
- `public_health_system_metrics` - Ontario EMS system-context records for analytics-only `/resources` context cards
- `public_health_source_alert_state` - Stateful public-health ingest status tracking

### Automation
- **Scheduled Workflows:** Scrapers, freshness checks, quality snapshots, and bounded retention cleanup
- **Playwright Browsers:** Automated for Alberta and browser-based verification flows
- **Health Tracking:** Source status is reconciled through state-change-aware checks
- **Cache Guardrails:** Shared anonymous read-heavy routes use short cache windows; user-specific and export routes use `no-store`

---

## Project Impact

Wait Time Canada demonstrates public-interest software development, health-systems thinking, documentation, and responsible handling of health-adjacent information.

The project is designed to:

- make provincial wait-time methodology differences visible instead of masking them through unsafe normalization
- preserve provenance and source semantics for every measurement
- help users understand when direct hospital or province comparisons are invalid
- support research, journalism, policy analysis, and public understanding with transparent caveats
- provide public-health resource discovery while clearly labeling source freshness, scope, and limitations

This is a non-clinical observatory. It does not provide medical advice, diagnose conditions, recommend care sites, or replace emergency services.

---

## 🚀 Quick Start (Local Development)

This section is for reproducible local development. Production deployment
details and environment-specific operations notes are intentionally excluded
from public documentation.

### Prerequisites

- Python 3.12+
- Node.js 22+
- PostgreSQL
- Mapbox account (free tier sufficient)

### Recommended Database Path: PostgreSQL

Wait Time Canada uses standard PostgreSQL and can be run against any compatible
database:

1. create or provision a PostgreSQL database
2. copy the connection string
3. export it into your shell before running backend commands
4. run the repo migrations and analytics bootstrap commands below

This keeps local setup portable while preserving a reproducible schema and
migration workflow.

### 1. Clone and Setup Environment

```bash
git clone https://github.com/yourusername/waittimecanada.git
cd waittimecanada

# Frontend environment
cp frontend/.env.example frontend/.env.local
# Edit frontend/.env.local with NEXT_PUBLIC_MAPBOX_TOKEN

# Backend runtime config
export DATABASE_URL="postgresql://user:pass@host:5432/dbname" # pragma: allowlist secret
```

`backend/.env.local` can still be kept as a human convenience template, but the
backend runtime expects `DATABASE_URL` to already be present in the process
environment.

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e '.[dev]'  # Note: use quotes in zsh

# Install Playwright browsers (required for Alberta scraper)
playwright install chromium

# Apply database migrations
python run_migrations.py

# Seed sources and bootstrap analytics
python -m waittime.cli.bootstrap_analytics --days 180
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Open `http://localhost:3000` to view the app.

### 4. Run Scrapers (Optional)

```bash
cd backend
source .venv/bin/activate

# Run all scrapers
python -m waittime.cli.scraper --all

# Or run single province
python -m waittime.cli.scraper --source quebec-msss
```

---

## 📚 Common Commands

### Backend

```bash
source .venv/bin/activate

# Scrapers
python -m waittime.cli.scraper --all              # Run all scrapers
python -m waittime.cli.scraper --source ontario-health  # Single province
python -m waittime.cli.scraper --dry-run --all    # Test without DB writes

# Maintenance
python -m waittime.cli.check_heartbeat            # Verify scraper health
python -m waittime.cli.aggregate --backfill       # Regenerate aggregates
python -m waittime.cli.cleanup --dry-run          # Preview cleanup
python -m waittime.cli.storage_stats              # Inspect measurements table growth

# Testing
pytest tests/unit                                  # Unit tests only
pytest tests/integration                           # Integration tests (requires DATABASE_URL)
pytest tests/ -v --cov=waittime                   # Full suite with coverage; backend smoke tests may skip without DATABASE_URL and a local frontend server
```

### Frontend

```bash
cd frontend

# Development
npm run dev          # Start dev server
npm run build        # Production build
npm run start        # Run production build

# Quality
npm run type-check   # TypeScript validation
npm run lint         # ESLint checks
npm run test:unit    # Vitest unit tests
```

---

## 📖 Documentation

### Essential Reading
- [`docs/planning/roadmap.md`](docs/planning/roadmap.md) - **Active roadmap and milestone status**
- [`AGENTS.md`](AGENTS.md) - repository agent instructions and project architecture

### Deep Dives
- [`docs/adr/`](docs/adr/) - Architecture Decision Records (16 ADRs)
- [`backend/docs/methodologies/`](backend/docs/methodologies/) - Provincial methodology documentation
- [`docs/case-studies/ottawa-gatineau-divergence.md`](docs/case-studies/ottawa-gatineau-divergence.md) - Cross-border methodology divergence case study
- [`backend/README.md`](backend/README.md) - Backend architecture and testing
- [`frontend/README.md`](frontend/README.md) - Frontend architecture and testing

### API Reference
- [`docs/API.md`](docs/API.md) - API contracts and examples
- [`docs/reference/data-dictionary.md`](docs/reference/data-dictionary.md) - **Data Dictionary & Schema**
- [`docs/architecture/data-flow.md`](docs/architecture/data-flow.md) - **Data Flow Architecture**
- Endpoints: `/api/hospitals`, `/api/comparisons`, `/api/analytics/*`, `/api/data-quality`

---

## 🔧 Repository Structure

```
waittimecanada/
├── backend/
│   ├── src/waittime/
│   │   ├── scrapers/          # Provincial scrapers (QC, ON, AB, BC)
│   │   ├── services/          # Business logic services
│   │   ├── core/              # Models, enums, ontology
│   │   └── cli/               # Command-line tools
│   ├── tests/                 # 375+ tests (unit + integration)
│   │                          # plus an opt-in local smoke/E2E path
│   ├── migrations/            # Database schema migrations
│   ├── seed_data/             # Hospital/region seed data
│   └── docs/                  # Backend-specific documentation
├── frontend/
│   ├── app/                   # Next.js 14 App Router
│   │   ├── api/               # API routes
│   │   ├── data-quality/      # Data quality dashboard
│   │   ├── analytics/         # Analytics dashboard
│   │   └── methods/           # Methodology documentation page
│   ├── components/            # React components
│   ├── tests/                 # 287 frontend tests
│   └── utils/                 # Utilities (cache, distance, date)
├── docs/
│   ├── planning/              # Roadmap, strategic plans
│   ├── operations/            # Operational guides
│   ├── adr/                   # Architecture decisions
│   ├── methodologies/         # Provincial methodology docs
│   └── architecture/          # System architecture
└── .github/workflows/         # CI/CD automation (10 workflows)
```

---

## 🎯 Operational Workflows

### Production Automation
- **Scraper Runs:** Scheduled collection from public provincial sources
- **Freshness Checks:** Source health is tracked from scraper status records
- **Database Cleanup:** Manual cleanup keeps a 30-day raw-measurement window; the GitHub Actions maintenance path uses bounded batched deletes and reports storage growth

### CI/CD Pipelines
- **Frontend CI:** Type checking, linting, unit tests
- **Scraper CI:** Python tests, coverage reporting
- **Production Readiness:** Pre-deployment validation
- **Docs CI:** Documentation quality checks

### Deployment Configuration

Public documentation covers reproducible local development, architecture, and
data methodology. Production deployment details, monitoring configuration, and
environment-specific paths are kept outside public documentation.

---

## 🛡️ Project Guardrails

### Clinical Safety
- ✅ Never provide medical advice or triage recommendations
- ✅ Always include emergency disclaimer: "Call 911 for emergencies"
- ✅ Display telehealth routing (811 varies by province)

### Data Integrity
- ✅ Preserve source semantics - never normalize incompatible metrics
- ✅ Surface divergence warnings when comparisons are invalid
- ✅ Hash payloads (SHA256) instead of storing full HTML
- ✅ Tag every measurement with complete ontology metadata

### Verification & Quality
- ✅ Government health authority sources are trusted and auto-approved
- ✅ Quality enforced via anomaly detection and data quality monitoring
- ✅ Heartbeat monitoring ensures data freshness
- ✅ Methodology change detection tracks reporting shifts

### Attribution
- ✅ Link back to official provincial sources
- ✅ Display data provenance in all visualizations
- ✅ Citation-ready export formats
- ✅ Never claim work from automated tools as human authorship

---

## 📊 Current Status (as of 2026-04-23)

### Milestones Completed
- ✅ M1-M4: Database foundation, Ontario/Quebec scrapers, methodology warnings, PWA setup
- ✅ M7-M8: UX polish, SEO, landing page optimization
- ✅ M9: Public launch foundations (About section, testimonial governance)
- ✅ M10-M11: Multi-province expansion, Access Burden Estimator
- ✅ M12: Research infrastructure (citation export, Dead Man's Switch alerts)
- ✅ M13: Aggregation pipeline (hourly/daily/weekly/monthly)
- ✅ M14: Data quality & anomaly detection (3 new DB tables)
- ✅ M15: Analytics & benchmarking (peer comparison, temporal patterns)
- ✅ M16: Multi-province operationalization (4 provinces, 380+ hospitals, region mapping)
- ✅ M17: Quebec occupancy implementation (scraper + API)
- ✅ M18: Occupancy frontend UI (visual indicators on hospital cards)
- ✅ M28: Ontario real-data equity layer (StatsCan tract integration)
- ✅ M29: Ontario equity academic rigor hardening (uncertainty + interpretation limits)
- ✅ M30-M33: Reliability hardening, divergence briefs, deployment readiness, and historical occupancy trends
- ✅ Operations: Production verification and comprehensive documentation
- ✅ Operations: CI coverage artifacts retained for both frontend and backend verification

### Validation Posture
- **Backend:** broad unit coverage, plus opt-in database-backed integration and
  local pipeline smoke checks when `DATABASE_URL` and a local frontend server
  are available
- **Frontend:** Vitest unit/component coverage is part of the normal workflow,
  while Playwright browser verification stays CI-first and manual-dispatch to
  conserve GitHub free-tier minutes
- **Current source of truth:** see `docs/planning/roadmap.md` for the active
  validation and deployment posture instead of relying on a fixed test-count
  snapshot here

### Data Freshness
- **Update Frequency:** Scheduled source refreshes
- **Freshness Thresholds:** Source-health checks flag stale or failed updates
- **Current Status:** See the public status and data-quality pages for current source state

---

## 💡 Future Roadmap

### Planned Enhancements
- [ ] Additional provinces (Nova Scotia, New Brunswick)
- [ ] Multi-province equity layer beyond Ontario
- [ ] Public research artifacts, including case studies and quantified methodology findings
- [ ] Privacy-safe usage analytics where compatible with the project privacy posture
- [ ] Smart scheduling (reduce frequency during overnight hours)
- [ ] Occupancy-based system-pressure indicators

### Deferred / Research
- [ ] Manitoba scraper (data source unclear)
- [ ] Saskatchewan scraper (no public data available)
- [ ] Territories expansion (limited data availability)

See [`docs/planning/roadmap.md`](docs/planning/roadmap.md) for detailed status and next steps.

---

## 🤝 Contributing

Contributions are welcome! Please see:

- [`CONTRIBUTING.md`](CONTRIBUTING.md) - Development workflow and guidelines
- [`CHANGELOG.md`](CHANGELOG.md) - Project history and versioning
- [`CITATION.cff`](CITATION.cff) - How to cite this project

Use GitHub issue templates for feature requests and data quality reports.

---

## 📄 License

MIT License - See [`LICENSE`](LICENSE) for details.

**Data Sources:**
- Quebec: Ministère de la Santé et des Services sociaux (MSSS)
- Ontario: Health Ontario
- Alberta: Alberta Health Services (AHS)
- British Columbia: Provincial Health Services Authority (PHSA)

All data sourced from publicly available provincial health authority websites.

---

## 🎯 Mission

Wait Time Canada is a public health data and methods observatory focused on transparent interpretation of Canadian emergency department reporting.

The project exists to improve access to operational health-system information, make methodological differences visible, and support safer interpretation of reported wait-time data by patients, clinicians, researchers, journalists, and policy users.

## ⚖️ Equity and Access

Wait Time Canada is developed with a health equity, EDIA, and barrier-reduction lens. Public health information is often fragmented, inconsistently defined, difficult to compare, or difficult to find. Those gaps can create barriers for people navigating care, for communities experiencing unequal access, and for decision-makers trying to improve the system responsibly.

The project aims to reduce those barriers by improving transparency, surfacing limitations, documenting methodological differences, and prioritizing public-interest access to operational health-system information.

## 🛡️ Stewardship

Wait Time Canada prioritizes provenance, comparability, limitations, and responsible reuse of public data. It does not provide medical advice, does not claim to resolve underlying reporting inconsistencies, and does not present invalid cross-system comparisons as if they were directly comparable.

**Contact:** Use the repository issue tracker or the repository owner's GitHub profile for project inquiries.

---

## 📞 Emergency Disclaimer

**⚠️ This is a data observatory tool, not a triage service.**

- **For medical emergencies:** Call **911** immediately
- **For health advice:** Call your provincial health line (**811** in most provinces)
- **Never delay emergency care** based on wait time estimates

Wait time data is for informational purposes only. Clinical decisions should always prioritize patient safety over convenience.
