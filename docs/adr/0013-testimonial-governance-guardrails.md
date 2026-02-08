# ADR 0013: Testimonial Governance Guardrails

## Status
Accepted (2026-02-08)

## Context
Stakeholder testimonials are high-trust content. Without explicit validation rules, accidental
mispublication (multiple quotes, missing consent trail, incomplete attribution) can undermine
professional credibility.

## Decision
Apply fail-closed testimonial governance in the frontend content layer:

1. Allow at most one `published: true` testimonial.
2. Require `publishedAt` and `approvalReference` for published testimonials.
3. Require `displayName` when attribution is `named`.
4. Prevent rendering unpublished testimonials.
5. If dataset validation fails, render no testimonial.

## Consequences

### Positive
- Prevents accidental over-publication.
- Enforces a lightweight consent audit trail for published quotes.
- Keeps homepage behavior deterministic and conservative.

### Tradeoff
- Slightly stricter editorial workflow when adding new testimonials.

## Follow-Up
1. Keep `approvalReference` linked to interview/consent notes.
2. Revisit schema if multiple published testimonials are intentionally introduced in future.
