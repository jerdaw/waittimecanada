# Downloadable Assets

This directory contains downloadable research assets for WaitTime Canada.

---

## Methodology Comparison Matrix

### Files

**Main Comparison:**
- **CSV**: `methodology-comparison.csv` (machine-readable)
- **HTML**: `methodology-comparison.html` (human-readable, web browser)

**Pairwise Comparability:**
- **CSV**: `methodology-pairwise-comparability.csv` (machine-readable)
- **HTML**: `methodology-pairwise-comparability.html` (human-readable, web browser)

### Purpose

These files document how Canadian provincial emergency department wait time methodologies differ across:
- **Ontario** (ON)
- **Alberta** (AB)
- **British Columbia** (BC)
- **Quebec** (QC)

### Content

#### Main Comparison Matrix

Shows for each province:
- **Province Code**: Two-letter abbreviation (ON, AB, BC, QC)
- **Source ID**: Database identifier for the data source
- **Metric Family**: What is measured (TIME_TO_PROVIDER)
- **Start Event**: When the wait time clock starts (TRIAGE vs REGISTRATION)
- **End Event**: When the wait time clock stops (PHYSICIAN)
- **Statistic Type**: How the value is calculated (POINT_ESTIMATE vs P90 vs ROLLING_AVG)
- **Update Frequency**: How often data refreshes
- **Notes**: Key insights and comparability implications

#### Pairwise Comparability Matrix

Shows for each province pair (6 combinations):
- **Province A & B**: Which provinces are being compared
- **Comparable?**: Yes/No/Partial assessment
- **Divergent Fields**: Which ontology dimensions differ
- **Notes**: Explanation of why comparison is/isn't valid

### Key Findings

**No province pair is fully comparable.**

- **Most Similar**: Ontario vs Alberta (both use TRIAGE → PHYSICIAN, POINT_ESTIMATE)
  - Same methodology when using real-time data
  - Both represent instantaneous snapshots

- **Most Distinct**: Quebec vs All Others
  - Uses REGISTRATION instead of TRIAGE (earlier start time)
  - Uses ROLLING_AVG instead of POINT_ESTIMATE/P90
  - Incomparable to all other provinces on two ontology dimensions

**Comparability Implications:**
- Quebec wait times systematically higher due to REGISTRATION start event
- BC's P90 (90th percentile) systematically higher than POINT_ESTIMATE
- Direct numeric comparison across provinces is scientifically invalid without ontology context

---

## Usage

### For Researchers

**CSV Files** - Load into analysis software:

```r
# R
data <- read.csv("methodology-comparison.csv")
```

```python
# Python
import pandas as pd
df = pd.read_csv("methodology-comparison.csv")
```

```sql
-- PostgreSQL (via COPY command)
COPY methodology_comparison FROM '/path/to/methodology-comparison.csv' CSV HEADER;
```

**HTML Files** - Open in web browser for formatted viewing

### For Developers

Reference these files when:
- Implementing comparability logic
- Generating divergence warnings
- Documenting cross-province differences
- Explaining why direct comparison may be invalid

### For Portfolio/Academic Use

**Citation:**
```
WaitTime Canada. (2026). Provincial Emergency Department Wait Time
Methodology Comparison. Retrieved from
https://github.com/jerdaw/waittimecanada/docs/assets/
```

**BibTeX:**
```bibtex
@misc{waittimecanada2026methodology,
  author = {Dawson, Jeremy},
  title = {Provincial Emergency Department Wait Time Methodology Comparison},
  year = {2026},
  publisher = {GitHub},
  journal = {WaitTime Canada},
  howpublished = {\url{https://github.com/jerdaw/waittimecanada}}
}
```

---

## Regenerating Assets

If provincial methodologies change, regenerate comparison matrices:

### Prerequisites

```bash
cd backend
source .venv/bin/activate
```

### Run Generator

```bash
python3 scripts/generate_methodology_comparison.py
```

**Output:**
```
✓ Generated: docs/assets/methodology-comparison.csv
✓ Generated: docs/assets/methodology-comparison.html
✓ Generated: docs/assets/methodology-pairwise-comparability.csv
✓ Generated: docs/assets/methodology-pairwise-comparability.html

✅ All methodology comparison assets generated successfully!
```

### Update Methodology Data

If a province's methodology changes:

1. **Update source data** in `backend/scripts/generate_methodology_comparison.py`:
   - Locate the `provinces` list
   - Modify the relevant province dictionary
   - Update `start_event`, `end_event`, `statistic_type`, etc.

2. **Regenerate assets** (run command above)

3. **Update documentation**:
   - `backend/docs/methodologies/{province}-methodology.md`
   - `backend/docs/methodologies/README.md`
   - `docs/API.md` (if API contracts changed)

4. **Create ADR** if methodology change is significant:
   - `docs/adr/NNNN-methodology-change-{province}.md`

---

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

If any ontology dimension differs, a **divergence brief** must be generated explaining why direct comparison is scientifically invalid.

---

## File Formats

### CSV Format

**methodology-comparison.csv:**
```csv
province,province_code,source_id,metric_family,start_event,end_event,statistic_type,update_frequency,data_source,notes
Ontario,ON,ontario-health,TIME_TO_PROVIDER,TRIAGE,PHYSICIAN,POINT_ESTIMATE,~15 min,Ontario Health (ER Watch),Real-time instantaneous wait times
...
```

**methodology-pairwise-comparability.csv:**
```csv
province_a,province_b,comparable,divergent_fields,notes
Ontario,Alberta,Partial,statistic_type matches (both POINT_ESTIMATE),Same ontology when using real-time Ontario data
...
```

### HTML Format

- Responsive design (works on mobile/desktop)
- Styled tables with hover effects
- Color-coded comparability indicators (green=yes, yellow=partial, red=no)
- Embedded ontology field definitions
- Citation information in footer

---

## Accessing Assets

### GitHub Repository

Direct links (raw files):
- CSV Main: `https://raw.githubusercontent.com/jerdaw/waittimecanada/main/docs/assets/methodology-comparison.csv`
- HTML Main: `https://raw.githubusercontent.com/jerdaw/waittimecanada/main/docs/assets/methodology-comparison.html`
- CSV Pairwise: `https://raw.githubusercontent.com/jerdaw/waittimecanada/main/docs/assets/methodology-pairwise-comparability.csv`
- HTML Pairwise: `https://raw.githubusercontent.com/jerdaw/waittimecanada/main/docs/assets/methodology-pairwise-comparability.html`

### Local Repository

```bash
cd /path/to/waittimecanada
open docs/assets/methodology-comparison.html  # macOS
xdg-open docs/assets/methodology-comparison.html  # Linux
start docs/assets/methodology-comparison.html  # Windows
```

---

## Version History

**v1.0.0** (2026-02-13)
- Initial release
- 4 provinces (ON, AB, BC, QC)
- 6 pairwise comparisons
- CSV and HTML formats

---

## Future Assets (Planned)

- [ ] Methodology timeline visualization (when provinces changed methodologies)
- [ ] Regional comparability matrix (within-province regional differences)
- [ ] Data quality metrics dashboard export
- [ ] Occupancy methodology comparison (when more provinces report occupancy)

---

## Questions?

For questions about these assets:
- **Methodology Details**: See `backend/docs/methodologies/README.md`
- **Comparability Logic**: See `CLAUDE.md` or `frontend/utils/comparability.ts`
- **Generator Script**: See `backend/scripts/generate_methodology_comparison.py`
- **Issues**: Open GitHub issue with `[methodology]` tag

---

**Last Updated:** 2026-02-13
**Generator Script:** `backend/scripts/generate_methodology_comparison.py`
**Source Data:** `backend/docs/methodologies/README.md`
