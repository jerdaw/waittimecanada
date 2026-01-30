# WaitTime Canada - Backend

Provincial ER wait time scrapers and core domain models.

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Project Structure

```
backend/
├── src/waittime/          # Main package
│   ├── core/              # Domain models and ontology
│   ├── scrapers/          # Provincial data scrapers
│   ├── services/          # Business logic
│   └── cli/               # Command-line interface
├── tests/                 # Test suite
│   ├── unit/              # Fast, no I/O
│   ├── integration/       # Database, HTTP
│   └── e2e/               # Full workflows
└── migrations/            # Database migrations
```

## Running Tests

```bash
# All tests
pytest

# Unit tests only (fast)
pytest -m unit

# With coverage report
pytest --cov=src/waittime --cov-report=html
```

## Code Quality

```bash
# Lint and format
ruff check src/ tests/
ruff format src/ tests/

# Type checking
mypy src/
```

## Core Concepts

### Metric Ontology

Every measurement is tagged with ontology fields that describe its methodology:

- **metric_family**: What is being measured (TIME_TO_PROVIDER, TOTAL_LOS)
- **start_event**: When the clock starts (TRIAGE, REGISTRATION, DOOR)
- **end_event**: When the clock stops (PHYSICIAN, PROVIDER, DISCHARGE)
- **statistic_type**: How value is calculated (P90, MEAN, ROLLING_AVG)

Two measurements are **comparable** only if all four fields match.

See [ADR-0002](../docs/adr/0002-metric-ontology.md) for the full rationale.
