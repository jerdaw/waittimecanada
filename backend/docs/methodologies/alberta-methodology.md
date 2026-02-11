# Alberta Emergency Department Wait Time Methodology

## Executive Summary

Alberta Health Services (AHS) reports real-time emergency department wait times through a centralized web portal. The data represents **point estimates** of current wait times, updated approximately every **2 minutes**.

**Key Findings:**
- Alberta uses a **single real-time methodology**: point estimates of triage-to-physician time
- Data covers **20+ emergency departments** across all 5 AHS geographic zones
- Wait times are **POINT_ESTIMATE** (instantaneous snapshots), fundamentally different from Ontario's P90 or BC's P90
- AHS operates as a single provincial health authority (unlike other provinces with regional authorities)

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Metric Ontology](#metric-ontology)
3. [Comparability Analysis](#comparability-analysis)
4. [Technical Implementation](#technical-implementation)
5. [Policy Context](#policy-context)
6. [References](#references)

---

## Data Sources

### Primary Source: AHS Wait Times Portal

**Provider:** Alberta Health Services
**URL:** https://www.albertahealthservices.ca/waittimes/Page14230.aspx
**Coverage:** 20+ emergency departments across Alberta
**Update Frequency:** Approximately every 2 minutes
**Data Type:** Real-time point estimates

**What They Report:**
- **Estimated wait time**: Current estimated wait from triage to physician assessment
- **Facility type**: Emergency department category (adult, pediatric, combined)
- **City/Zone**: Geographic grouping by AHS zone (South, Calgary, Central, Edmonton, North)

**Methodology:**
- Reports the **current instantaneous estimated wait time** at each facility
- Based on hospital operational data systems
- Represents a **point estimate**, not a statistical aggregate
- Subject to high variability depending on current ED volume and acuity mix

**Ontology Mapping:**
```
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE
end_event: PHYSICIAN
statistic_type: POINT_ESTIMATE
patient_scope: ALL
```

---

## Metric Ontology

### Time-to-Provider Definition

**Start Event: TRIAGE**
- Clock starts **after triage nurse assessment**
- Patient has been categorized by acuity (CTAS 1-5)
- Based on AHS description: "Triage nurse assessment to physician"

**End Event: PHYSICIAN**
- Clock stops when patient is **first assessed by a physician**
- Includes initial physician contact

### Statistical Type

**POINT_ESTIMATE:**
- Single instantaneous measurement at time of page load
- "Right now, the estimated wait is X minutes"
- High temporal variability (can change every 2 minutes)
- Suitable for: Patient decision-making about which ED to visit

**Key Distinction:**
- Alberta's POINT_ESTIMATE differs fundamentally from BC's P90 (90th percentile) and Quebec's ROLLING_AVG (moving average)
- A POINT_ESTIMATE captures a single moment; P90 captures the worst-case experience for 90% of patients over a time window
- Direct comparison between these statistic types is scientifically invalid

---

## Comparability Analysis

### Cross-Province Comparisons

**Alberta vs Ontario (Real-Time):**
- **Comparable?** Partially
- **Similarities:** Both measure TRIAGE to PHYSICIAN, both are real-time
- **Differences:** Ontario's real-time data is also POINT_ESTIMATE, so ontology fields match
- **Verdict:** Comparable when Ontario uses POINT_ESTIMATE. Not comparable with Ontario HQO (P90).

**Alberta vs BC:**
- **Comparable?** No
- **Similarities:** Both measure TRIAGE to PHYSICIAN
- **Differences:** Alberta uses POINT_ESTIMATE; BC uses P90
- **Verdict:** Different statistic types make direct comparison invalid. A BC P90 of 180 minutes means "90% of patients seen within 180 min." An Alberta POINT_ESTIMATE of 45 minutes means "right now the estimated wait is 45 min." These measure different things.

**Alberta vs Quebec:**
- **Comparable?** No
- **Differences:**
  - Start event: Alberta uses TRIAGE; Quebec uses REGISTRATION
  - Statistic type: Alberta uses POINT_ESTIMATE; Quebec uses ROLLING_AVG
- **Verdict:** Two ontology dimensions differ. Quebec's REGISTRATION start event means the clock starts earlier (before triage), inflating reported times. Combined with different statistics, comparison is doubly invalid.

### Divergence Brief Example

When comparing Foothills Medical Centre (Alberta) vs Vancouver General Hospital (BC):

> **Methodology Divergence**
> **Foothills Medical Centre (AB)** reports a real-time point estimate of triage-to-physician time, updated every 2 minutes.
> **Vancouver General (BC)** reports the 90th percentile of triage-to-physician time.
>
> **Why this matters:**
> - Alberta's point estimate captures the current wait at a single moment
> - BC's P90 means 90% of patients were seen within the posted time over a rolling window
> - A low Alberta point estimate does NOT mean Alberta consistently has shorter waits
> - **Direct comparison is clinically invalid.** These statistics measure different aspects of ED performance.

---

## Technical Implementation

### Scraper Configuration

```python
SOURCE = Source(
    id="alberta-ahs",
    name="Alberta Health Services",
    province="AB",
    url="https://www.albertahealthservices.ca/waittimes/Page14230.aspx",
    methodology_url="https://www.albertahealthservices.ca/waittimes/Page14230.aspx",
    telehealth_name="Health Link 811",
    telehealth_number="811",
    default_metric_family=MetricFamily.TIME_TO_PROVIDER,
    default_start_event=StartEvent.TRIAGE,
    default_end_event=EndEvent.PHYSICIAN,
    default_statistic_type=StatisticType.POINT_ESTIMATE,
)
```

### Scraper Approach: Playwright (JavaScript-Rendered)

**Why Playwright is Required:**
- AHS uses JavaScript to dynamically load wait time data
- The `div.well.wt-well` cards contain wait times rendered client-side
- Static HTML fetching returns an empty page shell

**Implementation:**
1. Launch headless Chromium via Playwright
2. Navigate to AHS wait times page
3. Wait for `div.wt-well` or `div.wt-times` elements to render
4. Parse rendered HTML with BeautifulSoup
5. Extract hospital names and wait times from card elements

### Hospital ID Generation

Alberta uses NFKD Unicode normalization to generate hospital IDs:

```python
def _normalize_hospital_id(hospital_name: str) -> str:
    normalized = unicodedata.normalize("NFKD", hospital_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return f"ca-ab-{slug}"
```

**Examples:**
- "Foothills Medical Centre" -> `ca-ab-foothills-medical-centre`
- "Alberta Children's Hospital" -> `ca-ab-alberta-children-s-hospital`
- "Queen Elizabeth II Hospital" -> `ca-ab-queen-elizabeth-ii-hospital`

### Wait Time Parsing

Wait times appear in formats like "45 min", "1 hour 30 min", or plain numbers. The parser handles hours+minutes combinations and falls back to numeric extraction.

---

## Policy Context

### Health Link 811

Alberta's telehealth service for health advice and information:
- **Phone:** 811
- **Service:** 24/7 registered nurses provide health advice
- **Languages:** Translation services available
- **Scope:** Can help determine if ED visit is necessary

**Integration:**
> When displaying Alberta hospital data, show:
> "Before visiting an emergency department, consider calling Health Link 811 for health advice."

### AHS Zone Structure

Alberta Health Services operates through 5 geographic zones:

| Zone | Major Cities | Key Emergency Departments |
|------|-------------|--------------------------|
| **South** | Lethbridge, Medicine Hat | Chinook Regional, Medicine Hat Regional |
| **Calgary** | Calgary, Canmore, High River | Foothills, Rockyview, Peter Lougheed, South Health Campus, Alberta Children's |
| **Central** | Red Deer | Red Deer Regional Hospital Centre |
| **Edmonton** | Edmonton, St. Albert, Sherwood Park | Royal Alexandra, U of A, Misericordia, Grey Nuns, Stollery, Sturgeon, Strathcona |
| **North** | Grande Prairie, Fort McMurray | Queen Elizabeth II, Northern Lights Regional |

### Triage System (CTAS)

Alberta uses the Canadian Triage and Acuity Scale (CTAS), same as all Canadian provinces:
1. **CTAS 1 (Resuscitation)**: Immediate
2. **CTAS 2 (Emergent)**: 15 minutes
3. **CTAS 3 (Urgent)**: 30 minutes
4. **CTAS 4 (Less Urgent)**: 60 minutes
5. **CTAS 5 (Non-Urgent)**: 120 minutes

Wait times reported on the AHS portal apply to **all patients** (patient_scope: ALL), not filtered by acuity level.

---

## Geographic Coverage

### Current Coverage

**Calgary Zone (5+ EDs):**
- Foothills Medical Centre (Level 1 Trauma)
- Rockyview General Hospital
- Peter Lougheed Centre
- South Health Campus
- Alberta Children's Hospital (Pediatric)

**Edmonton Zone (7+ EDs):**
- Royal Alexandra Hospital
- University of Alberta Hospital (Level 1 Trauma)
- Stollery Children's Hospital (Pediatric, co-located with U of A)
- Misericordia Community Hospital
- Grey Nuns Community Hospital
- Northeast Community Health Centre
- Sturgeon Community Hospital (St. Albert)
- Strathcona Community Hospital (Sherwood Park)

**Central Zone:**
- Red Deer Regional Hospital Centre

**South Zone:**
- Chinook Regional Hospital (Lethbridge)
- Medicine Hat Regional Hospital

**North Zone:**
- Queen Elizabeth II Hospital (Grande Prairie)
- Northern Lights Regional Health Centre (Fort McMurray)

---

## Validation Checklist

When adding a new Alberta hospital measurement:

- [ ] Hospital ID follows format `ca-ab-{normalized-slug}`
- [ ] `source_id` is `alberta-ahs`
- [ ] `metric_family` is `TIME_TO_PROVIDER`
- [ ] `start_event` is `TRIAGE`
- [ ] `end_event` is `PHYSICIAN`
- [ ] `statistic_type` is `POINT_ESTIMATE`
- [ ] `patient_scope` is `ALL`
- [ ] Timestamp is in UTC
- [ ] Raw payload is hashed (not stored in full)

---

## References

### Official Documentation

1. **Alberta Health Services - Emergency & Urgent Care Wait Times**
   https://www.albertahealthservices.ca/waittimes/Page14230.aspx

2. **AHS Zone Map & Information**
   https://www.albertahealthservices.ca/about/zone.aspx

3. **Canadian Triage and Acuity Scale (CTAS)**
   https://caep.ca/wp-content/uploads/2017/06/module_1_slides_v2.5_2012.pdf

### Telehealth

4. **Health Link 811**
   https://www.albertahealthservices.ca/info/Page12630.aspx

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial methodology documentation |

---

*Last Updated: February 11, 2026*
*Maintained by: WaitTime Canada Research Team*
