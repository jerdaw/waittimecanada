# Ontario Emergency Department Wait Time Methodology

## Executive Summary

Wait Time Canada currently models Ontario from the maintained
`ontario-health` source definition and the live Ontario scraper:

- source: Health Quality Ontario
- ontology: `TIME_TO_PROVIDER`, `TRIAGE -> PHYSICIAN`, `MEAN`
- patient scope: `ALL`
- refresh posture: historical public reporting, not a live operational feed

This means Ontario should be interpreted as a published average wait-time
measure, not as a point estimate and not as a percentile metric.

## Source Definition

- Source ID: `ontario-health`
- Display name: Health Quality Ontario
- URL: `https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments`
- Methodology URL: `https://www.hqontario.ca/System-Performance/Emergency-Department-Performance`
- Telehealth routing: `Health811` (`811`)

## Ontology Mapping

```text
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE
end_event: PHYSICIAN
statistic_type: MEAN
patient_scope: ALL
```

### Interpretation

#### Metric Family: `TIME_TO_PROVIDER`

Ontario reports the time until a patient is first seen by a physician in the
emergency department. This is not a total length-of-stay metric.

#### Start Event: `TRIAGE`

The reporting clock begins after triage assessment, not at registration and not
at the front door.

#### End Event: `PHYSICIAN`

The reporting clock stops at first physician assessment.

#### Statistic Type: `MEAN`

Ontario is currently documented in this repository as an arithmetic mean of the
relevant wait-time observations for the reporting period. This is distinct from:

- Alberta's `POINT_ESTIMATE`
- British Columbia's `P90`
- Quebec's `ROLLING_AVG`

#### Patient Scope: `ALL`

Ontario measurements in this repository are tagged to the full reporting cohort
rather than a narrowed acuity subset.

## Comparability Notes

### Within Ontario

Ontario-to-Ontario comparisons are directly comparable when they come from the
same maintained source definition because all four ontology dimensions match.

### Ontario vs Alberta

- shared dimensions: `TIME_TO_PROVIDER`, `TRIAGE`, `PHYSICIAN`
- divergence: `MEAN` vs `POINT_ESTIMATE`
- verdict: partial alignment only, not directly comparable

### Ontario vs British Columbia

- shared dimensions: `TIME_TO_PROVIDER`, `TRIAGE`, `PHYSICIAN`
- divergence: `MEAN` vs `P90`
- verdict: partial alignment only, not directly comparable

### Ontario vs Quebec

- shared dimensions: `TIME_TO_PROVIDER`, `PHYSICIAN`
- divergence: `TRIAGE` vs `REGISTRATION`, `MEAN` vs `ROLLING_AVG`
- verdict: partial alignment only, not directly comparable

### Example Divergence Brief

> Methodology Divergence: Direct comparison is scientifically invalid. Different
> start points: TRIAGE vs REGISTRATION. Different statistics: MEAN vs
> ROLLING_AVG.

## Implementation Reference

The Ontario scraper and source factory are the canonical implementation points.

```python
SOURCE = Source(
    id="ontario-health",
    name="Health Quality Ontario",
    province="ON",
    url="https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments",
    methodology_url="https://www.hqontario.ca/System-Performance/Emergency-Department-Performance",
    telehealth_name="Health811",
    telehealth_number="811",
    default_metric_family=MetricFamily.TIME_TO_PROVIDER,
    default_start_event=StartEvent.TRIAGE,
    default_end_event=EndEvent.PHYSICIAN,
    default_statistic_type=StatisticType.MEAN,
)
```

Ontario measurements should be created with the same ontology values:

```python
measurement = Measurement(
    hospital_id="ca-on-example",
    value=180,
    metric_family=MetricFamily.TIME_TO_PROVIDER,
    start_event=StartEvent.TRIAGE,
    end_event=EndEvent.PHYSICIAN,
    statistic_type=StatisticType.MEAN,
    patient_scope=PatientScope.ALL,
    source_id="ontario-health",
    raw_payload_hash="...",
)
```

## Validation Checklist

- source ID is `ontario-health`
- `metric_family` is `TIME_TO_PROVIDER`
- `start_event` is `TRIAGE`
- `end_event` is `PHYSICIAN`
- `statistic_type` is `MEAN`
- `patient_scope` is `ALL`
- telehealth routing remains `Health811` / `811`

## References

1. Health Quality Ontario ED performance reporting
2. Ontario emergency department performance methodology page
3. Wait Time Canada source catalog: `backend/data/sources/ontario-health.json`

Last updated: 2026-04-16
