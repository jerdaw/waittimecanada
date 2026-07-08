# Ontario Research Findings

**Date:** 2026-01-30
**Phase:** 0 - Research & Discovery
**Researcher:** Implementation of M2 Plan v1.0.0

> Implementation note (2026-07-08): the production Ontario scraper no longer uses Playwright. The current runtime fetches the Ontario Health reporting page directly over HTTP, follows the former HQOntario redirect chain, and parses the embedded HTML tables because the needed table content is available server-side.

---

## Data Source Options

### Option 1: Ontario Health (Official - Recommended)

**URL:** https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments

**Pros:**
- ✅ Official government source (Ontario Health)
- ✅ 100+ Ontario hospitals covered
- ✅ Data visible in HTML table
- ✅ Authoritative, trustworthy
- ✅ Clear methodology documentation

**Cons:**
- ⚠️ Upstream response latency can be intermittent
- ⚠️ Paginated/filtered interface
- ⚠️ Average wait times (not real-time)

**Technical Requirements:**
- Direct HTTP fetch of the Ontario Health reporting page
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
- Redirects to Ontario Health for actual data
- No scrapeable content

---

## Recommendation

### Primary: Ontario Health (Official Source)

**Rationale:**
1. **Authoritative** - Official government data
2. **Reliable** - Won't disappear like third-party sites
3. **Project value** - Using official sources shows professionalism
4. **Methodology clear** - Well-documented for ontology tagging

**Implementation Strategy:**
1. Fetch the Ontario Health reporting page directly over HTTP
2. Parse the hospital comparison table
3. Extract hospital rows
4. Parse wait times (convert hours → minutes)

**Sample Hospitals (from Ontario Health):**
- The Ottawa Hospital - Civic Campus
- The Ottawa Hospital - General Campus
- Queensway Carleton Hospital
- Montfort Hospital
- Toronto General Hospital
- Mount Sinai Hospital
- Sunnybrook Health Sciences Centre

---

## Methodology Documentation

Based on the Health Quality Ontario methodology page:

**Metric Family:** `TIME_TO_PROVIDER`
- Measures wait time until first assessment by doctor

**Start Event:** `TRIAGE`
- Clock starts after triage assessment
- Per CIHI NACRS definition

**End Event:** `PHYSICIAN`
- Clock stops at first physician assessment
- Not NP/PA - must be MD

**Statistic Type:** `MEAN`
- "Average (Hours)" per Ontario Health reporting
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

### Chosen: Direct HTTP fetch with HTML parsing

**Why direct HTTP over a browser runtime:**
- Simpler operationally
- Lower runtime overhead
- No browser dependency for the Ontario scraper path
- Works because the needed comparison table is present in the fetched HTML

**Implementation Pattern:**
```python
response = client.get(
    "https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments",
    follow_redirects=True,
)
response.raise_for_status()
html = response.text
# Parse with BeautifulSoup
```

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Ontario Health changes HTML structure | Medium | High | Version parser, add structure detection |
| Upstream read timeouts | Medium | Medium | Retry with an extended HTTP read timeout before surfacing failure |
| Data not updated regularly | Low | Low | Check timestamps, alert if stale |
| Hospital names don't match mapping | High | Low | Fuzzy matching (already have from Quebec) |

---

## Sources

- [Ontario Government - Emergency Department Wait Times](https://www.ontario.ca/page/time-spent-emergency-department)
- [Ontario Health - Time Spent in Emergency Departments](https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments)

- [Hamilton Emergency Wait Times](https://www.hamiltonemergencywaittimes.ca/)
- [Niagara Health - Emergency Department Wait Times](https://www.niagarahealth.on.ca/site/waiting-times)
- [CIHI - NACRS Emergency Department Visits](https://www.cihi.ca/en/nacrs-emergency-department-visits-and-lengths-of-stay)

---

## Next Steps (Phase 1)

1. Create `ontario.py` scraper
2. Implement Ontario Health HTML table parsing over HTTP
3. Add hospital ID normalization
4. Test with dry-run mode

Historical note: these Phase 1 steps are preserved for discovery context; the scraper is now implemented and live.
