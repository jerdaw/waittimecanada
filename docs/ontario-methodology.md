# Ontario Wait Time Methodology

**Source:** Health Quality Ontario (HQOntario)
**URL:** https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments
**Last Verified:** 2026-01-30

---

## Metric Ontology Tags

Per ADR-0002 (Metric Ontology System), Ontario measurements must be tagged as follows:

```python
metric_family = MetricFamily.TIME_TO_PROVIDER
start_event = StartEvent.TRIAGE
end_event = EndEvent.PHYSICIAN
statistic_type = StatisticType.MEAN
patient_scope = PatientScope.ALL
```

---

## Detailed Breakdown

### What is Measured?

**Metric:** Time to First Assessment by Doctor in Emergency

**Definition:** The elapsed time from when a patient completes triage until they are first assessed by a physician (MD).

**Excludes:**
- Nurse practitioners (NPs)
- Physician assistants (PAs)
- Other healthcare providers

**Must be:** Licensed medical doctor (MD)

---

### When Does the Clock Start?

**Start Event:** `TRIAGE`

**Definition:** After the patient completes the initial triage assessment by a registered nurse.

**Not:**
- Upon arrival at the hospital doors (DOOR)
- Upon registration at reception (REGISTRATION)

**Rationale:** Aligns with CIHI NACRS (National Ambulatory Care Reporting System) standard for emergency department metrics.

---

### When Does the Clock Stop?

**End Event:** `PHYSICIAN`

**Definition:** At the moment the physician (MD) begins their first assessment of the patient.

**Not:**
- When any provider (NP/PA) sees the patient (that would be PROVIDER)
- When patient receives first clinical intervention (that would be FIRST_ASSESSMENT)
- When patient is discharged (that would be DISCHARGE)

**Specificity:** This is the most common ED metric in Canada, following CIHI standards.

---

### How is the Value Calculated?

**Statistic Type:** `MEAN` (Average)

**Definition:** Simple arithmetic mean of all wait times for the reporting period.

**Not:**
- P90 (90th percentile) - Alberta uses this
- Median (50th percentile)
- Rolling average (Quebec uses this)
- Real-time estimate (BC uses this)

**Formula:** `sum(all_wait_times) / count(patients)`

**Reporting Period:** Monthly average (data updated monthly, not real-time)

---

### Which Patients are Included?

**Patient Scope:** `ALL`

**Definition:** All emergency department patients regardless of:
- CTAS acuity level (includes levels 1-5)
- Age (pediatric and adult)
- Admission status (admitted vs discharged)
- Presenting complaint

**Excludes:**
- Patients who leave without being seen (LWBS)
- Patients who leave against medical advice before assessment (LAMA)

---

## Comparability Analysis

### Comparable With:

**Same Methodology:**
- Other Ontario hospitals (directly comparable)
- Any province using TRIAGE → PHYSICIAN with MEAN

**Example:** If another province reports "Average wait from triage to doctor assessment", they are comparable.

### NOT Comparable With:

**Different Start Event:**
- ❌ Quebec: Uses REGISTRATION → PHYSICIAN
  - Quebec's clock starts earlier, so values will be higher
  - **Divergence:** ~15-30 min difference on average

**Different Statistic Type:**
- ❌ Alberta: Uses TRIAGE → PHYSICIAN with P90
  - P90 is typically 30-50% higher than MEAN
  - **Divergence:** Comparing Ontario's average to Alberta's 90th percentile is scientifically invalid

**Different End Event:**
- ❌ If a province uses TRIAGE → PROVIDER (includes NPs/PAs)
  - Provider assessment typically happens 10-20 min sooner
  - **Divergence:** Understates physician wait time

---

## Data Source Details

**Publisher:** Health Quality Ontario (HQO)
**Authority:** Provincial health quality agency
**Update Frequency:** Monthly
**Historical Data:** Available back to 2014
**Coverage:** ~140 hospitals across Ontario

**Methodology Documentation:**
- https://www.hqontario.ca/System-Performance/Emergency-Department-Performance
- Based on CIHI NACRS standards

**Quality Indicators:**
- ✅ Audited by CIHI
- ✅ Standardized data collection across hospitals
- ✅ Publicly reported with transparency

---

## Implementation Notes

### For Scraper (`ontario.py`):

```python
def _create_measurement(self, hospital_id: str, hours: float, ...) -> Measurement:
    """Create Ontario measurement with correct ontology."""
    return Measurement(
        hospital_id=hospital_id,
        value=hours * 60,  # Convert hours to minutes
        metric_family=MetricFamily.TIME_TO_PROVIDER,
        start_event=StartEvent.TRIAGE,
        end_event=EndEvent.PHYSICIAN,
        statistic_type=StatisticType.MEAN,  # KEY: Not P90
        patient_scope=PatientScope.ALL,
        source_id="ontario-health",
        ...
    )
```

### For Frontend (Divergence Warnings):

When comparing Ontario to Quebec:
```
⚠️ Methodology Divergence Detected

Ontario: Average wait from TRIAGE to PHYSICIAN
Quebec: Average wait from REGISTRATION to PHYSICIAN

Quebec includes ~15-30 min of pre-triage registration time.
Direct comparison may understate Quebec wait times relative to Ontario.
```

When comparing Ontario to Alberta:
```
⚠️ Methodology Divergence Detected

Ontario: MEAN (Average) wait time
Alberta: P90 (90th percentile) wait time

P90 represents the worst 10% of cases, typically 30-50% higher than average.
Alberta's values will appear worse but represent different patient experiences.
```

---

## References

1. CIHI NACRS Data Quality Documentation (2024)
2. Health Quality Ontario - ED Performance Indicators
3. Ontario Ministry of Health - ED Wait Time Standards
4. Canadian Association of Emergency Physicians (CAEP) - Wait Time Guidelines

---

**Status:** ✅ Methodology Documented (Phase 0 Complete)

**Next:** Implement `OntarioScraper` with these ontology tags (Phase 1)
