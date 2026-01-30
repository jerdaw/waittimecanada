# Technical Implementation Guide

## Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Development Environment Setup](#development-environment-setup)
4. [Code Quality Standards](#code-quality-standards)
5. [Testing Strategy](#testing-strategy)
6. [Security Considerations](#security-considerations)
7. [Performance Optimization](#performance-optimization)
8. [Error Handling & Observability](#error-handling--observability)

---

## Tech Stack

### Backend (Scrapers)

**Language & Runtime**
- Python 3.12+ (for modern type hints and performance)
- pip-tools for dependency management (reproducible builds)

**Core Dependencies**
```toml
# pyproject.toml
[project]
name = "waittime-scrapers"
version = "1.0.0"
requires-python = ">=3.12"
dependencies = [
    "requests>=2.31.0",           # HTTP client
    "beautifulsoup4>=4.12.0",     # HTML parsing
    "lxml>=5.0.0",                # Fast XML/HTML parser
    "supabase>=2.0.0",            # Database client
    "python-dotenv>=1.0.0",       # Environment variables
    "structlog>=24.0.0",          # Structured logging
    "tenacity>=8.2.0",            # Retry logic
    "pydantic>=2.5.0",            # Data validation
    "httpx>=0.26.0",              # Async HTTP (for parallel scraping)
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.1.0",                # Fast linter/formatter
    "mypy>=1.7.0",                # Type checking
    "pre-commit>=3.6.0",
]
```

**Rationale:**
- `requests` + `httpx`: Standard HTTP libs, httpx for async operations
- `beautifulsoup4` + `lxml`: Battle-tested HTML parsing
- `supabase`: Official Python client with connection pooling
- `structlog`: JSON-structured logs for production observability
- `tenacity`: Declarative retry logic (exponential backoff)
- `pydantic`: Runtime validation of scraped data against ontology
- `ruff`: Replace black + isort + flake8 with one fast tool

### Frontend

**Framework & Runtime**
- Next.js 14.x (App Router)
- React 18.x
- Node.js 20.x LTS
- pnpm 8.x (fast, disk-efficient package manager)

**Core Dependencies**
```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "mapbox-gl": "^3.0.0",
    "react-map-gl": "^7.1.0",
    "@supabase/supabase-js": "^2.39.0",
    "@tanstack/react-query": "^5.17.0",
    "date-fns": "^3.0.0",
    "zod": "^3.22.4"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "@types/react": "^18.2.0",
    "@types/node": "^20.10.0",
    "eslint": "^8.56.0",
    "eslint-config-next": "^14.0.0",
    "prettier": "^3.1.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.32",
    "vitest": "^1.1.0",
    "@testing-library/react": "^14.1.0",
    "playwright": "^1.40.0"
  }
}
```

**Rationale:**
- Next.js 14 App Router: RSC, parallel routes, server actions
- React Query: Data fetching, caching, infinite scroll
- Mapbox GL: Industry-standard mapping with Canadian base layers
- Zod: Runtime schema validation matching API contracts
- Vitest: Fast unit/component tests, Vite-powered
- Playwright: Reliable E2E tests with mobile emulation

### Database

**Platform**: Supabase (Managed PostgreSQL 15+)

**Key Features Used:**
- Row-Level Security (RLS) for read-only public access
- Database Webhooks for scraper heartbeat monitoring
- PostGIS extension for geospatial queries
- pgvector extension (future: ML embeddings for similarity)
- Realtime subscriptions for heartbeat UI updates

### Infrastructure

**CI/CD**: GitHub Actions
- Scraper workflow: 15-minute cron + manual trigger
- Frontend: Deploy to Vercel on push to main
- Database: Migrations applied via GitHub Actions

**Hosting**:
- Frontend: Vercel (edge functions, CDN)
- Scrapers: GitHub Actions (serverless, free tier)
- Database: Supabase (free tier for MVP, Pro at scale)

**Monitoring**:
- Sentry for error tracking (both frontend & scrapers)
- Supabase Dashboard for DB metrics
- Vercel Analytics for web vitals
- GitHub Actions notifications for scraper failures

---

## Project Structure

```
waittime-canada/
├── .github/
│   └── workflows/
│       ├── scraper-cron.yml          # 15-min scraper schedule
│       ├── scraper-ci.yml            # Test scrapers on PR
│       ├── frontend-ci.yml           # Test frontend on PR
│       └── database-migrate.yml      # Apply migrations
│
├── scrapers/                         # Python scraper service
│   ├── pyproject.toml                # Dependencies
│   ├── .env.example                  # Environment template
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                   # Orchestrator (run all scrapers)
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── database.py           # Supabase client
│   │   │   ├── models.py             # Pydantic models (Ontology)
│   │   │   ├── heartbeat.py          # Heartbeat logic
│   │   │   └── utils.py              # SHA256, logging setup
│   │   ├── scrapers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py               # Abstract scraper class
│   │   │   ├── quebec.py             # Quebec scraper
│   │   │   ├── alberta.py            # Alberta scraper
│   │   │   ├── ontario.py            # Ontario scraper
│   │   │   └── manitoba.py           # Manitoba scraper
│   │   └── auto_researcher.py        # Comparability logic
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py               # Pytest fixtures
│       ├── test_models.py            # Ontology validation
│       ├── test_scrapers.py          # Scraper unit tests
│       └── fixtures/                 # Mock HTML responses
│
├── frontend/                         # Next.js application
│   ├── package.json
│   ├── .env.local.example
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── public/                       # Static assets
│   ├── src/
│   │   ├── app/                      # App Router pages
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx              # Homepage (map)
│   │   │   ├── methods/
│   │   │   │   └── page.tsx          # Comparability matrix
│   │   │   └── api/                  # API routes (if needed)
│   │   ├── components/
│   │   │   ├── Map.tsx               # Mapbox map
│   │   │   ├── HospitalCard.tsx      # Hospital detail modal
│   │   │   ├── ProvinceAwareBanner.tsx
│   │   │   ├── AccessBurdenEstimator.tsx
│   │   │   ├── MethodologyWarning.tsx
│   │   │   └── HeartbeatMonitor.tsx
│   │   ├── lib/
│   │   │   ├── supabase.ts           # Supabase client
│   │   │   ├── api.ts                # API functions
│   │   │   ├── comparability.ts      # Comparability logic
│   │   │   └── utils.ts
│   │   ├── types/
│   │   │   └── index.ts              # TypeScript types
│   │   └── hooks/
│   │       ├── useHospitals.ts
│   │       ├── useMeasurements.ts
│   │       └── useHeartbeat.ts
│   └── tests/
│       ├── unit/                     # Vitest
│       ├── e2e/                      # Playwright
│       └── setup.ts
│
├── database/                         # Database schema
│   ├── migrations/
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_add_heartbeat.sql
│   │   └── 003_add_indexes.sql
│   ├── seed/
│   │   ├── sources.sql               # Initial province data
│   │   └── test_hospitals.sql        # Development data
│   └── types/
│       └── enums.sql                 # PostgreSQL enums
│
├── docs/                             # Documentation
│   ├── README.md
│   ├── IMPLEMENTATION.md             # This file
│   ├── DATABASE.md
│   ├── API.md
│   └── ROADMAP.md
│
├── .gitignore
├── .pre-commit-config.yaml
├── er-times-plan.md                  # Original strategic doc
└── CLAUDE.md                         # AI assistant guidance
```

---

## Development Environment Setup

### Prerequisites

Install these tools globally:
- Python 3.12+ (`python --version`)
- Node.js 20.x LTS (`node --version`)
- pnpm 8.x (`pnpm --version` or install: `npm i -g pnpm`)
- Git

### Step 1: Clone and Environment Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/waittime-canada.git
cd waittime-canada

# Copy environment templates
cp scrapers/.env.example scrapers/.env
cp frontend/.env.local.example frontend/.env.local
```

### Step 2: Supabase Project Setup

1. Create account at https://supabase.com
2. Create new project: "waittime-canada"
3. Get credentials from Settings → API:
   - Project URL: `https://xxxxx.supabase.co`
   - Anon/Public Key: `eyJhbGc...`
   - Service Role Key: `eyJhbGc...` (for scrapers)

4. Update `.env` files:
```bash
# scrapers/.env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbGc...    # Service key (write access)

# frontend/.env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGc...    # Anon key (read-only)
```

### Step 3: Database Initialization

```bash
# Run migrations (from project root)
psql $SUPABASE_URL -f database/migrations/001_initial_schema.sql
psql $SUPABASE_URL -f database/migrations/002_add_heartbeat.sql
psql $SUPABASE_URL -f database/migrations/003_add_indexes.sql

# Seed initial data
psql $SUPABASE_URL -f database/seed/sources.sql
psql $SUPABASE_URL -f database/seed/test_hospitals.sql

# OR use Supabase CLI (recommended):
supabase db push
```

### Step 4: Scraper Setup

```bash
cd scrapers

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests to verify setup
pytest

# Run single scraper
python -m src.scrapers.quebec

# Run all scrapers
python -m src.main
```

### Step 5: Frontend Setup

```bash
cd frontend

# Install dependencies
pnpm install

# Run development server
pnpm dev

# Open http://localhost:3000
```

### Step 6: Verify Integration

1. Run scraper: `python -m src.main`
2. Check Supabase Dashboard → Table Editor → measurements (should have rows)
3. Open frontend → Should show hospitals on map
4. Click hospital → Should show wait time data

---

## Code Quality Standards

### Python (Scrapers)

**Linting & Formatting: Ruff**
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "S", "B", "A"]
ignore = ["E501"]  # Line too long (formatter handles)

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

**Type Checking: mypy**
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**Pre-commit Hooks**
```yaml
# .pre-commit-config.yaml
repos:
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
        additional_dependencies: [types-requests]
```

### TypeScript (Frontend)

**ESLint Configuration**
```json
// .eslintrc.json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended"
  ],
  "rules": {
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "error"
  }
}
```

**TypeScript Configuration**
```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "jsx": "preserve",
    "module": "esnext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  }
}
```

**Prettier Configuration**
```json
// .prettierrc
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "es5",
  "printWidth": 100,
  "tabWidth": 2
}
```

---

## Testing Strategy

### Python Tests (pytest)

**Structure:**
```
tests/
├── conftest.py              # Shared fixtures
├── test_models.py           # Pydantic model validation
├── test_scrapers.py         # Scraper logic
├── test_database.py         # Database operations
├── test_heartbeat.py        # Heartbeat logic
└── fixtures/
    ├── quebec_sample.html   # Mock HTML responses
    └── alberta_sample.html
```

**Key Test Patterns:**

```python
# tests/test_scrapers.py
import pytest
from src.scrapers.quebec import QuebecScraper
from src.core.models import Measurement

@pytest.fixture
def quebec_html():
    """Load fixture HTML"""
    with open("tests/fixtures/quebec_sample.html") as f:
        return f.read()

def test_quebec_scraper_parses_correctly(quebec_html):
    """Quebec scraper extracts correct values and ontology"""
    scraper = QuebecScraper()
    measurements = scraper.parse(quebec_html)

    assert len(measurements) > 0
    assert measurements[0].metric_family == "TIME_TO_PROVIDER"
    assert measurements[0].start_event == "REGISTRATION"
    assert measurements[0].value > 0

def test_ontology_validation_rejects_invalid():
    """Pydantic model rejects invalid ontology values"""
    with pytest.raises(ValidationError):
        Measurement(
            hospital_id="test",
            value=100,
            metric_family="INVALID",  # Not in allowed enum
            start_event="TRIAGE",
            end_event="PHYSICIAN",
            statistic_type="P90"
        )
```

**Coverage Target:** 80%+ line coverage

```bash
pytest --cov=src --cov-report=html --cov-report=term
```

### Frontend Tests

**Unit Tests (Vitest)**
```typescript
// tests/unit/comparability.test.ts
import { describe, it, expect } from 'vitest';
import { areComparable } from '@/lib/comparability';

describe('Comparability Logic', () => {
  it('returns true for identical ontologies', () => {
    const measurementA = {
      metricFamily: 'TIME_TO_PROVIDER',
      startEvent: 'TRIAGE',
      endEvent: 'PHYSICIAN',
      statisticType: 'P90'
    };
    const measurementB = { ...measurementA };

    expect(areComparable(measurementA, measurementB)).toBe(true);
  });

  it('returns false for different start events', () => {
    const measurementA = { /* ... */ startEvent: 'TRIAGE' };
    const measurementB = { /* ... */ startEvent: 'REGISTRATION' };

    expect(areComparable(measurementA, measurementB)).toBe(false);
  });
});
```

**Component Tests (React Testing Library)**
```typescript
// tests/unit/ProvinceAwareBanner.test.tsx
import { render, screen } from '@testing-library/react';
import { ProvinceAwareBanner } from '@/components/ProvinceAwareBanner';

it('shows correct telehealth info for Quebec', () => {
  render(<ProvinceAwareBanner sourceId="ca-qc-msss" />);
  expect(screen.getByText(/Info-Santé 811/i)).toBeInTheDocument();
});

it('shows correct telehealth info for Alberta', () => {
  render(<ProvinceAwareBanner sourceId="ca-ab-ahs" />);
  expect(screen.getByText(/Health Link 811/i)).toBeInTheDocument();
});
```

**E2E Tests (Playwright)**
```typescript
// tests/e2e/map-interaction.spec.ts
import { test, expect } from '@playwright/test';

test('clicking hospital shows wait time', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Wait for map to load
  await page.waitForSelector('[data-testid="mapbox-map"]');

  // Click first hospital marker
  await page.click('[data-testid="hospital-marker"]').first();

  // Verify modal shows
  await expect(page.locator('[data-testid="hospital-modal"]')).toBeVisible();

  // Verify wait time displayed
  await expect(page.locator('[data-testid="wait-time"]')).toContainText(/\d+ minutes/);
});

test('methodology warning shown for incomparable data', async ({ page }) => {
  await page.goto('http://localhost:3000/methods');

  // Should show warning for AB vs MB comparison
  await expect(page.locator('[data-testid="divergence-warning"]')).toBeVisible();
});
```

---

## Security Considerations

### Input Validation

**Scrapers:**
- Use Pydantic models to validate all scraped data before database insert
- Never execute scraped content (no eval, exec)
- Validate URLs against allowlist before fetching

**Frontend:**
- Validate all user inputs with Zod schemas
- Sanitize any user-generated content (if added later)

### Database Security

**Row-Level Security (RLS) Policies:**
```sql
-- Public read-only access to visible hospitals
ALTER TABLE hospitals ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can view verified hospitals"
ON hospitals FOR SELECT
USING (is_visible = true AND is_verified = true);

-- Measurements readable by anyone
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public can view measurements"
ON measurements FOR SELECT
USING (true);

-- Only service role can insert (scrapers)
CREATE POLICY "Service role can insert measurements"
ON measurements FOR INSERT
WITH CHECK (auth.jwt()->>'role' = 'service_role');
```

**Parameterized Queries:**
- Supabase client automatically uses parameterized queries
- Never construct SQL strings manually

### Secrets Management

**Never commit:**
- `.env` files (use `.env.example` templates)
- API keys, database passwords
- Service role keys

**GitHub Secrets:**
```
SUPABASE_URL
SUPABASE_SERVICE_KEY
SENTRY_DSN (for error tracking)
```

**Environment Variables:**
- Development: `.env` files (gitignored)
- Production: GitHub Secrets → GitHub Actions → Supabase/Vercel

### Rate Limiting

**Scrapers:**
```python
# src/scrapers/base.py
import time
from tenacity import retry, wait_exponential, stop_after_attempt

class BaseScraper:
    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(3)
    )
    def fetch_with_backoff(self, url: str) -> str:
        time.sleep(1)  # Be respectful: 1 req/sec
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
```

**Frontend API:**
- Supabase free tier: 500 requests/sec (sufficient for MVP)
- Add Vercel rate limiting if needed:
```typescript
// middleware.ts
import { Ratelimit } from "@upstash/ratelimit";

export async function middleware(request: Request) {
  const ratelimit = new Ratelimit({
    redis: /* ... */,
    limiter: Ratelimit.slidingWindow(10, "10 s"),
  });

  const { success } = await ratelimit.limit(request.ip);
  if (!success) return new Response("Too Many Requests", { status: 429 });
}
```

---

## Performance Optimization

### Database

**Indexes:**
```sql
-- Fast lookup by hospital
CREATE INDEX idx_measurements_hospital_time
ON measurements(hospital_id, timestamp_utc DESC);

-- Fast filtering by province
CREATE INDEX idx_hospitals_province_visible
ON hospitals(province) WHERE is_visible = true;

-- Geospatial queries
CREATE INDEX idx_hospitals_location
ON hospitals USING GIST(geography(point(longitude, latitude)));
```

**Partitioning (future):**
```sql
-- Partition measurements by month for historical data
CREATE TABLE measurements_2024_01 PARTITION OF measurements
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Frontend

**Data Fetching:**
```typescript
// Use React Query for automatic caching
const { data: hospitals } = useQuery({
  queryKey: ['hospitals', province],
  queryFn: () => fetchHospitals(province),
  staleTime: 5 * 60 * 1000, // 5 minutes
  cacheTime: 30 * 60 * 1000, // 30 minutes
});
```

**Map Optimization:**
```typescript
// Cluster markers for performance
<Map
  mapboxAccessToken={token}
  clusterMaxZoom={10}
  clusterRadius={50}
>
  <Source
    type="geojson"
    data={hospitalsGeoJSON}
    cluster={true}
  >
    <Layer {...clusterLayer} />
  </Source>
</Map>
```

**Image Optimization:**
```typescript
// Use Next.js Image component
import Image from 'next/image';

<Image
  src="/province-logos/quebec.svg"
  alt="Quebec"
  width={50}
  height={50}
  loading="lazy"
/>
```

---

## Error Handling & Observability

### Structured Logging

**Scrapers:**
```python
# src/core/utils.py
import structlog

logger = structlog.get_logger()

# In scraper:
logger.info(
    "scraper_run_complete",
    scraper="quebec",
    hospitals_scraped=25,
    measurements_created=150,
    duration_seconds=12.4
)

logger.error(
    "scraper_failed",
    scraper="quebec",
    error=str(e),
    hospital_id="ca-qc-chum"
)
```

**Frontend:**
```typescript
// src/lib/logger.ts
export const logger = {
  error: (message: string, context: Record<string, unknown>) => {
    console.error(message, context);
    Sentry.captureException(new Error(message), { extra: context });
  },
  info: (message: string, context: Record<string, unknown>) => {
    console.log(message, context);
  }
};
```

### Error Tracking (Sentry)

```python
# scrapers/src/main.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment="production",
    traces_sample_rate=0.1,
)

try:
    run_all_scrapers()
except Exception as e:
    sentry_sdk.capture_exception(e)
    raise
```

```typescript
// frontend/src/app/layout.tsx
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
});
```

### Heartbeat Monitoring

**Scraper Side:**
```python
# src/core/heartbeat.py
from datetime import datetime
from supabase import Client

def write_heartbeat(client: Client, scraper_id: str, status: str = "healthy"):
    client.table("scraper_status").upsert({
        "scraper_id": scraper_id,
        "last_run": datetime.utcnow().isoformat(),
        "status": status
    }).execute()
```

**Frontend Side:**
```typescript
// src/hooks/useHeartbeat.ts
export function useHeartbeat() {
  return useQuery({
    queryKey: ['heartbeat'],
    queryFn: async () => {
      const { data } = await supabase
        .from('scraper_status')
        .select('*')
        .order('last_run', { ascending: false })
        .limit(1)
        .single();

      const minutesAgo = differenceInMinutes(new Date(), new Date(data.last_run));
      return {
        status: minutesAgo > 60 ? 'unhealthy' : 'healthy',
        lastRun: data.last_run,
        minutesAgo
      };
    },
    refetchInterval: 60000 // Check every minute
  });
}
```

**Display:**
```typescript
// src/components/HeartbeatMonitor.tsx
export function HeartbeatMonitor() {
  const { data } = useHeartbeat();

  return (
    <div className={data?.status === 'healthy' ? 'text-green-600' : 'text-red-600'}>
      Last Audit: {data?.minutesAgo} mins ago
      {data?.status === 'unhealthy' && ' ⚠️ Data may be stale'}
    </div>
  );
}
```

---

## Next Steps

After setting up your development environment:

1. Review [DATABASE.md](./DATABASE.md) for complete schema details
2. Review [API.md](./API.md) for endpoint specifications
3. Follow [ROADMAP.md](./ROADMAP.md) for week-by-week implementation

## Questions or Issues?

- Check [../er-times-plan.md](../er-times-plan.md) for strategic context
- Reference [../CLAUDE.md](../CLAUDE.md) for codebase guidance
- Review risk mitigations in strategic plan Part 6
