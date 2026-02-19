# LinkedIn Launch Post - Wait Time Canada

## Final Recommended Post (Ready To Publish)

ER wait times across Canada are often presented as if they are directly comparable. They are not.

I built **Wait Time Canada** as a Health Systems Observatory to audit methodology differences instead of hiding them.

Why this matters:
- Ontario and Quebec can report similar-looking wait numbers that represent different measurement methods.
- A direct comparison can be statistically invalid, even when both values are in minutes.

What the platform does:
- Tags each measurement with explicit methodology metadata (start event, end event, statistic type, metric family).
- Detects when comparisons are invalid and shows a clear divergence warning.
- Provides transparent methods/governance context so users know what they are actually comparing.

Core stack:
- Python scrapers + PostgreSQL + Next.js
- Operational checks: scraper cron, heartbeat monitoring, production readiness and smoke workflows

This project reflects how I approach health informatics: methodological rigor, transparent limitations, and patient-facing clarity.

GitHub: https://github.com/jerdaw/waittimecanada
Live demo: [INSERT_PRODUCTION_URL]

#HealthcareInnovation #CanadianHealthcare #HealthInformatics #DataTransparency #EmergencyMedicine #MedEd

---

## Publish Checklist

- Replace `[INSERT_PRODUCTION_URL]` with the live URL.
- Attach 2-3 screenshots from `docs/screenshot-guide.md`.
- Add alt text for each image.
- Post from your personal account and pin it for portfolio visibility.

---

## Optional Short Version

I built **Wait Time Canada** to make ER wait-time methodology differences explicit across provinces.

Instead of normalizing incompatible metrics, it tags each measurement with ontology metadata and warns users when direct comparisons are invalid.

That means clearer interpretation, better data stewardship, and fewer misleading comparisons.

GitHub: https://github.com/jerdaw/waittimecanada
Live demo: [INSERT_PRODUCTION_URL]
