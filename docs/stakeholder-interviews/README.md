# Stakeholder Interview Toolkit

This folder contains templates for M9 Phase 3 stakeholder validation.

## Files

- `outreach-template.md` - first-contact message template
- `interview-template.md` - guided 15-minute interview script + note capture
- `participant-intake-template.md` - participant metadata and consent check

## Workflow

1. Copy `participant-intake-template.md` for each participant.
2. Send outreach using `outreach-template.md`.
3. Run the interview using `interview-template.md`.
4. Summarize results in `docs/stakeholder-feedback.md`.
5. Convert actionable items into roadmap or implementation tasks.

## Publishing A Testimonial

1. Open `frontend/content/stakeholderTestimonials.ts`.
2. Add one entry with `published: true` and appropriate `attribution`.
3. Keep only approved quotes in this file.
4. The homepage will render the testimonial automatically when a published entry exists.

## Data Handling

- Do not store personal contact details beyond what is needed for follow-up.
- Only include direct quotes when explicit permission is documented.
- Keep role/title context when possible, but anonymize names if requested.

Last Updated: 2026-02-08
