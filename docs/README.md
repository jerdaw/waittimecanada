# Documentation Index

This directory is the documentation control plane for Wait Time Canada.

## Start Here

- Project overview and local setup: `README.md` (repo root)
- Active roadmap and milestone status: `docs/planning/roadmap.md`
- Human-intervention queue: `docs/planning/manual-tasks.md`

## Core References

- API contracts: `docs/API.md`
- Architecture overview: `docs/architecture/index.md`
- ADRs: `docs/adr/`
- Public operations quick start: `docs/operations/QUICK_START.md`
- Public source-freshness model: `docs/operations/scraper-scheduling.md`
- Latest maintenance log: `docs/planning/archive/maintenance-2026-04-23.md`
- Development setup: `docs/development/setup.md`
- Testing standards: `docs/development/testing-guidelines.md`
- Documentation standards: `docs/development/documentation-guidelines.md`

## Planning and Execution

- Planning hub: `docs/planning/README.md`
- Roadmap lifecycle process: `docs/planning/roadmap-process.md`
- Active milestone plans: `docs/planning/implementation/`
- Archived plans: `docs/planning/archive/`

## Historical Snapshots

- `docs/REPO_STRUCTURE_PLAN.md`
- `docs/REPO_STRUCTURE_PLAN.md`

These files are retained for historical context and may include superseded details.

## Public Research and Stakeholder Materials

- Screenshot guide: `docs/screenshot-guide.md`
- Stakeholder toolkit: `docs/stakeholder-interviews/`

## Public Documentation Boundary

This repository contains public project documentation and reproducible development information. Deployment details, credentials, monitoring configuration, private operational notes, and environment-specific production paths are intentionally excluded from public documentation.

## Maintenance Rules

- Treat docs as code: update docs in same PR as behavior changes.
- Run `bash scripts/check-docs.sh` before opening docs-heavy PRs.
- Keep roadmap current every working session.
- Archive milestone plans only when delivered/closed per process.
- Clearly label historical documents and avoid using them as source-of-truth.
- Keep author/contributor attribution human-only.
