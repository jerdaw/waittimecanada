# Admissions Strengthening Plan (OMSAS / CanMEDS)

**Created:** 2026-02-25
**Status:** Active
**Scope:** Real-world credibility, external validation, and public-facing artifacts to strengthen the project's presentation for Ontario medical school admissions.

---

## Current State Assessment

**Purpose:** Wait Time Canada is a Health Systems Observatory that audits methodological inconsistencies in Canadian ER wait-time reporting across 4 provinces (ON, QC, AB, BC), using a strict metric ontology to tag every measurement and auto-block invalid cross-hospital comparisons via divergence warnings.

**Target users:** Framed as a medical school portfolio project, but has genuine utility for patients making ER decisions, ER clinicians understanding reporting context, and health policy researchers studying interprovincial heterogeneity.

**Maturity:** Engineering is highly mature — 33 milestones complete, 777+ tests, full CI/CD, OpenAPI spec, MkDocs deployment, French i18n, Ontario equity layer with 2021 StatsCan census tracts, divergence briefs, historical occupancy trends, structured failure taxonomy.

**Evidence of use:** Still minimal. There are no completed stakeholder interviews yet, no published testimonials, no user analytics, no external citations, and no GitHub community signals. The placeholder Zenodo DOI has been removed from README, but no real DOI has been registered yet. The important launch gate is now cleared: `https://wait-time.ca` is live with valid HTTPS and verified redirects, so Phase B can focus on public-facing follow-through rather than infrastructure rescue.

**Biggest gaps:**
1. No meaningful public engagement yet — the canonical URL is live, but launch artifacts and stakeholder interaction still lag the engineering maturity.
2. No real-world human engagement — zero completed stakeholder conversations.
3. No published academic or semi-academic output.
4. Placeholder DOI undermines the "citable software" claim.
5. The health equity analysis covers only Ontario — the Advocate claim is narrow.
6. The README still lacks a clear public-facing mission, equity/EDIA posture, and stewardship statement that explains why the project matters beyond its engineering.

---

## Guiding Principles

1. **Phase A items are all pre-deployment.** No blockers. Start immediately.
2. **Stakeholder interview (#A4) and README mission/equity/stewardship section (#A1) are the two highest-ROI actions.** A1 is delivered. A4 remains high-value but should stay parked until explicitly activated.
3. **The technical report (C1) is the anchor scholarly artifact.** The case study, findings, and equity interpretation feed into it.
4. **Don't publicize anything you can't defend.** Every metric, finding, and claim must survive "how do you know that?" from a skeptical interviewer.
5. **The live URL enables Phase B but does not automatically create value.** The value comes from the content (case study, findings, limitations) already visible when someone visits.
6. **Phase D items are genuinely optional.** They improve the software but have diminishing admissions returns compared to Phases A–C. Don't sacrifice A–C quality by starting D early.

---

## Phase A: Immediate Credibility Cleanup

### A1: Mission, Equity, and Stewardship Section in README
**Priority:** 1 (tied with A4) | **Effort:** 30 min | **CanMEDS:** Professional, Communicator

Replace the maintainer-oriented README blurb with a short public-facing section that states the project's mission, health/data equity and EDIA posture, barrier-reduction aims, and stewardship standards. The goal is to make the site read like a serious public-interest health data observatory rather than a personal portfolio or pet project.

**Artifact:** `## Mission`, `## Equity and Access`, and `## Stewardship` sections in README.

**Status:** Delivered 2026-03-28.

### A2: Limitations Section in README
**Priority:** 1 | **Effort:** 1 h | **CanMEDS:** Scholar, Professional

Add specific, technical limitations to README. Keep limitations honest and specific rather than vague:
- Scraper data now reflects an hourly GitHub Actions cadence rather than continuous ingestion.
- Equity layer uses 2021 census income data, not current.
- Methodology labels are inferred from provincial documentation and may not match internal hospital reporting practices.
- Platform cannot account for unreported overcrowding events.

Most student projects overclaim. Honest limitations are a differentiated signal that demonstrates command of the material.

**Artifact:** `## Limitations` section in README and `docs/application-summary.md`.

### A3: Fix Placeholder Zenodo DOI
**Priority:** 2 | **Effort:** 90 min | **CanMEDS:** Scholar

The placeholder DOI has been removed from README, which is safer than displaying a fabricated citation signal. The remaining task is to register a real Zenodo deposit, update `CITATION.cff`, and restore the README badge only once the DOI is real.

**Status:** Repo and release preparation completed on 2026-03-28; real DOI still pending Zenodo account activation and publication. Parked until explicit user go-ahead.

A real Zenodo record is third-party-attested, timestamped evidence of the project's existence and authorship — not just a badge.

**Artifact:** Real Zenodo record with DOI; updated CITATION.cff and README badge.

### A4: Stakeholder Interview Outreach
**Priority:** 1 (tied with A1) | **Effort:** 2–3 h outreach; interviews on respondents' schedules | **CanMEDS:** Collaborator, Health Advocate

**Status:** Parked pending explicit user go-ahead.

Begin outreach to ER professionals using the existing templates in `docs/stakeholder-interviews/`. Aim for 10–15 contacts. The conversation, not the live URL, is the point — these interviews are about methodology, so no deployment is needed.

One genuine 15-minute conversation with an ER nurse or physician, honestly documented, is the target. Don't pad it. Don't inflate a 5-minute hallway chat into "stakeholder validation."

**Artifact:** Filled `docs/stakeholder-feedback.md` with date-stamped entries; potentially a published testimonial in `frontend/content/stakeholderTestimonials.ts`; a logged outreach campaign describable in an ABS entry.

### A5: Private Reflection Document
**Priority:** 3 | **Effort:** 2 h | **CanMEDS:** Professional, Scholar

Write a private document (not committed to the repo) covering:
1. What motivated the project — the specific insight or experience.
2. One technical decision you'd revisit.
3. One clinically relevant surprise from the data.
4. One ethical tension you navigated (e.g., surfacing raw occupancy numbers that could cause patient panic).
5. What competencies you think this demonstrates.

This is interview preparation that produces articulate, reflective answers. The document is not the artifact — the interview performance is.

**Artifact:** Private reflection document for ABS drafting and interview prep.

### A6: Ottawa–Gatineau Case Study
**Priority:** 2 | **Effort:** 2–3 h | **CanMEDS:** Scholar, Communicator, Health Advocate

**Status:** Delivered 2026-03-28.

Write a 2-page case study documenting the Ottawa–Gatineau methodology divergence. This is the project's clearest, most narratively compelling story: two cities across a provincial border, served by hospitals in two different provincial health systems, with patients who routinely cross the river for care — and reported wait times that measure fundamentally different things.

**Before writing:** Verify that Ottawa-area and Gatineau-area hospitals are active in the database (5 min query). If they're missing, identify the best alternative cross-border pair.

**Structure:** Context (border geography, patient behavior) → Specific metrics from each province → Why comparison is invalid (field-by-field ontology mismatch) → Clinical implication for patients → What a valid comparison would require.

**Artifact:** `docs/case-studies/ottawa-gatineau-divergence.md`; linked from README and application summary; interview-ready material.

### A7: Quantified Metrics & Methodology Findings
**Priority:** 5 | **Effort:** 3 h | **CanMEDS:** Scholar, Leader

**Status:** Delivered 2026-03-28.

Query the database for the strongest honest metrics. Add a "By the Numbers" section to README.

**Important scope constraint:** Findings must be methodology-characterization only — no cross-province performance claims. The project's premise is that cross-province comparisons are invalid; writing findings that implicitly compare performance would be self-undermining.

Safe examples:
- "X measurements collected since launch across 380+ hospitals."
- "100% of cross-province hospital pairs have ontology mismatches on ≥2 dimensions."
- "Quebec hospitals report stretcher occupancy >110% in X% of measurements."

If the raw numbers are still early or modest, lead with operational metrics (uptime, measurement count, anomaly detection events) rather than impact metrics.

**Artifact:** "By the Numbers" section in README; specific figures for ABS entries.

**Phase A total: ~12–15 hours. Remaining items are still valuable even after launch because they improve interpretability and ownership.**

---

## Phase B: Launch Follow-Through (Post-Verification)

### B1: Restore Production Hosting
**Priority:** 0 (gate) | **Effort:** 2–3 h | **CanMEDS:** Leader

Delivered on **2026-03-12**: custom-domain TLS + redirect validation completed, production smoke passes against `https://wait-time.ca`, and the canonical URL is now trustworthy.

**Artifact:** Clean HTTPS + redirect behavior at `https://wait-time.ca`; passing production smoke test against the canonical URL.

### B2: Privacy-Safe Usage Analytics
**Priority:** 3 | **Effort:** 2 h | **CanMEDS:** Professional, Privacy

Add Plausible Analytics to Next.js layout. Update `/privacy` page. Do not publicize numbers until they're meaningful. Every month without analytics is a month of data you can never recover — add now, report later.

**Artifact:** Analytics collecting baseline data; updated privacy policy.

### B3: Publish LinkedIn Launch Post
**Priority:** 3 | **Effort:** 30 min | **CanMEDS:** Communicator, Leader

The canonical URL is now live. Publish using `https://wait-time.ca`. Spend no more than 30 minutes total. The value is a public timestamp of work and asymmetric upside if it reaches health informatics professionals.

**Status:** Copy refreshed on 2026-03-28 to match the current mission/equity/stewardship posture and live Batch A feature set. Manual publication is parked until explicit user go-ahead.

**Artifact:** Public, timestamped LinkedIn post.

### B4: Video Walkthrough
**Priority:** 3 | **Effort:** 3 h | **CanMEDS:** Communicator

Script a 3–4 minute walkthrough. Record with decent audio (headset mic is sufficient). Cover: landing page → select two incomparable hospitals → divergence warning → methods page → equity layer. Upload as unlisted YouTube or Loom link.

This is the only format where a committee hears your voice and experiences your command of the material. Prioritize audio quality over video quality. A bad video is worse than none.

**Artifact:** Unlisted video linked from README and application summary.

### B5: GitHub Topics & Discoverability
**Priority:** 8 | **Effort:** 30 min | **CanMEDS:** Leader

Add repository topic tags (`health-systems`, `emergency-medicine`, `wait-times`, `canada`, `data-observatory`, `open-data`). Check 1–2 open data registries for activity; submit if active.

**Artifact:** GitHub topic tags; potentially external directory listing.

**Phase B total: ~5–6 hours remaining post-launch (B1 delivered).**

---

## Phase C: Weeks 2–4 (Scholarly Artifacts & External Validation)

### C1: Technical Report
**Priority:** 4 | **Effort:** 1–2 d | **CanMEDS:** Scholar, Health Advocate

Write a 2–4 page structured report: *"Methodological Heterogeneity in Canadian Emergency Department Wait-Time Reporting: A Four-Province Audit."*

**Check existing files first:** `docs/'Canadian ER Wait Time Data Audit.docx'` may be partially complete.

**Structure:** Background → The Measurement Problem → Methodology (metric ontology) → Findings (specific divergences, within-province observations) → Equity Layer Analysis (descriptive association → limitations → required study design) → Limitations → Implications.

**Quality gate:** Do not publish until at least one informed person has read it (from A4 interviewee or C2 researcher). Publish via SSRN or as a GitHub Pages document. The venue matters less than the quality.

The comparison class for "Scholar" is other pre-med students, not JAMA. No other pre-med applicant will have a written methodological analysis of interprovincial ER data reporting.

**Artifact:** Public, citable document with stable URL; SSRN deposit record or GitHub Pages link.

### C2: Targeted Researcher Outreach
**Priority:** 6 | **Effort:** 3 h + response time | **CanMEDS:** Collaborator, Scholar

Identify 3 specific researchers at ICES, INSPQ, or university health informatics labs whose published work relates to ER methodology. Reference their specific papers. Share the technical report (C1). Ask for 15–20 min methodology feedback.

Don't cold-email Ontario Health's general inbox — target individuals whose work you've read. Canadian health informatics is a small community where informed, targeted outreach can get a response.

**Artifact:** Documented outreach log; potentially a named reviewer in Acknowledgements.

### C3: Equity Layer Interpretive Summary
**Priority:** 6 | **Effort:** Merged with C1 | **CanMEDS:** Scholar, Health Advocate

Write as a section of the technical report (C1), not standalone. **The limitations ARE the finding.** Structure as: descriptive association → four specific reasons this cannot be interpreted causally (ecological fallacy, 2021/2025 temporal mismatch, confounders, census tract ≠ neighborhood) → what study design would answer the causal question.

A structured analysis of what you *cannot* conclude from this data is a stronger Scholar signal than a finding that ignores those limits.

**Artifact:** Equity analysis section in technical report.

### C4: Operational Transparency Report
**Priority:** 7 | **Effort:** 2 h | **CanMEDS:** Professional, Leader

Generate one monthly report from `data_quality_snapshots` and `scraper_status` tables. Be honest about the current hourly GitHub Actions runtime and any alert/recovery incidents. Store in `docs/operations/reports/`. The value is behavioral — demonstrating the practice of systematic operational review, not the specific numbers.

**Artifact:** `docs/operations/reports/YYYY-MM-operational-report.md`.

### C5: Incident Post-Mortem
**Priority:** 8 | **Effort:** 1–2 h | **CanMEDS:** Professional

Write the Quebec zero-value parser incident post-mortem (commit `0738054`). Timeline, impact, root cause, resolution, follow-up. Store in `docs/operations/incident-reports/`.

Write it for the interview answer it produces: "What was the hardest problem?" needs a specific, honest answer. The document itself is secondary.

**Artifact:** `docs/operations/incident-reports/YYYY-MM-DD-quebec-zero-value.md`; interview preparation material.

### C6: Named Reviewer Acknowledgement
**Priority:** 7 | **Effort:** 30 min if applicable | **CanMEDS:** Collaborator

If A4 (stakeholder interview) or C2 (researcher outreach) produces someone willing to be acknowledged as a methodology reviewer, add an Acknowledgements section to README. Do not pursue independently — this is a natural extension of Items A4 and C2, not a separate task.

Don't inflate titles. A 20-minute methodology review conversation makes someone a "reviewer," not an "advisor."

**Artifact:** Acknowledgements section in README (conditional).

**Phase C total: ~2–3 days of work over 2–3 weeks.**

---

## Phase D: If Time Permits (Weeks 5–12)

These items improve the project as software but have diminishing admissions returns. Only pursue after Phases A–C are complete.

### D1: Comparability Matrix Upgrade
**Effort:** M | **Condition:** Only if current `/methods` comparability matrix lacks explicit per-pair field-by-field justifications.

Check current implementation. If province-pair verdicts are high-level, add explicit field-by-field comparability verdicts for all 6 province pairs (ON-QC, ON-AB, ON-BC, QC-AB, QC-BC, AB-BC) with clinical implications.

### D2: Quebec Equity Layer Extension
**Effort:** M–L | **Condition:** Only after Phases A–C complete. Must apply full Ontario-equivalent rigor (ADR, suppression provenance, uncertainty bounds, non-causal framing).

A methodology that works for one province is interesting. A methodology with a proven framework that can be applied province-by-province is a system. But a rushed extension that cuts corners undermines Ontario's credibility.

### D3: Per-Hospital Data Freshness Indicators
**Effort:** S | Feature development, not admissions-critical.

Add `last_updated` timestamp and age indicator to hospital cards and export CSV. Consistent with the project's transparency identity but does not change how committees evaluate the project.

### D4: Nova Scotia Scraper (M35)
**Effort:** L | **Condition:** Only if NS methodology is confirmed to add a genuinely new ontology combination AND all higher-priority items are complete.

5 vs 4 provinces is not notably more impressive unless NS methodology is novel. The time cost (1–4 weeks) is disproportionate to the marginal admissions value.

### D5: Grant / Competition Application
**Effort:** M | **Condition:** Opportunistic only. Do not actively search. Apply if a suitable, eligible competition is discovered during other activities.

---

## Expected Outcome by Week 6

If Phases A–C execute on schedule, by mid-April 2026 the portfolio includes:

- A live, professional URL at `wait-time.ca` with current published data
- A clear public-facing mission, equity/EDIA, and stewardship statement
- A real Zenodo DOI resolving to a real record
- An honest limitations section demonstrating intellectual maturity
- At least one documented stakeholder conversation with an ER professional
- A concrete Ottawa–Gatineau case study ready for any interview
- Quantified metrics grounded in actual database queries
- A published LinkedIn post with a public timestamp
- A 3–4 minute video walkthrough in your own voice
- Usage analytics collecting baseline data
- A 2–4 page technical report reviewed by at least one external reader
- One monthly operational report
- One incident post-mortem for interview preparation
- A private reflection document for ABS drafting
- Potentially: a named reviewer acknowledged in the README

Total effort: approximately 5–6 days of focused work spread across 6 weeks.

---

## Analytical Notes

This plan is the product of three analytical passes:
1. **Original plan:** 24 improvements identified, sorted by admissions value.
2. **Devil's advocate pass:** Each item challenged for execution risk, overstated claims, and unfavorable comparison classes.
3. **Steelman pass:** Each item defended with the strongest possible case, identifying overlooked value.
4. **Final synthesis:** Both sides weighed objectively; items re-prioritized based on defensible value and effort.

Key insights from the analysis:
- The engineering foundation is already excellent. The gap is almost entirely in **real-world engagement, external validation, and public-facing artifacts**.
- Items 2 (stakeholder interview) and 8 (README mission/equity/stewardship section) are the two highest-ROI actions. A1 is now delivered; A4 should remain parked until explicitly activated.
- The technical report (C1) is the anchor scholarly artifact — the case study, findings, and equity interpretation all feed into it.
- Usage analytics should be added immediately after deployment to establish baseline data, but numbers should not be publicized until they tell a good story.
- Phase D items are genuinely optional for admissions purposes and should not compete with Phase A–C execution.
