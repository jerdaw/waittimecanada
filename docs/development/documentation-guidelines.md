# Documentation Guidelines

Documentation is treated as production code in this repository.

## Standards

- Accurate: reflects current runtime behavior, schema, and workflows.
- Actionable: command snippets run as written.
- Traceable: major decisions link to ADRs and roadmap entries.
- Maintained: stale plans are archived; active plans stay current.

## Update Triggers

Update docs in the same PR when changing:

- API routes, parameters, response contracts, or error behavior
- database schema, migrations, or bootstrap workflows
- setup steps, scripts, environment variables, or CI workflows
- roadmap/milestone status

## Link and Path Rules

- Use repository-relative links (for example, `docs/planning/roadmap.md`).
- Never use absolute local paths or `file://` links.
- Prefer stable links to source-of-truth docs over duplicate explanations.
- Keep private project and operations notes in the private/shared operations
  source of truth. Ignored local `private/` folders may exist as convenience
  copies only and are not durable documentation.
- Do not commit actual secrets; credentials, API keys, webhook secrets,
  database URLs with credentials, and private keys stay in Bitwarden or
  deployment environments.

## Active vs Historical Docs

- Active docs should describe current behavior.
- Historical plans should be clearly marked as archived/historical and removed from active task lists.
- The roadmap (`docs/planning/roadmap.md`) remains the primary status entry point.
- Documentation automation (`scripts/check-docs.sh`) validates active docs and intentionally excludes designated historical snapshots.

## Required Updates for Major Features

1. Update roadmap status: `docs/planning/roadmap.md`
2. Update related implementation plan: `docs/planning/implementation/*`
3. Add/update ADR when architecture or contracts changed: `docs/adr/*`
4. Update public docs for externally visible behavior: `README.md`, `docs/API.md`, `docs/architecture/*`

## Documentation Quality Check

Run before opening a PR:

```bash
bash scripts/check-docs.sh
```

This check enforces high-signal documentation hygiene rules used by CI.

The docs platform remains on MkDocs 1.x in the current wave. Do not swap this repo to Zensical or replace the `mkdocs gh-deploy` publishing path until the shared Wave 3 migration gate is explicitly opened in `docs/planning/roadmap.md`.

## Attribution Policy

Only human contributors may be listed as authors/co-authors in documentation and commits.
