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
- ❌ NEVER list an AI assistant, or any other automated developer tool, or agent as an author, co-author, or contributor.
- ❌ NEVER use `Co-Authored-By` trailers in git commits that reference an AI or automated tool.
- ✅ ONLY humans should be listed as authors or contributors in any part of this repository.
- ✅ Use generic terms like "automated tool" or "agent" if you need to reference your own actions in documentation.
- ❌ Do NOT include any AI tool names (Claude, Gemini, ChatGPT, etc.) in source code, comments, or documentation unless referring to the tools themselves as external dependencies.

---

## Overview

This is the **Wait Time Canada** project - a "Health Systems Observatory" designed to audit and standardize Canadian emergency room wait time data across provinces. This is **NOT a simple wait time app**, but rather a clinically defensible auditing platform that exposes methodological inconsistencies in healthcare reporting.

**Current Status:** Milestone 33 (Historical Occupancy Trends) Complete. **Four-province breadth achieved** (ON, QC, AB, BC). All scrapers active, 380+ hospitals visible, methodology documentation complete for all provinces, occupancy trend aggregation pipeline operational, the production domain `wait-time.ca` is live on the VPS via Caddy, and raw measurements are preserved by default for long-term analysis.

**Current Architecture:**
- **Database**: Neon PostgreSQL 17 (9 tables: sources, hospitals, measurements, scraper_status, measurement_aggregates, data_quality_snapshots, methodology_change_events, regions, hospital_regions)
- **Backend**: Python 3.12+ with psycopg2, pytest
  - **Tests**: 454+ passing (unit + integration)
  - Scrapers: Quebec (BeautifulSoup), Ontario (HTTP client), Alberta (Playwright), BC (JSON/__NEXT_DATA__)
  - Services: DatabaseService, AggregationService, DataQualityService, AnomalyDetectionService, MethodologyChangeDetector, GeocodingService
  - CLI tools: scraper runner, database maintenance / optional purge, seeding, aggregation, trusted hospital approval, region mapping
- **Frontend**: Next.js 14 + TypeScript + Mapbox GL JS
  - **Tests**: 359+ passing (Vitest + React Testing Library)
  - Map component with hospital markers and methodology display
  - Data quality dashboard (`/data-quality`)
  - Analytics & benchmarking dashboard (`/analytics`)
  - Data export with granularity selector
  - Trend charts with aggregate visualization (90d/6m/1y)
  - Methods & governance page (`/methods`)
  - API routes for hospitals, comparisons, health, data-quality, anomalies, export, analytics

## Core Architecture

### Technology Stack

- **Backend:** Python 3.12+ scrapers via GitHub Actions (cost-control mode: every 4 hours; post-unpause target: */20)
- **Database:** Neon PostgreSQL 17 with strict schema constraints
- **Frontend:** Next.js 14 App Router + TypeScript + Mapbox GL JS
- **Testing:** pytest (backend), Vitest (frontend), Playwright (E2E in CI)
- **Hosting:** Direct VPS via Caddy and Docker (frontend) + GitHub Actions (authoritative scraper scheduling)

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

**`hospitals`** - Facility metadata with visibility controls
- `is_verified` / `is_visible`: Hospitals from trusted government sources are auto-approved on insert
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

Retention policy: Preserve raw measurement rows by default; only purge old rows with an explicit operator-approved delete path (aggregates remain permanent).

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

### 3. Trusted Source Auto-Approval

Hospitals scraped from official government health authority websites (Ontario Health, Quebec MSSS, BC PHSA, Alberta AHS) are trusted sources and auto-approved on insert (`is_verified=TRUE, is_visible=TRUE`). Data quality is enforced through automated controls: anomaly detection, payload hashing, parser versioning, and heartbeat monitoring.

### 4. Province-Aware Routing

When displaying hospital details, query the `sources` table to show correct telehealth info:
- Ontario: "Call Health Connect Ontario 811"
- Quebec: "Call Info-Santé 811"
- Alberta: "Call Health Link 811"
- BC: "Call HealthLink BC 811"

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
4. **Trusted sources** - Government health authority data is auto-approved; quality enforced via automated monitoring
5. **Ontology enforcement** - Use database CHECK constraints or application-level validation
6. **Attribution** - Always link back to official provincial sources
7. **Human Authorship Only** - Never attribute work to AI or non-human agents

## Deployment Guardrails (Cost Control)

- Netlify production deploys are intentionally gated to explicit release commits.
- `frontend/netlify.toml` uses `frontend/scripts/netlify-ignore.sh`.
- A Netlify production build is allowed only when commit message contains `[release]` or `[deploy]`.
- Non-production branches are skipped by default.
- This guardrail prevents new accidental credit burn; it does **not** unsuspend already suspended Netlify projects before billing reset on March 2, 2026.
- `production-smoke.yml` remains manual-dispatch to conserve GitHub Actions minutes on the free tier; use explicit release commits and manual smoke checks rather than high-frequency automated production probes.

## Runtime Usage Guardrails

- Frontend health polling should remain low-frequency: `SystemStatus` checks `/api/health` every 5 minutes and only when the tab is visible.
- Shared read-heavy API routes should use CDN cache headers via `frontend/utils/cache.ts` with short TTLs (typically 2-10 minutes).
- User-specific API routes must use `Cache-Control: no-store` (for example IP geolocation).
- Export endpoints must use `no-store` to avoid serving stale downloadable datasets.

## Implementation Roadmap

- [x] **Milestones 1-15:** Database foundation, multi-province scrapers, methodology comparisons, data quality monitoring, aggregation pipeline, analytics & benchmarking.
- [x] **Milestone 16 (Complete):** Multi-Province Operationalization - 4 provinces active (ON, QC, AB, BC), 380+ hospitals visible, methodology documentation complete for all provinces, 15 health regions mapped, hospital seed data for all provinces.
- [x] **Milestones 17-32 (Complete):** Quebec occupancy implementation, occupancy frontend UI, governance & quality, reliability, i18n, documentation, equity layer (ON real data + academic rigor hardening), scraper observability hardening, divergence briefs, deployment readiness & CSV divergence.
- [x] **Milestone 33 (Complete):** Historical Occupancy Trends — STRETCHER_OCCUPANCY in aggregation pipeline, metric-family analytics API filter, occupancy trend panel on analytics page, DB migration 015, ADR-0019.

---

Note: This project uses **Neon PostgreSQL** as its primary database.

This is a **physician-innovator portfolio project** optimized for medical school admissions committee review. Every technical decision maps to a narrative competency (Scholar, Professional, Advocate, Leader).
