# Data Retention Policy

## Overview

Wait Time Canada implements a **30-day retention policy** for raw measurement
data. Routine cleanup refreshes recent aggregates first, then deletes
measurements older than the retention window to keep Neon storage bounded.

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
- **Default behavior**: refresh recent daily aggregates, then purge rows older than 30 days
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

# Use a custom retention window
python -m waittime.cli.cleanup --retention-days 60

# Verbose output with statistics
python -m waittime.cli.cleanup --verbose

# Inspect measurements table growth
python -m waittime.cli.storage_stats --relation measurements
```

## Monitoring

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
# 2. refresh recent daily aggregates
# 3. delete rows older than retention_days
```

### Insert-Time Efficiency Guards

- Exact duplicate raw observations are skipped via a database uniqueness guard.
- A BRIN index on `measurements.timestamp_utc` keeps long-range append-heavy scans efficient.

### Cleanup Query

```sql
DELETE FROM measurements
WHERE timestamp_utc < NOW() - INTERVAL '60 days'
```

## Best Practices

1. **Keep cleanup running regularly** so storage stays within the Neon tier.
2. **Monitor storage regularly**: use database size checks and measurement age stats.
3. **Keep aggregate maintenance coupled to cleanup** so long-range analytics remain available after raw rows roll off.
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

The aggregate pipeline reduces read cost for analytics and is refreshed before old raw rows are purged.

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

1. **Restore from database backup** (Neon provides point-in-time recovery)
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
# In GitHub Actions or systemd, run the cleanup CLI on a schedule
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
