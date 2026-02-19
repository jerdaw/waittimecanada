# Database Migrations Guide

This document explains how to create, apply, and roll back database migrations for Wait Time Canada.

> [!NOTE]
> The canonical migration history and schema reference lives in
> See `backend/migrations/README.md`.
> This guide covers the **process** — when and how to create migrations.

---

## When to Create a Migration

Create a migration whenever you need to:

- Add, rename, or drop a table or column
- Create or modify indexes
- Add or change CHECK constraints
- Create or modify PostgreSQL functions or enums
- Seed reference data that must exist before the application starts

**Never modify the production schema manually.** All schema changes must go through a migration file.

---

## Workflow

### 1. Determine the next migration number

```bash
ls backend/migrations/*.sql | tail -1
# e.g. backend/migrations/013_add_scraper_observability_columns.sql → next is 014
```

### 2. Create the migration file

```bash
touch backend/migrations/014_your_descriptive_name.sql
```

### 3. Write the migration

Use idempotent SQL so migrations are safe to re-run:

```sql
-- 014_your_descriptive_name.sql
-- Purpose: Brief description
-- Depends on: 012_optimize_indexes.sql

-- Idempotent column addition
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'your_table' AND column_name = 'your_column'
    ) THEN
        ALTER TABLE your_table ADD COLUMN your_column TEXT;
    END IF;
END
$$;

-- Rollback:
-- ALTER TABLE your_table DROP COLUMN IF EXISTS your_column;
```

### 4. Test locally

```bash
cd backend
source .venv/bin/activate
python run_migrations.py
```

Verify idempotency by running a second time — it should succeed without errors.

### 5. Document the migration

Add an entry to `backend/migrations/README.md` under the appropriate milestone section.

### 6. Update related docs

| If you changed…      | Also update…                                         |
|----------------------|------------------------------------------------------|
| API response shape   | `docs/API.md`                                        |
| Service layer        | Docstrings in `backend/src/waittime/services/`       |
| Major design choice  | New ADR in `docs/adr/`                               |

---

## Applying Migrations

### Development / staging

```bash
cd backend
source .venv/bin/activate
python run_migrations.py
```

### Production (Neon PostgreSQL)

1. **Backup first:**
   ```bash
   pg_dump $PRODUCTION_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **Run migrations:**
   ```bash
   export DATABASE_URL="$PRODUCTION_DATABASE_URL"
   python run_migrations.py
   ```

3. **Verify:**
   ```bash
   psql $PRODUCTION_DATABASE_URL -c "\d"
   ```

---

## Rolling Back

Migrations do not auto-rollback. Each migration file includes rollback SQL in comments.

**Steps:**

1. Identify the migration to undo (e.g., `014_your_descriptive_name.sql`).
2. Extract the rollback SQL from the file's comments.
3. Execute it manually:
   ```bash
   psql $DATABASE_URL
   -- paste rollback SQL here
   ```
4. Rename the migration file to `.sql.skip` to prevent re-application:
   ```bash
   mv backend/migrations/014_your_descriptive_name.sql \
      backend/migrations/014_your_descriptive_name.sql.skip
   ```

> [!CAUTION]
> Always rollback in **reverse order** (newest migration first).
> Data dropped by a rollback is **permanently lost** — ensure you have a backup.

---

## CI/CD Integration

Migrations are validated in two workflows:

| Workflow | What it checks |
|---|---|
| `scraper-ci.yml` | Runs `run_migrations.py` + full pytest suite |
| `production-readiness.yml` | Validates file naming convention and SQL syntax |

The `database-migrate.yml` workflow can be triggered manually to apply migrations to production via GitHub Actions.

---

## Current Schema Summary

| Table | Rows | Purpose |
|---|---|---|
| `sources` | 4 | Provincial data source metadata |
| `hospitals` | 380+ | Facility metadata with geo-coordinates |
| `measurements` | 100k+ (30d retention) | Wait time audit log with ontology tags |
| `measurement_aggregates` | permanent | Statistical summaries (hourly → monthly) |
| `scraper_status` | 4 | Heartbeat monitoring per source |
| `data_quality_snapshots` | daily | Scraper reliability metrics |
| `methodology_change_events` | historical | Drift detection audit log |
| `regions` | 15 | Health region metadata |
| `hospital_regions` | 380+ | Hospital-to-region mapping |

For the full schema, see `backend/migrations/README.md`.
