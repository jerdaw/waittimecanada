# Milestone 12: Research Infrastructure

> **Priority:** MEDIUM - Enhances "Scholar" narrative, positions as research tool
> **Estimated Effort:** 3-4 days
> **Admissions Appeal:** Scholar (research methodology), Leader (infrastructure thinking)

---

## Implementation Status (Updated 2026-02-08)

- Citation-ready export: implemented
- Dead Man's Switch + health endpoint: implemented
- Scraper runtime pipeline hardening: implemented
  - `backend/src/waittime/cli/scraper.py` now instantiates scrapers with `db` and delegates persistence/heartbeat to `BaseScraper.run(...)`
  - hospital prerequisite upserts are executed through a `before_save` hook so the shared run path remains authoritative
- Occupancy analytics contract: implemented with explicit availability states
  - `/api/analytics/occupancy` now returns `not_available_yet`, `no_reporting_data`, or `available`
  - `/analytics` now renders clear "Occupancy metrics not available yet" messaging when source
    fields are absent
- Remaining for full occupancy rollout:
  - ingest source occupancy fields once published by provincial feeds
  - backfill and validate occupancy aggregates for interpretation

---

## Overview

These features position WaitTime Canada as research infrastructure, not just a consumer app. The citation-ready export lets researchers use the data properly, while the alert system ensures operational reliability.

**Narrative for Applications:**
> "I designed the system to be citation-ready—every data export includes methodology tags so researchers can properly attribute and compare data. This isn't just a wait time tracker; it's a Health Systems Observatory that produces auditable, reproducible datasets."

---

## Phase 1: Citation-Ready Data Export (Days 1-2)

### 1.1 API Endpoint Design

**Endpoint:** `GET /api/export`

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `province` | string | Filter by province (ON, QC, AB) |
| `start_date` | ISO date | Start of date range |
| `end_date` | ISO date | End of date range |
| `format` | string | `csv` (default) or `json` |
| `include_methodology` | boolean | Include all ontology columns (default: true) |

**Response Headers:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="waittime-canada-export-2026-02-04.csv"
X-Data-License: CC-BY-4.0
X-Citation: "WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca"
```

### 1.2 CSV Schema

**Columns:**
```csv
timestamp_utc,hospital_id,hospital_name,province,city,latitude,longitude,wait_time_minutes,metric_family,start_event,end_event,statistic_type,patient_scope,source_id,source_name,methodology_url
```

**Example Row:**
```csv
2026-02-04T15:30:00Z,ca-on-toronto-general,Toronto General Hospital,ON,Toronto,43.6591,-79.3878,145,TIME_TO_PROVIDER,TRIAGE,PHYSICIAN,P90,ALL,ontario-health,Ontario Health,https://www.hqontario.ca/...
```

### 1.3 Implementation

**File:** `frontend/app/api/export/route.ts`

```typescript
import { NextRequest, NextResponse } from 'next/server';
import { getDb } from '@/utils/db';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const province = searchParams.get('province');
  const startDate = searchParams.get('start_date');
  const endDate = searchParams.get('end_date');
  const format = searchParams.get('format') || 'csv';
  const includeMethodology = searchParams.get('include_methodology') !== 'false';

  const sql = getDb();

  // Build query with filters
  let query = sql`
    SELECT
      m.timestamp_utc,
      m.hospital_id,
      h.name as hospital_name,
      h.province,
      h.city,
      h.latitude,
      h.longitude,
      m.value as wait_time_minutes,
      m.metric_family,
      m.start_event,
      m.end_event,
      m.statistic_type,
      m.patient_scope,
      s.id as source_id,
      s.name as source_name,
      s.methodology_url
    FROM measurements m
    JOIN hospitals h ON m.hospital_id = h.id
    JOIN sources s ON h.source_id = s.id
    WHERE h.is_verified = true
  `;

  // Apply filters (simplified - actual implementation would use parameterized queries)
  const filters: string[] = [];
  if (province) {
    filters.push(`h.province = '${province}'`);
  }
  if (startDate) {
    filters.push(`m.timestamp_utc >= '${startDate}'`);
  }
  if (endDate) {
    filters.push(`m.timestamp_utc <= '${endDate}'`);
  }

  // Execute query
  const results = await sql`
    SELECT
      m.timestamp_utc,
      m.hospital_id,
      h.name as hospital_name,
      h.province,
      h.city,
      h.latitude,
      h.longitude,
      m.value as wait_time_minutes,
      m.metric_family,
      m.start_event,
      m.end_event,
      m.statistic_type,
      m.patient_scope,
      s.id as source_id,
      s.name as source_name,
      s.methodology_url
    FROM measurements m
    JOIN hospitals h ON m.hospital_id = h.id
    JOIN sources s ON h.source_id = s.id
    WHERE h.is_verified = true
    ${province ? sql`AND h.province = ${province}` : sql``}
    ${startDate ? sql`AND m.timestamp_utc >= ${startDate}` : sql``}
    ${endDate ? sql`AND m.timestamp_utc <= ${endDate}` : sql``}
    ORDER BY m.timestamp_utc DESC
    LIMIT 10000
  `;

  // Format response
  if (format === 'json') {
    return NextResponse.json({
      data: results,
      metadata: {
        exported_at: new Date().toISOString(),
        record_count: results.length,
        filters: { province, startDate, endDate },
        license: 'CC-BY-4.0',
        citation: 'WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca',
      },
    });
  }

  // CSV format
  const headers = [
    'timestamp_utc', 'hospital_id', 'hospital_name', 'province', 'city',
    'latitude', 'longitude', 'wait_time_minutes',
    ...(includeMethodology ? ['metric_family', 'start_event', 'end_event', 'statistic_type', 'patient_scope'] : []),
    'source_id', 'source_name', 'methodology_url',
  ];

  const csvRows = [
    headers.join(','),
    ...results.map((row: any) =>
      headers.map(h => {
        const val = row[h];
        // Escape commas and quotes
        if (typeof val === 'string' && (val.includes(',') || val.includes('"'))) {
          return `"${val.replace(/"/g, '""')}"`;
        }
        return val ?? '';
      }).join(',')
    ),
  ];

  const csv = csvRows.join('\n');
  const filename = `waittime-canada-export-${new Date().toISOString().split('T')[0]}.csv`;

  return new NextResponse(csv, {
    headers: {
      'Content-Type': 'text/csv',
      'Content-Disposition': `attachment; filename="${filename}"`,
      'X-Data-License': 'CC-BY-4.0',
      'X-Citation': 'WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca',
    },
  });
}
```

### 1.4 Download UI Component

**File:** `frontend/components/DataExport.tsx`

```tsx
'use client';

import { useState } from 'react';
import { Download, FileSpreadsheet, Code, Info } from 'lucide-react';

export function DataExport() {
  const [province, setProvince] = useState<string>('');
  const [dateRange, setDateRange] = useState<'24h' | '7d' | '30d' | 'all'>('7d');
  const [format, setFormat] = useState<'csv' | 'json'>('csv');
  const [loading, setLoading] = useState(false);

  const handleExport = async () => {
    setLoading(true);

    const params = new URLSearchParams();
    if (province) params.set('province', province);
    params.set('format', format);

    // Calculate date range
    const now = new Date();
    if (dateRange !== 'all') {
      const days = { '24h': 1, '7d': 7, '30d': 30 }[dateRange];
      const start = new Date(now.getTime() - days * 24 * 60 * 60 * 1000);
      params.set('start_date', start.toISOString());
    }

    // Trigger download
    window.location.href = `/api/export?${params.toString()}`;
    setLoading(false);
  };

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileSpreadsheet className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">
          Download Data
        </h3>
      </div>

      <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
        Export wait time data with full methodology tags for research use.
        All exports include metric ontology columns for proper attribution.
      </p>

      {/* Filters */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Province
          </label>
          <select
            value={province}
            onChange={(e) => setProvince(e.target.value)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
          >
            <option value="">All Provinces</option>
            <option value="ON">Ontario</option>
            <option value="QC">Quebec</option>
            <option value="AB">Alberta</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
            Date Range
          </label>
          <select
            value={dateRange}
            onChange={(e) => setDateRange(e.target.value as any)}
            className="w-full px-3 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-900"
          >
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="all">All Data</option>
          </select>
        </div>
      </div>

      {/* Format Toggle */}
      <div className="flex items-center gap-4 mb-6">
        <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
          Format:
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setFormat('csv')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm ${
              format === 'csv'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" />
            CSV
          </button>
          <button
            onClick={() => setFormat('json')}
            className={`flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm ${
              format === 'json'
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-400'
            }`}
          >
            <Code className="w-4 h-4" />
            JSON
          </button>
        </div>
      </div>

      {/* Download Button */}
      <button
        onClick={handleExport}
        disabled={loading}
        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
      >
        <Download className="w-5 h-5" />
        {loading ? 'Preparing...' : 'Download Data'}
      </button>

      {/* Citation Info */}
      <div className="mt-4 p-3 bg-slate-50 dark:bg-slate-900 rounded-lg">
        <div className="flex items-start gap-2">
          <Info className="w-4 h-4 text-slate-400 mt-0.5" />
          <div className="text-xs text-slate-500 dark:text-slate-400">
            <p className="font-medium mb-1">Suggested Citation:</p>
            <p className="italic">
              WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set].
              https://waittimecanada.ca
            </p>
            <p className="mt-2">License: CC-BY-4.0 (Attribution Required)</p>
          </div>
        </div>
      </div>
    </div>
  );
}
```

### 1.5 Add to Methods Page

**Edit:** `frontend/app/methods/page.tsx`

Add DataExport component to the page:

```tsx
import { DataExport } from '@/components/DataExport';

// In the page component, add a new section:
<section>
  <div className="mb-8">
    <h2 className="text-3xl font-bold text-slate-900 mb-3">
      Data for Researchers
    </h2>
    <p className="text-slate-600 leading-relaxed max-w-3xl">
      Download wait time data with full methodology tags for research use.
      All exports include our metric ontology columns to ensure proper
      attribution and comparability analysis.
    </p>
  </div>
  <DataExport />
</section>
```

---

## Phase 2: Dead Man's Switch Alerts (Day 2-3)

### 2.1 Alert System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ GitHub Actions  │────▶│ check_heartbeat  │────▶│ Pushover API    │
│ (every 15 min)  │     │ CLI command      │     │ (notification)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │ scraper_status   │
                        │ table            │
                        └──────────────────┘
```

### 2.2 Pushover Integration

**Why Pushover:** Simple API, mobile app, free for personal use, no email deliverability issues.

**Setup:**
1. Create Pushover account at https://pushover.net
2. Get User Key and API Token
3. Add to GitHub Secrets: `PUSHOVER_USER_KEY`, `PUSHOVER_API_TOKEN`

**File:** `backend/src/waittime/services/alerts.py`

```python
"""Alert service for scraper health notifications."""
import os
import httpx
from dataclasses import dataclass
from typing import Optional


@dataclass
class AlertConfig:
    pushover_user_key: str
    pushover_api_token: str
    enabled: bool = True


class AlertService:
    """Service for sending operational alerts."""

    PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

    def __init__(self, config: Optional[AlertConfig] = None):
        self.config = config or AlertConfig(
            pushover_user_key=os.environ.get('PUSHOVER_USER_KEY', ''),
            pushover_api_token=os.environ.get('PUSHOVER_API_TOKEN', ''),
            enabled=bool(os.environ.get('ALERTS_ENABLED', 'true').lower() == 'true'),
        )

    def send_alert(
        self,
        title: str,
        message: str,
        priority: int = 0,  # -2 to 2 (2 = emergency)
        url: Optional[str] = None,
    ) -> bool:
        """
        Send an alert via Pushover.

        Args:
            title: Alert title
            message: Alert body
            priority: -2 (lowest) to 2 (emergency, requires acknowledgment)
            url: Optional URL to include

        Returns:
            True if sent successfully
        """
        if not self.config.enabled:
            print(f"[ALERT DISABLED] {title}: {message}")
            return True

        if not self.config.pushover_user_key or not self.config.pushover_api_token:
            print(f"[ALERT NO CONFIG] {title}: {message}")
            return False

        payload = {
            'token': self.config.pushover_api_token,
            'user': self.config.pushover_user_key,
            'title': title,
            'message': message,
            'priority': priority,
        }
        if url:
            payload['url'] = url
            payload['url_title'] = 'View Details'

        try:
            response = httpx.post(self.PUSHOVER_API_URL, data=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"[ALERT FAILED] {e}")
            return False

    def alert_scraper_stale(self, source_id: str, age_minutes: int):
        """Alert that a scraper hasn't run recently."""
        self.send_alert(
            title=f"⚠️ Scraper Stale: {source_id}",
            message=f"No heartbeat for {age_minutes} minutes. Check GitHub Actions.",
            priority=1,  # High priority
            url="https://github.com/YOUR_REPO/actions",
        )

    def alert_scraper_error(self, source_id: str, error: str):
        """Alert that a scraper encountered an error."""
        self.send_alert(
            title=f"🚨 Scraper Error: {source_id}",
            message=f"Error: {error[:200]}",
            priority=1,
            url="https://github.com/YOUR_REPO/actions",
        )
```

### 2.3 Enhanced Heartbeat Check CLI

**File:** `backend/src/waittime/cli/check_heartbeat.py`

```python
"""Check scraper heartbeat and alert if stale."""
import argparse
import sys
from datetime import datetime, timedelta, timezone

from waittime.services.database import DatabaseService
from waittime.services.alerts import AlertService


def main():
    parser = argparse.ArgumentParser(description='Check scraper heartbeat')
    parser.add_argument('--max-age', type=int, default=60,
                        help='Max heartbeat age in minutes before alerting')
    parser.add_argument('--source', type=str, default=None,
                        help='Check specific source (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print status without sending alerts')
    args = parser.parse_args()

    db = DatabaseService()
    alerts = AlertService()

    # Get latest heartbeats
    if args.source:
        sources = [args.source]
    else:
        sources = ['ontario-health', 'quebec-msss', 'alberta-ahs']

    all_healthy = True
    for source_id in sources:
        heartbeat = db.get_latest_heartbeat(source_id)

        if not heartbeat:
            print(f"❌ {source_id}: No heartbeat found")
            if not args.dry_run:
                alerts.alert_scraper_stale(source_id, age_minutes=9999)
            all_healthy = False
            continue

        age = datetime.now(timezone.utc) - heartbeat.timestamp
        age_minutes = int(age.total_seconds() / 60)

        if age_minutes > args.max_age:
            print(f"⚠️ {source_id}: Heartbeat is {age_minutes} minutes old (max: {args.max_age})")
            if not args.dry_run:
                alerts.alert_scraper_stale(source_id, age_minutes)
            all_healthy = False
        else:
            print(f"✅ {source_id}: Heartbeat is {age_minutes} minutes old")

    sys.exit(0 if all_healthy else 1)


if __name__ == '__main__':
    main()
```

### 2.4 GitHub Action for Monitoring

**File:** `.github/workflows/heartbeat-monitor.yml`

```yaml
name: Heartbeat Monitor

on:
  schedule:
    - cron: '*/30 * * * *'  # Every 30 minutes
  workflow_dispatch:

jobs:
  check-heartbeat:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          cd backend
          pip install -e .

      - name: Check heartbeats
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          PUSHOVER_USER_KEY: ${{ secrets.PUSHOVER_USER_KEY }}
          PUSHOVER_API_TOKEN: ${{ secrets.PUSHOVER_API_TOKEN }}
        run: |
          cd backend
          python -m waittime.cli.check_heartbeat --max-age 60
```

### 2.5 System Status Indicator

**File:** `frontend/components/SystemStatus.tsx`

```tsx
'use client';

import { useState, useEffect } from 'react';
import { Activity, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';

type Status = 'healthy' | 'degraded' | 'down' | 'loading';

interface HealthData {
  status: Status;
  lastHeartbeat: string | null;
  ageMinutes: number;
}

export function SystemStatus() {
  const [health, setHealth] = useState<HealthData>({
    status: 'loading',
    lastHeartbeat: null,
    ageMinutes: 0,
  });

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetch('/api/health');
        const data = await res.json();

        const ageMinutes = data.heartbeat_age_minutes || 999;
        let status: Status = 'healthy';
        if (ageMinutes > 120) status = 'down';
        else if (ageMinutes > 60) status = 'degraded';

        setHealth({
          status,
          lastHeartbeat: data.last_heartbeat,
          ageMinutes,
        });
      } catch {
        setHealth({ status: 'down', lastHeartbeat: null, ageMinutes: 999 });
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 60000); // Check every minute
    return () => clearInterval(interval);
  }, []);

  const statusConfig = {
    loading: { icon: Activity, color: 'text-slate-400', label: 'Checking...' },
    healthy: { icon: CheckCircle, color: 'text-green-500', label: 'All Systems Operational' },
    degraded: { icon: AlertTriangle, color: 'text-amber-500', label: 'Data May Be Stale' },
    down: { icon: XCircle, color: 'text-red-500', label: 'Data Unavailable' },
  };

  const { icon: Icon, color, label } = statusConfig[health.status];

  return (
    <div className="flex items-center gap-2 text-sm">
      <Icon className={`w-4 h-4 ${color}`} />
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      {health.ageMinutes < 999 && (
        <span className="text-slate-400 text-xs">
          (updated {health.ageMinutes}m ago)
        </span>
      )}
    </div>
  );
}
```

**File:** `frontend/app/api/health/route.ts`

```typescript
import { NextResponse } from 'next/server';
import { getDb } from '@/utils/db';

export async function GET() {
  try {
    const sql = getDb();

    const result = await sql`
      SELECT
        source_id,
        last_run,
        status,
        EXTRACT(EPOCH FROM (NOW() - last_run)) / 60 as age_minutes
      FROM scraper_status
      ORDER BY last_run DESC
      LIMIT 1
    `;

    if (result.length === 0) {
      return NextResponse.json({
        status: 'unknown',
        last_heartbeat: null,
        heartbeat_age_minutes: null,
      });
    }

    return NextResponse.json({
      status: result[0].status,
      last_heartbeat: result[0].last_run,
      heartbeat_age_minutes: Math.round(result[0].age_minutes),
      source_id: result[0].source_id,
    });
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      error: 'Failed to check health',
    }, { status: 500 });
  }
}
```

---

## Phase 3: Occupancy Statistics (Day 3-4, If Data Available)

### 3.1 Research Required

Before implementing, verify:
1. Does Ontario Health provide "patients waiting" count?
2. Does Ontario Health provide "patients in treatment" count?
3. Are these values in the same scrape or a different endpoint?

**Current implementation:** Deliver explicit availability contract now; defer ingestion until source
fields exist.

### 3.2 Schema Extension (If Available)

```sql
ALTER TABLE measurements
ADD COLUMN patients_waiting INTEGER,
ADD COLUMN patients_in_treatment INTEGER;
```

### 3.3 Scraper Update (If Available)

```python
# In ontario.py, update parse method:
measurement = Measurement(
    # ... existing fields ...
    patients_waiting=int(row.select_one('.patients-waiting').text) if row.select_one('.patients-waiting') else None,
    patients_in_treatment=int(row.select_one('.patients-treatment').text) if row.select_one('.patients-treatment') else None,
)
```

### 3.4 UI Display (If Available)

```tsx
// In HospitalCard expanded view:
{hospital.patients_waiting !== null && (
  <div className="flex items-center gap-4">
    <div className="flex items-center gap-1.5">
      <Users className="w-4 h-4 text-amber-500" />
      <span className="text-sm">
        <strong>{hospital.patients_waiting}</strong> waiting
      </span>
    </div>
    <div className="flex items-center gap-1.5">
      <Stethoscope className="w-4 h-4 text-green-500" />
      <span className="text-sm">
        <strong>{hospital.patients_in_treatment}</strong> in treatment
      </span>
    </div>
  </div>
)}
```

---

## Documentation

### API Documentation

**File:** `docs/API.md`

```markdown
# WaitTime Canada API Documentation

## Endpoints

### GET /api/hospitals
Returns list of hospitals with current wait times.

**Query Parameters:**
- `province` (optional): Filter by province code (ON, QC, AB)

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "ca-on-toronto-general",
      "name": "Toronto General Hospital",
      "province": "ON",
      "city": "Toronto",
      "latitude": 43.6591,
      "longitude": -79.3878,
      "wait_time": 145,
      "metric_family": "TIME_TO_PROVIDER",
      "start_event": "TRIAGE",
      "end_event": "PHYSICIAN",
      "statistic_type": "P90",
      "last_updated": "2026-02-04T15:30:00Z"
    }
  ]
}
```

### GET /api/export
Download wait time data in CSV or JSON format.

**Query Parameters:**
- `province` (optional): Filter by province code
- `start_date` (optional): ISO date for range start
- `end_date` (optional): ISO date for range end
- `format` (optional): `csv` (default) or `json`

**Response:** CSV file download or JSON object

### GET /api/health
System health status.

**Response:**
```json
{
  "status": "healthy",
  "last_heartbeat": "2026-02-04T15:30:00Z",
  "heartbeat_age_minutes": 5
}
```

## Data License

All data is provided under CC-BY-4.0 (Creative Commons Attribution 4.0).

**Required Attribution:**
> WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca

## Methodology

See `/methods` page for detailed explanation of the metric ontology.
```

---

## Verification Checklist

### Data Export
- [ ] `/api/export` endpoint returns CSV
- [ ] CSV includes all methodology columns
- [ ] JSON format option works
- [ ] Province and date filters work
- [ ] Citation header included in response
- [ ] Download button on /methods page

### Alerts
- [ ] `check_heartbeat` CLI works
- [ ] Pushover integration tested
- [ ] GitHub Action configured
- [ ] System status component displays correctly
- [ ] `/api/health` endpoint returns status

### Occupancy (If Implemented)
- [x] Occupancy endpoint returns explicit availability status
- [x] Analytics UI shows explicit "not available yet" state
- [ ] Schema extended for production occupancy ingestion
- [ ] Scraper collects occupancy fields when source supports them

---

## Success Criteria

1. **CSV export** with methodology tags downloadable from /methods
2. **JSON API** documented for programmatic access
3. **Heartbeat alerts** sent to Pushover when scraper stale
4. **System status** visible in footer
5. **API docs** in `docs/API.md`

---

## Time Estimate

| Task | Hours |
|------|-------|
| Export API endpoint | 2-3 |
| Export UI component | 1-2 |
| Pushover integration | 1-2 |
| Heartbeat check CLI | 1 |
| GitHub Action | 0.5 |
| System status component | 1-2 |
| Health API endpoint | 0.5 |
| API documentation | 1-2 |
| Occupancy (if available) | 2-3 |
| **Total** | **10-16 hours** |
