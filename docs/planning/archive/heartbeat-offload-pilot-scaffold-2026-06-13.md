# Public-Safe Heartbeat Offload Pilot Scaffold

**Date:** 2026-06-13
**Status:** Complete

## Purpose

Create the public repository scaffold for ADR-0027's first trusted-runner
offload pilot without adding private infrastructure, runner registration,
secrets, live schedules, or executable Forgejo workflow files.

## Scope

- Document the heartbeat checker command contract for a trusted offloaded
  runner.
- Document required and optional environment variable names without values.
- Define exit-code behavior for healthy and stale/error states.
- Keep GitHub `workflow_dispatch` as the fallback path while schedules remain
  constrained.
- Add a copy/adapt-only Forgejo Actions example under documentation, not under
  an executable workflow path.
- Add a public pilot checklist for private dry-run, manual live check, output
  comparison, log hygiene, and private scheduling gates.
- Link the public guide from the documentation index and operations navigation.

## Delivered Artifacts

- `docs/operations/heartbeat-offload-pilot.md`
- `docs/operations/examples/forgejo-heartbeat-monitor.yml`
- `docs/README.md`
- `docs/planning/manual-tasks.md`
- `mkdocs.yml`

## Out Of Scope

- Private runner provisioning.
- Secret creation or secret value documentation.
- Runner tokens, private hostnames, private paths, alert routes, or production
  connection strings.
- Enabling `.forgejo/workflows` or any private schedule from this public
  repository.
- Running the heartbeat checker against live credentials.
- Running Playwright locally.

## Remaining Follow-Up

The remaining pilot work is private/manual: provision the trusted runner, add
secrets in the private runner store, perform the dry run and one real manual
heartbeat check, compare behavior with the GitHub manual fallback, confirm logs
are clean, and only then enable a private schedule outside this repository.

## Verification

- `bash -n scripts/check-docs.sh`
- `bash scripts/check-docs.sh`
- `git diff --check`
- YAML syntax parse for `mkdocs.yml` and the copy/adapt Forgejo example
- Focused heartbeat CLI unit tests
- GitHub Docs CI
