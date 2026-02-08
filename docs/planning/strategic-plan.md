---

# Master Implementation Bible: WaitTime Canada

**Project Code:** `WAITTIME-CANADA`
**Document Type:** Comprehensive Strategic & Technical Specification
**Version:** 6.0 (The "Audit-Grade" Build)
**Date:** December 26, 2025
**Objective:** To build a rigorous, clinically defensible "Health Systems Observatory" that demonstrates "Physician-Innovator" competency.

> **Note (Feb 2026):** This document is the original strategic vision. Some implementation details have evolved:
> - **Database:** Now uses **Neon PostgreSQL** (not Supabase)
> - **Hosting:** Frontend on **Render** (not Vercel)
> - **Alerts:** Uses **Pushover** (not email)
> - **Current status:** See `docs/planning/roadmap.md` for up-to-date progress

---

## Part 1: Strategic Context & The "Auditor" Narrative

### 1.1. The Core Mission

We are **not** building a "Wait Time App." We are building **WaitTime Canada.**

**The Pivot:** Instead of claiming to "fix" the data, we **audit** the data. We expose the "black box" of Canadian healthcare by standardizing *how we describe* the wait.

### 1.2. The Value Proposition (Final Refinement)

Admissions committees will ask: *"Why does this exist?"*

| Feature           | The "Unicorn" Narrative                                                                                                                                            |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Comparability** | **Scholar:** "I built a Metric Ontology to scientifically prove why Alberta and Manitoba data cannot be directly compared."                                        |
| **Stewardship**   | **Professional:** "I implemented a 'Province-Aware' directory that routes users to their specific provincial telehealth line (e.g., Info-Santé 811 vs Health811)." |
| **Finance**       | **Health Advocate:** "I built an 'Access Burden Estimator' to highlight the hidden financial barriers to care."                                                    |
| **Ops**           | **Leader:** "I engineered a 'Heartbeat Monitor' to detect silent failures in public health reporting."                                                             |

---

## Part 2: Phase 1 — Data Ontology Protocol (The Scientific Layer)

**The Problem:** "Wait Time" is ambiguous.
**The Solution:** We replace "normalization" with a **Strict Metric Ontology**.

### 2.1. The Metric Ontology Schema (Strict Enums)

Every measurement is tagged with metadata. We use `CHECK` constraints or `ENUMs` to prevent drift.

| Attribute        | Definition        | Allowed Values (Enforced)                                          |
| ---------------- | ----------------- | ------------------------------------------------------------------ |
| `metric_family`  | What is measured? | `TIME_TO_PROVIDER`, `TOTAL_LOS`, `STRETCHER_OCCUPANCY`             |
| `start_event`    | Clock start?      | `TRIAGE`, `REGISTRATION`, `DOOR`, `UNKNOWN`                        |
| `end_event`      | Clock stop?       | `PHYSICIAN`, `PROVIDER`, `DISCHARGE`, `FIRST_ASSESSMENT`           |
| `statistic_type` | How derived?      | `POINT_ESTIMATE`, `P90` (Percentile), `ALGORITHMIC`, `ROLLING_AVG` |
| `patient_scope`  | Who included?     | `ALL`, `MID_ACUITY`, `NON_PRIORITY`                                |

### 2.2. The "Comparability Boolean" (The Logic)

We do not guess. We compute comparability.

**The Logic:**
`Comparable = (A.Family == B.Family) AND (A.Start == B.Start) AND (A.End == B.End) AND (A.StatType == B.StatType)`

**The Auto-Researcher Rule:**

* If `Comparable == True`: Compute the differential (e.g., "Ottawa is 2h faster than Gatineau").
* If `Comparable == False`: Generate a **"Divergence Brief"**: *"Ottawa publishes P90 Triage-to-Doc; Gatineau publishes Average Registration-to-Doc. Direct comparison is invalid."* (This is a huge "Scholar" win).

---

## Part 3: Phase 2 — Technical Architecture (The Engine Room)

**Design Philosophy:** "Resilient, Audit-Grade MVP."
**Architecture:** `[GitHub Actions] --> [Supabase (PG)] --> [Next.js] --> [Mapbox]`

### 3.1. The "Self-Healing" Scraper Fleet

* **Schedule:** Every 15 minutes (`*/15`).
* **Heartbeat Monitor:** The scraper writes a `heartbeat` row to a status table on every run. Frontend shows: *"Last Audit: 4 mins ago (Healthy)."*
* **Silent Failure Mitigation:** If the `heartbeat` is > 60 mins old, the "Dead Man's Switch" (GitHub Action) triggers an email alert.

### 3.2. Persistence Layer (Supabase/PostgreSQL)

**Storage Safety:** We store a **Hash** of the raw payload, not the full HTML, to save space.

**Table 1: `sources` (Provenance)**

```sql
CREATE TABLE sources (
    id TEXT PRIMARY KEY, -- e.g., 'ca-ab-ahs'
    name TEXT NOT NULL, -- 'Alberta Health Services'
    definition_url TEXT, -- Link to methodology page
    telehealth_name TEXT, -- 'Health Link 811'
    telehealth_phone TEXT -- '811'
);

```

**Table 2: `hospitals` (Metadata)**

```sql
CREATE TABLE hospitals (
    id TEXT PRIMARY KEY,
    source_id TEXT REFERENCES sources(id),
    name TEXT NOT NULL,
    province TEXT NOT NULL,
    latitude FLOAT,
    longitude FLOAT,
    facility_type TEXT DEFAULT 'ER',
    is_verified BOOLEAN DEFAULT FALSE, -- Verification Queue
    is_visible BOOLEAN DEFAULT FALSE
);

```

**Table 3: `measurements` (Audit Log)**

```sql
CREATE TABLE measurements (
    id BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    hospital_id TEXT REFERENCES hospitals(id),
    timestamp_utc TIMESTAMPTZ DEFAULT NOW(),
    value NUMERIC,

    -- STRICT ONTOLOGY (Enums)
    metric_family TEXT NOT NULL,
    start_event TEXT NOT NULL,
    end_event TEXT NOT NULL,
    statistic_type TEXT NOT NULL,

    -- STORAGE-SAFE AUDIT
    raw_payload_hash TEXT,       -- SHA256 of source HTML
    raw_payload_snippet TEXT,    -- First 200 chars only
    parser_version TEXT          -- 'v1.4'
);

```

---

## Part 4: Phase 3 — Feature Logic (The "Unicorn" Value-Adds)

### 4.1. Feature A: The "Province-Aware" Stewardship Directory

* **The Narrative:** Professional / Collaborator.
* **The Problem:** "811" isn't the same everywhere.
* **The Logic:** When a user selects a hospital, query the `sources` table to render the correct banner.
* **Ontario:** "Call Health811."
* **Quebec:** "Call Info-Santé 811."
* **Alberta:** "Call Health Link 811."

### 4.2. Feature B: The "Access Burden Estimator" (Opt-In)

* **The Narrative:** Health Advocate.
* **The UX:** Collapsible "Planning Lens."
* **Logic:** Calculates `(Distance * GasPrice) + Parking`.
* **Disclaimer:** "Logistical estimate only. Never delay care for cost."

### 4.3. Feature C: The "Methods & Governance" Page

* **The Narrative:** Scholar.
* **Content:** A dynamic table showing the **Comparability Matrix**.
* *Row:* Alberta. *Metric:* Triage-to-Doc (P90).
* *Row:* Manitoba. *Metric:* Reg-to-Doc (Average).
* *Conclusion:* "Methodologically Distinct."

---

## Part 5: Phase 4 — Execution Roadmap (The 4-Week Sprint)

### Week 1: The "Audit" MVP

**Goal:** Ingest data with the strict Ontology.

* **Days 1-2:** Setup Supabase. Create `sources`, `hospitals`, `measurements` tables with `CHECK` constraints.
* **Days 3-4:** Build `main.py` and `quebec.py`. Implement the **Storage-Safe Hash** logic.
* **Day 5:** Build the "Heartbeat" API endpoint.

### Week 2: The "Heterogeneity" MVP

**Goal:** Prove the Comparability Logic works.

* **Days 1-2:** Build `alberta.py` (Tag: `start=TRIAGE`) and `manitoba.py` (Tag: `start=REGISTRATION`).
* **Day 3:** Build the "Verification Queue" script (simple UI to approve new hospitals).
* **Day 4:** Populate the `sources` table with correct Telehealth strings (Info-Santé, etc.).
* **Day 5:** Run the Auto-Researcher. Verify it generates a **"Divergence Brief"** for AB vs MB (Correct behavior) instead of a comparison.

### Week 3: The "Scholar" Frontend

**Goal:** UI that prioritizes truth.

* **Days 1-2:** Next.js + Mapbox.
* **Day 3:** Build the **"Methodology Divergence Warning."**
* **Day 4:** Build the **Province-Aware Banner** (Health811 vs Info-Santé).
* **Day 5:** Write the `/methods` page.

### Week 4: The "Professional" Polish

**Goal:** Narrative alignment.

* **Day 1:** Mobile Optimization.
* **Day 2:** **The "Equity Layer."** (Income Shapefiles).
* **Day 3:** **Stakeholder Engagement.** (Interview 1 Nurse).
* **Day 4:** Launch.
* **Day 5:** The LinkedIn Post.

---

## Part 6: Risk Register & Mitigations (Final)

| Risk                  | Impact   | Mitigation Strategy                                                                                        |
| --------------------- | -------- | ---------------------------------------------------------------------------------------------------------- |
| **Misinterpretation** | High     | **Mitigation:** The "Methodology Divergence Warning." Never show a raw comparison table without footnotes. |
| **Silent Failure**    | High     | **Mitigation:** "Heartbeat Monitor" on frontend + "Dead Man's Switch" email alert.                         |
| **Storage Limits**    | Med      | **Mitigation:** Store Payload *Hash* only. Retention Policy deletes raw rows > 30 days.                    |
| **Triage Liability**  | Critical | **Mitigation:** REMOVED Symptom Router. Replaced with Province-Aware Telehealth Directory.                 |

---
