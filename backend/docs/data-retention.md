# Data Retention Policy

## Overview

Wait Time Canada implements a **30-day retention policy** for raw measurement
data. The default cleanup CLI can refresh recent aggregates before deleting old
rows, but the production GitHub Actions maintenance path now skips aggregate
refresh and performs bounded batched deletes so storage safety does not turn
into CI drag.

## Current Policy

1. Raw `measurements` rows older than 30 days are deleted during cleanup.
2. `measurement_aggregates` remain permanent and continue to power long-range analytics efficiently.
3. We still hash payloads instead of storing full HTML bodies.
4. Exact duplicate observations are now rejected at insert time.
5. Storage growth should still be monitored so retention failures are caught early.

## What Gets Deleted?

The default cleanup path deletes:
- Individual measurement records from the `measurements` table
- Associated `raw_payload_hash` and `raw_payload_snippet` fields

## What Gets Preserved?

Cleanup does **NOT** delete:
- Hospital metadata (name, location, verification status)
- Source configurations
- Scraper heartbeat/health status
- Aggregated analytics
- Daily quality snapshots
- Methodology change events

## Automated Cleanup

### GitHub Actions

The cleanup workflow is currently manual-dispatch only:
- **Workflow**: `.github/workflows/database-cleanup.yml`
- **Workflow behavior**: skip aggregate refresh, delete old rows in bounded batches, then report storage footprint
- **Stats behavior**: use `--verbose` or `--with-stats` to print age metrics too

### Manual Cleanup

You can also run cleanup manually:

```bash
# Preview cleanup
python -m waittime.cli.cleanup --dry-run

# Refresh aggregates and delete measurements older than 30 days
python -m waittime.cli.cleanup

# Collect age statistics too
python -m waittime.cli.cleanup --with-stats

# Match the bounded production cleanup path
python -m waittime.cli.cleanup --verbose --skip-aggregate-refresh --delete-batch-size 5000 --max-delete-batches 20

# Use a custom retention window
python -m waittime.cli.cleanup --retention-days 60

# Verbose output with statistics
python -m waittime.cli.cleanup --verbose

# Inspect measurements table growth
python -m waittime.cli.storage_stats --relation measurements
```

## Monitoring

### Read-Only Preservation Inventory

An already-authorized WaitTime backend runtime with its database connection
provisioned may run the fixed metadata-only inventory:

```bash
python -m waittime.cli.storage_stats --preservation-inventory
```

This is an explicit opt-in exact scan, not a routine health check. It uses one
repeatable-read, read-only transaction, sets the session timezone to UTC, and
applies a five-second PostgreSQL statement timeout to each bounded query. The
raw-measurement and aggregate tables are grouped separately by source and their
stored metric dimensions; the report includes UTC timestamp bounds, row counts,
the 30-day threshold count, and schema-aware missing-provenance counts. It emits
no hospital names, measurement values, payload hashes/snippets, URLs, or
credentials. Because exact counts and grouped bounds scan the tables, the query
may time out on a large database; on timeout it returns only a fixed error
classification and no partial report.

The inventory defines the 30-day comparison as 30 elapsed 24-hour days from a
UTC snapshot. It is not a purge preview or an audit of past cleanup runs. The
aggregate section reports summary-row coverage only and is not a backup. The
command does not inspect provider backup/PITR configuration, archive state, or
restore evidence; it cannot establish that any purge ran, that a backup exists,
or that a restore is possible. Keep those claims tied to separate provider and
isolated-restore evidence. This command does not add a production queue route or
change cleanup, retention, schedule, or backup behavior.

The existing database-cleanup.yml workflow is not an inventory route. In this
main revision it has no confirmation input and executes cleanup before
reporting storage statistics. Do not dispatch it to inspect preservation or
data age.

The prepared GitHub Actions entry point is
.github/workflows/preservation-inventory.yml. It is manual-only, runs only
from main at the exact dispatch SHA, and skips the job by default. A run
requires an explicit boolean confirmation that the operator is authorized and
accepts that detailed per-source/metric counts and date ranges will appear in
the public Actions logs. The database connect timeout is 10 seconds, lock wait
is 2 seconds, and each SQL statement retains the CLI's 5-second timeout. The
checkout/setup steps are capped at 2 minutes each, dependency installation at
8 minutes, the inventory step at 2 minutes, and the job at 15 minutes. Exact
grouped scans can still consume database read capacity and may time out. The
workflow adds no recurring scan or result artifact.

Publishing or dispatching this workflow is not authorized by preparing its
code. A project owner must separately approve the production scan and verify
that the existing DATABASE_URL secret is present and points to the intended
database. Repository source cannot verify that secret's existence or target,
and no protected GitHub environment is configured or assumed.
### Check Data Age Statistics

```python
from waittime.services.database import DatabaseService

db = DatabaseService()
stats = db.get_measurement_age_stats()

print(f"Total measurements: {stats['total_measurements']}")
print(f"Oldest measurement: {stats['oldest_measurement_age_days']} days")
print(
    f"Measurements older than {stats['older_than_days_threshold']} days: "
    f"{stats['measurements_older_than_threshold']}"
)
```

### Example Output

```
Total measurements: 15,234
Oldest measurement: 45.3 days old
Newest measurement: 0.2 days old
Measurements older than 30 days: 1,847
```

### Check Storage Growth

```bash
python -m waittime.cli.storage_stats --relation measurements
python -m waittime.cli.storage_stats --relation measurements --exact-count --json
```

## Implementation Details

### Default Cleanup Flow

```python
# In cleanup CLI
# 1. optionally collect full-table age stats (--dry-run/--verbose/--with-stats)
# 2. optionally refresh recent daily aggregates
# 3. delete rows older than retention_days in bounded batches
```

### Insert-Time Efficiency Guards

- Exact duplicate raw observations are skipped via a database uniqueness guard.
- A BRIN index on `measurements.timestamp_utc` keeps long-range append-heavy scans efficient.

### Cleanup Query

```sql
WITH rows_to_delete AS (
    SELECT id
    FROM measurements
    WHERE timestamp_utc < NOW() - INTERVAL '60 days'
    LIMIT 5000
)
DELETE FROM measurements m
USING rows_to_delete d
WHERE m.id = d.id;
```

## Best Practices

1. **Keep cleanup running regularly** so storage stays within the configured database tier.
2. **Monitor storage regularly**: use database size checks and measurement age stats.
3. **Use explicit aggregation runs when needed** instead of forcing broad backfills into every storage-maintenance run.
4. **Use `--dry-run` before changing the retention window**.

## Analytics & Reporting

Long-term analytics should continue to prefer aggregate tables:

```sql
-- Example: Daily average wait times (keep forever)
CREATE TABLE daily_averages AS
SELECT
    DATE(timestamp_utc) as date,
    hospital_id,
    AVG(value) as avg_wait_time,
    COUNT(*) as measurement_count
FROM measurements
GROUP BY DATE(timestamp_utc), hospital_id;
```

The aggregate pipeline reduces read cost for analytics, but the production cleanup workflow intentionally skips routine aggregate refresh to keep maintenance bounded.

## Troubleshooting

### "Deleted 0 measurements"

This is expected if all measurements are newer than the requested retention threshold.

### "Database connection failed"

Check that `DATABASE_URL` environment variable is set correctly:

```bash
echo $DATABASE_URL
# Should output: postgresql://user@host/database
```

### Manual Recovery

If cleanup deletes data you needed:

1. **Restore from database backup** (use the configured PostgreSQL provider's recovery tooling)
2. **Re-run scrapers** to collect fresh data
3. Historical raw rows older than the retention window are not recoverable without backup restore

## Configuration

The retention period is configurable:

```python
# In code
db.cleanup_old_measurements(retention_days=60)
```

```bash
# Via CLI
python -m waittime.cli.cleanup --retention-days 60
```

```yaml
# Run the cleanup CLI on an environment-appropriate schedule
```

**Default policy**: retain raw measurements for 30 days

## Security Considerations

- Cleanup requires `DATABASE_URL` with write permissions
- The GitHub Action uses repository secrets for database access
- Always test a new retention window with `--dry-run` in production first
- Run cleanup during low-traffic windows when possible

## Future Enhancements

Potential improvements for v2:

- [ ] Storage growth dashboards / alerts
- [ ] Archive-to-cold-storage path if raw history ever needs to exceed 30 days
- [ ] Slack/email notifications on cleanup completion
- [ ] Province-specific retention policies if research needs change
