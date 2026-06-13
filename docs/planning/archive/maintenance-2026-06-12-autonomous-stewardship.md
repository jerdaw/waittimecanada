# Maintenance: Autonomous Public Stewardship Pass

**Date:** 2026-06-12
**Status:** Complete

## Purpose

This pass covers repository work that can be completed autonomously without
secret access, deployment authority, production changes, or new product-scope
decisions. The work is intentionally limited to public documentation alignment,
methodology/safety posture, and local verification.

## Scope

- Align public status documents with the current Milestone 33 baseline.
- Keep the public documentation boundary explicit and free of private
  operational details.
- Preserve clinical-safety wording: the project is a data observatory, not a
  triage service or hospital-choice recommendation tool.
- Preserve the strict ontology comparability rule and research-facing
  methodology framing.
- Run feasible local verification that does not require credentials.

## Alternatives Considered

1. **Restore scheduled workflows now.** Rejected for this pass because workflow
   cadence has cost and operations impact and requires explicit release or quota
   intent.
2. **Add new provinces or resource sources.** Rejected for this pass because
   each new source needs source-stability, methodology, reuse-rights, and product
   scope review.
3. **Make runtime behavior changes.** Deferred unless verification exposes a
   concrete repo-side issue. The immediate evidence points to documentation
   drift, not a runtime defect.

## Implementation Notes

- Updated public status language to reflect the Milestone 33 stewardship phase.
- Updated README freshness wording to match the manual-dispatch posture while
  scheduled GitHub Actions runs are constrained.
- Refreshed README ADR, test, and workflow counts to match the current public
  tree and verified local test results.
- Updated documentation indexes so their latest-maintenance references point to
  existing files.
- Added a recurring manual task for public status alignment after milestones.
- Expanded `scripts/check-docs.sh` so it checks the planning index and current
  maintenance logs, including this file.
- Expanded public artifact coverage in `scripts/check-docs.sh` so file-link,
  public-boundary, and local authorship checks derive selected non-Markdown
  public artifacts from the same checked path list as Markdown docs, including
  docs HTML, OpenAPI YAML, methodology JSON, and public methodology CSV files.
- Expanded the public-boundary marker check to catch Windows/WSL local path
  leaks such as local WSL hostnames, WSL UNC paths, and Windows user-profile
  paths in public documentation artifacts.
- Expanded the public-boundary marker check to catch generic Linux and macOS
  home-directory path leaks without flagging ordinary URLs that contain
  `/home/` as a route segment.
- Added focused unit coverage for the roadmap freshness check so future
  milestone updates are validated against the latest completed milestone in the
  roadmap table instead of stale hard-coded milestone names.
- Added README/roadmap status-alignment verification so the README baseline
  dates and current-status milestone wording must track the roadmap's current
  update date and latest completed milestone.
- Tightened roadmap and README status-date validation to require exact
  `YYYY-MM-DD` matches, including trailing-text regression coverage for the
  roadmap status date.
- Restricted latest-completed-milestone detection to the Completed Milestones
  table so future-planning milestone placeholders do not make the status checks
  falsely stale.
- Added `docs/research/export-methodology-interpretation-guide.md` as a
  public research artifact explaining how to interpret CSV and JSON exports
  without weakening ontology comparability or clinical-safety boundaries.
- Added explicit clinical-safety and comparability guardrails to
  `scripts/check-docs.sh` so core public docs fail verification if they drop
  emergency, non-medical-advice, non-triage, hospital-choice, or four-field
  ontology-comparability language.
- Broadened the authorship guardrail in `scripts/check-docs.sh` from
  co-author trailers only to source/doc attribution markers such as author,
  contributor, generated-by, created-by, and written-by fields. The check is
  limited to tracked text/source files and excludes env, key, certificate, and
  private paths.
- Added a Git history authorship audit to `scripts/check-docs.sh` so available
  commit author, committer, and authorship-trailer metadata is checked for
  non-human identities.
- Included the discovered public markdown set in the authorship guardrail so
  newly created public docs are checked locally before they are staged, without
  scanning arbitrary untracked files.
- Added a docs-check guardrail requiring `CLAUDE.md` and `GEMINI.md` to remain
  relative symlinks to `AGENTS.md`, preserving the shared repo instructions
  across supported agent entrypoints.
- Updated Docs CI path filters and the workflow catalog so changes to
  `AGENTS.md`, agent-entrypoint symlinks, public top-level docs, the workflow
  README, and docs-check logic trigger the same guardrails they describe.
- Updated Docs CI checkout depth to fetch full Git history for the commit
  authorship audit while keeping the lane lightweight and non-Playwright.
- Broadened Docs CI path filters to tracked text/source extension globs so the
  lightweight authorship guardrail still runs when source files, scripts,
  workflow files, or backend/frontend code change.
- Included public CSV data-artifact files in Docs CI path filters and docs
  checks so methodology exports under `docs/assets` receive the same lightweight
  public-boundary and authorship scans.
- Added `docs/**` to the docs-checker's required Docs CI path filters so the
  broad public-docs trigger remains enforced alongside enumerated text/source
  and data-artifact extensions.
- Broadened the file-URL guardrail beyond Markdown links and HTML `href`
  attributes to catch structured values and CSV fields that start with
  `file://`, while still allowing policy prose that mentions `file://` as a
  banned form.
- Extended repository-relative markdown link validation to include
  reference-style link definitions, not only inline markdown links.
- Added fixture-level backend tests for `scripts/check-docs.sh` covering a
  passing minimal policy fixture, `AGENTS.md` ontology drift detection, and
  reference-style markdown broken-link detection.
- Added fixture-level docs-check tests for required broad `docs/**` Docs CI path
  coverage and `file://` leakage in public CSV artifacts.
- Added fixture-level docs-check tests for full-history Docs CI checkout
  configuration and forbidden commit author/trailer metadata.
- Added fixture-level docs-check tests for the agent-entrypoint symlink rule
  and scoped local-home path leakage detection.
- Added a Docs CI path-filter coverage check to `scripts/check-docs.sh` so the
  lightweight policy workflow fails if future edits remove required
  text/source globs from either the pull-request or push trigger, or remove
  manual dispatch.
- Refactored the docs checker's file-link, attribution, and public-boundary
  regular expressions into named variables so future maintenance is auditable.
- Aligned the `AGENTS.md` ontology lists with the implemented database/model
  enums, including `MEDIAN`, `MEAN`, and `HIGH_ACUITY`.
- Added a docs-check guardrail that compares the `AGENTS.md` ontology constants
  against `backend/src/waittime/core/enums.py`.
- Removed local build/test cache artifacts created during verification:
  backend pytest cache, Ruff caches, frontend `.next`, and backend
  `__pycache__` directories outside `.venv`.
- Reclassified historical Public Health Hub planning baselines out of the
  active planning-doc lists in the planning README and MkDocs planning index.
- Replaced a stale historical Public Health Hub handoff reference with links to
  the archived Batch A implementation plan and decision brief.
- Added roadmap/manual-task coverage for evaluating CI offload options because
  GitHub Actions quota is currently the limiting operational resource. The
  roadmap frames this as a decision to compare external CI, self-hosted GitHub
  runners, Forgejo Actions on the NAS, and narrower manual GitHub Actions lanes
  before choosing a migration path.
- No new ADR was added in this wrap-up because the work tightened
  documentation/process controls without changing runtime architecture,
  persistent data contracts, or product behavior.

## Verification

- `bash scripts/check-docs.sh` passed. This covered markdown link integrity,
  public-boundary marker terms, non-human authorship attribution markers, Docs
  CI trigger coverage, and roadmap consistency.
- Public status scan found no current references to the stale M14/M15 roadmap
  summary or old README status baseline.
- Clinical-safety and methodology-language scan confirmed current public docs
  still state that the project does not provide medical advice, is not a triage
  service, avoids hospital-choice recommendations, and preserves strict
  ontology comparability.
- Backend unit tests passed: `538 passed`.
- Focused Python lint passed for `backend/scripts/verify_roadmap_consistency.py`
  and `backend/tests/unit/test_verify_roadmap_consistency.py`.
- Frontend type-check passed.
- Frontend lint passed.
- Frontend unit tests passed: `76` test files and `419` tests. The checked-out
  dependency tree is Linux/WSL-oriented, so the successful run used a temporary
  Linux Node 22.13.1 runtime in `/tmp` matching `.nvmrc`; no project dependency
  files were changed.
- Documentation checks now cover the planning index, maintenance logs, case
  studies, and the export methodology guide.
- Documentation checks now also cover the public stakeholder-interview toolkit
  linked from `docs/README.md`.
- Documentation checks now also cover public top-level docs, data-source notes,
  stakeholder feedback, and public-health-hub planning contract docs that sit
  outside the main docs subdirectory indexes.
- Documentation checks now include selected public non-Markdown artifacts for
  local path, public-boundary, and authorship attribution scans.
- Documentation checks now include public CSV artifacts in those selected
  non-Markdown scans.
- Documentation checks now catch `file://` values in YAML/JSON-style fields and
  CSV columns, not only Markdown links and HTML attributes.
- Documentation checks now validate local reference-style markdown link
  definitions with the same target rules used for inline markdown links.
- Backend unit coverage now directly exercises the docs checker against a
  minimal temporary repository fixture, including failure cases for ontology
  drift, reference-style broken links, missing broad docs path filters, and CSV
  file-URL leaks.
- Backend unit coverage now also verifies that `CLAUDE.md`/`GEMINI.md` must
  remain relative symlinks to `AGENTS.md`, and that local Linux/macOS home paths
  are rejected without treating ordinary `/home/` URL routes as leaks.
- Backend unit coverage now also verifies the expanded human-authorship
  guardrail against both newly created public docs and tracked source files.
- Documentation checks now also flag Windows/WSL local path markers in public
  documentation artifacts, complementing the existing Linux path and
  private-operations markers.
- Documentation checks now also flag whitespace-prefixed Linux/macOS
  home-directory paths such as `/home/user` and `/Users/user` while allowing
  external URLs with `/home/` route segments.
- Documentation checks now also verify required clinical-safety and
  comparability wording across README, API docs, roadmap, export guidance, and
  the Ottawa-Gatineau case study.
- Documentation checks now also enforce the broader human-authorship guardrail
  across tracked public text/source files while avoiding secret-bearing path
  patterns.
- Documentation checks now include newly created public markdown files in the
  local authorship scan before they are tracked.
- Documentation checks now verify that `CLAUDE.md` and `GEMINI.md` still point
  to `AGENTS.md` as relative symlinks.
- Docs CI trigger coverage now includes the public top-level files and workflow
  catalog that `scripts/check-docs.sh` validates.
- Docs CI trigger coverage now follows the tracked text/source file types that
  the authorship guardrail can inspect, while the checker itself still excludes
  env, key, certificate, and private path patterns.
- Documentation checks now fail if Docs CI loses any required tracked
  text/source extension filter from either trigger, or loses its manual
  dispatch entry point.
- Documentation checks now also fail if Docs CI loses the broad `docs/**`
  trigger from either pull-request or push path filters.
- Roadmap consistency verification now also checks that README public status
  dates and current-status milestone wording remain aligned with
  `docs/planning/roadmap.md`.
- Roadmap consistency unit coverage now rejects malformed current-status dates
  such as `2026-06-12 extra`, not only natural-language dates.
- Roadmap consistency unit coverage now verifies that future milestone
  placeholders outside the Completed Milestones table do not affect latest
  completed milestone detection.
- Repo instruction ontology values now match `backend/src/waittime/core/enums.py`
  for metric families, start events, end events, statistic types, and patient
  scopes.
- Documentation checks now fail if those `AGENTS.md` ontology constants drift
  from the implemented backend enum classes.
- Commit metadata audit found only Jeremy Dawson and permitted bot identities
  (`dependabot[bot]` and GitHub-generated committer metadata) in existing
  history; no AI-agent author or committer identities were found.
- Existing commit-message co-author trailers found during the audit list only
  Jeremy Dawson or `dependabot[bot]`.
- Local Playwright tests were not run, matching the testing guidelines and
  GitHub Actions free-tier conservation posture.

## Non-Autonomous Follow-Ups

- Re-enable scheduled operational workflows only after explicit release/quota
  intent.
- Choose a CI/offload path only after documenting security, secrets, logging,
  cost, reliability, and rollback tradeoffs.
- Add public-health resource sources only after official-source and reuse-rights
  review.
- Add new provinces only after source stability and methodology review.
- Add privacy analytics only after explicit privacy-policy approval.
