# Manual Tasks

This file tracks public, non-secret manual follow-ups that are useful to
contributors and maintainers. Private deployment runbooks, credentials,
monitoring configuration, and personal planning notes are intentionally excluded
from public documentation.

## Decision Required

- [ ] Resolve the Ontario methodology representation before changing runtime
  tags or treating paused Ontario research artifacts as current. Use the exact
  decision scope in the roadmap execution queue.

## External Operations

- [ ] Complete the trusted source-freshness offload pilot using
  `docs/operations/heartbeat-offload-pilot.md`; keep GitHub manual dispatch as
  fallback.
- [ ] After the first complete 24-hour proof window, compare workflow history,
  `/api/status`, and `/api/data-quality` with the accepted cadence.
- [ ] Restore remaining scheduled workflows only after the proof window and
  rollback evidence are accepted.

## Recurring Reviews

- [ ] Quarterly: review public source links and update stale provenance URLs.
- [ ] After each completed milestone: align README, roadmap, and planning
  indexes.

## Conditional Follow-Ups

- [ ] Before a major release: re-run the public documentation boundary review.
- [ ] After a provincial reporting change: re-run methodology documentation
  review and update affected artifacts.
- [ ] After a major frontend change: capture updated demo screenshots.
- [ ] After source methodology or displayed examples change: refresh affected
  public case studies.
- [ ] After a new data flow or third-party service is introduced: review
  `/privacy` and `/terms`.

## Completed Repository Prerequisites

- [x] Runner isolation, secret handling, log retention, failure-summary, and
  rollback requirements are documented in the public offload contract, with
  the concrete value-free operator procedure retained in the private/shared
  operations source of truth.

## Review Checklist

- Emergency and non-triage disclaimers remain prominent.
- Methodology caveats are not weakened.
- Public docs avoid private hostnames, paths, credentials, runbooks, and
  personal strategy notes.
- Source attribution links point to official provincial or federal sources.
- Durable private project notes live in the private/shared operations source
  of truth; ignored `private/` folders may exist locally only as convenience
  copies.
- Actual secrets remain in Bitwarden or deployment environments, not Git.
