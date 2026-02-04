# Ontario Research Findings

**Date:** 2026-01-30
**Phase:** 0 - Research & Discovery
**Researcher:** Implementation of M2 Plan v1.0.0

---

## Data Source Options

### Option 1: HQOntario (Official - Recommended)

**URL:** https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments

**Pros:**
- ✅ Official government source (Health Quality Ontario)
- ✅ 100+ Ontario hospitals covered
- ✅ Data visible in HTML table
- ✅ Authoritative, trustworthy
- ✅ Clear methodology documentation

**Cons:**
- ⚠️ Dynamically loaded via JavaScript (requires headless browser)
- ⚠️ Paginated/filtered interface
- ⚠️ Average wait times (not real-time)

**Technical Requirements:**
- Selenium or Playwright for JavaScript rendering
- Wait for table to load
- Parse HTML table structure

**Data Structure:**
```html
<table>
  <tr>
    <td>Hospital Name</td>
    <td>Average (Hours)</td>
    <td>vs Ontario Average (2.0)</td>
  </tr>
  <!-- Example -->
  <tr>
    <td>South Bruce Grey Health Centre-Durham</td>
    <td>0.5</td>
    <td>Better than average</td>
  </tr>
</table>
```

---


### Option 3: Ontario.ca (Informational Only)

**URL:** https://www.ontario.ca/page/time-spent-emergency-department

**Status:** ❌ Not a data source
- Informational page only
- Redirects to HQOntario for actual data
- No scrapeable content

---

## Recommendation

### Primary: HQOntario (Official Source)

**Rationale:**
1. **Authoritative** - Official government data
2. **Reliable** - Won't disappear like third-party sites
3. **Portfolio value** - Using official sources shows professionalism
4. **Methodology clear** - Well-documented for ontology tagging

**Implementation Strategy:**
1. Use Playwright (already in dependencies from plan)
2. Navigate to HQOntario URL
3. Wait for table to render
4. Extract hospital rows
5. Parse wait times (convert hours → minutes)

**Sample Hospitals (from HQOntario):**
- The Ottawa Hospital - Civic Campus
- The Ottawa Hospital - General Campus
- Queensway Carleton Hospital
- Montfort Hospital
- Toronto General Hospital
- Mount Sinai Hospital
- Sunnybrook Health Sciences Centre

---

## Methodology Documentation

Based on HQOntario methodology page:

**Metric Family:** `TIME_TO_PROVIDER`
- Measures wait time until first assessment by doctor

**Start Event:** `TRIAGE`
- Clock starts after triage assessment
- Per CIHI NACRS definition

**End Event:** `PHYSICIAN`
- Clock stops at first physician assessment
- Not NP/PA - must be MD

**Statistic Type:** `MEAN`
- "Average (Hours)" per HQOntario
- NOT P90 (unlike Alberta)
- Important distinction for comparability

**Patient Scope:** `ALL`
- All patients regardless of CTAS level
- Includes 1-5 acuity levels

**Data Freshness:**
- Updated monthly (not real-time)
- Shows average over previous month

---

## Hospital Mapping (Top 10 Target)

### Ottawa Hospitals (5)
```python
{
    "The Ottawa Hospital - Civic Campus": "ca-on-ottawa-civic",
    "The Ottawa Hospital - General Campus": "ca-on-ottawa-general",
    "Queensway Carleton Hospital": "ca-on-queensway-carleton",
    "Montfort Hospital": "ca-on-montfort",
    "CHEO (Children's Hospital of Eastern Ontario)": "ca-on-cheo"
}
```

### Toronto Hospitals (5)
```python
{
    "Toronto General Hospital": "ca-on-toronto-general",
    "Mount Sinai Hospital": "ca-on-mount-sinai",
    "Sunnybrook Health Sciences Centre": "ca-on-sunnybrook",
    "St. Michael's Hospital": "ca-on-st-michaels",
    "The Hospital for Sick Children": "ca-on-sickkids"
}
```

---

## Technical Decision: Scraping Approach

### Chosen: Playwright with Python

**Why Playwright over Selenium:**
- Modern, faster, more reliable
- Better async support
- Easier to install (no driver management)
- Already have playwright-python in dependencies

**Implementation Pattern:**
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments")
    page.wait_for_selector("table")  # Wait for data to load
    html = page.content()
    # Parse with BeautifulSoup
    browser.close()
```

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| HQOntario changes HTML structure | Medium | High | Version parser, add structure detection |
| Playwright install issues | Low | Medium | Use fallback scraping method |
| Data not updated regularly | Low | Low | Check timestamps, alert if stale |
| Hospital names don't match mapping | High | Low | Fuzzy matching (already have from Quebec) |

---

## Sources

- [Ontario Government - Emergency Department Wait Times](https://www.ontario.ca/page/time-spent-emergency-department)
- [Health Quality Ontario - Time Spent in Emergency Departments](https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments)

- [Hamilton Emergency Wait Times](https://www.hamiltonemergencywaittimes.ca/)
- [Niagara Health - Emergency Department Wait Times](https://www.niagarahealth.on.ca/site/waiting-times)
- [CIHI - NACRS Emergency Department Visits](https://www.cihi.ca/en/nacrs-emergency-department-visits-and-lengths-of-stay)

---

## Next Steps (Phase 1)

1. Install Playwright: `pip install playwright && playwright install chromium`
2. Create `ontario.py` scraper
3. Implement HQOntario parsing with Playwright
4. Test with dry-run mode

**Estimated Time:** 6-8 hours (per plan)
