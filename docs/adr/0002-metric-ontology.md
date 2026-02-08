# 2. Implement Strict Metric Ontology System

Date: 2024-12-26

Status: Accepted

Deciders: Project Team

Technical Story: Core architectural decision for data model

## Context and Problem Statement

Canadian provinces report emergency room wait times using different methodologies:
- Alberta: Triage-to-Physician (90th percentile)
- Quebec: Registration-to-Physician (Rolling average)
- Manitoba: Algorithmic estimate (proprietary calculation)

**Problem:** Users will naturally assume these values are directly comparable and make inappropriate comparisons between provinces, leading to misinterpretation and potential poor healthcare decisions.

How do we store heterogeneous wait time data in a way that enables transparency about comparability without attempting to normalize incomparable metrics?

## Decision Drivers

* **Data Integrity** - Never misrepresent or artificially normalize provincial data
* **Scientific Rigor** - Enable researchers to understand exact methodology
* **User Safety** - Prevent misinterpretation that could lead to poor healthcare decisions
* **Portfolio Value** - Demonstrate understanding of research methodology ("Scholar" narrative)
* **Maintainability** - Clear schema that prevents future drift

## Considered Options

1. **Strict Metric Ontology** - Tag every measurement with 4-field ontology (metric_family, start_event, end_event, statistic_type)
2. **Normalization Approach** - Convert all measurements to standardized metric
3. **Free-Text Methodology** - Store methodology as unstructured text
4. **Province-Specific Tables** - Separate tables per province

## Decision Outcome

Chosen option: "Strict Metric Ontology", because:
- Only option that maintains data integrity while enabling comparability analysis
- Provides scientific rigor required for research use
- Enables automatic generation of "divergence briefs" when data is incomparable
- Demonstrates deep understanding of research methodology (key portfolio value)
- Scales to new provinces without schema changes

### Positive Consequences

* **Automatic Comparability Detection** - Can programmatically determine if two measurements are comparable
* **Divergence Brief Generation** - System automatically explains why data is incomparable
* **Database-Level Enforcement** - PostgreSQL enums prevent invalid ontology values
* **Research-Grade Data** - Researchers can query by exact methodology
* **Future-Proof** - Adding new provinces/metrics doesn't require schema changes
* **Portfolio Differentiation** - Showcases "Physician-Innovator" competency

### Negative Consequences

* **Initial Complexity** - Requires understanding of each province's methodology
* **Cannot Average Across Provinces** - No "national average" wait time possible
* **Scraper Complexity** - Each scraper must correctly tag ontology fields
* **UI Complexity** - Must show methodology warnings prominently

## Pros and Cons of the Options

### Strict Metric Ontology

Example schema:
```sql
CREATE TABLE measurements (
    metric_family TEXT NOT NULL,    -- TIME_TO_PROVIDER, TOTAL_LOS
    start_event TEXT NOT NULL,      -- TRIAGE, REGISTRATION, DOOR
    end_event TEXT NOT NULL,        -- PHYSICIAN, PROVIDER, DISCHARGE
    statistic_type TEXT NOT NULL    -- P90, MEAN, ALGORITHMIC
);
```

Comparability logic:
```python
comparable = (
    A.metric_family == B.metric_family and
    A.start_event == B.start_event and
    A.end_event == B.end_event and
    A.statistic_type == B.statistic_type
)
```

* Good, because maintains exact provincial methodology
* Good, because enables automatic comparability detection
* Good, because database-enforced via enums (no drift)
* Good, because demonstrates research methodology understanding
* Bad, because cannot provide "average Canadian wait time"
* Bad, because each scraper must tag correctly

### Normalization Approach

Convert all measurements to standard metric (e.g., "Triage-to-Physician P90")

* Good, because enables direct cross-province comparison
* Good, because simpler UI (just show wait time)
* Good, because can calculate national averages
* Bad, because scientifically invalid (cannot convert Registration→Triage accurately)
* Bad, because loses original methodology information
* Bad, because creates false precision
* Bad, because misrepresents provincial data

### Free-Text Methodology

Store methodology as unstructured text field

* Good, because flexible (any methodology)
* Good, because preserves original description
* Bad, because cannot programmatically determine comparability
* Bad, because no enforcement (can drift over time)
* Bad, because difficult to query/filter
* Bad, because requires manual interpretation

### Province-Specific Tables

Separate tables: `measurements_ab`, `measurements_qc`, etc.

* Good, because each province can have custom schema
* Good, because no cross-province confusion
* Bad, because cannot query across provinces
* Bad, because schema changes required for each new province
* Bad, because violates DRY principle
* Bad, because complex cross-province features

## Links

* [Related to] [Architecture Database Guide](../architecture/database.md) - PostgreSQL enums chosen for ontology enforcement
* [Refines] Strategic plan "Comparability Boolean" section

## Additional Information

### Ontology Field Definitions

**metric_family** - What is being measured?
- `TIME_TO_PROVIDER`: Wait to see doctor/nurse
- `TOTAL_LOS`: Total length of stay in ED
- `STRETCHER_OCCUPANCY`: Current ED occupancy rate

**start_event** - When does the clock start?
- `TRIAGE`: After initial triage assessment
- `REGISTRATION`: After administrative check-in
- `DOOR`: Upon physical arrival at ED
- `UNKNOWN`: Source doesn't specify

**end_event** - When does the clock stop?
- `PHYSICIAN`: Physician initial assessment
- `PROVIDER`: Any provider (doctor, NP, PA)
- `DISCHARGE`: Patient leaves ED
- `FIRST_ASSESSMENT`: First clinical contact (any role)

**statistic_type** - How is value calculated?
- `P90`: 90th percentile (CIHI standard)
- `MEDIAN`: 50th percentile
- `MEAN`: Average
- `ROLLING_AVG`: Moving average (window unspecified)
- `ALGORITHMIC`: Proprietary calculation
- `POINT_ESTIMATE`: Current real-time value

### Implementation Notes

1. Use PostgreSQL enums for strict enforcement
2. Create `CHECK` constraints as fallback
3. Pydantic models validate on insert
4. Frontend shows methodology warnings when comparing incomparable data
5. Auto-researcher generates "divergence briefs" for incomparable pairs

### Real-World Example

**Alberta (AHS):**
```python
{
    "metric_family": "TIME_TO_PROVIDER",
    "start_event": "TRIAGE",
    "end_event": "PHYSICIAN",
    "statistic_type": "P90"
}
```

**Quebec (MSSS):**
```python
{
    "metric_family": "TIME_TO_PROVIDER",
    "start_event": "REGISTRATION",
    "end_event": "PHYSICIAN",
    "statistic_type": "MEAN"
}
```

**Comparability Result:** `False` (different start_event AND statistic_type)

**Divergence Brief:**
> ⚠️ **Methodology Divergence:** Alberta reports 90th percentile Triage-to-Physician time, meaning 90% of patients are seen within the reported time. Quebec reports average Registration-to-Physician time, which starts the clock later and uses a different statistical measure. Direct comparison is scientifically invalid.

### References

- CIHI Emergency Department Performance Measures: https://www.cihi.ca/en/indicators/
- Alberta AHS Methodology: https://www.albertahealthservices.ca/waittimes/waittimes.aspx
- Quebec MSSS Methodology: https://www.quebec.ca/sante/urgences
