# Provincial Methodology Documentation

This directory contains comprehensive methodology documentation for each Canadian province's emergency department wait time reporting system.

## Purpose

These documents serve multiple purposes:

1. **Scholar Narrative**: Demonstrates understanding of research methodology and comparability
2. **Transparency**: Explains to users why direct comparisons may be invalid
3. **Developer Reference**: Guides implementation of scrapers and ontology tagging
4. **Stakeholder Communication**: Shows health authorities we understand their data

## Available Documentation

### Ontario
- **File**: `ontario-methodology.md`
- **Status**: Complete
- **Data Sources**: ER Watch (real-time), Health Quality Ontario (historical)
- **Key Insight**: Two distinct methodologies (POINT_ESTIMATE vs P90) that are incomparable

### Alberta
- **File**: `alberta-methodology.md`
- **Status**: Complete
- **Data Sources**: Alberta Health Services Wait Times Portal
- **Key Insight**: POINT_ESTIMATE (real-time, updated every 2 minutes), TRIAGE to PHYSICIAN

### British Columbia
- **File**: `bc-methodology.md`
- **Status**: Complete
- **Data Sources**: BC PHSA via edwaittimes.ca
- **Key Insight**: P90 statistic (90th percentile), TRIAGE to PHYSICIAN, 5-minute refresh

### Quebec
- **File**: `quebec-methodology.md`
- **Status**: Complete
- **Data Sources**: MSSS Emergency Room Situation Portal
- **Key Insight**: Uses REGISTRATION start event (not TRIAGE) and ROLLING_AVG statistic - incomparable to all other provinces on two ontology dimensions

### Manitoba (Future)
- **Status**: Not yet tracked
- **Data Sources**: Shared Health Manitoba
- **Expected Differences**: Different statistic_type

## Cross-Province Comparability Summary

All four active provinces measure TIME_TO_PROVIDER but differ in start event and statistic type:

| Province | Source ID | Start Event | End Event | Statistic Type | Update Freq |
|----------|-----------|-------------|-----------|----------------|-------------|
| **Ontario** | ontario-health | TRIAGE | PHYSICIAN | POINT_ESTIMATE | ~15 min |
| **Alberta** | alberta-ahs | TRIAGE | PHYSICIAN | POINT_ESTIMATE | ~2 min |
| **BC** | bc-phsa | TRIAGE | PHYSICIAN | P90 | ~5 min |
| **Quebec** | quebec-msss | REGISTRATION | PHYSICIAN | ROLLING_AVG | Periodic |

### Pairwise Comparability

| Pair | Comparable? | Divergent Fields | Notes |
|------|-------------|------------------|-------|
| **ON vs AB** | Partial | statistic_type matches (both POINT_ESTIMATE) | Same ontology when using real-time Ontario data |
| **ON vs BC** | No | statistic_type (POINT_ESTIMATE vs P90) | Same start/end events but different statistics |
| **ON vs QC** | No | start_event + statistic_type | Two dimensions differ; Quebec times systematically higher |
| **AB vs BC** | No | statistic_type (POINT_ESTIMATE vs P90) | Same start/end events but different statistics |
| **AB vs QC** | No | start_event + statistic_type | Two dimensions differ |
| **BC vs QC** | No | start_event + statistic_type | Two dimensions differ |

**Key Takeaway:** No province pair is fully comparable. Ontario and Alberta share the closest methodology (both TRIAGE -> PHYSICIAN, POINT_ESTIMATE), but even these represent instantaneous snapshots that may vary by measurement timing. Quebec is the most methodologically distinct province.

## Methodology Document Structure

Each provincial methodology document should follow this structure:

```markdown
# {Province} Emergency Department Wait Time Methodology

## Executive Summary
- Key findings
- Main differences from other provinces
- Comparability summary

## Data Sources
- Primary sources
- Update frequencies
- Coverage

## Metric Ontology
- metric_family
- start_event
- end_event
- statistic_type
- patient_scope

## Comparability Analysis
- Within-province comparisons
- Cross-province comparisons
- Divergence scenarios

## Technical Implementation
- Source configuration
- Scraper examples
- Measurement creation

## Policy Context
- Telehealth information
- Triage systems
- Provincial guidelines

## References
- Official documentation
- Data source URLs
- Academic literature
```

## Using These Documents

### For Frontend Display

When showing a hospital's methodology on the frontend:

```typescript
// Example: Link to methodology
<Link href="/methods?province=ON">
  Learn about Ontario's methodology →
</Link>
```

### For Divergence Warnings

When comparing hospitals with different methodologies:

```typescript
if (!comparable) {
  const brief = generateDivergenceBrief(measurementA, measurementB);
  // brief references the methodology differences
  // Link to provincial methodology docs for details
}
```

### For Developer Onboarding

New developers should:
1. Read `ontario-methodology.md` as the reference example
2. Review the ontology section carefully
3. Understand why comparability matters
4. Implement scrapers following the documented patterns

## Ontology Quick Reference

### Metric Families

- **TIME_TO_PROVIDER**: Triage/registration → first physician assessment
- **TOTAL_LOS**: Arrival → discharge (complete ED stay)
- **STRETCHER_OCCUPANCY**: % of stretchers in use (capacity metric)

### Start Events

- **TRIAGE**: After triage assessment (Ontario, Alberta)
- **REGISTRATION**: After administrative registration (Quebec)
- **DOOR**: From physical arrival (some US systems)
- **UNKNOWN**: When methodology is unclear

### End Events

- **PHYSICIAN**: First physician assessment
- **PROVIDER**: First provider (MD, NP, or PA)
- **DISCHARGE**: Patient leaves ED
- **FIRST_ASSESSMENT**: First clinical assessment (any provider)

### Statistic Types

- **POINT_ESTIMATE**: Current/instantaneous measurement
- **P90**: 90th percentile of distribution
- **MEDIAN**: 50th percentile
- **MEAN**: Arithmetic average
- **ROLLING_AVG**: Moving average over time window
- **ALGORITHMIC**: Calculated via complex model

### Patient Scopes

- **ALL**: All patients regardless of acuity
- **MID_ACUITY**: Excludes most critical (typically CTAS 2-5)
- **NON_PRIORITY**: Low-acuity only (typically CTAS 4-5)

## Comparability Rules

Two measurements are **directly comparable** if and only if:

```python
comparable = (
    measurement_a.metric_family == measurement_b.metric_family and
    measurement_a.start_event == measurement_b.start_event and
    measurement_a.end_event == measurement_b.end_event and
    measurement_a.statistic_type == measurement_b.statistic_type
)
```

If any dimension differs, a **divergence brief** must be generated explaining why direct comparison is scientifically invalid.

## Contributing

When adding a new province's methodology:

1. Create `{province-lowercase}-methodology.md` in this directory
2. Follow the standard structure outlined above
3. Include specific examples from that province
4. Document all data sources with URLs
5. Explain telehealth routing (811 or equivalent)
6. Map to our standardized ontology
7. Identify cross-province comparability issues
8. Update this README with the new province

## Validation

Before publishing methodology documentation:

- [ ] All URLs tested and accessible
- [ ] Ontology mapping validated against actual data
- [ ] Comparability analysis includes real examples
- [ ] Telehealth information verified
- [ ] References include official government sources
- [ ] Code examples tested
- [ ] Peer reviewed by team member

## Academic Context

These methodology documents support the **Scholar** competency in the CanMEDS framework:

> "Demonstrates understanding of research methodology, statistical concepts, and the importance of comparability when analyzing health systems data. Recognizes when direct comparison is scientifically invalid and communicates this to stakeholders."

By documenting methodology differences transparently, we demonstrate:
- Critical appraisal of data sources
- Understanding of measurement validity
- Commitment to scientific integrity
- Respect for provincial autonomy in data reporting

## Questions?

For methodology questions, consult:
1. This README
2. The specific provincial methodology document
3. The `/methods` page on the frontend
4. The `AGENTS.md` file in the repository root

---

*Last Updated: February 11, 2026*
