# Roadmap Optimization Design

**Status:** Approved for implementation planning

## Context

`docs/planning/roadmap.md` is the public planning source of truth, but its
current structure mixes four different concerns:

1. a long chronological maintenance history;
2. a narrative `Active Priorities` list;
3. a second checkbox-based `Active Roadmap` list; and
4. permanent safety and stewardship invariants presented as unfinished tasks.

This makes the document accurate but harder to scan and creates false backlog:
continuous safeguards look like finite deliverables, duplicated priorities can
drift, and actionable work does not consistently name its dependency or
completion condition. `docs/planning/manual-tasks.md` also repeats several
roadmap items without consistently identifying whether they are recurring,
decision-gated, external, or conditional.

PR #89 is the required base for this work. It completes the repository-side
offloaded-operations documentation contract while correctly leaving runner
selection, provisioning, credentials, live validation, schedule cutover, and
the 24-hour soak open. Its private companion currently remains a separate
delivery dependency and must not be summarized with private environment detail
in this public repository.

## Goals

- Make the roadmap useful to both public readers and maintainers without
  creating separate competing status documents.
- Keep a short, stable public strategy summary at the top.
- Separate continuous safeguards from finite deliverables.
- Make each finite deliverable state its priority, current state, dependency or
  gate, and observable definition of done.
- Keep manual and external work visible without implying it can be completed by
  repository-only changes.
- Remove duplicated active-priority prose and relocate historical chronology to
  existing durable maintenance records.
- Enforce the new structure with repository tests and documentation checks.
- Preserve clinical-safety, ontology, provenance, storage, cost, and public
  documentation boundaries.

## Non-Goals

- Do not select or provision a trusted runner.
- Do not access credentials, private operations notes, or environment-specific
  deployment information.
- Do not run live scrapes, change schedules, remove fallbacks, deploy, or
  release.
- Do not resolve the Ontario ontology decision, choose new data sources, or
  invent dates for externally gated work.
- Do not renumber completed milestones or rewrite historical implementation
  records.
- Do not turn recurring stewardship into artificial one-time completion work.

## Approaches Considered

### 1. Minimal editorial cleanup

Shorten the current status and remove obvious duplicate bullets while retaining
the existing `Now`/`Next`/`Later` checkbox layout.

This is low risk, but it does not solve false TODOs or make dependencies and
completion criteria enforceable.

### 2. Maintainer-only execution board

Replace most narrative content with a detailed internal-style execution table.

This is highly actionable, but it weakens the roadmap's role as a public project
summary and risks leaking operational detail that belongs in the private/shared
operations source of truth.

### 3. Hybrid public strategy and execution queue

Keep a concise public snapshot, then provide separate continuous guardrails and
a structured finite execution queue. Use the manual-task ledger for recurring,
decision-gated, external, and conditional follow-ups.

This is the selected approach because it improves scanability and execution
clarity while preserving one public source of truth and the existing public/
private boundary.

## Roadmap Information Architecture

The optimized roadmap will use this order:

1. `Current Snapshot`
2. `Completed Foundations`
3. `Continuous Guardrails`
4. `Execution Queue`
5. `Completed Milestones`
6. architecture, ADR, schema, and historical reference sections already used by
   consistency checks

### Current Snapshot

Replace the chronological status essay with a short summary that states:

- Milestone 33 is the latest completed milestone;
- the project is in stewardship and selective expansion;
- four-province and Ontario-first public-health scope;
- the current operational focus is the trusted source-freshness pilot; and
- repository hardening is complete while live runner validation remains gated.

The snapshot must remain aligned with the README date and latest-milestone
contract. Historical maintenance waves remain available in
`docs/maintenance-audit.md`, archived maintenance logs, closed plans, and Git
history rather than being repeated in the current snapshot.

### Continuous Guardrails

Permanent responsibilities will be ordinary bullets, not checkboxes. They will
cover:

- clinical safety and non-triage boundaries;
- four-field ontology comparability;
- source freshness and data-quality visibility;
- 30-day raw retention with permanent aggregates;
- provenance and official-source attribution;
- public/private documentation separation;
- low-frequency health polling, cache, and production cost controls; and
- manual-dispatch fallback until an offload proof window is accepted.

These are invariants with no terminal completion state. They remain testable
through existing documentation and code contracts.

### Execution Queue

Finite work will use one Markdown table with these columns:

| Field | Meaning |
| --- | --- |
| Priority | `P0`, `P1`, or `P2` using the existing priority definitions |
| Outcome | A finite user-, research-, or operations-facing result |
| State | `Ready`, `Decision required`, `External prerequisite`, `In validation`, or `Later` |
| Gate | The dependency that must be satisfied before or during work |
| Done when | An observable repository or operator acceptance condition |

The initial queue will contain only currently supported work:

- complete and observe the trusted source-freshness offload pilot;
- restore remaining scheduled cadence after a successful proof window;
- resolve Ontario methodology representation before runtime-tag changes;
- extend public methodology artifacts after Ontario revalidation or another
  verified methodology change;
- select public-health resource expansion only after official-source and reuse
  review;
- evaluate additional provinces only after a stable official source is found;
- explore smarter scheduling after freshness evidence establishes safe bounds;
  and
- reassess broader CI migration only if the hybrid offload pilot fails its
  reliability or cost objectives.

No invented owner name or target date will be added. State and gate provide
honest scheduling information when work depends on decisions or external state.

## Manual Task Ledger

`docs/planning/manual-tasks.md` will become the operational companion to the
roadmap rather than a duplicate backlog. Entries will be grouped by type:

- `Decision Required`
- `External Operations`
- `Recurring Reviews`
- `Conditional Follow-Ups`

Each manual task will link to the relevant roadmap outcome or contract and state
its trigger. The ledger will retain Ontario revalidation, trusted-runner pilot,
24-hour observation, cadence restoration, quarterly provenance review,
release-time review, methodology-change review, screenshot refresh, case-study
refresh, and privacy/legal review. The completed repository-side offload
hardening item from PR #89 will remain recorded as complete without duplicating
the live pilot task.

## Planning Process Contract

`docs/planning/roadmap-process.md` will be aligned with the actual document:

- update the snapshot when public project state changes, not by appending a new
  maintenance paragraph each session;
- keep continuous guardrails free of checkboxes;
- add finite work only when outcome, state, gate, and definition of done are
  known;
- move completed finite outcomes to the appropriate milestone, foundation, or
  durable completion record;
- keep recurring and operator-dependent work in the manual ledger; and
- update README status dates only when the roadmap's public baseline changes.

## README Alignment

README's checkbox-based `Future Roadmap` section will be replaced with a short
non-checkbox summary of the finite outcome categories plus a direct link to the
canonical execution queue. README will continue to state the latest completed
milestone and matching roadmap baseline date, but it will no longer act as a
second backlog that can drift from `docs/planning/roadmap.md`.

## Validation Design

`backend/scripts/verify_roadmap_consistency.py` will gain pure validation for the
optimized structure. The checker will require:

- exactly one `## Continuous Guardrails` section;
- no task-list checkboxes inside that section;
- exactly one `## Execution Queue` table;
- the five required columns in the defined order;
- only the allowed priority and state values;
- non-empty outcome, gate, and done-when cells; and
- removal of the legacy `## Active Priorities` and `## Active Roadmap`
  sections.

`backend/tests/unit/test_verify_roadmap_consistency.py` will use synthetic
roadmaps to prove valid structure passes and each structural regression fails
with an actionable message. The repository-level documentation check will then
validate the real roadmap through `scripts/check-docs.sh`.

The existing schema-count, ADR-reference, implementation-plan, milestone,
status-date, README-alignment, clinical-safety, and comparability checks remain
in force.

## Delivery Strategy

The implementation branch is stacked on PR #89 so the roadmap does not
reintroduce the completed repository-side hardening item. The roadmap change
will be reviewed independently and validated against the exact stacked head.

The optimized roadmap PR must not be merged ahead of PR #89. After PR #89 is
merged, the roadmap branch must be rebased or otherwise updated onto the new
`main`, all affected checks rerun, and the final diff reviewed for accidental
loss of the offload contract. Automatic documentation publication caused by a
later authorized merge remains a separate delivery action.

## Success Criteria

- A reader can identify current project state, permanent safeguards, and finite
  remaining work without reading historical maintenance chronology.
- Every finite roadmap outcome has an explicit state, gate, and definition of
  done.
- No continuous invariant appears as an unfinished checkbox.
- Manual tasks are typed by trigger and do not compete with the roadmap.
- PR #89's completed repository hardening remains completed while its live pilot
  remains open.
- The roadmap consistency unit tests and all documentation gates pass.
- No private operational detail, credential value, deployment path, or
  environment-specific runner information is introduced.
