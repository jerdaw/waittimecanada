# Québec Emergency-Department Wait-Time Methodology

## Status and Scope

This note distinguishes the public description of Québec's emergency-room
wait-time estimate from the legacy ontology tags currently assigned by this
project. It does not change the production source, stored measurements, or
runtime behavior. For the source review and the separate hourly CSV fields, see
[`docs/data-sources/quebec-research.md`](../../../docs/data-sources/quebec-research.md).

## What the Published Page Says

The [Québec.ca emergency-room situation page](https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec)
labels the displayed duration as an **estimated waiting time for non-priority
cases to see a doctor**. Its note says the estimate is based on clientele
arriving in the emergency-department waiting room, may vary quickly, and may
not reflect conditions when someone arrives.

The reviewed page does not specify a clock-start event such as registration or
triage, a clock-stop event beyond “to see a doctor,” the calculation formula,
whether the value is an average or point estimate, or an averaging window.
Those details should not be inferred from the displayed label. In particular,
the available page documentation does not substantiate a registration-to-
physician duration, a rolling-average calculation, or a numerical
registration-to-triage interval.

## Current Project Mapping (Legacy, Not Official Methodology)

The current scraper code assigns the wait estimate these ontology tags:

```text
metric_family: TIME_TO_PROVIDER
start_event: REGISTRATION
end_event: PHYSICIAN
statistic_type: ROLLING_AVG
patient_scope: ALL (Measurement model default; not set by the Québec scraper)
```

These values document current project behavior, not a method confirmed by
MSSS. The `ALL` patient scope conflicts with the public page's explicit
**non-priority** scope. The scraper does not set `patient_scope`; the
`Measurement` model supplies `ALL` as its default. This is a substantive
source-contract and data interpretation mismatch.

Changing the producer to `NON_PRIORITY` is not a seed-only or documentation-
only correction. The current `are_comparable()` check compares metric family,
start event, end event, and statistic type, but not patient scope. The
comparison service reads scope into its internal measurements but omits it
from the response's methodology fields; the divergence brief does not
currently identify a scope-only difference. Aggregation includes scope in its
method signature: mixed scopes produce an `ambiguous_methodology` gap, while a
homogeneous non-`ALL` group is rejected because the aggregate schema cannot
represent scope. A prospective correction therefore needs a separately
reviewed producer change plus scope-aware comparability and aggregate/reader
handling. Preserve existing `ALL` rows; do not silently relabel historical
measurements or change runtime behavior in this documentation update.

The scraper also assigns stretcher occupancy a separate
`STRETCHER_OCCUPANCY` metric with `UNKNOWN` start event and
`POINT_ESTIMATE` statistic. Its `PHYSICIAN` end-event value is an internal
placeholder, not a claim that an occupancy measurement ends at physician
contact. See the source note for distinctions among occupancy, current counts,
the prior-day length-of-stay fields, and the estimated wait duration.

## Comparability

Do not describe the Québec estimate as systematically longer or shorter than
another province's measure, assign a numerical adjustment, or claim direct
methodological equivalence based on the current tags alone. Such claims would
require source definitions for both measures, including patient scope, start
and end events, and statistic type. Until then, comparisons should identify
Québec's published value as a non-priority estimated wait to see a doctor and
make the undocumented calculation details explicit.

## Implementation Notes

The current `QuebecScraper` retrieves paginated HTML from the Québec.ca page,
parses the displayed wait estimate and stretcher-occupancy percentage, and
assigns the legacy tags listed above. These are implementation facts, not a
publisher guarantee that the underlying page mechanism is a stable API. The
page-based source and the separately published MSSS hourly CSV dataset have
different documented fields; counts and prior-day length-of-stay statistics
must not be presented as substitutes for the non-priority wait estimate.

## References

- [Québec.ca: Situation in emergency rooms in Québec](https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec)
- [Données Québec: MSSS hourly emergency-situation dataset](https://www.donneesquebec.ca/recherche/dataset/fichier-horaire-des-donnees-de-la-situation-a-l-urgence)
- [MSSS variable list and methodological notes for the hourly dataset (PDF)](https://www.donneesquebec.ca/recherche/dataset/d4541afe-9391-44bf-a78f-dae3c9cf1217/resource/968af2e2-8c0f-43d4-9f34-100bd8d295a7/download/listevariables_notesmetho_relevehoraireurgence_20230202.pdf)

*Reviewed: 2026-10-22. This is a documentation correction; no source, schema,
or stored data was changed.*
