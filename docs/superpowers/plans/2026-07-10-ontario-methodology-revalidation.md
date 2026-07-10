# Ontario Methodology Revalidation Containment Plan

**Goal:** Stop public research and methodology documents from presenting the
repository's legacy Ontario ontology tags as an exact transcription of the
current official indicator, while preserving the existing runtime and data
model until an explicit ontology and historical-data decision is made.

**Status:** Implementation verified; independent review and delivery pending

**Base:** `main` at `18dbcfef4e3c44695c2433b763d7f48e15deb124`

## Problem Statement

The repository currently maps Ontario's public wait-to-first-assessment metric
as `TIME_TO_PROVIDER`, `TRIAGE -> PHYSICIAN`, `MEAN`. Several public documents
describe those event tags as the current official methodology.

The official Ontario Health indicator page, verified on 2026-07-10, instead
defines the metric as:

- start: triage or registration, whichever is earlier;
- end: initial assessment by a doctor, nurse practitioner, physician
  assistant, or dentist, whichever qualifying assessment is earlier; and
- statistic: arithmetic average.

Official source:
<https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments>

The current `StartEvent` enum cannot encode "earlier of triage or registration"
as one exact value. Changing the runtime mapping also raises a historical-data
question: existing measurements and source rows already carry the legacy tags.
Silently changing only new measurements would split one source's history across
two ontology definitions.

## Decision For This Batch

Apply a documentation containment correction only:

1. distinguish the repository's current implementation tags from the official
   indicator definition;
2. mark affected research conclusions as requiring Ontario revalidation;
3. preserve the safe conclusion that direct cross-province performance
   comparison is invalid;
4. add a durable manual decision item with exact resolution criteria; and
5. add regression tests so the qualification cannot disappear while the
   legacy tags remain.

## Non-Goals

- Do not change ontology enums.
- Do not change `backend/data/sources/ontario-health.json`.
- Do not change scraper output, measurement creation, API behavior, or frontend
  labels.
- Do not edit an old migration or add a database migration.
- Do not update production data, deploy, release, or inspect secrets.
- Do not choose between extending the ontology and using a conservative
  existing fallback such as `UNKNOWN -> PROVIDER`.

## Resolution Required After This Batch

An owner-reviewed follow-up must decide all of the following together:

1. the exact ontology representation for the composite start event and broader
   provider endpoint;
2. whether new enum values are required;
3. how existing source metadata and historical measurements are migrated or
   versioned;
4. how comparability and divergence briefs change; and
5. how frontend methodology labels communicate the new definition.

The follow-up must include a migration/backfill plan, parser/source versioning,
tests, public documentation, and validation against the official indicator.

## Files

- Modify: `backend/docs/methodologies/ontario-reference.json`
- Modify: `backend/docs/methodologies/ontario-methodology.md`
- Modify: `docs/ontario-methodology.md`
- Modify: `docs/ontario-research-findings.md`
- Modify: `docs/case-studies/ottawa-gatineau-divergence.md`
- Modify:
  `docs/research/methodological-heterogeneity-four-province-audit-draft.md`
- Modify: `docs/planning/manual-tasks.md`
- Modify: `backend/tests/unit/test_methodology_docs.py`
- Modify: this plan

## Task 1: Add Failing Documentation-Contract Tests

- [x] Add assertions that the structured Ontario reference records:
  - revalidation status;
  - the official composite start and provider endpoint;
  - that the repository tags are implementation tags pending resolution; and
  - the current official Ontario Health URL.
- [x] Add assertions that the maintained Ontario methodology Markdown, public
  mirror, research draft, and Ottawa-Gatineau case study visibly state that
  Ontario revalidation is required.
- [x] Run the focused tests and record the expected failures before editing the
  documents.

Focused command:

```bash
cd backend
uv run pytest tests/unit/test_methodology_docs.py -q
```

## Task 2: Correct The Canonical Ontario Methodology Records

- [x] Update `ontario-reference.json` to separate `repository_mapping` from the
  official indicator definition without changing the repository mapping.
- [x] Replace the stale HQOntario methodology reference with the current
  Ontario Health indicator URL.
- [x] Update the maintained Markdown and its public mirror with a prominent
  revalidation notice and exact official definition.
- [x] Qualify within- and cross-province statements as descriptions of current
  repository tags, not source-faithful official event boundaries.

## Task 3: Contain Research Claims And Record The Decision

- [x] Mark the four-province audit draft as paused for Ontario methodology
  revalidation.
- [x] Mark the Ottawa-Gatineau case study as requiring revalidation; retain its
  non-comparability conclusion while removing the unsupported claim that the
  current official Ontario clock starts only at triage and ends only at a
  physician.
- [x] Add a correction note to the historical Ontario research findings.
- [x] Add one manual task pointing to this plan and listing the ontology,
  historical-data, UI, and migration decisions needed for full resolution.

## Task 4: Verify, Review, And Deliver

- [x] Run focused methodology documentation tests.
- [x] Run Ruff formatting and lint for the changed test.
- [x] Run `bash scripts/check-docs.sh`.
- [x] Run the full backend test suite because a canonical structured methodology
  artifact and its tests changed.
- [x] Run `git diff --check` and confirm no runtime/source/migration/frontend
  files changed.
- [ ] Request independent review and address critical or important findings.
- [x] Commit in reviewable steps.
- [ ] Push `codex/ontario-methodology-revalidation` and open a ready PR.
- [ ] Do not merge: changed documentation paths trigger deployment on `main`.
- [ ] Verify all GitHub checks on the exact final PR head.

## Baseline Evidence

- `bash scripts/check-docs.sh`: all 11 groups passed.
- Focused baseline:
  `uv run pytest tests/unit/test_methodology_docs.py tests/unit/test_source_consistency.py -q`
  passed 19 tests.
- No source, schema, data, production, secret, deployment, or release action was
  performed during discovery.

## Completion Record

### TDD And Implementation

- RED: the focused methodology module collected 21 tests with 6 expected
  failures: missing structured revalidation metadata plus missing visible
  notices in the five affected public artifacts.
- GREEN: `test_methodology_docs.py` passed all 21 tests after the containment
  update.
- Combined focused verification:
  `test_methodology_docs.py` plus `test_source_consistency.py` passed all 25
  tests.
- Plan commit: `5200345d`.
- Containment implementation commit: `ad5394f7`.

### Full Local Verification

- `bash scripts/check-docs.sh`: all 11 groups passed.
- `uv run ruff format --check tests/unit/test_methodology_docs.py`: passed.
- `uv run ruff check tests/unit/test_methodology_docs.py`: passed.
- `uv run pytest -q`: 585 passed and 27 prerequisite-dependent skips in 26.30
  seconds.
- `git diff --check`: passed.
- Exact changed surfaces: methodology/reference documentation, the historical
  research artifacts, manual task ledger, one methodology-doc test, and this
  plan. No runtime source catalog, scraper, migration, frontend, schema, or data
  file changed.
- Pre-commit hooks passed, including JSON validation, Ruff, secret scanning,
  and authorship guardrails.

### Remaining Boundary

Full ontology remediation remains intentionally unresolved. The manual task
retains the exact owner decision required: composite start, qualifying-provider
endpoint, historical migration or versioning, source metadata, divergence
briefs, and frontend labels must be handled together rather than through a
partial tag change.

Independent review, PR details, final head SHA, and CI run IDs remain to be
recorded.
