# Ontario Wait Time Methodology

> [!WARNING]
> **Ontario methodology revalidation required.** Wait Time Canada currently
> uses `TRIAGE -> PHYSICIAN` as legacy implementation tags. Ontario Health now
> defines the indicator from triage or registration, whichever is earlier, to
> the first assessment by a doctor, nurse practitioner, physician assistant,
> or dentist. The current ontology cannot encode the composite start exactly.
>
> Official definition:
> <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>

This note summarizes the maintained record in
`backend/docs/methodologies/ontario-methodology.md`.

## Current Repository Mapping

```python
metric_family = MetricFamily.TIME_TO_PROVIDER
start_event = StartEvent.TRIAGE
end_event = EndEvent.PHYSICIAN
statistic_type = StatisticType.MEAN
patient_scope = PatientScope.ALL
```

These values describe current implementation behavior. The `MEAN` statistic and
metric family remain consistent with the official indicator, but the event tags
are not an exact official definition.

## Official Definition

- Start: triage or registration, whichever is earlier.
- End: first assessment by a doctor, nurse practitioner, physician
  assistant, or dentist.
- Statistic: average.
- Reporting cadence: monthly.

## Comparability Consequences

Direct cross-province comparison remains invalid.

No active cross-province pair should be treated as directly comparable. The
current platform's divergence behavior remains the safe outcome, but its legacy
Ontario event tags must not be used to claim exact event-boundary alignment or
mismatch until revalidation is complete.

Full resolution requires one owner-reviewed decision covering ontology values,
historical measurement migration or versioning, source metadata, divergence
briefs, and frontend methodology labels.

## Source And Telehealth

- Source ID: `ontario-health`
- Public data and methodology URL:
  <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>
- Ontario public context:
  <https://www.ontario.ca/page/time-spent-emergency-department>
- Telehealth: `Health811`, phone `811`
