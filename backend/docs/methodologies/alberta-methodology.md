# Alberta Emergency Department Wait Time Methodology

> [!WARNING]
> **Alberta methodology revalidation required.** An audit of official sources on
> 22 Nov 2026 found that the repository's Alberta tags overstate what AHS
> publishes. The posted figure is a software-modelled estimate for a mid-acuity
> patient, not an observed instantaneous measurement of all patients. The stored
> `patient_scope: ALL` is wrong, and `POINT_ESTIMATE` hides that the figure is
> modelled. These are legacy implementation values pending an ontology and
> historical-data decision; do not backfill or reinterpret historical Alberta
> values in the meantime.
>
> What AHS says (accessed 22 Nov 2026):
>
> - Start and end: "an estimate of how long it might take from an assessment by
>   a triage nurse" in the emergency department or urgent care to being seen by
>   a physician. The page adds that wait times do not represent the total time
>   at the hospital.
>   <https://www.albertahealthservices.ca/waittimes/Page14230.aspx>
> - Method: the times "are calculated through a software system" that uses
>   current data from the facility, and the figure "represents a prediction of a
>   very specific snapshot in time". The calculation is repeated "every 2
>   minutes". The page's illustration is generally based on a physician seeing a
>   patient every 30 minutes. No averaging window is stated.
>   <https://www.albertahealthservices.ca/waittimes/Page14230.aspx>
> - Scope: the estimates are designed for "the average, mid-acuity patient".
>   The calculation does not aim to predict times for the most urgent patients
>   (CTAS 1) or the least ill (CTAS 5), and the page says estimates do not apply
>   to critically ill or injured patients.
>   <https://www.albertahealthservices.ca/assets/about/data/ahs-data-edm-understanding-wait-times-patients.pdf>
> - The page lists facilities in six cities; the repository's facility
>   coverage was not reconciled with that list in this correction.

## Executive Summary

Alberta Health Services (AHS) reports real-time emergency department wait times through a centralized web portal. The posted figures are **software-modelled estimates** of the current wait for a mid-acuity patient, recalculated approximately every **2 minutes**.

**Key Findings:**
- Alberta publishes a **modelled prediction** from triage nurse assessment to being seen by a physician, not an observed statistic
- The estimate is for an average, mid-acuity patient and excludes CTAS 1 and CTAS 5 by design
- The repository stores it as `POINT_ESTIMATE` with `patient_scope: ALL`; both are legacy tags (see the warning above)
- Data covers **20+ emergency departments** across all 5 AHS geographic zones
- The figure is a different kind of quantity from Ontario's observed monthly mean and BC's posted 90th percentile
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
**Data Type:** Real-time modelled estimates (mid-acuity patient)

**What They Report:**
- **Estimated wait time**: Modelled estimate of the wait from a triage nurse's assessment to being seen by a physician, for a mid-acuity patient
- **Facility type**: Emergency department category (adult, pediatric, combined)
- **City/Zone**: Geographic grouping by AHS zone (South, Calgary, Central, Edmonton, North)

**Methodology:**
- Reports a **software-modelled estimate** at each facility, calculated from current facility data (patients present and acuity compared with available resources)
- Designed for the average, mid-acuity patient; CTAS 1 and CTAS 5 are excluded from what the calculation aims to predict
- Recalculated about every 2 minutes; no averaging window is stated
- Subject to high variability depending on current ED volume and acuity mix

**Ontology Mapping:**
```
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE
end_event: PHYSICIAN
statistic_type: POINT_ESTIMATE   # legacy tag; the figure is model-derived (ALGORITHMIC is the closer existing value)
patient_scope: ALL               # legacy tag; incorrect, official scope is mid-acuity (CTAS 1 and 5 excluded)
mapping_status: LEGACY_IMPLEMENTATION_TAGS_PENDING_REVALIDATION
```

This block documents current stored behavior only. Start and end events are
consistent with the AHS wording. Statistic and patient scope are not.

---

## Metric Ontology

### Time-to-Provider Definition

**Start Event: TRIAGE**
- Clock starts at the **triage nurse's assessment**, so any wait before triage is excluded by design
- Consistent with the AHS description of an assessment by a triage nurse to being seen by a physician

**End Event: PHYSICIAN**
- Clock stops when the patient is **seen by a physician**
- The AHS FAQ notes that other providers may start assessments, tests, or treatment while patients wait

### Statistical Type

**POINT_ESTIMATE (legacy tag):**
- The posted number is a prediction for a specific moment, produced by software, not a measured statistic over completed visits
- High temporal variability (recalculated about every 2 minutes)
- The tag name hides that the value is modelled; `ALGORITHMIC` is the existing ontology value closest to the official description, but changing tags is outside this documentation correction

**Key Distinction:**
- Alberta's modelled mid-acuity estimate differs fundamentally from BC's posted 90th percentile and from Ontario's observed monthly mean
- Quebec's live estimate has no published definition (see the Quebec methodology note)
- Direct comparison between these quantities is not supported

---

## Comparability Analysis

### Cross-Province Comparisons

**Alberta vs Ontario:**
- **Comparable?** No
- **Similarities:** Both are time-to-provider measures
- **Differences:** Alberta publishes a modelled estimate for a mid-acuity patient (CTAS 1 and 5 excluded); Ontario publishes an observed monthly mean for all eligible visits, from the earlier of triage or registration to first assessment by a qualifying provider
- **Verdict:** Not comparable. Start point, end point, statistic, and patient scope all differ in the official definitions.

**Alberta vs BC:**
- **Comparable?** No
- **Similarities:** Both are described as running from triage assessment to seeing a physician (BC also names nurse practitioners)
- **Differences:** Alberta publishes a modelled estimate for a mid-acuity patient; BC publishes a 90th-percentile figure (method of calculation not stated)
- **Verdict:** Not comparable. A BC 90th percentile is the time within which 90% of patients are said to be seen. An Alberta figure is a prediction for a typical mid-acuity patient. These measure different things.

**Alberta vs Quebec:**
- **Comparable?** No
- **Differences:**
  - Alberta documents a triage-nurse-assessment start, a modelled statistic, and a mid-acuity scope
  - Quebec's live estimate has no published start point, statistic, or window, and is labelled for "non-priority cases"
- **Verdict:** Not comparable. The earlier claim that Quebec starts earlier and therefore inflates times has no official support and is withdrawn.

### Divergence Brief Example

When comparing Foothills Medical Centre (Alberta) vs Vancouver General Hospital (BC):

> **Methodology Divergence**
> **Foothills Medical Centre (AB)** posts a software-modelled estimate of the wait from triage nurse assessment to physician for a mid-acuity patient, recalculated about every 2 minutes.
> **Vancouver General (BC)** posts a 90th-percentile time to be seen by a physician.
>
> **Why this matters:**
> - Alberta's figure is a prediction for a typical mid-acuity patient at one moment
> - BC's figure is a percentile, and its look-back window is not stated
> - A low Alberta estimate does NOT mean Alberta consistently has shorter waits
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
    default_statistic_type=StatisticType.POINT_ESTIMATE,  # legacy tag, pending revalidation
)
```

The statistic default above is a legacy implementation value (see the warning
at the top of this document).

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

The AHS estimate is designed for the **average, mid-acuity patient**. It does not aim to predict waits for CTAS 1 or CTAS 5 patients, and AHS says it does not apply to critically ill or injured patients. The stored `patient_scope: ALL` is therefore incorrect (legacy tag pending revalidation).

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
- [ ] `statistic_type` matches the stored legacy default (`POINT_ESTIMATE`; pending revalidation, the figure is modelled)
- [ ] `patient_scope` matches the stored legacy default (`ALL`; incorrect, official scope is mid-acuity; pending revalidation)
- [ ] Timestamp is in UTC
- [ ] Raw payload is hashed (not stored in full)

---

## References

### Official Documentation

1. **Alberta Health Services - Emergency & Urgent Care Wait Times**
   https://www.albertahealthservices.ca/waittimes/Page14230.aspx

2. **AHS Zone Map & Information**
   https://www.albertahealthservices.ca/about/zone.aspx

3. **AHS - Understanding Wait Times: Frequently Asked Questions** (accessed 22 Nov 2026)
   https://www.albertahealthservices.ca/assets/about/data/ahs-data-edm-understanding-wait-times-patients.pdf

4. **Canadian Triage and Acuity Scale (CTAS)**
   https://caep.ca/wp-content/uploads/2017/06/module_1_slides_v2.5_2012.pdf

### Telehealth

5. **Health Link 811**
   https://www.albertahealthservices.ca/info/Page12630.aspx

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial methodology documentation |
| 1.1 | 2026-11-22 | Revalidation warning; corrected patient scope and described the figure as modelled |

---

*Last Updated: November 22, 2026*
*Maintained by: Wait Time Canada Research Team*
