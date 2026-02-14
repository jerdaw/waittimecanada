# Quick Start: Manual Operations

**Purpose:** Quick reference for running scrapers and checking system health locally.

---

## Prerequisites

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="your_neon_connection_string"
```

---

## Run Scrapers

### Run All Scrapers
```bash
python -m waittime.cli.scraper --all
```

### Run Single Province
```bash
# Quebec
python -m waittime.cli.scraper --source quebec-msss

# Ontario
python -m waittime.cli.scraper --source ontario-health

# Alberta
python -m waittime.cli.scraper --source alberta-ahs

# British Columbia
python -m waittime.cli.scraper --source bc-phsa
```

### Dry Run (No Database Writes)
```bash
python -m waittime.cli.scraper --all --dry-run
```

### List Available Scrapers
```bash
python -m waittime.cli.scraper --list
```

---

## Check System Health

### Heartbeat Status
```bash
python -m waittime.cli.check_heartbeat --max-age 60
```

### Check Specific Source
```bash
python -m waittime.cli.check_heartbeat --source quebec-msss
```

### Dry Run (No Alerts)
```bash
python -m waittime.cli.check_heartbeat --max-age 60 --dry-run
```

---

## Database Queries

### Recent Measurements
```sql
SELECT
  source_id,
  COUNT(*) as count,
  MAX(timestamp_utc) as latest
FROM measurements
WHERE timestamp_utc > NOW() - INTERVAL '1 hour'
GROUP BY source_id;
```

### Scraper Status
```sql
SELECT
  source_id,
  last_run,
  status,
  error_message,
  EXTRACT(EPOCH FROM (NOW() - last_run))/60 AS minutes_ago
FROM scraper_status
ORDER BY last_run DESC;
```

### Hospital Visibility
```sql
SELECT
  province,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE is_visible) as visible
FROM hospitals
GROUP BY province;
```

### Transfer Alert Triage (Neon)
```sql
SELECT
  source_id,
  COUNT(*) AS measurements_24h
FROM measurements
WHERE timestamp_utc > NOW() - INTERVAL '24 hours'
GROUP BY source_id
ORDER BY source_id;
```

If counts are normal but transfer is still high, use the runbook in `docs/operations/scraper-scheduling.md` under "Neon Public Transfer Guardrails".

---

## GitHub Actions

### View Workflow Runs
1. Go to: https://github.com/yourusername/waittimecanada/actions
2. Select workflow: "Scraper Cron Job" or "Heartbeat Monitor"
3. Click latest run to view logs

### Manual Trigger
1. Go to Actions tab
2. Select "Scraper Cron Job"
3. Click "Run workflow" button
4. Select branch (usually `main`)
5. Click green "Run workflow" button

---

## Common Issues

### "No module named 'waittime'"
```bash
cd backend
pip install -e .
```

### "Database connection failed"
```bash
# Verify DATABASE_URL is set
echo $DATABASE_URL

# Test connection
python -c "import os; from waittime.services import DatabaseService; db = DatabaseService(); print('✅ Connected')"
```

### "Playwright browsers not found"
```bash
playwright install chromium
```

---

## Production Status

**Current Schedule:**
- Scrapers run every 15 minutes
- Heartbeat checks every 30 minutes
- All 4 provinces operational

**Monitoring:**
- Pushover alerts on failures
- GitHub Actions logs
- Database `scraper_status` table

**See Also:**
- [Full Operations Guide](./scraper-scheduling.md)
- [Methodology Documentation](../methodologies/)
