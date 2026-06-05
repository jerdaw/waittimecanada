# Provincial Expansion Roadmap

> [!NOTE]
> Historical planning snapshot. Use `docs/planning/roadmap.md` for current priorities and status.

## Philosophy: One Province at a Time

**Rationale:** Better to have ONE province working end-to-end (scraper → database → frontend → deployment) than FIVE provinces half-built.

**Success Criteria for Expansion:**
Before moving to the next province, the current province must have:
- ✅ Scraper with >80% test coverage
- ✅ Real data flowing to database
- ✅ Frontend displaying data on map
- ✅ GitHub Actions cron running successfully
- ✅ At least 3 hospitals verified and visible
- ✅ Documentation complete

---

## Phase 1: Ontario (Primary Target)

**Why Ontario First:**
1. **Largest population** - 15M people, most impact
2. **Best data availability** - Health Ontario publishes structured data
3. **Geographic proximity** - Ottawa-Gatineau comparison (vs Quebec)
4. **Project narrative** - "Started with home province"

**Target URL:**
- https://www.ontariohealth.ca/our-work/programs/ontario-wait-times
- Alternative: https://health.gov.on.ca/en/pro/programs/waittimes/

**Expected Methodology (per ADR-0002):**
- `metric_family`: TIME_TO_PROVIDER
- `start_event`: TRIAGE (most common in Ontario)
- `end_event`: PHYSICIAN
- `statistic_type`: P90 (CIHI standard)
- `patient_scope`: MID_ACUITY (CTAS 3-4)

**Key Hospitals to Target:**
1. Ottawa Hospital (Civic Campus)
2. Ottawa Hospital (General Campus)
3. The Ottawa Hospital (Riverside Campus)
4. CHEO (Children's Hospital)
5. Queensway Carleton Hospital
6. Montfort Hospital
7. Toronto General Hospital
8. Mount Sinai Hospital
9. Sunnybrook Health Sciences
10. Hospital for Sick Children (SickKids)

**Deliverables:**
- [ ] Ontario scraper (`backend/src/waittime/scrapers/ontario.py`)
- [ ] Hospital mappings for 10+ Ottawa/Toronto hospitals
- [ ] Unit tests with >80% coverage
- [ ] Integration test with live URL
- [ ] GitHub Actions workflow
- [ ] Frontend map centered on Ontario

**Timeline:** 2-3 weeks for complete end-to-end

---

## Phase 2: Quebec (Cross-Border Comparison)

**Why Quebec Second:**
1. **Ottawa-Gatineau comparison** - Demonstrates methodology divergence
2. **Bilingual support** - Showcases Info-Santé vs Health811 routing
3. **Methodology contrast** - Quebec uses REGISTRATION→PHYSICIAN (vs Ontario's TRIAGE→PHYSICIAN)

**Status:** Scraper MVP complete, needs real URL and verification

**Target Hospitals:**
1. CHUM (Montreal)
2. Jewish General Hospital
3. Hôpital de Gatineau
4. Hôpital de Hull

**Deliverables:**
- [x] Quebec scraper (already built)
- [ ] Find actual Quebec health portal URL
- [ ] Verify hospital mappings
- [ ] Add to frontend with methodology warning

**Timeline:** 1 week (scraper done, just needs integration)

---

## Phase 3: Alberta (CIHI Gold Standard)

**Why Alberta Third:**
1. **Best methodology** - Uses CIHI-recommended P90 + TRIAGE start
2. **Excellent data quality** - AHS publishes real-time estimates
3. **Strong documentation** - Methodology PDF available

**Target URL:** https://www.albertahealthservices.ca/waittimes/waittimes.aspx

**Expected Methodology:**
- `start_event`: TRIAGE
- `statistic_type`: P90
- Very comparable to Ontario

**Timeline:** 1 week

---

## Phase 4: Manitoba (Algorithmic Challenge)

**Why Manitoba Fourth:**
1. **Unique methodology** - Uses algorithmic estimates (not raw data)
2. **Demonstrates ontology value** - Shows why ALGORITHMIC can't be compared to P90

**Timeline:** 1 week

---

## Phase 5: British Columbia (Real-Time Data)

**Why BC Last:**
1. **Real-time estimates** - POINT_ESTIMATE statistic type
2. **Western representation** - Geographic diversity

**Timeline:** 1 week

---

## Expansion Checklist Template

Use this for each new province:

### Pre-Development
- [ ] Research provincial health authority data source
- [ ] Verify URL is accessible and not paywalled
- [ ] Document methodology (start_event, end_event, statistic_type)
- [ ] Identify 5-10 key hospitals to map
- [ ] Check for API vs HTML scraping

### Development
- [ ] Create `scrapers/{province}.py` inheriting from `BaseScraper`
- [ ] Add hospital ID mappings (`HOSPITAL_MAPPING` dict)
- [ ] Implement `parse()` method with multiple strategies
- [ ] Write unit tests (aim for >80% coverage)
- [ ] Test with dry-run mode
- [ ] Add integration test with real URL

### Database
- [ ] Seed source record in `sources` table
- [ ] Verify telehealth contact info is correct
- [ ] Test heartbeat monitoring
- [ ] Verify measurements write correctly

### Frontend
- [ ] Add province boundary to map
- [ ] Display hospitals as markers
- [ ] Show methodology tags in tooltips
- [ ] Add divergence warnings when comparing across provinces

### Deployment
- [ ] Add to GitHub Actions cron workflow
- [ ] Monitor first 24 hours for errors
- [ ] Verify heartbeat is updating
- [ ] Check no silent failures

### Documentation
- [ ] Update README with new province
- [ ] Add scraper to CLI `--list`
- [ ] Update expansion roadmap status

---

## Current Status (2026-01-30)

| Province | Scraper | Database | Frontend | GitHub Actions | Status |
|----------|---------|----------|----------|----------------|--------|
| Ontario  | ⏸️ Planned | ⏸️ Schema ready | ⏸️ Not started | ⏸️ Not configured | 🎯 **PRIMARY TARGET** |
| Quebec   | ✅ MVP complete | ✅ Source seeded | ⏸️ Not started | ⏸️ Not configured | 🔄 Needs real URL |
| Alberta  | ⏸️ Planned | ✅ Source seeded | ⏸️ Not started | ⏸️ Not configured | ⏳ Phase 3 |
| Manitoba | ⏸️ Planned | ✅ Source seeded | ⏸️ Not started | ⏸️ Not configured | ⏳ Phase 4 |
| BC       | ⏸️ Planned | ✅ Source seeded | ⏸️ Not started | ⏸️ Not configured | ⏳ Phase 5 |

---

## Decision: Focus on Ontario Now

**Action Items:**
1. Build Ontario scraper (reuse Quebec scraper patterns)
2. Test with real Ontario health portal
3. Verify data quality
4. Build basic frontend map showing Ontario hospitals
5. Deploy GitHub Actions cron for Ontario only
6. Monitor for 1 week

**Success Metric:**
- Ontario scraper runs successfully every 15 minutes for 7 days
- At least 5 Ottawa hospitals showing data
- Frontend displays live wait times

**Only then** expand to Quebec/other provinces.

---

## Notes

- **Don't build all scrapers at once** - Risk of none working well
- **Validate data quality early** - Better to catch issues with 1 province
- **User feedback loop** - Get feedback on Ontario before expanding
- **Project narrative** - "Started local, expanded methodically" is stronger than "tried to do everything"
