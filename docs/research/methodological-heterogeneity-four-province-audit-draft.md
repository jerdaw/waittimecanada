# Methodological Heterogeneity in Canadian Emergency Department Wait-Time Reporting: A Four-Province Audit

**Status:** Paused for Ontario methodology revalidation; not ready for external review
**Date:** 2026-03-28
**Scope:** Ontario, Quebec, Alberta, British Columbia

> This draft is intended to support informed review before the report is treated as a finalized public scholarly artifact. It summarizes methodology differences already documented in the live platform and repository.

> [!WARNING]
> **Ontario methodology revalidation required.** Ontario Health currently
> defines its indicator from triage or registration, whichever is earlier, to
> the first qualifying provider assessment. The repository's
> `TRIAGE -> PHYSICIAN` values are legacy implementation tags and cannot be
> treated as an exact official definition. Source-level Ontario conclusions in
> this draft are paused until the ontology and historical-data treatment are
> resolved together.
>
> Official definition:
> <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>

## Executive Summary

Wait Time Canada audits publicly reported emergency department wait-time data
across four Canadian provinces: Ontario, Quebec, Alberta, and British Columbia.
The current platform blocks direct cross-province comparisons. This draft must
not elevate that implementation result into a fully source-validated
four-province methodology conclusion until Ontario is revalidated.

Across the four live provincial source inventories, the platform currently
observes four distinct statistic tags: `MEAN`, `ROLLING_AVG`, `POINT_ESTIMATE`,
and `P90`. Quebec also remains the only live province in the platform that
publishes stretcher occupancy as a public metric. As of **2026-03-28**, all
**6 of 6** cross-province source pairs fail direct comparability on the
platform's current ontology tags. The Ontario event tags require revalidation,
so this is a platform-state result rather than a final source-level finding.

The practical implication is that a public wait number is not meaningful in isolation. Interpretation requires source-specific context about where the clock starts, where it stops, how the reported value is summarized, and how frequently it is updated.

## Background

Public emergency department wait-time tools are often read as if they provide a common national measure of "how long the ER wait is." In practice, provinces publish operational data through different reporting systems, built for different institutional needs, with different methodological choices. A number expressed in minutes can look comparable while still measuring a different segment of the patient journey or using a different statistical summary.

Wait Time Canada was built around the claim that public availability does not automatically imply comparability. Rather than normalizing provincial values into a single scale, the platform tags each measurement with a strict metric ontology and blocks invalid comparisons with divergence warnings.

## The Measurement Problem

For the purposes of this audit, direct comparability requires alignment on four ontology fields:

1. `metric_family`
2. `start_event`
3. `end_event`
4. `statistic_type`

Two public measurements are directly comparable only if those fields match. If they do not, a numeric difference may reflect methodology rather than performance.

This matters because emergency department reporting choices encode substantive assumptions:

- A `REGISTRATION` start event includes pre-triage administrative time that a `TRIAGE` start event excludes.
- A `POINT_ESTIMATE` captures a single operational moment, while a `P90` summarizes the experience of most patients over a time window.
- A `ROLLING_AVG` smooths variation over time and may dampen abrupt operational changes.
- A `MEAN` can be more sensitive to skew than a percentile-based statistic.

These are not cosmetic differences. They change what the published number actually means.

## Methods

This audit uses the live Wait Time Canada source inventory and methodology mappings for the four currently active provinces. The project ingests public data from official provincial or health-authority sources and assigns ontology tags based on publicly documented methodology and source behavior. The platform does not attempt to correct, normalize, or translate one province's value into another's.

The four live provincial sources used in this draft are:

- Ontario: Health Quality Ontario / Ontario Health public emergency wait-time reporting
- Quebec: MSSS emergency room situation portal
- Alberta: Alberta Health Services wait-times portal
- British Columbia: PHSA / `edwaittimes.ca`

As of **2026-03-28**, the repository documents **393 hospital records** across the four active provincial source inventories, with **8,804 measurements** in the most recent 24-hour quality window and **273 hospitals** showing at least one reported measurement in that same window.

## Four-Province Methodology Summary

| Province | Primary public metric in live platform | Start event | End event | Statistic type | Operational posture |
| --- | --- | --- | --- | --- | --- |
| Ontario | `TIME_TO_PROVIDER` | `TRIAGE`* | `PHYSICIAN`* | `MEAN` | Repository event tags pending official-source revalidation |
| Quebec | `TIME_TO_PROVIDER` | `REGISTRATION` | `PHYSICIAN` | `ROLLING_AVG` | Rolling average estimate |
| Alberta | `TIME_TO_PROVIDER` | `TRIAGE` | `PHYSICIAN` | `POINT_ESTIMATE` | Real-time current estimate |
| British Columbia | `TIME_TO_PROVIDER` | `TRIAGE` | `PHYSICIAN` | `P90` | Percentile-based public wait metric |

This table describes current platform tags. The asterisked Ontario event values
do not exactly represent the official composite start and qualifying-provider
endpoint. The table can explain current platform divergence, but not a final
source-level Ontario comparison.

## Findings

### 1. Cross-province direct comparability currently fails in every live source pair

As verified in the current platform state on **2026-03-28**, all **6 of 6** cross-province source pairs fail direct comparability on the current ontology tags.

This remains a strong platform-safety finding: the application does not permit
any cross-province pair to be treated as directly comparable. External
methodology claims must wait for Ontario revalidation.

### 2. Current repository tags distinguish Quebec on two dimensions

Quebec is the only live province currently tagged with `REGISTRATION` rather
than `TRIAGE`. That implementation difference contributes to platform
divergence. It must not be read as proof that Ontario's official indicator
excludes registration: Ontario uses triage or registration, whichever is
earlier.

Quebec also reports a `ROLLING_AVG`, while the other provinces currently expose `MEAN`, `POINT_ESTIMATE`, or `P90`. This makes Quebec the clearest case of double divergence:

- different start event
- different statistic type

### 3. Alberta and British Columbia show that matching start/end events is not enough

Alberta and British Columbia both use `TRIAGE` to `PHYSICIAN` in the current ontology mapping, but they still fail direct comparability because Alberta publishes a `POINT_ESTIMATE` while British Columbia publishes `P90`.

This matters because it demonstrates a narrower but still critical point: even when two provinces are talking about the same segment of the patient journey, the summary statistic can still make direct comparison invalid.

### 4. Quebec remains the only province with live stretcher occupancy in the platform

The platform's current live occupancy surface is Quebec-only. That asymmetry matters for both public interpretation and future analytics. Occupancy adds operational depth, but it also means the live system has unequal metric breadth by province.

This is not a flaw to be hidden. It is part of the public reporting landscape being audited.

### 5. The Ottawa-Gatineau corridor is the clearest narrative case

The Ottawa-Gatineau pair remains the most intuitive demonstration of the platform's core thesis. Users could reasonably expect two hospitals across a provincial border in the same functional urban corridor to be comparable. They are not.

For the production pair used in the linked case study, the current repository
tags are:

- Ottawa reports `TRIAGE` to `PHYSICIAN` with `MEAN`
- Gatineau reports `REGISTRATION` to `PHYSICIAN` with `ROLLING_AVG`

The platform correctly prevents a direct comparison. A final explanation of
the event-boundary difference requires the Ontario revalidation decision.

## Equity Layer Interpretation

The Ontario equity layer should be interpreted as descriptive and exploratory, not causal.

That point is important enough to state explicitly because equity overlays can be rhetorically powerful while still being methodologically limited. Any apparent relationship between neighborhood income context and hospital wait-time patterns in the current platform must be treated cautiously for at least four reasons:

1. **Ecological fallacy**
   Census-tract context is not the same thing as an individual patient's socioeconomic situation.

2. **Temporal mismatch**
   The platform's live operational measurements and the underlying income data do not come from the same time period.

3. **Unmeasured confounding**
   Hospital size, referral role, case mix, geography, transport patterns, and health-system design all shape reported waits.

4. **Administrative geography mismatch**
   Census tracts and hospital service catchments are not equivalent units.

The equity layer is still valuable. It helps make access-pattern questions visible and supports more disciplined future inquiry. But the limitation is the finding: the current platform can describe patterns worth investigating, not prove why they exist.

## Implications

### For patients and the public

The safest takeaway from a cross-province difference is often not "one hospital is faster." It is "these systems may be publishing different measures."

### For journalists and policy users

Reported wait numbers should be interpreted with methodology attached. Cross-jurisdiction stories that omit metric definitions risk turning reporting artifacts into performance claims.

### For health-system reporting

The current public landscape would benefit from stronger methodological standardization, or at minimum from much more explicit public metadata about start events, endpoints, statistics, windows, and exclusions.

## Limitations

This draft has several important limitations:

- It is an audit of publicly reported measures, not an audit of internal hospital operations.
- Provincial methodology labels are inferred from current public documentation and source behavior; undocumented source changes could alter the interpretation.
- The Ontario event tags do not exactly encode the current official composite
  definition; Ontario-specific source-level findings are paused pending an
  ontology and historical-data decision.
- Coverage is limited to the four live provinces in the current platform.
- The platform's own quality window metrics are operational snapshots, not long-horizon epidemiologic findings.
- This draft has not yet had an external public-interest methodology review.

## Conclusion

The main conclusion of this audit is not that one province performs better than another. It is that public emergency department wait-time reporting across the four live provinces is methodologically heterogeneous in ways that materially limit direct comparison.

That is exactly why a system like Wait Time Canada should audit methodology first and ranking logic last. Transparent incomparability is more responsible than false precision.

## Related Internal Artifacts

- Ottawa-Gatineau case study: `docs/case-studies/ottawa-gatineau-divergence.md`
- README methodology findings: `README.md`
- Ontario methodology notes: `docs/ontario-methodology.md`
- Alberta methodology notes: `backend/docs/methodologies/alberta-methodology.md`
- BC methodology notes: `backend/docs/methodologies/bc-methodology.md`
- Quebec methodology notes: `backend/docs/methodologies/quebec-methodology.md`

## External Source URLs

- Ontario emergency department wait-time context: <https://www.ontario.ca/page/time-spent-emergency-department>
- Ontario Health public wait-time reporting: <https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>
- Quebec emergency room situation portal: <https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec>
- Alberta Health Services wait-times portal: <https://www.albertahealthservices.ca/waittimes/Page14230.aspx>
- BC emergency department wait-times portal: <https://edwaittimes.ca/>
