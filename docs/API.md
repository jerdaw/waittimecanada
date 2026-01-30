# API Specification

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST Endpoints](#rest-endpoints)
4. [Data Models](#data-models)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [OpenAPI Specification](#openapi-specification)

---

## Overview

**Base URL:** `https://xxxxx.supabase.co/rest/v1`
**Client:** Supabase JavaScript Client (auto-generates REST calls)
**Protocol:** REST over HTTPS
**Format:** JSON

**Design Philosophy:**
- Read-heavy API (99% reads, 1% writes)
- Public read-only access (no auth required for GET)
- Writes restricted to service role (scrapers only)
- Optimistic caching (5-minute stale time)

---

## Authentication

### Public Access (Frontend)

**Anon Key:** Read-only access via Supabase anon key
- Automatically filtered by RLS policies
- No rate limiting on free tier (500 req/sec)

```typescript
// Frontend initialization
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
```

### Service Role (Scrapers)

**Service Key:** Full read/write access
- Bypasses RLS policies
- Used only in server-side scrapers
- Never exposed to frontend

```python
# Scraper initialization
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)
```

---

## REST Endpoints

### 1. GET `/hospitals`

Get list of verified hospitals with latest wait times.

**Query Parameters:**
- `province` (optional): Filter by province code (e.g., `QC`, `AB`)
- `select` (optional): Specify fields to return
- `order` (optional): Sort order

**Example Request:**
```typescript
const { data, error } = await supabase
  .from('hospitals')
  .select(`
    id,
    name,
    province,
    city,
    latitude,
    longitude,
    facility_type,
    phone,
    website,
    source:sources (
      telehealth_name,
      telehealth_phone
    ),
    measurements (
      value,
      timestamp_utc,
      metric_family,
      start_event,
      end_event,
      statistic_type
    )
  `)
  .eq('is_visible', true)
  .eq('is_verified', true)
  .eq('province', 'QC')  // Optional filter
  .order('timestamp_utc', { foreignTable: 'measurements', ascending: false })
  .limit(1, { foreignTable: 'measurements' });
```

**Response:**
```json
{
  "data": [
    {
      "id": "ca-qc-chum",
      "name": "CHUM - Hôtel-Dieu",
      "province": "QC",
      "city": "Montreal",
      "latitude": 45.5122,
      "longitude": -73.5706,
      "facility_type": "ER",
      "phone": "514-890-8000",
      "website": "https://www.chumontreal.qc.ca/",
      "source": {
        "telehealth_name": "Info-Santé 811",
        "telehealth_phone": "811"
      },
      "measurements": [
        {
          "value": 180,
          "timestamp_utc": "2024-01-15T14:30:00Z",
          "metric_family": "TIME_TO_PROVIDER",
          "start_event": "REGISTRATION",
          "end_event": "PHYSICIAN",
          "statistic_type": "ROLLING_AVG"
        }
      ]
    }
  ],
  "error": null
}
```

---

### 2. GET `/hospitals/:id`

Get detailed information for a single hospital.

**Path Parameters:**
- `id` (required): Hospital ID (e.g., `ca-qc-chum`)

**Example Request:**
```typescript
const { data, error } = await supabase
  .from('hospitals')
  .select(`
    *,
    source:sources (*),
    measurements (*)
  `)
  .eq('id', 'ca-qc-chum')
  .order('timestamp_utc', { foreignTable: 'measurements', ascending: false })
  .limit(20, { foreignTable: 'measurements' })
  .single();
```

**Response:**
```json
{
  "data": {
    "id": "ca-qc-chum",
    "name": "CHUM - Hôtel-Dieu",
    "province": "QC",
    "city": "Montreal",
    "address": "3840 Rue Saint-Urbain",
    "postal_code": "H2W 1T8",
    "latitude": 45.5122,
    "longitude": -73.5706,
    "facility_type": "ER",
    "is_verified": true,
    "is_visible": true,
    "phone": "514-890-8000",
    "website": "https://www.chumontreal.qc.ca/",
    "source": {
      "id": "ca-qc-msss",
      "name": "Ministère de la Santé et des Services sociaux",
      "province": "QC",
      "telehealth_name": "Info-Santé 811",
      "telehealth_phone": "811",
      "definition_url": "https://..."
    },
    "measurements": [
      { /* latest measurement */ },
      { /* previous measurements */ }
    ]
  },
  "error": null
}
```

---

### 3. GET `/measurements`

Get raw measurements (for time-series charts).

**Query Parameters:**
- `hospital_id` (required): Filter by hospital
- `gte.timestamp_utc` (optional): Start time (ISO 8601)
- `lte.timestamp_utc` (optional): End time (ISO 8601)
- `order` (optional): Sort order

**Example Request:**
```typescript
const { data, error } = await supabase
  .from('measurements')
  .select('timestamp_utc, value, metric_family, start_event, end_event, statistic_type')
  .eq('hospital_id', 'ca-qc-chum')
  .gte('timestamp_utc', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
  .order('timestamp_utc', { ascending: true });
```

**Response:**
```json
{
  "data": [
    {
      "timestamp_utc": "2024-01-15T00:00:00Z",
      "value": 165,
      "metric_family": "TIME_TO_PROVIDER",
      "start_event": "REGISTRATION",
      "end_event": "PHYSICIAN",
      "statistic_type": "ROLLING_AVG"
    },
    {
      "timestamp_utc": "2024-01-15T00:15:00Z",
      "value": 172,
      "metric_family": "TIME_TO_PROVIDER",
      "start_event": "REGISTRATION",
      "end_event": "PHYSICIAN",
      "statistic_type": "ROLLING_AVG"
    }
  ],
  "error": null
}
```

---

### 4. GET `/sources`

Get list of provincial data sources.

**Query Parameters:**
- `is_active` (optional): Filter by active status

**Example Request:**
```typescript
const { data, error } = await supabase
  .from('sources')
  .select('*')
  .eq('is_active', true)
  .order('province');
```

**Response:**
```json
{
  "data": [
    {
      "id": "ca-ab-ahs",
      "name": "Alberta Health Services",
      "province": "AB",
      "definition_url": "https://...",
      "data_url": "https://...",
      "telehealth_name": "Health Link 811",
      "telehealth_phone": "811",
      "is_active": true
    }
  ],
  "error": null
}
```

---

### 5. GET `/scraper_status`

Get scraper health status (for Heartbeat Monitor).

**Example Request:**
```typescript
const { data, error } = await supabase
  .from('scraper_status')
  .select('*')
  .order('last_run', { ascending: false });
```

**Response:**
```json
{
  "data": [
    {
      "scraper_id": "quebec-scraper",
      "last_run": "2024-01-15T14:30:00Z",
      "status": "healthy",
      "hospitals_scraped": 25,
      "measurements_created": 150,
      "duration_seconds": 12.4,
      "error_message": null,
      "error_count": 0
    }
  ],
  "error": null
}
```

---

### 6. POST `/measurements` (Service Role Only)

Insert new measurements from scrapers.

**Request Body:**
```json
{
  "hospital_id": "ca-qc-chum",
  "timestamp_utc": "2024-01-15T14:30:00Z",
  "value": 180,
  "metric_family": "TIME_TO_PROVIDER",
  "start_event": "REGISTRATION",
  "end_event": "PHYSICIAN",
  "statistic_type": "ROLLING_AVG",
  "patient_scope": "ALL",
  "raw_payload_hash": "a3f5e1b2c4d6e8f9a1b2c3d4e5f6a7b8",
  "raw_payload_snippet": "<html><body>CHUM wait time: 3h00...",
  "parser_version": "v1.0.0",
  "scraper_id": "quebec-scraper"
}
```

**Python Example:**
```python
from src.core.models import Measurement

measurement = Measurement(
    hospital_id="ca-qc-chum",
    value=180,
    metric_family="TIME_TO_PROVIDER",
    start_event="REGISTRATION",
    end_event="PHYSICIAN",
    statistic_type="ROLLING_AVG",
    raw_payload_hash=payload_hash,
    raw_payload_snippet=html[:200],
    parser_version="v1.0.0",
    scraper_id="quebec-scraper"
)

result = supabase.table("measurements").insert(measurement.dict()).execute()
```

**Response:**
```json
{
  "data": [
    {
      "id": 12345,
      "hospital_id": "ca-qc-chum",
      "timestamp_utc": "2024-01-15T14:30:00Z",
      "value": 180,
      "metric_family": "TIME_TO_PROVIDER",
      "start_event": "REGISTRATION",
      "end_event": "PHYSICIAN",
      "statistic_type": "ROLLING_AVG"
    }
  ],
  "error": null
}
```

---

### 7. POST `/scraper_status` (Service Role Only)

Upsert scraper heartbeat.

**Request Body:**
```json
{
  "scraper_id": "quebec-scraper",
  "last_run": "2024-01-15T14:30:00Z",
  "status": "healthy",
  "hospitals_scraped": 25,
  "measurements_created": 150,
  "duration_seconds": 12.4,
  "error_message": null,
  "error_count": 0
}
```

**Python Example:**
```python
from src.core.heartbeat import write_heartbeat

write_heartbeat(
    supabase,
    scraper_id="quebec-scraper",
    status="healthy",
    hospitals_scraped=25,
    measurements_created=150,
    duration_seconds=12.4
)
```

---

## Data Models

### TypeScript Types

```typescript
// src/types/index.ts

export type MetricFamily = 'TIME_TO_PROVIDER' | 'TOTAL_LOS' | 'STRETCHER_OCCUPANCY';
export type StartEvent = 'TRIAGE' | 'REGISTRATION' | 'DOOR' | 'UNKNOWN';
export type EndEvent = 'PHYSICIAN' | 'PROVIDER' | 'DISCHARGE' | 'FIRST_ASSESSMENT' | 'TREATMENT_START';
export type StatisticType = 'POINT_ESTIMATE' | 'P90' | 'MEDIAN' | 'MEAN' | 'ROLLING_AVG' | 'ALGORITHMIC';
export type PatientScope = 'ALL' | 'MID_ACUITY' | 'NON_PRIORITY' | 'ADMITTED' | 'DISCHARGED';
export type FacilityType = 'ER' | 'URGENT_CARE' | 'TRAUMA_CENTER';
export type ScraperStatus = 'healthy' | 'degraded' | 'failed';

export interface Source {
  id: string;
  name: string;
  province: string;
  definition_url: string | null;
  data_url: string;
  telehealth_name: string | null;
  telehealth_phone: string | null;
  telehealth_url: string | null;
  is_active: boolean;
}

export interface Hospital {
  id: string;
  source_id: string;
  name: string;
  province: string;
  city: string | null;
  address: string | null;
  postal_code: string | null;
  latitude: number | null;
  longitude: number | null;
  facility_type: FacilityType;
  is_verified: boolean;
  is_visible: boolean;
  phone: string | null;
  website: string | null;
  source?: Source;
  measurements?: Measurement[];
}

export interface Measurement {
  id: number;
  hospital_id: string;
  timestamp_utc: string;
  value: number;
  metric_family: MetricFamily;
  start_event: StartEvent;
  end_event: EndEvent;
  statistic_type: StatisticType;
  patient_scope: PatientScope;
}

export interface ScraperStatus {
  scraper_id: string;
  last_run: string;
  status: ScraperStatus;
  hospitals_scraped: number | null;
  measurements_created: number | null;
  duration_seconds: number | null;
  error_message: string | null;
  error_count: number;
}
```

### Python Models (Pydantic)

```python
# scrapers/src/core/models.py
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field

class MetricFamily(str, Enum):
    TIME_TO_PROVIDER = "TIME_TO_PROVIDER"
    TOTAL_LOS = "TOTAL_LOS"
    STRETCHER_OCCUPANCY = "STRETCHER_OCCUPANCY"

class StartEvent(str, Enum):
    TRIAGE = "TRIAGE"
    REGISTRATION = "REGISTRATION"
    DOOR = "DOOR"
    UNKNOWN = "UNKNOWN"

class EndEvent(str, Enum):
    PHYSICIAN = "PHYSICIAN"
    PROVIDER = "PROVIDER"
    DISCHARGE = "DISCHARGE"
    FIRST_ASSESSMENT = "FIRST_ASSESSMENT"
    TREATMENT_START = "TREATMENT_START"

class StatisticType(str, Enum):
    POINT_ESTIMATE = "POINT_ESTIMATE"
    P90 = "P90"
    MEDIAN = "MEDIAN"
    MEAN = "MEAN"
    ROLLING_AVG = "ROLLING_AVG"
    ALGORITHMIC = "ALGORITHMIC"

class PatientScope(str, Enum):
    ALL = "ALL"
    MID_ACUITY = "MID_ACUITY"
    NON_PRIORITY = "NON_PRIORITY"
    ADMITTED = "ADMITTED"
    DISCHARGED = "DISCHARGED"

class Measurement(BaseModel):
    hospital_id: str
    timestamp_utc: datetime = Field(default_factory=datetime.utcnow)
    value: float = Field(gt=0)
    metric_family: MetricFamily
    start_event: StartEvent
    end_event: EndEvent
    statistic_type: StatisticType
    patient_scope: PatientScope = PatientScope.ALL
    raw_payload_hash: str
    raw_payload_snippet: str = Field(max_length=200)
    parser_version: str
    scraper_id: str

    class Config:
        use_enum_values = True
```

---

## Error Handling

### Error Response Format

```json
{
  "data": null,
  "error": {
    "message": "Invalid query parameter: province must be two-letter code",
    "code": "PGRST203",
    "details": "...",
    "hint": "..."
  }
}
```

### Common Error Codes

| Code | Meaning | Example |
|------|---------|---------|
| `PGRST116` | Not found | Hospital ID doesn't exist |
| `PGRST203` | Invalid query | Invalid filter parameter |
| `42501` | Insufficient privilege | Trying to write with anon key |
| `23503` | Foreign key violation | Hospital doesn't exist |
| `23505` | Unique constraint violation | Duplicate measurement |

### Frontend Error Handling

```typescript
// src/lib/api.ts
import { PostgrestError } from '@supabase/supabase-js';

export async function fetchHospitals(province?: string) {
  const query = supabase
    .from('hospitals')
    .select('*')
    .eq('is_visible', true);

  if (province) {
    query.eq('province', province);
  }

  const { data, error } = await query;

  if (error) {
    console.error('Error fetching hospitals:', error);
    throw new Error(`Failed to fetch hospitals: ${error.message}`);
  }

  return data;
}
```

### Scraper Error Handling

```python
# scrapers/src/scrapers/base.py
from tenacity import retry, stop_after_attempt, wait_exponential
import structlog

logger = structlog.get_logger()

class BaseScraper:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60)
    )
    def insert_measurement(self, measurement: Measurement):
        try:
            result = self.supabase.table("measurements").insert(
                measurement.dict()
            ).execute()
            logger.info("measurement_inserted", hospital_id=measurement.hospital_id)
            return result
        except Exception as e:
            logger.error(
                "measurement_insert_failed",
                error=str(e),
                hospital_id=measurement.hospital_id
            )
            raise
```

---

## Rate Limiting

### Supabase Free Tier

- **Requests per second:** 500
- **Database connections:** 60 simultaneous
- **Egress:** 2GB/month

**Expected Usage (MVP):**
- Scraper writes: ~100 measurements / 15 min = 7/min (well below limit)
- Frontend reads: ~1000 page loads/day × 3 API calls = 0.03/sec (well below limit)

### Rate Limiting Strategy (Future)

If scaling beyond free tier:

```typescript
// middleware.ts (Vercel Edge)
import { Ratelimit } from "@upstash/ratelimit";
import { Redis } from "@upstash/redis";

const ratelimit = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(10, "10 s"),
  analytics: true,
});

export async function middleware(request: Request) {
  const ip = request.headers.get('x-forwarded-for') ?? 'anonymous';
  const { success, limit, reset, remaining } = await ratelimit.limit(ip);

  if (!success) {
    return new Response('Too Many Requests', {
      status: 429,
      headers: {
        'X-RateLimit-Limit': limit.toString(),
        'X-RateLimit-Remaining': remaining.toString(),
        'X-RateLimit-Reset': reset.toString(),
      },
    });
  }

  return NextResponse.next();
}
```

---

## OpenAPI Specification

### Minimal OpenAPI 3.0 Spec

```yaml
# docs/openapi.yaml
openapi: 3.0.0
info:
  title: WaitTime Canada API
  version: 1.0.0
  description: Public API for Canadian emergency room wait times

servers:
  - url: https://xxxxx.supabase.co/rest/v1
    description: Production (Supabase)

paths:
  /hospitals:
    get:
      summary: List hospitals
      parameters:
        - name: province
          in: query
          schema:
            type: string
            enum: [AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, QC, SK, YT]
        - name: select
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Hospital'

  /measurements:
    get:
      summary: Get measurements
      parameters:
        - name: hospital_id
          in: query
          required: true
          schema:
            type: string
        - name: gte.timestamp_utc
          in: query
          schema:
            type: string
            format: date-time
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Measurement'

components:
  schemas:
    Hospital:
      type: object
      properties:
        id:
          type: string
        name:
          type: string
        province:
          type: string
        latitude:
          type: number
        longitude:
          type: number

    Measurement:
      type: object
      properties:
        id:
          type: integer
        hospital_id:
          type: string
        timestamp_utc:
          type: string
          format: date-time
        value:
          type: number
        metric_family:
          type: string
          enum: [TIME_TO_PROVIDER, TOTAL_LOS, STRETCHER_OCCUPANCY]
        start_event:
          type: string
          enum: [TRIAGE, REGISTRATION, DOOR, UNKNOWN]
        end_event:
          type: string
          enum: [PHYSICIAN, PROVIDER, DISCHARGE, FIRST_ASSESSMENT, TREATMENT_START]
        statistic_type:
          type: string
          enum: [POINT_ESTIMATE, P90, MEDIAN, MEAN, ROLLING_AVG, ALGORITHMIC]
```

---

## Testing API Endpoints

### Using cURL

```bash
# Get hospitals
curl "https://xxxxx.supabase.co/rest/v1/hospitals?is_visible=eq.true&select=*" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"

# Get measurements for hospital
curl "https://xxxxx.supabase.co/rest/v1/measurements?hospital_id=eq.ca-qc-chum&select=*" \
  -H "apikey: YOUR_ANON_KEY" \
  -H "Authorization: Bearer YOUR_ANON_KEY"
```

### Using Postman/Insomnia

Import the OpenAPI spec from `docs/openapi.yaml` for auto-generated requests.

---

## Next Steps

- Review [DATABASE.md](./DATABASE.md) for schema details
- Review [IMPLEMENTATION.md](./IMPLEMENTATION.md) for setup
- Follow [ROADMAP.md](./ROADMAP.md) for step-by-step implementation
