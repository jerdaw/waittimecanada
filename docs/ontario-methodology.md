# Ontario Wait Time Methodology

This note mirrors the maintained Ontario methodology record in
[`backend/docs/methodologies/ontario-methodology.md`](/home/jer/repos/waittimecanada/backend/docs/methodologies/ontario-methodology.md).

## Current Ontario Mapping

Wait Time Canada currently treats Ontario as:

```python
metric_family = MetricFamily.TIME_TO_PROVIDER
start_event = StartEvent.TRIAGE
end_event = EndEvent.PHYSICIAN
statistic_type = StatisticType.MEAN
patient_scope = PatientScope.ALL
```

## Source

- Source ID: `ontario-health`
- Source name: Health Quality Ontario
- Public URL: `https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments`
- Methodology URL: `https://www.hqontario.ca/System-Performance/Emergency-Department-Performance`

## What This Means

- Ontario is modeled as a published average wait time, not a point estimate.
- The reporting clock starts at triage, not registration.
- The reporting clock stops at first physician assessment.

## Cross-Province Consequences

- Ontario vs Alberta: same event boundaries, different statistic type (`MEAN` vs `POINT_ESTIMATE`)
- Ontario vs British Columbia: same event boundaries, different statistic type (`MEAN` vs `P90`)
- Ontario vs Quebec: different start event and statistic type (`TRIAGE/MEAN` vs `REGISTRATION/ROLLING_AVG`)

No active cross-province pair is directly comparable under the four-dimension
ontology rule.

## Telehealth

- Ontario routing: `Health811`
- Phone: `811`

## Reference

For the full maintained document, implementation snippet, and validation
checklist, use the backend methodology note linked above.
