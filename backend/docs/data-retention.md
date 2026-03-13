# Data Retention Policy

## Overview

Wait Time Canada now preserves raw measurement rows for long-term historical
analysis by default. The maintenance tooling still refreshes aggregates and
reports data-age statistics, but raw measurement deletion is no longer the
standard path.

## Current Policy

1. Raw `measurements` rows are retained indefinitely unless an operator explicitly runs a purge.
2. `measurement_aggregates` remain permanent and continue to power long-range analytics efficiently.
3. We still hash payloads instead of storing full HTML bodies.
4. Exact duplicate observations are now rejected at insert time.
5. Storage growth should now be monitored instead of controlled through automatic deletion.

## What Gets Preserved?

The default maintenance path **does NOT delete**:
- Individual measurement records from the `measurements` table
- Associated `raw_payload_hash` and `raw_payload_snippet` fields
- Hospital metadata (name, location, verification status)
- Source configurations
- Scraper heartbeat/health status
- Aggregated analytics
- Daily quality snapshots
- Methodology change events

## Automated Maintenance

### GitHub Actions

The maintenance workflow is currently manual-dispatch only:
- **Workflow**: `.github/workflows/database-cleanup.yml`
- **Default behavior**: refresh aggregates without forcing a full-table age scan
- **Purge behavior**: only if the CLI is run with an explicit purge flag

### Manual Maintenance

You can also run maintenance manually:

```bash
# Preview current maintenance / optional purge behavior
python -m waittime.cli.cleanup --dry-run

# Refresh aggregates without deleting raw rows
python -m waittime.cli.cleanup

# Refresh aggregates and also collect age statistics
python -m waittime.cli.cleanup --with-stats

# Explicitly purge old raw measurements (only if you really mean to)
python -m waittime.cli.cleanup --purge-old-measurements --retention-days 60

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

### Default Maintenance Flow

```python
# In cleanup CLI
# 1. optionally collect full-table age stats (--dry-run/--verbose/--with-stats)
# 2. refresh recent hourly/daily aggregates
# 3. skip deletion unless --purge-old-measurements is provided
```

### Insert-Time Efficiency Guards

- Exact duplicate raw observations are skipped via a database uniqueness guard.
- A BRIN index on `measurements.timestamp_utc` keeps long-range append-heavy scans efficient.

### Optional Purge Query

```sql
DELETE FROM measurements
WHERE timestamp_utc < NOW() - INTERVAL '60 days'
```

## Best Practices

1. **Keep raw history unless you have a clear reason to purge it**.
2. **Monitor storage regularly**: use database size checks and measurement age stats.
3. **Keep aggregate maintenance running** so analytics stay efficient even with full raw retention.
4. **Use `--dry-run` before any purge**.

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

The aggregate pipeline reduces read cost for analytics, but it is no longer a prerequisite for preserving raw history.

## Troubleshooting

### "Deleted 0 measurements"

This is expected if:
- you did not pass `--purge-old-measurements`
- all measurements are newer than the requested purge threshold

### "Database connection failed"

Check that `DATABASE_URL` environment variable is set correctly:

```bash
echo $DATABASE_URL
# Should output: postgresql://user@host/database
```

### Manual Recovery

If a purge accidentally deletes data you needed:

1. **Restore from database backup** (Neon provides point-in-time recovery)
2. **Re-run scrapers** to collect fresh data
3. Future raw history will continue accumulating once the purge path is no longer used

## Configuration

The optional purge period is configurable:

```python
# In code
db.cleanup_old_measurements(retention_days=60)
```

```bash
# Via CLI
python -m waittime.cli.cleanup --purge-old-measurements --retention-days 60
```

```yaml
# In GitHub Actions or systemd, add an explicit purge flag only if you intend to delete raw history
```

**Default policy**: preserve raw measurements indefinitely

## Security Considerations

- Cleanup requires `DATABASE_URL` with write permissions
- The GitHub Action uses repository secrets for database access
- Always test any purge command with `--dry-run` in production first
- Treat purging raw history as an operator decision, not a routine task

## Future Enhancements

Potential improvements for v2:

- [ ] Storage growth dashboards / alerts
- [ ] Archive-to-cold-storage path if Neon cost becomes material
- [ ] Slack/email notifications on maintenance completion
- [ ] Purge safety rails requiring a second explicit confirmation flag
