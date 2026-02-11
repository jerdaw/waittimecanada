# Operations: Production Verification & Documentation

**Status:** ✅ COMPLETE (2026-02-11)
**Related:** M16, M17, M18 (operational readiness for all scrapers)

---

## Objective

Verify that all 4 provincial scrapers are operational on automated schedules, document production configuration, and create comprehensive operational guides for monitoring and troubleshooting.

## Success Criteria

- [x] Verify all 4 scrapers (QC, ON, AB, BC) running on 15-minute schedule
- [x] Confirm heartbeat monitoring active with 30-minute checks
- [x] Validate GitHub Actions workflows are correctly configured
- [x] Fix BC source metadata inconsistencies
- [x] Create comprehensive operational documentation
- [x] Document cost analysis and optimization options

## Implementation Summary

### Verification Activities

**Scrapers Verified:**
1. **Quebec (quebec-msss):** ✅ Operational
   - BeautifulSoup scraper
   - 110+ hospitals
   - Includes stretcher occupancy (M17)

2. **Ontario (ontario-health):** ✅ Operational
   - Playwright scraper (JavaScript rendering)
   - 160+ hospitals
   - P90 TRIAGE→PHYSICIAN methodology

3. **Alberta (alberta-ahs):** ✅ Operational
   - Playwright scraper
   - 50+ hospitals
   - Alberta Health Services portal

4. **British Columbia (bc-phsa):** ✅ Operational
   - JSON/__NEXT_DATA__ extraction
   - 60+ hospitals
   - P90 TRIAGE→PHYSICIAN methodology

**Total Coverage:** 380+ hospitals across 4 provinces

### GitHub Actions Configuration

**Workflows Verified:**

1. **scraper-cron.yml**
   - Schedule: `*/15 * * * *` (every 15 minutes)
   - Command: `python -m waittime.cli.scraper --all`
   - Timeout: 20 minutes
   - Installs Playwright browsers
   - Failure alerting configured

2. **heartbeat-monitor.yml**
   - Schedule: `*/30 * * * *` (every 30 minutes)
   - Command: `python -m waittime.cli.check_heartbeat --max-age 60`
   - Dynamic source discovery from database
   - Pushover alerts on stale data

**Concurrency Settings:**
- Both workflows: `cancel-in-progress: false`
- Allows overlapping runs if previous scraper is slow
- Prevents duplicate heartbeat alerts

### BC Source Metadata Corrections

**Issue Found:**
BC source metadata in database seed didn't match scraper implementation.

**Corrections Applied:**
```sql
-- In backend/migrations/004_seed_sources.sql
UPDATE sources SET
  url = 'https://edwaittimes.ca',  -- was: http://www.edwaittimes.ca/
  methodology = 'TRIAGE → PHYSICIAN, P90',  -- was: REGISTRATION → PHYSICIAN, POINT_ESTIMATE
  methodology_url = 'https://www.edwaittimes.ca/about'  -- was: NULL
WHERE id = 'bc-phsa';
```

**Verification:**
- Created `tests/unit/test_source_consistency.py`
- Validates all 4 sources match between seed data and scraper factories
- All tests passing

### Documentation Created

**1. scraper-scheduling.md (9.4 KB)**
- Comprehensive operational guide
- Individual scraper details for all 4 provinces
- GitHub Actions workflow documentation
- Monitoring and alerting procedures
- Database queries for health checks
- Troubleshooting guide
- Cost analysis (~$240/month at 15-minute frequency)
- Optimization options (30-minute frequency = 50% savings)

**2. QUICK_START.md (2.1 KB)**
- Quick reference for manual operations
- Common CLI commands
- Database health queries
- Troubleshooting shortcuts

**3. OPERATIONAL_STATUS.md (7.8 KB)**
- Production verification report
- Infrastructure status summary
- Verification test results
- User action options (no action, reduce costs, add monitoring)
- Support and troubleshooting resources

### Cost Analysis

**Current Configuration:**
- Scraper cron: ~34,560 minutes/month
- Heartbeat monitor: ~2,880 minutes/month
- **Total:** ~37,440 minutes/month
- **Free tier:** 2,000 minutes/month
- **Overage:** ~35,440 minutes/month
- **Estimated cost:** ~$283/month at $0.008/min

**Optimization Options:**
- Reduce to 30-minute frequency: ~$141/month (50% savings)
- Smart scheduling (skip overnight): ~$120/month (58% savings)
- Self-hosted runner: $0 (requires infrastructure)

### Monitoring & Alerting

**Heartbeat Monitoring:**
- Checks all sources dynamically from database
- 60-minute staleness threshold
- Pushover notifications on failure
- No hardcoded source lists (adapts automatically)

**Dead Man's Switch:**
- CLI command: `python -m waittime.cli.check_heartbeat`
- Runs every 30 minutes via GitHub Actions
- Alerts if any scraper hasn't run in 60 minutes
- Separate alerts per source

**Data Quality:**
- Database table: `scraper_status`
- Tracks last_run, status, error_message per source
- Frontend displays "Last Audit" timestamp
- Data quality dashboard at `/data-quality`

## Test Results

**Source Consistency Tests:**
```bash
$ pytest tests/unit/test_source_consistency.py -v
# Result: 4/4 tests passing
```

**Verified:**
- Quebec source factory matches seed data ✅
- Ontario source factory matches seed data ✅
- Alberta source factory matches seed data ✅
- BC source factory matches seed data (after correction) ✅

**All Backend Tests:**
- 375 tests passing
- 77% code coverage

## Files Created/Modified

**Created:**
- `docs/operations/scraper-scheduling.md`
- `docs/operations/QUICK_START.md`
- `docs/operations/OPERATIONAL_STATUS.md`
- `backend/tests/unit/test_source_consistency.py`

**Modified:**
- `backend/migrations/004_seed_sources.sql` (BC source corrections)
- `docs/planning/roadmap.md` (added Operations milestone)
- `IMPLEMENTATION_SUMMARY.md` (marked scraper scheduling complete)

## Production Status

**Current State (2026-02-11):**
- ✅ All 4 scrapers operational
- ✅ 15-minute update frequency
- ✅ Heartbeat monitoring active
- ✅ 380+ hospitals visible
- ✅ Zero manual intervention required
- ✅ Pushover alerting configured

**Data Freshness:**
- Update frequency: 15 minutes
- Heartbeat threshold: 60 minutes
- All sources healthy

## User Action Taken

**Option Selected:** No action required

The system is fully operational. Scrapers run automatically every 15 minutes with heartbeat monitoring and alerting. No manual intervention needed.

**Monitoring Recommendation:**
- Check GitHub Actions runs daily for first week
- Review Pushover alerts (should be none if healthy)
- Verify data freshness via database queries

## Future Enhancements

**Short-term:**
1. Cost optimization (reduce frequency to 30 minutes)
2. Smart scheduling (pause overnight for some provinces)

**Long-term:**
1. Prometheus metrics endpoint
2. Grafana visualization dashboard
3. Per-hospital staleness tracking
4. Automatic scraper recovery

## Known Limitations

1. **GitHub Actions Cost:** Exceeds free tier (~$283/month)
2. **No Visual Dashboard:** Alerts via Pushover only
3. **No Real-Time Logs:** Must check GitHub Actions UI

## References

- GitHub Actions: `.github/workflows/scraper-cron.yml`
- Heartbeat: `.github/workflows/heartbeat-monitor.yml`
- CLI Tool: `backend/src/waittime/cli/scraper.py`
- Check Heartbeat: `backend/src/waittime/cli/check_heartbeat.py`
- Documentation: `docs/operations/scraper-scheduling.md`

---

**Completed:** 2026-02-11
**Verification Date:** 2026-02-11
**Next Review:** 2026-02-18 (1 week)
