# WaitTime Canada API Documentation

## Overview

The WaitTime Canada API provides programmatic access to Canadian emergency department wait time data with full methodology attribution. All endpoints are read-only and return data under the CC-BY-4.0 license.

**Base URL:** `https://waittimecanada.ca/api`

**Data License:** CC-BY-4.0 (Creative Commons Attribution 4.0 International)

**Required Attribution:**
> WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca

---

## Endpoints

### GET /api/hospitals

Returns a list of hospitals with current wait times and full methodology metadata.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `province` | string | No | Filter by province code (ON, QC, AB) |

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
      "current_wait_time": 145,
      "metric_family": "TIME_TO_PROVIDER",
      "start_event": "TRIAGE",
      "end_event": "PHYSICIAN",
      "statistic_type": "P90",
      "patient_scope": "ALL",
      "last_updated": "2026-02-04T15:30:00Z",
      "source_id": "ontario-health",
      "methodology_url": "https://www.hqontario.ca/..."
    }
  ]
}
```

**Example:**
```bash
curl "https://waittimecanada.ca/api/hospitals?province=ON"
```

---

### GET /api/export

Download historical wait time data in CSV or JSON format with full methodology tags.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `province` | string | No | Filter by province code (ON, QC, AB) |
| `start_date` | ISO 8601 | No | Start of date range (e.g., `2026-01-01T00:00:00Z`) |
| `end_date` | ISO 8601 | No | End of date range (e.g., `2026-02-04T23:59:59Z`) |
| `format` | string | No | Response format: `csv` (default) or `json` |
| `include_methodology` | boolean | No | Include ontology columns in CSV (default: `true`) |

**CSV Response:**

```csv
timestamp_utc,hospital_id,hospital_name,province,city,latitude,longitude,wait_time_minutes,metric_family,start_event,end_event,statistic_type,patient_scope,source_id,source_name,methodology_url
2026-02-04T15:30:00Z,ca-on-toronto-general,Toronto General Hospital,ON,Toronto,43.6591,-79.3878,145,TIME_TO_PROVIDER,TRIAGE,PHYSICIAN,P90,ALL,ontario-health,Ontario Health,https://www.hqontario.ca/...
```

**Response Headers:**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="waittime-canada-export-2026-02-04.csv"
X-Data-License: CC-BY-4.0
X-Citation: WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca
```

**JSON Response:**

```json
{
  "data": [
    {
      "timestamp_utc": "2026-02-04T15:30:00Z",
      "hospital_id": "ca-on-toronto-general",
      "hospital_name": "Toronto General Hospital",
      "province": "ON",
      "city": "Toronto",
      "latitude": 43.6591,
      "longitude": -79.3878,
      "wait_time_minutes": 145,
      "metric_family": "TIME_TO_PROVIDER",
      "start_event": "TRIAGE",
      "end_event": "PHYSICIAN",
      "statistic_type": "P90",
      "patient_scope": "ALL",
      "source_id": "ontario-health",
      "source_name": "Ontario Health",
      "methodology_url": "https://www.hqontario.ca/..."
    }
  ],
  "metadata": {
    "exported_at": "2026-02-04T16:00:00Z",
    "record_count": 1,
    "filters": {
      "province": "ON",
      "startDate": "2026-02-01T00:00:00Z",
      "endDate": null
    },
    "license": "CC-BY-4.0",
    "citation": "WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca"
  }
}
```

**Examples:**

```bash
# Download last 7 days as CSV
curl "https://waittimecanada.ca/api/export?format=csv&start_date=2026-01-28T00:00:00Z"

# Get Ontario data as JSON
curl "https://waittimecanada.ca/api/export?format=json&province=ON"

# Download all data without methodology columns
curl "https://waittimecanada.ca/api/export?format=csv&include_methodology=false"
```

**Rate Limits:**
- 10,000 records per request
- No authentication required
- No rate limiting (please be respectful)

---

### GET /api/health

Returns system health status and scraper heartbeat information.

**Response:**

```json
{
  "status": "healthy",
  "last_heartbeat": "2026-02-04T15:30:00Z",
  "heartbeat_age_minutes": 5,
  "source_id": "ontario-health"
}
```

**Status Values:**
- `healthy`: Scraper ran recently (< 60 minutes ago)
- `degraded`: Scraper data is stale (60-120 minutes ago)
- `down`: No recent scraper activity (> 120 minutes ago)
- `unknown`: No heartbeat data available

**Example:**
```bash
curl "https://waittimecanada.ca/api/health"
```

---

## Methodology Ontology

All data exports include these methodology tags for proper attribution:

| Field | Values | Description |
|-------|--------|-------------|
| `metric_family` | `TIME_TO_PROVIDER`, `TOTAL_LOS`, `STRETCHER_OCCUPANCY` | What is being measured |
| `start_event` | `TRIAGE`, `REGISTRATION`, `DOOR`, `UNKNOWN` | When measurement starts |
| `end_event` | `PHYSICIAN`, `PROVIDER`, `DISCHARGE`, `FIRST_ASSESSMENT` | When measurement ends |
| `statistic_type` | `POINT_ESTIMATE`, `P90`, `ALGORITHMIC`, `ROLLING_AVG` | How the value was calculated |
| `patient_scope` | `ALL`, `MID_ACUITY`, `NON_PRIORITY` | Which patients are included |

**Comparability Rule:**
Two measurements are directly comparable if and only if:
```
A.metric_family == B.metric_family AND
A.start_event == B.start_event AND
A.end_event == B.end_event AND
A.statistic_type == B.statistic_type
```

See [/methods](https://waittimecanada.ca/methods) for detailed explanations.

---

## Usage Examples

### Python

```python
import requests
import pandas as pd
from io import StringIO

# Download CSV data
response = requests.get(
    'https://waittimecanada.ca/api/export',
    params={
        'format': 'csv',
        'province': 'ON',
        'start_date': '2026-01-01T00:00:00Z'
    }
)

# Load into pandas
df = pd.read_csv(StringIO(response.text))

# Filter for comparable measurements
comparable = df[
    (df['metric_family'] == 'TIME_TO_PROVIDER') &
    (df['start_event'] == 'TRIAGE') &
    (df['end_event'] == 'PHYSICIAN') &
    (df['statistic_type'] == 'P90')
]

print(comparable.groupby('hospital_name')['wait_time_minutes'].mean())
```

### R

```r
library(httr)
library(readr)

# Download data
response <- GET(
  'https://waittimecanada.ca/api/export',
  query = list(
    format = 'csv',
    province = 'QC'
  )
)

# Parse CSV
data <- read_csv(content(response, 'text'))

# Analyze by city
library(dplyr)
data %>%
  group_by(city) %>%
  summarize(
    avg_wait = mean(wait_time_minutes, na.rm = TRUE),
    n = n()
  )
```

### JavaScript

```javascript
// Fetch JSON data
const response = await fetch(
  'https://waittimecanada.ca/api/export?format=json&province=AB'
);
const { data, metadata } = await response.json();

// Filter for recent data
const recent = data.filter(row => {
  const age = Date.now() - new Date(row.timestamp_utc);
  return age < 24 * 60 * 60 * 1000; // Last 24 hours
});

console.log(`Found ${recent.length} recent measurements`);
console.log(`Citation: ${metadata.citation}`);
```

---

## Data License & Attribution

All data is provided under **CC-BY-4.0** (Creative Commons Attribution 4.0 International).

**You are free to:**
- Share: Copy and redistribute the material
- Adapt: Remix, transform, and build upon the material

**Under the following terms:**
- **Attribution:** You must give appropriate credit, provide a link to the license, and indicate if changes were made

**Suggested Citation:**
> WaitTime Canada. (2026). Canadian ER Wait Time Data [Data set]. https://waittimecanada.ca

**BibTeX:**
```bibtex
@misc{waittimecanada2026,
  title = {Canadian ER Wait Time Data},
  author = {{WaitTime Canada}},
  year = {2026},
  howpublished = {\url{https://waittimecanada.ca}},
  note = {Data set}
}
```

---

## Support

**Documentation:** https://waittimecanada.ca/methods
**Issues:** https://github.com/jerdaw/waittimecanada/issues
**Email:** [Contact via GitHub]

---

*Last Updated: February 4, 2026*
