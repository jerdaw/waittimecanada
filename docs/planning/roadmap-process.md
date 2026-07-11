# Roadmap Process

`docs/planning/roadmap.md` is the single public source of truth for project
status and strategic direction. `docs/planning/manual-tasks.md` is its companion
for human decisions, external operations, recurring reviews, and conditional
follow-ups.

## Canonical Structure

Keep roadmap sections in this order:

1. `Current Snapshot`
2. `Completed Foundations`
3. `Continuous Guardrails`
4. `Execution Queue`
5. `Completed Milestones`
6. architecture, ADR, schema, and historical implementation references

Do not add a second active-priority list or repeat the execution queue in
README. Historical session chronology belongs in maintenance records, closed
plans, and Git history.

## Current Snapshot

Update the snapshot only when public project state changes. Keep it concise,
mention the latest completed milestone, and align its `YYYY-MM-DD` date with
README's roadmap baseline and Current Status dates. Do not append session logs.

## Continuous Guardrails

Guardrails are permanent invariants, not finite tasks. Use ordinary bullets,
never task-list checkboxes. Preserve clinical safety, ontology comparability,
source provenance, freshness visibility, retention, cost controls, and the
public/private documentation boundary.

## Execution Queue

Use one Markdown table with columns in this exact order:

| Priority | Outcome | State | Gate | Done when |
| --- | --- | --- | --- | --- |

Allowed priorities are `P0`, `P1`, and `P2`. Every row must name a finite
outcome, its current state, the dependency or decision gate, and an observable
completion condition.

Allowed states:

- `Ready`: repository work can start without a missing decision or external prerequisite.
- `Decision required`: an owner-approved product, methodology, legal, or data decision is missing.
- `External prerequisite`: credentials, infrastructure, an official source, or another external state is missing.
- `In validation`: implementation exists and an observation or acceptance window is active.
- `Later`: the trigger for reconsideration has not occurred.

Do not invent owner names or dates when work is gated. Use state and gate to
make the dependency explicit.

## Manual Task Ledger

Group manual tasks under `Decision Required`, `External Operations`, `Recurring
Reviews`, `Conditional Follow-Ups`, or `Completed Repository Prerequisites`.
State the trigger for recurring and conditional work. Link to the roadmap
outcome or public contract rather than restating a competing backlog.

## Lifecycle

- When a finite outcome is completed, move its durable result to Completed
  Foundations, Completed Milestones, or the appropriate historical record.
- Keep operator work open until its observable acceptance evidence exists.
- Archive closed implementation plans that are no longer living records.
- Update README status dates only when the roadmap's public baseline changes.
- Run `backend/scripts/verify_roadmap_consistency.py` and
  `scripts/check-docs.sh` for every roadmap change.

## Public Alignment

Every roadmap update must preserve non-medical-advice and non-triage boundaries,
the four-field direct-comparison rule, official-source attribution, methodology
limitations, and separation of public reproducible guidance from private
operations detail.
