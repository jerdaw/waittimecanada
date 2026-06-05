# Database Migrations

This directory contains SQL migration files for the Wait Time Canada database schema.

---

## Quick Start

### Running Migrations

From the repository root:

```bash
cd backend
source .venv/bin/activate
python run_migrations.py
```

**Output:**
```
Found 20 migration files:

Running: 001_create_enums.sql
  ✓ Success

Running: 002_create_tables.sql
  ✓ Success

...

✅ All migrations completed successfully!
```

### Idempotency

Migrations use `DO $$ ... EXCEPTION WHEN duplicate_object THEN NULL; END $$;` blocks or similar patterns to be safely re-runnable. The migration runner (`run_migrations.py`) will skip migrations that have already been applied.

---

## Migration Architecture

### File Naming Convention

```
NNN_descriptive_name.sql
```

- `NNN`: Zero-padded sequential number (001, 002, ..., 020)
- `descriptive_name`: Action and target (e.g., `create_enums`, `add_occupancy_columns`)
- **Always use `.sql` extension** (`.sql.skip` files are intentionally excluded)

### Execution Order

Migrations run in **lexicographic order** (alphabetical). The numeric prefix ensures correct execution sequence.

### Migration Runner

**Location:** `backend/run_migrations.py`

**Behavior:**
- Reads all `*.sql` files from `backend/migrations/`
- Sorts alphabetically (001 → 020)
- Executes each in a transaction
- Stops on first error (unless safe duplicate)
- Safe duplicate errors (already exists): ⚠ Warning, continues
- Other errors: ❌ Fails, stops execution

**Safe Duplicate Error Codes:**
- `42710`: Duplicate object (enum, type)
- `42P07`: Duplicate table/relation
- `42723`: Duplicate function

---

## Migration History

### M1: Foundation (001-005)

#### 001_create_enums.sql
**Purpose:** Define PostgreSQL enums for the metric ontology system
**Created:** 2026-01-29
**Milestone:** M1 (Database Foundation)

**Enums Created:**
- `metric_family_enum`: What is measured? (TIME_TO_PROVIDER, TOTAL_LOS, STRETCHER_OCCUPANCY)
- `start_event_enum`: When does clock start? (TRIAGE, REGISTRATION, DOOR, UNKNOWN)
- `end_event_enum`: When does clock stop? (PHYSICIAN, PROVIDER, DISCHARGE, FIRST_ASSESSMENT)
- `statistic_type_enum`: How is value calculated? (P90, MEDIAN, MEAN, ROLLING_AVG, ALGORITHMIC, POINT_ESTIMATE)
- `patient_scope_enum`: Which patients? (ALL, MID_ACUITY, NON_PRIORITY, HIGH_ACUITY)
- `scraper_status_enum`: Scraper health (healthy, error, stale)

**Rationale:** See ADR-0002 (Ontology-based metric tagging)

**Rollback:**
```sql
DROP TYPE IF EXISTS scraper_status_enum;
DROP TYPE IF EXISTS patient_scope_enum;
DROP TYPE IF EXISTS statistic_type_enum;
DROP TYPE IF EXISTS end_event_enum;
DROP TYPE IF EXISTS start_event_enum;
DROP TYPE IF EXISTS metric_family_enum;
```

---

#### 002_create_tables.sql
**Purpose:** Create core database tables
**Created:** 2026-01-29
**Milestone:** M1 (Database Foundation)
**Depends on:** 001_create_enums.sql

**Tables Created:**
1. **sources** - Provincial data source metadata
   - Tracks official provincial URLs and methodology links
   - Stores default ontology mappings per source
   - Includes telehealth routing info (811 variations by province)

2. **hospitals** - Healthcare facility metadata
   - Geographic coordinates (latitude/longitude) for mapping
   - Verification workflow: `is_verified`, `is_visible` flags
   - Constraint: Must be verified before visible

3. **measurements** - Wait time measurement audit log
   - Full ontology tagging (metric_family, start_event, end_event, statistic_type, patient_scope)
   - Payload hashing (SHA256) instead of full HTML storage
   - Parser version tracking for schema evolution
   - Indexes: `idx_measurements_hospital_timestamp`, `idx_measurements_timestamp`

4. **scraper_status** - Heartbeat monitoring
   - Last run timestamp per source
   - Status enum (healthy, error, stale)

**Rollback:**
```sql
DROP TABLE IF EXISTS scraper_status;
DROP TABLE IF EXISTS measurements;
DROP TABLE IF EXISTS hospitals;
DROP TABLE IF EXISTS sources;
```

---

#### 003_create_rls_policies.sql.skip
**Purpose:** Row-Level Security policies (SKIPPED)
**Status:** Intentionally excluded (`.sql.skip` extension)
**Rationale:** RLS policies deferred; some hosted PostgreSQL pooling modes may conflict with RLS session variables

**Note:** This file will not be executed by `run_migrations.py`. If RLS is needed in future, rename to `.sql` and review policies.

---

#### 004_seed_sources.sql
**Purpose:** Seed provincial data sources
**Created:** 2026-02-11
**Milestone:** M16 (Multi-Province Operationalization)

**Sources Seeded:**
- `quebec-msss`: Quebec MSSS (Ministère de la Santé)
- `ontario-health`: historical seed later corrected to Health Quality Ontario semantics by `020_sync_active_source_definitions.sql`
- `alberta-ahs`: Alberta Health Services
- `bc-phsa`: BC Provincial Health Services Authority

**Telehealth Routing:**
- ON: Health Connect Ontario 811
- QC: Info-Santé 811
- AB: Health Link 811
- BC: HealthLink BC 811

**Rollback:**
```sql
DELETE FROM sources WHERE id IN ('quebec-msss', 'ontario-health', 'alberta-ahs', 'bc-phsa');
```

#### 020_sync_active_source_definitions.sql
**Purpose:** Re-align active source rows to the canonical source catalog in
`backend/data/sources/*.json`
**Created:** 2026-04-16
**Milestone:** Ontario completion / source-metadata sync

**Key Corrections Applied:**
- `ontario-health`: Health Quality Ontario, current HQO URLs, `MEAN`
- `alberta-ahs`: `POINT_ESTIMATE`
- active source URLs and telehealth metadata re-synced without changing source IDs

---

#### 005_create_functions.sql
**Purpose:** Create PostgreSQL utility functions
**Created:** 2026-01-29
**Functions:** (Content TBD - check file for specific functions)

---

### M13: Aggregation Pipeline (006)

#### 006_create_measurement_aggregates.sql
**Purpose:** Permanent statistical summary storage
**Created:** 2026-02-06
**Milestone:** M13 (Aggregation Pipeline)
**Rationale:** ADR-0008 (Permanent aggregates for retention policy)

**Table Created:** `measurement_aggregates`
- Granularity: `hourly`, `daily`, `weekly`, `monthly`
- Metrics: count, min, max, mean, median, p50, p75, p90, p95, p99
- Purpose: Retain aggregates for efficient long-range analytics while raw measurements are also preserved
- Indexes: Composite index on (hospital_id, granularity, window_start) for efficient querying

**Rollback:**
```sql
DROP TABLE IF EXISTS measurement_aggregates;
```

---

### M14: Data Quality & Anomaly Detection (007-009)

#### 007_create_data_quality_snapshots.sql
**Purpose:** Daily scraper reliability metrics
**Created:** 2026-02-06
**Milestone:** M14 (Data Quality & Anomaly Detection)
**Rationale:** ADR-0009 (Data quality monitoring)

**Table Created:** `data_quality_snapshots`
- Daily snapshots of measurement counts, anomaly counts, scraper success rates
- Per-source tracking for quality dashboard
- Enables trend analysis of data quality over time

**Rollback:**
```sql
DROP TABLE IF EXISTS data_quality_snapshots;
```

---

#### 008_add_anomaly_columns.sql
**Purpose:** Add anomaly detection flags to measurements
**Created:** 2026-02-06
**Milestone:** M14 (Data Quality & Anomaly Detection)

**Columns Added to `measurements`:**
- `is_anomaly`: Boolean flag for statistical outliers
- `anomaly_reason`: TEXT description of why flagged (e.g., "Exceeds 3 sigma threshold")

**Rollback:**
```sql
ALTER TABLE measurements DROP COLUMN IF EXISTS anomaly_reason;
ALTER TABLE measurements DROP COLUMN IF EXISTS is_anomaly;
```

---

#### 009_create_methodology_change_events.sql
**Purpose:** Track provincial reporting methodology changes
**Created:** 2026-02-06
**Milestone:** M14 (Data Quality & Anomaly Detection)

**Table Created:** `methodology_change_events`
- Tracks when provinces change metric_family, start_event, end_event, statistic_type
- Stores old/new ontology values for comparability impact analysis
- Enables methodology timeline visualization

**Rollback:**
```sql
DROP TABLE IF EXISTS methodology_change_events;
```

---

### M15: Analytics & Benchmarking (010)

#### 010_create_regions_tables.sql
**Purpose:** Add regional intelligence mapping
**Created:** 2026-02-07
**Milestone:** M15 (Analytics & Benchmarking)

**Tables Created:**
1. **regions** - Health region metadata (15 regions across 4 provinces)
   - Official region names and province associations
   - Enables regional benchmarking (hospital vs regional average)

2. **hospital_regions** - Hospital-to-region mapping
   - Many-to-one relationship (hospitals belong to regions)
   - Foreign keys to both hospitals and regions tables

**Rollback:**
```sql
DROP TABLE IF EXISTS hospital_regions;
DROP TABLE IF EXISTS regions;
```

---

### M17: Quebec Occupancy (011)

#### 011_add_occupancy_columns.sql
**Purpose:** Add stretcher occupancy metrics
**Created:** 2026-02-08
**Milestone:** M17 (Quebec Occupancy Implementation)

**Columns Added to `measurements`:**
- `patients_waiting`: Number of patients waiting for provider (INTEGER ≥ 0)
- `patients_in_treatment`: Number of patients being treated (INTEGER ≥ 0)
- `total_treatment_spaces`: ER capacity (INTEGER ≥ 0)

**Usage:** Calculate occupancy percentage = (patients_in_treatment / total_treatment_spaces) × 100

**Rollback:**
```sql
ALTER TABLE measurements DROP COLUMN IF EXISTS total_treatment_spaces;
ALTER TABLE measurements DROP COLUMN IF EXISTS patients_in_treatment;
ALTER TABLE measurements DROP COLUMN IF EXISTS patients_waiting;
```

---

### M23: Performance Optimization (012)

#### 012_optimize_indexes.sql
**Purpose:** Add composite indexes for common analytics and API query patterns
**Created:** 2026-02-18
**Milestone:** M23 (Quality & Standardization)

**Highlights:**
- Adds targeted indexes for high-frequency measurement queries
- Improves trend, benchmark, and filtering performance
- Leaves table contracts unchanged (index-only migration)

---

### M30: Scraper Observability (013)

#### 013_add_scraper_observability_columns.sql
**Purpose:** Add structured heartbeat metadata for failure visibility and reliability triage
**Created:** 2026-02-19
**Milestone:** M30 (Scraper Failure Visibility & Reliability Hardening)

**Columns Added to `scraper_status`:**
- `last_success_run`
- `last_success_measurements_count`
- `last_error_run`
- `last_error_category`
- `last_error_stage`
- `consecutive_failures`
- `last_run_duration_ms`

**Indexes Added:**
- `idx_scraper_status_last_success_run`
- `idx_scraper_status_last_error_run`
- `idx_scraper_status_consecutive_failures`

---

### M31: Raw Retention Efficiency Guards (016)

#### 016_add_measurement_retention_efficiency_guards.sql
**Purpose:** Improve raw-measurement retention efficiency and suppress exact duplicates
**Created:** 2026-03-13
**Milestone:** M31 (Raw Retention Hardening)

**Changes:**
- Removes exact historical duplicate raw observations before constraints are added
- Adds an exact-observation uniqueness guard on `measurements`
- Adds a BRIN index on `measurements.timestamp_utc`

**Rationale:** Prevent exact duplicate growth and keep append-heavy time scans efficient regardless of the cleanup window.

---

### M31: Alert State Deduplication (017)

#### 017_add_scraper_alert_state.sql
**Purpose:** Persist scraper incident state so heartbeat alerting only notifies on transitions
**Created:** 2026-03-13
**Milestone:** M31 (Alert Noise Reduction & Incident State Tracking)

**Table Added:**
- `scraper_alert_state`

**Columns Added:**
- `active_incident_kind`
- `active_incident_fingerprint`
- `opened_at`
- `last_notified_at`
- `last_resolved_at`

**Indexes Added:**
- `idx_scraper_alert_state_active_incident`

---

## Creating New Migrations

### Step 1: Determine Next Number

```bash
ls backend/migrations/*.sql | tail -1
# Output: backend/migrations/020_sync_active_source_definitions.sql
# Next: 021
```

### Step 2: Create Migration File

```bash
touch backend/migrations/018_your_descriptive_name.sql
```

### Step 3: Write Migration

**Template:**

```sql
-- 014_your_descriptive_name.sql
-- Brief description of what this migration does
-- Depends on: NNN_previous_migration.sql (if applicable)

-- Your SQL here (DDL statements, ALTER TABLE, CREATE INDEX, etc.)

-- Add comments for complex changes
COMMENT ON TABLE your_table IS 'Description of table purpose';

-- Include idempotency where possible
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'your_table' AND column_name = 'your_column') THEN
        ALTER TABLE your_table ADD COLUMN your_column TEXT;
    END IF;
END
$$;

-- Rollback (optional but recommended):
-- DROP TABLE IF EXISTS your_table;
-- ALTER TABLE your_table DROP COLUMN IF EXISTS your_column;
```

### Step 4: Test Migration Locally

```bash
cd backend
source .venv/bin/activate

# Test on your local/dev database
python run_migrations.py

# Verify schema changes
psql $DATABASE_URL -c "\d your_table"
```

### Step 5: Document in This README

Add entry to **Migration History** section above with:
- Migration number and file name
- Purpose and rationale
- Milestone context
- Tables/columns affected
- Rollback instructions

### Step 6: Update Related Docs

If schema changes affect:
- **API responses**: Update `docs/API.md`
- **Services**: Update docstrings in `backend/src/waittime/services/`
- **Models**: Update `backend/src/waittime/core/models.py`
- **Architecture**: Consider ADR in `docs/adr/` if major design decision

---

## Rollback Procedures

### Principles

1. **Never rollback in production without backup**
2. **Test rollback on dev/staging first**
3. **Data loss is permanent** - ensure you have exports if needed

### Manual Rollback Steps

#### Step 1: Identify Migration to Rollback

```bash
# List all migrations
ls -1 backend/migrations/*.sql

# Example: Rollback 011_add_occupancy_columns.sql
```

#### Step 2: Extract Rollback Commands

Each migration should include rollback instructions in comments. Example:

```sql
-- Rollback:
-- ALTER TABLE measurements DROP COLUMN IF EXISTS total_treatment_spaces;
-- ALTER TABLE measurements DROP COLUMN IF EXISTS patients_in_treatment;
-- ALTER TABLE measurements DROP COLUMN IF EXISTS patients_waiting;
```

#### Step 3: Execute Rollback

```bash
# Connect to database
psql $DATABASE_URL

# Run rollback commands (remove comment markers)
ALTER TABLE measurements DROP COLUMN IF EXISTS total_treatment_spaces;
ALTER TABLE measurements DROP COLUMN IF EXISTS patients_in_treatment;
ALTER TABLE measurements DROP COLUMN IF EXISTS patients_waiting;

# Verify
\d measurements
```

#### Step 4: Remove Migration File (Optional)

```bash
# Only if you want to prevent re-application
mv backend/migrations/011_add_occupancy_columns.sql \
   backend/migrations/011_add_occupancy_columns.sql.skip
```

### Rollback Last N Migrations

If you need to rollback multiple migrations in sequence:

```bash
# Example: Rollback 010 and 011

# Rollback 011 first (reverse order)
psql $DATABASE_URL < backend/migrations/011_rollback.sql

# Then rollback 010
psql $DATABASE_URL < backend/migrations/010_rollback.sql
```

**Critical:** Always rollback in **reverse order** (newest first) to respect dependencies.

---

## Testing Migrations

### Local Testing Checklist

Before committing a new migration:

- [ ] **Idempotency**: Run `python run_migrations.py` twice - should succeed both times
- [ ] **Rollback**: Execute rollback commands, verify schema reverts
- [ ] **Re-apply**: Run migration again after rollback, should succeed
- [ ] **Unit Tests**: Ensure `pytest tests/` still passes
- [ ] **Service Tests**: Test affected services (e.g., DatabaseService, scrapers)
- [ ] **Manual Verification**: Connect to DB and inspect schema with `\d table_name`

### CI/CD Testing

Migrations are tested in GitHub Actions:

- **Scraper CI** (`scraper-ci.yml`): Runs migrations + pytest
- **Production Readiness** (`production-readiness.yml`): Validates migration file naming and syntax

### Migration Smoke Test

```bash
# Test migrations on a fresh database
export DATABASE_URL="postgresql://user@localhost:5432/waittimecanada_test"

# Drop and recreate test database
dropdb waittimecanada_test
createdb waittimecanada_test

# Run all migrations
cd backend
python run_migrations.py

# Should output:
# ✅ All migrations completed successfully!
```

---

## Troubleshooting

### Error: "relation already exists"

**Cause:** Migration already applied, but not marked as idempotent

**Fix:** Wrap in idempotency check or use `IF NOT EXISTS`:

```sql
CREATE TABLE IF NOT EXISTS your_table (...);
```

### Error: "duplicate object"

**Cause:** Enum or type already exists

**Fix:** Use exception handling:

```sql
DO $$
BEGIN
    CREATE TYPE your_enum AS ENUM ('value1', 'value2');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;
```

### Error: "column already exists"

**Cause:** Column addition already applied

**Fix:** Check before adding:

```sql
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'your_table' AND column_name = 'your_column') THEN
        ALTER TABLE your_table ADD COLUMN your_column TEXT;
    END IF;
END
$$;
```

### Error: "permission denied for schema public"

**Cause:** Database user lacks schema creation privileges

**Fix:** Grant permissions (requires admin access):

```sql
GRANT CREATE ON SCHEMA public TO your_user;
```

### Migration Fails Mid-Execution

**Cause:** Syntax error or constraint violation

**Steps:**
1. Check error message in console output
2. Fix SQL in migration file
3. Manually rollback any partially applied changes
4. Re-run `python run_migrations.py`

**Prevention:** Always test migrations on dev database first

---

## Schema Visualization

### Current Schema (15 tables)

```
sources (4 rows)
  ├── id (TEXT, PK)
  ├── province (CHAR(2))
  ├── url, methodology_url
  └── default_metric_family, default_start_event, default_end_event, default_statistic_type

hospitals (380+ rows)
  ├── id (TEXT, PK)
  ├── source_id → sources(id)
  ├── province, city, latitude, longitude
  └── is_verified, is_visible

measurements (30-day retained raw history)
  ├── id (BIGSERIAL, PK)
  ├── hospital_id → hospitals(id)
  ├── metric_family, start_event, end_event, statistic_type, patient_scope
  ├── value (wait time in minutes)
  ├── raw_payload_hash (SHA256), raw_payload_snippet
  ├── is_anomaly, anomaly_reason
  └── patients_waiting, patients_in_treatment, total_treatment_spaces (occupancy)

measurement_aggregates (permanent storage)
  ├── hospital_id → hospitals(id)
  ├── granularity (hourly, daily, weekly, monthly)
  ├── window_start, window_end
  └── count, min, max, mean, median, p50, p75, p90, p95, p99

scraper_status (4 rows, one per source)
  ├── source_id → sources(id)
  ├── last_run, status (healthy|error|stale)
  └── error_message

scraper_alert_state (4 rows, one per source)
  ├── source_id → sources(id)
  ├── active_incident_kind, active_incident_fingerprint
  └── opened_at, last_notified_at, last_resolved_at

data_quality_snapshots (daily)
  ├── source_id → sources(id)
  ├── snapshot_date
  └── measurement_count, anomaly_count, success_rate

methodology_change_events (historical log)
  ├── source_id → sources(id)
  ├── detected_at
  ├── old_metric_family, new_metric_family (+ other ontology fields)
  └── impact_description

regions (15 rows)
  ├── id (TEXT, PK)
  ├── name, province
  └── created_at

hospital_regions (380+ mappings)
  ├── hospital_id → hospitals(id)
  └── region_id → regions(id)

public_data_sources (public-health-hub source catalog)
  ├── source_id (TEXT, PK)
  ├── domain, connector_type, license_reuse_status
  └── provenance_url, last_verified_at, last_refreshed_at

resource_locations (public-health facilities and AEDs)
  ├── id (TEXT, PK)
  ├── source_id → public_data_sources(source_id)
  ├── kind, name, province
  └── latitude, longitude, provenance_url, last_refreshed_at

public_health_alerts (recalls and safety alerts)
  ├── id (TEXT, PK)
  ├── source_id → public_data_sources(source_id)
  ├── title, alert_type, published_at
  └── provenance_url, last_refreshed_at

public_health_system_metrics (Ontario EMS context)
  ├── id (TEXT, PK)
  ├── source_id → public_data_sources(source_id)
  ├── series_key, geography_name, reporting_year
  └── metrics (JSONB), provenance_url, last_refreshed_at

public_health_source_alert_state (public-health incident state)
  ├── source_id → public_data_sources(source_id)
  ├── active_incident_kind, active_incident_fingerprint
  └── opened_at, last_notified_at, last_resolved_at
```

### Entity Relationships

- **sources** ← **hospitals** (one source, many hospitals)
- **hospitals** ← **measurements** (one hospital, many measurements)
- **hospitals** ← **hospital_regions** → **regions** (many-to-many)
- **public_data_sources** ← **resource_locations / public_health_alerts / public_health_system_metrics** (one source, many normalized public-health rows)
- **sources** ← **scraper_status** (one source, one status)
- **sources** ← **data_quality_snapshots** (one source, daily snapshots)
- **sources** ← **methodology_change_events** (one source, historical events)

---

## Best Practices

### DO:
- ✅ Add migrations for **all schema changes** (never modify schema manually in production)
- ✅ Use **sequential numbering** (001, 002, ...)
- ✅ Include **rollback instructions** in comments
- ✅ Make migrations **idempotent** (safe to re-run)
- ✅ Test on **dev/staging** before production
- ✅ Document **purpose and rationale** in comments
- ✅ Link to **ADRs** for major design decisions
- ✅ Add **indexes** for frequently queried columns
- ✅ Use **CHECK constraints** for data validation
- ✅ Include **COMMENT ON** for complex tables/columns

### DON'T:
- ❌ Edit existing migrations after they've been applied to production
- ❌ Skip migration numbering (e.g., 001, 005, 006 - missing 002-004)
- ❌ Store full HTML/JSON in database (use hashing or external storage)
- ❌ Create migrations with **destructive** operations without backups
- ❌ Use `CASCADE` on `DROP` statements without careful consideration
- ❌ Forget to update this README when adding new migrations
- ❌ Run migrations manually in production without testing

---

## Production Deployment

### Pre-Deployment Checklist

Before deploying migrations to production:

- [ ] Migrations tested on dev database
- [ ] Rollback procedure documented and tested
- [ ] Database backup created (`pg_dump`)
- [ ] Downtime window scheduled (if needed for complex migrations)
- [ ] Stakeholders notified of schema changes
- [ ] CI/CD pipeline passes all tests
- [ ] This README updated with new migration entry

### Deployment Steps

1. **Backup Production Database**
   ```bash
   pg_dump $PRODUCTION_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run Migrations**
   ```bash
   cd backend
   source .venv/bin/activate
   export DATABASE_URL="$PRODUCTION_DATABASE_URL"
   python run_migrations.py
   ```

3. **Verify Schema**
   ```bash
   psql $PRODUCTION_DATABASE_URL -c "\d"
   ```

4. **Test Application**
   - Verify scrapers still run
   - Check API endpoints return expected data
   - Monitor error logs for schema-related issues

5. **Rollback Plan (if needed)**
   - Have rollback SQL ready
   - Know rollback execution time
   - Monitor application after rollback

---

## Resources

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **PostgreSQL Migration Best Practices**: https://www.postgresql.org/docs/current/ddl.html
- **ADR-0002**: Ontology-based metric tagging rationale
- **ADR-0008**: Permanent aggregates for retention policy
- **ADR-0009**: Data quality monitoring architecture
- **Backend README**: `backend/README.md` - Service architecture
- **API Docs**: `docs/API.md` - Endpoint contracts

---

## Questions?

For migration questions or issues:
- Check this README first
- Review `backend/src/waittime/services/database.py` for service-level schema interactions
- Consult ADRs in `docs/adr/` for architectural context
- Open a GitHub issue with `[migration]` tag

---

**Last Updated:** 2026-04-16
**Total Migrations:** 20
**Database Engine:** PostgreSQL 17
**Schema Version:** 020 (Active Source Definition Sync)
