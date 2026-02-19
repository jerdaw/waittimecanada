# ADR-0007: BC Scraper Implementation

**Date:** 2026-02-06
**Status:** Accepted
**Context:** Multi-province expansion

---

## Context

Wait Time Canada initially supported Ontario and Quebec. To demonstrate national scalability and provide Western Canada coverage, we need to add British Columbia emergency department wait time data.

**Data Source:** BC Provincial Health Services Authority (PHSA)
**URL:** https://edwaittimes.ca

---

## Decision

Implement BC scraper using HTML parsing of Next.js SSG embedded JSON data rather than Playwright-based dynamic scraping.

### Implementation Approach

**1. Data Extraction Method:**
- Parse `__NEXT_DATA__` JSON embedded in `/legacy` route HTML
- No browser automation required (simpler, faster, more reliable)
- Extract from `props.pageProps.locationsWithWaitTimes` array

**2. Metric Ontology:**
```python
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE (after triage nurse assessment)
end_event: PHYSICIAN (doctor or nurse practitioner)
statistic_type: P90 (90th percentile - "9 out of 10 patients")
patient_scope: ALL
```

**3. Hospital Coverage:**
- Vancouver Coastal Health (VCH): 9 facilities
- Fraser Health (FH): 11 facilities
- Total: 20+ emergency departments
- Geographic focus: Metro Vancouver + Fraser Valley

**4. Update Frequency:**
- Source updates every 5 minutes (automated)
- Recommend scraper frequency: 15 minutes (respectful rate limiting)

**5. Comparability:**
- ✅ **Comparable to Ontario:** Both use TRIAGE→PHYSICIAN, P90
- ❌ **NOT comparable to Quebec:** Different start event (REGISTRATION) and statistic (mean)

---

## Consequences

### Positive

1. **Simple Implementation:** No Playwright dependency, reduces complexity
2. **Reliable Scraping:** Static JSON is more stable than dynamic DOM
3. **Western Canada Coverage:** First province west of Ontario
4. **Methodology Transparency:** BC provides clear methodology documentation
5. **Real-time Data:** 5-minute update frequency (best of all provinces)

### Negative

1. **Limited Geographic Coverage:**
   - Only Metro Vancouver and Fraser Valley
   - No Interior Health (Kelowna, Kamloops)
   - No Island Health (Victoria, Nanaimo - they have separate system)
   - No Northern Health (Prince George, Fort St. John)

2. **Data Structure Dependency:**
   - Relies on Next.js `__NEXT_DATA__` JSON structure
   - Could break if BC migrates away from Next.js or changes page structure
   - Requires monitoring for breaking changes

3. **Hospital ID Mapping:**
   - Some hospitals not in initial mapping (auto-generation fallback)
   - Requires manual verification of new facilities
   - Surrey Memorial has separate Adult/Pediatrics entries

### Technical Debt

- **Hospital Verification:** 20+ BC hospitals need manual admin approval before appearing on site
- **Monitoring:** Add BC scraper to heartbeat monitoring
- **Testing:** Integration tests with live site are slow (marked @slow)

---

## Alternatives Considered

### Alternative 1: Playwright-Based Dynamic Scraping

**Approach:** Use Playwright to render JavaScript and extract data from DOM

**Pros:**
- Would work if data was only available via client-side rendering
- More resilient to JSON structure changes

**Cons:**
- Significantly slower (3-5x slower than HTML parsing)
- Requires Playwright installation and browser binaries
- Higher resource usage (memory, CPU)
- More failure modes (timeouts, browser crashes)

**Decision:** Rejected - JSON parsing is sufficient and simpler

### Alternative 2: Reverse Engineer BC API

**Approach:** Find and use undocumented API endpoints

**Pros:**
- Most efficient data access
- JSON response is structured
- Fastest scraping method

**Cons:**
- No documented public API exists
- API endpoints may be intentionally private
- Could break without notice
- Ethically questionable (using undocumented APIs)

**Decision:** Rejected - HTML parsing is official and documented

### Alternative 3: Wait for Official API

**Approach:** Contact BC PHSA and request official API access

**Pros:**
- Officially supported integration
- Guaranteed stability
- Could include additional data

**Cons:**
- Unknown timeline (could be months/years)
- May require formal partnership agreement
- Delays Western Canada coverage

**Decision:** Rejected - Current approach works now, can migrate if API becomes available

---

## Implementation Details

### Scraper Architecture

```python
class BCScraper(BaseScraper):
    BASE_URL = "https://edwaittimes.ca/legacy"

    def fetch(self) -> str:
        # Simple HTTP GET, no browser needed
        return requests.get(self.BASE_URL).text

    def parse(self, html: str) -> list[Measurement]:
        # Extract __NEXT_DATA__ JSON
        soup = BeautifulSoup(html, "html.parser")
        next_data = json.loads(soup.find("script", id="__NEXT_DATA__").string)

        # Extract locations
        locations = next_data["props"]["pageProps"]["locationsWithWaitTimes"]

        # Filter to ED type only (exclude UPCCs)
        # Create measurements with P90 ontology
        ...
```

### Hospital ID Mapping

**Strategy:** Maintain explicit mapping with auto-generation fallback

```python
HOSPITAL_MAPPING = {
    "Vancouver General Hospital": "ca-bc-vgh",
    "St. Paul's Hospital": "ca-bc-st-pauls",
    # ... 20+ hospitals
}

# Fallback for unmapped hospitals
if not hospital_id:
    slug = generate_slug(name)  # "New Hospital" → "new-hospital"
    hospital_id = f"ca-bc-{slug}"
    log.warning(f"Auto-generated ID: {hospital_id}")
```

### Error Handling

- **Missing JSON:** Log error, return empty list
- **Invalid Structure:** Gracefully handle KeyError
- **No Wait Time:** Skip location (closed hospitals)
- **Network Failure:** Retry with exponential backoff (inherited from BaseScraper)

---

## Testing Strategy

### Unit Tests (12 tests, 85% coverage)

```python
# Test fixtures with sample __NEXT_DATA__ JSON
def test_parse_extracts_ed_locations()  # Filters ED vs UPCC
def test_parse_creates_correct_measurements()  # Validates ontology
def test_parse_handles_unmapped_hospital()  # Auto-generation
def test_parse_handles_missing_next_data()  # Error handling
def test_measurement_has_correct_ontology()  # P90, TRIAGE→PHYSICIAN
```

### Integration Tests

```python
@pytest.mark.slow
@pytest.mark.integration
def test_bc_scraper_live():
    """Test against actual BC PHSA website."""
    scraper = BCScraper(create_bc_source())
    html = scraper.fetch()
    measurements = scraper.parse(html)

    assert len(measurements) > 0
    assert all(m.statistic_type == StatisticType.P90 for m in measurements)
```

### Manual Testing Checklist

- [ ] Scraper runs via CLI: `python -m waittime.cli.scraper bc`
- [ ] Measurements stored in database
- [ ] BC hospitals auto-approved and visible on map
- [ ] Province filter includes "British Columbia" option
- [ ] Methodology page shows BC comparability

---

## Deployment Plan

### Phase 1: Initial Deployment

1. **Seed BC Source:** Run `seed_sources.py` to add bc-phsa to database
2. **Manual Test:** Run scraper locally, verify measurements
3. **Verify Hospitals:** Confirm BC hospitals are auto-approved from trusted source
4. **Deploy Frontend:** Province filter with BC option
5. **Monitor:** Check heartbeat API for BC scraper health

### Phase 2: Automation

1. **Add to GitHub Actions:** Schedule BC scraper every 15 minutes
2. **Alerting:** Configure heartbeat monitoring (>60 min = alert)
3. **Metrics:** Track BC measurement counts via dashboard

### Phase 3: Documentation

1. **Update /methods Page:** Add BC methodology card
2. **Update Comparability Matrix:** Show BC ↔ ON/QC compatibility
3. **Add to README:** Update province count, BC coverage

---

## Monitoring & Maintenance

### Key Metrics

- **Measurement Count:** Expect 15-20 measurements per scraper run
- **Failure Rate:** Should be <1% (BC site is stable)
- **Data Freshness:** Max age should be <20 minutes
- **Hospital Coverage:** Track when new hospitals appear

### Breaking Change Detection

**Symptoms:**
- Zero measurements returned
- JSON parsing errors in logs
- Missing `__NEXT_DATA__` script tag

**Response:**
1. Check if BC migrated to new framework
2. Inspect live site HTML structure
3. Update scraper if structure changed
4. Fall back to manual monitoring if unfixable

### Maintenance Tasks

- **Quarterly:** Review BC methodology page for updates
- **When New Hospitals Added:** Update HOSPITAL_MAPPING
- **After BC Site Redesign:** Re-validate scraper functionality

---

## Related Documents

- **Methodology:** `/backend/docs/methodologies/bc-methodology.md` (582 lines)
- **Scraper Code:** `/backend/src/waittime/scrapers/bc.py`
- **Tests:** `/backend/tests/unit/test_bc_scraper.py`
- **Frontend:** `/frontend/components/ProvinceFilter.tsx`

---

## Revision History

| Date | Change | Rationale |
|------|--------|-----------|
| 2026-02-06 | Initial ADR | BC scraper implementation complete |

---

## Approval

**Author:** Development Team
**Reviewers:** N/A (Educational/Portfolio Project)
**Status:** Accepted and Implemented
