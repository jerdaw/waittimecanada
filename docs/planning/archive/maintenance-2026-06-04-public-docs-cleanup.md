# Maintenance: Public Documentation Cleanup

Date: 2026-06-04

Status: Archived

## Summary

Completed a public documentation hygiene pass that separated public project
documentation from private maintainer material. The public repository now
focuses on reproducible local development, methodology, limitations, public
source attribution, API behavior, and contributor guidance.

## Completed

- Moved private operations notes, private deployment scripts, environment-
  specific runbooks, personal planning material, and stale implementation notes
  out of tracked public documentation.
- Preserved private material under ignored local `private/` paths.
- Updated public docs to avoid private deployment paths, private alerting
  details, application-oriented positioning, and non-human attribution.
- Added ADR-0026 to define the public documentation boundary.
- Kept emergency disclaimers, methodology caveats, and source attribution in
  public documentation.

## Follow-Up

Ongoing documentation hygiene remains tracked through
`docs/planning/roadmap.md` and `docs/planning/manual-tasks.md`.
