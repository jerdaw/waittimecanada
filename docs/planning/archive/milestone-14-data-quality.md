# Milestone 14: Data Quality & Anomaly Detection

> Archived plan (historical reference). Milestone delivered and closed.

> **Priority:** HIGH - Establishes research-grade trust in the platform
> **Estimated Effort:** 4-5 days
> **Admissions Appeal:** Scholar (scientific rigor), Professional (data stewardship), Leader (operational excellence)
> **Dependencies:** M13 (Aggregation Pipeline) - needs historical aggregates for anomaly baselines
> **Blocks:** None (but enhances M15 Analytics significantly)

---

## Overview

A research platform is only as credible as its data quality transparency. This milestone adds three capabilities that no competitor offers:

1. **Data quality metrics** - Track and expose scraper reliability, coverage gaps, and collection frequency
2. **Anomaly detection** - Automatically flag statistically unusual measurements
3. **Methodology change detection** - Detect when a province silently changes how they calculate wait times

**Narrative for Applications:**
> "I built self-auditing data infrastructure. The system doesn't just collect data — it monitors its own reliability, flags statistical outliers, and detects when upstream provinces change their measurement methodology. This is the kind of data stewardship that clinical researchers require."

---

## Phase 1: Data Quality Metrics Service (Day 1-2)

### 1.1 Database Schema

No new tables required. Data quality metrics are computed on-the-fly from existing `measurements` and `scraper_status` tables, with optional caching.

**Optional: Add quality cache table for expensive computations:**

```sql
CREATE TABLE data_quality_snapshots (
    id SERIAL PRIMARY KEY,
    hospital_id TEXT REFERENCES hospitals(id),
    source_id TEXT REFERENCES sources(id),
    snapshot_date DATE NOT NULL,

    -- Collection metrics
    expected_scrapes INTEGER NOT NULL,  -- based on 15-min intervals in a day = 96
    actual_scrapes INTEGER NOT NULL,
    success_rate DOUBLE PRECISION NOT NULL,  -- actual/expected as 0.0-1.0
    longest_gap_minutes INTEGER,  -- longest period with no data
    mean_gap_minutes DOUBLE PRECISION,

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (hospital_id, snapshot_date)
);

CREATE INDEX idx_quality_hospital_date
    ON data_quality_snapshots (hospital_id, snapshot_date DESC);

CREATE INDEX idx_quality_source_date
    ON data_quality_snapshots (source_id, snapshot_date DESC);
```

### 1.2 DataQualityService

**File:** `backend/src/waittime/services/data_quality.py`

```python
"""Service for computing and reporting data quality metrics."""

import logging
from datetime import datetime, timedelta, timezone

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class DataQualityService:
    """Computes data quality metrics for hospitals and sources."""

    # Scrapers run every 15 minutes = 96 expected scrapes per day
    EXPECTED_SCRAPES_PER_DAY = 96
    SCRAPE_INTERVAL_MINUTES = 15

    def __init__(self, db: DatabaseService):
        self.db = db

    def compute_hospital_quality(
        self, hospital_id: str, date: datetime
    ) -> dict:
        """
        Compute data quality metrics for a single hospital on a single day.

        Returns:
            {
                'hospital_id': str,
                'date': str,
                'expected_scrapes': int,
                'actual_scrapes': int,
                'success_rate': float,  # 0.0-1.0
                'longest_gap_minutes': int | None,
                'mean_gap_minutes': float | None,
                'gaps': [{'start': datetime, 'end': datetime, 'duration_minutes': int}]
            }
        """
        # 1. Query all measurements for hospital on this date
        # 2. Count actual measurements
        # 3. Compute gaps between consecutive measurements
        # 4. Calculate success_rate = actual / expected
        # 5. Find longest gap and mean gap
        pass

    def compute_source_quality(
        self, source_id: str, start_date: datetime, end_date: datetime
    ) -> dict:
        """
        Compute quality metrics for an entire source over a date range.

        Returns:
            {
                'source_id': str,
                'period': {'start': str, 'end': str},
                'total_expected': int,
                'total_actual': int,
                'overall_success_rate': float,
                'daily_success_rates': [{'date': str, 'rate': float}],
                'hospitals_with_data_today': int,
                'total_hospitals': int,
                'coverage_rate': float,  # hospitals_with_data / total_hospitals
            }
        """
        pass

    def compute_system_quality(self) -> dict:
        """
        Compute system-wide quality metrics (all sources, last 24h and 7d).

        Returns:
            {
                'overall_status': 'healthy' | 'degraded' | 'critical',
                'sources': [{
                    'source_id': str,
                    'province': str,
                    'last_24h_success_rate': float,
                    'last_7d_success_rate': float,
                    'hospitals_reporting': int,
                    'last_heartbeat_age_minutes': int,
                }],
                'system_uptime_24h': float,
                'system_uptime_7d': float,
                'total_measurements_24h': int,
                'total_measurements_7d': int,
            }
        """
        pass

    def get_coverage_timeline(
        self, hospital_id: str, days: int = 30
    ) -> list[dict]:
        """
        Get data availability timeline for a hospital.

        Returns list of daily entries:
            [{'date': '2026-02-01', 'scrape_count': 92, 'success_rate': 0.958, 'has_gaps': True}]

        Used for rendering heatmap-style data availability visualization.
        """
        pass

    def snapshot_daily_quality(self, date: datetime) -> int:
        """
        Compute and cache quality metrics for all hospitals for a given date.
        Saves to data_quality_snapshots table.

        Returns:
            Number of snapshots saved
        """
        pass
```

### 1.3 DatabaseService Extensions

**File:** `backend/src/waittime/services/database.py`

Add:

```python
def get_measurement_timestamps(
    self, hospital_id: str, start: datetime, end: datetime
) -> list[datetime]:
    """Get just the timestamps of measurements for gap analysis.
    Returns list of timestamp_utc values ordered chronologically."""
    pass

def get_measurement_count_by_hospital(
    self, source_id: str, start: datetime, end: datetime
) -> dict[str, int]:
    """Get measurement counts grouped by hospital_id for a source and time range.
    Returns: {'ca-on-ottawa-civic': 94, 'ca-on-toronto-general': 88, ...}"""
    pass

def insert_quality_snapshot(self, snapshot: dict) -> bool:
    """Insert a data quality snapshot (ON CONFLICT DO NOTHING)."""
    pass

def get_quality_snapshots(
    self, hospital_id: str, start_date: datetime, end_date: datetime
) -> list[dict]:
    """Get cached quality snapshots for a hospital and date range."""
    pass
```

### 1.4 Tests

**File:** `backend/tests/unit/test_data_quality_service.py`

Test cases:
- `test_compute_hospital_quality_full_coverage` - 96/96 scrapes, success_rate=1.0
- `test_compute_hospital_quality_partial` - 72/96 scrapes, verify gaps detected
- `test_compute_hospital_quality_no_data` - 0 scrapes, success_rate=0.0
- `test_gap_detection_single_gap` - missing data from 02:00-05:00, verify gap detected
- `test_gap_detection_multiple_gaps` - multiple gaps, verify longest and mean
- `test_compute_source_quality` - aggregate across multiple hospitals
- `test_compute_system_quality` - verify overall status logic (healthy/degraded/critical)
- `test_coverage_timeline_30_days` - verify daily entries for 30-day timeline
- `test_snapshot_idempotent` - running snapshot twice doesn't create duplicates

---

## Phase 2: Anomaly Detection (Day 2-3)

### 2.1 Schema Update

**Add column to measurements table:**

```sql
ALTER TABLE measurements
ADD COLUMN is_anomaly BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE measurements
ADD COLUMN anomaly_reason TEXT;
```

### 2.2 Update Measurement Model

**Modify:** `backend/src/waittime/core/models.py`

Add to `Measurement`:
```python
is_anomaly: bool = False
anomaly_reason: str | None = None
```

### 2.3 AnomalyDetectionService

**File:** `backend/src/waittime/services/anomaly_detection.py`

```python
"""Service for detecting anomalous wait time measurements."""

import logging
import statistics
from datetime import datetime, timedelta, timezone

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class AnomalyDetectionService:
    """Detects statistical outliers in incoming measurements."""

    # Configuration
    LOOKBACK_DAYS = 7  # Use 7-day rolling window for baseline
    MIN_SAMPLES_FOR_DETECTION = 20  # Need at least 20 data points
    Z_SCORE_THRESHOLD = 3.0  # Flag if >3 standard deviations from mean
    IQR_MULTIPLIER = 1.5  # For IQR-based detection

    def __init__(self, db: DatabaseService):
        self.db = db

    def check_measurement(
        self, hospital_id: str, value: float, timestamp: datetime
    ) -> dict:
        """
        Check if a new measurement is anomalous compared to recent history.

        Args:
            hospital_id: Hospital being measured
            value: Wait time in minutes
            timestamp: When the measurement was taken

        Returns:
            {
                'is_anomaly': bool,
                'reason': str | None,
                'details': {
                    'value': float,
                    'baseline_mean': float,
                    'baseline_std': float,
                    'z_score': float,
                    'iqr_lower': float,
                    'iqr_upper': float,
                } | None
            }
        """
        # 1. Get recent measurements for this hospital (last 7 days)
        # 2. If fewer than MIN_SAMPLES_FOR_DETECTION, return not anomalous
        #    (insufficient data to judge)
        # 3. Compute z-score: (value - mean) / std_dev
        # 4. Compute IQR bounds: Q1 - 1.5*IQR, Q3 + 1.5*IQR
        # 5. Flag as anomaly if EITHER:
        #    - |z_score| > Z_SCORE_THRESHOLD
        #    - value < iqr_lower or value > iqr_upper
        # 6. Return result with explanation
        pass

    def check_batch(
        self, measurements: list[dict]
    ) -> list[dict]:
        """
        Check a batch of measurements (from a scraper run).
        More efficient than checking one at a time - loads baselines once per hospital.

        Args:
            measurements: List of {'hospital_id': str, 'value': float, 'timestamp': datetime}

        Returns:
            List of anomaly check results (same order as input)
        """
        pass

    def flag_measurement(
        self, measurement_id: int, reason: str
    ) -> None:
        """Mark a measurement as anomalous in the database."""
        pass

    def get_recent_anomalies(
        self, source_id: str | None = None, days: int = 7
    ) -> list[dict]:
        """
        Get recent anomalies for display/review.

        Returns:
            List of anomalous measurements with hospital info and reason
        """
        pass

    @staticmethod
    def _compute_z_score(value: float, values: list[float]) -> float | None:
        """Compute z-score for a value against a distribution."""
        if len(values) < 3:
            return None
        mean = statistics.mean(values)
        std = statistics.stdev(values)
        if std == 0:
            return 0.0
        return (value - mean) / std

    @staticmethod
    def _compute_iqr_bounds(values: list[float]) -> tuple[float, float] | None:
        """Compute IQR-based anomaly bounds."""
        if len(values) < 4:
            return None
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        q1 = sorted_vals[n // 4]
        q3 = sorted_vals[3 * n // 4]
        iqr = q3 - q1
        return (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
```

### 2.4 Integrate with Scraper Pipeline

**Modify:** `backend/src/waittime/scrapers/base.py`

In the `run()` method, after parsing measurements and before saving:

```python
# After: measurements = self.parse(content)
# Before: self.save_measurements(measurements)

# Check for anomalies
anomaly_service = AnomalyDetectionService(self.db)
for measurement in measurements:
    result = anomaly_service.check_measurement(
        hospital_id=measurement.hospital_id,
        value=measurement.value,
        timestamp=measurement.timestamp_utc,
    )
    if result['is_anomaly']:
        measurement.is_anomaly = True
        measurement.anomaly_reason = result['reason']
        logger.warning(
            "Anomaly detected: %s value=%.0f (%s)",
            measurement.hospital_id,
            measurement.value,
            result['reason'],
        )
```

**Important:** Anomalies are still saved and displayed. They are flagged, not excluded. This preserves data integrity — the anomaly flag is metadata, not a filter.

### 2.5 Tests

**File:** `backend/tests/unit/test_anomaly_detection.py`

Test cases:
- `test_z_score_normal_value` - value within 1 std dev, not anomalous
- `test_z_score_high_outlier` - value >3 std dev above mean, flagged
- `test_z_score_low_outlier` - value >3 std dev below mean, flagged
- `test_iqr_bounds_normal` - value within IQR bounds, not anomalous
- `test_iqr_bounds_outlier` - value outside IQR bounds, flagged
- `test_insufficient_data` - <20 samples, returns not anomalous
- `test_zero_std_dev` - all same values, new same value = not anomalous
- `test_check_batch_efficiency` - verify batch loads baseline once per hospital
- `test_anomaly_reason_format` - verify reason string is human-readable
- `test_integration_with_scraper` - mock scraper run, verify anomalies flagged

---

## Phase 3: Data Provenance Page (Day 3-4)

### 3.1 API Endpoint

**File:** `frontend/app/api/data-quality/route.ts`

```typescript
// GET /api/data-quality
// Returns system-wide quality metrics

// Query params:
//   hospital_id (optional) - get quality for specific hospital
//   days (optional, default 30) - lookback period

// Response for system-wide:
// {
//   overall_status: 'healthy' | 'degraded' | 'critical',
//   sources: [{ source_id, province, success_rate_24h, success_rate_7d, ... }],
//   total_measurements_24h: number,
//   total_measurements_7d: number,
// }

// Response for specific hospital:
// {
//   hospital_id: string,
//   coverage_timeline: [{ date, scrape_count, success_rate }],
//   current_quality: { success_rate, longest_gap, mean_gap },
//   anomalies_7d: [{ timestamp, value, reason }],
// }
```

### 3.2 API Endpoint for Anomalies

**File:** `frontend/app/api/anomalies/route.ts`

```typescript
// GET /api/anomalies
// Returns recent anomalies

// Query params:
//   source_id (optional)
//   days (optional, default 7)

// Response:
// {
//   anomalies: [{
//     hospital_id, hospital_name, province,
//     value, timestamp, reason,
//     baseline_mean, z_score,
//   }],
//   total_count: number,
// }
```

### 3.3 DataQuality Page

**File:** `frontend/app/data-quality/page.tsx`

A dedicated page showing:

1. **System Health Summary** - Overall status indicator with per-source breakdown
   - Each source shows: province name, success rate (24h + 7d), hospitals reporting, last heartbeat
   - Color coding: green (>95%), amber (80-95%), red (<80%)

2. **Collection Coverage Heatmap** - Per-hospital data availability over last 30 days
   - Rows: hospitals (sorted by province, then name)
   - Columns: days
   - Cells: colored by success rate (green=100%, lighter green=partial, white=no data)
   - Click a cell to see details (scrape count, gaps)

3. **Recent Anomalies Feed** - Chronological list of flagged measurements
   - Show: hospital name, value, expected range, reason, timestamp
   - Visual indicator: amber for moderate outliers, red for extreme outliers

4. **Methodology Notes** - Short section explaining:
   - How quality metrics are computed
   - What constitutes an anomaly
   - Why transparency matters for research use

### 3.4 Components

**File:** `frontend/components/DataQualityCard.tsx`
- Reusable card showing quality metrics for a source
- Success rate gauge (circular or bar)
- Hospital coverage count
- Last heartbeat age

**File:** `frontend/components/CoverageHeatmap.tsx`
- Grid visualization of data availability
- 30 columns (days) x N rows (hospitals)
- Color scale: white (0%) → light green (50%) → dark green (100%)
- Tooltip on hover: "Toronto General: 94/96 scrapes (97.9%)"

**File:** `frontend/components/AnomalyFeed.tsx`
- List of recent anomalies
- Each entry: hospital name, flagged value, baseline range, reason
- Badge: "Z-Score: 4.2" or "Outside IQR"
- Link to hospital on map

### 3.5 Navigation

Add "Data Quality" link to the site header navigation, alongside "Methods" and "FAQ".

### 3.6 Tests

**File:** `frontend/__tests__/components/DataQualityCard.test.tsx`
- Renders source name and province
- Shows success rate with correct color (green/amber/red)
- Displays hospital count
- Shows heartbeat age

**File:** `frontend/__tests__/components/CoverageHeatmap.test.tsx`
- Renders correct number of rows and columns
- Correct color for 100% coverage cell
- Correct color for 0% coverage cell
- Tooltip appears on hover

**File:** `frontend/__tests__/components/AnomalyFeed.test.tsx`
- Renders anomaly entries
- Shows correct hospital name and value
- Empty state when no anomalies

---

## Phase 4: Methodology Change Detection (Day 4-5)

### 4.1 MethodologyChangeDetector

**File:** `backend/src/waittime/services/methodology_change.py`

```python
"""Service for detecting when a province silently changes measurement methodology."""

import logging
import statistics
from datetime import datetime, timedelta

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class MethodologyChangeDetector:
    """
    Detects distributional shifts that may indicate methodology changes.

    Example: If Ontario switches from MEAN to P90 reporting, all hospitals
    would suddenly report higher values. This detector compares rolling
    statistics between consecutive periods to flag such shifts.
    """

    # Configuration
    COMPARISON_WINDOW_DAYS = 7  # Compare this week vs last week
    MIN_HOSPITALS_FOR_DETECTION = 5  # Need data from enough hospitals
    SHIFT_THRESHOLD_PERCENT = 20  # Flag if province-wide mean shifts >20%

    def __init__(self, db: DatabaseService):
        self.db = db

    def check_source(self, source_id: str) -> dict:
        """
        Check a source for potential methodology changes.

        Compares the distribution of values in the current period vs previous period.
        If the province-wide mean shifts significantly, flags a potential change.

        Returns:
            {
                'source_id': str,
                'change_detected': bool,
                'details': {
                    'current_period_mean': float,
                    'previous_period_mean': float,
                    'shift_percent': float,
                    'hospitals_analyzed': int,
                    'explanation': str,
                } | None
            }
        """
        # 1. Get daily aggregates for current week and previous week
        #    (requires M13 aggregation pipeline)
        # 2. Compute province-wide mean for each period
        #    (average of hospital daily means)
        # 3. Calculate shift: (current - previous) / previous * 100
        # 4. If |shift| > SHIFT_THRESHOLD_PERCENT AND
        #    hospitals_analyzed >= MIN_HOSPITALS_FOR_DETECTION:
        #    → Flag as potential change
        # 5. Return result with explanation
        pass

    def check_all_sources(self) -> list[dict]:
        """Check all active sources for methodology changes."""
        pass

    def get_change_history(self, source_id: str) -> list[dict]:
        """
        Get history of detected methodology changes.
        Used for display on data quality page.
        """
        pass
```

**Note:** This service depends on M13 aggregation tables. Without aggregates, it would need to compute statistics from raw measurements each time, which is expensive. With aggregates, it's a simple comparison of stored summary stats.

### 4.2 Schema for Change Events

```sql
CREATE TABLE methodology_change_events (
    id SERIAL PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(id),
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    previous_period_start DATE NOT NULL,
    previous_period_end DATE NOT NULL,
    current_period_start DATE NOT NULL,
    current_period_end DATE NOT NULL,
    previous_mean DOUBLE PRECISION NOT NULL,
    current_mean DOUBLE PRECISION NOT NULL,
    shift_percent DOUBLE PRECISION NOT NULL,
    hospitals_analyzed INTEGER NOT NULL,
    explanation TEXT NOT NULL,
    is_confirmed BOOLEAN NOT NULL DEFAULT FALSE,  -- Manual confirmation
    resolution_notes TEXT,  -- Admin notes on what actually changed
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_methodology_changes_source
    ON methodology_change_events (source_id, detected_at DESC);
```

### 4.3 Integration with Check Heartbeat

**Modify:** `backend/src/waittime/cli/check_heartbeat.py`

Add methodology check alongside heartbeat check:

```python
# After heartbeat checks:
detector = MethodologyChangeDetector(db)
changes = detector.check_all_sources()
for change in changes:
    if change['change_detected']:
        logger.warning("Potential methodology change: %s", change['source_id'])
        if not args.dry_run:
            alerts.send_alert(
                title=f"Methodology Change Detected: {change['source_id']}",
                message=change['details']['explanation'],
                priority=0,
            )
```

### 4.4 Frontend Integration

Add to the `/data-quality` page (Phase 3):

- **Methodology Change Alerts** section
- Show detected changes with: source, dates, shift %, explanation
- Status: "Unconfirmed" (yellow) or "Confirmed" (green with resolution notes)
- Link to the province's methodology documentation

### 4.5 Tests

**File:** `backend/tests/unit/test_methodology_change.py`

Test cases:
- `test_no_change_stable_data` - both periods similar, no change detected
- `test_change_detected_large_shift` - 30% shift, change flagged
- `test_change_not_detected_small_shift` - 10% shift, below threshold
- `test_insufficient_hospitals` - <5 hospitals, no detection attempted
- `test_explanation_format` - verify human-readable explanation
- `test_check_all_sources` - verify all sources checked

---

## Verification Checklist

### Data Quality
- [ ] `data_quality_snapshots` table created
- [ ] `DataQualityService` computes correct metrics
- [ ] Hospital quality: success_rate, gaps, gap durations correct
- [ ] Source quality: aggregate across hospitals
- [ ] System quality: overall status logic (healthy/degraded/critical)
- [ ] Coverage timeline returns 30 days of daily data

### Anomaly Detection
- [ ] `is_anomaly` and `anomaly_reason` columns added to measurements
- [ ] Z-score detection works for extreme values
- [ ] IQR detection works for moderate outliers
- [ ] Insufficient data returns "not anomalous" (safe default)
- [ ] Anomalies are flagged but still saved and displayed
- [ ] Scraper pipeline integrates anomaly checking

### Data Quality Page
- [ ] `/data-quality` route renders system health
- [ ] Coverage heatmap shows per-hospital availability
- [ ] Anomaly feed shows recent flagged measurements
- [ ] Navigation link added to header

### Methodology Change Detection
- [ ] `methodology_change_events` table created
- [ ] Detector correctly identifies large distributional shifts
- [ ] Small variations don't trigger false positives
- [ ] Integration with heartbeat check CLI
- [ ] Display on data quality page

---

## Success Criteria

1. **Transparent quality metrics:** Any researcher can see exactly how reliable the data is
2. **Anomaly flagging works:** Extreme values are flagged without being excluded
3. **No false positives in normal operation:** Anomaly detection doesn't cry wolf
4. **Methodology changes detected:** A 20%+ province-wide shift triggers an alert
5. **Coverage heatmap:** Visual at-a-glance data availability for every hospital

---

## Time Estimate

| Task | Hours |
|------|-------|
| Data quality schema + model | 1 |
| DataQualityService implementation | 3-4 |
| DataQualityService tests | 2-3 |
| Anomaly detection schema changes | 0.5 |
| AnomalyDetectionService implementation | 3-4 |
| Anomaly detection tests | 2-3 |
| Scraper pipeline integration | 1-2 |
| Data quality API endpoints | 2-3 |
| Data quality page + components | 4-5 |
| Frontend tests | 2-3 |
| Methodology change detector | 2-3 |
| Methodology change tests | 1-2 |
| Heartbeat CLI integration | 1 |
| Integration tests | 2-3 |
| **Total** | **26-37 hours** |
