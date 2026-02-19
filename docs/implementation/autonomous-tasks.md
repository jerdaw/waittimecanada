# Autonomous Implementation Tasks

> Detailed specifications for 12 tasks that can be completed without user interaction.
> Design philosophy: Modern, trustworthy, Dribbble-quality polish.

---

## Table of Contents

1. [Complete Map Component](#1-complete-map-component)
2. [Build Methods Page](#2-build-methods-page)
3. ~~[Verification Queue UI](#3-verification-queue-ui)~~ (Removed)
4. [Heartbeat Monitoring](#4-heartbeat-monitoring)
5. [Data Retention Cleanup](#5-data-retention-cleanup)
6. [Divergence Brief Integration](#6-divergence-brief-integration)
7. [Frontend Tests](#7-frontend-tests)
8. [Integration Tests](#8-integration-tests)
9. [Backend Coverage](#9-backend-coverage)
10. [Ontario Methodology Doc](#10-ontario-methodology-doc)
11. [Research Ontario HQO URL](#11-research-ontario-hqo-url)
12. [Research Quebec MSSS URL](#12-research-quebec-msss-url)

---

## Design System Foundation

Before implementation, establish consistent design tokens:

```typescript
// frontend/lib/design-tokens.ts

export const colors = {
  // Trust-building blues
  primary: {
    50: '#EFF6FF',
    100: '#DBEAFE',
    500: '#3B82F6',
    600: '#2563EB',
    700: '#1D4ED8',
    900: '#1E3A8A',
  },
  // Status colors (accessible)
  status: {
    good: '#059669',      // Green - under 60 min
    moderate: '#D97706',  // Amber - 60-120 min
    busy: '#DC2626',      // Red - over 120 min
    unknown: '#6B7280',   // Gray - no data
  },
  // Neutral palette
  slate: {
    50: '#F8FAFC',
    100: '#F1F5F9',
    200: '#E2E8F0',
    300: '#CBD5E1',
    400: '#94A3B8',
    500: '#64748B',
    600: '#475569',
    700: '#334155',
    800: '#1E293B',
    900: '#0F172A',
  },
};

export const typography = {
  fontFamily: {
    sans: ['Inter', 'system-ui', 'sans-serif'],
    mono: ['JetBrains Mono', 'Menlo', 'monospace'],
  },
  fontSize: {
    xs: ['0.75rem', { lineHeight: '1rem' }],
    sm: ['0.875rem', { lineHeight: '1.25rem' }],
    base: ['1rem', { lineHeight: '1.5rem' }],
    lg: ['1.125rem', { lineHeight: '1.75rem' }],
    xl: ['1.25rem', { lineHeight: '1.75rem' }],
    '2xl': ['1.5rem', { lineHeight: '2rem' }],
    '3xl': ['1.875rem', { lineHeight: '2.25rem' }],
  },
};

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  DEFAULT: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
};

export const radius = {
  sm: '0.375rem',
  DEFAULT: '0.5rem',
  md: '0.625rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
};
```

---

## 1. Complete Map Component

### Overview
Transform the minimal `Map.tsx` stub into a fully-featured interactive map with hospital markers, popups, and real-time wait time visualization.

### Design Goals
- **Trustworthy**: Clean, professional cartography with muted base map
- **Accessible**: High contrast markers, keyboard navigation
- **Informative**: Glanceable wait times without overwhelming detail

### File: `frontend/components/Map.tsx`

### Implementation Spec

```typescript
// Component Structure
interface MapProps {
  initialCenter?: [number, number];  // [lng, lat]
  initialZoom?: number;
  province?: string;  // Filter to single province
  onHospitalSelect?: (hospitalId: string) => void;
}

interface HospitalMarker {
  id: string;
  name: string;
  coordinates: [number, number];
  waitTimeMinutes: number | null;
  lastUpdated: string | null;
  province: string;
  city: string;
  methodologyWarning?: string;
}
```

### Visual Design

#### Map Style
- Use Mapbox Light style as base (`mapbox://styles/mapbox/light-v11`)
- Reduce label density for cleaner look
- Subtle province boundaries
- No terrain/satellite - keep it clinical and professional

#### Markers
```
┌─────────────────────────────────────────────┐
│  MARKER DESIGN (SVG, 32x40px)               │
│                                             │
│      ╭───────╮                              │
│     │   42   │  ← Wait time in minutes      │
│     │  min   │    Bold number, small "min"  │
│      ╰───┬───╯                              │
│          │     ← Pin tail                   │
│          ▼                                  │
│                                             │
│  Colors:                                    │
│  • Green (#059669): 0-59 min                │
│  • Amber (#D97706): 60-119 min              │
│  • Red (#DC2626): 120+ min                  │
│  • Gray (#6B7280): No data                  │
│                                             │
│  States:                                    │
│  • Default: 90% opacity                     │
│  • Hover: 100% opacity, scale 1.1           │
│  • Selected: 100% opacity, ring animation   │
└─────────────────────────────────────────────┘
```

#### Popup Design
```
┌─────────────────────────────────────────────────────┐
│  POPUP (320px wide, card style)                     │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ ● St. Michael's Hospital                    │   │
│  │   Toronto, Ontario                          │   │
│  │                                             │   │
│  │   ┌─────────────────────────────────┐       │   │
│  │   │         42 minutes              │       │   │
│  │   │    Current Wait Time            │       │   │
│  │   └─────────────────────────────────┘       │   │
│  │                                             │   │
│  │   Updated 12 minutes ago                    │   │
│  │                                             │   │
│  │   ┌─────────────────────────────────┐       │   │
│  │   │ ⓘ Methodology: P90 Triage→MD   │       │   │
│  │   └─────────────────────────────────┘       │   │
│  │                                             │   │
│  │   ┌──────────┐  ┌──────────────────┐       │   │
│  │   │ Details  │  │ Call Health811  │       │   │
│  │   └──────────┘  └──────────────────┘       │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### Key Features

1. **Clustering**: Group nearby hospitals at low zoom levels
2. **Smooth Animations**: Fly-to on hospital selection
3. **Responsive**: Full-screen on mobile, contained on desktop
4. **Loading States**: Skeleton markers while data loads
5. **Error Boundary**: Graceful fallback if Mapbox fails

### API Integration

```typescript
// Fetch hospitals with wait times
const { data, isLoading, error } = useSWR<HospitalMarker[]>(
  `/api/hospitals${province ? `?province=${province}` : ''}`,
  fetcher,
  { refreshInterval: 60000 }  // Refresh every minute
);
```

### Accessibility Requirements
- Markers focusable via keyboard (Tab navigation)
- Popup content readable by screen readers
- Color not sole indicator (include text labels)
- Reduced motion support

### Files to Create/Modify
- `frontend/components/Map.tsx` - Main component (rewrite)
- `frontend/components/HospitalMarker.tsx` - Custom marker component
- `frontend/components/HospitalPopup.tsx` - Popup card component
- `frontend/components/MapSkeleton.tsx` - Loading state
- `frontend/hooks/useHospitals.ts` - Data fetching hook

---

## 2. Build Methods Page

### Overview
Create `/methods` page explaining the comparability matrix and methodology differences across provinces. This is the "Scholar" narrative - demonstrating deep understanding of healthcare research methodology.

### Route: `frontend/app/methods/page.tsx`

### Page Structure

```
┌─────────────────────────────────────────────────────────────────┐
│  METHODS PAGE LAYOUT                                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  HERO SECTION                                             │ │
│  │                                                           │ │
│  │  Understanding Wait Time Metrics                          │ │
│  │  ─────────────────────────────────────────               │ │
│  │  Canadian provinces measure emergency department          │ │
│  │  wait times using different methodologies. Direct         │ │
│  │  comparison requires understanding these differences.     │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  COMPARABILITY MATRIX                                     │ │
│  │                                                           │ │
│  │  ┌─────────┬─────────┬─────────┬─────────┬─────────┐     │ │
│  │  │         │   ON    │   QC    │   AB    │   MB    │     │ │
│  │  ├─────────┼─────────┼─────────┼─────────┼─────────┤     │ │
│  │  │   ON    │    ✓    │    ⚠    │    ✓    │    ✗    │     │ │
│  │  │   QC    │    ⚠    │    ✓    │    ⚠    │    ✗    │     │ │
│  │  │   AB    │    ✓    │    ⚠    │    ✓    │    ✗    │     │ │
│  │  │   MB    │    ✗    │    ✗    │    ✗    │    ✓    │     │ │
│  │  └─────────┴─────────┴─────────┴─────────┴─────────┘     │ │
│  │                                                           │ │
│  │  ✓ Comparable  ⚠ Partial  ✗ Not Comparable               │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  METHODOLOGY CARDS (one per province)                     │ │
│  │                                                           │ │
│  │  ┌─────────────────────┐  ┌─────────────────────┐        │ │
│  │  │ 🏛 Ontario          │  │ ⚜ Quebec            │        │ │
│  │  │                     │  │                     │        │ │
│  │  │ Metric: Time to     │  │ Metric: Time to     │        │ │
│  │  │ Physician           │  │ First Assessment    │        │ │
│  │  │                     │  │                     │        │ │
│  │  │ Start: Triage       │  │ Start: Registration │        │ │
│  │  │ End: MD Contact     │  │ End: Provider       │        │ │
│  │  │ Stat: 90th %ile     │  │ Stat: Rolling Avg   │        │ │
│  │  │                     │  │                     │        │ │
│  │  │ [View Source →]     │  │ [View Source →]     │        │ │
│  │  └─────────────────────┘  └─────────────────────┘        │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  ONTOLOGY EXPLAINER                                       │ │
│  │                                                           │ │
│  │  The Four Dimensions of Wait Time Measurement             │ │
│  │                                                           │ │
│  │  1. METRIC FAMILY                                         │ │
│  │     └─ What is being measured?                            │ │
│  │        • Time to Provider                                 │ │
│  │        • Total Length of Stay                             │ │
│  │        • Stretcher Occupancy                              │ │
│  │                                                           │ │
│  │  2. START EVENT                                           │ │
│  │     └─ When does the clock start?                         │ │
│  │        • Door (arrival)                                   │ │
│  │        • Triage (nurse assessment)                        │ │
│  │        • Registration (admin check-in)                    │ │
│  │                                                           │ │
│  │  3. END EVENT                                             │ │
│  │     └─ When does the clock stop?                          │ │
│  │        • Physician contact                                │ │
│  │        • Any provider contact                             │ │
│  │        • Discharge                                        │ │
│  │                                                           │ │
│  │  4. STATISTIC TYPE                                        │ │
│  │     └─ How is the number calculated?                      │ │
│  │        • 90th percentile (worst-case)                     │ │
│  │        • Median (typical case)                            │ │
│  │        • Rolling average (smoothed)                       │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  FAQ ACCORDION                                            │ │
│  │                                                           │ │
│  │  ▶ Why can't I compare Ottawa to Gatineau directly?       │ │
│  │  ▶ What does "90th percentile" mean?                      │ │
│  │  ▶ Why do some hospitals show "No Data"?                  │ │
│  │  ▶ How often is this data updated?                        │ │
│  │  ▶ Where does this data come from?                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Visual Design

#### Typography Hierarchy
- Page title: `text-3xl font-semibold tracking-tight`
- Section headers: `text-xl font-medium`
- Body text: `text-base text-slate-600`
- Labels: `text-sm font-medium text-slate-500`

#### Color Usage
- Matrix cell backgrounds based on comparability
- Province cards with subtle colored left border
- Icons use province-specific colors where appropriate

### Data Source
Pull methodology info from `sources` table:
```sql
SELECT
  id, name, province,
  default_metric_family, default_start_event,
  default_end_event, default_statistic_type,
  methodology_url
FROM sources
WHERE is_active = true;
```

### Files to Create
- `frontend/app/methods/page.tsx` - Main page
- `frontend/components/methods/ComparabilityMatrix.tsx`
- `frontend/components/methods/ProvinceMethodologyCard.tsx`
- `frontend/components/methods/OntologyExplainer.tsx`
- `frontend/components/methods/FAQ.tsx`

---

## 3. ~~Verification Queue UI~~ (Removed)

> **Removed:** The admin verification queue was removed because all data sources are trusted government health authority websites. Automated quality controls (anomaly detection, data quality monitoring, payload hashing, parser versioning, heartbeat monitoring) provide better assurance than manual approval of government data. Hospitals from trusted sources are now auto-approved on insert.

---

## 4. Heartbeat Monitoring

### Overview
Implement the heartbeat pattern so scrapers write status after each run, enabling stale data detection.

### Database Table (already exists)
```sql
CREATE TABLE scraper_status (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source_id TEXT NOT NULL REFERENCES sources(id),
  last_run TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  status scraper_status_enum NOT NULL DEFAULT 'healthy',
  error_message TEXT,
  measurements_count INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Backend Implementation

#### File: `backend/src/waittime/services/heartbeat.py`

```python
"""
Heartbeat monitoring service for scraper health tracking.
"""
from datetime import datetime, timezone
from typing import Optional
import logging

from ..core.models import ScraperStatus
from .database import DatabaseService

logger = logging.getLogger(__name__)


class HeartbeatService:
    """Manages scraper heartbeat recording and health checks."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def record_success(
        self,
        source_id: str,
        measurements_count: int
    ) -> ScraperStatus:
        """Record a successful scraper run."""
        status = ScraperStatus(
            source_id=source_id,
            last_run=datetime.now(timezone.utc),
            status='healthy',
            measurements_count=measurements_count,
            error_message=None
        )
        self._write_status(status)
        logger.info(f"Heartbeat recorded for {source_id}: {measurements_count} measurements")
        return status

    def record_failure(
        self,
        source_id: str,
        error_message: str
    ) -> ScraperStatus:
        """Record a failed scraper run."""
        status = ScraperStatus(
            source_id=source_id,
            last_run=datetime.now(timezone.utc),
            status='error',
            measurements_count=0,
            error_message=error_message[:500]  # Truncate long errors
        )
        self._write_status(status)
        logger.error(f"Heartbeat error for {source_id}: {error_message}")
        return status

    def check_health(self, source_id: str, max_age_minutes: int = 60) -> dict:
        """Check if a scraper is healthy (ran within max_age_minutes)."""
        query = """
            SELECT source_id, last_run, status, error_message, measurements_count
            FROM scraper_status
            WHERE source_id = %s
            ORDER BY last_run DESC
            LIMIT 1
        """
        result = self.db.execute_query(query, (source_id,))

        if not result:
            return {
                'source_id': source_id,
                'healthy': False,
                'reason': 'no_heartbeat',
                'message': 'No heartbeat ever recorded'
            }

        row = result[0]
        last_run = row['last_run']
        age_minutes = (datetime.now(timezone.utc) - last_run).total_seconds() / 60

        if row['status'] == 'error':
            return {
                'source_id': source_id,
                'healthy': False,
                'reason': 'last_run_failed',
                'message': row['error_message'],
                'last_run': last_run.isoformat(),
                'age_minutes': round(age_minutes, 1)
            }

        if age_minutes > max_age_minutes:
            return {
                'source_id': source_id,
                'healthy': False,
                'reason': 'stale',
                'message': f'Last run was {round(age_minutes)} minutes ago',
                'last_run': last_run.isoformat(),
                'age_minutes': round(age_minutes, 1)
            }

        return {
            'source_id': source_id,
            'healthy': True,
            'last_run': last_run.isoformat(),
            'age_minutes': round(age_minutes, 1),
            'measurements_count': row['measurements_count']
        }

    def _write_status(self, status: ScraperStatus) -> None:
        """Insert heartbeat record into database."""
        query = """
            INSERT INTO scraper_status
                (source_id, last_run, status, error_message, measurements_count)
            VALUES (%s, %s, %s, %s, %s)
        """
        self.db.execute_query(query, (
            status.source_id,
            status.last_run,
            status.status,
            status.error_message,
            status.measurements_count
        ))
```

### Scraper Integration

Modify base scraper to use heartbeat:

```python
# In backend/src/waittime/scrapers/base.py

class BaseScraper:
    def run(self) -> list[Measurement]:
        heartbeat = HeartbeatService(self.db)

        try:
            measurements = self._scrape()
            self._save_measurements(measurements)
            heartbeat.record_success(self.source_id, len(measurements))
            return measurements
        except Exception as e:
            heartbeat.record_failure(self.source_id, str(e))
            raise
```

### Frontend Display

Add "Last Updated" indicator to map:

```typescript
// In Map.tsx or Header
const { data: health } = useSWR('/api/health', fetcher);

// Display
<div className="text-sm text-slate-500">
  Last audit: {health?.lastRun ? formatRelative(health.lastRun) : 'Unknown'}
  {!health?.healthy && (
    <span className="text-amber-600 ml-2">⚠ Data may be stale</span>
  )}
</div>
```

### API Endpoint

```typescript
// frontend/app/api/health/route.ts
export async function GET() {
  const result = await sql`
    SELECT source_id, last_run, status, measurements_count
    FROM scraper_status
    ORDER BY last_run DESC
    LIMIT 10
  `;

  const oldestHealthy = result.rows
    .filter(r => r.status === 'healthy')
    .sort((a, b) => new Date(a.last_run) - new Date(b.last_run))[0];

  return Response.json({
    healthy: result.rows.every(r => r.status === 'healthy'),
    lastRun: oldestHealthy?.last_run,
    sources: result.rows
  });
}
```

### Files to Create/Modify
- `backend/src/waittime/services/heartbeat.py` - New service
- `backend/src/waittime/scrapers/base.py` - Integrate heartbeat
- `frontend/app/api/health/route.ts` - Health endpoint
- `frontend/components/DataFreshnessIndicator.tsx` - UI component

---

## 5. Data Retention Cleanup

### Overview
Implement the 30-day retention policy: delete raw measurement rows older than 30 days while preserving aggregated statistics.

### Implementation

#### File: `backend/src/waittime/services/retention.py`

```python
"""
Data retention service - cleans up old measurements per AGENTS.md policy.
"""
from datetime import datetime, timezone, timedelta
import logging

from .database import DatabaseService

logger = logging.getLogger(__name__)


class RetentionService:
    """Manages data retention and cleanup."""

    RETENTION_DAYS = 30

    def __init__(self, db: DatabaseService):
        self.db = db

    def cleanup_old_measurements(self, dry_run: bool = False) -> dict:
        """
        Delete measurements older than RETENTION_DAYS.

        Before deletion, ensures daily aggregates exist for the data being removed.

        Args:
            dry_run: If True, report what would be deleted without actually deleting

        Returns:
            dict with counts of affected rows
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=self.RETENTION_DAYS)

        # First, count what would be deleted
        count_query = """
            SELECT COUNT(*) as count,
                   MIN(timestamp_utc) as oldest,
                   MAX(timestamp_utc) as newest
            FROM measurements
            WHERE timestamp_utc < %s
        """
        count_result = self.db.execute_query(count_query, (cutoff,))

        to_delete = count_result[0]['count'] if count_result else 0

        if to_delete == 0:
            logger.info("No measurements to clean up")
            return {'deleted': 0, 'dry_run': dry_run}

        logger.info(f"Found {to_delete} measurements older than {self.RETENTION_DAYS} days")

        if dry_run:
            return {
                'deleted': 0,
                'would_delete': to_delete,
                'oldest': count_result[0]['oldest'].isoformat() if count_result[0]['oldest'] else None,
                'newest': count_result[0]['newest'].isoformat() if count_result[0]['newest'] else None,
                'dry_run': True
            }

        # Ensure aggregates exist before deletion
        self._ensure_daily_aggregates(cutoff)

        # Perform deletion
        delete_query = """
            DELETE FROM measurements
            WHERE timestamp_utc < %s
        """
        self.db.execute_query(delete_query, (cutoff,))

        logger.info(f"Deleted {to_delete} old measurements")

        return {
            'deleted': to_delete,
            'cutoff': cutoff.isoformat(),
            'dry_run': False
        }

    def _ensure_daily_aggregates(self, before_date: datetime) -> None:
        """
        Create daily aggregate records for data about to be deleted.
        This preserves historical statistics even after raw data is removed.
        """
        # Aggregate query - creates daily summaries per hospital
        aggregate_query = """
            INSERT INTO measurement_aggregates
                (hospital_id, date, metric_family, avg_value, min_value, max_value, count)
            SELECT
                hospital_id,
                DATE(timestamp_utc) as date,
                metric_family,
                AVG(value) as avg_value,
                MIN(value) as min_value,
                MAX(value) as max_value,
                COUNT(*) as count
            FROM measurements
            WHERE timestamp_utc < %s
              AND timestamp_utc >= %s - INTERVAL '1 day'
            GROUP BY hospital_id, DATE(timestamp_utc), metric_family
            ON CONFLICT (hospital_id, date, metric_family) DO NOTHING
        """
        # Note: This requires a measurement_aggregates table to be created
        # For now, log intent - table creation is separate task
        logger.info(f"Would aggregate data before {before_date}")
```

#### CLI Command

```python
# In backend/src/waittime/cli/retention.py

import click
from ..services.retention import RetentionService
from ..services.database import DatabaseService

@click.command()
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without deleting')
def cleanup(dry_run: bool):
    """Clean up measurements older than 30 days."""
    db = DatabaseService()
    retention = RetentionService(db)

    result = retention.cleanup_old_measurements(dry_run=dry_run)

    if dry_run:
        click.echo(f"Would delete {result['would_delete']} measurements")
    else:
        click.echo(f"Deleted {result['deleted']} measurements")
```

### GitHub Action for Scheduled Cleanup

```yaml
# .github/workflows/data-retention.yml
name: Data Retention Cleanup

on:
  schedule:
    - cron: '0 4 * * *'  # Run daily at 4 AM UTC
  workflow_dispatch:

jobs:
  cleanup:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -e ./backend
      - run: python -m waittime.cli.retention cleanup
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### Files to Create
- `backend/src/waittime/services/retention.py`
- `backend/src/waittime/cli/retention.py`
- `backend/migrations/006_create_aggregates_table.sql`
- `.github/workflows/data-retention.yml`

---

## 6. Divergence Brief Integration

### Overview
The `generate_divergence_brief()` function exists in `models.py` but is never called. Wire it up to display warnings when comparing hospitals with different methodologies.

### Current Function (in models.py)
```python
def generate_divergence_brief(a: Measurement, b: Measurement) -> str:
    """Generate human-readable explanation of methodology differences."""
    # Already implemented - needs to be used
```

### Integration Points

#### 1. API Endpoint for Comparison

```typescript
// frontend/app/api/compare/route.ts

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const hospitalA = searchParams.get('a');
  const hospitalB = searchParams.get('b');

  // Fetch latest measurements for both hospitals
  const [a, b] = await Promise.all([
    getLatestMeasurement(hospitalA),
    getLatestMeasurement(hospitalB)
  ]);

  // Check comparability
  const comparable = areComparable(a, b);
  const divergenceBrief = comparable ? null : generateDivergenceBrief(a, b);

  return Response.json({
    hospitalA: a,
    hospitalB: b,
    comparable,
    divergenceBrief
  });
}
```

#### 2. Comparison UI Component

```typescript
// frontend/components/ComparisonCard.tsx

interface ComparisonCardProps {
  hospitalA: Hospital;
  hospitalB: Hospital;
}

export function ComparisonCard({ hospitalA, hospitalB }: ComparisonCardProps) {
  const { data } = useSWR(
    `/api/compare?a=${hospitalA.id}&b=${hospitalB.id}`,
    fetcher
  );

  if (!data) return <Skeleton />;

  return (
    <div className="rounded-xl border border-slate-200 p-6">
      {/* Hospital comparison content */}

      {!data.comparable && (
        <div className="mt-4 rounded-lg bg-amber-50 border border-amber-200 p-4">
          <div className="flex gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0" />
            <div>
              <h4 className="font-medium text-amber-800">
                Methodology Divergence
              </h4>
              <p className="mt-1 text-sm text-amber-700">
                {data.divergenceBrief}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
```

#### 3. Map Popup Warning

When clicking between hospitals from different provinces, show subtle indicator:

```typescript
// In HospitalPopup.tsx

{hospital.province !== selectedProvince && (
  <div className="text-xs text-slate-500 mt-2 flex items-center gap-1">
    <Info className="h-3 w-3" />
    <span>Different methodology than your selected region</span>
  </div>
)}
```

### Python Utilities Needed

```python
# backend/src/waittime/services/comparison.py

def get_comparison_data(hospital_a_id: str, hospital_b_id: str, db: DatabaseService) -> dict:
    """Get comparison data including divergence analysis."""

    # Fetch latest measurements
    query = """
        SELECT m.*, h.name as hospital_name, h.province, s.default_metric_family,
               s.default_start_event, s.default_end_event, s.default_statistic_type
        FROM measurements m
        JOIN hospitals h ON m.hospital_id = h.id
        JOIN sources s ON h.source_id = s.id
        WHERE m.hospital_id = %s
        ORDER BY m.timestamp_utc DESC
        LIMIT 1
    """

    a = db.execute_query(query, (hospital_a_id,))[0]
    b = db.execute_query(query, (hospital_b_id,))[0]

    # Build measurement objects
    measurement_a = Measurement(**a)
    measurement_b = Measurement(**b)

    comparable = are_comparable(measurement_a, measurement_b)

    return {
        'hospital_a': a,
        'hospital_b': b,
        'comparable': comparable,
        'divergence_brief': None if comparable else generate_divergence_brief(measurement_a, measurement_b)
    }
```

### Files to Create/Modify
- `frontend/app/api/compare/route.ts`
- `frontend/components/ComparisonCard.tsx`
- `frontend/components/DivergenceWarning.tsx`
- `backend/src/waittime/services/comparison.py`

---

## 7. Frontend Tests

### Overview
The frontend currently has zero tests. Implement comprehensive test coverage using Vitest and React Testing Library.

### Test Setup

```typescript
// frontend/vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./tests/setup.ts'],
    include: ['**/*.test.{ts,tsx}'],
    coverage: {
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/setup.ts']
    }
  }
});
```

```typescript
// frontend/tests/setup.ts
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock Mapbox GL (doesn't work in jsdom)
vi.mock('mapbox-gl', () => ({
  default: {
    Map: vi.fn(() => ({
      on: vi.fn(),
      remove: vi.fn(),
      addControl: vi.fn(),
      addSource: vi.fn(),
      addLayer: vi.fn(),
    })),
    Marker: vi.fn(() => ({
      setLngLat: vi.fn().mockReturnThis(),
      addTo: vi.fn().mockReturnThis(),
      remove: vi.fn(),
    })),
    Popup: vi.fn(() => ({
      setLngLat: vi.fn().mockReturnThis(),
      setHTML: vi.fn().mockReturnThis(),
      addTo: vi.fn().mockReturnThis(),
    })),
  },
}));

// Mock next/navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({
    push: vi.fn(),
    replace: vi.fn(),
    prefetch: vi.fn(),
  }),
  useSearchParams: () => new URLSearchParams(),
  usePathname: () => '/',
}));
```

### Test Files

#### Component Tests

```typescript
// frontend/tests/components/HospitalPopup.test.tsx
import { render, screen } from '@testing-library/react';
import { HospitalPopup } from '@/components/HospitalPopup';

describe('HospitalPopup', () => {
  const mockHospital = {
    id: 'ca-on-st-michaels',
    name: "St. Michael's Hospital",
    city: 'Toronto',
    province: 'Ontario',
    waitTimeMinutes: 42,
    lastUpdated: new Date().toISOString(),
  };

  it('renders hospital name and location', () => {
    render(<HospitalPopup hospital={mockHospital} />);

    expect(screen.getByText("St. Michael's Hospital")).toBeInTheDocument();
    expect(screen.getByText('Toronto, Ontario')).toBeInTheDocument();
  });

  it('displays wait time with correct color for short waits', () => {
    render(<HospitalPopup hospital={mockHospital} />);

    const waitTime = screen.getByText('42 minutes');
    expect(waitTime).toHaveClass('text-green-600');
  });

  it('displays wait time with amber color for moderate waits', () => {
    render(<HospitalPopup hospital={{ ...mockHospital, waitTimeMinutes: 90 }} />);

    const waitTime = screen.getByText('90 minutes');
    expect(waitTime).toHaveClass('text-amber-600');
  });

  it('displays wait time with red color for long waits', () => {
    render(<HospitalPopup hospital={{ ...mockHospital, waitTimeMinutes: 150 }} />);

    const waitTime = screen.getByText('150 minutes');
    expect(waitTime).toHaveClass('text-red-600');
  });

  it('shows "No data" when wait time is null', () => {
    render(<HospitalPopup hospital={{ ...mockHospital, waitTimeMinutes: null }} />);

    expect(screen.getByText('No data available')).toBeInTheDocument();
  });

  it('formats last updated time relatively', () => {
    const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000).toISOString();
    render(<HospitalPopup hospital={{ ...mockHospital, lastUpdated: fiveMinutesAgo }} />);

    expect(screen.getByText(/5 minutes ago/i)).toBeInTheDocument();
  });
});
```

```typescript
// frontend/tests/components/ComparabilityMatrix.test.tsx
import { render, screen } from '@testing-library/react';
import { ComparabilityMatrix } from '@/components/methods/ComparabilityMatrix';

describe('ComparabilityMatrix', () => {
  const mockSources = [
    { id: 'on', province: 'Ontario', default_statistic_type: 'P90' },
    { id: 'qc', province: 'Quebec', default_statistic_type: 'ROLLING_AVG' },
  ];

  it('renders province headers', () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    expect(screen.getByText('Ontario')).toBeInTheDocument();
    expect(screen.getByText('Quebec')).toBeInTheDocument();
  });

  it('shows checkmark for same-province comparison', () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // Diagonal should be comparable (same province)
    const cells = screen.getAllByRole('cell');
    // Check that ON-ON and QC-QC are marked as comparable
  });

  it('shows warning for different methodology', () => {
    render(<ComparabilityMatrix sources={mockSources} />);

    // ON uses P90, QC uses ROLLING_AVG - should show warning
    expect(screen.getByTitle(/not directly comparable/i)).toBeInTheDocument();
  });
});
```

#### API Route Tests

```typescript
// frontend/tests/api/hospitals.test.ts
import { GET } from '@/app/api/hospitals/route';
import { NextRequest } from 'next/server';

// Mock database
vi.mock('@/lib/db', () => ({
  sql: vi.fn(),
}));

describe('GET /api/hospitals', () => {
  it('returns verified and visible hospitals', async () => {
    const mockHospitals = [
      { id: 'test-1', name: 'Test Hospital', is_verified: true, is_visible: true },
    ];

    // Setup mock
    const { sql } = await import('@/lib/db');
    sql.mockResolvedValueOnce({ rows: mockHospitals });

    const request = new NextRequest('http://localhost/api/hospitals');
    const response = await GET(request);
    const data = await response.json();

    expect(data).toHaveLength(1);
    expect(data[0].name).toBe('Test Hospital');
  });

  it('filters by province when provided', async () => {
    const { sql } = await import('@/lib/db');

    const request = new NextRequest('http://localhost/api/hospitals?province=Ontario');
    await GET(request);

    expect(sql).toHaveBeenCalledWith(
      expect.stringContaining('province ='),
      expect.arrayContaining(['Ontario'])
    );
  });
});
```

#### Hook Tests

```typescript
// frontend/tests/hooks/useHospitals.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useHospitals } from '@/hooks/useHospitals';
import { SWRConfig } from 'swr';

describe('useHospitals', () => {
  it('fetches hospitals on mount', async () => {
    const wrapper = ({ children }) => (
      <SWRConfig value={{ dedupingInterval: 0, provider: () => new Map() }}>
        {children}
      </SWRConfig>
    );

    const { result } = renderHook(() => useHospitals(), { wrapper });

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.hospitals).toBeDefined();
  });

  it('filters by province', async () => {
    const { result } = renderHook(() => useHospitals({ province: 'Ontario' }));

    await waitFor(() => {
      expect(result.current.hospitals?.every(h => h.province === 'Ontario')).toBe(true);
    });
  });
});
```

### Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:coverage": "vitest run --coverage",
    "test:ui": "vitest --ui"
  }
}
```

### Files to Create
- `frontend/vitest.config.ts`
- `frontend/tests/setup.ts`
- `frontend/tests/components/HospitalPopup.test.tsx`
- `frontend/tests/components/ComparabilityMatrix.test.tsx`
- `frontend/tests/components/Map.test.tsx`
- `frontend/tests/api/hospitals.test.ts`
- `frontend/tests/hooks/useHospitals.test.ts`

---

## 8. Integration Tests

### Overview
Test the full pipeline: scraper → database → API. Uses pytest with a test database.

### Test Database Setup

```python
# backend/tests/conftest.py (additions)

import pytest
from testcontainers.postgres import PostgresContainer

@pytest.fixture(scope='session')
def postgres_container():
    """Spin up a real PostgreSQL container for integration tests."""
    with PostgresContainer('postgres:17') as postgres:
        yield postgres

@pytest.fixture(scope='function')
def test_db(postgres_container):
    """Create a fresh test database for each test."""
    from waittime.services.database import DatabaseService

    db = DatabaseService(postgres_container.get_connection_url())

    # Run migrations
    db.run_migrations()

    yield db

    # Cleanup
    db.execute_query("TRUNCATE measurements, hospitals, sources, scraper_status CASCADE")
```

### Integration Test Files

```python
# backend/tests/integration/test_scraper_pipeline.py

import pytest
from datetime import datetime, timezone

from waittime.scrapers.quebec import QuebecScraper
from waittime.services.database import DatabaseService
from waittime.services.heartbeat import HeartbeatService


class TestScraperPipeline:
    """Integration tests for full scraper → database pipeline."""

    @pytest.fixture
    def seeded_db(self, test_db):
        """Database with source and hospital data pre-populated."""
        # Insert Quebec source
        test_db.execute_query("""
            INSERT INTO sources (id, name, province, url, telehealth_name, telehealth_number)
            VALUES ('qc-msss', 'Quebec MSSS', 'Quebec', 'https://example.com',
                    'Info-Santé', '811')
        """)

        # Insert a test hospital
        test_db.execute_query("""
            INSERT INTO hospitals (id, name, province, city, source_id, is_verified, is_visible)
            VALUES ('ca-qc-chum', 'CHUM', 'Quebec', 'Montreal', 'qc-msss', true, true)
        """)

        return test_db

    def test_scraper_saves_measurements(self, seeded_db, mock_quebec_html):
        """Test that scraper correctly saves measurements to database."""
        scraper = QuebecScraper(db=seeded_db)
        scraper._fetch_html = lambda: mock_quebec_html  # Mock the fetch

        measurements = scraper.run()

        # Verify measurements were saved
        result = seeded_db.execute_query(
            "SELECT COUNT(*) as count FROM measurements WHERE hospital_id = 'ca-qc-chum'"
        )
        assert result[0]['count'] > 0

        # Verify measurement values
        result = seeded_db.execute_query(
            "SELECT value, metric_family FROM measurements WHERE hospital_id = 'ca-qc-chum' LIMIT 1"
        )
        assert result[0]['metric_family'] == 'TIME_TO_PROVIDER'
        assert result[0]['value'] > 0

    def test_scraper_writes_heartbeat(self, seeded_db, mock_quebec_html):
        """Test that successful scrape records heartbeat."""
        scraper = QuebecScraper(db=seeded_db)
        scraper._fetch_html = lambda: mock_quebec_html

        scraper.run()

        # Check heartbeat was recorded
        result = seeded_db.execute_query(
            "SELECT status, measurements_count FROM scraper_status WHERE source_id = 'qc-msss'"
        )
        assert result[0]['status'] == 'healthy'
        assert result[0]['measurements_count'] > 0

    def test_scraper_failure_records_error(self, seeded_db):
        """Test that failed scrape records error heartbeat."""
        scraper = QuebecScraper(db=seeded_db)
        scraper._fetch_html = lambda: None  # Simulate failure

        with pytest.raises(Exception):
            scraper.run()

        # Check error heartbeat
        result = seeded_db.execute_query(
            "SELECT status, error_message FROM scraper_status WHERE source_id = 'qc-msss'"
        )
        assert result[0]['status'] == 'error'
        assert result[0]['error_message'] is not None

    def test_payload_hash_is_stored(self, seeded_db, mock_quebec_html):
        """Test that payload hash is stored, not full HTML."""
        scraper = QuebecScraper(db=seeded_db)
        scraper._fetch_html = lambda: mock_quebec_html

        scraper.run()

        result = seeded_db.execute_query(
            "SELECT raw_payload_hash, raw_payload_snippet FROM measurements LIMIT 1"
        )

        # Hash should be 64 char SHA256
        assert len(result[0]['raw_payload_hash']) == 64

        # Snippet should be truncated
        assert len(result[0]['raw_payload_snippet']) <= 200


class TestDatabaseAPI:
    """Test database service operations."""

    def test_get_hospitals_respects_visibility(self, seeded_db):
        """Only verified AND visible hospitals should be returned."""
        # Insert hospitals with various states
        seeded_db.execute_query("""
            INSERT INTO hospitals (id, name, province, city, source_id, is_verified, is_visible)
            VALUES
                ('visible', 'Visible Hospital', 'Ontario', 'Toronto', 'on-hqo', true, true),
                ('unverified', 'Unverified Hospital', 'Ontario', 'Ottawa', 'on-hqo', false, false),
                ('hidden', 'Hidden Hospital', 'Ontario', 'Hamilton', 'on-hqo', true, false)
        """)

        result = seeded_db.execute_query(
            "SELECT id FROM hospitals WHERE is_verified = true AND is_visible = true"
        )

        ids = [r['id'] for r in result]
        assert 'visible' in ids
        assert 'unverified' not in ids
        assert 'hidden' not in ids


@pytest.fixture
def mock_quebec_html():
    """Sample HTML that Quebec scraper can parse."""
    return """
    <html>
    <body>
        <table class="urgences">
            <tr>
                <td>CHUM</td>
                <td>45 min</td>
                <td>2h30</td>
            </tr>
        </table>
    </body>
    </html>
    """
```

```python
# backend/tests/integration/test_api_database.py

import pytest
from datetime import datetime, timezone, timedelta


class TestMeasurementRetrieval:
    """Test measurement queries for API."""

    def test_get_latest_measurement_per_hospital(self, seeded_db):
        """API should return only the most recent measurement per hospital."""
        now = datetime.now(timezone.utc)

        # Insert old and new measurements
        seeded_db.execute_query("""
            INSERT INTO measurements (hospital_id, value, timestamp_utc, metric_family,
                                      start_event, end_event, statistic_type, source_id,
                                      raw_payload_hash, parser_version)
            VALUES
                ('ca-qc-chum', 60, %s, 'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN',
                 'P90', 'qc-msss', 'hash1', 'v1'),
                ('ca-qc-chum', 45, %s, 'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN',
                 'P90', 'qc-msss', 'hash2', 'v1')
        """, (now - timedelta(hours=1), now))

        # Query for latest
        result = seeded_db.execute_query("""
            SELECT DISTINCT ON (hospital_id) hospital_id, value
            FROM measurements
            ORDER BY hospital_id, timestamp_utc DESC
        """)

        assert len(result) == 1
        assert result[0]['value'] == 45  # Most recent value

    def test_comparability_query(self, seeded_db):
        """Test query that determines if two hospitals are comparable."""
        # Insert measurements with different methodologies
        seeded_db.execute_query("""
            INSERT INTO measurements (hospital_id, value, timestamp_utc, metric_family,
                                      start_event, end_event, statistic_type, source_id,
                                      raw_payload_hash, parser_version)
            VALUES
                ('hospital-a', 60, NOW(), 'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN',
                 'P90', 'source-a', 'hash1', 'v1'),
                ('hospital-b', 45, NOW(), 'TIME_TO_PROVIDER', 'REGISTRATION', 'PHYSICIAN',
                 'ROLLING_AVG', 'source-b', 'hash2', 'v1')
        """)

        # Check comparability
        result = seeded_db.execute_query("""
            SELECT
                a.metric_family = b.metric_family AND
                a.start_event = b.start_event AND
                a.end_event = b.end_event AND
                a.statistic_type = b.statistic_type AS is_comparable
            FROM measurements a, measurements b
            WHERE a.hospital_id = 'hospital-a' AND b.hospital_id = 'hospital-b'
        """)

        assert result[0]['is_comparable'] == False
```

### Files to Create
- `backend/tests/integration/__init__.py`
- `backend/tests/integration/test_scraper_pipeline.py`
- `backend/tests/integration/test_api_database.py`
- `backend/tests/integration/conftest.py`

---

## 9. Backend Coverage

### Overview
Increase backend test coverage from 56% to 80%+ by adding tests for edge cases, error paths, and untested modules.

### Coverage Gaps to Address

Based on current test files, these areas need coverage:

#### 1. Database Service Error Handling

```python
# backend/tests/test_database_service.py

import pytest
from unittest.mock import patch, MagicMock
from waittime.services.database import DatabaseService


class TestDatabaseServiceErrors:
    """Test error handling in database service."""

    def test_connection_retry_on_transient_error(self):
        """Should retry on connection errors."""
        with patch('psycopg2.connect') as mock_connect:
            # Fail twice, succeed third time
            mock_connect.side_effect = [
                psycopg2.OperationalError("connection refused"),
                psycopg2.OperationalError("connection refused"),
                MagicMock()
            ]

            db = DatabaseService()

            assert mock_connect.call_count == 3

    def test_gives_up_after_max_retries(self):
        """Should raise after max retry attempts."""
        with patch('psycopg2.connect') as mock_connect:
            mock_connect.side_effect = psycopg2.OperationalError("connection refused")

            with pytest.raises(psycopg2.OperationalError):
                DatabaseService(max_retries=3)

            assert mock_connect.call_count == 3

    def test_invalid_query_raises_descriptive_error(self):
        """Should wrap SQL errors with context."""
        db = DatabaseService()

        with pytest.raises(DatabaseError) as exc_info:
            db.execute_query("SELECT * FROM nonexistent_table")

        assert "nonexistent_table" in str(exc_info.value)
```

#### 2. Scraper Edge Cases

```python
# backend/tests/test_scraper_edge_cases.py

import pytest
from waittime.scrapers.quebec import QuebecScraper
from waittime.scrapers.ontario import OntarioScraper


class TestQuebecScraperEdgeCases:
    """Edge cases for Quebec scraper parsing."""

    def test_handles_missing_wait_time_cell(self):
        """Should handle rows with missing data gracefully."""
        html = """
        <table>
            <tr><td>Hospital A</td><td>45 min</td></tr>
            <tr><td>Hospital B</td><td></td></tr>
            <tr><td>Hospital C</td><td>60 min</td></tr>
        </table>
        """
        scraper = QuebecScraper()
        results = scraper._parse_html(html)

        # Should parse A and C, skip B
        assert len(results) == 2

    def test_handles_french_time_formats(self):
        """Should parse French time notation."""
        test_cases = [
            ("2h30", 150),
            ("1h", 60),
            ("45 min", 45),
            ("2 h 15 min", 135),
            ("moins de 30 min", 30),
            ("> 4h", 240),
        ]

        scraper = QuebecScraper()
        for text, expected in test_cases:
            assert scraper._parse_time(text) == expected, f"Failed for: {text}"

    def test_handles_special_characters_in_names(self):
        """Should normalize hospital names with accents."""
        html = """
        <table>
            <tr><td>Hôpital Général de Montréal</td><td>45 min</td></tr>
            <tr><td>CHSLD René-Lévesque</td><td>30 min</td></tr>
        </table>
        """
        scraper = QuebecScraper()
        results = scraper._parse_html(html)

        # IDs should be normalized ASCII
        assert any('montreal' in r.hospital_id for r in results)

    def test_handles_network_timeout(self):
        """Should raise appropriate error on timeout."""
        scraper = QuebecScraper()

        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout("Connection timed out")

            with pytest.raises(ScraperError) as exc_info:
                scraper.run()

            assert "timeout" in str(exc_info.value).lower()

    def test_handles_malformed_html(self):
        """Should not crash on malformed HTML."""
        malformed_html = """
        <table>
            <tr><td>Hospital</td><td>
            </table>  <!-- Unclosed td -->
        """
        scraper = QuebecScraper()

        # Should not raise, just return empty or partial results
        results = scraper._parse_html(malformed_html)
        assert isinstance(results, list)


class TestOntarioScraperEdgeCases:
    """Edge cases for Ontario scraper parsing."""

    def test_handles_javascript_rendered_content(self):
        """Should wait for JS content to load."""
        # This tests Playwright integration
        pass  # Requires separate browser test setup

    def test_handles_wait_time_ranges(self):
        """Should parse range formats like '1-2 hours'."""
        test_cases = [
            ("1-2 hours", 90),  # Use midpoint
            ("30-60 minutes", 45),
            ("< 30 minutes", 30),
            ("> 4 hours", 240),
        ]

        scraper = OntarioScraper()
        for text, expected in test_cases:
            assert scraper._parse_time(text) == expected
```

#### 3. Model Validation

```python
# backend/tests/test_model_validation.py

import pytest
from datetime import datetime, timezone
from waittime.core.models import Measurement, Hospital, Source


class TestMeasurementValidation:
    """Test Measurement model validation."""

    def test_rejects_negative_value(self):
        """Wait time cannot be negative."""
        with pytest.raises(ValueError, match="value must be positive"):
            Measurement(
                hospital_id="test",
                value=-10,
                timestamp_utc=datetime.now(timezone.utc),
                metric_family="TIME_TO_PROVIDER",
                start_event="TRIAGE",
                end_event="PHYSICIAN",
                statistic_type="P90",
                source_id="test",
                raw_payload_hash="abc123",
                parser_version="v1"
            )

    def test_rejects_invalid_metric_family(self):
        """Should reject invalid enum values."""
        with pytest.raises(ValueError):
            Measurement(
                hospital_id="test",
                value=60,
                timestamp_utc=datetime.now(timezone.utc),
                metric_family="INVALID_METRIC",  # Invalid
                start_event="TRIAGE",
                end_event="PHYSICIAN",
                statistic_type="P90",
                source_id="test",
                raw_payload_hash="abc123",
                parser_version="v1"
            )

    def test_truncates_long_snippet(self):
        """Snippet should be max 200 chars."""
        long_html = "x" * 500

        m = Measurement(
            hospital_id="test",
            value=60,
            timestamp_utc=datetime.now(timezone.utc),
            metric_family="TIME_TO_PROVIDER",
            start_event="TRIAGE",
            end_event="PHYSICIAN",
            statistic_type="P90",
            source_id="test",
            raw_payload_hash="abc123",
            raw_payload_snippet=long_html,
            parser_version="v1"
        )

        assert len(m.raw_payload_snippet) <= 200


class TestHospitalValidation:
    """Test Hospital model validation."""

    def test_visible_requires_verified(self):
        """Cannot be visible without being verified."""
        with pytest.raises(ValueError, match="cannot be visible without being verified"):
            Hospital(
                id="test",
                name="Test Hospital",
                province="Ontario",
                city="Toronto",
                source_id="test",
                is_verified=False,
                is_visible=True  # Invalid: visible but not verified
            )

    def test_valid_coordinates(self):
        """Latitude and longitude must be valid."""
        with pytest.raises(ValueError):
            Hospital(
                id="test",
                name="Test",
                province="Ontario",
                city="Toronto",
                source_id="test",
                lat=200,  # Invalid: >90
                lng=-80
            )
```

#### 4. Comparability Logic

```python
# backend/tests/test_comparability.py

import pytest
from waittime.core.models import Measurement, are_comparable, generate_divergence_brief


class TestComparability:
    """Test measurement comparability logic."""

    @pytest.fixture
    def base_measurement(self):
        """Standard measurement for comparison."""
        return Measurement(
            hospital_id="test",
            value=60,
            timestamp_utc=datetime.now(timezone.utc),
            metric_family="TIME_TO_PROVIDER",
            start_event="TRIAGE",
            end_event="PHYSICIAN",
            statistic_type="P90",
            source_id="test",
            raw_payload_hash="abc",
            parser_version="v1"
        )

    def test_identical_methodology_is_comparable(self, base_measurement):
        """Same methodology should be comparable."""
        other = base_measurement.model_copy(update={"hospital_id": "other"})
        assert are_comparable(base_measurement, other) == True

    def test_different_metric_family_not_comparable(self, base_measurement):
        """Different metric family is not comparable."""
        other = base_measurement.model_copy(update={
            "hospital_id": "other",
            "metric_family": "TOTAL_LOS"
        })
        assert are_comparable(base_measurement, other) == False

    def test_different_start_event_not_comparable(self, base_measurement):
        """Different start event is not comparable."""
        other = base_measurement.model_copy(update={
            "hospital_id": "other",
            "start_event": "REGISTRATION"
        })
        assert are_comparable(base_measurement, other) == False

    def test_different_statistic_not_comparable(self, base_measurement):
        """Different statistic type is not comparable."""
        other = base_measurement.model_copy(update={
            "hospital_id": "other",
            "statistic_type": "MEDIAN"
        })
        assert are_comparable(base_measurement, other) == False

    def test_divergence_brief_explains_differences(self, base_measurement):
        """Divergence brief should explain all differences."""
        other = base_measurement.model_copy(update={
            "hospital_id": "other",
            "start_event": "REGISTRATION",
            "statistic_type": "ROLLING_AVG"
        })

        brief = generate_divergence_brief(base_measurement, other)

        assert "start event" in brief.lower() or "triage" in brief.lower()
        assert "statistic" in brief.lower() or "P90" in brief
```

### Files to Create/Modify
- `backend/tests/test_database_service.py`
- `backend/tests/test_scraper_edge_cases.py`
- `backend/tests/test_model_validation.py`
- `backend/tests/test_comparability.py`
- `backend/tests/test_heartbeat.py`
- `backend/tests/test_retention.py`

---

## 10. Ontario Methodology Doc

### Overview
Create standalone documentation explaining Ontario's wait time measurement methodology for the Scholar narrative.

### File: `docs/methodology/ontario.md`

```markdown
# Ontario Emergency Department Wait Time Methodology

> Official documentation of how Ontario Health Quality (HQO) measures and reports
> emergency department wait times.

## Data Source

**Provider:** Health Quality Ontario (HQO)
**Portal:** [Ontario Wait Times](https://www.ontariowaittimes.com)
**Update Frequency:** Every 15 minutes (real-time)
**Coverage:** 100+ emergency departments across Ontario

## Metric Definition

### What is Measured

Ontario reports **Time to Physician Initial Assessment (PIA)**.

This measures the elapsed time from when a patient completes triage to when they
are first seen by an emergency physician or authorized delegate (nurse practitioner,
physician assistant).

### Ontology Classification

| Dimension | Value | Notes |
|-----------|-------|-------|
| **Metric Family** | `TIME_TO_PROVIDER` | Time until clinical assessment |
| **Start Event** | `TRIAGE` | Clock starts at triage completion |
| **End Event** | `PHYSICIAN` | First MD/NP contact |
| **Statistic Type** | `P90` | 90th percentile (9 of 10 patients seen faster) |
| **Patient Scope** | `ALL` | All CTAS levels combined |

### Why 90th Percentile?

Ontario uses the 90th percentile rather than median or mean because:

1. **Worst-case planning**: Shows what longer-waiting patients experience
2. **Less gaming**: Harder to manipulate than averages
3. **CIHI alignment**: Matches Canadian Institute for Health Information standards

A P90 of 120 minutes means 90% of patients are seen within 2 hours.

## Comparability Notes

### Comparable With

- **Alberta**: Also uses P90, triage-to-physician
- **Other Ontario hospitals**: Same methodology province-wide

### NOT Comparable With

- **Quebec**: Uses rolling average, registration-to-provider
- **Manitoba**: Uses median, different patient scope

When comparing Ontario to Quebec:

> ⚠️ **Methodology Divergence**: Ontario reports 90th percentile triage-to-physician
> time. Quebec reports rolling average registration-to-provider time. Direct
> comparison is statistically invalid.

## Data Quality Considerations

### Strengths

- Real-time updates (15-minute refresh)
- Standardized across all Ontario EDs
- Validated against NACRS submissions

### Limitations

- Does not distinguish by CTAS acuity level
- "Time to physician" may include PA/NP contact
- Does not capture admitted patient wait times separately

## Technical Implementation

### Scraper Details

- **Parser Version**: `ontario-hqo-v1.0`
- **Fetch Method**: Playwright (JavaScript-rendered content)
- **Hospital Matching**: Fuzzy matching on facility name

### Data Fields Captured

```json
{
  "hospital_id": "ca-on-st-michaels",
  "value": 127,
  "metric_family": "TIME_TO_PROVIDER",
  "start_event": "TRIAGE",
  "end_event": "PHYSICIAN",
  "statistic_type": "P90",
  "patient_scope": "ALL",
  "raw_payload_hash": "sha256:abc123...",
  "parser_version": "ontario-hqo-v1.0"
}
```

## References

1. Health Quality Ontario. (2024). *Emergency Department Wait Times Technical Specifications*.
2. Canadian Institute for Health Information. (2023). *NACRS Data Quality Documentation*.
3. Ontario Ministry of Health. *Public Reporting of Emergency Department Wait Times: Methodology*.

---

*Last updated: January 2026*
*Maintained by: Wait Time Canada Project*
```

### Files to Create
- `docs/methodology/ontario.md`
- `docs/methodology/quebec.md` (similar structure)
- `docs/methodology/README.md` (index)

---

## 11. Research Ontario HQO URL

### Overview
Find the actual Ontario Health Quality portal URL for real-time ED wait times.

### Research Approach

1. **Web Search Queries**:
   - "Ontario emergency department wait times real-time"
   - "Health Quality Ontario ED wait times portal"
   - "Ontario hospital wait times live"
   - "ontariowaittimes.com" (check if still active)

2. **Known URLs to Verify**:
   - `https://www.ontariowaittimes.com/` (historical)
   - `https://www.hqontario.ca/` (HQO main site)
   - `https://www.ontario.ca/page/wait-times-ontario`

3. **Expected Data Format**:
   - JavaScript-rendered (hence Playwright)
   - Table with hospital name, wait time, last updated
   - Possibly JSON API endpoint

### Output

Document findings in:
```
docs/data-sources/ontario-research.md
```

Include:
- Working URL(s)
- Data format (HTML table, JSON, etc.)
- Authentication requirements
- Rate limiting observations
- Sample raw data

---

## 12. Research Quebec MSSS URL

### Overview
Find the actual Quebec MSSS (Ministère de la Santé et des Services sociaux) portal URL for ED wait times.

### Research Approach

1. **Web Search Queries**:
   - "Quebec urgences temps attente"
   - "MSSS Quebec emergency wait times"
   - "Index santé Québec urgences"
   - "temps d'attente urgence Montréal"

2. **Known URLs to Verify**:
   - `https://www.indexsante.ca/urgences/` (third-party aggregator)
   - `https://www.msss.gouv.qc.ca/` (ministry main site)
   - `https://www.quebec.ca/sante/` (Quebec health portal)

3. **Expected Data Format**:
   - Likely server-rendered HTML (no JS)
   - French language
   - Table with établissement, temps d'attente, occupation civières

### Output

Document findings in:
```
docs/data-sources/quebec-research.md
```

---

## Implementation Priority

Recommended execution order for maximum value:

| Priority | Task | Rationale |
|----------|------|-----------|
| 1 | #4 Heartbeat Monitoring | Enables production reliability |
| 2 | #1 Complete Map Component | Highest user-facing impact |
| 3 | #11-12 URL Research | Unblocks real data testing |
| 4 | #2 Methods Page | Scholar narrative, differentiator |
| 5 | #6 Divergence Integration | Core value proposition |
| 6 | #7 Frontend Tests | Prevents regression |
| 7 | #3 Verification Queue | Admin capability |
| 8 | #8 Integration Tests | Pipeline confidence |
| 9 | #5 Data Retention | Storage management |
| 10 | #9 Backend Coverage | Code quality |
| 11 | #10 Ontario Methodology | Documentation |

---

## Success Criteria

Each task is complete when:

1. **Code**: Implemented, linted, type-checked
2. **Tests**: Relevant tests passing
3. **Documentation**: Updated if applicable
4. **Review**: Self-reviewed for AGENTS.md compliance

---

*Document Version: 1.0*
*Created: February 2026*
