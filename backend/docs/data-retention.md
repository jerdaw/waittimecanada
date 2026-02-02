# Data Retention Policy

## Overview

WaitTime Canada implements a **30-day retention policy** for raw measurement data to ensure storage safety and prevent database bloat. This is a core architectural requirement from the strategic plan.

## Why 30 Days?

1. **Storage Safety**: We hash (not store) raw HTML payloads to avoid storing full web pages
2. **Database Performance**: Keeping unbounded historical data degrades query performance
3. **Privacy**: Minimizing data retention reduces privacy risk
4. **Cost Control**: Prevents runaway storage costs on cloud database (Neon)

## What Gets Deleted?

After 30 days, the following are **automatically deleted**:
- Individual measurement records from the `measurements` table
- Associated `raw_payload_hash` and `raw_payload_snippet` fields

## What Is Preserved?

The cleanup process **does NOT delete**:
- Hospital metadata (name, location, verification status)
- Source configurations
- Scraper heartbeat/health status
- Any aggregated analytics you compute beforehand

## Automated Cleanup

### GitHub Actions (Recommended)

The cleanup runs automatically via GitHub Actions:
- **Schedule**: Daily at 2 AM UTC
- **Workflow**: `.github/workflows/database-cleanup.yml`
- **Manual Trigger**: Can be triggered manually from Actions tab

### Manual Cleanup

You can also run cleanup manually:

```bash
# Preview what would be deleted
python -m waittime.cli.cleanup --dry-run

# Actually delete old measurements (30 days)
python -m waittime.cli.cleanup

# Use custom retention period (e.g., 60 days)
python -m waittime.cli.cleanup --retention-days 60

# Verbose output with statistics
python -m waittime.cli.cleanup --verbose
```

## Monitoring

### Check Data Age Statistics

```python
from waittime.services.database import DatabaseService

db = DatabaseService()
stats = db.get_measurement_age_stats()

print(f"Total measurements: {stats['total_measurements']}")
print(f"Oldest measurement: {stats['oldest_measurement_age_days']} days")
print(f"Measurements needing cleanup: {stats['measurements_older_than_30_days']}")
```

### Example Output

```
Total measurements: 15,234
Oldest measurement: 45.3 days old
Newest measurement: 0.2 days old
Measurements older than 30 days: 1,847
```

## Implementation Details

### Database Method

```python
# In DatabaseService
deleted_count = db.cleanup_old_measurements(retention_days=30)
# Returns: number of measurements deleted
```

### SQL Query

```sql
DELETE FROM measurements
WHERE timestamp_utc < NOW() - INTERVAL '30 days'
```

## Best Practices

1. **Compute Aggregates First**: If you need historical trends, compute them **before** the 30-day mark
2. **Monitor Regularly**: Use `get_measurement_age_stats()` to monitor data age
3. **Alert on Failures**: The GitHub Action should notify you if cleanup fails
4. **Test Retention Period**: Use `--dry-run` before changing retention period

## Analytics & Reporting

If you need long-term analytics, create aggregated views:

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

Then run this aggregation **before** the 30-day cleanup.

## Troubleshooting

### "Cleanup deleted 0 measurements"

This means all measurements are newer than the retention period. This is normal if:
- The database was recently created
- Scrapers haven't been running for 30 days yet

### "Database connection failed"

Check that `DATABASE_URL` environment variable is set correctly:

```bash
echo $DATABASE_URL
# Should output: postgresql://user:pass@host/database
```

### Manual Recovery

If cleanup accidentally deletes data you needed:

1. **Restore from database backup** (Neon provides point-in-time recovery)
2. **Re-run scrapers** to collect fresh data
3. Historical data is gone, but new data will accumulate

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
# In GitHub Actions
env:
  RETENTION_DAYS: 60
```

**Default**: 30 days (recommended)

## Security Considerations

- Cleanup requires `DATABASE_URL` with write permissions
- The GitHub Action uses repository secrets for database access
- Always test with `--dry-run` in production first
- Consider running cleanup during low-traffic hours (2 AM UTC)

## Future Enhancements

Potential improvements for v2:

- [ ] Selective retention (keep high-priority hospital data longer)
- [ ] Automated aggregate computation before cleanup
- [ ] Slack/email notifications on cleanup completion
- [ ] Retention policy per province (different data retention laws)
- [ ] Archive to cheaper cold storage instead of delete
