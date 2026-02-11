# Scraper Scheduling & Operations

**Last Updated:** 2026-02-11
**Status:** ✅ All 4 provincial scrapers operational

---

## Overview

WaitTime Canada operates 4 provincial emergency department wait time scrapers running on GitHub Actions. This document describes the scheduling, monitoring, and operational procedures.

---

## Active Scrapers

| Province | Source ID | Status | Schedule | Last Verified |
|----------|-----------|--------|----------|---------------|
| **Quebec** | `quebec-msss` | ✅ Active | Every 15 min | 2026-02-11 |
| **Ontario** | `ontario-health` | ✅ Active | Every 15 min | 2026-02-11 |
| **Alberta** | `alberta-ahs` | ✅ Active | Every 15 min | 2026-02-11 |
| **British Columbia** | `bc-phsa` | ✅ Active | Every 15 min | 2026-02-11 |

**Total Coverage:** 380+ hospitals across 4 provinces

---

## GitHub Actions Workflows

### 1. Scraper Cron (`scraper-cron.yml`)

**Purpose:** Run all scrapers on schedule
**Schedule:** `*/15 * * * *` (every 15 minutes)
**Runtime:** ~8-12 minutes (all 4 scrapers)
**Timeout:** 20 minutes

**Execution:**
```bash
python -m waittime.cli.scraper --all
```

**Features:**
- ✅ Runs all registered scrapers automatically
- ✅ Playwright browsers installed for Ontario/Alberta
- ✅ Failure alerting via Pushover
- ✅ Tolerates individual scraper failures (succeeds if ANY data collected)
- ✅ Database connection via `DATABASE_URL` secret
- ✅ Sentry error tracking configured

**Manual Trigger:**
Available via GitHub Actions UI (`workflow_dispatch`)

---

### 2. Heartbeat Monitor (`heartbeat-monitor.yml`)

**Purpose:** Dead Man's Switch - verify scrapers are running
**Schedule:** `*/30 * * * *` (every 30 minutes)
**Max Heartbeat Age:** 60 minutes

**Execution:**
```bash
python -m waittime.cli.check_heartbeat --max-age 60
```

**Features:**
- ✅ Dynamically discovers all sources from database
- ✅ Checks `scraper_status` table for last run timestamp
- ✅ Alerts via Pushover if heartbeat > 60 minutes old
- ✅ Alerts if no heartbeat ever recorded for a source

**Alert Conditions:**
- ⚠️ Heartbeat older than 60 minutes
- 🚨 No heartbeat found for source

---

## Scraper Details

### Quebec (MSSS)
- **Methodology:** REGISTRATION → PHYSICIAN (ROLLING_AVG)
- **Technology:** BeautifulSoup (HTML parsing)
- **Coverage:** 110+ hospitals
- **Update Frequency:** Every 15 minutes
- **Special Features:** ✅ Stretcher occupancy data (M17/M18)
- **Data Quality:** 86% test coverage

### Ontario (Health Ontario)
- **Methodology:** TRIAGE → PHYSICIAN (P90)
- **Technology:** Playwright (JavaScript rendering required)
- **Coverage:** 160+ hospitals
- **Update Frequency:** Every 15 minutes
- **Browser:** Chromium (installed in GitHub Actions)

### Alberta (AHS)
- **Methodology:** TRIAGE → PHYSICIAN (P90)
- **Technology:** Playwright (JavaScript rendering required)
- **Coverage:** 50+ hospitals
- **Update Frequency:** Every 15 minutes
- **Browser:** Chromium (installed in GitHub Actions)

### British Columbia (PHSA)
- **Methodology:** TRIAGE → PHYSICIAN (P90)
- **Technology:** BeautifulSoup + JSON extraction (`__NEXT_DATA__`)
- **Coverage:** 60+ hospitals
- **Update Frequency:** Every 15 minutes
- **URL:** `https://edwaittimes.ca/legacy`

---

## Database Schema

### Sources Table
All scrapers reference entries in the `sources` table:

```sql
SELECT id, name, province FROM sources WHERE id IN (
  'quebec-msss', 'ontario-health', 'alberta-ahs', 'bc-phsa'
);
```

**Seeded via:** `migrations/004_seed_sources.sql`

### Scraper Status Table
Heartbeat tracking in `scraper_status`:

```sql
SELECT source_id, last_run, status, error_message
FROM scraper_status
ORDER BY last_run DESC;
```

**Updated by:** Each scraper run (success or failure)
**Monitored by:** `heartbeat-monitor.yml` workflow

---

## CLI Commands

### Run All Scrapers
```bash
cd backend
source .venv/bin/activate
python -m waittime.cli.scraper --all
```

### Run Single Scraper
```bash
python -m waittime.cli.scraper --source quebec-msss
```

### List Available Scrapers
```bash
python -m waittime.cli.scraper --list
```

### Check Heartbeat Health
```bash
python -m waittime.cli.check_heartbeat --max-age 60
```

### Dry Run (No Database Writes)
```bash
python -m waittime.cli.scraper --all --dry-run
```

---

## Alerting

### Pushover Configuration

**Secrets Required:**
- `PUSHOVER_USER_KEY` - Your Pushover user key
- `PUSHOVER_API_TOKEN` - Your Pushover API token

**Alert Types:**
1. **Scraper Failure** (scraper-cron.yml)
   - Title: 🚨 Scraper Failure
   - Trigger: Any scraper run exits with failure
   - Priority: 1 (High)

2. **Stale Heartbeat** (heartbeat-monitor.yml)
   - Title: ⚠️ Scraper Stale
   - Trigger: No heartbeat in last 60 minutes
   - Priority: 1 (High)

**Manual Alert Test:**
```bash
python -m waittime.cli.check_heartbeat --max-age 1 --dry-run
```

---

## Monitoring Dashboard

### GitHub Actions
View workflow runs: [Actions Tab](https://github.com/yourusername/waittimecanada/actions)

### Key Metrics
- **Scraper Success Rate:** Check `scraper-cron` workflow runs
- **Data Freshness:** Query `MAX(timestamp_utc)` from `measurements` per source
- **Error Rate:** Count failures in `scraper_status` table

### SQL Queries

**Data Freshness per Province:**
```sql
SELECT
  s.id,
  s.province,
  MAX(m.timestamp_utc) AS last_measurement,
  EXTRACT(EPOCH FROM (NOW() - MAX(m.timestamp_utc)))/60 AS minutes_ago
FROM sources s
LEFT JOIN measurements m ON m.source_id = s.id
WHERE s.id IN ('quebec-msss', 'ontario-health', 'alberta-ahs', 'bc-phsa')
GROUP BY s.id, s.province
ORDER BY minutes_ago ASC;
```

**Measurements per Source (Last 24h):**
```sql
SELECT
  source_id,
  COUNT(*) as measurement_count,
  COUNT(DISTINCT hospital_id) as hospital_count
FROM measurements
WHERE timestamp_utc > NOW() - INTERVAL '24 hours'
GROUP BY source_id
ORDER BY source_id;
```

---

## Troubleshooting

### Scraper Failing in GitHub Actions

1. **Check Workflow Logs:**
   - Go to Actions → Scraper Cron Job → Latest Run
   - Review step-by-step output

2. **Common Issues:**
   - **Database Connection:** Verify `DATABASE_URL` secret is set
   - **Playwright Timeout:** Ontario/Alberta scrapers may timeout if page loads slowly
   - **HTML Structure Changed:** Provincial websites may update their HTML

3. **Test Locally:**
   ```bash
   export DATABASE_URL="your_connection_string"
   python -m waittime.cli.scraper --source <source-id>
   ```

### No Heartbeat Alert

1. **Check scraper_status Table:**
   ```sql
   SELECT * FROM scraper_status WHERE source_id = '<source-id>' ORDER BY last_run DESC LIMIT 5;
   ```

2. **Verify Source Exists:**
   ```sql
   SELECT * FROM sources WHERE id = '<source-id>';
   ```

3. **Check GitHub Actions Runs:**
   - Ensure scraper-cron is actually running every 15 minutes
   - Check for workflow errors

### Low Measurement Count

1. **Verify Hospital Visibility:**
   ```sql
   SELECT COUNT(*)
   FROM hospitals
   WHERE source_id = '<source-id>'
     AND is_visible = true
     AND is_verified = true;
   ```

2. **Check Recent Errors:**
   ```sql
   SELECT * FROM scraper_status
   WHERE source_id = '<source-id>'
     AND error_message IS NOT NULL;
   ```

---

## Deployment Checklist

When adding a new scraper:

- [ ] Implement scraper class extending `BaseScraper`
- [ ] Add to `SCRAPERS` registry in `scraper.py`
- [ ] Create source factory function
- [ ] Add source to `migrations/004_seed_sources.sql`
- [ ] Run migration or insert source manually
- [ ] Write unit tests (minimum 10 tests)
- [ ] Document methodology in `docs/methodologies/`
- [ ] Seed hospital data in `backend/seed_data/hospitals/<province>.json`
- [ ] Test locally with `--dry-run`
- [ ] Verify in GitHub Actions (manual trigger)
- [ ] Monitor heartbeat for 24 hours

---

## Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Scraper Run Frequency | Every 15 min | ✅ Configured |
| Max Scraper Runtime | < 15 min | ✅ ~8-12 min |
| Heartbeat Check Frequency | Every 30 min | ✅ Configured |
| Max Heartbeat Age | < 60 min | ✅ Monitored |
| Scraper Success Rate | > 95% | ✅ Tolerant design |
| Data Freshness | < 30 min | ✅ 15 min cadence |

---

## Cost Analysis

### GitHub Actions Minutes
- **Scraper Cron:** 12 min × 96 runs/day = 1,152 min/day = ~34,560 min/month
- **Heartbeat Monitor:** 2 min × 48 runs/day = 96 min/day = ~2,880 min/month
- **Total:** ~37,440 min/month

**Free Tier:** 2,000 minutes/month
**Status:** ⚠️ Exceeds free tier by ~35,440 minutes/month

**Cost Estimate:** $0.008/min × 35,440 = ~$283.52/month

**Optimization Options:**
1. Reduce scraper frequency to 30 minutes (save 50%)
2. Use self-hosted runner (free, but requires infrastructure)
3. Optimize scraper runtime (currently ~10 min average)

---

## Future Enhancements

### Planned
- [ ] Add Nova Scotia scraper
- [ ] Add New Brunswick scraper
- [ ] Implement smart scheduling (skip night hours for some provinces)
- [ ] Add Prometheus/Grafana monitoring
- [ ] Implement scraper performance metrics dashboard

### Deferred
- Manitoba scraper (data source unclear)
- Saskatchewan scraper (no public data available)

---

## References

- [Scraper CLI Documentation](../../backend/src/waittime/cli/scraper.py)
- [Heartbeat Monitor CLI](../../backend/src/waittime/cli/check_heartbeat.py)
- [GitHub Actions Workflows](../../.github/workflows/)
- [Provincial Methodologies](../methodologies/)
