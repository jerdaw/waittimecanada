# WaitTime Canada

> A clinically defensible "Health Systems Observatory" that audits and standardizes Canadian emergency room wait time data across provinces.

**Status:** 🚀 Core Features Complete | 📊 Ready for Production
**Test Coverage:** Backend: 143 tests (57% coverage) | Frontend: 79 tests (100% pass rate)
**Live Site:** Coming Soon
**Documentation:** [docs/](./docs/)



---

## What This Is

WaitTime Canada is **not** a typical wait time aggregator. It's a research-grade data auditing platform that:

1. **Exposes Methodological Inconsistencies** - Demonstrates why Ontario P90 times cannot be directly compared to Quebec rolling averages
2. **Provides Clinically Defensible Comparisons** - Automatically detects and warns about methodology divergence
3. **Offers Province-Aware Stewardship** - Routes users to correct provincial telehealth resources (Health811, Info-Santé 811)
4. **Maintains Transparency** - Full methodology documentation and interactive comparability matrix
5. **Monitors Data Freshness** - Heartbeat system detects when scrapers fail silently

**Key Insight:** Instead of claiming to "fix" inconsistent data, we **audit** it. We standardize *how we describe* the measurement, not the measurement itself.

---

## Core Features

### 🗺️ Interactive Map
- Live wait times for 213+ Ontario hospitals
- Color-coded markers (< 60 min: green, 60-120 min: amber, > 120 min: red)
- Hospital popups with methodology transparency
- Province-specific telehealth routing
- Data freshness indicators

### ⚖️ Methodology Comparability
When comparing two hospitals, the system automatically:
- Checks if methodologies match across 4 dimensions
- Shows visual comparison table (✓ match, ≠ mismatch)
- Generates divergence brief explaining differences
- Warns when direct comparison is statistically invalid

**Example:**
> ⚠️ **Methodology Divergence:** Ottawa reports P90 Triage-to-Physician time. Gatineau reports Rolling Average Registration-to-Physician time. Direct comparison is scientifically invalid. Different start points: TRIAGE vs REGISTRATION; Different statistics: P90 vs ROLLING_AVG.

### 📊 Methods & Governance Page
- **Comparability Matrix:** Interactive table showing which provinces can be directly compared
- **Ontology Explainer:** Accordion explaining the 4 dimensions of wait time measurement
- **Province Methodology Cards:** Visual cards showing each province's measurement approach
- **FAQ:** Answers common questions about methodology differences

### 🏥 Telehealth Routing
Province-specific healthcare guidance in every hospital popup:
- **Ontario:** "Need medical advice? Call Health811 - 811"
- **Quebec:** "Call Info-Santé 811 - 811"
- **Alberta:** "Call Health Link 811 - 811"
- Mobile-friendly with one-tap tel: links

### 📈 Wait Time Trends
Historical data visualization integrated into hospital details:
- **Timeframes:** 24 Hours, 7 Days, 30 Days
- **Aggregation:** Hourly or daily averages
- **Visuals:** Interactive line charts with tooltips

### 📱 Progressive Web App (PWA)
Installable application with offline support:
- **Offline Access:** Caches static assets and API responses (stale-while-revalidate)
- **Installability:** Custom install prompt for eligible devices
- **Experience:** Splash screens, app icons, and standalone mode

### 🔬 The Metric Ontology

Every measurement is tagged with metadata that determines comparability:

| Dimension | Question | Ontario Example | Quebec Example |
|-----------|----------|----------------|----------------|
| `metric_family` | What is measured? | TIME_TO_PROVIDER | TIME_TO_PROVIDER |
| `start_event` | When does clock start? | TRIAGE | REGISTRATION |
| `end_event` | When does clock stop? | PHYSICIAN | PHYSICIAN |
| `statistic_type` | How is value calculated? | P90 (90th percentile) | ROLLING_AVG |

**Comparability Logic:** Two measurements are comparable **if and only if** all four dimensions match.

**Examples:**
- ✅ **Comparable:** Hospital A (Triage→Physician, P90) vs. Hospital B (Triage→Physician, P90)
- ❌ **Not Comparable:** Ontario (Triage→Physician, P90) vs. Quebec (Registration→Physician, Rolling Avg)

---

## Tech Stack

### Backend
- **Language:** Python 3.12+
- **Database:** Neon PostgreSQL 17 (serverless with connection pooling)
- **Scraping:** BeautifulSoup4 (Quebec), Playwright (Ontario - dynamic content)
- **Validation:** Pydantic v2 with strict ontology enums
- **Testing:** pytest (143 tests, 57% coverage)
- **Execution:** GitHub Actions (15-min cron) + local CLI

### Frontend
- **Framework:** Next.js 14 with App Router + TypeScript
- **Mapping:** Mapbox GL JS with interactive markers
- **Database Client:** postgres (Neon serverless driver)
- **Styling:** Tailwind CSS with custom design tokens
- **Testing:** Vitest + React Testing Library (79 tests, 100% pass rate)
- **Deployment:** Vercel (planned)

### Data Pipeline
```
Provincial Portal → Scraper → Neon PostgreSQL → Next.js API Routes → Frontend
       ↓                ↓              ↓                  ↓              ↓
  Live HTML     Ontology Tags   Measurements      JSON API      Interactive Map
```

---

## Quick Start

### Prerequisites

- **Python:** 3.12+ (backend scrapers)
- **Node.js:** 20.x LTS (frontend)
- **Database:** Neon PostgreSQL account ([neon.tech](https://neon.tech) - free tier available)

### Backend Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/waittime-canada.git
cd waittime-canada/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment
cp .env.example .env.local
# Edit .env.local with your Neon DATABASE_URL

# Run migrations
python run_migrations.py

# Test database connection
python test_connection.py

# Run tests
pytest tests/ -v

# Seed Ontario hospitals (optional)
python -m waittime.cli.seed_sources backend/data/sources/ontario-health.json
python -m waittime.cli.seed backend/data/hospitals/ontario-seed.json
python -m waittime.cli.generate_test_data --source ontario-health --count 530
```

### Frontend Setup

```bash
cd waittime-canada/frontend

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your Neon DATABASE_URL and MAPBOX_TOKEN

# Run development server
npm run dev

# Run tests
npm run test:unit

# Build for production
npm run build
```

### Running Scrapers

```bash
cd backend
source .venv/bin/activate

# List available scrapers
python -m waittime.cli.scraper --list

# Dry run (no database writes)
python -m waittime.cli.scraper --source quebec-msss --dry-run

# Run Ontario scraper
python -m waittime.cli.scraper --source ontario-health

# Run all scrapers
python -m waittime.cli.scraper --all
```

---

## Project Structure

```
waittime-canada/
├── backend/                      # Python scraper service
│   ├── src/waittime/            # Main package
│   │   ├── core/                # Domain models & ontology enums
│   │   │   ├── models.py        # Hospital, Measurement, Source
│   │   │   └── enums.py         # MetricFamily, StartEvent, etc.
│   │   ├── scrapers/            # Provincial scrapers
│   │   │   ├── base.py          # BaseScraper abstract class
│   │   │   ├── quebec.py        # Quebec MSSS scraper
│   │   │   └── ontario.py       # Ontario Health scraper (Playwright)
│   │   ├── services/            # Business logic
│   │   │   ├── database.py      # DatabaseService (CRUD operations)
│   │   │   ├── comparison.py    # ComparisonService (divergence detection)
│   │   │   └── heartbeat.py     # HeartbeatService (scraper health)
│   │   └── cli/                 # Command-line interface
│   │       ├── scraper.py       # Scraper runner
│   │       ├── seed.py          # Hospital seeding tool
│   │       └── cleanup.py       # Data retention (30-day policy)
│   ├── tests/                   # Test suite (143 tests)
│   │   ├── unit/                # Unit tests (122 tests)
│   │   └── integration/         # Integration tests (21 tests)
│   ├── migrations/              # SQL schema migrations
│   ├── data/                    # Seed data (sources, hospitals)
│   └── pyproject.toml           # Dependencies & tool config
│
├── frontend/                    # Next.js application
│   ├── app/                     # App Router pages
│   │   ├── page.tsx             # Home page with map
│   │   ├── methods/             # Methods & governance page
│   │   └── api/                 # API routes
│   │       ├── hospitals/       # GET /api/hospitals
│   │       └── compare/         # GET /api/compare?a=...&b=...
│   ├── components/              # React components
│   │   ├── Map.tsx              # Interactive Mapbox map
│   │   ├── ComparisonModal.tsx  # Hospital comparison modal
│   │   ├── DivergenceWarning.tsx # Methodology warning
│   │   └── methods/             # Methods page components
│   ├── tests/                   # Test suite (79 tests)
│   └── package.json             # Dependencies
│
├── docs/                        # Documentation
│   ├── implementation/          # Task completion summaries
│   │   ├── task-2.2-hospital-seeding.md
│   │   ├── task-2.3-map-integration.md
│   │   ├── task-2.4-comparison-testing.md
│   │   └── task-5.3-telehealth-routing.md
│   ├── methodologies/           # Provincial methodology docs
│   │   └── ontario-methodology.md
│   └── architecture/            # System design docs
│
├── .github/workflows/           # CI/CD pipelines
│   ├── backend-ci.yml           # Backend tests + linting
│   ├── frontend-ci.yml          # Frontend tests + type-check
│   └── database-cleanup.yml     # 30-day data retention
│
├── ROADMAP.md                   # Master task list with milestones
├── AGENTS.md                    # Guidance for automated developer tools
└── README.md                    # This file
```

---

## Testing

### Test Coverage

**Backend (143 tests, 57% coverage):**
- Unit tests: 122 tests
  - Core models: 96% coverage
  - Services: 85-100% coverage (ComparisonService: 100%)
  - Scrapers: 73-96% coverage
- Integration tests: 21 tests
  - Database operations: 14 tests
  - Comparison feature: 7 tests

**Frontend (79 tests, 100% pass rate):**
- Component tests: 79 tests
  - Map component: 6 tests
  - ComparisonModal: 14 tests
  - DivergenceWarning: 10 tests
  - ComparabilityMatrix: 12 tests
  - Other components: 37 tests

### Running Tests

```bash
# Backend tests
cd backend
source .venv/bin/activate
pytest tests/ -v                          # All tests
pytest tests/unit/ -v                     # Unit tests only
pytest tests/integration/ -v              # Integration tests only
pytest tests/ --cov=src --cov-report=html # With coverage

# Frontend tests
cd frontend
npm run test:unit                         # Vitest
npm run test:e2e                          # Playwright (CI only)
```

### Manual Testing

```bash
# Test hospitals API with real data
cd frontend
node test-api.js

# Test comparison feature
node test-comparison-api.js

# Test telehealth routing
node test-telehealth-api.js
```

---

## Development Workflow

### Code Quality Tools

```bash
# Backend (Python)
cd backend
ruff check src/              # Linting
ruff format src/             # Formatting
mypy src/                    # Type checking

# Frontend (TypeScript)
cd frontend
npm run lint                 # ESLint
npm run type-check           # TypeScript
```

### Git Workflow

```bash
# Feature branch
git checkout -b feat/new-feature

# Make changes and test
pytest tests/ -v             # Backend tests
npm run test:unit            # Frontend tests

# Commit with conventional commits
git add .
git commit -m "feat(comparison): add divergence brief generation"

# Push and create PR
git push origin feat/new-feature
```

### Running Development Servers

```bash
# Backend (for local scraper testing)
cd backend
source .venv/bin/activate
python -m waittime.cli.scraper --source ontario-health

# Frontend (for UI development)
cd frontend
npm run dev
# Open http://localhost:3000
```

---

## Deployment

### Database (Neon PostgreSQL)
1. Create Neon project at [neon.tech](https://neon.tech)
2. Copy connection string to `.env.local`
3. Run migrations: `python run_migrations.py`
4. Seed data: `python -m waittime.cli.seed_sources ...`

### Frontend (Vercel)
1. Connect GitHub repo to Vercel
2. Set environment variables:
   - `DATABASE_URL` - Neon connection string
   - `NEXT_PUBLIC_MAPBOX_TOKEN` - Mapbox API key
3. Deploy automatically on push to `main`

### Scrapers (GitHub Actions)
1. Add GitHub secrets:
   - `DATABASE_URL` - Neon connection string
2. Scrapers run every 15 minutes via cron
3. Heartbeat monitor alerts if scrapers fail

---

## Data

### Current Coverage

**Ontario:**
- 213 hospitals seeded
- 165 verified and visible
- 530 test measurements
- Source: ontario-health
- Methodology: TIME_TO_PROVIDER, TRIAGE → PHYSICIAN, P90

**Quebec:**
- Scraper implemented (BeautifulSoup-based)
- Awaiting URL verification and hospital seeding
- Methodology: TIME_TO_PROVIDER, REGISTRATION → PHYSICIAN, ROLLING_AVG

### Data Retention Policy
- Measurements older than 30 days are automatically deleted
- Cleanup runs daily via GitHub Actions
- Aggregate statistics preserved for trending

### Verification Queue
- New hospitals require manual approval (is_verified=true)
- Admin UI at `/admin/verify` for review
- Prevents incorrect data from going live

---

## Key Implementation Details

### Comparability Detection

```typescript
function areComparable(a: Hospital, b: Hospital): boolean {
  return (
    a.metric_family === b.metric_family &&
    a.start_event === b.start_event &&
    a.end_event === b.end_event &&
    a.statistic_type === b.statistic_type
  );
}
```

### Divergence Brief Generation

```python
def _generate_divergence_brief(self, meth_a: Measurement, meth_b: Measurement) -> str:
    differences = []
    if meth_a.metric_family != meth_b.metric_family:
        differences.append(f"Different metric families: {meth_a.metric_family} vs {meth_b.metric_family}")
    if meth_a.start_event != meth_b.start_event:
        differences.append(f"Different start points: {meth_a.start_event} vs {meth_b.start_event}")
    # ... more checks ...
    return f"Methodology Divergence: Direct comparison is scientifically invalid. {'; '.join(differences)}."
```

### Scraper Pattern

```python
class OntarioScraper(BaseScraper):
    def scrape(self) -> List[Measurement]:
        # 1. Fetch HTML (with retry logic)
        html = self._fetch_with_retry(url)

        # 2. Parse with Playwright (for dynamic content)
        measurements = self._parse_html(html)

        # 3. Tag with ontology
        for m in measurements:
            m.metric_family = "TIME_TO_PROVIDER"
            m.start_event = "TRIAGE"
            m.end_event = "PHYSICIAN"
            m.statistic_type = "P90"

        # 4. Write heartbeat
        self.heartbeat_service.write_heartbeat(self.source_id)

        return measurements
```

---

## Documentation

### For Users
- **[Methods Page](/methods)** - Understanding wait time methodologies
- **[FAQ](./docs/faq.md)** - Common questions
- **Divergence Warnings** - Shown automatically when comparing incompatible hospitals

### For Developers
- **[ROADMAP.md](./ROADMAP.md)** - Master task list with milestones
- **[AGENTS.md](./AGENTS.md)** - Guidance for automated developer tools
- **[Ontario Methodology](./docs/methodologies/ontario-methodology.md)** - Detailed methodology docs
- **[Task Summaries](./docs/implementation/)** - Implementation completion docs

### Architecture Decision Records
- Database choice (Neon PostgreSQL vs Supabase)
- Scraper execution (GitHub Actions vs Lambda)
- Ontology enforcement (strict enums vs tags)
- Verification workflow (manual vs automatic)

**Latest Update (Feb 4, 2026):**
- ✅ Milestone 7 Complete: UX Polish & SEO enhancements implemented
- ✅ Skeleton screens and real-time hospital search/filter live
- ✅ Browser geolocation sorting and distance display live
- ✅ Schema.org structured data and healthcare meta tags added
- ✅ Geocoding coverage (100%), 150+ unit tests passing

---

## Roadmap

### 🔄 Planned & In Progress
- [ ] **Regional Scaling**: Implement Alberta and British Columbia scrapers
- [ ] **Admin Enhancements**: Batch operations and search/filter for verification queue
- [ ] **Data Insights**: Historical trend charts and aggregate data export

### 🎯 Future Backlog
- [ ] **Burden Estimator**: Access burden calculator (logistics, parking, and gas estimates)
- [ ] **Proactive Alerts**: Email/Push notifications for significant wait time spikes
- [ ] **Mobile App**: Dedicated mobile application (React Native / Expo)
- [ ] **Equity Layer**: Socio-economic overlays for access analysis

---

## Contributing

This is a portfolio project for medical school applications, but feedback and contributions are welcome:

1. **Report Issues:** Open an issue describing the bug or suggestion
2. **Submit PRs:** Fork, create feature branch, ensure tests pass
3. **Improve Docs:** Documentation PRs always appreciated
4. **Add Provinces:** Help scrape and document other provincial portals

### Code Standards
- Backend: Follow ruff formatting, mypy type hints
- Frontend: ESLint + TypeScript strict mode
- Tests: Minimum 80% coverage for new code
- Commits: Conventional commits (feat:, fix:, docs:, etc.)

---

## License

MIT License - See [LICENSE](./LICENSE)

You are free to use, modify, and distribute this code for educational and commercial purposes.

---

## Acknowledgments

- **Provincial Health Authorities** - For publishing wait time data publicly
- **Neon PostgreSQL** - Serverless database with excellent DX
- **Next.js & Vercel** - Modern web framework and hosting
- **Mapbox** - Beautiful, performant mapping
- **Canadian Healthcare Workers** - For their tireless service
- **Open Source Community** - For building amazing tools

---

## Contact & Purpose

**Purpose:** Physician-innovator portfolio project demonstrating:
- **Scholar:** Research methodology, data auditing, ontology design
- **Professional:** Clinical defensibility, stewardship, ethical data handling
- **Advocate:** Healthcare transparency, access barriers, system monitoring
- **Leader:** Project planning, technical execution, documentation

**Author:** Jeremy Dawson
**GitHub:** [github.com/jerdaw/waittimecanada](https://github.com/jerdaw/waittimecanada)
**LinkedIn:** [linkedin.com/in/jeremyjdawson](https://www.linkedin.com/in/jeremyjdawson/)
**Email:** jeremyjdawson@gmail.com

---

**Built with ❤️ for transparent, evidence-based healthcare.**

*"The goal is not to fix broken data—it's to audit it, explain the brokenness, and prevent misuse."*
