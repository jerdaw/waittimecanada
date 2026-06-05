# Integration Testing Guide

## Overview

Integration tests verify the full stack of Wait Time Canada with real database interactions. Unlike unit tests that use mocks, integration tests connect to a real PostgreSQL database to ensure the entire system works correctly.

## Test Coverage

Integration tests cover:
- **DatabaseService** - Full CRUD operations with real database
- **HeartbeatService** - Recording and checking scraper health
- **ComparisonService** - Comparing hospitals end-to-end
- **Scrapers** - Discovering hospitals and writing measurements
- **Data cleanup** - Age statistics and retention queries
- **Visibility filtering** - Ensuring unverified/hidden hospitals don't appear

## Running Integration Tests

### Prerequisites

1. **PostgreSQL Database**: You need access to a PostgreSQL database
   - Recommended: Create a separate test database
   - Alternative: Use a local PostgreSQL instance

2. **Environment Variable**: Set `DATABASE_URL` with connection string
   ```bash
   export DATABASE_URL="postgresql://user@host/database"
   ```

### Run All Integration Tests

```bash
# Run only integration tests
uv run pytest -m integration

# Run integration tests with verbose output
uv run pytest -m integration -v

# Run integration tests with coverage
uv run pytest -m integration --cov=src/waittime
```

### Run Specific Integration Test Files

```bash
# Test database operations
uv run pytest tests/integration/test_database_integration.py -v

# Test scraper integration
uv run pytest tests/integration/test_scraper_integration.py -v
```

### Skip Integration Tests

If you don't have a database available, integration tests will be automatically skipped:

```bash
# Run all tests except integration tests
uv run pytest -m "not integration"
```

## Test Database Setup

### Option 1: Use Hosted PostgreSQL Test Database (Recommended)

1. Create a dedicated hosted test database called `waittimecanada_test`
2. Copy the connection string
3. Set environment variable:
   ```bash
   export DATABASE_URL="postgresql://user@host/waittimecanada_test"
   ```

### Option 2: Use Local PostgreSQL

1. Install PostgreSQL locally
2. Create test database:
   ```bash
   createdb waittimecanada_test
   ```
3. Set environment variable:
   ```bash
   export DATABASE_URL="postgresql://localhost/waittimecanada_test"
   ```

### Option 3: Use Docker PostgreSQL

```bash
# Start PostgreSQL container
docker run -d \
  --name waittime-test-db \
  -e POSTGRES_PASSWORD=testpass \
  -e POSTGRES_DB=waittimecanada_test \
  -p 5432:5432 \
  postgres:17

# Set environment variable
export DATABASE_URL="postgresql://postgres@localhost:5432/waittimecanada_test"

# Stop and remove when done
docker stop waittime-test-db
docker rm waittime-test-db
```

## Test Isolation

Integration tests use two strategies to maintain isolation:

### 1. Transaction Rollback (Default)

The `db_transaction` fixture wraps each test in a transaction that rolls back after the test:

```python
def test_example(db_transaction: DatabaseService):
    # Any database changes here will be rolled back
    db_transaction.insert_hospital(...)
    # Test assertions
    # Automatic rollback after test
```

**Pros:**
- Fast (no actual database cleanup needed)
- Perfect isolation
- No impact on database state

**Cons:**
- Slightly more complex fixture setup
- Doesn't test transaction commit behavior

### 2. Clean Database (Explicit Cleanup)

The `clean_database` fixture clears test data before and after:

```python
def test_example(clean_database: DatabaseService):
    # Database is clean at start
    clean_database.insert_hospital(...)
    # Test assertions
    # Cleanup happens after test
```

**Pros:**
- Tests actual database commit
- Simpler to understand

**Cons:**
- Slower (requires DELETE queries)
- Requires test data to use `test-` prefix

## Test Data Naming Convention

**All test data MUST use `test-` prefix:**

```python
# Good
hospital_id = "test-hospital-123"
source_id = "test-source-qc"

# Bad
hospital_id = "ca-qc-montreal-chum"  # Could conflict with real data
```

The `clean_database` fixture automatically cleans up any data with `test-` prefix.

## Integration Test Fixtures

### `database_url`
Returns `DATABASE_URL` from environment. Skips tests if not set.

### `db_service`
Session-scoped DatabaseService instance. Reused across all tests.

### `db_transaction`
Function-scoped fixture with transaction rollback. Use for most tests.

### `clean_database`
Function-scoped fixture with explicit cleanup. Use when testing commits.

## Example Integration Test

```python
import pytest
from waittime.core import Hospital, Source
from waittime.services.database import DatabaseService


@pytest.mark.integration
def test_hospital_workflow(clean_database: DatabaseService):
    """Test complete hospital discovery and verification workflow."""
    db = clean_database

    # 1. Scraper discovers hospital
    source = Source(
        id="test-source-example",
        name="Test Source",
        province="ON",
        # ... other fields
    )
    db.insert_source(source)

    hospital = Hospital(
        id="test-hospital-example",
        name="Example Hospital",
        province="ON",
        city="Toronto",
        latitude=43.6532,
        longitude=-79.3832,
        source_id="test-source-example",
        is_verified=False,
        is_visible=False,
    )
    db.insert_hospital(hospital)

    # 2. Admin verifies hospital
    verified = db.verify_hospital("test-hospital-example", make_visible=True)

    # 3. Assert hospital is now public
    assert verified.is_verified is True
    assert verified.is_visible is True

    public_hospitals = db.get_hospitals()
    test_ids = [h.id for h in public_hospitals if h.id.startswith("test-")]
    assert "test-hospital-example" in test_ids
```

## Continuous Integration

### GitHub Actions

The default blocking backend workflow does **not** currently provision a
database-backed integration lane on every push or PR. Use the example below
only if you intentionally add a dedicated opt-in integration workflow or a
separate CI lane with a real test database:

```yaml
# .github/workflows/integration-tests.yml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv
        run: pip install uv

      - name: Install dependencies
        run: uv pip install -e ".[dev]"

      - name: Run integration tests
        env:
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
        run: uv run pytest -m integration -v
```

**Note:** Store `TEST_DATABASE_URL` as a GitHub secret pointing to a dedicated test database.

## Common Issues

### Issue: "DATABASE_URL not set, skipping integration tests"

**Solution:** Set the environment variable:
```bash
export DATABASE_URL="postgresql://user@host/database"
```

### Issue: "relation 'hospitals' does not exist"

**Solution:** Run database migrations to create tables. See `/backend/scripts/migrate-structure.sh`

### Issue: Tests fail with "duplicate key value violates unique constraint"

**Solution:**
- Ensure you're using `test-` prefix for all test data
- Use `clean_database` fixture to ensure cleanup
- Check that previous test run cleaned up properly

### Issue: Tests are very slow

**Solution:**
- Use `db_transaction` fixture instead of `clean_database` for faster tests
- Run fewer integration tests in development
- Use local PostgreSQL instead of a remote database for faster network

## Best Practices

1. **Use `test-` prefix** for all test data
2. **Prefer `db_transaction`** for faster tests
3. **Keep tests independent** - don't rely on data from other tests
4. **Test realistic scenarios** - integration tests should mirror production workflows
5. **Don't test implementation details** - test the public API, not internals
6. **Clean up external resources** - close connections, cleanup temp files
7. **Use separate test database** - never run integration tests against production

## Test Statistics

Current integration coverage changes over time. Treat the files under
`backend/tests/integration/` plus local pytest output as the source of truth
instead of relying on a fixed test-count claim in this document.

Typical characteristics:
- database and scraper workflows are covered
- tests run fastest against a local PostgreSQL instance
- `DATABASE_URL` is still required, otherwise the integration lane skips

## Future Improvements

Potential enhancements:
- [ ] Add integration tests for frontend API endpoints
- [ ] Test database connection pooling under load
- [ ] Add integration tests for geocoding service
- [ ] Test concurrent scraper runs
- [ ] Add performance benchmarks for database queries
- [ ] Test database migration scripts
- [ ] Add integration tests for data export/import

---

*Last Updated: February 1, 2026*
*Part of Task #8 - Integration Tests Implementation*
