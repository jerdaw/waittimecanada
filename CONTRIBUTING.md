# Contributing to WaitTime Canada

Thank you for your interest in contributing to WaitTime Canada! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Standards](#code-standards)
5. [Testing Requirements](#testing-requirements)
6. [Documentation](#documentation)
7. [Submitting Changes](#submitting-changes)
8. [Architecture Decision Records](#architecture-decision-records)

---

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

---

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 20.x LTS
- pnpm 8.x
- Git
- A Neon account (for database access)

### Initial Setup

1. **Fork and Clone**

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/waittime-canada.git
cd waittime-canada
```

2. **Install Dependencies**

```bash
# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Frontend
cd ../frontend
pnpm install

# Install pre-commit hooks (run from project root)
cd ..
pre-commit install
```

3. **Set Up Environment**

```bash
# Copy environment templates
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local

# Edit with your credentials
# You'll need Neon DATABASE_URL
```

4. **Verify Setup**

```bash
# Run backend tests
cd backend && pytest

# Run frontend tests
cd ../frontend && pnpm test

# Serve docs locally
mkdocs serve
```

---

## Development Workflow

### Branching Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/descriptive-name` - Feature branches
- `fix/descriptive-name` - Bug fix branches
- `docs/descriptive-name` - Documentation updates

### Creating a Feature

1. **Create a branch from `develop`**

```bash
git checkout develop
git pull origin develop
git checkout -b feature/add-ontario-scraper
```

2. **Make changes following code standards**

3. **Write tests** (see Testing Requirements below)

4. **Run quality checks**

```bash
# Backend
cd backend
ruff check src/
ruff format src/
mypy src/
pytest

# Frontend
cd frontend
pnpm lint
pnpm format:check
pnpm type-check
pnpm test
```

5. **Commit with conventional commits**

```bash
git add .
git commit -m "feat(scrapers): add Ontario scraper

- Parse Ontario health data portal
- Tag with TRIAGE start event
- Add tests with mock HTML fixtures

Closes #42"
```

**Conventional Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

6. **Push and create Pull Request**

```bash
git push origin feature/add-ontario-scraper
# Create PR on GitHub targeting `develop` branch
```

---

## Code Standards

### Python (Backend)

**Linting & Formatting:**
- Use Ruff for both linting and formatting
- Max line length: 100 characters
- Configuration in `backend/pyproject.toml`

**Type Hints:**
- All functions must have type hints
- Use `mypy` in strict mode
- No `Any` types without justification

**Example:**

```python
from waittime.core.models import Measurement
from waittime.scrapers.base import BaseScraper

class OntarioScraper(BaseScraper):
    """Scraper for Ontario health data portal."""

    def parse(self, html: str) -> list[Measurement]:
        """Parse Ontario HTML into measurements.

        Args:
            html: Raw HTML from Ontario data portal

        Returns:
            List of validated Measurement objects

        Raises:
            ValueError: If HTML structure is unexpected
        """
        # Implementation
        ...
```

### TypeScript (Frontend)

**Linting & Formatting:**
- ESLint for linting
- Prettier for formatting
- TypeScript strict mode enabled

**Component Structure:**

```typescript
// Use named exports for components
export function HospitalCard({ hospital }: HospitalCardProps) {
  // Implementation
}

// Define prop types
interface HospitalCardProps {
  hospital: Hospital;
  onSelect?: (id: string) => void;
}
```

**Hooks:**

```typescript
// Custom hooks start with 'use'
export function useHospitals(province?: string) {
  return useQuery({
    queryKey: ['hospitals', province],
    queryFn: () => fetchHospitals(province),
    staleTime: 5 * 60 * 1000,
  });
}
```

### SQL

**Migrations:**
- Sequential numbering: `001_initial_schema.sql`
- Descriptive names
- Include both up and rollback (in comments)
- Test locally before committing

**Example:**

```sql
-- 004_add_alert_thresholds.sql
-- Add configurable alert thresholds for hospitals

CREATE TABLE alert_thresholds (
    hospital_id TEXT PRIMARY KEY REFERENCES hospitals(id),
    warning_threshold INTEGER NOT NULL DEFAULT 120,  -- minutes
    critical_threshold INTEGER NOT NULL DEFAULT 240,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rollback:
-- DROP TABLE alert_thresholds;
```

---

## Testing Requirements

### Backend Tests

**Test Organization:**

```
backend/tests/
├── unit/              # Fast, no I/O
├── integration/       # Database, HTTP
└── e2e/              # Full workflows
```

**Markers:**

```python
import pytest

@pytest.mark.unit
def test_comparability_logic():
    """Unit test for comparability (fast, no I/O)."""
    ...

@pytest.mark.integration
def test_database_insert():
    """Integration test with real database."""
    ...

@pytest.mark.e2e
@pytest.mark.slow
def test_full_scrape():
    """End-to-end test (slow, hits real APIs)."""
    ...
```

**Coverage Requirement:** 80%+ overall

Run tests:

```bash
# All tests
pytest

# Unit tests only (default)
pytest -m unit

# Integration tests
pytest -m integration

# With coverage
pytest --cov=src --cov-report=html
```

### Frontend Tests

**Test Organization:**

```
frontend/tests/
├── unit/              # Component tests (Vitest)
└── e2e/              # E2E tests (Playwright)
```

**Component Test Example:**

```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('HeartbeatMonitor', () => {
  it('shows healthy status when recent', () => {
    render(<HeartbeatMonitor lastRun={new Date()} />);
    expect(screen.getByText(/healthy/i)).toBeInTheDocument();
  });
});
```

**E2E Test Example:**

```typescript
import { test, expect } from '@playwright/test';

test('user can view hospital details', async ({ page }) => {
  await page.goto('/');
  await page.click('[data-testid="hospital-marker"]').first();
  await expect(page.locator('[data-testid="hospital-modal"]')).toBeVisible();
});
```

Run tests:

```bash
# Unit tests
pnpm test

# E2E tests
pnpm test:e2e

# E2E with UI
pnpm test:e2e:ui
```

---

## Documentation

### When to Update Docs

- **Always:** When adding new features
- **Always:** When changing APIs or database schema
- **Always:** When making architectural decisions (create ADR)
- **Recommended:** When fixing non-trivial bugs (troubleshooting guide)

### Documentation Types

**MkDocs Pages:**
- Guides: How-to documentation (`docs/guides/`)
- Architecture: System design (`docs/architecture/`)
- Reference: API specs, schema (`docs/reference/`)

**ADRs:**
- Significant architectural decisions
- Use template in `docs/adr/template.md`
- See "Architecture Decision Records" section below

**Code Comments:**
- Docstrings for all public functions/classes
- Inline comments for complex logic only
- Avoid obvious comments

**Example:**

```python
def calculate_comparability_score(
    measurement_a: Measurement,
    measurement_b: Measurement
) -> float:
    """Calculate comparability score between two measurements.

    The score ranges from 0.0 (completely incomparable) to 1.0
    (identical methodology). Partial matches receive intermediate scores.

    Args:
        measurement_a: First measurement to compare
        measurement_b: Second measurement to compare

    Returns:
        Comparability score between 0.0 and 1.0

    Example:
        >>> score = calculate_comparability_score(qc_measurement, ab_measurement)
        >>> print(f"Comparability: {score:.0%}")
        Comparability: 50%
    """
    # Implementation
    ...
```

### Building Docs Locally

```bash
# Serve with live reload
mkdocs serve

# Build static site
mkdocs build

# Deploy to GitHub Pages (maintainers only)
mkdocs gh-deploy
```

---

## Submitting Changes

### Pull Request Process

1. **Ensure all checks pass:**
   - All tests passing
   - Code coverage ≥ 80%
   - Linting/formatting clean
   - Type checking passes
   - Docs build successfully

2. **Fill out PR template:**
   - Description of changes
   - Related issues
   - Testing performed
   - Screenshots (if UI changes)

3. **Request review:**
   - Tag relevant reviewers
   - Respond to feedback promptly
   - Make requested changes in new commits (don't force-push)

4. **After approval:**
   - Squash commits if requested
   - Merge to `develop`
   - Delete feature branch

### Review Criteria

Reviewers will check:

- **Functionality:** Does it work as intended?
- **Tests:** Adequate test coverage?
- **Code Quality:** Follows standards?
- **Documentation:** Updated appropriately?
- **Architecture:** Consistent with existing patterns?
- **Security:** No vulnerabilities introduced?
- **Performance:** No obvious performance issues?

---

## Architecture Decision Records

When making significant architectural decisions, create an ADR:

### When to Create an ADR

- Choosing between multiple technology options
- Changing core data models
- Adopting new patterns or frameworks
- Making trade-offs that future contributors should understand

### How to Create an ADR

1. **Copy template:**

```bash
cp docs/adr/template.md docs/adr/0004-your-decision.md
```

2. **Fill in template:**
   - Context and problem statement
   - Decision drivers (requirements, constraints)
   - Options considered
   - Decision and rationale
   - Consequences (positive and negative)

3. **Update index:**

Edit `docs/adr/index.md` to add your ADR to the table.

4. **Submit with PR:**

ADRs are submitted via pull request like code changes.

### Example ADRs

See existing ADRs for examples:
- [ADR-0001: Use Neon PostgreSQL](docs/adr/0001-use-neon.md)
- [ADR-0002: Metric Ontology](docs/adr/0002-metric-ontology.md)
- [ADR-0003: Serverless Scrapers](docs/adr/0003-serverless-scrapers.md)

---

## Common Tasks

### Adding a New Province Scraper

1. Create scraper file: `backend/src/waittime/scrapers/province_name.py`
2. Extend `BaseScraper` class
3. Implement `parse()` method
4. Tag with correct ontology values
5. Add tests with mock HTML fixtures
6. Add source to database seed
7. Register scraper in `backend/src/waittime/scrapers/__init__.py`
8. Update documentation: `docs/guides/adding-province.md`

### Creating a Database Migration

1. Create file: `backend/migrations/XXX_description.sql`
2. Write migration SQL
3. Add rollback SQL in comments
4. Test locally: `psql $SUPABASE_URL -f backend/migrations/XXX_description.sql`
5. Update `docs/architecture/database.md` if schema changes
6. Create PR - migrations auto-apply on merge to `main`

### Adding a New API Endpoint

1. Define TypeScript types in `frontend/src/types/`
2. Create API function in `frontend/src/lib/api.ts`
3. Create React Query hook in `frontend/src/hooks/`
4. Update `docs/architecture/api.md`
5. Add tests for new endpoint

---

## Getting Help

- **Documentation:** Check [docs/](docs/) first
- **Issues:** Search existing issues before creating new one
- **Discussions:** Use GitHub Discussions for questions
- **Discord:** [Coming soon]

---

## Recognition

Contributors will be recognized in:
- `CHANGELOG.md` for each release
- GitHub contributors page
- README.md acknowledgments section

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (MIT License).

---

Thank you for contributing to WaitTime Canada! 🎉
