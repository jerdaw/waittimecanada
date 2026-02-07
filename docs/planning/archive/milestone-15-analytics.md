# Milestone 15: Analytics & Benchmarking

> **Priority:** HIGH - Transforms data into actionable insights for administrators and researchers
> **Estimated Effort:** 5-6 days
> **Admissions Appeal:** Scholar (publishable analysis), Professional (peer benchmarking), Health Advocate (temporal access patterns), Leader (system-level dashboards)
> **Dependencies:** M13 (Aggregation Pipeline) - needs aggregated data for all analytics

---

## Overview

This milestone transforms raw data and aggregates into the kind of analysis that hospital administrators, health researchers, and policymakers actually use. It answers questions like:

- "How does Ottawa Civic compare to other Ontario ERs this week?" (Peer Benchmarking)
- "Are wait times worse on weekends?" (Temporal Patterns)
- "Which Ontario Health Team region has the longest waits?" (Regional Intelligence)
- "Are Ontario ER waits getting better or worse over time?" (System Trends)

**Narrative for Applications:**
> "I didn't just collect data — I built analytical tools that produce the kind of insights found in peer-reviewed health systems research. Hospital administrators can benchmark against regional peers, researchers can identify temporal patterns, and policymakers can track system-wide trends over time."

---

## Phase 1: Hospital Peer Benchmarking (Day 1-2)

### 1.1 API Endpoint

**File:** `frontend/app/api/analytics/benchmarks/route.ts`

```typescript
// GET /api/analytics/benchmarks
//
// Query params:
//   province: string (required, e.g., "ON")
//   period: string (optional, default "7d") - "24h" | "7d" | "30d"
//
// Response:
// {
//   province: "ON",
//   period: "7d",
//   generated_at: "2026-02-06T12:00:00Z",
//   hospital_count: 160,
//   province_stats: {
//     mean: 145.2,
//     median: 132.0,
//     p25: 95.0,
//     p75: 185.0,
//     min: 22.0,
//     max: 410.0,
//   },
//   hospitals: [{
//     hospital_id: "ca-on-ottawa-civic",
//     hospital_name: "The Ottawa Hospital - Civic Campus",
//     city: "Ottawa",
//     current_wait: 165,
//     period_mean: 158.3,
//     percentile: 72,          // This hospital is in the 72nd percentile (worse than 72% of hospitals)
//     quartile: 3,             // Q1=best, Q4=worst
//     trend: "worsening",      // "improving" | "stable" | "worsening"
//     trend_change_percent: 8.5, // +8.5% compared to previous period
//   }],
// }
```

**Implementation logic:**

1. Query daily aggregates for all hospitals in province for the specified period (from M13 `measurement_aggregates`)
2. Compute each hospital's period mean from daily aggregates
3. Rank hospitals by period mean
4. Compute percentile: `(rank / total) * 100`
5. Compute quartile: `Q1` (0-25th), `Q2` (25-50th), `Q3` (50-75th), `Q4` (75-100th)
6. Compute trend: compare this period's mean to previous period's mean
   - Improving: >5% decrease
   - Stable: within +/-5%
   - Worsening: >5% increase
7. Compute province-wide summary stats

### 1.2 Backend Support

If computing benchmarks in the API route is too complex, create a backend service:

**File:** `backend/src/waittime/services/benchmarking.py`

```python
"""Service for computing hospital peer benchmarks."""

import logging
import statistics
from datetime import datetime, timedelta

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class BenchmarkingService:
    """Computes hospital rankings and peer comparisons within a province."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def compute_benchmarks(
        self, province: str, period_days: int = 7
    ) -> dict:
        """
        Compute peer benchmarks for all hospitals in a province.

        Args:
            province: Province code (e.g., "ON")
            period_days: Lookback period for computing averages

        Returns:
            Dict with province_stats and per-hospital rankings
        """
        # 1. Get all hospitals in province
        # 2. For each hospital, get daily aggregates for the period
        # 3. Compute period mean per hospital
        # 4. Rank hospitals by period mean (ascending = shorter wait = better)
        # 5. Compute percentile and quartile for each
        # 6. Get previous period data for trend calculation
        # 7. Compute province-wide summary statistics
        pass

    def get_hospital_benchmark(
        self, hospital_id: str, period_days: int = 7
    ) -> dict:
        """Get benchmark data for a single hospital (used in hospital detail view)."""
        pass

    @staticmethod
    def _compute_percentile(rank: int, total: int) -> int:
        """Compute percentile from rank. Rank 1 = best = lowest percentile."""
        return int((rank / total) * 100)

    @staticmethod
    def _compute_trend(
        current_mean: float, previous_mean: float, threshold: float = 5.0
    ) -> str:
        """
        Determine trend direction.

        Returns: 'improving', 'stable', or 'worsening'
        """
        if previous_mean == 0:
            return 'stable'
        change_pct = ((current_mean - previous_mean) / previous_mean) * 100
        if change_pct < -threshold:
            return 'improving'
        elif change_pct > threshold:
            return 'worsening'
        return 'stable'
```

### 1.3 Frontend Component

**File:** `frontend/components/BenchmarkCard.tsx`

A card shown in the expanded hospital detail (or map popup) showing:

- **Percentile badge:** "Better than 72% of Ontario ERs" (colored: green Q1, amber Q2-Q3, red Q4)
- **Trend indicator:** Arrow up/down/flat with percentage change
- **Province context:** "Ontario avg: 145 min | This hospital: 165 min"
- **Quartile label:** "Q3 - Above Average Wait"

**Design notes:**
- Keep it compact — this goes inside existing hospital cards/popups
- Use the same color system: green (<60 min / Q1), amber (60-120 min / Q2-Q3), red (>120 min / Q4)
- Include disclaimer: "Rankings based on 7-day average. Methodology differences affect comparability."

### 1.4 Integration Points

- Add `BenchmarkCard` to `ExpandedCardDetails.tsx` (hospital list expanded view)
- Add benchmark summary to `Map.tsx` popups (compact version: just percentile + trend)
- Consider adding a sortable benchmarking table view (new component or enhancement to hospital list)

### 1.5 Tests

**Backend tests** (`backend/tests/unit/test_benchmarking_service.py`):
- `test_compute_benchmarks_basic` - 5 hospitals, verify correct ranking
- `test_percentile_calculation` - rank 1 of 10 = 10th percentile
- `test_quartile_assignment` - verify Q1-Q4 boundaries
- `test_trend_improving` - current mean < previous mean by >5%
- `test_trend_stable` - change within +/-5%
- `test_trend_worsening` - current mean > previous mean by >5%
- `test_single_hospital_benchmark` - verify individual hospital data

**Frontend tests** (`frontend/__tests__/components/BenchmarkCard.test.tsx`):
- Renders percentile badge with correct value
- Correct color for Q1 (green), Q2-Q3 (amber), Q4 (red)
- Trend arrow direction matches trend value
- Province context line shows correct values

---

## Phase 2: Temporal Pattern Analysis (Day 2-3)

### 2.1 API Endpoint

**File:** `frontend/app/api/analytics/patterns/route.ts`

```typescript
// GET /api/analytics/patterns
//
// Query params:
//   hospital_id: string (required)
//   type: string (optional, default "hour_of_day")
//     - "hour_of_day": Average wait by hour (0-23)
//     - "day_of_week": Average wait by day (Mon-Sun)
//     - "monthly": Monthly averages for seasonal trends
//
// Response for hour_of_day:
// {
//   hospital_id: "ca-on-ottawa-civic",
//   hospital_name: "The Ottawa Hospital - Civic Campus",
//   pattern_type: "hour_of_day",
//   data_period: { start: "2026-01-01", end: "2026-02-06" },
//   sample_count: 3456,
//   patterns: [
//     { hour: 0, mean: 92.3, median: 85.0, sample_count: 144 },
//     { hour: 1, mean: 88.1, median: 82.0, sample_count: 142 },
//     ...
//     { hour: 23, mean: 95.7, median: 89.0, sample_count: 143 },
//   ],
//   insights: {
//     peak_hour: 14,       // 2 PM
//     quietest_hour: 4,    // 4 AM
//     peak_mean: 185.3,
//     quietest_mean: 72.1,
//     peak_vs_quiet_ratio: 2.57,  // Peak is 2.57x the quietest hour
//   }
// }
//
// Response for day_of_week:
// {
//   patterns: [
//     { day: "Monday", day_index: 0, mean: 142.3, median: 135.0, sample_count: 480 },
//     ...
//     { day: "Sunday", day_index: 6, mean: 168.9, median: 155.0, sample_count: 475 },
//   ],
//   insights: {
//     worst_day: "Sunday",
//     best_day: "Wednesday",
//     weekend_vs_weekday_ratio: 1.18,
//   }
// }
```

**Implementation logic:**

1. Query hourly aggregates from M13 `measurement_aggregates`
2. Group by hour-of-day (or day-of-week, or month)
3. Compute mean-of-means and total sample count per group
4. Identify peak/quietest periods
5. Compute ratios for insights

### 2.2 Backend Support

**File:** `backend/src/waittime/services/patterns.py`

```python
"""Service for computing temporal wait time patterns."""

import logging
from datetime import datetime, timedelta
from collections import defaultdict

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class TemporalPatternService:
    """Analyzes temporal patterns in wait time data."""

    DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    def __init__(self, db: DatabaseService):
        self.db = db

    def hour_of_day_pattern(
        self, hospital_id: str, lookback_days: int = 30
    ) -> dict:
        """
        Compute average wait time by hour of day.

        Uses hourly aggregates from M13. Groups all Monday-2PMs, all Tuesday-2PMs, etc.
        into a single "2 PM" bucket to get a typical hourly profile.

        Args:
            hospital_id: Hospital to analyze
            lookback_days: How far back to look

        Returns:
            Dict with 24 hourly entries + peak/quiet insights
        """
        # 1. Query hourly aggregates for hospital in lookback period
        # 2. Group by hour (0-23)
        # 3. For each hour: compute mean of the hourly means, total sample count
        # 4. Identify peak and quietest hours
        # 5. Compute peak/quiet ratio
        pass

    def day_of_week_pattern(
        self, hospital_id: str, lookback_days: int = 90
    ) -> dict:
        """
        Compute average wait time by day of week.

        Uses daily aggregates grouped by weekday.

        Args:
            hospital_id: Hospital to analyze
            lookback_days: How far back to look (longer for weekly patterns)

        Returns:
            Dict with 7 daily entries + weekend vs weekday insights
        """
        # 1. Query daily aggregates for hospital in lookback period
        # 2. Group by day of week (0=Monday, 6=Sunday)
        # 3. Compute mean of daily means per weekday
        # 4. Identify best/worst days
        # 5. Compute weekend vs weekday ratio
        pass

    def monthly_trend(
        self, hospital_id: str, lookback_months: int = 12
    ) -> dict:
        """
        Compute monthly average wait times for seasonal analysis.

        Uses monthly aggregates from M13.

        Returns:
            Dict with monthly entries + year-over-year insights
        """
        pass
```

### 2.3 Frontend Components

**File:** `frontend/components/TemporalPatterns.tsx`

A tabbed component (Hour of Day | Day of Week | Monthly) showing:

**Hour of Day tab:**
- Bar chart (0-23 hours on x-axis, average wait time on y-axis)
- Highlighted bars for peak (red) and quietest (green) hours
- Insight text: "Wait times peak at 2 PM (185 min avg) and are lowest at 4 AM (72 min avg)"

**Day of Week tab:**
- Bar chart (Mon-Sun on x-axis, average wait time on y-axis)
- Weekend bars highlighted differently
- Insight text: "Weekends average 18% longer waits than weekdays"

**Monthly tab:**
- Line chart showing monthly averages over time
- Trend line overlay
- Insight text: "Wait times have [increased/decreased] X% over the past 6 months"

**Library:** Use Recharts (already a dependency) for all charts.

### 2.4 Integration

- Add `TemporalPatterns` as a tab or section in the hospital detail view
- Could be in the map popup (if space allows) or in an expanded analysis modal
- Consider a dedicated `/analytics` page that aggregates patterns across hospitals

### 2.5 Tests

**Backend tests** (`backend/tests/unit/test_temporal_patterns.py`):
- `test_hour_of_day_24_entries` - verify 24 hourly buckets
- `test_peak_and_quiet_identification` - correct peak/quiet hours
- `test_day_of_week_7_entries` - verify 7 daily buckets
- `test_weekend_vs_weekday_ratio` - correct ratio calculation
- `test_monthly_trend_chronological` - entries in correct month order
- `test_insufficient_data` - graceful handling when not enough data

**Frontend tests** (`frontend/__tests__/components/TemporalPatterns.test.tsx`):
- Tab switching works
- Correct number of bars in hour-of-day chart
- Insight text renders with correct values
- Loading state renders skeleton

---

## Phase 3: Ontario Health Region Mapping (Day 3-4)

### 3.1 Region Seed Data

**File:** `backend/data/regions/ontario-regions.json`

```json
{
  "province": "ON",
  "region_type": "Ontario Health Region",
  "regions": [
    {
      "id": "on-central",
      "name": "Central",
      "description": "Includes Toronto, York Region, Simcoe Muskoka",
      "hospitals": [
        "ca-on-toronto-general",
        "ca-on-toronto-western",
        "ca-on-sunnybrook",
        "ca-on-st-michaels",
        "ca-on-mount-sinai",
        "ca-on-north-york-general",
        "ca-on-humber-river"
      ]
    },
    {
      "id": "on-east",
      "name": "East",
      "description": "Includes Ottawa, Kingston, Champlain",
      "hospitals": [
        "ca-on-ottawa-civic",
        "ca-on-ottawa-general",
        "ca-on-queensway-carleton",
        "ca-on-kingston-general"
      ]
    },
    {
      "id": "on-west",
      "name": "West",
      "description": "Includes Hamilton, Waterloo, Erie St. Clair",
      "hospitals": [
        "ca-on-hamilton-general",
        "ca-on-st-josephs-hamilton",
        "ca-on-grand-river"
      ]
    },
    {
      "id": "on-north",
      "name": "North",
      "description": "Includes Sudbury, Thunder Bay, North East",
      "hospitals": [
        "ca-on-health-sciences-north",
        "ca-on-thunder-bay-regional"
      ]
    },
    {
      "id": "on-toronto",
      "name": "Toronto",
      "description": "City of Toronto hospitals",
      "hospitals": []
    }
  ]
}
```

**Important Notes:**
- The hospital-to-region mapping needs to be researched from Ontario Health's official regional structure
- Ontario Health has 5 regions: West, Central, Toronto, East, North
- Hospital IDs must match existing IDs in the hospitals table
- This seed file should be populated with ALL Ontario hospitals mapped to their correct region
- Use official sources: https://www.ontariohealth.ca/ for region definitions

### 3.2 Database Schema

**Option A: Add region column to hospitals table**

```sql
ALTER TABLE hospitals
ADD COLUMN region_id TEXT,
ADD COLUMN region_name TEXT;
```

**Option B: Separate regions table (more flexible)**

```sql
CREATE TABLE regions (
    id TEXT PRIMARY KEY,           -- e.g., "on-central"
    name TEXT NOT NULL,            -- e.g., "Central"
    province TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE hospital_regions (
    hospital_id TEXT NOT NULL REFERENCES hospitals(id),
    region_id TEXT NOT NULL REFERENCES regions(id),
    PRIMARY KEY (hospital_id, region_id)
);

CREATE INDEX idx_hospital_regions_region
    ON hospital_regions (region_id);
```

**Recommendation:** Option B. It's more flexible and allows hospitals to potentially belong to multiple grouping systems (Ontario Health Regions, LHINs, census divisions, etc.) in the future.

### 3.3 Seed CLI Extension

**Modify:** `backend/src/waittime/cli/seed.py` or create new CLI

```bash
python -m waittime.cli.seed_regions --file data/regions/ontario-regions.json
python -m waittime.cli.seed_regions --list
```

### 3.4 API Endpoint

**File:** `frontend/app/api/analytics/regions/route.ts`

```typescript
// GET /api/analytics/regions
//
// Query params:
//   province: string (required, e.g., "ON")
//   period: string (optional, default "7d")
//
// Response:
// {
//   province: "ON",
//   period: "7d",
//   regions: [{
//     region_id: "on-central",
//     region_name: "Central",
//     hospital_count: 45,
//     hospitals_reporting: 42,
//     region_mean_wait: 152.3,
//     region_median_wait: 138.0,
//     worst_hospital: { id: "...", name: "...", mean: 285.0 },
//     best_hospital: { id: "...", name: "...", mean: 55.0 },
//     trend: "stable",
//     trend_change_percent: -2.1,
//   }],
// }
```

### 3.5 Frontend Components

**File:** `frontend/components/RegionDashboard.tsx`

- Dropdown to select province (Ontario only for now)
- Region cards in a grid layout
- Each card shows: region name, hospital count, average wait, best/worst hospital, trend
- Color-coded by average wait (green/amber/red)
- Click a region to filter hospital list to that region

**File:** `frontend/components/RegionSelector.tsx`

- Compact region filter for the hospital list
- Dropdown or pill buttons: "All | Central | East | West | North | Toronto"
- When selected, filters both list and map to show only that region's hospitals

### 3.6 Integration

- Add `RegionSelector` to the hospital list filter bar (alongside province filter)
- Add `RegionDashboard` as a section on a new `/analytics` page or enhance the landing page
- Map could highlight region boundaries (if GeoJSON available) — this is optional and complex

### 3.7 Tests

**Backend tests:**
- `test_seed_regions` - verify region data loads correctly
- `test_hospital_region_mapping` - verify hospitals map to correct regions
- `test_region_stats_computation` - verify aggregate stats per region

**Frontend tests:**
- `test_region_dashboard_renders` - shows correct number of region cards
- `test_region_card_content` - shows hospital count, average wait, trend
- `test_region_selector_filters` - selecting region filters hospital list

---

## Phase 4: System-Wide Trend Dashboard (Day 4-5)

### 4.1 API Endpoint

**File:** `frontend/app/api/analytics/trends/route.ts`

```typescript
// GET /api/analytics/trends
//
// Query params:
//   province: string (required)
//   period: string (optional, default "monthly") - "weekly" | "monthly"
//   lookback: string (optional, default "6m") - "3m" | "6m" | "1y"
//
// Response:
// {
//   province: "ON",
//   period: "monthly",
//   lookback: "6m",
//   data_points: [{
//     period_start: "2025-09-01",
//     period_end: "2025-09-30",
//     province_mean: 142.3,
//     province_median: 128.0,
//     province_p90: 245.0,
//     hospitals_reporting: 155,
//     total_measurements: 42000,
//   }],
//   trend_summary: {
//     direction: "worsening",           // "improving" | "stable" | "worsening"
//     change_percent: 12.5,             // Over the lookback period
//     start_mean: 126.5,
//     end_mean: 142.3,
//     narrative: "Ontario ER wait times have increased approximately 12% over the past 6 months, from an average of 127 minutes to 142 minutes."
//   }
// }
```

**Implementation logic:**

1. Query monthly (or weekly) aggregates across all hospitals in province
2. For each period: compute province-wide mean (average of hospital means), weighted by sample count
3. Compute median and P90 across hospital means
4. Determine trend direction by comparing first and last period
5. Generate narrative text

### 4.2 Backend Support

**File:** `backend/src/waittime/services/trends.py`

```python
"""Service for computing system-wide trend analysis."""

import logging
from datetime import datetime

from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class SystemTrendService:
    """Computes province-level and system-level wait time trends."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def province_trend(
        self, province: str, period_type: str = "monthly", lookback_months: int = 6
    ) -> dict:
        """
        Compute province-wide wait time trend.

        Aggregates all hospital monthly/weekly aggregates into province-level stats.

        Args:
            province: Province code
            period_type: "weekly" or "monthly"
            lookback_months: How far back to analyze

        Returns:
            Dict with data_points and trend_summary
        """
        # 1. Query aggregates grouped by period for all hospitals in province
        # 2. For each period, compute province mean (weighted by sample_count)
        # 3. Compute trend direction and change percentage
        # 4. Generate narrative
        pass

    def generate_narrative(
        self, province: str, direction: str, change_pct: float,
        start_mean: float, end_mean: float, lookback: str
    ) -> str:
        """
        Generate human-readable trend narrative.

        Example outputs:
        - "Ontario ER wait times have increased approximately 12% over the past 6 months."
        - "Ontario ER wait times have remained stable over the past year."
        - "Ontario ER wait times have decreased approximately 8% over the past 3 months."
        """
        pass
```

### 4.3 Frontend Components

**File:** `frontend/components/SystemTrendChart.tsx`

A prominent chart component showing:

- **Line chart:** Province-wide mean over time (with confidence band showing min-max range)
- **Trend summary badge:** "Ontario ER Waits: +12% over 6 months" (red if worsening, green if improving)
- **Narrative text:** The generated narrative below the chart
- **Period controls:** 3m | 6m | 1y toggles
- **Granularity controls:** Weekly | Monthly toggles

**Design:** This should be visually prominent — it's the kind of data that gets cited in news articles and research papers.

### 4.4 Analytics Page

**File:** `frontend/app/analytics/page.tsx`

A dedicated analytics page bringing together all analytical features:

1. **System Trend** (top) - Province-wide trend chart with narrative
2. **Regional Overview** (middle) - Region cards with comparative stats
3. **Hospital Rankings** (bottom) - Sortable table with percentile, trend, quartile

**Navigation:** Add "Analytics" link to header, positioned after "Methods" and before "FAQ".

**SEO:** Add appropriate schema.org structured data for the analytics page (Dataset schema).

### 4.5 Tests

**Backend tests** (`backend/tests/unit/test_system_trends.py`):
- `test_province_trend_monthly` - verify monthly data points
- `test_trend_direction_improving` - decreasing mean = improving
- `test_trend_direction_worsening` - increasing mean = worsening
- `test_trend_direction_stable` - small change = stable
- `test_narrative_generation` - verify narrative text format
- `test_weighted_mean` - verify sample_count weighting works correctly

**Frontend tests** (`frontend/__tests__/components/SystemTrendChart.test.tsx`):
- Chart renders with correct number of data points
- Trend badge shows correct direction and color
- Period toggle changes displayed data
- Narrative text renders

**Frontend tests** (`frontend/__tests__/app/analytics/page.test.tsx`):
- Page renders all three sections
- Loading states display skeletons

---

## Phase 5: Operationalization & Reliability (Day 5)

### 5.1 Runtime Resilience

**File:** `frontend/app/api/analytics/regions/route.ts`

- Detect missing region schema (`42P01`) and return `503` with `setup_required=true`
- Include concrete setup commands in `setup_steps`
- Avoid opaque 500 errors during fresh-environment bootstraps

**File:** `frontend/app/api/analytics/trends/route.ts`

- Keep weekly/monthly as primary data source
- If requested rollups are missing, derive points from daily aggregates
- Return metadata (`data_source`, `fallback_used`) for transparency

### 5.2 One-Command Bootstrap

**File:** `backend/src/waittime/cli/bootstrap_analytics.py`

- Apply all migrations (`backend/migrations/*.sql`)
- Seed Ontario regions from `backend/data/regions/ontario-regions.json`
- Backfill `daily`, `weekly`, and `monthly` aggregates for analytics
- Support `--dry-run`, `--skip-*`, and `--days` flags

### 5.3 UI Guidance for Incomplete Setup

**File:** `frontend/app/analytics/page.tsx`

- Show inline setup guidance when `/api/analytics/regions` reports `setup_required`
- Display setup commands directly in dashboard context

### 5.4 Tests

**Backend tests** (`backend/tests/unit/test_bootstrap_analytics_cli.py`):
- migration execution/dry-run behavior
- region seed and aggregate backfill orchestration
- CLI argument validation and happy-path flow

**Frontend tests:**
- `frontend/tests/api/analytics-regions.test.ts` validates setup-required response
- `frontend/tests/api/analytics-trends.test.ts` validates daily-rollup fallback
- `frontend/tests/pages/analytics.test.tsx` validates setup guidance rendering

---

## Phase 6: Region Coverage Expansion (Day 5-6)

### 6.1 Coverage Audit + Auto-Assignment CLI

**File:** `backend/src/waittime/cli/region_mapping.py`

- Add mapping audit command:
  - total hospitals
  - mapped/unmapped counts
  - coverage percentage
  - per-region distribution
- Add first-pass auto-assignment:
  - explicit hospital overrides (highest priority)
  - city/name token rules
  - coordinate-based fallback rules
- Add JSON report export option for repeatable operational checks

**Overrides file:** `backend/data/regions/ontario-region-overrides.json`

### 6.2 API Coverage Telemetry

**File:** `frontend/app/api/analytics/regions/route.ts`

- Add mapping coverage metadata to response:
  - `mapped_hospital_count`
  - `province_hospital_total`
  - `mapping_coverage` object (`mapped_hospitals`, `total_hospitals`, `coverage_percent`)

### 6.3 Regional UI Coverage Badge

**Files:**
- `frontend/components/RegionDashboard.tsx`
- `frontend/app/analytics/page.tsx`

- Show mapping coverage badge near Regional Intelligence heading
- Highlight low coverage states (`<60%`) with warning styling

### 6.4 Tests

**Backend tests:**
- `backend/tests/unit/test_region_mapping_cli.py`:
  - override loading
  - heuristic assignment behavior
  - coverage report computation
  - dry-run and write behavior

**Frontend tests:**
- `frontend/tests/api/analytics-regions.test.ts` validates coverage telemetry
- `frontend/tests/components/RegionDashboard.test.tsx` validates coverage badge rendering

---

## Verification Checklist

### Peer Benchmarking
- [x] `/api/analytics/benchmarks` returns correct rankings
- [x] Percentile and quartile calculations are accurate
- [x] Trend direction computed correctly
- [x] BenchmarkCard renders in hospital detail view
- [x] Province-wide stats are accurate

### Temporal Patterns
- [x] Hour-of-day returns 24 entries with correct stats
- [x] Day-of-week returns 7 entries with correct stats
- [x] Peak/quiet insights are correct
- [x] Weekend vs weekday ratio computed
- [x] Charts render correctly with Recharts
- [x] Tab switching works

### Regional Intelligence
- [x] Ontario regions seeded correctly
- [x] Hospital-region mapping is accurate
- [x] Regional aggregate stats computed
- [x] RegionDashboard renders region cards
- [x] RegionSelector filters hospital list

### System Trends
- [x] Province-wide monthly trend computed
- [x] Trend narrative generated correctly
- [x] SystemTrendChart renders with confidence band
- [x] Period toggles work (3m/6m/1y)
- [x] Analytics page brings all features together

### Operationalization
- [x] Missing region schema produces actionable setup response (not opaque 500)
- [x] Trends endpoint falls back to daily rollups when weekly/monthly data is absent
- [x] Bootstrap CLI applies migrations + seeds regions + backfills analytics aggregates
- [x] Analytics UI shows setup instructions when region schema is not initialized

### Region Coverage
- [x] Region mapping audit + auto-assignment CLI available
- [x] Override file for explicit hospital-to-region mapping precedence
- [x] Regions API exposes mapping coverage metrics
- [x] Regional dashboard displays mapping coverage status

---

## Success Criteria

1. **Benchmarking:** Any hospital can be ranked against provincial peers with correct percentile
2. **Temporal patterns:** Clear visualization of peak/quiet hours and weekend effects
3. **Regional intelligence:** Ontario hospitals grouped by health region with aggregate stats
4. **System trends:** A single chart showing "Ontario ER waits have [improved/worsened] X% over Y months"
5. **Narrative generation:** Machine-generated trend descriptions suitable for citation
6. **Analytics page:** A dedicated page that a health administrator would bookmark

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Insufficient historical data for trends | Can't show 6m/1y trends | Show whatever data exists; label time range accurately |
| Ontario Health region boundaries change | Hospital mapping becomes stale | Use seed file approach so mapping is easy to update |
| Small sample sizes for temporal patterns | Unreliable hour/day averages | Show sample count; grey out entries with <10 samples |
| Province-wide mean skewed by outliers | Misleading trend | Use median alongside mean; show range |

---

## Time Estimate

| Task | Hours |
|------|-------|
| Benchmarks API + service | 3-4 |
| BenchmarkCard component | 2-3 |
| Benchmark tests | 2-3 |
| Temporal patterns API + service | 3-4 |
| TemporalPatterns component + charts | 3-4 |
| Temporal pattern tests | 2-3 |
| Region seed data + schema | 2-3 |
| Region seed CLI | 1-2 |
| Region API + dashboard | 3-4 |
| Region tests | 1-2 |
| System trend API + service | 2-3 |
| SystemTrendChart component | 2-3 |
| Analytics page layout | 2-3 |
| Analytics page tests | 1-2 |
| **Total** | **29-41 hours** |
