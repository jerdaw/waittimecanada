# Ontario Emergency Department Wait Time Methodology

> [!WARNING]
> **Ontario methodology revalidation required.** The repository currently uses
> `TRIAGE -> PHYSICIAN` as legacy implementation tags. The official Ontario
> Health indicator instead starts at triage or registration, whichever is
> earlier, and ends at the first qualifying provider assessment. The current
> ontology cannot represent that composite start exactly. Until the ontology
> and historical-data treatment are resolved together, do not treat the
> repository event tags as an exact transcription of the official definition.
>
> Official definition:
> <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>

## Executive Summary

Wait Time Canada currently implements the maintained `ontario-health` source
with these tags:

- metric family: `TIME_TO_PROVIDER`
- start event: `TRIAGE`
- end event: `PHYSICIAN`
- statistic type: `MEAN`
- patient scope: `ALL`
- refresh posture: historical public reporting, not a live operational feed

The `MEAN` statistic and `TIME_TO_PROVIDER` family remain consistent with the
current official indicator. The event tags are implementation values pending
revalidation, not source-faithful definitions.

## Official Indicator Definition

Ontario Health currently defines the average time to first assessment as:

- **Start:** triage or registration, whichever is earlier.
- **End:** the first qualifying assessment by a doctor, nurse practitioner,
  physician assistant, or dentist.
- **Statistic:** average time, calculated from total wait time divided by the
  count of eligible emergency department visits.
- **Scope:** all eligible unscheduled emergency department visits, subject to
  the published inclusion and exclusion rules.
- **Refresh:** monthly.

This definition was revalidated against the official indicator page on
2026-07-10.

## Current Repository Mapping

```text
metric_family: TIME_TO_PROVIDER
start_event: TRIAGE
end_event: PHYSICIAN
statistic_type: MEAN
patient_scope: ALL
mapping_status: LEGACY_IMPLEMENTATION_TAGS_PENDING_REVALIDATION
```

This block documents current behavior only. It is not the recommended target
mapping for the official composite indicator.

### Fidelity Gap

The existing `StartEvent` values can represent `TRIAGE` or `REGISTRATION`, but
not "whichever is earlier." The existing `EndEvent.PROVIDER` may be closer to
the official endpoint than `PHYSICIAN`, but changing only that field would not
resolve the composite start, historical measurements, or versioning. A partial
tag change would create a misleading split in one source's measurement history.

## Source Definition

- Source ID: `ontario-health`
- Current display name: `Health Quality Ontario`
- Public data and methodology URL:
  <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>
- Public context:
  <https://www.ontario.ca/page/time-spent-emergency-department>
- Telehealth routing: `Health811` (`811`)

The source catalog still contains the legacy display name, event tags, and
methodology URL. Those runtime/data changes are intentionally outside this
containment pass because they require a migration and compatibility decision.

## Comparability Notes

### Within Ontario

Ontario records using the same current repository tags are implementation-tag
compatible with one another. That does not prove that the event fields exactly
describe the current official indicator.

### Cross-Province Comparisons

No direct cross-province performance conclusion is valid while:

1. the provincial statistic types differ; or
2. the Ontario event mapping does not faithfully encode its official source.

The current platform still produces divergence for Ontario versus Alberta,
British Columbia, and Quebec. That safety outcome must be preserved. Public
documents must not claim exact event-boundary alignment or mismatch from the
legacy Ontario tags until revalidation is complete.

### Safe Divergence Brief

> Methodology Divergence: Direct comparison is invalid. Ontario event tags
> require source-fidelity revalidation, and the provincial reporting statistics
> or event definitions are not fully aligned.

## Implementation Reference

Current behavior is defined by:

- `backend/data/sources/ontario-health.json`
- `backend/src/waittime/scrapers/ontario.py`
- source seeding and existing database rows

The current implementation continues to emit `TRIAGE`, `PHYSICIAN`, and
`MEAN`. Do not change one surface in isolation. The follow-up must address:

- the composite start representation;
- the broader provider endpoint;
- existing source rows and historical measurements;
- parser/source versioning;
- comparability and divergence text; and
- frontend methodology labels.

## Validation Checklist

- The documentation distinguishes official methodology from repository tags.
- The official Ontario Health definition and URL are current.
- Current runtime tags remain unchanged during containment.
- Cross-province direct comparison remains blocked.
- A migration/versioning plan exists before any runtime mapping change.
- Telehealth routing remains `Health811` / `811`.

## References

1. [Ontario Health — Time Spent in Emergency Departments](https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments)
2. [Ontario — Time Spent in the Emergency Department](https://www.ontario.ca/page/time-spent-emergency-department)
3. Wait Time Canada structured reference:
   `backend/docs/methodologies/ontario-reference.json`
4. Wait Time Canada source catalog:
   `backend/data/sources/ontario-health.json`

Last revalidated: 2026-07-10
