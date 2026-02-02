# Ontario Emergency Department Data Sources

> Research findings for real-time ED wait time data in Ontario.

## Primary Data Sources

### 1. ER Watch (Recommended for Scraping)

**URL:** https://www.er-watch.ca/

**Overview:**
- Third-party aggregator covering 140+ Ontario hospitals
- Updates every 15 minutes
- Free, accurate, always up-to-date

**Data Fields:**
| Field | Description |
|-------|-------------|
| `id` | Hospital identifier |
| `name` | Hospital name |
| `slug` | URL-friendly name |
| `region` | Ontario Health region |
| `street` | Street address |
| `city` | City name |
| `postal_code` | Postal code |
| `latitude` | Geographic coordinate |
| `longitude` | Geographic coordinate |
| `website` | Hospital website URL |
| `phone` | Contact phone number |
| `er_status` | "online" or "offline" |
| `estimated_wait_time` | Wait time in minutes |
| `patients_waiting` | Number of patients waiting |
| `patients_in_treatment` | Number currently being treated |
| `last_updated` | Timestamp of last update |

**Data Format:**
- HTML page with embedded JSON in React component props
- Organized by Ontario Health regions: Central, East, North East, etc.

**Technical Notes:**
- Requires JavaScript rendering (Playwright recommended)
- Data appears embedded in `HomePageClient` component
- No documented REST API, but JSON structure is consistent

---

### 2. Health Quality Ontario (HQO) - Official

**URL:** https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments

**Overview:**
- Official government data source
- Historical/aggregate data (not real-time)
- Quarterly updates

**Metrics Reported:**
- Wait time to first assessment by doctor (P90)
- Length of stay for low-urgency patients not admitted
- Length of stay for high-urgency patients not admitted

**Limitations:**
- Not real-time (monthly aggregates)
- Suitable for methodology documentation, not live scraping

---

### 3. Ontario.ca Wait Times

**URL:** https://www.ontario.ca/page/time-spent-emergency-department

**Overview:**
- Government portal linking to HQO data
- Provides context and explanations
- Not a data source for scraping

---

### 4. Hospital-Specific Portals

Several hospitals publish their own real-time data:

| Hospital | URL | Update Frequency |
|----------|-----|------------------|
| UHN (Toronto General, Toronto Western) | https://www.uhn.ca/PatientsFamilies/Visit_UHN/Emergency/Pages/ED_wait_times.aspx | Real-time |
| LHSC (London) | https://www.lhsc.on.ca/adult-ed/emergency-department-wait-times | Real-time |
| Hamilton Health Sciences | https://www.hamiltonemergencywaittimes.ca/ | Every 15 min |
| Niagara Health | https://www.niagarahealth.on.ca/site/waiting-times | Real-time |

**Note:** These are useful for verification but ER Watch aggregates them all.

---

## Recommended Approach

### For MVP: Use ER Watch

1. **Fetch URL:** `https://www.er-watch.ca/`
2. **Parse Method:** Playwright to render JavaScript, then extract JSON from page
3. **Update Scraper:** Modify `ontario.py` to target ER Watch instead of HQO

### Scraper Configuration

```python
# backend/src/waittime/scrapers/ontario.py

SOURCE_CONFIG = {
    "id": "on-erwatch",
    "name": "ER Watch Ontario",
    "url": "https://www.er-watch.ca/",
    "province": "Ontario",
    "methodology_url": "https://www.hqontario.ca/System-Performance/Measuring-System-Performance/Measuring-Time-Spent-in-Emergency-Departments",
    "update_frequency_minutes": 15,
}

# Ontology mapping
ONTOLOGY = {
    "metric_family": "TIME_TO_PROVIDER",
    "start_event": "TRIAGE",  # ER Watch uses triage start
    "end_event": "PHYSICIAN",
    "statistic_type": "POINT_ESTIMATE",  # Real-time estimate, not P90
    "patient_scope": "ALL",
}
```

### Data Extraction Strategy

```python
# Pseudocode for extraction

async def extract_hospitals(page):
    # Wait for React to hydrate
    await page.wait_for_selector('[data-testid="hospital-card"]')

    # Extract JSON from page's __NEXT_DATA__ script
    json_data = await page.evaluate('''
        () => {
            const script = document.getElementById('__NEXT_DATA__');
            return script ? JSON.parse(script.textContent) : null;
        }
    ''')

    # Parse hospitals from props
    hospitals = json_data['props']['pageProps']['hospitals']
    return hospitals
```

---

## Ontology Mapping

| ER Watch Field | Our Ontology |
|----------------|--------------|
| `estimated_wait_time` | `value` (minutes) |
| Hospital location | Maps to our `hospital_id` via fuzzy matching |
| Real-time point estimate | `statistic_type: POINT_ESTIMATE` |

**Important:** ER Watch shows real-time estimates, which differs from HQO's P90 historical data. Our ontology must reflect this:

- ER Watch: `POINT_ESTIMATE` (current wait)
- HQO: `P90` (90th percentile historical)

These are **not directly comparable** and should trigger a divergence warning.

---

## Next Steps

1. [ ] Update Ontario scraper URL to `https://www.er-watch.ca/`
2. [ ] Implement Playwright-based JSON extraction
3. [ ] Map ER Watch hospital IDs to our standardized IDs
4. [ ] Update source record in database with new ontology values
5. [ ] Test with real data

---

*Research conducted: February 2026*
