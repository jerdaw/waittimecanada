# Ontario Emergency Department Wait Time Methodology

## Executive Summary

Ontario reports emergency department (ED) wait times through multiple channels, each with distinct methodologies. This document provides a comprehensive analysis of Ontario's wait time measurement approaches, data sources, and comparability considerations for the WaitTime Canada project.

**Key Findings:**
- Ontario uses **two primary methodologies**: real-time point estimates and historical P90 statistics (HQO)
- Real-time data updates **every 15 minutes** and covers **140+ hospitals**
- Official government data (HQO) reports **90th percentile (P90)** monthly aggregates
- These methodologies are **scientifically incomparable** and must be clearly distinguished

---

## Table of Contents

1. [Data Sources](#data-sources)
2. [Metric Ontology](#metric-ontology)
3. [Real-Time vs. Historical Data](#real-time-vs-historical-data)
4. [Comparability Analysis](#comparability-analysis)
5. [Technical Implementation](#technical-implementation)
6. [Policy Context](#policy-context)
7. [References](#references)

---

## Data Sources

### Primary Source: Real-Time Ontario Data

**Provider:** Ontario Real-Time Wait Time Service
**Coverage:** 140+ Ontario hospitals
**Update Frequency:** Every 15 minutes
**Data Type:** Real-time point estimates

**What They Report:**
- **Estimated wait time**: Current wait time in minutes
- **Patients waiting**: Number of patients in waiting room
- **Patients in treatment**: Number currently being seen
- **Last updated**: Timestamp of last data refresh

**Methodology:**
- Reports the **current instantaneous wait time** as of the last update
- Based on hospital-provided real-time data feeds
- Represents a **point estimate**, not a statistical aggregate
- Subject to high variability throughout the day

**Ontology Mapping:**
```
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE
end_event: PHYSICIAN
statistic_type: POINT_ESTIMATE
patient_scope: ALL
```

### Secondary Source: Health Quality Ontario (Historical)

**Provider:** Health Quality Ontario (HQO) - Official Government Agency
**URL:** https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments
**Coverage:** All Ontario hospitals
**Update Frequency:** Quarterly
**Data Type:** Historical aggregates

**What They Report:**
- **P90 wait time to physician**: Time for 90% of patients to see a doctor
- **Length of stay**: Total time in ED for admitted vs. discharged patients
- **By triage level**: CTAS 2-5 (excludes most critical CTAS 1)

**Methodology:**
- Calculates the **90th percentile** of historical wait times
- Aggregated over **monthly** or **quarterly** periods
- Represents the wait time experienced by 90% of patients (90% waited this long or less)
- Based on administrative data submitted by hospitals

**Ontology Mapping:**
```
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE
end_event: PHYSICIAN
statistic_type: P90
patient_scope: MID_ACUITY (CTAS 2-5, excludes CTAS 1)
```

---

## Metric Ontology

### Time-to-Provider Definition

**Start Event: TRIAGE**
- Clock starts **after initial triage assessment**
- Patient has been categorized by acuity (CTAS 1-5)
- Does NOT include time spent in waiting room before triage

**End Event: PHYSICIAN**
- Clock stops when patient is **first assessed by a physician**
- Includes both MDs and potentially NPs/PAs (source-dependent)
- Does NOT include time waiting for test results or discharge

### Statistical Type Distinction

**POINT_ESTIMATE (Real-Time Data):**
- Single instantaneous measurement
- "Right now, the wait is X minutes"
- High temporal variability
- Suitable for: Deciding where to go right now

**P90 (Health Quality Ontario):**
- 90th percentile of historical distribution
- "90% of patients waited X minutes or less (last month)"
- Smoothed over time
- Suitable for: Understanding typical system performance

**Comparability:**
⚠️ **These are NOT directly comparable.** Mixing a point estimate with a P90 is scientifically invalid.

---

## Real-Time vs. Historical Data

### When to Use Real-Time Data

**Best For:**
- Patient decision-making: "Where should I go right now?"
- Live capacity monitoring
- Media reporting during flu season
- Public health crisis response

**Limitations:**
- High variability (can change minute-to-minute)
- Not suitable for performance benchmarking
- Doesn't capture variation across shift changes
- May not reflect patient experience for non-urgent cases

**Example:**
> "Ottawa Civic Hospital reports a 45-minute wait as of 2:15 PM. However, this is a point estimate and may not reflect your actual wait time."

### When to Use Historical Data (HQO)

**Best For:**
- Performance benchmarking
- Policy analysis
- Research and academic studies
- Hospital accountability

**Limitations:**
- Lag time (data is 1-3 months old)
- Not useful for immediate decisions
- Aggregation may hide variation

**Example:**
> "In January 2026, the P90 wait time at Ottawa Civic Hospital was 3.2 hours. This means 90% of patients waited 3.2 hours or less that month."

---

## Comparability Analysis

### Within-Ontario Comparisons

**Compatible Comparisons:**
1. **ER Watch ↔ ER Watch**: Directly comparable (same methodology)
2. **HQO ↔ HQO**: Directly comparable (same methodology)

**Incompatible Comparisons:**
3. **ER Watch ↔ HQO**: ❌ NOT comparable (point estimate vs. P90)

**Divergence Brief Example:**
> "⚠️ Methodology Divergence Warning: You are comparing a real-time point estimate (45 min) with a historical P90 statistic (192 min). These measure different things and cannot be directly compared. The P90 represents the 90th percentile over a full month, while the point estimate shows only the current wait."

### Cross-Province Comparisons

**Ontario (Real-Time) vs. Quebec:**
- **Compatible?** ⚠️ Partially
- **Differences:**
  - Ontario: POINT_ESTIMATE
  - Quebec: ROLLING_AVG
- **Verdict:** Both are real-time, but different statistics. Comparison should include divergence warning.

**Ontario (HQO) vs. Alberta:**
- **Compatible?** ✅ Yes (if Alberta uses P90)
- **Differences:** Minimal, both use P90 and TIME_TO_PROVIDER
- **Verdict:** Directly comparable

**Ontario (HQO) vs. British Columbia:**
- **Compatible?** ❌ No
- **Differences:**
  - Ontario: TIME_TO_PROVIDER (triage → physician)
  - BC: TOTAL_LOS (arrival → discharge)
- **Verdict:** Measuring different metrics entirely

---

## Technical Implementation

### Real-Time Scraper Configuration

```python
# Source configuration
SOURCE = Source(
    id="on-erwatch",
    name="Ontario Real-Time Wait Times",
    province="ON",
    methodology_url="https://www.hqontario.ca/System-Performance/Measuring-System-Performance",
    telehealth_name="Health Connect Ontario",
    telehealth_number="811",
    default_metric_family=MetricFamily.TIME_TO_PROVIDER,
    default_start_event=StartEvent.TRIAGE,
    default_end_event=EndEvent.PHYSICIAN,
    default_statistic_type=StatisticType.POINT_ESTIMATE,
)
```

### HQO Scraper Configuration

```python
# Source configuration
SOURCE = Source(
    id="on-hqo",
    name="Health Quality Ontario",
    province="ON",
    url="https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments",
    methodology_url="https://www.hqontario.ca/System-Performance/Measuring-System-Performance",
    telehealth_name="Health Connect Ontario",
    telehealth_number="811",
    default_metric_family=MetricFamily.TIME_TO_PROVIDER,
    default_start_event=StartEvent.TRIAGE,
    default_end_event=EndEvent.PHYSICIAN,
    default_statistic_type=StatisticType.P90,
)
```

### Measurement Creation

```python
measurement = Measurement(
    hospital_id="ca-on-ottawa-civic",
    value=45,  # minutes
    timestamp_utc=datetime.now(UTC),
    metric_family=MetricFamily.TIME_TO_PROVIDER,
    start_event=StartEvent.TRIAGE,
    end_event=EndEvent.PHYSICIAN,
    statistic_type=StatisticType.POINT_ESTIMATE,  # or P90 for HQO
    patient_scope=PatientScope.ALL,
    source_id="on-erwatch",
    raw_payload_hash=hash_payload(html),
    raw_payload_snippet=html[:200],
    parser_version="v1.0",
)
```

---

## Policy Context

### Health Connect Ontario (811)

Ontario's telehealth service for medical advice:
- **Phone:** 811
- **Service:** 24/7 nurse triage and advice
- **Languages:** 300+ languages via interpretation
- **Scope:** Can help determine if ED visit is necessary

**Integration:**
> When displaying Ontario hospital comparisons, show:
> "Before visiting an emergency department, consider calling Health Connect Ontario at 811 for medical advice."

### Triage System (CTAS)

Ontario uses the **Canadian Triage and Acuity Scale (CTAS)**:
1. **CTAS 1 (Resuscitation)**: Immediate
2. **CTAS 2 (Emergent)**: ≤15 minutes
3. **CTAS 3 (Urgent)**: ≤30 minutes
4. **CTAS 4 (Less Urgent)**: ≤60 minutes
5. **CTAS 5 (Non-Urgent)**: ≤120 minutes

**Implication:**
- Wait time data typically excludes CTAS 1 (most critical)
- CTAS 2-5 patients may wait longer than targets
- Patient scope should be tagged as `MID_ACUITY` for HQO data

---

## Comparability Decision Tree

```
┌─────────────────────────────────────┐
│ Are both measurements from Ontario? │
└──────────┬──────────────────────────┘
           │
     ┌─────┴─────┐
     │           │
    YES          NO → Check cross-province compatibility
     │
┌────┴────────────────────────────────┐
│ Are both from the same source?      │
│ (both ER Watch OR both HQO)         │
└────┬───────────────────┬────────────┘
     │                   │
    YES                 NO
     │                   │
   COMPATIBLE    ┌───────┴──────────┐
                 │ ER Watch vs HQO? │
                 └────┬─────────────┘
                      │
                 INCOMPATIBLE
                 Show divergence warning
```

---

## Validation Checklist

When adding a new Ontario hospital measurement:

- [ ] Hospital ID follows format `ca-on-{city}-{hospital-slug}`
- [ ] `source_id` matches the data source (`on-erwatch` or `on-hqo`)
- [ ] `metric_family` is `TIME_TO_PROVIDER`
- [ ] `start_event` is `TRIAGE`
- [ ] `end_event` is `PHYSICIAN`
- [ ] `statistic_type` is `POINT_ESTIMATE` (ER Watch) or `P90` (HQO)
- [ ] `patient_scope` is `ALL` (ER Watch) or `MID_ACUITY` (HQO)
- [ ] Timestamp is in UTC
- [ ] Raw payload is hashed (not stored in full)

---

## References

### Official Documentation

1. **Health Quality Ontario - ED Performance**
   https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments

2. **Ontario Ministry of Health - Wait Times**
   https://www.ontario.ca/page/time-spent-emergency-department

3. **Canadian Triage and Acuity Scale (CTAS)**
   https://caep.ca/wp-content/uploads/2017/06/module_1_slides_v2.5_2012.pdf

### Data Sources

4. **Ontario Real-Time Wait Time Service**
   Source ID: `on-erwatch`

5. **Health Connect Ontario**
   https://healthconnectontario.health.gov.on.ca/

### Academic Literature

6. Affleck, A., Parks, P., Drummond, A., Rowe, B. H., & Ovens, H. J. (2013). *Emergency department overcrowding and access block.* CJEM, 15(6), 359-370.

7. Hoot, N. R., & Aronsky, D. (2008). *Systematic review of emergency department crowding: causes, effects, and solutions.* Annals of Emergency Medicine, 52(2), 126-136.

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-01 | Initial methodology documentation |

---

## Appendix: Statistical Definitions

### P90 (90th Percentile)

**Definition:** The value below which 90% of observations fall.

**Example:**
If the P90 wait time is 180 minutes, it means:
- 90% of patients waited ≤180 minutes
- 10% of patients waited >180 minutes
- The median (P50) is typically much lower

**Why P90?**
- Captures the experience of most patients, including outliers
- More robust than mean (not affected by extreme values)
- Healthcare standard for performance measurement

### Point Estimate

**Definition:** A single measurement at a specific point in time.

**Example:**
"As of 2:15 PM, the wait time is 45 minutes."

**Limitations:**
- No measure of variability
- May not represent typical experience
- Subject to rapid change

---

*Last Updated: February 1, 2026*
*Maintained by: WaitTime Canada Research Team*
