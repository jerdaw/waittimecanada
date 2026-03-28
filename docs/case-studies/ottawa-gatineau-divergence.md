# Ottawa–Gatineau Methodology Divergence Case Study

## Summary

Ottawa and Gatineau are one of the clearest examples of why published emergency department wait times cannot be compared safely across provincial systems without methodology review first.

The hospitals are geographically close and sit on opposite sides of a provincial boundary, but the reported wait times are generated using different clocks and different statistics. That means the numbers are not answering the same question.

## Verified Pair

The following production pair was verified on **2026-03-28**:

- **Ottawa Hospital The Civic Site** (`ca-on-ottawa-hospital-the-civic-site`)
- **Hopital De Gatineau** (`ca-qc-hopital-de-gatineau`)

Verification basis:

- Both hospitals were present in the live hospital feed on `wait-time.ca`
- The live comparison path returned a methodology divergence for the pair after constraining comparison to the latest `TIME_TO_PROVIDER` measurement

## Why This Corridor Matters

Ottawa and Gatineau are a useful case because they sit in the same cross-border urban region. From a public-information perspective, they are exactly the kind of pair that a user might expect to compare directly. That expectation is understandable, but the underlying reported metrics are different enough that a direct comparison would be misleading.

## Methodology Comparison

| Dimension | Ottawa (Ontario current public feed) | Gatineau (Quebec MSSS portal) |
|-----------|--------------------------------------|-------------------------------|
| Metric family | `TIME_TO_PROVIDER` | `TIME_TO_PROVIDER` |
| Start event | `TRIAGE` | `REGISTRATION` |
| End event | `PHYSICIAN` | `PHYSICIAN` |
| Statistic type | `MEAN` | `ROLLING_AVG` |
| Source posture | Current public Ontario wait-time feed | Current public MSSS emergency room portal |

## Why Direct Comparison Is Invalid

Two ontology dimensions differ in a way that materially changes what the number means:

1. **Start event mismatch**

Ontario starts the clock at `TRIAGE`. Quebec starts the clock at `REGISTRATION`. Quebec therefore includes the registration-to-triage interval that Ontario excludes. Even if two hospitals had the same underlying physician-assessment performance, Quebec's reported number could still appear longer because the clock starts earlier.

2. **Statistic mismatch**

Ontario's current public feed reports a `MEAN`. Quebec reports a `ROLLING_AVG`. Those are not interchangeable summary statistics. A rolling average smooths over time and may dampen short-term swings; a mean reflects a different aggregation choice. Without a shared statistic definition and time window, the numbers are not methodologically aligned.

## What Wait Time Canada Does With This

Wait Time Canada treats this pair as **not directly comparable**. The platform's role is not to normalize the mismatch away or to guess at a correction factor. Its role is to expose the mismatch clearly so users do not interpret the two values as equivalent measures of the same thing.

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
- Quebec emergency room situation portal: <https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec>
- Wait Time Canada Ontario methodology notes: [../../backend/docs/methodologies/ontario-methodology.md](/home/jer/repos/waittimecanada/backend/docs/methodologies/ontario-methodology.md)
- Wait Time Canada Quebec methodology notes: [../../backend/docs/methodologies/quebec-methodology.md](/home/jer/repos/waittimecanada/backend/docs/methodologies/quebec-methodology.md)

## Date of Verification

Verified against the live production system on **2026-03-28**.
