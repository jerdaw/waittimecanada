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
- [ ] Resolve the Ontario methodology revalidation in
  `docs/superpowers/plans/2026-07-10-ontario-methodology-revalidation.md` before
  changing runtime tags or treating the paused research artifacts as current.
  Decide the composite start, qualifying-provider endpoint, historical
  migration or versioning, source metadata, divergence briefs, and frontend
  labels together.
- [ ] Re-run public status alignment after each completed milestone so README,
  roadmap, and planning indexes keep the same current-state baseline.
- [ ] Pilot ADR-0027 source-freshness offload with scraper, watchdog, aggregate,
  and smoke commands on a trusted runner using
  `docs/operations/heartbeat-offload-pilot.md`, keeping GitHub manual dispatch
  as fallback.
- [ ] Review scraper, heartbeat, and heartbeat-triggered scraper recovery
  history after the first full 24-hour recovery window so `/api/status` and
  `/api/data-quality` can be checked against sustained cadence rather than
  one-off recovery evidence.
- [ ] Restore remaining scheduled operational workflows incrementally after the
  trusted source-freshness offload pilot succeeds; keep manual dispatch as the
  fallback path.
- [x] Runner isolation, secret handling, log retention, failure-summary, and
  rollback requirements are documented in
  `docs/operations/heartbeat-offload-pilot.md`, with the concrete operator
  procedure in the private/shared operations source of truth. Live runner
  selection, validation, and cutover remain open in the pilot task above.
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
