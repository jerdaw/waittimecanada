# Roadmap Process

`docs/planning/roadmap.md` is the single public source of truth for project
status and strategic direction. `docs/planning/manual-tasks.md` is its companion
for event-triggered human stewardship. Neither file creates a standing manual
work queue.

## Canonical Structure

Keep roadmap sections in this order:

1. `Current Snapshot`
2. `Completed Foundations`
3. `Continuous Guardrails`
4. `Event-Triggered Stewardship`
5. `Completed Milestones`
6. architecture, ADR, schema, and historical implementation references

Do not add an active-priority list, recurring review cadence, or external
operations queue. Historical session chronology belongs in maintenance records,
closed plans, and Git history.

## Current Snapshot

Update the snapshot only when public project state changes. Keep it concise,
mention the latest completed milestone, and align its `YYYY-MM-DD` date with
README's roadmap baseline and Current Status dates. Do not append session logs.

## Continuous Guardrails

Guardrails are permanent invariants, not finite tasks. Use ordinary bullets,
never task-list checkboxes. Preserve clinical safety, ontology comparability,
source provenance, freshness visibility, retention, cost controls, and the
public/private documentation boundary.

## Event-Triggered Stewardship

Use one Markdown table with columns in this exact order:

| Trigger | Bounded response | Stop condition |
| ------- | ---------------- | -------------- |

Every row must name a concrete public-service trigger, the smallest permitted
response, and an observable stop condition. Triggers are not tasks and must not
be represented with owners, target dates, priorities, or checkboxes.

The section must state that there is no standing implementation or manual-review
queue. Parked methodology, infrastructure, research, and expansion ideas remain
historical until an explicit new project decision activates one.

## Stewardship Trigger Reference

`manual-tasks.md` records the same dormant posture in contributor-facing terms:
what automation handles, which concrete events permit human action, and which
older proposals are parked. It must not contain open task-list checkboxes,
calendar-based reviews, or an external-operations campaign.

## Lifecycle

- When a finite outcome is completed, move its durable result to Completed
  Foundations, Completed Milestones, or the appropriate historical record.
- Close bounded incident work when its observable stop condition is met.
- Archive closed implementation plans that are no longer living records.
- Update README status dates only when the roadmap's public baseline changes.
- Run `backend/scripts/verify_roadmap_consistency.py` and
  `scripts/check-docs.sh` for every roadmap change.

## Public Alignment

Every roadmap update must preserve non-medical-advice and non-triage boundaries,
the four-field direct-comparison rule, official-source attribution, methodology
limitations, and separation of public reproducible guidance from private
operations detail.
