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
- [ ] Re-run public status alignment after each completed milestone so README,
  roadmap, and planning indexes keep the same current-state baseline.
- [ ] Pilot ADR-0027 CI offload with heartbeat/status checks on a trusted
  runner using `docs/operations/heartbeat-offload-pilot.md`, keeping GitHub
  manual dispatch as fallback.
- [ ] Confirm a new GitHub `event=schedule` run for `scraper-cron.yml` after
  the 2026-07-08 recovery; heartbeat schedule creation has recovered, but keep
  manual scraper dispatch or a trusted external scheduler fallback active until
  scraper schedule evidence exists.
- [ ] Restore remaining scheduled operational workflows incrementally after the
  trusted heartbeat/status offload pilot succeeds; keep manual dispatch as the
  fallback path.
- [ ] Before moving scraper cron or public-health ingest off GitHub, document
  runner isolation, secret handling, log retention, failure summaries, and
  rollback steps in the private/shared operations source of truth.
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
