# WaitTime Canada

> A clinically defensible "Health Systems Observatory" that audits and standardizes Canadian emergency room wait time data across provinces.

**Status:** 🚧 Active Development (Infrastructure Complete)
**Primary Focus:** 🎯 Ontario Implementation In Progress
**Live Site:** Coming Soon
**Documentation:** [docs/](./docs/)

**Latest:** Core infrastructure complete (127 tests, 67% coverage), Ontario scraper implemented ✓

---

## What This Is

WaitTime Canada is **not** a typical wait time aggregator. It's a research-grade data auditing platform that:

1. **Exposes Methodological Inconsistencies** - Proves why Alberta and Manitoba data cannot be directly compared
2. **Provides Province-Aware Stewardship** - Routes users to correct provincial telehealth resources
3. **Highlights Access Barriers** - Calculates hidden financial costs of seeking care
4. **Monitors System Health** - Detects silent failures in public health reporting

**Key Insight:** Instead of claiming to "fix" inconsistent data, we **audit** it. We standardize *how we describe* the wait, not the wait itself.

---

## The Metric Ontology

Every measurement is tagged with metadata:

| Field | Question | Examples |
|-------|----------|----------|
| `metric_family` | What is measured? | TIME_TO_PROVIDER, TOTAL_LOS |
| `start_event` | When does clock start? | TRIAGE, REGISTRATION, DOOR |
| `end_event` | When does clock stop? | PHYSICIAN, DISCHARGE |
| `statistic_type` | How is value calculated? | P90, MEAN, ROLLING_AVG |

**Comparability Logic:** Two measurements are comparable if and only if all four fields match.

**Example:**
- ✅ **Comparable:** Alberta (Triage→Physician, P90) vs. BC (Triage→Physician, P90)
- ❌ **Not Comparable:** Alberta (Triage→Physician, P90) vs. Quebec (Registration→Physician, Mean)

---

## Tech Stack

- **Backend:** Python 3.12+ with psycopg2, BeautifulSoup, Playwright, Pydantic
- **Database:** Neon PostgreSQL 17 (serverless with autoscaling)
- **Scraper Execution:** GitHub Actions (15-min cron) or local CLI
- **Frontend:** Next.js 14 + Mapbox GL + React Query
- **Testing:** Backend: 127 tests (113 unit + 14 integration), 67% coverage | Frontend: 73 tests, 100% pass
- **CI/CD:** GitHub Actions + Vercel

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20.x LTS (for frontend, later)
- Neon PostgreSQL account (free tier: [neon.tech](https://neon.tech))

### Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/waittime-canada.git
cd waittime-canada

# Set up environment variables
cd backend
cp .env.example .env.local
# Edit .env.local with your Neon DATABASE_URL

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Test database connection
python test_connection.py

# Run migrations
python run_migrations.py

# Run tests
pytest tests/unit/ -v

# Test Quebec scraper (dry run)
python -m waittime.cli.scraper --source quebec-msss --dry-run

# List available scrapers
python -m waittime.cli.scraper --list
```

---

## Project Structure

```
waittime-canada/
├── backend/                      # Python scraper service
│   ├── src/waittime/            # Main package
│   │   ├── core/                # Domain models & ontology
│   │   ├── scrapers/            # Provincial scrapers
│   │   │   ├── base.py          # BaseScraper abstract class
│   │   │   └── quebec.py        # Quebec MSSS scraper
│   │   ├── services/            # Database & external services
│   │   └── cli/                 # Command-line interface
│   ├── tests/                   # Test suite
│   │   ├── unit/                # Fast, no I/O
│   │   ├── integration/         # Database, HTTP
│   │   └── e2e/                 # Full workflows
│   ├── migrations/              # SQL migrations
│   └── pyproject.toml           # Dependencies & tooling
├── frontend/                    # Next.js app (planned)
├── docs/                        # MkDocs Material documentation
│   ├── architecture/            # Database, API specs
│   ├── development/             # Setup guides
│   ├── planning/                # Roadmap, strategic plan
│   └── adr/                     # Architecture Decision Records
├── .github/workflows/           # CI/CD pipelines
└── mkdocs.yml                   # Documentation config
```

---

## Documentation

**Project Planning:**
- [ROADMAP.md](./ROADMAP.md) - **Start here** - Master task list with milestones
- [Expansion Strategy](./docs/planning/expansion-roadmap.md) - Provincial rollout plan

**Technical Reference:**
- [Implementation Guide](./docs/development/setup.md) - Development environment setup
- [Database Schema](./docs/architecture/database.md) - Schema and migrations
- [API Specification](./docs/architecture/api.md) - Endpoint contracts
- [Strategic Plan](./docs/planning/strategic-plan.md) - Original specification

**For AI Assistants:**
- [CLAUDE.md](./CLAUDE.md) - Codebase guidance for Claude Code

---

## Key Features

### 1. Methodology Divergence Warnings
When comparing hospitals with different methodologies, the system shows:
> ⚠️ **Methodology Divergence:** Ottawa reports P90 Triage-to-Doctor time. Gatineau reports Average Registration-to-Doctor time. Direct comparison is invalid.

### 2. Province-Aware Telehealth Directory
- **Ontario:** "Call Health811"
- **Quebec:** "Call Info-Santé 811"
- **Alberta:** "Call Health Link 811"

### 3. Heartbeat Monitor
Frontend displays: *"Last Audit: 4 mins ago (Healthy)"*
If >60 minutes old, alerts trigger via GitHub Actions.

### 4. Methods & Governance Page
Dynamic table showing comparability matrix across provinces.

---

## Development

### Running Tests

```bash
# Scraper tests
cd scrapers
pytest --cov=src

# Frontend tests
cd frontend
pnpm test:unit          # Vitest
pnpm test:e2e           # Playwright
```

### Code Quality

```bash
# Python linting
cd scrapers
ruff check src/
ruff format src/
mypy src/

# TypeScript linting
cd frontend
pnpm lint
pnpm format:check
pnpm type-check
```

### Running Scrapers Locally

```bash
cd backend
source .venv/bin/activate

# List available scrapers
python -m waittime.cli.scraper --list

# Dry run (no database writes)
python -m waittime.cli.scraper --source quebec-msss --dry-run

# Run single scraper
python -m waittime.cli.scraper --source quebec-msss

# Run all scrapers
python -m waittime.cli.scraper --all
```

---

## Deployment

### Frontend (Vercel)
- Auto-deployed on push to `main`
- Configure environment variables in Vercel dashboard

### Scrapers (GitHub Actions)
- Runs every 15 minutes via cron schedule
- Configure secrets in GitHub repo settings

### Database (Neon PostgreSQL)
- Migrations applied via GitHub Actions on merge to `main`

---

## Contributing

This is a portfolio project, but feedback is welcome:

1. Open an issue describing your suggestion
2. For code changes, fork and submit a PR
3. Ensure all tests pass and linting is clean

---

## License

MIT License - See [LICENSE](./LICENSE)

---

## Acknowledgments

- Provincial health authorities for publishing wait time data
- Open source communities: Neon, Next.js, Mapbox
- Canadian healthcare workers

---

## Contact

**Author:** [Your Name]
**Purpose:** Physician-innovator portfolio project for medical school applications
**LinkedIn:** [Your LinkedIn]

---

Built with ❤️ for transparent, evidence-based healthcare.
