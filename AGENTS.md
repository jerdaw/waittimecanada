# AGENTS.md

This file provides guidance to automated developer tools when working with code in this repository.

## ⚠️ CRITICAL SECURITY RULES ⚠️

**NEVER access `.env.local` files under ANY circumstances:**

- ❌ Do NOT use Read tool on any `.env.local` file
- ❌ Do NOT use Bash commands (cat, grep, head, tail, etc.) on `.env.local` files
- ❌ Do NOT try to "help" by reading credentials to automate setup
- ❌ Do NOT access `.env.local` even if asked to debug environment issues
- ✅ If you need credential info, ask the user - do NOT access files
- ✅ Only create/modify `.env.example` files with placeholder values

**Files I must NEVER access:**
- `**/.env.local` (all .env.local files in any directory)
- `**/.env` (production environment files)
- `**/key.txt` (encryption keys)
- `**/*.pem` (SSL certificates)
- `**/*.key` (private keys)
- Any file containing secrets, tokens, passwords, or API keys

**If I accidentally access these files:**
- Stop immediately
- Inform the user
- Do not use or store the information
- Recommend the user rotate compromised credentials

**Authorship and Attribution:**
- ❌ NEVER list an automated developer tool, agent, or AI as an author, co-author, or contributor.
- ❌ NEVER use `Co-Authored-By` trailers in git commits that reference an AI or automated tool.
- ✅ ONLY humans should be listed as authors or contributors in any part of this repository.
- ✅ Use generic terms like "automated tool" or "agent" if you need to reference your own actions in documentation.

---

## Overview

This is the **WaitTime Canada** project - a "Health Systems Observatory" designed to audit and standardize Canadian emergency room wait time data across provinces. This is **NOT a simple wait time app**, but rather a clinically defensible auditing platform that exposes methodological inconsistencies in healthcare reporting.

**Current Status:** Active development, significant infrastructure complete. **PRIMARY FOCUS: Core infrastructure ✓, Ontario & Quebec scrapers live ✓, Geocoding manual override live ✓**.

**Current Architecture:**
- **Database**: Neon PostgreSQL 17 with full schema (sources, hospitals, measurements, scraper_status)
- **Backend**: Python 3.12+ with psycopg2, pytest
  - **Tests**: 143 passing (122 unit + 21 integration), 57% coverage
  - Quebec scraper: Complete
  - Ontario scraper: Complete (Playwright-based for dynamic content)
  - Services: DatabaseService, HeartbeatService, ComparisonService
  - CLI tools: scraper runner, database cleanup, seeding
- **Frontend**: Next.js 14 + TypeScript + Mapbox GL JS
  - **Tests**: 79 passing (Vitest + React Testing Library)
  - Map component with hospital markers and methodology display
  - Comparison modal with methodology divergence warnings
  - Admin verification queue UI (`/admin/verify`)
  - Methods & governance page (`/methods`)
  - API routes for hospitals, comparisons, health checks

## Core Architecture

### Technology Stack

- **Backend:** Python 3.12+ scrapers via GitHub Actions (15-minute cron configured)
- **Database:** Neon PostgreSQL 17 with strict schema constraints
- **Frontend:** Next.js 14 App Router + TypeScript + Mapbox GL JS
- **Testing:** pytest (backend), Vitest (frontend), Playwright (E2E in CI)
- **Hosting:** Render (frontend) + GitHub Actions (scrapers)

### The Metric Ontology System

The fundamental architectural principle is the **Strict Metric Ontology** - never normalize data, but instead tag every measurement with metadata to enable comparability analysis.

**Required Enums/Constants:**

```python
METRIC_FAMILY = ["TIME_TO_PROVIDER", "TOTAL_LOS", "STRETCHER_OCCUPANCY"]
START_EVENT = ["TRIAGE", "REGISTRATION", "DOOR", "UNKNOWN"]
END_EVENT = ["PHYSICIAN", "PROVIDER", "DISCHARGE", "FIRST_ASSESSMENT"]
STATISTIC_TYPE = ["POINT_ESTIMATE", "P90", "ALGORITHMIC", "ROLLING_AVG"]
PATIENT_SCOPE = ["ALL", "MID_ACUITY", "NON_PRIORITY"]
```

**Comparability Logic:**

Two measurements are comparable if and only if:
```python
comparable = (
    A.metric_family == B.metric_family and
    A.start_event == B.start_event and
    A.end_event == B.end_event and
    A.statistic_type == B.statistic_type
)
```

If not comparable, generate a **"Divergence Brief"** explaining why direct comparison is invalid.

## Database Schema

### Core Tables

**`sources`** - Provenance tracking for each provincial data source
- Includes telehealth contact info (Health Link 811 vs Info-Santé 811)
- Links to official methodology documentation

**`hospitals`** - Facility metadata with verification workflow
- `is_verified`: Requires manual approval before appearing on site
- `is_visible`: Toggle for production visibility
- Geographic coordinates for mapping

**`measurements`** - Audit log of all scraped data
- Uses ontology enums to tag metric characteristics
- Stores SHA256 hash of raw payload (NOT full HTML) to save storage
- Includes `parser_version` for schema evolution tracking
- `raw_payload_snippet`: First 200 chars for debugging only

## Implementation Principles

### 1. Storage Safety

**NEVER store full HTML payloads.** Use:
```python
import hashlib
payload_hash = hashlib.sha256(html.encode()).hexdigest()
payload_snippet = html[:200]
```

Retention policy: Delete raw measurement rows older than 30 days (keep aggregates).

### 2. Silent Failure Detection

**Heartbeat Monitor:** Every scraper run must write a status row with timestamp. Frontend displays "Last Audit: X mins ago". If heartbeat is >60 minutes old, GitHub Action triggers alert.

Implementation pattern:
```python
def write_heartbeat(source_id: str):
    supabase.table('scraper_status').insert({
        'source_id': source_id,
        'last_run': datetime.utcnow(),
        'status': 'healthy'
    })
```

### 3. Verification Queue

**NEVER auto-publish new hospitals.** All discovered facilities must go through verification:
1. Scraper inserts with `is_verified=FALSE, is_visible=FALSE`
2. Admin reviews via simple UI
3. Manual approval sets `is_verified=TRUE, is_visible=TRUE`

### 4. Province-Aware Routing

When displaying hospital details, query the `sources` table to show correct telehealth info:
- Ontario: "Call Health811"
- Quebec: "Call Info-Santé 811"
- Alberta: "Call Health Link 811"

This demonstrates **stewardship** and **professional collaboration**.

## Scraper Implementation Pattern

Each provincial scraper (`scrapers/quebec.py`, `scrapers/alberta.py`, etc.) must:

1. **Fetch** data from provincial source
2. **Parse** using BeautifulSoup or similar
3. **Tag** measurements with correct ontology values:
   ```python
   measurement = {
       'hospital_id': 'ca-qc-chum',
       'value': 180,  # minutes
       'metric_family': 'TIME_TO_PROVIDER',
       'start_event': 'REGISTRATION',
       'end_event': 'PHYSICIAN',
       'statistic_type': 'ROLLING_AVG',
       'raw_payload_hash': payload_hash,
       'parser_version': 'v1.0'
   }
   ```
4. **Write** heartbeat on completion
5. **Handle** errors gracefully (log but don't crash entire run)

## Key Features (Value Proposition)

### Feature A: Methodology Divergence Warning
When comparing hospitals from different provinces, show prominent warning if ontology doesn't match:
> "⚠️ Methodology Divergence: Ottawa reports P90 Triage-to-Doctor time. Gatineau reports Average Registration-to-Doctor time. Direct comparison is invalid."

### Feature B: Access Burden Estimator (Optional)
Collapsible UI showing `(Distance × Gas Price) + Parking` with disclaimer:
> "Logistical estimate only. Never delay care for cost."

### Feature C: Methods & Governance Page
Dynamic table showing comparability matrix across provinces. This is the **Scholar** narrative - demonstrating understanding of research methodology.

## Critical Rules

1. **Never claim to "fix" inconsistent data** - We audit and expose inconsistencies
2. **Never provide medical advice** - This is a data observatory, not a triage tool
3. **Storage-first thinking** - Hash payloads, not store full HTML
4. **Verification gate** - No auto-publishing of new facilities
5. **Ontology enforcement** - Use database CHECK constraints or application-level validation
6. **Attribution** - Always link back to official provincial sources
7. **Human Authorship Only** - Never attribute work to AI or non-human agents

## 4-Week Implementation Roadmap

### Week 1: Database Foundation
- Setup Supabase project
- Create tables with CHECK constraints on ontology enums
- Build Quebec scraper (simplest starting point)
- Implement heartbeat endpoint

### Week 2: Multi-Province Heterogeneity
- Add Alberta scraper (different `start_event` than Quebec)
- Add Manitoba scraper (different `statistic_type`)
- Build verification queue UI
- Populate `sources` table with telehealth data
- Test divergence detection service generates divergence briefs correctly

### Week 3: Frontend "Scholar" UI
- Next.js app with Mapbox integration
- Methodology divergence warnings
- Province-aware banner system
- `/methods` page explaining comparability logic

### Week 4: Polish & Launch
- Mobile optimization
- Equity layer (income shapefiles overlay)
- Stakeholder interview (1 nurse or ED staff)
- Launch + LinkedIn post

## Risk Mitigations

- **Misinterpretation Risk:** Always show methodology warnings, never raw comparison tables
- **Silent Failure Risk:** Heartbeat monitor + dead man's switch alerts
- **Storage Risk:** Hash-only storage + 30-day retention policy
- **Liability Risk:** NO symptom router, only province-aware telehealth directory

## Documentation Reference

The master specification is in `docs/planning/strategic-plan.md` (the "Master Implementation Bible"). Treat this as the authoritative source for:
- Complete ontology definitions
- Table schemas with SQL DDL
- Feature requirements and narrative justification
- Risk register and compliance considerations

Note: The strategic plan references "Supabase" in some places - the project now uses **Neon PostgreSQL**.

This is a **physician-innovator portfolio project** optimized for medical school admissions committee review. Every technical decision must map to a narrative competency (Scholar, Professional, Advocate, Leader).
