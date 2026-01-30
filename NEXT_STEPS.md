# Next Steps: Ontario-First Strategy

**Last Updated:** 2026-01-30
**Current Phase:** Week 1 Complete → Week 2 Starting
**Focus:** Ontario scraper end-to-end

---

## ✅ What's Done

- [x] Repository modernized (proper Python package structure)
- [x] Database schema on Neon PostgreSQL
- [x] Core models with metric ontology
- [x] BaseScraper abstract class
- [x] Quebec scraper MVP (24 tests passing)
- [x] CLI tool for running scrapers
- [x] Documentation structure

---

## 🎯 Immediate Priority: Ontario Scraper

**Goal:** Get ONE province working end-to-end before expanding.

### Step 1: Research Ontario Data Source (1-2 hours)

**Tasks:**
- [ ] Find actual Ontario health portal URL for ED wait times
  - Try: https://www.ontariohealth.ca/our-work/programs/ontario-wait-times
  - Try: https://health.gov.on.ca/en/pro/programs/waittimes/
- [ ] Inspect HTML structure (view source, find tables/JSON)
- [ ] Document methodology (start_event, end_event, statistic_type)
- [ ] List 5-10 target hospitals (Ottawa + Toronto)

**Acceptance:** Can load URL in browser and see wait time data

---

### Step 2: Build Ontario Scraper (4-6 hours)

**Tasks:**
- [ ] Create `backend/src/waittime/scrapers/ontario.py`
- [ ] Copy structure from `quebec.py` (reuse patterns)
- [ ] Update `HOSPITAL_MAPPING` with Ontario hospitals:
  ```python
  HOSPITAL_MAPPING = {
      "Ottawa Hospital - Civic": "ca-on-ottawa-civic",
      "Ottawa Hospital - General": "ca-on-ottawa-general",
      "Queensway Carleton": "ca-on-queensway-carleton",
      "Toronto General": "ca-on-toronto-general",
      # ... etc
  }
  ```
- [ ] Implement parsing strategy (table/JSON/card)
- [ ] Tag with Ontario methodology (likely TRIAGE→PHYSICIAN, P90)
- [ ] Add to `backend/src/waittime/scrapers/__init__.py`
- [ ] Update CLI registry in `cli/scraper.py`

**Acceptance:** `python -m waittime.cli.scraper --source ontario-health --dry-run` shows parsed hospitals

---

### Step 3: Test Ontario Scraper (2-3 hours)

**Tasks:**
- [ ] Create `backend/tests/unit/test_ontario_scraper.py`
- [ ] Test wait time extraction
- [ ] Test hospital ID normalization
- [ ] Test parsing strategy
- [ ] Test ontology tagging
- [ ] Aim for >80% coverage
- [ ] Run: `pytest tests/unit/test_ontario_scraper.py -v`

**Acceptance:** All tests passing

---

### Step 4: Database Integration (1-2 hours)

**Tasks:**
- [ ] Update `sources` seed data if Ontario methodology differs
- [ ] Run scraper for real: `python -m waittime.cli.scraper --source ontario-health`
- [ ] Verify measurements write to database
- [ ] Check heartbeat updates
- [ ] Query database to see results:
  ```python
  from waittime.services import DatabaseService
  db = DatabaseService()
  measurements = db.list_measurements(province='ON')
  print(f"Found {len(measurements)} Ontario measurements")
  ```

**Acceptance:** Data flowing from Ontario scraper → Neon database

---

### Step 5: Frontend Basics (1 day)

**Tasks:**
- [ ] Initialize Next.js 14 project in `frontend/`
- [ ] Set up Mapbox GL
- [ ] Display map centered on Ontario
- [ ] Query Neon for Ontario hospitals
- [ ] Display hospitals as markers
- [ ] Click marker → show wait time + methodology tags

**Acceptance:** Can see Ontario hospitals on map with live data

---

### Step 6: GitHub Actions (2-3 hours)

**Tasks:**
- [ ] Update `.github/workflows/scraper-cron.yml`
- [ ] Set to run only `ontario-health` scraper (not all)
- [ ] Configure Neon `DATABASE_URL` secret in GitHub
- [ ] Test workflow manually
- [ ] Enable cron schedule (every 15 minutes)

**Acceptance:** Ontario scraper runs automatically, heartbeat shows "healthy"

---

### Step 7: Monitor & Stabilize (3-7 days)

**Tasks:**
- [ ] Watch GitHub Actions logs for errors
- [ ] Check heartbeat every day
- [ ] Verify data quality (no outliers, no silent failures)
- [ ] Fix any bugs that appear
- [ ] Document any quirks in Ontario scraper

**Acceptance:** 7 days of stable operation (>95% success rate)

---

## 🔄 After Ontario is Stable

**Only then** expand to Quebec:
1. Fix Quebec scraper URL (find real health portal)
2. Test Quebec scraper with real data
3. Add Quebec to frontend map
4. Enable Quebec in GitHub Actions

**Criteria for expansion:**
- Ontario scraper: 7 days stable operation
- Frontend: Ontario hospitals displaying correctly
- No critical bugs or silent failures

See [docs/planning/expansion-roadmap.md](docs/planning/expansion-roadmap.md) for full provincial expansion strategy.

---

## 📊 Success Metrics

**Week 2 Goal:**
- [ ] Ontario scraper running every 15 min
- [ ] 5+ Ottawa hospitals showing data
- [ ] Frontend displays live Ontario wait times
- [ ] No silent failures

**When these are met**, we're ready for Quebec.

---

## 🚫 What NOT to Do

- ❌ Don't build all 5 scrapers at once
- ❌ Don't start frontend until Ontario scraper works
- ❌ Don't enable cron for untested scrapers
- ❌ Don't expand to new province until current one is stable

**Philosophy:** One province, end-to-end, working reliably. Then expand.

---

## 📝 Notes

If Ontario health portal doesn't exist or is paywalled:
- **Fallback:** Start with Quebec (already built) and find real URL
- **Alternative:** Use mock data to build frontend, then add real scrapers

Priority order:
1. Get ANY province working end-to-end
2. Perfect that one province
3. Add second province
4. Repeat
