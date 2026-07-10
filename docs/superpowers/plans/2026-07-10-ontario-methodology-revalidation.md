# Ontario Methodology Revalidation Containment Plan

**Goal:** Stop public research and methodology documents from presenting the
repository's legacy Ontario ontology tags as an exact transcription of the
current official indicator, while preserving the existing runtime and data
model until an explicit ontology and historical-data decision is made.

**Status:** In progress

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

- [ ] Add assertions that the structured Ontario reference records:
  - revalidation status;
  - the official composite start and provider endpoint;
  - that the repository tags are implementation tags pending resolution; and
  - the current official Ontario Health URL.
- [ ] Add assertions that the maintained Ontario methodology Markdown, public
  mirror, research draft, and Ottawa-Gatineau case study visibly state that
  Ontario revalidation is required.
- [ ] Run the focused tests and record the expected failures before editing the
  documents.

Focused command:

```bash
cd backend
uv run pytest tests/unit/test_methodology_docs.py -q
```

## Task 2: Correct The Canonical Ontario Methodology Records

- [ ] Update `ontario-reference.json` to separate `repository_mapping` from the
  official indicator definition without changing the repository mapping.
- [ ] Replace the stale HQOntario methodology reference with the current
  Ontario Health indicator URL.
- [ ] Update the maintained Markdown and its public mirror with a prominent
  revalidation notice and exact official definition.
- [ ] Qualify within- and cross-province statements as descriptions of current
  repository tags, not source-faithful official event boundaries.

## Task 3: Contain Research Claims And Record The Decision

- [ ] Mark the four-province audit draft as paused for Ontario methodology
  revalidation.
- [ ] Mark the Ottawa-Gatineau case study as requiring revalidation; retain its
  non-comparability conclusion while removing the unsupported claim that the
  current official Ontario clock starts only at triage and ends only at a
  physician.
- [ ] Add a correction note to the historical Ontario research findings.
- [ ] Add one manual task pointing to this plan and listing the ontology,
  historical-data, UI, and migration decisions needed for full resolution.

## Task 4: Verify, Review, And Deliver

- [ ] Run focused methodology documentation tests.
- [ ] Run Ruff formatting and lint for the changed test.
- [ ] Run `bash scripts/check-docs.sh`.
- [ ] Run the full backend test suite because a canonical structured methodology
  artifact and its tests changed.
- [ ] Run `git diff --check` and confirm no runtime/source/migration/frontend
  files changed.
- [ ] Request independent review and address critical or important findings.
- [ ] Commit in reviewable steps.
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

Update this section with RED/GREEN results, exact command output, commit SHAs,
review findings, PR URL, final head SHA, and CI run IDs. If full remediation is
still blocked, retain the manual task and state the precise owner decision
required rather than repeatedly retrying a partial mapping change.
