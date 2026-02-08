# Milestone 13: Aggregation Pipeline

> Archived plan (historical reference). Milestone delivered and closed.

> **Priority:** CRITICAL - Foundational infrastructure for all research/analytics features
> **Estimated Effort:** 4-5 days
> **Admissions Appeal:** Scholar (longitudinal research), Professional (data stewardship), Leader (systems thinking)
> **Dependencies:** None (builds on existing measurements table)
> **Blocks:** M14 (Data Quality), M15 (Analytics & Benchmarking)

---

## Overview

The aggregation pipeline computes and permanently stores hourly, daily, weekly, and monthly summary statistics per hospital. This solves the fundamental tension between the 30-day raw measurement retention policy (necessary for storage) and the need for long-term trend analysis (necessary for research credibility).

**Without this:** The project is a real-time snapshot tool with no historical memory.
**With this:** The project becomes a genuine health systems observatory with longitudinal analysis capability.

**Narrative for Applications:**
> "I designed a two-tier data architecture: raw measurements with a 30-day retention window for operational freshness, and permanent statistical aggregates for longitudinal research. This mirrors how real clinical data warehouses balance storage constraints with analytical needs."

---

## Phase 1: Database Schema (Day 1)

### 1.1 New Table: `measurement_aggregates`

**SQL Migration:**

```sql
CREATE TABLE measurement_aggregates (
    id SERIAL PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    source_id TEXT NOT NULL REFERENCES sources(id),

    -- Time period
    period_type TEXT NOT NULL CHECK (period_type IN ('hourly', 'daily', 'weekly', 'monthly')),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Summary statistics
    mean_value DOUBLE PRECISION NOT NULL,
    median_value DOUBLE PRECISION,
    p90_value DOUBLE PRECISION,
    min_value DOUBLE PRECISION NOT NULL,
    max_value DOUBLE PRECISION NOT NULL,
    std_dev DOUBLE PRECISION,
    sample_count INTEGER NOT NULL CHECK (sample_count > 0),

    -- Ontology tags (inherited from source at time of aggregation)
    metric_family TEXT NOT NULL,
    start_event TEXT NOT NULL,
    end_event TEXT NOT NULL,
    statistic_type TEXT NOT NULL,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Prevent duplicate aggregates for same hospital+period
    UNIQUE (hospital_id, period_type, period_start)
);

-- Performance indexes
CREATE INDEX idx_aggregates_hospital_period
    ON measurement_aggregates (hospital_id, period_type, period_start DESC);

CREATE INDEX idx_aggregates_period_type_start
    ON measurement_aggregates (period_type, period_start DESC);

CREATE INDEX idx_aggregates_source
    ON measurement_aggregates (source_id, period_type, period_start DESC);
```

**Important Notes:**
- No retention policy on this table - aggregates are permanent
- The `UNIQUE` constraint prevents recomputing the same period
- Ontology tags are denormalized here intentionally - if a source changes methodology, historical aggregates preserve what the methodology *was* at that time
- `median_value`, `p90_value`, and `std_dev` are nullable because some periods may have too few samples to compute them meaningfully

### 1.2 Add Pydantic Model

**File:** `backend/src/waittime/core/models.py`

Add to existing models:

```python
class MeasurementAggregate(BaseModel):
    """Aggregated statistics for a hospital over a time period."""
    hospital_id: str
    source_id: str
    period_type: str  # 'hourly', 'daily', 'weekly', 'monthly'
    period_start: datetime
    period_end: datetime
    mean_value: float
    median_value: float | None = None
    p90_value: float | None = None
    min_value: float
    max_value: float
    std_dev: float | None = None
    sample_count: int
    metric_family: str
    start_event: str
    end_event: str
    statistic_type: str
    created_at: datetime | None = None
```

Export from `waittime/core/__init__.py`.

### 1.3 Tests for Schema

**File:** `backend/tests/unit/test_aggregate_models.py`

Test:
- MeasurementAggregate model creation with valid data
- Validation: `sample_count` must be > 0
- Validation: `period_type` must be one of the allowed values
- `period_end` must be after `period_start`
- Nullable fields (median, p90, std_dev) work correctly

---

## Phase 2: AggregationService (Day 2-3)

### 2.1 Service Implementation

**File:** `backend/src/waittime/services/aggregation.py`

```python
"""Service for computing and storing measurement aggregates."""

import logging
import statistics
from datetime import datetime, timedelta, timezone

from waittime.core import MeasurementAggregate
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class AggregationService:
    """Computes and stores permanent statistical aggregates from raw measurements."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def aggregate_hourly(self, hospital_id: str, hour_start: datetime) -> MeasurementAggregate | None:
        """
        Compute aggregate statistics for a single hospital for a 1-hour window.

        Args:
            hospital_id: Hospital to aggregate
            hour_start: Start of the hour (must be on the hour, e.g., 14:00:00)

        Returns:
            MeasurementAggregate if data exists, None if no measurements in window
        """
        # 1. Query raw measurements for this hospital in the hour window
        # 2. If no measurements, return None
        # 3. Compute: mean, median, p90, min, max, std_dev, count
        # 4. Get ontology tags from the source
        # 5. Return MeasurementAggregate (do NOT save yet - caller decides)
        pass

    def aggregate_daily(self, hospital_id: str, date: datetime) -> MeasurementAggregate | None:
        """Compute aggregate for a full day (00:00 to 23:59:59)."""
        pass

    def aggregate_weekly(self, hospital_id: str, week_start: datetime) -> MeasurementAggregate | None:
        """Compute aggregate for a full week (Monday to Sunday)."""
        pass

    def aggregate_monthly(self, hospital_id: str, year: int, month: int) -> MeasurementAggregate | None:
        """Compute aggregate for a full calendar month."""
        pass

    def save_aggregate(self, aggregate: MeasurementAggregate) -> bool:
        """
        Save an aggregate to the database. Uses INSERT ... ON CONFLICT DO NOTHING
        to skip already-computed periods.

        Returns:
            True if inserted, False if already existed
        """
        pass

    def backfill(
        self,
        hospital_id: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        period_types: list[str] | None = None,
    ) -> dict:
        """
        Backfill missing aggregates for a hospital or all hospitals.

        Args:
            hospital_id: Specific hospital, or None for all
            start_date: Start of backfill range (default: earliest measurement)
            end_date: End of backfill range (default: now)
            period_types: Which periods to compute (default: all)

        Returns:
            Dict with counts: {'hourly': 48, 'daily': 2, 'weekly': 0, 'monthly': 0}
        """
        # 1. Get list of hospitals to process
        # 2. For each hospital, determine date range
        # 3. For each period type, iterate through periods
        # 4. Skip periods that already have aggregates (query existing)
        # 5. Compute and save each aggregate
        # 6. Return summary counts
        pass

    def get_aggregates(
        self,
        hospital_id: str,
        period_type: str,
        start: datetime,
        end: datetime,
    ) -> list[MeasurementAggregate]:
        """Query stored aggregates for a hospital and time range."""
        pass

    def get_latest_aggregate(
        self,
        hospital_id: str,
        period_type: str = "daily",
    ) -> MeasurementAggregate | None:
        """Get the most recent aggregate for a hospital."""
        pass

    @staticmethod
    def _compute_statistics(values: list[float]) -> dict:
        """
        Compute summary statistics from a list of values.

        Returns:
            Dict with keys: mean, median, p90, min, max, std_dev, count
            median/p90/std_dev are None if fewer than 3 samples
        """
        if not values:
            return None

        result = {
            'mean': statistics.mean(values),
            'min': min(values),
            'max': max(values),
            'count': len(values),
            'median': None,
            'p90': None,
            'std_dev': None,
        }

        if len(values) >= 3:
            result['median'] = statistics.median(values)
            result['std_dev'] = statistics.stdev(values)
            # P90: 90th percentile
            sorted_values = sorted(values)
            p90_index = int(len(sorted_values) * 0.9)
            result['p90'] = sorted_values[min(p90_index, len(sorted_values) - 1)]

        return result
```

### 2.2 DatabaseService Extensions

**File:** `backend/src/waittime/services/database.py`

Add these methods to the existing `DatabaseService`:

```python
def get_measurements_in_range(
    self, hospital_id: str, start: datetime, end: datetime
) -> list[dict]:
    """Get raw measurements for a hospital within a time range."""
    # SELECT value, timestamp_utc FROM measurements
    # WHERE hospital_id = %s AND timestamp_utc >= %s AND timestamp_utc < %s
    # ORDER BY timestamp_utc
    pass

def insert_aggregate(self, aggregate: MeasurementAggregate) -> bool:
    """Insert aggregate, returning False if duplicate (ON CONFLICT DO NOTHING)."""
    pass

def get_aggregates(
    self, hospital_id: str, period_type: str, start: datetime, end: datetime
) -> list[dict]:
    """Query aggregates for a hospital, period type, and time range."""
    pass

def get_existing_aggregate_periods(
    self, hospital_id: str, period_type: str, start: datetime, end: datetime
) -> set[datetime]:
    """Return set of period_start values that already have aggregates.
    Used by backfill to skip already-computed periods."""
    pass

def get_all_hospital_ids(self) -> list[str]:
    """Return all hospital IDs (verified and visible)."""
    pass
```

### 2.3 Tests

**File:** `backend/tests/unit/test_aggregation_service.py`

Test cases:
- `test_compute_statistics_basic` - mean, min, max, count for simple list
- `test_compute_statistics_median_p90` - verify median and p90 calculations
- `test_compute_statistics_few_samples` - <3 samples: median/p90/std_dev should be None
- `test_compute_statistics_empty` - empty list returns None
- `test_compute_statistics_single_value` - single value: mean=min=max=value
- `test_aggregate_hourly_with_data` - mock DB returns measurements, verify aggregate
- `test_aggregate_hourly_no_data` - mock DB returns empty, verify None returned
- `test_aggregate_daily` - verify full-day window
- `test_save_aggregate_new` - mock DB insert succeeds
- `test_save_aggregate_duplicate` - mock DB returns False (already exists)
- `test_backfill_single_hospital` - verify correct periods iterated
- `test_backfill_skips_existing` - verify already-computed periods are skipped

**File:** `backend/tests/integration/test_aggregation_integration.py`

Test cases (require database):
- `test_full_aggregation_cycle` - insert measurements, aggregate, verify stored correctly
- `test_backfill_idempotent` - running backfill twice produces same results
- `test_aggregates_survive_cleanup` - run cleanup, verify aggregates still exist

---

## Phase 3: CLI Tool (Day 3-4)

### 3.1 Aggregate CLI

**File:** `backend/src/waittime/cli/aggregate.py`

```python
"""CLI tool for computing measurement aggregates."""

# Usage:
#   python -m waittime.cli.aggregate --backfill --days 30
#   python -m waittime.cli.aggregate --incremental
#   python -m waittime.cli.aggregate --hospital ca-on-ottawa-civic --period daily
#   python -m waittime.cli.aggregate --dry-run

# Arguments:
#   --backfill          Compute all missing aggregates for specified range
#   --incremental       Only compute aggregates for periods since last run
#   --hospital ID       Process specific hospital (default: all)
#   --period TYPE       Period type: hourly, daily, weekly, monthly (default: all)
#   --days N            How far back to look for backfill (default: 30)
#   --dry-run           Show what would be computed without saving
#   --verbose           Show detailed progress
```

### 3.2 Integrate with Cleanup

**Modify:** `backend/src/waittime/cli/cleanup.py`

The cleanup flow should become:
1. Run aggregation for any un-aggregated periods in the retention window
2. Then delete raw measurements older than retention period
3. This ensures no data is lost - aggregates are computed before raw rows are deleted

```python
# In cleanup.py main():
# 1. First, aggregate any periods that haven't been aggregated yet
# 2. Then proceed with existing cleanup logic
```

### 3.3 GitHub Action Update

**Modify:** `.github/workflows/scraper-cron.yml` (or create new workflow)

Add aggregation step after scraper runs:

```yaml
- name: Aggregate measurements
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    cd backend
    python -m waittime.cli.aggregate --incremental

- name: Cleanup old measurements
  env:
    DATABASE_URL: ${{ secrets.DATABASE_URL }}
  run: |
    cd backend
    python -m waittime.cli.cleanup --retention-days 30
```

### 3.4 Tests

**File:** `backend/tests/unit/test_aggregate_cli.py`

Test cases:
- `test_backfill_flag` - verify --backfill triggers backfill method
- `test_incremental_flag` - verify --incremental computes only recent periods
- `test_dry_run` - verify no database writes in dry-run mode
- `test_specific_hospital` - verify --hospital filters correctly
- `test_specific_period` - verify --period filters correctly

---

## Phase 4: Update Data Export API (Day 4)

### 4.1 Enhance `/api/export` Endpoint

**Modify:** `frontend/app/api/export/route.ts`

Add support for aggregated data:

- New query parameter: `granularity` = `raw` | `hourly` | `daily` | `weekly` | `monthly`
- Default behavior:
  - If date range is <=30 days: serve raw measurements (existing behavior)
  - If date range is >30 days: automatically serve daily aggregates
- When serving aggregates, include additional columns: `mean_value`, `median_value`, `p90_value`, `min_value`, `max_value`, `sample_count`, `std_dev`
- JSON metadata should indicate whether data is raw or aggregated

**Response columns for aggregated data:**
```csv
period_start,period_end,hospital_id,hospital_name,province,city,latitude,longitude,mean_wait_minutes,median_wait_minutes,p90_wait_minutes,min_wait_minutes,max_wait_minutes,sample_count,std_dev,metric_family,start_event,end_event,statistic_type,source_id,methodology_url
```

### 4.2 Enhance Frontend DataExport Component

**Modify:** `frontend/components/DataExport.tsx`

- Add granularity selector (Raw, Hourly, Daily, Weekly, Monthly)
- Show info text: "Raw data available for last 30 days. Aggregated data available for all time."
- Add new date range options: 90d, 6m, 1y, All
- When granularity is not "raw", disable date ranges <= 30 days (or auto-suggest appropriate granularity)

### 4.3 Tests

**Frontend tests for DataExport updates:**
- Test granularity selector renders
- Test granularity is passed as query parameter
- Test info text appears when aggregate granularity selected
- Test new date range options appear

---

## Phase 5: Trend API Enhancement (Day 4-5)

### 5.1 Update Trend Endpoint

**Modify:** `frontend/app/api/hospitals/[slug]/trends/route.ts`

- Add new period options: `90d`, `6m`, `1y`
- For periods <= 30d: use raw measurements (existing behavior)
- For periods > 30d: query `measurement_aggregates` table with appropriate period_type
  - 90d: use daily aggregates
  - 6m: use weekly aggregates
  - 1y: use monthly aggregates

### 5.2 Update TrendChart Component

**Modify:** `frontend/components/TrendChart.tsx`

- Add period buttons: 24h, 7d, 30d, 90d, 6m, 1y
- For aggregate periods, show mean line with min/max shaded range
- Add visual indicator when viewing aggregated vs raw data
- Tooltip: show mean, p90, sample count for aggregate data points

### 5.3 Tests

**Frontend tests:**
- Test new period buttons render
- Test aggregate period shows mean/min/max visualization
- Test raw vs aggregate indicator

---

## Verification Checklist

- [ ] `measurement_aggregates` table created with correct schema and indexes
- [ ] `MeasurementAggregate` Pydantic model added and exported
- [ ] `AggregationService` computes correct statistics (verify with known test data)
- [ ] `_compute_statistics` handles edge cases (empty, single value, few values)
- [ ] `backfill` correctly identifies and fills missing periods
- [ ] `backfill` is idempotent (running twice doesn't create duplicates)
- [ ] CLI `--backfill` and `--incremental` modes work correctly
- [ ] CLI `--dry-run` produces no database writes
- [ ] Cleanup job runs aggregation before deleting raw data
- [ ] `/api/export` serves aggregated data for ranges >30 days
- [ ] `/api/hospitals/[slug]/trends` supports 90d, 6m, 1y periods
- [ ] TrendChart shows aggregate data with min/max range
- [ ] All new backend tests pass
- [ ] All new frontend tests pass
- [ ] Existing tests still pass (no regressions)

---

## Success Criteria

1. **Permanent historical data:** Aggregates survive the 30-day cleanup window
2. **Correct statistics:** Mean, median, P90, min, max, std_dev verified against manual calculation
3. **Idempotent backfill:** Running aggregation multiple times produces identical results
4. **Seamless UX:** Users see trend data for 90d/6m/1y without knowing about the two-tier architecture
5. **Export works:** Researchers can download aggregated data for long time ranges
6. **No data loss:** Cleanup never deletes raw data before aggregation runs

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Raw data already deleted (>30 days old) | Can't backfill older periods | Accept gap; aggregation starts from whatever data exists |
| Large backfill overwhelms DB | Medium | Process in batches; add progress logging |
| Median/P90 computation slow for large datasets | Low | Use Python `statistics` module; data per hospital per hour is small (<100 rows) |
| Ontology changes mid-period | Low | Denormalize ontology in aggregates; each aggregate records what the methodology was |

---

## Time Estimate

| Task | Hours |
|------|-------|
| Database schema + migration | 1-2 |
| Pydantic model + model tests | 1 |
| AggregationService implementation | 4-5 |
| AggregationService unit tests | 2-3 |
| DatabaseService extensions | 2-3 |
| CLI tool (aggregate.py) | 2-3 |
| CLI tests | 1-2 |
| Cleanup integration | 1 |
| GitHub Action update | 0.5 |
| Export API update | 2-3 |
| TrendChart update | 2-3 |
| Frontend tests | 1-2 |
| Integration tests | 2-3 |
| **Total** | **22-31 hours** |
