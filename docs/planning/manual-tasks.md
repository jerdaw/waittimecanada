# Manual Tasks

This file tracks public, non-secret manual follow-ups that are useful to
contributors and maintainers. Private deployment runbooks, credentials,
monitoring configuration, and personal planning notes are intentionally excluded
from public documentation.

## Public Follow-Ups

- [ ] Review public data-source links quarterly and update stale provenance
  URLs.
- [ ] Re-run public documentation boundary review before major releases.
- [ ] Re-run methodology documentation review after any provincial reporting
  change.
- [ ] Restore scheduled operational workflows after GitHub Actions quota resets;
  use manual dispatch in the meantime.
- [ ] Capture updated demo screenshots after major frontend changes.
- [ ] Refresh public case studies when source methodology or displayed examples
  change.
- [ ] Review `/privacy` and `/terms` after any new data flow or third-party
  service is introduced.

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
