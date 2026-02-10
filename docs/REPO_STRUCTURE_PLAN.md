# Repository Structure Modernization Plan

> [!WARNING]
> Historical planning snapshot. This file is preserved for context and may reference superseded tooling or paths.
> Use `docs/planning/roadmap.md` and `docs/development/documentation-guidelines.md` as current source of truth.

**Goal:** Transform the WaitTime Canada repository into a best-practice exemplar with:
- MkDocs Material for beautiful, searchable documentation
- Architecture Decision Records (ADRs) for design choices
- Well-organized tests with clear conventions
- Modern project structure that scales
- Developer experience automation

---

## Table of Contents

1. [Target Repository Structure](#target-repository-structure)
2. [MkDocs Material Setup](#mkdocs-material-setup)
3. [Architecture Decision Records](#architecture-decision-records)
4. [Test Organization](#test-organization)
5. [Planning & Documentation](#planning--documentation)
6. [Developer Experience](#developer-experience)
7. [Implementation Roadmap](#implementation-roadmap)

---

## Target Repository Structure

### Complete Directory Layout

```
waittime-canada/
├── .github/                          # GitHub-specific configuration
│   ├── ISSUE_TEMPLATE/               # Issue templates
│   │   ├── bug_report.yml
│   │   ├── feature_request.yml
│   │   └── documentation.yml
│   ├── PULL_REQUEST_TEMPLATE.md      # PR template
│   ├── workflows/                    # CI/CD workflows
│   │   ├── ci-backend.yml            # Renamed from scraper-ci.yml
│   │   ├── ci-frontend.yml
│   │   ├── ci-docs.yml               # Documentation builds
│   │   ├── deploy-backend.yml        # Renamed from scraper-cron.yml
│   │   ├── deploy-docs.yml           # Deploy to GitHub Pages
│   │   └── quality.yml               # Code quality checks
│   └── dependabot.yml                # Automated dependency updates
│
├── docs/                             # MkDocs documentation source
│   ├── index.md                      # Landing page
│   ├── getting-started/              # User-facing guides
│   │   ├── index.md
│   │   ├── quick-start.md
│   │   ├── installation.md
│   │   └── first-scraper.md
│   ├── architecture/                 # System design
│   │   ├── index.md
│   │   ├── overview.md               # High-level architecture
│   │   ├── data-ontology.md          # Metric ontology deep dive
│   │   ├── database.md               # Current DATABASE.md content
│   │   ├── api.md                    # Current API.md content
│   │   └── scrapers.md               # Scraper architecture
│   ├── development/                  # Developer guides
│   │   ├── index.md
│   │   ├── setup.md                  # Current IMPLEMENTATION.md content
│   │   ├── testing.md                # Testing strategy
│   │   ├── code-style.md             # Linting, formatting standards
│   │   ├── contributing.md           # How to contribute
│   │   └── debugging.md              # Common issues & solutions
│   ├── deployment/                   # Operations
│   │   ├── index.md
│   │   ├── ci-cd.md                  # GitHub Actions workflows
│   │   ├── monitoring.md             # Sentry, heartbeat, alerts
│   │   └── scaling.md                # Future scaling considerations
│   ├── reference/                    # API reference
│   │   ├── api/                      # Auto-generated API docs
│   │   ├── database-schema.md        # Complete schema reference
│   │   └── environment-variables.md  # All env vars documented
│   ├── adr/                          # Architecture Decision Records
│   │   ├── 0001-use-supabase.md
│   │   ├── 0002-metric-ontology.md
│   │   ├── 0003-serverless-scrapers.md
│   │   └── template.md
│   ├── planning/                     # Project planning docs
│   │   ├── roadmap.md                # Current ROADMAP.md
│   │   ├── strategic-plan.md         # Current er-times-plan.md
│   │   └── retrospectives/           # Post-sprint learnings
│   ├── guides/                       # How-to guides
│   │   ├── adding-province.md        # How to add new province scraper
│   │   ├── database-migrations.md    # Migration best practices
│   │   └── troubleshooting.md        # Common problems
│   └── assets/                       # Documentation assets
│       ├── images/
│       ├── diagrams/                 # Architecture diagrams (Mermaid, draw.io)
│       └── screenshots/
│
├── backend/                          # Renamed from scrapers/
│   ├── pyproject.toml
│   ├── setup.py                      # For editable installs
│   ├── README.md                     # Backend-specific README
│   ├── src/
│   │   ├── waittime/                 # Proper package name
│   │   │   ├── __init__.py
│   │   │   ├── __main__.py           # Entry point: python -m waittime
│   │   │   ├── core/                 # Shared utilities
│   │   │   │   ├── __init__.py
│   │   │   │   ├── database.py
│   │   │   │   ├── models.py         # Pydantic models
│   │   │   │   ├── config.py         # Settings (pydantic-settings)
│   │   │   │   ├── logging.py        # Logging setup
│   │   │   │   └── exceptions.py     # Custom exceptions
│   │   │   ├── scrapers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── quebec.py
│   │   │   │   ├── alberta.py
│   │   │   │   ├── ontario.py
│   │   │   │   └── registry.py       # Scraper registration
│   │   │   ├── services/             # Business logic
│   │   │   │   ├── __init__.py
│   │   │   │   ├── heartbeat.py
│   │   │   │   └── comparability.py  # Auto-researcher logic
│   │   │   └── cli/                  # CLI commands
│   │   │       ├── __init__.py
│   │   │       ├── scrape.py         # Scraping commands
│   │   │       ├── verify.py         # Verification commands
│   │   │       └── migrate.py        # Migration commands
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # Pytest fixtures
│   │   ├── unit/                     # Unit tests (fast, no I/O)
│   │   │   ├── __init__.py
│   │   │   ├── test_models.py
│   │   │   ├── test_comparability.py
│   │   │   └── scrapers/
│   │   │       ├── test_base.py
│   │   │       └── test_quebec.py
│   │   ├── integration/              # Integration tests (database, HTTP)
│   │   │   ├── __init__.py
│   │   │   ├── test_database.py
│   │   │   ├── test_scrapers_live.py
│   │   │   └── test_heartbeat.py
│   │   ├── e2e/                      # End-to-end tests
│   │   │   ├── __init__.py
│   │   │   └── test_full_scrape.py
│   │   └── fixtures/                 # Test data
│   │       ├── html/                 # Mock HTML responses
│   │       │   ├── quebec_sample.html
│   │       │   └── alberta_sample.html
│   │       └── data/                 # JSON fixtures
│   ├── migrations/                   # Database migrations (moved here)
│   │   ├── README.md
│   │   └── versions/
│   │       ├── 001_initial_schema.sql
│   │       ├── 002_add_heartbeat.sql
│   │       └── 003_add_indexes.sql
│   └── scripts/                      # Utility scripts
│       ├── seed_database.py
│       ├── generate_test_data.py
│       └── check_data_quality.py
│
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vitest.config.ts
│   ├── playwright.config.ts
│   ├── README.md                     # Frontend-specific README
│   ├── public/
│   │   ├── favicon.ico
│   │   └── images/
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── methods/
│   │   │   ├── about/
│   │   │   └── api/                  # API routes (if needed)
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # Reusable UI primitives
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Card.tsx
│   │   │   │   └── Modal.tsx
│   │   │   ├── map/                  # Map-specific components
│   │   │   │   ├── Map.tsx
│   │   │   │   ├── HospitalMarker.tsx
│   │   │   │   └── ClusterMarker.tsx
│   │   │   ├── hospital/             # Hospital-specific components
│   │   │   │   ├── HospitalCard.tsx
│   │   │   │   ├── WaitTimeChart.tsx
│   │   │   │   └── ProvinceAwareBanner.tsx
│   │   │   └── layout/               # Layout components
│   │   │       ├── Header.tsx
│   │   │       ├── Footer.tsx
│   │   │       └── HeartbeatMonitor.tsx
│   │   ├── lib/                      # Utilities
│   │   │   ├── supabase.ts
│   │   │   ├── api.ts
│   │   │   ├── comparability.ts
│   │   │   └── utils.ts
│   │   ├── hooks/                    # Custom React hooks
│   │   │   ├── useHospitals.ts
│   │   │   ├── useMeasurements.ts
│   │   │   └── useHeartbeat.ts
│   │   ├── types/                    # TypeScript types
│   │   │   ├── index.ts
│   │   │   └── database.ts           # Supabase-generated types
│   │   ├── config/                   # Configuration
│   │   │   └── constants.ts
│   │   └── styles/
│   │       └── globals.css
│   └── tests/
│       ├── unit/                     # Component tests (Vitest + RTL)
│       │   ├── components/
│       │   └── lib/
│       ├── e2e/                      # End-to-end tests (Playwright)
│       │   ├── map.spec.ts
│       │   ├── hospital-details.spec.ts
│       │   └── methods.spec.ts
│       └── setup.ts
│
├── infrastructure/                   # Infrastructure as Code (future)
│   ├── terraform/                    # If scaling beyond Supabase/Vercel
│   └── docker/                       # Docker configs for local dev
│       ├── docker-compose.yml
│       └── Dockerfile.backend
│
├── scripts/                          # Project-wide scripts
│   ├── setup.sh                      # Initial project setup
│   ├── test-all.sh                   # Run all tests
│   ├── generate-types.sh             # Generate TypeScript types from DB
│   └── validate-docs.sh              # Ensure docs build successfully
│
├── .vscode/                          # VS Code workspace settings
│   ├── settings.json                 # Editor settings
│   ├── extensions.json               # Recommended extensions
│   └── launch.json                   # Debug configurations
│
├── .cursorrules                      # Cursor IDE rules (optional)
├── .editorconfig                     # Editor configuration
├── .gitattributes                    # Git attributes
├── .gitignore
├── .pre-commit-config.yaml           # Pre-commit hooks
├── LICENSE
├── README.md                         # Main project README
├── CONTRIBUTING.md                   # Contribution guidelines
├── CHANGELOG.md                      # Keep a changelog
├── CODE_OF_CONDUCT.md                # Code of conduct
├── SECURITY.md                       # Security policy
├── mkdocs.yml                        # MkDocs configuration
└── package.json                      # Root package.json for workspaces (optional)
```

---

## MkDocs Material Setup

### Installation & Configuration

**Install MkDocs Material:**
```bash
pip install mkdocs-material
pip install mkdocs-git-revision-date-localized-plugin
pip install mkdocs-minify-plugin
pip install mkdocs-mermaid2-plugin
pip install mkdocs-macros-plugin
```

### Complete `mkdocs.yml` Configuration

```yaml
# mkdocs.yml
site_name: WaitTime Canada
site_url: https://waittime-canada.github.io/docs
site_description: A clinically defensible Health Systems Observatory for Canadian ER wait times
site_author: Your Name
repo_url: https://github.com/YOUR_USERNAME/waittime-canada
repo_name: waittime-canada
edit_uri: edit/main/docs/

theme:
  name: material
  custom_dir: docs/overrides  # For custom templates

  palette:
    # Light mode
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: red
      accent: blue
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode

    # Dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: red
      accent: blue
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

  font:
    text: Roboto
    code: Roboto Mono

  icon:
    repo: fontawesome/brands/github
    admonition:
      note: octicons/tag-16
      abstract: octicons/checklist-16
      info: octicons/info-16
      tip: octicons/squirrel-16
      success: octicons/check-16
      question: octicons/question-16
      warning: octicons/alert-16
      failure: octicons/x-circle-16
      danger: octicons/zap-16
      bug: octicons/bug-16
      example: octicons/beaker-16
      quote: octicons/quote-16

  features:
    - navigation.instant        # Fast page loads (SPA-like)
    - navigation.tracking       # URL updates with scroll
    - navigation.tabs           # Top-level tabs
    - navigation.tabs.sticky    # Tabs stay visible on scroll
    - navigation.sections       # Sections in sidebar
    - navigation.expand         # Expand all sections by default
    - navigation.path           # Breadcrumbs
    - navigation.indexes        # Section index pages
    - toc.follow                # ToC follows scroll
    - toc.integrate             # ToC integrated into sidebar
    - navigation.top            # Back to top button
    - search.suggest            # Search suggestions
    - search.highlight          # Highlight search terms
    - search.share              # Share search results
    - header.autohide           # Auto-hide header on scroll
    - content.code.copy         # Copy code button
    - content.code.annotate     # Code annotations
    - content.tabs.link         # Link content tabs

plugins:
  - search:
      lang: en
      separator: '[\s\-,:!=\[\]()"/]+|(?!\b)(?=[A-Z][a-z])|\.(?!\d)|&[lg]t;'

  - git-revision-date-localized:
      enable_creation_date: true
      type: timeago

  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
      htmlmin_opts:
        remove_comments: true

  - mermaid2:
      version: 10.6.1

  - macros:
      module_name: docs/macros

  # Future: Generate API docs from code
  # - mkdocstrings:
  #     handlers:
  #       python:
  #         options:
  #           show_source: true

markdown_extensions:
  # Python Markdown
  - abbr
  - admonition
  - attr_list
  - def_list
  - footnotes
  - md_in_html
  - toc:
      permalink: true
      toc_depth: 3

  # Python Markdown Extensions
  - pymdownx.arithmatex:
      generic: true
  - pymdownx.betterem:
      smart_enable: all
  - pymdownx.caret
  - pymdownx.details
  - pymdownx.emoji:
      emoji_index: !!python/name:material.extensions.emoji.twemoji
      emoji_generator: !!python/name:material.extensions.emoji.to_svg
  - pymdownx.highlight:
      anchor_linenums: true
      line_spans: __span
      pygments_lang_class: true
  - pymdownx.inlinehilite
  - pymdownx.keys
  - pymdownx.mark
  - pymdownx.smartsymbols
  - pymdownx.snippets:
      check_paths: true
  - pymdownx.superfences:
      custom_fences:
        - name: mermaid
          class: mermaid
          format: !!python/name:mermaid2.fence_mermaid
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.tasklist:
      custom_checkbox: true
  - pymdownx.tilde

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/YOUR_USERNAME
    - icon: fontawesome/brands/linkedin
      link: https://linkedin.com/in/YOUR_PROFILE

  analytics:
    provider: google
    property: G-XXXXXXXXXX  # Optional

  version:
    provider: mike  # Versioned docs (future)

extra_css:
  - assets/stylesheets/extra.css

extra_javascript:
  - assets/javascripts/extra.js

nav:
  - Home: index.md

  - Getting Started:
    - getting-started/index.md
    - Quick Start: getting-started/quick-start.md
    - Installation: getting-started/installation.md
    - First Scraper: getting-started/first-scraper.md

  - Architecture:
    - architecture/index.md
    - Overview: architecture/overview.md
    - Data Ontology: architecture/data-ontology.md
    - Database: architecture/database.md
    - API: architecture/api.md
    - Scrapers: architecture/scrapers.md

  - Development:
    - development/index.md
    - Environment Setup: development/setup.md
    - Testing: development/testing.md
    - Code Style: development/code-style.md
    - Contributing: development/contributing.md
    - Debugging: development/debugging.md

  - Deployment:
    - deployment/index.md
    - CI/CD: deployment/ci-cd.md
    - Monitoring: deployment/monitoring.md
    - Scaling: deployment/scaling.md

  - Reference:
    - Database Schema: reference/database-schema.md
    - Environment Variables: reference/environment-variables.md

  - ADRs:
    - adr/index.md
    - "0001: Use Supabase": adr/0001-use-supabase.md
    - "0002: Metric Ontology": adr/0002-metric-ontology.md
    - "0003: Serverless Scrapers": adr/0003-serverless-scrapers.md

  - Planning:
    - Roadmap: planning/roadmap.md
    - Strategic Plan: planning/strategic-plan.md

  - Guides:
    - Adding a Province: guides/adding-province.md
    - Database Migrations: guides/database-migrations.md
    - Troubleshooting: guides/troubleshooting.md

copyright: Copyright &copy; 2024-2026 Your Name
```

### Documentation Commands

**Local Development:**
```bash
# Serve docs locally with live reload
mkdocs serve

# Open http://127.0.0.1:8000
```

**Build Static Site:**
```bash
# Build static HTML
mkdocs build

# Output to site/ directory
```

**Deploy to GitHub Pages:**
```bash
# Deploy docs to gh-pages branch
mkdocs gh-deploy

# Or use GitHub Actions (recommended)
```

---

## Architecture Decision Records

### ADR Template

Create `docs/adr/template.md`:

```markdown
# [Number]. [Title]

Date: YYYY-MM-DD
Status: [Proposed | Accepted | Deprecated | Superseded]
Deciders: [Names]
Technical Story: [Ticket/Issue URL]

## Context and Problem Statement

[Describe the context and problem statement, e.g., in free form using two to three sentences. You may want to articulate the problem in form of a question.]

## Decision Drivers

* [Driver 1, e.g., a force, facing concern, ...]
* [Driver 2, e.g., a force, facing concern, ...]
* [...]

## Considered Options

* [Option 1]
* [Option 2]
* [Option 3]
* [...]

## Decision Outcome

Chosen option: "[Option 1]", because [justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force force | ... | comes out best (see below)].

### Positive Consequences

* [e.g., improvement of quality attribute satisfaction, follow-up decisions required, ...]
* [...]

### Negative Consequences

* [e.g., compromising quality attribute, follow-up decisions required, ...]
* [...]

## Pros and Cons of the Options

### [Option 1]

[Example | description | pointer to more information | ...]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* [...]

### [Option 2]

[Example | description | pointer to more information | ...]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* [...]

### [Option 3]

[Example | description | pointer to more information | ...]

* Good, because [argument a]
* Good, because [argument b]
* Bad, because [argument c]
* [...]

## Links

* [Link type] [Link to ADR] <!-- example: Refined by [ADR-0005](0005-example.md) -->
* [Link type] [Link to ADR] <!-- example: Supersedes [ADR-0001](0001-example.md) -->
* [...]
```

### Example ADR: Supabase

Create `docs/adr/0001-use-supabase.md`:

```markdown
# 1. Use Supabase for Backend Database

Date: 2024-12-26
Status: Accepted
Deciders: Project Team
Technical Story: Evaluating database options for MVP

## Context and Problem Statement

We need a PostgreSQL database with:
- Row-Level Security for public read-only access
- Real-time subscriptions for heartbeat monitoring
- Geospatial queries (PostGIS)
- Low operational overhead for MVP
- Free tier sufficient for initial launch

Should we use managed Supabase, self-hosted PostgreSQL, or alternative like PlanetScale?

## Decision Drivers

* Time to market (4-week sprint)
* Cost (free tier for MVP)
* Developer experience (minimal setup)
* Feature requirements (RLS, PostGIS, real-time)
* Scaling path (can upgrade to paid tier)

## Considered Options

* Supabase (managed PostgreSQL)
* Self-hosted PostgreSQL on DigitalOcean
* PlanetScale (managed MySQL)
* Firebase (NoSQL)

## Decision Outcome

Chosen option: "Supabase", because:
- Provides all required PostgreSQL features (RLS, PostGIS, enums)
- Generous free tier (500MB database, 2GB bandwidth)
- Built-in authentication and real-time (future features)
- Auto-generated REST API and TypeScript types
- Excellent developer experience (GUI, CLI, local dev)
- Can self-host later if needed

### Positive Consequences

* Rapid development (database + API in one platform)
* Type-safe frontend (auto-generated TypeScript types)
* Row-Level Security enforced at database level
* Real-time subscriptions for heartbeat UI
* PostGIS support for geospatial queries

### Negative Consequences

* Vendor lock-in (mitigated by standard PostgreSQL)
* Free tier limitations (500MB database, 2GB bandwidth/month)
* Must upgrade to Pro ($25/month) if traffic grows
* Requires internet connection for development (unless using local Supabase)

## Pros and Cons of the Options

### Supabase

* Good, because provides PostgreSQL with all needed extensions
* Good, because generous free tier
* Good, because excellent developer experience
* Good, because can self-host if needed (open source)
* Bad, because vendor lock-in (mitigated by PostgreSQL compatibility)
* Bad, because free tier limits may require upgrade

### Self-hosted PostgreSQL

* Good, because complete control
* Good, because no vendor lock-in
* Good, because predictable costs
* Bad, because requires server management
* Bad, because no built-in REST API
* Bad, because slower development velocity

### PlanetScale

* Good, because excellent scaling story
* Good, because generous free tier
* Bad, because MySQL not PostgreSQL (no enums, different RLS)
* Bad, because no PostGIS support
* Bad, because different migration strategy

### Firebase

* Good, because real-time by default
* Good, because generous free tier
* Bad, because NoSQL (doesn't fit relational data model)
* Bad, because no SQL support for complex queries
* Bad, because different mental model from PostgreSQL

## Links

* Superseded by: None
* Refines: Strategic plan decision to use PostgreSQL
* Related: [ADR-0003](0003-serverless-scrapers.md) - Serverless scrapers integrate with Supabase
```

### ADR Index Page

Create `docs/adr/index.md`:

```markdown
# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for WaitTime Canada.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences.

## Format

We use the [MADR](https://adr.github.io/madr/) (Markdown Any Decision Records) format.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [0001](0001-use-supabase.md) | Use Supabase for Backend Database | Accepted | 2024-12-26 |
| [0002](0002-metric-ontology.md) | Implement Strict Metric Ontology | Accepted | 2024-12-26 |
| [0003](0003-serverless-scrapers.md) | Use GitHub Actions for Serverless Scrapers | Accepted | 2024-12-27 |

## Creating a New ADR

1. Copy `template.md` to a new file with the next sequential number
2. Fill in the template with your decision
3. Submit a pull request
4. Update this index after merge
```

---

## Test Organization

### Backend Test Structure

**`backend/tests/conftest.py`** - Shared fixtures:

```python
"""Pytest configuration and shared fixtures."""
import pytest
from supabase import Client, create_client
from waittime.core.config import Settings
from waittime.core.database import DatabaseClient

@pytest.fixture(scope="session")
def settings() -> Settings:
    """Test settings."""
    return Settings(
        supabase_url="http://localhost:54321",  # Local Supabase
        supabase_key="test-key",
        environment="test"
    )

@pytest.fixture(scope="session")
def supabase_client(settings: Settings) -> Client:
    """Supabase client for integration tests."""
    return create_client(settings.supabase_url, settings.supabase_key)

@pytest.fixture(scope="session")
def db_client(supabase_client: Client) -> DatabaseClient:
    """Database client."""
    return DatabaseClient(supabase_client)

@pytest.fixture
def sample_hospital_data():
    """Sample hospital data for testing."""
    return {
        "id": "test-hospital",
        "name": "Test General Hospital",
        "province": "QC",
        "latitude": 45.5017,
        "longitude": -73.5673,
        "is_verified": True,
        "is_visible": True
    }

@pytest.fixture
def sample_measurement_data():
    """Sample measurement data for testing."""
    return {
        "hospital_id": "test-hospital",
        "value": 120,
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "REGISTRATION",
        "end_event": "PHYSICIAN",
        "statistic_type": "MEAN",
        "raw_payload_hash": "abc123",
        "parser_version": "1.0.0",
        "scraper_id": "test-scraper"
    }
```

**Test Organization by Type:**

```python
# tests/unit/test_comparability.py
"""Unit tests for comparability logic (no I/O)."""
from waittime.services.comparability import are_comparable, generate_divergence_brief

def test_identical_ontologies_are_comparable():
    """Measurements with identical ontology should be comparable."""
    measurement_a = {
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "P90"
    }
    measurement_b = measurement_a.copy()

    assert are_comparable(measurement_a, measurement_b) is True

def test_different_start_events_not_comparable():
    """Measurements with different start events should not be comparable."""
    measurement_a = {"start_event": "TRIAGE", ...}
    measurement_b = {"start_event": "REGISTRATION", ...}

    assert are_comparable(measurement_a, measurement_b) is False

    brief = generate_divergence_brief(measurement_a, measurement_b)
    assert "start_event" in brief
    assert "TRIAGE" in brief
    assert "REGISTRATION" in brief
```

```python
# tests/integration/test_database.py
"""Integration tests with real database."""
import pytest
from waittime.core.models import Measurement

@pytest.mark.integration
def test_insert_measurement(db_client, sample_measurement_data):
    """Can insert measurement into database."""
    measurement = Measurement(**sample_measurement_data)

    result = db_client.insert_measurement(measurement)

    assert result.id is not None
    assert result.hospital_id == sample_measurement_data["hospital_id"]

@pytest.mark.integration
def test_duplicate_measurement_rejected(db_client, sample_measurement_data):
    """Duplicate measurements should be rejected by unique constraint."""
    measurement = Measurement(**sample_measurement_data)

    db_client.insert_measurement(measurement)

    with pytest.raises(Exception):  # Unique constraint violation
        db_client.insert_measurement(measurement)
```

```python
# tests/e2e/test_full_scrape.py
"""End-to-end tests simulating full scrape workflow."""
import pytest
from waittime.scrapers.quebec import QuebecScraper

@pytest.mark.e2e
@pytest.mark.slow
def test_quebec_scraper_full_workflow(db_client):
    """Quebec scraper can fetch, parse, and store real data."""
    scraper = QuebecScraper(db_client)

    # This hits the real Quebec website
    result = scraper.run()

    assert result.hospitals_scraped > 0
    assert result.measurements_created > 0
    assert result.status == "success"

    # Verify data in database
    measurements = db_client.get_recent_measurements(limit=10)
    assert len(measurements) > 0
```

**Pytest Configuration:**

```ini
# backend/pyproject.toml
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, no I/O)",
    "integration: Integration tests (database, HTTP)",
    "e2e: End-to-end tests (full workflows)",
    "slow: Slow-running tests",
]

# Run only unit tests by default
addopts = "-v -m 'not integration and not e2e'"

# Coverage settings
[tool.coverage.run]
source = ["src/waittime"]
omit = ["*/tests/*", "*/migrations/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

### Frontend Test Structure

**Component Test Example:**

```typescript
// frontend/tests/unit/components/ProvinceAwareBanner.test.tsx
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProvinceAwareBanner } from '@/components/hospital/ProvinceAwareBanner';

describe('ProvinceAwareBanner', () => {
  it('shows correct telehealth info for Quebec', () => {
    const source = {
      id: 'ca-qc-msss',
      telehealth_name: 'Info-Santé 811',
      telehealth_phone: '811',
    };

    render(<ProvinceAwareBanner source={source} />);

    expect(screen.getByText(/Info-Santé 811/i)).toBeInTheDocument();
    expect(screen.getByRole('link')).toHaveAttribute('href', 'tel:811');
  });

  it('shows correct telehealth info for Alberta', () => {
    const source = {
      id: 'ca-ab-ahs',
      telehealth_name: 'Health Link 811',
      telehealth_phone: '811',
    };

    render(<ProvinceAwareBanner source={source} />);

    expect(screen.getByText(/Health Link 811/i)).toBeInTheDocument();
  });
});
```

**E2E Test Example:**

```typescript
// frontend/tests/e2e/map.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Hospital Map', () => {
  test('displays hospitals on map', async ({ page }) => {
    await page.goto('/');

    // Wait for map to load
    await expect(page.locator('[data-testid="mapbox-map"]')).toBeVisible();

    // Wait for hospital markers
    await expect(page.locator('[data-testid="hospital-marker"]').first()).toBeVisible();

    // Should have multiple markers
    const markerCount = await page.locator('[data-testid="hospital-marker"]').count();
    expect(markerCount).toBeGreaterThan(0);
  });

  test('clicking hospital shows details', async ({ page }) => {
    await page.goto('/');

    // Click first hospital marker
    await page.locator('[data-testid="hospital-marker"]').first().click();

    // Modal should open
    await expect(page.locator('[data-testid="hospital-modal"]')).toBeVisible();

    // Should show hospital name
    await expect(page.locator('[data-testid="hospital-name"]')).toBeVisible();

    // Should show wait time
    await expect(page.locator('[data-testid="wait-time"]')).toContainText(/\d+\s*(min|hour)/);
  });

  test('province filter works', async ({ page }) => {
    await page.goto('/');

    // Select Quebec from filter
    await page.selectOption('[data-testid="province-filter"]', 'QC');

    // Wait for markers to update
    await page.waitForTimeout(500);

    // All visible hospitals should be in Quebec
    const hospitalCards = await page.locator('[data-testid="hospital-marker"]').all();
    // Further assertions...
  });
});
```

---

## Planning & Documentation

### Planning Document Organization

**`docs/planning/roadmap.md`** - Current ROADMAP.md content

**`docs/planning/strategic-plan.md`** - Current er-times-plan.md content

**`docs/planning/retrospectives/`** - Post-sprint learnings:

```markdown
# docs/planning/retrospectives/week-1.md

# Week 1 Retrospective (Jan 1-5, 2026)

## What Went Well ✅

- Database schema created without issues
- Quebec scraper working on first try
- Heartbeat system simple and effective
- Team morale high

## What Could Be Improved 🔧

- Underestimated time for RLS policy debugging (2 hours)
- Should have created test fixtures before writing scraper
- Documentation fell behind code (will catch up Week 2)

## Action Items 📋

- [ ] Create test fixtures for all provinces upfront
- [ ] Update docs daily, not at end of week
- [ ] Add 20% buffer to time estimates

## Metrics 📊

- **Planned:** 5 days, 30 hours
- **Actual:** 5 days, 34 hours
- **Velocity:** 0.88 (below target)
- **Tests Written:** 15
- **Coverage:** 82%

## Next Sprint Focus

- Build Alberta and Manitoba scrapers
- Implement comparability logic
- Catch up on documentation
```

---

## Developer Experience

### VS Code Workspace Settings

**`.vscode/settings.json`**:

```json
{
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true,
    "source.organizeImports": true
  },
  "editor.rulers": [100],

  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "none",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,

  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    }
  },

  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },

  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },

  "files.associations": {
    "*.css": "tailwindcss"
  },

  "tailwindCSS.experimental.classRegex": [
    ["cva\\(([^)]*)\\)", "[\"'`]([^\"'`]*).*?[\"'`]"],
    ["cx\\(([^)]*)\\)", "(?:'|\"|`)([^']*)(?:'|\"|`)"]
  ],

  "search.exclude": {
    "**/node_modules": true,
    "**/.next": true,
    "**/__pycache__": true,
    "**/.pytest_cache": true,
    "**/.venv": true
  }
}
```

**`.vscode/extensions.json`**:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "charliermarsh.ruff",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "bradlc.vscode-tailwindcss",
    "yzhang.markdown-all-in-one",
    "bierner.markdown-mermaid",
    "GitHub.copilot",
    "eamodio.gitlens"
  ]
}
```

**`.vscode/launch.json`** - Debug configurations:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": true
    },
    {
      "name": "Python: Run Scraper",
      "type": "python",
      "request": "launch",
      "module": "waittime",
      "args": ["scrape", "--province", "QC"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}/backend"
    },
    {
      "name": "Next.js: Debug",
      "type": "node",
      "request": "launch",
      "runtimeExecutable": "pnpm",
      "runtimeArgs": ["dev"],
      "cwd": "${workspaceFolder}/frontend",
      "serverReadyAction": {
        "pattern": "started server on .+, url: (https?://.+)",
        "uriFormat": "%s",
        "action": "debugWithChrome"
      }
    },
    {
      "name": "Playwright: Debug",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/frontend/node_modules/.bin/playwright",
      "args": ["test", "--debug"],
      "cwd": "${workspaceFolder}/frontend"
    }
  ]
}
```

### Pre-commit Hooks

**`.pre-commit-config.yaml`**:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-json
      - id: check-toml
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.1
    hooks:
      - id: mypy
        additional_dependencies: [types-requests, pydantic]
        args: [--strict]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(ts|tsx)$
        args: [--fix]

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: \.(ts|tsx|json|yaml|yml|md)$
```

### GitHub Templates

**`.github/PULL_REQUEST_TEMPLATE.md`**:

```markdown
## Description

<!-- Provide a brief description of the changes -->

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Infrastructure change

## Related Issues

<!-- Link to related issues, e.g., "Closes #123" -->

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] E2E tests added/updated
- [ ] Manual testing completed

## Checklist

- [ ] My code follows the project's code style
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)

<!-- Add screenshots to help explain your changes -->

## Additional Context

<!-- Add any other context about the PR here -->
```

**`.github/ISSUE_TEMPLATE/bug_report.yml`**:

```yaml
name: Bug Report
description: File a bug report
title: "[Bug]: "
labels: ["bug", "triage"]
body:
  - type: markdown
    attributes:
      value: |
        Thanks for taking the time to fill out this bug report!

  - type: textarea
    id: what-happened
    attributes:
      label: What happened?
      description: A clear and concise description of what the bug is.
    validations:
      required: true

  - type: textarea
    id: expected
    attributes:
      label: Expected Behavior
      description: What did you expect to happen?
    validations:
      required: true

  - type: textarea
    id: steps
    attributes:
      label: Steps to Reproduce
      description: Steps to reproduce the behavior
      placeholder: |
        1. Go to '...'
        2. Click on '...'
        3. Scroll down to '...'
        4. See error
    validations:
      required: true

  - type: dropdown
    id: component
    attributes:
      label: Component
      description: Which component is affected?
      options:
        - Backend (Scrapers)
        - Frontend
        - Database
        - Documentation
        - CI/CD
        - Other
    validations:
      required: true

  - type: textarea
    id: logs
    attributes:
      label: Relevant log output
      description: Please copy and paste any relevant log output.
      render: shell

  - type: checkboxes
    id: terms
    attributes:
      label: Checklist
      options:
        - label: I have searched existing issues
          required: true
        - label: I am using the latest version
          required: true
```

### EditorConfig

**`.editorconfig`**:

```ini
# EditorConfig is awesome: https://EditorConfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true

[*.{py,pyi}]
indent_style = space
indent_size = 4
max_line_length = 100

[*.{ts,tsx,js,jsx,json}]
indent_style = space
indent_size = 2

[*.{yml,yaml}]
indent_style = space
indent_size = 2

[*.md]
trim_trailing_whitespace = false
max_line_length = off

[Makefile]
indent_style = tab
```

---

## Implementation Roadmap

### Phase 1: Documentation Foundation (Week 1)

**Day 1: MkDocs Setup (4 hours)**

- [ ] Install MkDocs Material and plugins
- [ ] Create `mkdocs.yml` configuration
- [ ] Set up documentation structure (`docs/` directory)
- [ ] Migrate existing docs to MkDocs format:
  - [ ] `IMPLEMENTATION.md` → `docs/development/setup.md`
  - [ ] `DATABASE.md` → `docs/architecture/database.md`
  - [ ] `API.md` → `docs/architecture/api.md`
  - [ ] `ROADMAP.md` → `docs/planning/roadmap.md`
- [ ] Add navigation structure to `mkdocs.yml`
- [ ] Test local build: `mkdocs serve`
- [ ] Verify all links work

**Acceptance Criteria:**
- [ ] `mkdocs serve` runs without errors
- [ ] All existing docs migrated
- [ ] Navigation menu functional
- [ ] Code blocks have syntax highlighting

**Day 2: ADR Implementation (4 hours)**

- [ ] Copy ADR template to `docs/adr/template.md`
- [ ] Create ADR index page: `docs/adr/index.md`
- [ ] Write first 3 ADRs:
  - [ ] `0001-use-supabase.md`
  - [ ] `0002-metric-ontology.md`
  - [ ] `0003-serverless-scrapers.md`
- [ ] Add ADRs to `mkdocs.yml` navigation
- [ ] Create script to generate ADR index automatically

**Acceptance Criteria:**
- [ ] 3 ADRs written following template
- [ ] ADR index auto-generates
- [ ] ADRs linked in navigation

**Day 3: Repository Structure (6 hours)**

- [ ] Rename `scrapers/` → `backend/`
- [ ] Restructure backend package:
  - [ ] Create `src/waittime/` package
  - [ ] Move scrapers to `src/waittime/scrapers/`
  - [ ] Create `core/`, `services/`, `cli/` directories
  - [ ] Update imports
- [ ] Reorganize tests:
  - [ ] Create `tests/unit/`, `tests/integration/`, `tests/e2e/`
  - [ ] Move existing tests to appropriate directories
  - [ ] Update `conftest.py`
- [ ] Update `pyproject.toml` package name
- [ ] Verify tests still pass

**Acceptance Criteria:**
- [ ] New structure matches target layout
- [ ] All tests pass
- [ ] Imports work correctly
- [ ] `python -m waittime` runs

**Day 4: Test Organization (6 hours)**

- [ ] Create comprehensive `conftest.py` with fixtures
- [ ] Add pytest markers (unit, integration, e2e, slow)
- [ ] Configure pytest.ini for marker-based test selection
- [ ] Add test coverage configuration
- [ ] Create example tests for each type:
  - [ ] Unit test example
  - [ ] Integration test example
  - [ ] E2E test example
- [ ] Document testing strategy in `docs/development/testing.md`

**Acceptance Criteria:**
- [ ] Can run `pytest -m unit` (fast tests only)
- [ ] Can run `pytest -m integration` (with database)
- [ ] Coverage report generated
- [ ] Testing docs complete

**Day 5: Developer Experience (4 hours)**

- [ ] Create `.vscode/` directory with settings
- [ ] Add VS Code extensions recommendations
- [ ] Create debug configurations
- [ ] Set up `.editorconfig`
- [ ] Configure pre-commit hooks
- [ ] Create `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] Create issue templates
- [ ] Test pre-commit hooks work

**Acceptance Criteria:**
- [ ] VS Code opens with recommended extensions
- [ ] Pre-commit hooks run on commit
- [ ] Debug configurations work
- [ ] Issue templates appear in GitHub

---

### Phase 2: CI/CD & Automation (Week 2)

**Day 6: GitHub Actions for Docs (3 hours)**

- [ ] Create `.github/workflows/ci-docs.yml`
- [ ] Build docs on every PR
- [ ] Deploy docs to GitHub Pages on merge to main
- [ ] Add documentation build status badge to README
- [ ] Test workflow

**Acceptance Criteria:**
- [ ] Docs build successfully in CI
- [ ] Docs deployed to GitHub Pages
- [ ] Badge shows build status

**Day 7: Quality Automation (5 hours)**

- [ ] Create `.github/workflows/quality.yml`
- [ ] Add automated checks:
  - [ ] Pre-commit hooks run in CI
  - [ ] Test coverage enforcement (80%+)
  - [ ] Link checking in docs
  - [ ] Security scanning (Bandit, npm audit)
- [ ] Configure Dependabot for dependency updates
- [ ] Test all workflows

**Acceptance Criteria:**
- [ ] Quality checks run on every PR
- [ ] Coverage reports generated
- [ ] Dependabot configured
- [ ] All workflows pass

**Day 8-10: Polish & Documentation (12 hours)**

- [ ] Write all missing documentation pages:
  - [ ] Getting Started guide
  - [ ] Contributing guide
  - [ ] Troubleshooting guide
  - [ ] Adding a province guide
- [ ] Create architecture diagrams (Mermaid)
- [ ] Add code examples to docs
- [ ] Review and improve all existing docs
- [ ] Add screenshots where helpful
- [ ] Final review and polish

**Acceptance Criteria:**
- [ ] All planned documentation pages written
- [ ] Architecture diagrams clear and accurate
- [ ] Code examples tested and working
- [ ] Docs reviewed for clarity

---

## Migration Checklist

### Files to Rename/Move

- [ ] `scrapers/` → `backend/`
- [ ] `scrapers/src/` → `backend/src/waittime/`
- [ ] `database/` → `backend/migrations/`
- [ ] `er-times-plan.md` → `docs/planning/strategic-plan.md`
- [ ] `IMPLEMENTATION.md` → `docs/development/setup.md`
- [ ] `DATABASE.md` → `docs/architecture/database.md`
- [ ] `API.md` → `docs/architecture/api.md`
- [ ] `ROADMAP.md` → `docs/planning/roadmap.md`

### Files to Create

- [ ] `mkdocs.yml`
- [ ] `docs/index.md`
- [ ] `docs/adr/template.md`
- [ ] `docs/adr/0001-use-supabase.md`
- [ ] `docs/adr/0002-metric-ontology.md`
- [ ] `docs/adr/0003-serverless-scrapers.md`
- [ ] `.vscode/settings.json`
- [ ] `.vscode/extensions.json`
- [ ] `.vscode/launch.json`
- [ ] `.editorconfig`
- [ ] `.pre-commit-config.yaml`
- [ ] `.github/PULL_REQUEST_TEMPLATE.md`
- [ ] `.github/ISSUE_TEMPLATE/bug_report.yml`
- [ ] `.github/ISSUE_TEMPLATE/feature_request.yml`
- [ ] `.github/workflows/ci-docs.yml`
- [ ] `.github/workflows/quality.yml`
- [ ] `CONTRIBUTING.md`
- [ ] `CODE_OF_CONDUCT.md`
- [ ] `SECURITY.md`
- [ ] `CHANGELOG.md`

### Configuration Updates

- [ ] Update `pyproject.toml` with new package name
- [ ] Update imports in all Python files
- [ ] Update paths in GitHub Actions workflows
- [ ] Update README.md with new structure
- [ ] Update AGENTS.md with new structure

---

## Benefits of This Structure

### Documentation
✅ **Searchable** - MkDocs Material has excellent search
✅ **Beautiful** - Professional appearance for portfolio
✅ **Versioned** - Can version docs with Mike plugin
✅ **Mobile-friendly** - Responsive design out of the box
✅ **Fast** - Static site with instant page loads

### Testing
✅ **Clear separation** - Unit vs integration vs E2E
✅ **Fast CI** - Can run unit tests only for quick feedback
✅ **Comprehensive** - All test types covered
✅ **Discoverable** - Easy to find and write tests

### ADRs
✅ **Design rationale** - Captures "why" decisions were made
✅ **Portfolio value** - Shows thoughtful decision-making
✅ **Onboarding** - New contributors understand context
✅ **Consistency** - Standard format for all decisions

### Developer Experience
✅ **Automated** - Pre-commit hooks prevent bad commits
✅ **Standardized** - EditorConfig ensures consistency
✅ **Debuggable** - VS Code debug configs included
✅ **Discoverable** - Clear structure, easy to navigate

---

## Next Steps

1. Review this plan
2. Decide on implementation timeline (suggested: 2 weeks)
3. Start with Phase 1, Day 1 (MkDocs setup)
4. Work through checklist systematically
5. Update this plan as learnings emerge

---

**Questions?**
- Check examples in this document
- Review MkDocs Material documentation: https://squidfunk.github.io/mkdocs-material/
- Review ADR examples: https://adr.github.io/
- Review pytest best practices: https://docs.pytest.org/

This structure will make WaitTime Canada a showcase repository! 🚀
