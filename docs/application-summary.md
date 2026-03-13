# Wait Time Canada - Application Summary

## Primary Summary (Applications)

Wait Time Canada is a Health Systems Observatory I built to audit Canadian emergency department wait-time data across provinces. Rather than treating all wait numbers as directly comparable, the platform applies a strict metric ontology to each measurement (metric family, start event, end event, statistic type) and warns users when cross-hospital comparisons are methodologically invalid. For example, Ontario commonly reports P90 triage-to-physician time, while Quebec reports rolling-average registration-to-physician time; those metrics answer different operational questions and should not be compared as equivalent. The project combines full-stack technical execution (Python scrapers, PostgreSQL, Next.js analytics/dashboard tooling) with clinical defensibility principles: transparent limitations, explicit provenance, and safety-oriented communication for patients and decision-makers.

---

## 60-Second Version (Interviews)

I built Wait Time Canada because most ER wait tools compare numbers that are not methodologically equivalent. My platform tags each measurement with structured ontology metadata and automatically blocks invalid comparisons through divergence warnings. Technically, it includes scraper pipelines, database constraints, analytics endpoints, and operational monitoring workflows. Conceptually, it demonstrates that health informatics should prioritize methodological clarity over superficial comparability.

---

## Technical Summary (Engineering Context)

Wait Time Canada is a full-stack system using Python-based provincial scrapers, PostgreSQL with ontology-aligned constraints, and a Next.js frontend/API layer. The architecture emphasizes:

- Ontology-enforced measurement tagging for comparability analysis
- Verification workflows to prevent accidental publication of unverified facilities
- Aggregation + analytics services for trends, benchmarking, and regional views
- Operational safeguards via heartbeat checks and production readiness/smoke workflows

The key design choice is to audit and expose heterogeneity rather than normalize it away.

---

## Limitations

- Current scraper freshness reflects an hourly GitHub Actions cadence rather than continuous ingestion.
- Methodology labels are inferred from public provincial documentation and can lag unannounced source-side reporting changes.
- The platform can only surface what provinces publish; it cannot detect unreported overcrowding or internal flow constraints.
- Equity analysis is currently implemented for Ontario only and should not be generalized to other provinces without province-specific validation.

---

## CanMEDS Mapping Summary

- `Scholar`: methodology ontology design, comparability reasoning, and transparent assumptions
- `Professional`: defensible communication of uncertainty and invalid comparisons
- `Leader`: end-to-end technical execution from data acquisition to operational monitoring
- `Health Advocate`: patient-facing clarity about what wait-time numbers do and do not mean

---

Last Updated: 2026-03-12
