# Milestone 26: Strategic Documentation & Robustness

**Goal**: Formalize system knowledge through comprehensive documentation and enhance core logic reliability with property-based testing. This directly supports "Scholar" (methodological rigor) and "Professional" (reliability) competencies.

## User Review Required

> [!NOTE]
> This milestone focuses on high-value documentation and testing infrastructure. No user-facing feature changes are planned.

## Proposed Changes

### Documentation (Scholar & Professional)

#### [NEW] [docs/reference/data-dictionary.md](file:///home/jer/localsync/waittimecanada/docs/reference/data-dictionary.md)
*   Comprehensive reference of all 9 database tables.
*   Detailed schema for core models (`Measurement`, `Hospital`, `Source`).
*   Definition of strict ontology enums (`MetricFamily`, `StartEvent`, `EndEvent`, `StatisticType`).

#### [NEW] [docs/architecture/data-flow.md](file:///home/jer/localsync/waittimecanada/docs/architecture/data-flow.md)
*   Mermaid diagrams visualizing the end-to-end data journey.
*   **Scraper Pipeline**: Source HTML -> Parser -> Raw Measurement -> Hash Validation -> Database.
*   **Aggregation Pipeline**: Raw Measurements -> SQL Aggregation -> Monthly/Weekly Stats.
*   **Comparability Logic**: Measurement A vs B -> Ontology Check -> Divergence Brief.

#### [MODIFY] [CONTRIBUTING.md](file:///home/jer/localsync/waittimecanada/CONTRIBUTING.md)
*   Add links to the new Data Dictionary and Data Flow docs in the "Before You Start" section.

### Backend Testing (Robustness)

#### [MODIFY] [backend/pyproject.toml](file:///home/jer/localsync/waittimecanada/backend/pyproject.toml)
*   Add `hypothesis` to `[project.optional-dependencies] dev`.

#### [NEW] [backend/tests/unit/core/test_comparability_properties.py](file:///home/jer/localsync/waittimecanada/backend/tests/unit/core/test_comparability_properties.py)
*   Property-based tests for `are_comparable` and `generate_divergence_brief` using Hypothesis.
*   **Properties to Verify**:
    *   **Reflexivity**: `are_comparable(m, m)` is always `True`.
    *   **Symmetry**: `are_comparable(a, b) == are_comparable(b, a)`.
    *   **Transitivity**: If `a ~ b` and `b ~ c`, then `a ~ c`.
    *   **Consistency**: `generate_divergence_brief(a, b)` returns `None` IF AND ONLY IF `are_comparable(a, b)` is `True`.

## Verification Plan

### Automated Tests
1.  **Install new dependencies**:
    ```bash
    pip install -e 'backend[dev]'
    ```
2.  **Run Property Tests**:
    ```bash
    pytest backend/tests/unit/core/test_comparability_properties.py
    ```
3.  **Run Documentation Check**:
    ```bash
    # Verify no broken links
    bash scripts/check-docs.sh
    ```

### Manual Verification
1.  **Review Documentation**:
    *   Open `docs/reference/data-dictionary.md` and verify table schemas match `backend/src/waittime/core/models.py`.
    *   Open `docs/architecture/data-flow.md` and verify diagrams render correctly on GitHub (preview).
