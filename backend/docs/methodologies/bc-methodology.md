# BC PHSA Emergency Department Wait Times - Technical & Methodology Analysis

**Website:** https://edwaittimes.ca (formerly http://www.edwaittimes.ca)
**Operator:** Provincial Health Services Authority (PHSA) in collaboration with Vancouver Coastal Health (VCH), Providence Healthcare (PHC), Fraser Health (FH), and BC Children's Hospital (BCH)
**Date Analyzed:** February 6, 2026
**Data Source:** https://edwaittimes.ca/legacy

---

## Executive Summary

BC's emergency department wait time system is a **Next.js-based web application** with data embedded via Server-Side Generation (SSG). There is **no documented public API** - data is embedded in the `__NEXT_DATA__` JSON payload on each page load. The system uses:

- **90th percentile** for physician wait times
- **75th percentile** for estimated length of stay
- **5-minute refresh cycles** (automated updates)
- **Azure-hosted CMS backend** (not publicly accessible)

**Scraping Strategy:** Parse the `__NEXT_DATA__` JSON object from the legacy page (`/legacy` route) or use Playwright to render the modern interface.

---

## 1. API Endpoint Analysis

### Finding: No Public REST/GraphQL API

**Evidence:**
- Search queries for API documentation returned no official endpoints
- The BC Health Data researcher noted they had to **scrape** the site (Source: [BC Health Data - Emergency Rooms](https://healthdatabc.ca/emrg/erwaits.html))
- The Azure CMS backend (`https://vcha-m-prd-admin-ui-website.azurewebsites.net`) is an admin interface, not a public API

**Data Access Method:**
The `/legacy` route embeds a complete JSON payload in the `__NEXT_DATA__` script tag:

```javascript
window.__NEXT_DATA__ = {
  props: {
    pageProps: {
      locationsWithWaitTimes: [
        {
          id: "...",
          name: "Vancouver General Hospital",
          waitTime: {
            waitTimeMinutes: 282,
            elosMinutes: 601,
            status: "normal",
            createdAt: "2026-02-06T20:38:00.000Z"
          },
          // ... additional fields
        }
      ]
    }
  }
}
```

**Recommended Scraping Approach:**
1. Fetch `https://edwaittimes.ca/legacy`
2. Parse HTML to extract `<script id="__NEXT_DATA__">` tag
3. Parse JSON and access `props.pageProps.locationsWithWaitTimes`
4. Extract `waitTime.waitTimeMinutes` and `waitTime.elosMinutes` for each location

---

## 2. JavaScript Framework & Data Loading

### Framework: Next.js 14+ with Static Site Generation (SSG)

**Technical Stack:**
- **Framework:** Next.js (build ID: `_q6MgAbpLBPeAU4DskxvP`)
- **Rendering:** Server-Side Generation with automatic revalidation (`"__N_SSG": true`)
- **Map Library:** Mapbox GL JS (token: `pk.eyJ1Oi...`)
- **Analytics:** Google Analytics 4 (ID: `G-FQJLPMV86M`)
- **Serialization:** SuperJSON (for Date objects and referential equality)

**Data Loading Strategy:**
- Data is **pre-rendered** during build/revalidation (not fetched client-side)
- Page states: "automatically refresh every 5 minutes"
- No visible AJAX/fetch calls in browser DevTools (data is embedded in initial HTML)

---

## 3. Wait Time Data Structure

### Sample Hospital Data

Based on the `/legacy` page (Feb 6, 2026 at 12:38 PM PST):

#### 24/7 Emergency Departments (Core Metro Vancouver)

| Hospital                      | Type | Wait Time to MD | Est. Length of Stay | Open 24/7 |
|-------------------------------|------|-----------------|---------------------|-----------|
| St. Paul's Hospital           | ED   | 1h 35m (95 min) | 4h 34m (274 min)    | Yes       |
| Vancouver General Hospital    | ED   | 4h 42m (282 min)| 10h 1m (601 min)    | Yes       |
| BC Children's Hospital        | ED   | 5h 10m (310 min)| 7h 11m (431 min)    | Yes       |
| Richmond Hospital             | ED   | 5h 47m (347 min)| 9h 57m (597 min)    | Yes       |
| Lions Gate Hospital           | ED   | 4h 9m (249 min) | 7h 56m (476 min)    | Yes       |

#### Fraser Health Region (24/7)

| Hospital                      | Wait Time to MD  |
|-------------------------------|------------------|
| Ridge Meadows Hospital        | 1h 26m (86 min)  |
| Burnaby Hospital              | 2h 44m (164 min) |
| Royal Columbian Hospital      | 2h 33m (153 min) |
| Eagle Ridge Hospital          | 2h 37m (157 min) |
| Peace Arch Hospital           | 3h 4m (184 min)  |
| Delta Hospital                | 2h 1m (121 min)  |
| Chilliwack General Hospital   | 1h 49m (109 min) |
| Langley Memorial Hospital     | 3h 6m (186 min)  |
| Abbotsford Regional Hospital  | 3h 31m (211 min) |
| Surrey Memorial (Adult)       | 2h 44m (164 min) |
| Surrey Memorial (Pediatrics)  | 1h 54m (114 min) |

#### Limited Hours EDs

| Facility              | Operating Hours     | Status at Sample Time |
|-----------------------|---------------------|-----------------------|
| Mount Saint Joseph    | 8am - 8pm           | Closed                |
| UBC Hospital          | 8am - 8pm           | Closed                |
| Whistler Health Care  | 8am - 10pm          | Closed                |
| Pemberton Health Care | 8:30am - 8:30pm     | Closed                |

---

## 4. Methodology Analysis

### Official Definitions (Source: [About Page](https://www.edwaittimes.ca/about))

#### Wait Time to Physician
**Metric Definition:**
> "the length of time between being assessed by a triage nurse and seeing a doctor or nurse practitioner."

**Statistic Type:** 90th percentile
> "the time it takes for almost all patients – 9 out of every 10 who visit the ED – to be seen by a physician"

**Interpretation:** 90% of patients see a physician within the posted time; ~10% wait longer.

#### Estimated Length of Stay (ELOS)
**Metric Definition:**
> "the length of time in the emergency department from the time you arrive to the time you are discharged home"

**Statistic Type:** 75th percentile
> "75 out of 100" patients are discharged within the posted time

**Exclusions:** Patients admitted to hospital (only discharged patients counted)

### Data Freshness
- **Update Frequency:** Every 5 minutes (automated)
- **Timestamp Format:** ISO 8601 UTC (`2026-02-06T20:38:00.000Z`)

### Disclaimers
The site explicitly warns:
> "wait times can change significantly and immediately, without warning"

Actual wait times may differ due to:
- Patient acuity (sicker patients seen first)
- Sudden surges in demand
- Staffing changes

---

## 5. Metric Ontology Mapping

Based on the WaitTime Canada ontology system:

### Wait Time to Physician

| Ontology Field    | BC Value               | Notes                                      |
|-------------------|------------------------|--------------------------------------------|
| `metric_family`   | `TIME_TO_PROVIDER`     | Measures time to MD/NP                     |
| `start_event`     | `TRIAGE`               | Explicitly stated: "after triage nurse"    |
| `end_event`       | `PHYSICIAN`            | Seeing "doctor or nurse practitioner"      |
| `statistic_type`  | `P90`                  | 90th percentile                            |
| `patient_scope`   | `ALL`                  | No acuity filtering mentioned              |

### Estimated Length of Stay

| Ontology Field    | BC Value               | Notes                                      |
|-------------------|------------------------|--------------------------------------------|
| `metric_family`   | `TOTAL_LOS`            | Arrival to discharge                       |
| `start_event`     | `DOOR`                 | "time you arrive"                          |
| `end_event`       | `DISCHARGE`            | "discharged home"                          |
| `statistic_type`  | `P75`                  | 75th percentile                            |
| `patient_scope`   | `ALL`                  | Excludes admitted patients (explicit)      |

### Critical Comparability Note

**BC's wait time metric is COMPARABLE to:**
- Ontario's "Time to Physician Assessment" (both P90, Triage → MD)
- Any province using TRIAGE → PHYSICIAN with P90

**BC's wait time metric is NOT COMPARABLE to:**
- Quebec's metrics (uses REGISTRATION start event, not TRIAGE)
- Alberta (if they use different percentile or patient scope)
- Any metric using median/mean instead of P90

---

## 6. Data Structure Details

### JSON Schema (Extracted from `__NEXT_DATA__`)

```typescript
interface Location {
  id: string;
  name: string;
  slug: string;
  address: string;
  latitude: number;
  longitude: number;
  phone: string;
  website: string | null;
  description: string;
  type: "ed" | "upcc";  // Emergency Dept or Urgent Primary Care Centre
  audience: string[];   // e.g., ["adult", "children"]
  open247: boolean;
  operatingHours: {
    monday: { open: string; close: string; closed: boolean };
    tuesday: { open: string; close: string; closed: boolean };
    // ... (all days)
  };
  waitTime: {
    id: string;
    locationId: string;
    createdAt: string;  // ISO 8601 timestamp
    reportId: string;
    waitTimeMinutes: number | null;
    elosMinutes: number | null;
    status: "normal" | "closed" | "unavailable";
  };
}

interface PageProps {
  locationsWithWaitTimes: Location[];
}
```

### Example Hospital Record

```json
{
  "id": "vgh-ed",
  "name": "Vancouver General Hospital",
  "slug": "vgh",
  "address": "899 West 12th Avenue, Vancouver, BC V5Z 1M9",
  "latitude": 49.2606,
  "longitude": -123.1236,
  "phone": "604-875-4111",
  "website": "http://www.vch.ca/locations-and-services/find-locations/vancouver-general-hospital",
  "description": "Vancouver General Hospital's Emergency Department...",
  "type": "ed",
  "audience": ["adult"],
  "open247": true,
  "operatingHours": {
    "monday": { "open": "00:00", "close": "23:59", "closed": false },
    // ... (consistent 24/7 pattern)
  },
  "waitTime": {
    "id": "wt-12345",
    "locationId": "vgh-ed",
    "createdAt": "2026-02-06T20:38:00.000Z",
    "reportId": "report-67890",
    "waitTimeMinutes": 282,
    "elosMinutes": 601,
    "status": "normal"
  }
}
```

---

## 7. Scraper Implementation Notes

### Recommended Approach: HTML Parsing (No Playwright Required)

**Why HTML Parsing Works:**
- Data is embedded in SSG payload (no client-side rendering needed)
- `__NEXT_DATA__` is present in initial HTML response
- No authentication or bot detection observed

**Implementation Steps:**

1. **Fetch Page**
   ```python
   response = requests.get("https://edwaittimes.ca/legacy")
   html = response.text
   ```

2. **Extract JSON**
   ```python
   from bs4 import BeautifulSoup
   import json

   soup = BeautifulSoup(html, 'html.parser')
   next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
   data = json.loads(next_data_script.string)
   ```

3. **Parse Locations**
   ```python
   locations = data['props']['pageProps']['locationsWithWaitTimes']

   for loc in locations:
       if loc['type'] == 'ed' and loc['waitTime']['status'] == 'normal':
           hospital_id = f"ca-bc-{loc['slug']}"
           wait_minutes = loc['waitTime']['waitTimeMinutes']
           elos_minutes = loc['waitTime']['elosMinutes']
           timestamp = loc['waitTime']['createdAt']
   ```

4. **Store with Ontology Tags**
   ```python
   # Wait time measurement
   measurement_wait = {
       'hospital_id': hospital_id,
       'value': wait_minutes,
       'metric_family': 'TIME_TO_PROVIDER',
       'start_event': 'TRIAGE',
       'end_event': 'PHYSICIAN',
       'statistic_type': 'P90',
       'patient_scope': 'ALL',
       'scraped_at': timestamp,
       'source_id': 'ca-bc-phsa'
   }

   # ELOS measurement
   measurement_elos = {
       'hospital_id': hospital_id,
       'value': elos_minutes,
       'metric_family': 'TOTAL_LOS',
       'start_event': 'DOOR',
       'end_event': 'DISCHARGE',
       'statistic_type': 'P75',
       'patient_scope': 'ALL',
       'scraped_at': timestamp,
       'source_id': 'ca-bc-phsa'
   }
   ```

### Alternative: Playwright (If SSG Changes)

If BC switches to client-side rendering:
```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://edwaittimes.ca/legacy")
    page.wait_for_selector('[data-testid="hospital-card"]')
    data = page.evaluate('() => window.__NEXT_DATA__')
    browser.close()
```

### Rate Limiting Recommendations
- **Frequency:** Every 15 minutes (data updates every 5 min, but scraping every 15 min is respectful)
- **User-Agent:** Include contact info: `WaitTimeCanada-Bot/1.0 (contact@waittimecanada.org)`
- **Caching:** Store `createdAt` timestamp to avoid duplicate records

---

## 8. Geographic Coverage

### Current Coverage (Feb 2026)

**Vancouver Coastal Health:**
- Vancouver General Hospital
- St. Paul's Hospital
- Lions Gate Hospital
- Richmond Hospital
- Mount Saint Joseph Hospital (limited hours)
- UBC Hospital (limited hours)

**Fraser Health:**
- Surrey Memorial Hospital (Adult & Pediatric)
- Royal Columbian Hospital
- Burnaby Hospital
- Abbotsford Regional Hospital
- Langley Memorial Hospital
- Chilliwack General Hospital
- Ridge Meadows Hospital
- Eagle Ridge Hospital
- Delta Hospital
- Peace Arch Hospital

**Provincial Health Services Authority:**
- BC Children's Hospital

**Vancouver Coastal Health (Resort Areas):**
- Whistler Health Care Centre (limited hours)
- Pemberton Health Care Centre (limited hours)

### Missing Regions
- **Interior Health:** No coverage (Kelowna, Kamloops, Vernon, etc.)
- **Island Health:** Separate system (different website/methodology)
- **Northern Health:** No coverage (Prince George, Fort St. John, etc.)

**Note:** Island Health launched their own dashboard showing 8-week aggregated data (not real-time). See: [Island Health ED Wait Times News](https://medicalstaff.islandhealth.ca/news-events/er-webpage-waittimes)

---

## 9. Sources & References

- **Main Website:** https://edwaittimes.ca
- **Legacy Interface:** https://edwaittimes.ca/legacy
- **Methodology Page:** https://www.edwaittimes.ca/about
- **Resources Page:** https://www.edwaittimes.ca/resources
- **BC Health Data Analysis:** [BC Health Data - Emergency Rooms](https://healthdatabc.ca/emrg/erwaits.html)
- **BC Children's Announcement:** [BC Children's - ED Wait Times Now Online](https://www.bcchildrens.ca/about-us/news-features/emergency-department-wait-times-now-online-real-time)
- **Island Health System:** [Island Health ED Wait Times](https://medicalstaff.islandhealth.ca/news-events/er-webpage-waittimes)
- **Global News Coverage:** [Vancouver Hospital Wait Times Listed Online](https://globalnews.ca/news/484236/vancouver-hospital-emergency-wait-times-listed-online/)

---

## 10. Critical Considerations for WaitTime Canada Integration

### Strengths
✅ **Methodology transparency:** Clear definition of P90 for wait times
✅ **Frequent updates:** 5-minute refresh cycle
✅ **Comprehensive coverage:** 20+ facilities across Metro Vancouver
✅ **Both metrics:** Provides wait time AND length of stay
✅ **Operating hours:** Distinguishes 24/7 vs limited hours facilities

### Weaknesses
⚠️ **No public API:** Requires scraping (risk of breaking changes)
⚠️ **Limited geography:** Only Vancouver/Fraser regions (no Interior, Island, Northern)
⚠️ **Mixed percentiles:** P90 for wait time, P75 for ELOS (inconsistent)
⚠️ **No acuity breakdown:** All patients lumped together
⚠️ **No historical data:** Only current snapshot available

### Comparability Matrix

| Province | Wait Metric Start | Wait Metric End | Statistic | Comparable to BC? |
|----------|-------------------|-----------------|-----------|-------------------|
| BC       | TRIAGE            | PHYSICIAN       | P90       | ✅ (reference)    |
| Ontario  | TRIAGE            | PHYSICIAN       | P90       | ✅ **YES**        |
| Quebec   | REGISTRATION      | PHYSICIAN       | Mean      | ❌ **NO**         |
| Alberta  | TBD               | TBD             | TBD       | ❓ Unknown        |

### Divergence Brief Example

When comparing Vancouver General Hospital (BC) vs CHUM (Quebec):

> **⚠️ Methodology Divergence**
> **Vancouver General (BC)** reports the 90th percentile time from triage to physician assessment.
> **CHUM (Quebec)** reports the average time from registration to physician assessment.
>
> **Why this matters:**
> - Different start events: Triage happens after registration, making BC times appear shorter
> - Different statistics: P90 (BC) excludes the longest 10% of waits, while mean (QC) includes all patients
> - **Direct comparison is clinically invalid.** Use this data to understand regional methodology, not to compare facility performance.

---

## 11. Recommended Implementation Priority

**Phase 1: Core Scraper** (Week 1)
- ✅ Parse `/legacy` page for 20+ hospitals
- ✅ Store wait time + ELOS measurements with ontology tags
- ✅ Implement 15-minute scraping schedule via GitHub Actions
- ✅ Create heartbeat monitor

**Phase 2: Verification Queue** (Week 2)
- ✅ Geocode hospital addresses (lat/lon already provided by BC!)
- ✅ Manual verification UI for new hospitals
- ✅ Link to source methodology page

**Phase 3: Frontend Integration** (Week 3)
- ✅ Display BC hospitals on map
- ✅ Show "Last updated: X minutes ago"
- ✅ Comparability warnings when viewing BC + other provinces
- ✅ Telehealth info: "Call HealthLink BC at 811"

**Phase 4: Analytics** (Week 4)
- ✅ Wait time trends over time
- ✅ Peak hours analysis
- ✅ Methodology comparison table on `/methods` page

---

## 12. Contact & Governance

**Data Provider:** Provincial Health Services Authority (PHSA)
**Collaborators:** Vancouver Coastal Health, Providence Healthcare, Fraser Health, BC Children's Hospital
**Telehealth Line:** HealthLink BC - 811
**Website Contact:** No public contact form identified (would need to contact PHSA directly)

**Data License:** Not specified (public health data, likely open for non-commercial research use)

---

## Appendix: Sample Scraper Pseudocode

```python
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import hashlib

def scrape_bc_wait_times():
    """Scrape BC PHSA emergency department wait times."""

    url = "https://edwaittimes.ca/legacy"
    response = requests.get(url, headers={
        'User-Agent': 'WaitTimeCanada-Bot/1.0 (contact@waittimecanada.org)'
    })

    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    next_data = soup.find('script', {'id': '__NEXT_DATA__'})
    data = json.loads(next_data.string)

    # Extract locations
    locations = data['props']['pageProps']['locationsWithWaitTimes']

    # Generate payload hash
    payload_hash = hashlib.sha256(response.text.encode()).hexdigest()

    measurements = []

    for loc in locations:
        if loc['type'] != 'ed':
            continue  # Skip UPCCs

        wait_time = loc['waitTime']
        if wait_time['status'] != 'normal':
            continue  # Skip closed/unavailable

        hospital_id = f"ca-bc-{loc['slug']}"

        # Wait time measurement (Triage → Physician)
        if wait_time['waitTimeMinutes'] is not None:
            measurements.append({
                'hospital_id': hospital_id,
                'value': wait_time['waitTimeMinutes'],
                'metric_family': 'TIME_TO_PROVIDER',
                'start_event': 'TRIAGE',
                'end_event': 'PHYSICIAN',
                'statistic_type': 'P90',
                'patient_scope': 'ALL',
                'scraped_at': wait_time['createdAt'],
                'raw_payload_hash': payload_hash,
                'raw_payload_snippet': response.text[:200],
                'parser_version': 'v1.0'
            })

        # ELOS measurement (Door → Discharge)
        if wait_time['elosMinutes'] is not None:
            measurements.append({
                'hospital_id': hospital_id,
                'value': wait_time['elosMinutes'],
                'metric_family': 'TOTAL_LOS',
                'start_event': 'DOOR',
                'end_event': 'DISCHARGE',
                'statistic_type': 'P75',
                'patient_scope': 'ALL',
                'scraped_at': wait_time['createdAt'],
                'raw_payload_hash': payload_hash,
                'raw_payload_snippet': response.text[:200],
                'parser_version': 'v1.0'
            })

    # Write heartbeat
    write_heartbeat('ca-bc-phsa', 'healthy', len(measurements))

    return measurements

def write_heartbeat(source_id, status, record_count):
    """Write scraper status to database."""
    # Implementation depends on your database service
    pass
```

---

**End of Methodology Document**

**Last Updated:** February 6, 2026
**Analyst:** Automated Research (WaitTime Canada Project)
**Status:** ✅ Complete - Ready for scraper implementation
