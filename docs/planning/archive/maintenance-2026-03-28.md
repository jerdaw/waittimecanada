# Maintenance Log — 2026-03-28

## Scope

Post-D1/D13 maintenance sweep covering roadmap state, docs deploy authorship,
planning index hygiene, CI verification, and GitHub branch/PR cleanup.

## Completed

- Confirmed the latest two engineering follow-ups are delivered and reflected in
  the roadmap:
  - `D1` comparability matrix upgrade
  - `D13` mixed-cadence historical quality annotation
- Updated the roadmap summary and next-action wording so active work is not
  overstated now that the low-risk D-phase cleanup items are complete.
- Confirmed there are no open pull requests.
- Confirmed the only remote branches are `main` and `gh-pages`.
- Confirmed the latest pushed commit (`5ad43fa`) is green in:
  - `Docs CI`
  - `Frontend CI`
  - `Lighthouse CI`
  - `Deploy Docs`
- Confirmed no local junk artifacts were present (`.DS_Store`, `*.tmp`,
  `*.bak`, `*.orig`, `*.rej`, `Thumbs.db`).
- Confirmed `CLAUDE.md` and `GEMINI.md` remain relative symlinks to
  `AGENTS.md`.
- Confirmed active source-branch history (`main`) remains human-authored only.

## Authorship Remediation

- Updated `.github/workflows/deploy-docs.yml` so future docs-publish commits use
  the human repository author identity instead of `github-actions[bot]`.
- Rebuilt the reachable `gh-pages` branch history under the human author
  identity so active branch history now matches the repository's
  human-authorship policy.

## Planning State

- `docs/planning/implementation/admissions-strengthening-plan.md` remains
  active because it still contains intentionally parked and conditional items.
  It should not be archived yet.
- The current roadmap now reflects that there is no immediate low-risk
  engineering cleanup item left; the remaining engineering entries are larger
  optional expansions.

## Verification

- `bash scripts/check-docs.sh`
- `git diff --check`
- `git log origin/main --format='%an <%ae>' | sort -u`
- `gh pr list`
- `gh run list --limit 10`
