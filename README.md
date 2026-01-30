# WaitTime Canada

> A clinically defensible "Health Systems Observatory" that audits and standardizes Canadian emergency room wait time data across provinces.

**Status:** Planning Phase → Implementation Starting
**Live Site:** Coming Soon
**Documentation:** [docs/](./docs/)

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

- **Backend:** Python 3.12 scrapers via GitHub Actions (serverless, 15-min cron)
- **Database:** Supabase (PostgreSQL 15+ with PostGIS and strict enums)
- **Frontend:** Next.js 14 + Mapbox GL + React Query
- **CI/CD:** GitHub Actions + Vercel
- **Monitoring:** Sentry + Heartbeat system

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20.x LTS
- pnpm 8.x
- Supabase account

### Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/waittime-canada.git
cd waittime-canada

# Set up environment variables
cp scrapers/.env.example scrapers/.env
cp frontend/.env.local.example frontend/.env.local
# Edit .env files with your credentials

# Initialize database
psql $SUPABASE_URL -f database/migrations/001_initial_schema.sql
psql $SUPABASE_URL -f database/migrations/002_add_heartbeat.sql
psql $SUPABASE_URL -f database/migrations/003_add_indexes.sql
psql $SUPABASE_URL -f database/seed/sources.sql

# Install and run scrapers
cd scrapers
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python -m src.main

# Install and run frontend
cd ../frontend
pnpm install
pnpm dev
# Open http://localhost:3000
```

---

## Project Structure

```
waittime-canada/
├── docs/                    # Implementation documentation
│   ├── IMPLEMENTATION.md    # Tech stack & setup guide
│   ├── DATABASE.md          # Schema & migrations
│   ├── API.md               # Endpoint specifications
│   └── ROADMAP.md           # Week-by-week plan
├── scrapers/                # Python scraper service
│   └── src/
│       ├── scrapers/        # Provincial scrapers
│       └── core/            # Shared utilities
├── frontend/                # Next.js application
│   └── src/
│       ├── app/             # Pages (App Router)
│       ├── components/      # React components
│       └── lib/             # API & utilities
├── database/                # SQL migrations & seed data
│   └── migrations/
└── .github/workflows/       # CI/CD pipelines
```

---

## Documentation

**For Developers:**
- [Implementation Guide](./docs/IMPLEMENTATION.md) - Detailed tech setup
- [Database Schema](./docs/DATABASE.md) - Complete schema with RLS policies
- [API Specification](./docs/API.md) - Endpoint contracts
- [Roadmap](./docs/ROADMAP.md) - 4-week implementation plan

**For AI Assistants:**
- [CLAUDE.md](./CLAUDE.md) - Codebase guidance for Claude Code

**Strategic Context:**
- [er-times-plan.md](./er-times-plan.md) - Original strategic specification

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
cd scrapers
source .venv/bin/activate

# Run single scraper
python -m src.scrapers.quebec

# Run all scrapers
python -m src.main
```

---

## Deployment

### Frontend (Vercel)
- Auto-deployed on push to `main`
- Configure environment variables in Vercel dashboard

### Scrapers (GitHub Actions)
- Runs every 15 minutes via cron schedule
- Configure secrets in GitHub repo settings

### Database (Supabase)
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
- Open source communities: Supabase, Next.js, Mapbox
- Canadian healthcare workers

---

## Contact

**Author:** [Your Name]
**Purpose:** Physician-innovator portfolio project for medical school applications
**LinkedIn:** [Your LinkedIn]

---

Built with ❤️ for transparent, evidence-based healthcare.
