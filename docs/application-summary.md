# WaitTime Canada - Application Summary

## One-Paragraph Summary (For Applications)

WaitTime Canada is a Health Systems Observatory I built to audit Canadian emergency room wait time data across provinces. Unlike typical wait time aggregators, it uses a "metric ontology" to tag each measurement with its methodology (start event, end event, statistic type, patient scope) and automatically warns users when comparing hospitals that use incompatible measurement methods. For example, Ontario reports the 90th percentile time from triage to physician, while Quebec reports the rolling average from registration to physician—these answer fundamentally different clinical questions and cannot be directly compared. The project demonstrates my approach to healthcare informatics: rigorous methodology, transparent limitations, and a commitment to helping patients make evidence-based decisions even when that means clearly communicating what we don't know. The live platform serves 213 Ontario hospitals with plans for pan-Canadian expansion, combining full-stack technical implementation (Python, PostgreSQL, Next.js) with clinical thinking about data stewardship and patient safety.

---

## Alternative Versions (For Different Contexts)

### Short Version (100 words)

WaitTime Canada is a Health Systems Observatory that audits Canadian ER wait time data using a strict metric ontology. The platform tags every measurement with methodology metadata (start event, end event, statistic type) and warns users when comparing incompatible data. For instance, Ontario's 90th percentile triage-to-physician time cannot be directly compared with Quebec's rolling average registration-to-physician time. This project demonstrates rigorous research methodology, clinical defensibility, and transparent communication of limitations—showing that good healthcare informatics means being explicit about what we don't know, not just what we do.

### Technical Version (For Computer Science Applications)

WaitTime Canada is a full-stack healthcare data auditing platform built with Python 3.12, Neon PostgreSQL 17, and Next.js 14. The system enforces a 4-dimension metric ontology (metric_family, start_event, end_event, statistic_type) at the database level using CHECK constraints, enabling automatic comparability detection across provincial data sources. When methodologies diverge, the platform generates structured "divergence briefs" explaining why direct comparison is statistically invalid. The architecture includes automated scrapers (BeautifulSoup + Playwright), a verification queue preventing bad data publication, and comprehensive testing (278 total tests, 100% frontend pass rate). Currently serving 213 Ontario hospitals with real-time data, demonstrating both technical competence and domain-specific clinical thinking.

### CanMEDS-Focused Version (For Medical Schools)

WaitTime Canada demonstrates multiple CanMEDS competencies applied to healthcare informatics. As a **Scholar**, I researched provincial methodologies and designed a formal ontology system for measurement classification. As a **Professional**, I implemented clinical defensibility through methodology transparency and verification workflows that prevent incorrect data from reaching patients. As a **Health Advocate**, I highlighted access barriers by making methodology differences explicit rather than hiding them in normalized aggregates. As a **Leader**, I executed a multi-phase development roadmap from research through production deployment. The project shows that effective health informatics requires both technical skills and clinical judgment—knowing when to say "these numbers cannot be compared" is as important as the ability to compare them.

---

## Key Talking Points (For Interviews)

### Why This Project?

"I noticed that ER wait time apps present Ontario and Quebec data side-by-side without explaining that they measure fundamentally different things. Ontario reports the 90th percentile time from triage to seeing a physician, while Quebec reports the rolling average from registration to seeing a physician. These answer different clinical questions—one tells you about worst-case waits, the other about average experience. I built WaitTime Canada to make these methodology differences transparent rather than hiding them through false normalization."

### What Makes It Different?

"Most wait time aggregators try to normalize heterogeneous data into a single number. We do the opposite—we audit the data and warn users when comparisons are invalid. Every measurement is tagged with methodology metadata, and the system automatically detects when two hospitals use incompatible measurement approaches. Instead of showing '90 minutes' at both hospitals, we explain: 'Hospital A reports 90th percentile triage-to-physician; Hospital B reports rolling average registration-to-physician. Direct comparison is not scientifically valid.'"

### Technical Challenges

"The biggest challenge was designing an ontology system that's both comprehensive and enforceable. I needed to capture four dimensions of methodology variation (metric family, start and end events, statistic type) while ensuring data integrity at the database level. I used PostgreSQL CHECK constraints to prevent invalid ontology combinations and implemented a comparability service that performs 4-way equality checks. The system has 100% test coverage on the comparison logic because that's the core clinical safety feature—we never want to tell users two hospitals are comparable when they're not."

### What I Learned

"This project taught me that good health informatics isn't about maximizing data availability—it's about maximizing clarity about data limitations. Sometimes the right answer is 'this comparison is invalid' rather than showing a number. I also learned the importance of verification workflows; the system requires manual approval before publishing new hospitals because automated geocoding isn't perfect and displaying incorrect data could lead patients to the wrong facility. These are clinical safety considerations dressed up as technical features."

---

## Portfolio Integration

### GitHub README Badge Section

Add these badges to make the repo more professional:

```markdown
[![Tests](https://img.shields.io/badge/tests-278%20passing-success)](./tests)
[![Coverage](https://img.shields.io/badge/coverage-57%25-yellow)](./coverage)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE)
[![Python](https://img.shields.io/badge/python-3.12-blue)](./backend)
[![Next.js](https://img.shields.io/badge/next.js-14-black)](./frontend)
```

### Repository Topics

Add these topics to GitHub:
- `healthcare`
- `canada`
- `emergency-medicine`
- `data-auditing`
- `nextjs`
- `postgresql`
- `python`
- `mapbox`
- `wait-times`
- `health-informatics`
- `ontology`
- `canmeds`
- `portfolio-project`

### Repository Description

```
A clinically defensible Health Systems Observatory for Canadian ER wait times. Audits methodology differences across provinces and prevents invalid comparisons.
```

---

## Frequently Asked Questions (For Applications)

### Q: Why not just normalize the data?

"Normalizing heterogeneous methodologies creates the illusion of comparability where none exists. If Ontario measures 90th percentile and Quebec measures rolling average, there's no valid mathematical transformation that makes them equivalent—they answer different clinical questions. Normalization would hide important information that patients and policymakers need to make informed decisions. Our approach makes the differences explicit."

### Q: How is this clinically relevant?

"Triage-based measurements tell you about access to initial assessment, while registration-based measurements include administrative delays. 90th percentile metrics reveal worst-case scenarios important for capacity planning, while averages show typical experience. When patients compare hospitals for care, they need to know whether they're comparing apples to apples. Similarly, policymakers analyzing system performance need to understand what different metrics actually measure before making resource allocation decisions."

### Q: What about future expansion?

"The architecture is designed for pan-Canadian scalability. Each new province is just another row in the sources table with its own ontology tags. The comparability logic automatically detects methodology matches and mismatches. I've already documented Alberta's expected methodology (triage-to-physician, point estimate) which differs from both Ontario (triage-to-physician, 90th percentile) and Quebec (registration-to-physician, rolling average). This proves the system can handle genuine methodological heterogeneity."

---

## Media Kit (If Needed)

### Project Title
WaitTime Canada: A Health Systems Observatory for Emergency Wait Times

### Tagline
Auditing methodology, not just aggregating data

### Elevator Pitch
WaitTime Canada makes Canadian ER wait time methodologies transparent. Instead of normalizing incompatible data, we tag every measurement with metadata and warn users when direct comparisons are statistically invalid.

### Target Audience
1. Patients comparing hospitals for care
2. Healthcare policymakers analyzing system performance
3. Medical students/residents learning about health informatics
4. Data scientists interested in healthcare applications
5. Medical school admissions committees

### Key Differentiators
- Only platform that audits methodology rather than aggregating data
- Automatic divergence detection across 4 ontology dimensions
- Clinical defensibility through transparency, not normalization
- Open source with comprehensive documentation

---

## Contact Information

**Developer:** Jeremy Dawson
**Email:** jeremyjdawson@gmail.com
**LinkedIn:** https://linkedin.com/in/jeremyjdawson
**GitHub:** https://github.com/jerdaw/waittimecanada
**Project:** Pre-medical portfolio (physician-innovator track)

---

*Last Updated: February 4, 2026*
