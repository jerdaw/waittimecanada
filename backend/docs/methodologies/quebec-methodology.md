# Quebec Emergency Department Wait Time Methodology

## Executive Summary

Quebec reports emergency department wait times through the Ministere de la Sante et des Services sociaux (MSSS) web portal. Quebec's methodology is **fundamentally different** from all other Canadian provinces currently tracked, using a **REGISTRATION** start event (not TRIAGE) and a **ROLLING_AVG** statistic type.

**Key Findings:**
- Quebec uses **REGISTRATION as the start event** (administrative check-in), not TRIAGE
- This means Quebec's reported times include the registration-to-triage interval, making numbers appear longer
- Wait times are reported as a **rolling average** (window unspecified by MSSS)
- Data covers **110+ emergency departments** across all Quebec health regions
- Quebec's methodology is **not directly comparable** to any other province on two ontology dimensions

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

### Primary Source: MSSS Emergency Room Situation Portal

**Provider:** Ministere de la Sante et des Services sociaux (MSSS)
**URL:** https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec
**Coverage:** 110+ emergency departments across Quebec
**Update Frequency:** Periodically throughout the day (exact interval not publicly documented)
**Data Type:** Rolling average estimates

**What They Report:**
- **Estimated waiting time for non-priority cases**: Average wait from registration to physician ✅ **SCRAPED**
- **Stretcher occupancy rate**: Percentage of stretchers in use ✅ **SCRAPED (M17)** - Stored as STRETCHER_OCCUPANCY measurements
- **Number of patients on stretchers**: Current count (displayed but not scraped)
- **Average length of stay on stretcher**: For admitted patients awaiting transfer (not scraped)

**Methodology:**
- Reports a **rolling average** of registration-to-physician time
- The averaging window is not publicly specified by MSSS
- Based on hospital administrative data systems
- Includes all patient acuity levels

**Ontology Mapping (Wait Time):**
```
metric_family: TIME_TO_PROVIDER
start_event: REGISTRATION
end_event: PHYSICIAN
statistic_type: ROLLING_AVG
patient_scope: ALL
```

**Ontology Mapping (Occupancy):**
```
metric_family: STRETCHER_OCCUPANCY
start_event: UNKNOWN (point-in-time snapshot)
end_event: PHYSICIAN (placeholder for consistency)
statistic_type: POINT_ESTIMATE
patient_scope: ALL
```

**Note:** Stretcher occupancy is reported as a percentage (e.g., 110% = 10% over capacity). This is a **Quebec-only metric** - no other province currently reports occupancy data.

---

## Metric Ontology

### Time-to-Provider Definition

**Start Event: REGISTRATION**
- Clock starts at **administrative check-in** (registration desk)
- This is **before triage** in the patient flow
- Patient has identified themselves and been entered into the hospital system
- Does NOT require clinical assessment to have occurred

**End Event: PHYSICIAN**
- Clock stops when patient is **first assessed by a physician**
- Includes initial physician contact

### Statistical Type

**ROLLING_AVG (Rolling Average):**
- Moving average over an unspecified time window
- Smooths out short-term fluctuations
- More stable than point estimates but less informative than percentiles
- The averaging window is not documented by MSSS, introducing methodological uncertainty

**Key Distinction:**
The REGISTRATION start event is the critical differentiator. In the typical patient flow:

```
DOOR -> REGISTRATION -> TRIAGE -> ... -> PHYSICIAN
       ^                ^
       Quebec starts     Ontario/Alberta/BC start
       clock here        clock here
```

This means Quebec's reported wait times inherently include the registration-to-triage interval, which can add 15-60 minutes depending on ED volume. Quebec's numbers will **systematically appear longer** than Ontario, Alberta, or BC for the same actual triage-to-physician performance.

---

## Comparability Analysis

### Cross-Province Comparisons

**Quebec vs Ontario:**
- **Comparable?** No
- **Differences:**
  - Start event: Quebec REGISTRATION vs Ontario TRIAGE
  - Statistic: Quebec ROLLING_AVG vs Ontario POINT_ESTIMATE (real-time) or P90 (HQO)
- **Verdict:** Two ontology dimensions differ. Quebec's times are systematically longer due to the earlier start event, and a rolling average cannot be compared to a point estimate or P90.

**Quebec vs BC:**
- **Comparable?** No
- **Differences:**
  - Start event: Quebec REGISTRATION vs BC TRIAGE
  - Statistic: Quebec ROLLING_AVG vs BC P90
- **Verdict:** Both the start event and statistic type differ. Quebec measures from registration (earlier) using an average (including all values), while BC measures from triage (later) using the 90th percentile (capturing worst-case).

**Quebec vs Alberta:**
- **Comparable?** No
- **Differences:**
  - Start event: Quebec REGISTRATION vs Alberta TRIAGE
  - Statistic: Quebec ROLLING_AVG vs Alberta POINT_ESTIMATE
- **Verdict:** Two ontology dimensions differ.

### Summary: Quebec Is Unique

Quebec is the only province in our system that uses REGISTRATION as the start event. This makes it incomparable to all other provinces without adjustment. The rolling average statistic adds a second dimension of incomparability.

### Divergence Brief Example

When comparing CHUM (Quebec) vs The Ottawa Hospital - Civic Campus (Ontario):

> **Methodology Divergence**
> **CHUM (QC)** reports a rolling average of registration-to-physician time.
> **Ottawa Hospital - Civic Campus (ON)** reports a real-time point estimate of triage-to-physician time.
>
> **Why this matters:**
> - Quebec's clock starts at registration (before triage); Ontario's starts at triage (after registration)
> - This registration-to-triage gap typically adds 15-60 minutes to Quebec's reported times
> - Quebec uses a rolling average while Ontario uses an instantaneous snapshot
> - **Direct comparison is clinically invalid.** Quebec's numbers will appear systematically higher even if actual physician assessment times are identical.

---

## Technical Implementation

### Scraper Configuration

```python
SOURCE = Source(
    id="quebec-msss",
    name="Ministere de la Sante et des Services sociaux",
    province="QC",
    url="https://www.quebec.ca/en/health/...",
    methodology_url=None,
    telehealth_name="Info-Sante 811",
    telehealth_number="811",
    default_metric_family=MetricFamily.TIME_TO_PROVIDER,
    default_start_event=StartEvent.REGISTRATION,
    default_end_event=EndEvent.PHYSICIAN,
    default_statistic_type=StatisticType.ROLLING_AVG,
)
```

### Scraper Approach: Paginated AJAX

**Why Pagination is Needed:**
- The MSSS portal uses a Typo3 AJAX endpoint with paginated results
- Results are returned as HTML fragments (10 hospitals per page)
- Typically 12+ pages covering 110+ hospitals

**Implementation:**
1. Iterate through pages using the Typo3 AJAX endpoint
2. Parse HTML fragments for `div.hospital_element` cards
3. Extract hospital name and wait time from each card
4. Handle bilingual content (French and English text patterns)
5. Respect 1-second delay between page requests

### Hospital ID Generation

Quebec uses a two-tier ID system:
1. **Static mapping** for well-known hospitals (21 entries in `HOSPITAL_MAPPING`)
2. **Auto-generation** via NFKD normalization for newly discovered hospitals

```python
# Static mapping examples:
"CHUM" -> "ca-qc-chum"
"Hopital general juif" -> "ca-qc-jewish-general"

# Auto-generated examples:
"Hopital de Gatineau" -> "ca-qc-hopital-de-gatineau"
"CHU Sainte-Justine" -> "ca-qc-chu-sainte-justine"
```

### Wait Time Parsing

Quebec reports wait times in multiple formats:
- `"4 h 15 min"` (hours and minutes, French style)
- `"2:30"` (time format)
- `"120 min"` (minutes only)

The parser handles all variants and converts to total minutes.

---

## Policy Context

### Info-Sante 811

Quebec's telehealth service:
- **Phone:** 811
- **Service:** Info-Sante 811 provides 24/7 telephone nursing consultation
- **Languages:** French, English, and interpretation services
- **Scope:** Health advice, referral guidance, non-emergency triage

**Integration:**
> When displaying Quebec hospital data, show:
> "Before visiting an emergency department, consider calling Info-Sante 811 for health advice."

### Quebec Health Network Structure

Quebec's health system is organized into regional CISSS/CIUSSS:

| Region | Key Facilities |
|--------|---------------|
| **Montreal** | CHUM, Jewish General, Maisonneuve-Rosemont, Sacre-Coeur, Notre-Dame, Santa Cabrini |
| **Laval** | Hopital de la Cite-de-la-Sante |
| **Monteregie** | Charles-Le Moyne, Pierre-Boucher, Anna-Laberge, Haut-Richelieu, Honore-Mercier |
| **Quebec City** | CHU de Quebec (Enfant-Jesus, CHUL, Hotel-Dieu) |
| **Outaouais** | Hopital de Gatineau, Hopital de Hull |

### Outaouais-Ottawa Corridor

The Gatineau/Hull hospitals are particularly important for the WaitTime Canada cross-province comparison narrative:
- **Hopital de Gatineau** is 15 km from **The Ottawa Hospital - Civic Campus**
- These facilities serve overlapping populations in the National Capital Region
- Despite geographic proximity, their methodologies are completely incomparable
- This demonstrates why methodology transparency matters for patient decision-making

### Triage System (ETG / CTAS)

Quebec uses the Echelle de triage et de gravite (ETG), the French-language adaptation of CTAS:
1. **P1 (Reanimation)**: Immediate
2. **P2 (Tres urgent)**: 15 minutes
3. **P3 (Urgent)**: 30 minutes
4. **P4 (Moins urgent)**: 60 minutes
5. **P5 (Non urgent)**: 120 minutes

The MSSS portal reports wait times for **all patients** (patient_scope: ALL).

---

## Geographic Coverage

### Current Coverage

Quebec has the broadest coverage of any province in our system with **110+ emergency departments** across all health regions, including:

- **Major urban centres**: Montreal, Quebec City, Laval, Longueuil, Gatineau
- **Regional hospitals**: Rimouski, Chicoutimi, Sherbrooke, Trois-Rivieres
- **Community hospitals**: Smaller facilities across rural Quebec

### Notable Coverage

Unlike BC (which only covers Vancouver Coastal/Fraser regions), Quebec's MSSS portal covers the **entire province**, making it the most comprehensive provincial data source by geographic coverage.

---

## Validation Checklist

When adding a new Quebec hospital measurement:

- [ ] Hospital ID follows format `ca-qc-{normalized-slug}`
- [ ] `source_id` is `quebec-msss`
- [ ] `metric_family` is `TIME_TO_PROVIDER`
- [ ] `start_event` is `REGISTRATION` (not TRIAGE)
- [ ] `end_event` is `PHYSICIAN`
- [ ] `statistic_type` is `ROLLING_AVG`
- [ ] `patient_scope` is `ALL`
- [ ] Timestamp is in UTC
- [ ] Raw payload is hashed (not stored in full)

---

## References

### Official Documentation

1. **MSSS - Situation in Emergency Rooms**
   https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec

2. **Quebec Health System Organization**
   https://www.quebec.ca/en/health/health-system-and-services/service-organization

3. **Canadian Triage and Acuity Scale (CTAS/ETG)**
   https://caep.ca/wp-content/uploads/2017/06/module_1_slides_v2.5_2012.pdf

### Telehealth

4. **Info-Sante 811**
   https://www.quebec.ca/en/health/finding-a-resource/info-sante-811

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-11 | Initial methodology documentation |

---

*Last Updated: February 11, 2026*
*Maintained by: WaitTime Canada Research Team*
