# Milestone 30: Scraper Failure Visibility and Reliability Hardening

**Version:** 1.0.0
**Status:** Implemented (Delivered)
**Created:** 2026-02-19
**Last Updated:** 2026-02-19
**Priority:** P1 (Engineering Reliability)
**Roadmap References:** `docs/planning/roadmap.md` P1 items at lines 94 and 95

---

## Executive Summary

This plan covers two active roadmap items:

1. `P1 / Ops: Scraper failure visibility` - consolidate last-known-good and last-error into one operational view (CLI + `/api/health`) to prevent silent data decay.
2. `P1 / Ops: Scraper reliability hardening` - standardize retry/backoff/timeouts and classify failures as upstream outage vs parser breakage.

The implementation sequence is intentionally visibility-first, then reliability hardening. This minimizes risk and ensures we can observe behavior changes as hardening is introduced.

No implementation is performed by this document.

---

## Current State Summary (Repo + Docs)

### What is already in place

- Scrapers run on GitHub Actions via `python -m waittime.cli.scraper --all` from `.github/workflows/scraper-cron.yml`.
- Heartbeat checks run via `.github/workflows/heartbeat-monitor.yml` using `python -m waittime.cli.check_heartbeat --max-age 90`.
- `BaseScraper` includes shared flow (`fetch -> parse -> save -> heartbeat`) and `tenacity` retries for its own `fetch()` method (`backend/src/waittime/scrapers/base.py`).
- Heartbeat persistence exists in `scraper_status` with fields: `source_id`, `last_run`, `status`, `error_message`, `measurements_count` (`backend/migrations/002_create_tables.sql`, `backend/src/waittime/services/database.py`).
- `/api/health` already returns per-source last run, status, error message, count, and age (`frontend/app/api/health/route.ts`).

### Important gaps relevant to these two roadmap items

- Retry behavior is inconsistent by scraper:
  - `BaseScraper.fetch()` retries.
  - Ontario/Alberta override fetch with Playwright and currently do not use shared retry/backoff policy.
  - Quebec uses paginated `requests.get()` path outside shared fetch behavior.
- Failure semantics are shallow:
  - Errors are stored as free-text message only.
  - No explicit failure category (`upstream`, `parser`, `infra`) or stage (`fetch`, `parse`, `persist`).
  - No dedicated `last_success_run` field in `scraper_status`.
- The current heartbeat monitor CLI only checks heartbeat age and ignores failure class and error status (`backend/src/waittime/cli/check_heartbeat.py`).
- `run_scraper` returns only integer measurement count, limiting structured failure reporting (`backend/src/waittime/cli/scraper.py`).
- `scraper-cron.yml` has a placeholder "Check scraper health" step that currently only echoes text.

### Documentation and operational drift found during review

- Schedule and threshold docs are inconsistent in several places (still referencing 15-minute cadence and 60-minute stale threshold while workflows run in temporary 30/60 cadence with 90-minute heartbeat threshold).
- `/api/health` and status-oriented UI text still embed assumptions tied to 15-minute cadence.

This drift is not the main scope, but it is a direct operational risk for visibility and will be addressed in plan phases where it affects alerting correctness.

---

## Key Unknowns and Assumptions

### Key unknowns (non-blocking)

1. Real-world failure distribution by source over the last 30 days (needed to calibrate classification heuristics).
2. Whether single-row heartbeat state is sufficient, or if we need a dedicated run-event history table in this milestone.
3. Expected alert sensitivity for partial-success scenarios (some data written, but one stage failed).

### Assumptions used in this plan

1. Additive DB schema changes are acceptable (Neon PostgreSQL migration path available).
2. Backward compatibility for existing API consumers is required (`/api/health` shape should not break existing fields).
3. Current resources are one maintainer plus existing CI workflows (no net-new observability platform).
4. Public frontend hosting remains paused; rollout validation relies on CI, workflow logs, and DB queries.

No blocking questions are required before implementation.

---

## Goals, Non-Goals, and Success Criteria

### Goals

1. Provide a single operational view showing per-source:
   - last attempt,
   - last success (last-known-good),
   - last error (timestamp, message, classification),
   - consecutive failures,
   - freshness age.
2. Standardize retry/backoff/timeout behavior across all provincial scrapers.
3. Classify failures with stable categories that separate upstream availability from parser/data-contract breakage.
4. Keep system behavior backward-compatible and safe to roll back quickly.

### Non-goals

- New provinces, new product pages, or unrelated analytics features.
- Replacing current alert provider or adding external APM stack.
- Redesigning methodology/ontology logic.

### Milestone success criteria

- Operational view available in both CLI and `/api/health`, with last-known-good + last-error for every active source.
- Failure classification present for new failures and visible in operational surfaces.
- Scraper reliability policy (retry/backoff/timeouts) applied consistently across ON/QC/AB/BC paths.
- Automated tests cover core classification and failure-surface behavior.
- Runbook updated for on-call triage using new classifications.

---

## Design Principles

1. **Visibility before hardening:** baseline and expose signals first, then tune behavior.
2. **Additive-first schema:** avoid destructive migrations; maintain compatibility.
3. **Structured failure metadata:** never rely on free-text error parsing for primary classification.
4. **Deterministic classification:** same failure input should classify identically.
5. **Safe defaults:** unknown failures remain visible as `unknown`, never silently ignored.

---

## Proposed Technical Approach

### 1. Failure taxonomy (canonical)

- `failure_category` (primary):
  - `upstream_unavailable` (5xx, DNS/TLS/connectivity, provider outage)
  - `parser_breakage` (HTML/JSON structure drift, missing selectors/keys)
  - `infra_runtime` (Playwright/browser/runtime/environment failures)
  - `persistence_failure` (DB write/upsert/transaction errors)
  - `unknown`

- `failure_stage` (pipeline stage):
  - `fetch`
  - `parse`
  - `before_save`
  - `persist`
  - `heartbeat`
  - `orchestration`

### 2. Operational state model

Per source, maintain:

- last attempt (`last_run` existing)
- last success timestamp and count (new)
- last error timestamp, category, stage, message (new)
- consecutive failure count (new)
- computed operational status for presentation (`healthy`, `degraded`, `error`, `stale`)

### 3. Reliability policy baseline

- Shared retry policy by source type:
  - HTTP scrapers: bounded exponential backoff with jitter.
  - Playwright scrapers: bounded attempt wrapper around browser/session startup + page load + selector wait.
- Standard timeout profiles:
  - connect timeout, read timeout, total run timeout guard.
- "No silent partials" rule:
  - if partial collection occurs, outcome is explicitly recorded and surfaced.

---

## Phased Implementation Plan

### Phase 0: Baseline and Contract Freeze

**Goal:** Establish measurable baseline and freeze the operational contract before code changes.

**Estimated effort:** 0.5 day

### Tasks

- Capture baseline per-source health/freshness/error from:
  - `scraper_status`,
  - latest measurements,
  - GitHub Actions last-run outcomes.
- Define API contract extension strategy for `/api/health` (backward-compatible additive fields only).
- Finalize failure taxonomy and stage mapping to specific exception classes.

### Deliverables

- Baseline snapshot section added to the implementation PR description.
- Contract note for `/api/health` field additions.

### Validation

- Manual SQL baseline query outputs saved in PR notes.
- Team sign-off on taxonomy names before Phase 1 migration.

### Dependencies and risks

- Dependency: database connectivity + workflow visibility.
- Risk: taxonomy too coarse -> rework in Phase 2.
- Mitigation: keep `unknown` category and stage fallback from day one.

---

### Phase 1: Data Model and Service Contract for Visibility

**Goal:** Persist enough structured state to support last-known-good + last-error operational view.

**Estimated effort:** 0.5 to 1.0 day

### Tasks

- Add additive columns to `scraper_status` via new migration:
  - `last_success_run TIMESTAMPTZ NULL`
  - `last_success_measurements_count INTEGER NULL`
  - `last_error_run TIMESTAMPTZ NULL`
  - `last_error_category TEXT NULL`
  - `last_error_stage TEXT NULL`
  - `consecutive_failures INTEGER NOT NULL DEFAULT 0`
  - `last_run_duration_ms INTEGER NULL`
- Extend `ScraperStatus` model and `DatabaseService.update_heartbeat()` to support structured metadata writes.
- Keep current fields and enum behavior intact for compatibility.

### Deliverables

- Migration file for additive operational metadata.
- Updated core model + database service signatures.

### Validation

- Migration applies/rolls back in local dev path.
- Unit tests for DB write/update semantics including:
  - success resets `consecutive_failures`,
  - failure increments `consecutive_failures`,
  - last-success fields preserved on failure.

### Dependencies and risks

- Dependency: migration tooling and CI DB test flow.
- Risk: incorrect update logic can overwrite last success.
- Mitigation: explicit tests for success->failure and failure->success transitions.

---

### Phase 2: Instrument Scraper Pipeline and Classify Failures

**Goal:** Implement deterministic failure classification and standardized reliability controls.

**Estimated effort:** 1.0 to 1.5 days

### Tasks

- Introduce shared run outcome structure (`ScraperRunResult`) in scraper orchestration path.
- Add `classify_scraper_failure(exception, stage)` utility.
- Standardize retry/backoff/timeouts per scraper:
  - Ontario/Alberta Playwright wrappers with bounded retry attempts.
  - Quebec paginated fetch retry strategy + explicit handling for partial page failures.
  - BC request fetch aligned with shared policy.
- Ensure heartbeat metadata writes include:
  - success path: last success and duration,
  - failure path: category, stage, message, consecutive failures.

### Deliverables

- Shared failure classification utility and tests.
- Refactored scraper run paths emitting structured outcomes.
- Reliability policy constants centralized (single source for attempts/backoff/timeout).

### Validation

- Unit tests per scraper path for retry behavior and classification mapping.
- Regression tests for existing parse outputs.
- CLI tests for `--all` mixed success/failure behavior.

### Dependencies and risks

- Dependency: stable exception mapping from Playwright, `httpx`, and parser code.
- Risk: over-retry increases run duration and overlaps cron windows.
- Mitigation: hard cap attempts and per-source timeout budgets; monitor run duration metric.

---

### Phase 3: Consolidated Operational View (CLI + `/api/health`)

**Goal:** Surface last-known-good + last-error in one place for humans and automation.

**Estimated effort:** 0.75 day

### Tasks

- Add backend operational query path that returns per-source:
  - current status,
  - last_run,
  - last_success_run,
  - last_error_run,
  - last_error_category,
  - last_error_stage,
  - error_message,
  - consecutive_failures,
  - age minutes.
- Extend `/api/health` response with additive operational fields (preserve existing keys).
- Add dedicated CLI status command or extend heartbeat CLI with `--verbose` operational table output.

### Deliverables

- Enhanced `/api/health` payload with structured operational diagnostics.
- CLI view for on-call triage without manual SQL.

### Validation

- Frontend API route tests updated for new health payload fields.
- CLI tests validate human-readable and machine-readable output modes.
- Manual smoke: one induced parser error and one induced upstream timeout produce distinct categories.

### Dependencies and risks

- Dependency: Phase 1 metadata fields present.
- Risk: accidental breaking change to existing health consumers.
- Mitigation: additive fields only; existing response keys untouched and tested.

---

### Phase 4: Workflow and Alerting Integration

**Goal:** Make new visibility actionable in operations workflows.

**Estimated effort:** 0.5 day

### Tasks

- Update `check_heartbeat` logic to evaluate:
  - stale heartbeat,
  - explicit error state,
  - consecutive failures threshold.
- Replace placeholder "Check scraper health" step in `scraper-cron.yml` with real operational summary call.
- Improve failure alert payload to include source, category, stage, and link to workflow run.
- Align threshold constants (temporary 90-minute policy) between workflows and `/api/health` contract.

### Deliverables

- Workflow-integrated failure summary.
- Alert messages carrying actionable failure classification.

### Validation

- Workflow dry-run/manual dispatch shows structured status output.
- Alert payload verification in logs (without exposing secrets).

### Dependencies and risks

- Dependency: secrets for alerting already configured.
- Risk: alert fatigue from classification noise.
- Mitigation: threshold gate for consecutive failures and dedup strategy by fingerprint.

---

### Phase 5: Documentation, Runbook, and Closeout

**Goal:** Ensure operators can use the new visibility and reliability model correctly.

**Estimated effort:** 0.5 day

### Tasks

- Update operations docs:
  - `docs/operations/QUICK_START.md`
  - `docs/operations/scraper-scheduling.md`
  - `docs/operations/OPERATIONAL_STATUS.md` (current-state references)
  - `.github/workflows/README.md` (actual schedule/threshold)
- Add triage decision tree:
  - `upstream_unavailable` -> monitor/retry/escalate source outage
  - `parser_breakage` -> parser fix + targeted tests
  - `infra_runtime` -> runner/browser/runtime remediation
  - `persistence_failure` -> DB connectivity/permission remediation
- Update roadmap item notes to reference this plan once implementation starts.

### Deliverables

- Updated runbook and workflow docs aligned to reality.
- Milestone closeout checklist.

### Validation

- Docs consistency checks pass.
- Manual operator walkthrough can triage a simulated failure in under 10 minutes.

### Dependencies and risks

- Dependency: phases 1-4 complete.
- Risk: docs drift reappears with future cadence changes.
- Mitigation: centralize operational thresholds in code constants and reference them in docs.

---

## High-Level Timeline and Milestones

Assuming one maintainer and normal CI turnaround.

| Day | Milestone | Outcome |
|-----|-----------|---------|
| Day 1 | M30-A Baseline + contract freeze | taxonomy and API extension contract approved |
| Day 1-2 | M30-B Data model + metadata writes | structured failure metadata persisted |
| Day 2-3 | M30-C Scraper reliability hardening | standardized retry/backoff/timeouts + classification |
| Day 3 | M30-D Operational view | CLI + `/api/health` visibility complete |
| Day 4 | M30-E Workflow integration | heartbeat + alerting consume new metadata |
| Day 4-5 | M30-F Docs + stabilization | runbook finalized, regression checks complete |

Target completion window: 4 to 5 working days.

---

## Validation Strategy (Progress and Quality Gates)

### Automated validation

- Backend unit tests (classification, heartbeat metadata, scraper retries).
- Existing scraper unit tests (no parser regressions).
- Frontend API route tests for `/api/health` shape and status logic.
- Integration tests for heartbeat state transitions where feasible.

### Manual validation

- Trigger one controlled upstream timeout and one controlled parser mismatch.
- Confirm both are distinguishable in:
  - `scraper_status` metadata,
  - CLI operational output,
  - `/api/health` response,
  - workflow logs/alerts.

### Exit criteria for completion

- Both roadmap items can be marked complete with objective evidence:
  - screenshots/log snippets of operational view,
  - tests added and passing,
  - docs/runbook updated.

---

## Rollout and Rollback Approach

### Rollout

1. Deploy additive migration first (safe, no behavior change).
2. Deploy dual-write metadata updates in scraper runtime.
3. Enable read path in `/api/health` and CLI.
4. Turn on workflow/alert enrichment.
5. Monitor 48 hours before marking roadmap items complete.

### Rollback

1. Revert application code to previous release while leaving additive columns in place.
2. Keep legacy heartbeat fields (`status`, `error_message`, `last_run`) as primary source.
3. If alert noise occurs, temporarily disable enriched failure-based alerts and keep stale-only checks.
4. If classification logic misbehaves, route all failures to `unknown` category while preserving raw error text.

Rollback is low risk because schema changes are additive and legacy fields remain valid.

---

## Dependencies, Risks, and Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Retry policy increases runtime and overlaps cron windows | Medium | Medium | cap attempts, cap per-source timeout, monitor run duration |
| Classification false positives (parser vs upstream) | Medium | Medium | deterministic mapping + `unknown` fallback + fixtures |
| Backward incompatibility in `/api/health` | High | Low | additive-only response changes + existing test coverage |
| Alert fatigue from transient errors | Medium | Medium | consecutive-failure threshold and dedup fingerprint |
| Documentation drift on thresholds/cadence | Medium | High | single source constants + docs updates in same PR |

---

## Resource and Scope Alignment

- This plan stays within current project constraints:
  - no new paid infrastructure,
  - no changes to core observatory purpose,
  - focused only on reliability and operational transparency.
- Implementation prioritizes clinically defensible audit posture:
  - transparent failure reporting,
  - explicit uncertainty about data freshness,
  - no silent suppression of data collection issues.

---

## Implementation Checklist (For Execution Phase)

- [x] Phase 0 baseline captured and taxonomy approved
- [x] Phase 1 migration + metadata model updates
- [x] Phase 2 classification + reliability policy implemented
- [x] Phase 3 CLI + `/api/health` operational view complete
- [x] Phase 4 workflow + alert integration complete
- [x] Phase 5 docs/runbook updates complete
- [x] Roadmap items (lines 94 and 95) marked complete with evidence
