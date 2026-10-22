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
- **Confirmation**: `confirm_delete` is a required boolean input defaulting to `false`; the job is skipped unless it is set to `true`
- **Workflow**: `.github/workflows/database-cleanup.yml`
- **Workflow behavior**: pass `--confirm-delete`, skip aggregate refresh, delete old rows in bounded batches, then report storage footprint
- **Stats behavior**: use `--verbose` or `--with-stats` to print age metrics too

The confirmation acknowledges operator intent only. It does not prove that the
operator is authorized or that backups and restore readiness have been verified.

### Manual Cleanup

You can also run cleanup manually:

```bash
# Preview cleanup
python -m waittime.cli.cleanup --dry-run

# Refresh aggregates and delete measurements older than 30 days
python -m waittime.cli.cleanup --confirm-delete

# Collect age statistics too
python -m waittime.cli.cleanup --with-stats --confirm-delete

# Match the bounded production cleanup path
python -m waittime.cli.cleanup --verbose --skip-aggregate-refresh --delete-batch-size 5000 --max-delete-batches 20 --confirm-delete

# Use a custom retention window
python -m waittime.cli.cleanup --retention-days 60 --confirm-delete

# Verbose output with statistics
python -m waittime.cli.cleanup --verbose --confirm-delete

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

Before writing to stdout, the CLI validates the complete result against a fixed
field and label allowlist. Unknown fields, unsupported non-null source or
dimension labels, and malformed values produce only the fixed
`output_contract_mismatch` error; no partial report is emitted. Legitimate
null provenance, dimension, and timestamp fields remain null. Adding a source
ID or changing the ontology requires a corresponding reviewed CLI allowlist
update before the value can appear in this output.

The inventory defines the 30-day comparison as 30 elapsed 24-hour days from a
UTC snapshot. It is not a purge preview or an audit of past cleanup runs. The
aggregate section reports summary-row coverage only and is not a backup. The
command does not inspect provider backup/PITR configuration, archive state, or
restore evidence; it cannot establish that any purge ran, that a backup exists,
or that a restore is possible. Keep those claims tied to separate provider and
isolated-restore evidence. This command does not add a production queue route or
change cleanup, retention, schedule, or backup behavior.

### Opt-In Private Measurement Archive Command (Not a Backup or Restore)

The backend provides an explicitly invoked command for exporting exact stored
`measurements` rows, plus offline verification commands. Export is not called
by a workflow, scheduler, cleanup path, public exporter, route, or production
job. Its `--confirm-export` flag records operator intent only; it does not
establish authorization. The command uses a read-only repeatable-read PostgreSQL
transaction and streams the full stored row identity and provenance fields
without joins or scientific normalization. The representation preserves
unknown stored labels and nullable values; it does not claim that archived
observations are scientifically equivalent or comparable. Before reading rows,
the writer compares the live `measurements` table's column names, types,
modifiers, and nullability with the versioned projection, independent of
physical column order, and fails closed on schema drift. The explicit select
list controls archive order. The resulting artifact covers the measurement
table only; it is not a full database backup of hospitals, sources, or schema.
The writer passes a libpq connection timeout capped at 10 seconds, bounds each
control and fetch statement by the remaining 600-second transaction deadline
(with a maximum 120-second statement timeout), and aborts if the deadline is
exceeded. Client/server scheduling may still cause a small cancellation
overrun; libpq may apply its connection timeout separately to each host in a
multi-host connection string.

The archive directory and files are created with owner-only permissions. The
utility does not inspect the destination parent's permissions, access controls,
encryption, or durability; choose an already approved, access-controlled
storage location. A parent symlink is resolved before creating the archive,
while an existing or symlink final destination is rejected. Its canonical
JSONL artifact and manifest are checksummed and the manifest is published last,
so incomplete output is rejected. Checksums detect accidental changes and
truncation but are not a digital signature or an authenticated source/approval
record. The manifest requires policy, access-control, and
expiry references, but those values are recorded only: this utility does not
verify approval, authorize access, or enforce expiry. Supply reference
identifiers, never credentials, keys, or secret URLs. An archive contains
complete historical measurement rows, including payload snippets, and must be
handled as sensitive data.

The `python -m waittime.cli.measurement_archive export` command requires an
explicit new destination, policy and access-control references, a
timezone-aware expiry, and `--confirm-export`. It reads its database
connection from the existing runtime environment; it has no credential
argument. Before constructing the database service, it validates these inputs
and rejects an unavailable, existing, or symlink destination. Its bounded JSON
output contains only status, row count,
checksums, and verification flags; failures do not echo paths, database errors,
or row content. For example, the command shape is:

```bash
python -m waittime.cli.measurement_archive export \
  --destination /path/to/new-private-directory \
  --policy-reference approved-policy-id \
  --access-control-reference approved-access-id \
  --expires-at-utc 2027-10-18T12:00:00Z \
  --confirm-export
```

This example is documentation only, not approval to export real rows. Before
any export of real rows, the owner must separately approve its purpose,
authorized operators, access-controlled storage location, and expiry/deletion
process. The offline `python -m waittime.cli.measurement_archive verify` and
`python -m waittime.cli.measurement_archive restore-check` commands inspect
only local files. They confirm archive checksums, schema, row ordering, and
exact parse/serialize read-back; `restore-check` is explicitly **not** a
PostgreSQL restore. A separate isolated PostgreSQL 17.11 run passed the
native archive tests using synthetic records only, including repeatable-read
behavior during concurrent insert/update, schema-drift rejection,
statement-cancellation cleanup, and an exact restore into a separate test
database. This does not validate provider
backups/PITR or any restore of real Wait Time Canada data. No archive or purge
receipt is created by the inventory command. Before any archive of real rows
is run, real-data backup and restore readiness remain separate gates. The
30-day raw-measurement retention policy and production cleanup behavior remain
unchanged.

To repeat the synthetic test from `backend/`, use a sanitized environment and
an explicit PostgreSQL 17 binary directory; no database URL or environment
database settings are accepted. The current native fixture creates temporary
cluster state under canonical `/private/tmp`, which must be writable on the
host:

```sh
env -i PATH=/usr/bin:/bin LC_ALL=C LANG=C TZ=UTC PYTHONPATH=src \
  /absolute/path/to/python -m pytest -q \
  tests/integration/test_measurement_archive_native_postgres.py \
  --run-native-archive-pg \
  --native-pg-bin-dir=/absolute/path/to/postgresql-17/bin
```

The database-backed cases in this test module remain skipped unless both
explicit options are supplied; its pure enum regression runs without them.

The existing database-cleanup.yml workflow is not an inventory route. It
requires an explicit `confirm_delete` input (default false) and skips the job
unless that confirmation is true; when run, it executes cleanup before
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

The inventory shares the cleanup concurrency group. GitHub allows only one
pending run in a concurrency group; a newer pending run can replace an older
one even when cancel-in-progress is false, so the queue is not FIFO. Dispatch
only in an approved quiet window after confirming there is no active or pending
cleanup or inventory run. A dispatch is not proof that the job started; do not
repeat or automatically retry it. Verify the exact event SHA and wait for the
run's terminal result before using its output.

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
db.cleanup_old_measurements(retention_days=60, confirm_delete=True)
```

```bash
# Via CLI
python -m waittime.cli.cleanup --retention-days 60 --confirm-delete
```

```yaml
# Run the cleanup CLI on an environment-appropriate schedule
```

**Default policy**: retain raw measurements for 30 days

## Security Considerations

- Cleanup requires `DATABASE_URL` with write permissions
- `--confirm-delete` acknowledges operator intent; it does not verify authorization, backup availability, or restore readiness
- The GitHub Action uses repository secrets for database access
- Always test a new retention window with `--dry-run` in production first
- Run cleanup during low-traffic windows when possible

## Future Enhancements

Potential improvements for v2:

- [ ] Storage growth dashboards / alerts
- [ ] Archive-to-cold-storage path if raw history ever needs to exceed 30 days
- [ ] Slack/email notifications on cleanup completion
- [ ] Province-specific retention policies if research needs change
