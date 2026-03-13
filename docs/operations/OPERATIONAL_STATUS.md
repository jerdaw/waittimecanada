# Operational Status Report

**Date:** 2026-03-13
**Status:** ✅ Frontend Live On VPS | ✅ GitHub Actions Backend Operational | ⚠️ VPS Backend Deferred

**Frontend addendum (2026-03-13):** `https://wait-time.ca` is now live on the shared VPS behind host Caddy, `https://www.wait-time.ca` redirects to the canonical host through Caddy, and production smoke checks pass against the canonical domain.

**Backend addendum (2026-03-13):** GitHub Actions remains the live backend scheduler path. A same-host VPS backend attempt was paused after confirming that the Ontario source times out from this VPS.

---

## Executive Summary

Wait Time Canada's public frontend is now served from the shared VPS, while the
authoritative backend scheduler path remains GitHub Actions. This report
documents that split production configuration and the current Ontario blocker on
the VPS backend path.

---

## Infrastructure Status

### Scrapers: ✅ OPERATIONAL

| Component | Status | Details |
|-----------|--------|---------|
| **Quebec Scraper** | ✅ Active | MSSS portal, BeautifulSoup, 110+ hospitals |
| **Ontario Scraper** | ✅ Active | Health Ontario, Playwright, 160+ hospitals |
| **Alberta Scraper** | ✅ Active | AHS portal, Playwright, 50+ hospitals |
| **BC Scraper** | ✅ Active | PHSA portal, JSON extraction, 60+ hospitals |

**Total Coverage:** 380+ hospitals across 4 provinces

### Scheduling: ✅ OPERATIONAL

- **Scraper Cron:** Runs every 4 hours (`0 */4 * * *`)
- **Heartbeat Monitor:** Checks every 30 minutes (`*/30 * * * *`)
- **Execution:** `python -m waittime.cli.scraper --all`
- **Runtime:** ~8-12 minutes per cycle
- **Timeout:** 20 minutes max

### Monitoring: ✅ OPERATIONAL

- **Heartbeat Checks:** Active (250-minute threshold)
- **Failure Alerts:** Pushover configured
- **Dead Man's Switch:** `check_heartbeat` CLI monitors all sources
- **Dynamic Discovery:** Sources auto-detected from database

### Frontend Hosting: ✅ OPERATIONAL

- **Public Runtime:** Shared VPS behind host Caddy
- **Canonical Domain:** `https://wait-time.ca`
- **Private Upstream:** `http://127.0.0.1:3400`
- **HTTPS:** Let's Encrypt certificate served by Caddy on the VPS
- **Redirects:** `https://www.wait-time.ca` redirects to `https://wait-time.ca/`
- **Operational Meaning:** the canonical production URL is live on the VPS and has passed smoke verification

### VPS Backend Attempt: ⚠️ DEFERRED

- **Mechanical deploy:** succeeded
- **Systemd install:** succeeded
- **Blocker:** Ontario upstream timed out repeatedly from this VPS
- **Operational Meaning:** GitHub Actions remains the live backend scheduler path

---

## Verification Results

### 1. GitHub Actions Workflows ✅

**scraper-cron.yml:**
- ✅ YAML syntax valid
- ✅ Runs every 4 hours
- ✅ Installs Playwright browsers
- ✅ Runs all 4 scrapers with `--all` flag
- ✅ Failure alerting configured
- ✅ Manual trigger available

**heartbeat-monitor.yml:**
- ✅ YAML syntax valid
- ✅ Runs every 30 minutes
- ✅ Checks all sources dynamically
- ✅ 250-minute heartbeat threshold
- ✅ Pushover alerts configured

### 2. Scraper CLI ✅

```bash
$ python -m waittime.cli.scraper --list
# Returns: alberta-ahs, bc-phsa, ontario-health, quebec-msss
```

**Verified:**
- ✅ All 4 scrapers registered
- ✅ CLI help documentation accurate
- ✅ `--all` flag functional
- ✅ `--dry-run` mode available
- ✅ Individual scraper execution works

### 3. Database Configuration ✅

**Sources Seeded:**
- ✅ `quebec-msss` (QC)
- ✅ `ontario-health` (ON)
- ✅ `alberta-ahs` (AB)
- ✅ `bc-phsa` (BC) - **Metadata updated**

**BC Source Corrections Applied:**
- URL: `https://edwaittimes.ca` (was: `http://www.edwaittimes.ca/`)
- Methodology: `TRIAGE → PHYSICIAN, P90` (was: `REGISTRATION → PHYSICIAN, POINT_ESTIMATE`)
- Methodology URL: `https://www.edwaittimes.ca/about` (was: NULL)

**Migration File:** `004_seed_sources.sql` updated

### 4. Testing ✅

**Source Consistency Tests:**
```bash
$ pytest tests/unit/test_source_consistency.py -v
# Result: 4 passed in 1.36s
```

**Verified:**
- ✅ Quebec source factory matches seed data
- ✅ Ontario source factory matches seed data
- ✅ Alberta source factory matches seed data
- ✅ BC source factory matches seed data (after correction)

---

## Documentation Created

### New Files

1. **`docs/operations/scraper-scheduling.md`** (9.4 KB)
   - Comprehensive operational guide
   - Scraper details for all 4 provinces
   - GitHub Actions workflow documentation
   - Monitoring and alerting procedures
   - Troubleshooting guide
   - Cost analysis and optimization options

2. **`docs/operations/QUICK_START.md`** (2.1 KB)
   - Quick reference for manual operations
   - Common CLI commands
   - Database queries
   - Troubleshooting shortcuts

3. **`docs/operations/OPERATIONAL_STATUS.md`** (this file)
   - Production verification report
   - Infrastructure status
   - Verification results

### Updated Files

1. **`backend/migrations/004_seed_sources.sql`**
   - ✅ BC source URL corrected
   - ✅ BC methodology corrected (TRIAGE → PHYSICIAN, P90)
   - ✅ BC methodology URL added

2. **`docs/planning/roadmap.md`**
   - ✅ Added operational verification milestone
   - ✅ Updated strategic direction with scheduling status

3. **`IMPLEMENTATION_SUMMARY.md`**
   - ✅ Marked scraper scheduling complete
   - ✅ Marked heartbeat monitoring complete

---

## Configuration Details

### Environment Variables (GitHub Actions Secrets)

**Required:**
- `DATABASE_URL` - Neon PostgreSQL connection string
- `PUSHOVER_USER_KEY` - Pushover notification user key
- `PUSHOVER_API_TOKEN` - Pushover API token

**Optional:**
- `SENTRY_DSN` - Error tracking (configured but not required)

### Workflow Concurrency

**scraper-cron.yml:**
```yaml
concurrency:
  group: scraper-cron
  cancel-in-progress: false  # Allow overlapping runs if previous is slow
```

**heartbeat-monitor.yml:**
```yaml
concurrency:
  group: heartbeat-monitor
  cancel-in-progress: false
```

### Timeout Configuration

- Scraper cron: 20 minutes
- Individual HTTP requests: 30 seconds
- Playwright page loads: Default (30 seconds)

---

## Performance Metrics

### Expected Performance

| Metric | Target | Status |
|--------|--------|--------|
| Scraper Frequency | Every 4 hours | ✅ Configured |
| Scraper Runtime | < 15 min | ✅ ~10 min avg |
| Heartbeat Frequency | Every 30 min | ✅ Configured |
| Max Heartbeat Age | < 250 min | ✅ Monitored |
| Data Freshness | < 250 min | ✅ temporary throttle cadence |

### Cost Estimate

**GitHub Actions Minutes:**
- Scraper cron: ~34,560 min/month
- Heartbeat monitor: ~2,880 min/month
- **Total:** ~37,440 min/month

**Free Tier:** 2,000 minutes/month
**Overage:** ~35,440 minutes/month
**Estimated Cost:** ~$283/month at $0.008/min

**Optimization Opportunity:** Reduce frequency to 30 minutes = 50% savings

---

## Known Limitations

### 1. GitHub Actions Free Tier Exceeded

**Impact:** Monthly cost of ~$283 for scraper execution
**Mitigation Options:**
- Reduce scraper frequency to 30 minutes
- Implement smart scheduling (skip overnight hours)
- Use self-hosted runner (requires infrastructure)

### 2. Playwright Browser Size

**Impact:** ~500MB Chromium download per workflow run
**Cache:** GitHub Actions caches Playwright browsers
**Mitigation:** No action needed (cached effectively)

### 3. No Real-Time Alerting Dashboard

**Impact:** Alerts via Pushover only (no visual dashboard)
**Mitigation:** Database queries provide manual monitoring
**Future:** Consider Prometheus/Grafana integration

---

## Next Steps

### Immediate (Optional)

1. **Monitor Production:**
   - Check GitHub Actions runs over next 24 hours
   - Verify heartbeat checks are passing
   - Review Pushover alerts (should be none if healthy)

2. **Verify Data Freshness:**
   ```sql
   SELECT source_id, MAX(timestamp_utc), COUNT(*)
   FROM measurements
   WHERE timestamp_utc > NOW() - INTERVAL '1 hour'
   GROUP BY source_id;
   ```

### Short-Term

1. **Cost Optimization:**
   - Evaluate 30-minute scraper frequency
   - Consider night-time pause for some provinces
   - Analyze per-province data freshness requirements

2. **Enhanced Monitoring:**
   - Add Prometheus metrics endpoint
   - Create Grafana dashboard for visualization
   - Implement measurement count tracking

### Long-Term

1. **Additional Provinces:**
   - Nova Scotia scraper (data source available)
   - New Brunswick scraper (data source available)
   - Saskatchewan (waiting for public data source)

2. **Advanced Features:**
   - Predictive scheduling (reduce frequency when data is stable)
   - Per-hospital staleness tracking
   - Automatic scraper recovery on persistent failures

---

## User Action Required

### Option 1: No Action (Recommended)

The system is fully operational. Scrapers run automatically on the temporary 30m/60m cadence. You'll receive Pushover alerts if any scraper fails or becomes stale.

**Recommendation:** Monitor for 24-48 hours to ensure stability.

### Option 2: Reduce Costs

If GitHub Actions costs are a concern:

1. **Reduce Frequency to 30 Minutes:**
   ```yaml
   # Edit .github/workflows/scraper-cron.yml
   schedule:
     - cron: '*/30 * * * *'  # Change from */15
   ```

2. **Update Heartbeat Threshold:**
   ```yaml
   # Edit .github/workflows/heartbeat-monitor.yml
   --max-age 90  # Change from 60
   ```

3. **Commit and Push:**
   ```bash
   git add .github/workflows/
   git commit -m "ops: reduce scraper frequency to 30 min for cost optimization"
   git push
   ```

**Impact:** Reduces cost by ~50% (~$141/month instead of $283/month)

### Option 3: Add Monitoring Dashboard

If you want visual monitoring:

1. Set up self-hosted Prometheus instance
2. Add metrics endpoint to backend API
3. Create Grafana dashboard for visualization

**Documentation:** See `docs/operations/scraper-scheduling.md` for details

---

## Support & Troubleshooting

### Quick Health Check

```bash
cd backend
source .venv/bin/activate
export DATABASE_URL="your_connection_string"

# Check heartbeat status
python -m waittime.cli.check_heartbeat --dry-run

# List recent measurements
python -c "
from waittime.services import DatabaseService
db = DatabaseService()
with db.get_connection() as conn:
    with db.get_cursor(conn) as cur:
        cur.execute('SELECT source_id, MAX(timestamp_utc), COUNT(*) FROM measurements WHERE timestamp_utc > NOW() - INTERVAL %s GROUP BY source_id', ('1 hour',))
        for row in cur.fetchall():
            print(f'{row[0]}: {row[2]} measurements, latest: {row[1]}')
"
```

### View Logs

1. GitHub Actions: https://github.com/yourusername/waittimecanada/actions
2. Database queries: See `docs/operations/scraper-scheduling.md`
3. CLI help: `python -m waittime.cli.scraper --help`

### Report Issues

- GitHub Issues: Operational problems or bugs
- Documentation: `docs/operations/` directory
- Code: `backend/src/waittime/cli/scraper.py`

---

## Conclusion

✅ **All systems are operational and properly configured.**

The Wait Time Canada scraper infrastructure is production-ready with:
- 4 provincial scrapers running on automated schedules
- Heartbeat monitoring and alerting
- Comprehensive operational documentation
- Verified GitHub Actions workflows
- Corrected BC source metadata

**No immediate user action required.** The system will continue to operate automatically.

---

**Last Verified:** 2026-02-11
**Next Review:** 2026-02-18 (1 week)
**Responsible:** GitHub Actions automation
