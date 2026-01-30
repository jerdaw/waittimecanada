# Database Specification

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Tables & Constraints](#tables--constraints)
3. [Enums & Types](#enums--types)
4. [Indexes](#indexes)
5. [Row-Level Security](#row-level-security)
6. [Migrations](#migrations)
7. [Sample Queries](#sample-queries)

---

## Schema Overview

**Database:** PostgreSQL 15+ (via Supabase)
**Extensions Required:**
- `postgis` - Geospatial queries
- `pgcrypto` - UUID generation (built-in to Supabase)

**Design Principles:**
1. **Strict Ontology Enforcement** - Enums at database level prevent drift
2. **Audit Trail** - All measurements timestamped, never deleted
3. **Verification Workflow** - Manual approval required before public visibility
4. **Storage Safety** - Hash payloads, not full HTML
5. **Performance First** - Indexes on all query paths

**Entity Relationship:**
```
sources (1) ──< (N) hospitals (1) ──< (N) measurements
                                                ↓
                                        scraper_status (heartbeat)
```

---

## Tables & Constraints

### 1. `sources` - Provincial Data Provenance

Tracks metadata about each provincial data source.

```sql
CREATE TABLE sources (
    -- Identity
    id TEXT PRIMARY KEY,  -- e.g., 'ca-ab-ahs', 'ca-qc-msss'
    name TEXT NOT NULL,   -- e.g., 'Alberta Health Services'
    province TEXT NOT NULL CHECK (province IN (
        'AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'
    )),

    -- Documentation
    definition_url TEXT,           -- Official methodology page
    last_updated_url TEXT,         -- Where to find last update time
    data_url TEXT NOT NULL,        -- Actual data endpoint/page

    -- Province-Aware Telehealth Directory
    telehealth_name TEXT,          -- e.g., 'Info-Santé 811', 'Health Link 811'
    telehealth_phone TEXT,         -- e.g., '811'
    telehealth_url TEXT,           -- Official telehealth website

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT true,

    -- Notes for future maintainers
    scraper_notes TEXT             -- e.g., "Uses JavaScript rendering, requires Playwright"
);

-- Ensure province has unique source
CREATE UNIQUE INDEX idx_sources_province ON sources(province) WHERE is_active = true;
```

**Example Row:**
```sql
INSERT INTO sources VALUES (
    'ca-qc-msss',
    'Ministère de la Santé et des Services sociaux',
    'QC',
    'https://www.quebec.ca/en/health/finding-a-resource/consulting-in-case-of-problem/emergency-room-wait-times',
    NULL,
    'https://www.quebec.ca/sante/trouver-une-ressource/consulter-un-professionnel/urgences',
    'Info-Santé 811',
    '811',
    'https://www.quebec.ca/en/health/finding-a-resource/consulting-in-case-of-problem/info-sante-811',
    NOW(),
    NOW(),
    true,
    'Simple HTML table, no JS required'
);
```

---

### 2. `hospitals` - Facility Metadata

Stores hospital/ER facility information with verification workflow.

```sql
CREATE TABLE hospitals (
    -- Identity
    id TEXT PRIMARY KEY,           -- e.g., 'ca-qc-chum', 'ca-ab-rac'
    source_id TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    external_id TEXT,              -- ID from provincial system (if available)

    -- Basic Info
    name TEXT NOT NULL,            -- e.g., 'CHUM - Hôtel-Dieu'
    name_en TEXT,                  -- English name (for bilingual provinces)
    name_fr TEXT,                  -- French name (for bilingual provinces)

    -- Location
    province TEXT NOT NULL,        -- Denormalized for easy filtering
    city TEXT,
    address TEXT,
    postal_code TEXT,
    latitude FLOAT,
    longitude FLOAT,

    -- Classification
    facility_type TEXT NOT NULL DEFAULT 'ER' CHECK (facility_type IN (
        'ER',                      -- Emergency Room
        'URGENT_CARE',             -- Urgent Care Center
        'TRAUMA_CENTER'            -- Designated Trauma Center
    )),

    -- Workflow Flags
    is_verified BOOLEAN NOT NULL DEFAULT false,   -- Admin approved
    is_visible BOOLEAN NOT NULL DEFAULT false,    -- Show on public site
    verified_at TIMESTAMPTZ,                      -- When approved
    verified_by TEXT,                             -- Admin user ID

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_scraped_at TIMESTAMPTZ,

    -- Contact (optional)
    phone TEXT,
    website TEXT,

    -- Constraints
    CONSTRAINT valid_coordinates CHECK (
        (latitude IS NULL AND longitude IS NULL) OR
        (latitude BETWEEN -90 AND 90 AND longitude BETWEEN -180 AND 180)
    )
);

-- Composite unique constraint: one hospital per external_id per source
CREATE UNIQUE INDEX idx_hospitals_source_external
ON hospitals(source_id, external_id)
WHERE external_id IS NOT NULL;
```

**Example Row:**
```sql
INSERT INTO hospitals VALUES (
    'ca-qc-chum',
    'ca-qc-msss',
    'CHUM',
    'CHUM - Hôtel-Dieu',
    'CHUM - Hotel-Dieu',
    'CHUM - Hôtel-Dieu',
    'QC',
    'Montreal',
    '3840 Rue Saint-Urbain',
    'H2W 1T8',
    45.5122,
    -73.5706,
    'ER',
    true,
    true,
    NOW(),
    'admin-user-id',
    NOW(),
    NOW(),
    NOW(),
    NOW(),
    '514-890-8000',
    'https://www.chumontreal.qc.ca/'
);
```

---

### 3. `measurements` - Audit Log of Wait Times

The core fact table storing all scraped measurements.

```sql
CREATE TABLE measurements (
    -- Identity
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    hospital_id TEXT NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,

    -- Time
    timestamp_utc TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    scraped_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Value
    value NUMERIC NOT NULL CHECK (value >= 0),  -- Minutes
    unit TEXT NOT NULL DEFAULT 'minutes' CHECK (unit = 'minutes'),

    -- STRICT ONTOLOGY (Database-enforced enums)
    metric_family metric_family_enum NOT NULL,
    start_event start_event_enum NOT NULL,
    end_event end_event_enum NOT NULL,
    statistic_type statistic_type_enum NOT NULL,
    patient_scope patient_scope_enum NOT NULL DEFAULT 'ALL',

    -- Storage-Safe Audit
    raw_payload_hash TEXT,         -- SHA256 of source HTML/JSON
    raw_payload_snippet TEXT,      -- First 200 chars for debugging
    parser_version TEXT NOT NULL,  -- e.g., 'v1.0.0'

    -- Metadata
    scraper_id TEXT NOT NULL,      -- Which scraper produced this
    is_anomaly BOOLEAN DEFAULT false,  -- Flagged for review (future)
    notes TEXT                     -- Human notes (if manually corrected)
);

-- Prevent duplicate measurements (idempotency)
CREATE UNIQUE INDEX idx_measurements_dedup
ON measurements(hospital_id, timestamp_utc, metric_family, start_event, end_event, statistic_type)
WHERE is_anomaly = false;
```

**Example Row:**
```sql
INSERT INTO measurements (
    hospital_id, timestamp_utc, value,
    metric_family, start_event, end_event, statistic_type,
    raw_payload_hash, raw_payload_snippet, parser_version, scraper_id
) VALUES (
    'ca-qc-chum',
    '2024-01-15 14:30:00+00',
    180,
    'TIME_TO_PROVIDER',
    'REGISTRATION',
    'PHYSICIAN',
    'ROLLING_AVG',
    'a3f5e1b2c4d6e8f9a1b2c3d4e5f6a7b8',
    '<html><body>CHUM wait time: 3h00...',
    'v1.0.0',
    'quebec-scraper'
);
```

---

### 4. `scraper_status` - Heartbeat Monitor

Tracks last successful run of each scraper.

```sql
CREATE TABLE scraper_status (
    scraper_id TEXT PRIMARY KEY,   -- e.g., 'quebec-scraper', 'alberta-scraper'
    last_run TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('healthy', 'degraded', 'failed')),

    -- Stats
    hospitals_scraped INTEGER,
    measurements_created INTEGER,
    duration_seconds NUMERIC,

    -- Error tracking
    error_message TEXT,
    error_count INTEGER DEFAULT 0,

    -- Metadata
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Upsert pattern: ON CONFLICT UPDATE
```

**Example Row:**
```sql
INSERT INTO scraper_status VALUES (
    'quebec-scraper',
    NOW(),
    'healthy',
    25,
    150,
    12.4,
    NULL,
    0,
    NOW()
) ON CONFLICT (scraper_id) DO UPDATE SET
    last_run = EXCLUDED.last_run,
    status = EXCLUDED.status,
    hospitals_scraped = EXCLUDED.hospitals_scraped,
    measurements_created = EXCLUDED.measurements_created,
    duration_seconds = EXCLUDED.duration_seconds,
    error_message = EXCLUDED.error_message,
    updated_at = NOW();
```

---

## Enums & Types

PostgreSQL enums for strict ontology enforcement.

```sql
-- Metric Family: What is being measured?
CREATE TYPE metric_family_enum AS ENUM (
    'TIME_TO_PROVIDER',      -- Wait to see doctor/nurse
    'TOTAL_LOS',             -- Total length of stay
    'STRETCHER_OCCUPANCY'    -- Current ED occupancy rate
);

-- Start Event: When does the clock start?
CREATE TYPE start_event_enum AS ENUM (
    'TRIAGE',                -- After initial triage assessment
    'REGISTRATION',          -- After administrative check-in
    'DOOR',                  -- Upon physical arrival
    'UNKNOWN'                -- Source doesn't specify
);

-- End Event: When does the clock stop?
CREATE TYPE end_event_enum AS ENUM (
    'PHYSICIAN',             -- Physician initial assessment
    'PROVIDER',              -- Any provider (doctor, NP, PA)
    'DISCHARGE',             -- Patient leaves ED
    'FIRST_ASSESSMENT',      -- First clinical contact (any role)
    'TREATMENT_START'        -- Treatment begins
);

-- Statistic Type: How is the value calculated?
CREATE TYPE statistic_type_enum AS ENUM (
    'POINT_ESTIMATE',        -- Current real-time value
    'P90',                   -- 90th percentile (CIHI standard)
    'MEDIAN',                -- 50th percentile
    'MEAN',                  -- Average
    'ROLLING_AVG',           -- Moving average (window unspecified)
    'ALGORITHMIC'            -- Proprietary calculation
);

-- Patient Scope: Which patients are included?
CREATE TYPE patient_scope_enum AS ENUM (
    'ALL',                   -- All ED patients
    'MID_ACUITY',            -- CTAS 3-4 (most common)
    'NON_PRIORITY',          -- CTAS 4-5 (non-urgent)
    'ADMITTED',              -- Only patients subsequently admitted
    'DISCHARGED'             -- Only patients discharged home
);
```

---

## Indexes

Performance-critical indexes for common query patterns.

```sql
-- Fast lookup: Latest measurement per hospital
CREATE INDEX idx_measurements_hospital_time
ON measurements(hospital_id, timestamp_utc DESC);

-- Fast filtering: Visible hospitals by province
CREATE INDEX idx_hospitals_province_visible
ON hospitals(province)
WHERE is_visible = true AND is_verified = true;

-- Fast filtering: Hospitals pending verification
CREATE INDEX idx_hospitals_verification_queue
ON hospitals(created_at DESC)
WHERE is_verified = false;

-- Geospatial queries (nearest hospitals)
CREATE INDEX idx_hospitals_location
ON hospitals USING GIST (
    geography(ST_MakePoint(longitude, latitude))
)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- Fast comparability queries (same ontology)
CREATE INDEX idx_measurements_ontology
ON measurements(metric_family, start_event, end_event, statistic_type);

-- Time-series queries (recent measurements)
CREATE INDEX idx_measurements_time
ON measurements(timestamp_utc DESC);

-- Scraper health check
CREATE INDEX idx_scraper_status_updated
ON scraper_status(updated_at DESC);
```

---

## Row-Level Security

Public read-only access with write restrictions.

```sql
-- Enable RLS on all tables
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospitals ENABLE ROW LEVEL SECURITY;
ALTER TABLE measurements ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraper_status ENABLE ROW LEVEL SECURITY;

-- PUBLIC READ POLICIES (Anon key)

-- Anyone can view active sources
CREATE POLICY "Public can view active sources"
ON sources FOR SELECT
USING (is_active = true);

-- Anyone can view verified, visible hospitals
CREATE POLICY "Public can view verified hospitals"
ON hospitals FOR SELECT
USING (is_visible = true AND is_verified = true);

-- Anyone can view measurements (for visible hospitals)
CREATE POLICY "Public can view measurements"
ON measurements FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM hospitals
        WHERE hospitals.id = measurements.hospital_id
          AND hospitals.is_visible = true
          AND hospitals.is_verified = true
    )
);

-- Anyone can view scraper status
CREATE POLICY "Public can view scraper status"
ON scraper_status FOR SELECT
USING (true);

-- SERVICE ROLE WRITE POLICIES (Scrapers only)

-- Service role can insert/update sources
CREATE POLICY "Service role can manage sources"
ON sources FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

-- Service role can insert/update hospitals
CREATE POLICY "Service role can manage hospitals"
ON hospitals FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

-- Service role can insert measurements
CREATE POLICY "Service role can insert measurements"
ON measurements FOR INSERT
WITH CHECK (auth.jwt()->>'role' = 'service_role');

-- Service role can upsert scraper status
CREATE POLICY "Service role can manage scraper status"
ON scraper_status FOR ALL
USING (auth.jwt()->>'role' = 'service_role');

-- ADMIN POLICIES (Future: Admin dashboard)

-- Admins can update verification flags
-- (To be added when admin UI is built)
```

---

## Migrations

### Migration Strategy

**Tool:** Supabase CLI (`supabase migration new`)
**Versioning:** Sequential numbered files
**Application:** CI/CD pipeline applies on merge to main

### Migration Files

**`database/migrations/001_initial_schema.sql`**
```sql
-- Create enums first
CREATE TYPE metric_family_enum AS ENUM (
    'TIME_TO_PROVIDER', 'TOTAL_LOS', 'STRETCHER_OCCUPANCY'
);

CREATE TYPE start_event_enum AS ENUM (
    'TRIAGE', 'REGISTRATION', 'DOOR', 'UNKNOWN'
);

CREATE TYPE end_event_enum AS ENUM (
    'PHYSICIAN', 'PROVIDER', 'DISCHARGE', 'FIRST_ASSESSMENT', 'TREATMENT_START'
);

CREATE TYPE statistic_type_enum AS ENUM (
    'POINT_ESTIMATE', 'P90', 'MEDIAN', 'MEAN', 'ROLLING_AVG', 'ALGORITHMIC'
);

CREATE TYPE patient_scope_enum AS ENUM (
    'ALL', 'MID_ACUITY', 'NON_PRIORITY', 'ADMITTED', 'DISCHARGED'
);

-- Create tables
CREATE TABLE sources ( /* ... full definition ... */ );
CREATE TABLE hospitals ( /* ... full definition ... */ );
CREATE TABLE measurements ( /* ... full definition ... */ );
```

**`database/migrations/002_add_heartbeat.sql`**
```sql
CREATE TABLE scraper_status ( /* ... full definition ... */ );
```

**`database/migrations/003_add_indexes.sql`**
```sql
CREATE INDEX idx_measurements_hospital_time ON measurements(hospital_id, timestamp_utc DESC);
CREATE INDEX idx_hospitals_province_visible ON hospitals(province) WHERE is_visible = true;
-- ... all other indexes ...
```

**`database/migrations/004_enable_rls.sql`**
```sql
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
-- ... all RLS policies ...
```

### Migration Commands

```bash
# Create new migration
supabase migration new add_feature_name

# Apply locally
supabase db reset

# Apply to production (via GitHub Actions)
supabase db push --linked
```

---

## Sample Queries

### 1. Get Latest Wait Times for All Hospitals (Public Map View)

```sql
SELECT DISTINCT ON (h.id)
    h.id,
    h.name,
    h.province,
    h.city,
    h.latitude,
    h.longitude,
    m.value AS wait_minutes,
    m.timestamp_utc,
    m.metric_family,
    m.start_event,
    m.end_event,
    m.statistic_type
FROM hospitals h
LEFT JOIN measurements m ON m.hospital_id = h.id
WHERE h.is_visible = true
  AND h.is_verified = true
ORDER BY h.id, m.timestamp_utc DESC;
```

**Frontend Implementation:**
```typescript
const { data: hospitals } = await supabase
  .from('hospitals')
  .select(`
    id, name, province, city, latitude, longitude,
    measurements (
      value, timestamp_utc, metric_family, start_event, end_event, statistic_type
    )
  `)
  .eq('is_visible', true)
  .eq('is_verified', true)
  .order('timestamp_utc', { foreignTable: 'measurements', ascending: false })
  .limit(1, { foreignTable: 'measurements' });
```

### 2. Check Comparability Between Two Hospitals

```sql
WITH hospital_a AS (
    SELECT m.metric_family, m.start_event, m.end_event, m.statistic_type
    FROM measurements m
    WHERE m.hospital_id = 'ca-ab-rac'
    ORDER BY m.timestamp_utc DESC
    LIMIT 1
),
hospital_b AS (
    SELECT m.metric_family, m.start_event, m.end_event, m.statistic_type
    FROM measurements m
    WHERE m.hospital_id = 'ca-mb-hsc'
    ORDER BY m.timestamp_utc DESC
    LIMIT 1
)
SELECT
    a.metric_family = b.metric_family AND
    a.start_event = b.start_event AND
    a.end_event = b.end_event AND
    a.statistic_type = b.statistic_type AS is_comparable
FROM hospital_a a, hospital_b b;
```

### 3. Time Series Data for Chart (Last 24 Hours)

```sql
SELECT
    timestamp_utc,
    value AS wait_minutes
FROM measurements
WHERE hospital_id = 'ca-qc-chum'
  AND timestamp_utc > NOW() - INTERVAL '24 hours'
ORDER BY timestamp_utc ASC;
```

### 4. Verification Queue (Admin Dashboard)

```sql
SELECT
    h.id,
    h.name,
    h.province,
    h.source_id,
    h.created_at,
    COUNT(m.id) AS measurement_count
FROM hospitals h
LEFT JOIN measurements m ON m.hospital_id = h.id
WHERE h.is_verified = false
GROUP BY h.id, h.name, h.province, h.source_id, h.created_at
ORDER BY h.created_at DESC;
```

### 5. Scraper Health Dashboard

```sql
SELECT
    scraper_id,
    last_run,
    status,
    EXTRACT(EPOCH FROM (NOW() - last_run)) / 60 AS minutes_since_last_run,
    hospitals_scraped,
    measurements_created,
    error_message
FROM scraper_status
ORDER BY last_run DESC;
```

### 6. Nearest Hospitals (Geospatial Query)

```sql
SELECT
    h.id,
    h.name,
    h.city,
    ST_Distance(
        geography(ST_MakePoint(h.longitude, h.latitude)),
        geography(ST_MakePoint(-73.5673, 45.5017))  -- Montreal coordinates
    ) / 1000 AS distance_km
FROM hospitals h
WHERE h.is_visible = true
  AND h.latitude IS NOT NULL
ORDER BY distance_km ASC
LIMIT 10;
```

### 7. Comparability Matrix (Methods Page)

```sql
WITH latest_measurements AS (
    SELECT DISTINCT ON (hospital_id)
        hospital_id,
        metric_family,
        start_event,
        end_event,
        statistic_type
    FROM measurements
    ORDER BY hospital_id, timestamp_utc DESC
)
SELECT
    h.province,
    h.name,
    lm.metric_family,
    lm.start_event,
    lm.end_event,
    lm.statistic_type,
    CONCAT(lm.metric_family, '-', lm.start_event, '-', lm.end_event, '-', lm.statistic_type) AS ontology_signature
FROM hospitals h
JOIN latest_measurements lm ON lm.hospital_id = h.id
WHERE h.is_visible = true
ORDER BY h.province, h.name;
```

---

## Data Retention Policy

**Active Measurements:**
- Keep all measurements < 30 days old

**Historical Aggregates (Future):**
- Create daily aggregates for data > 30 days
- Store min, max, avg, p50, p90 per hospital per day

**Implementation:**
```sql
-- Run daily via GitHub Actions
DELETE FROM measurements
WHERE timestamp_utc < NOW() - INTERVAL '30 days'
  AND is_anomaly = false;  -- Keep anomalies for analysis
```

---

## Backup & Recovery

**Supabase Automatic Backups:**
- Daily backups retained for 7 days (free tier)
- Point-in-time recovery available (paid plans)

**Manual Backup:**
```bash
# Export schema
pg_dump $SUPABASE_URL --schema-only > schema.sql

# Export data
pg_dump $SUPABASE_URL --data-only > data.sql

# Full backup
pg_dump $SUPABASE_URL > full_backup.sql
```

**Restore:**
```bash
psql $SUPABASE_URL < full_backup.sql
```

---

## Performance Monitoring

**Query Performance:**
```sql
-- Enable pg_stat_statements extension
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- View slow queries
SELECT
    query,
    calls,
    total_time,
    mean_time,
    max_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

**Table Sizes:**
```sql
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

---

## Next Steps

- Review [API.md](./API.md) for how the frontend queries this schema
- Review [IMPLEMENTATION.md](./IMPLEMENTATION.md) for setup instructions
- See [ROADMAP.md](./ROADMAP.md) for implementation timeline
