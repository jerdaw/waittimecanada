# Ottawa–Gatineau Methodology Divergence Case Study

**Status:** Paused for Ontario methodology revalidation

> [!WARNING]
> **Ontario methodology revalidation required.** The production behavior below
> was verified on 2026-03-28, but the Ontario event-boundary interpretation is
> not current source-faithful evidence. Ontario Health defines the indicator
> from triage or registration, whichever is earlier, to the first assessment
> by a doctor, nurse practitioner, physician assistant, or dentist. The
> repository still uses `TRIAGE -> PHYSICIAN` as
> legacy implementation tags.
>
> Official definition:
> <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>

## Summary

Ottawa and Gatineau are one of the clearest examples of why published emergency department wait times cannot be compared safely across provincial systems without methodology review first.

The hospitals are geographically close and sit on opposite sides of a
provincial boundary. The current platform tags and statistics do not support a
direct performance comparison, and the Ontario tags require revalidation
before this case study can make a source-level event-boundary claim.

## Verified Pair

The following production pair was verified on **2026-03-28**:

- **Ottawa Hospital The Civic Site** (`ca-on-ottawa-hospital-the-civic-site`)
- **Hopital De Gatineau** (`ca-qc-hopital-de-gatineau`)

Verification basis:

- Both hospitals were present in the live hospital feed on `wait-time.ca`
- The live comparison path returned a methodology divergence for the pair after constraining comparison to the latest `TIME_TO_PROVIDER` measurement

## Why This Corridor Matters

Ottawa and Gatineau are a useful case because they sit in the same cross-border urban region. From a public-information perspective, they are exactly the kind of pair that a user might expect to compare directly. That expectation is understandable, but the underlying reported metrics are different enough that a direct comparison would be misleading.

## Current Platform Mapping

The table records implementation tags observed in the platform on 2026-03-28.
It does not claim that Ontario's event tags exactly encode the current official
indicator.

| Dimension | Ottawa (current repository tags) | Gatineau (Quebec MSSS portal) |
|-----------|--------------------------------------|-------------------------------|
| Metric family | `TIME_TO_PROVIDER` | `TIME_TO_PROVIDER` |
| Start event | `TRIAGE` | `REGISTRATION` |
| End event | `PHYSICIAN` | `PHYSICIAN` |
| Statistic type | `MEAN` | `ROLLING_AVG` |
| Source posture | Official source; event tags pending revalidation | Current public MSSS emergency room portal |

Ontario's official definition uses triage or registration, whichever is
earlier, through the first qualifying provider assessment. The present ontology
does not encode that composite start exactly.

## Why Direct Comparison Is Invalid

Direct cross-province comparison remains invalid.

Two independent safeguards prevent a direct performance conclusion:

1. **Ontario source-fidelity gap**

The repository currently tags Ontario as `TRIAGE -> PHYSICIAN`, while the
official definition uses a composite start and a broader qualifying-provider
endpoint. Until the ontology and historical measurements are resolved
together, the Ontario side cannot support an exact event-boundary comparison.

2. **Statistic mismatch**

Ontario's public indicator reports a `MEAN`. Quebec reports a `ROLLING_AVG` in
the current repository mapping. Those are not interchangeable summary
statistics. Without a shared statistic definition and time window, the numbers
are not methodologically aligned even apart from the Ontario fidelity gap.

## What Wait Time Canada Does With This

Wait Time Canada treats this pair as **not directly comparable**. That remains
the safe outcome. The platform's role is not to normalize the mismatch away or
guess at a correction factor, especially while one source mapping is under
revalidation.

This is a good example of the project's core thesis:

- public health-system data can be useful and important
- public availability does not automatically mean cross-jurisdiction comparability
- transparent limitations are part of responsible communication, not a weakness

## Public and Policy Implication

If a user sees one number in Ottawa and another in Gatineau, the safe conclusion is **not** "one hospital is faster." The safe conclusion is that the two systems are publishing different operational measures.

For patients, clinicians, journalists, and policy users, the practical implication is the same: methodology has to be part of the interpretation. A cross-border region makes that especially visible, but the same logic applies nationally.

## What A Valid Comparison Would Require

A stronger cross-border comparison would require all of the following:

- the same metric family
- the same start event
- the same end event
- the same statistic type
- similar update cadence and aggregation window
- clear documentation of patient scope and exclusions

Without that alignment, a numeric difference is not a valid performance conclusion.

## Sources

- Ontario public wait-time context: <https://www.ontario.ca/page/time-spent-emergency-department>
- Ontario Health indicator definition: <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>
- Quebec emergency room situation portal: <https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec>
- Wait Time Canada Ontario methodology notes: `backend/docs/methodologies/ontario-methodology.md`
- Wait Time Canada Quebec methodology notes: `backend/docs/methodologies/quebec-methodology.md`

## Date of Verification

Production pair and platform divergence verified on **2026-03-28**. Ontario
methodology containment revalidated against the official source on
**2026-07-10**. This case study should not return to current verified status
until the Ontario ontology and historical-data decision is complete.
