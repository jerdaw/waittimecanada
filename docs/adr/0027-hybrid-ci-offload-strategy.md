# 0027. Hybrid CI Offload Strategy

Date: 2026-06-13

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: GitHub Actions quota and operational workflow cost control

## Context and Problem Statement

Wait Time Canada uses GitHub as the public collaboration surface, but the
project's scheduled and operational automation can create substantial GitHub
Actions usage. Scheduled workflows are currently paused or manual-dispatch only
to conserve free-tier capacity, which protects cost but weakens routine source
freshness and operations cadence.

How should the project reduce GitHub Actions pressure without weakening public
PR quality gates, source-health monitoring, secret handling, or clinical-safety
guardrails?

## Decision Drivers

* Preserve GitHub as the public repository and pull-request review surface
* Keep fast, reproducible PR checks available for code and documentation changes
* Reduce reliance on GitHub-hosted runners for heavy recurring operational jobs
* Never run untrusted pull-request code on a private/NAS runner
* Keep production secrets isolated from public logs and untrusted workflow input
* Keep manual GitHub dispatch as a rollback path while offloaded jobs mature
* Preserve source-health observability, failure summaries, and alert state

## Current Workflow Inventory

This inventory was generated from the tracked workflow YAML and recent
`gh run list --limit 100` output on 2026-06-13. The minute totals are approximate
wall-clock run durations from recent history, not a billing invoice.

| Workflow class | Workflows | Current trigger posture | Recent observed pressure |
|----------------|-----------|-------------------------|--------------------------|
| PR/push docs and backend checks | `docs-ci.yml`, `scraper-ci.yml` | `pull_request` / `push` | Low: docs CI under 1 minute across 6 recent push runs; scraper CI about 2 minutes across 2 recent push runs |
| Frontend quality gates | `frontend-ci.yml` | `pull_request` / `push` / manual | Moderate per run; path-gated and not the dominant recent source |
| Docs publishing | `deploy-docs.yml`, GitHub Pages deployment | `push` / manual or dynamic | Low to moderate; tied to public documentation releases |
| Heavy scheduled operations | `scraper-cron.yml`, `heartbeat-monitor.yml`, `public-health-hub-cron.yml`, `snapshot-cron.yml`, `production-smoke.yml` | currently manual dispatch in YAML, historically scheduled | Dominant recent pressure: scraper cron about 255 minutes across 26 recent scheduled runs; heartbeat about 18 minutes across 32 runs |
| Privileged manual operations | `database-cleanup.yml`, `database-migrate.yml`, `production-readiness.yml`, `release.yml` | manual or protected push | Lower frequency, high blast radius because secrets or release authority are involved |
| Optional presentation/performance artifacts | `demo-screenshots.yml`, `lighthouse.yml` | manual or push | Keep manual/path-gated unless explicitly needed |

## Considered Options

* Keep all workflows on GitHub Actions with stricter manual dispatch and path
  filters
* Move selected jobs to self-hosted GitHub runners
* Mirror or migrate operational jobs to Forgejo Actions on the NAS
* Move CI to a third-party external CI service while keeping GitHub as the repo
* Adopt a hybrid model: keep public PR/push gates on GitHub, offload trusted
  recurring operational jobs to a private runner/orchestrator, and keep GitHub
  manual dispatch as fallback

## Decision Outcome

Chosen option: hybrid model.

Keep public PR/push quality gates on GitHub Actions, because those checks are
low-cost, familiar to contributors, and tied directly to GitHub pull-request
review. Offload recurring trusted operational jobs incrementally to a private
runner/orchestrator, with Forgejo Actions on the NAS or a self-hosted GitHub
runner as implementation candidates. Do not move untrusted pull-request
execution onto the NAS.

### Positive Consequences

* Reduces the dominant source of observed run time without disrupting public
  review workflows
* Preserves GitHub as the public collaboration and PR status surface
* Keeps a GitHub manual-dispatch rollback path while offloaded jobs mature
* Separates trusted operational automation from untrusted PR code execution
* Allows each secret-bearing workflow to be migrated only after its logging,
  retry, and rollback behavior is understood

### Negative Consequences

* Introduces a second automation surface to operate and monitor
* Requires runner hardening, log-retention decisions, and private runbooks
* Offloaded jobs will not automatically produce native GitHub check runs unless
  additional reporting is added
* NAS or self-hosted runner outages become an operations dependency
* A partial migration means some workflows remain on GitHub Actions for the
  foreseeable future

## Implementation Policy

### Keep On GitHub Actions

Keep these on GitHub-hosted runners unless a future ADR supersedes this one:

* `docs-ci.yml`
* `scraper-ci.yml`
* `frontend-ci.yml` PR/push gates
* `deploy-docs.yml` and GitHub Pages deployment
* `release.yml`
* `database-migrate.yml` until migration authority and rollback are explicitly
  documented

Rationale: these workflows either provide public PR feedback, publish public
documentation, or carry release/migration authority that should not be moved
without a narrower security review.

### Offload Candidates

Migrate in this order:

1. Heartbeat/status check as a low-risk proof of runner scheduling, logging, and
   alert-state behavior.
2. Scraper cron, because it is the dominant observed source of historical
   runtime pressure.
3. Quality snapshot and public-health ingest once database secret handling and
   summary reporting are proven.
4. Production smoke checks after public-route probing and notification behavior
   are documented.

Keep `workflow_dispatch` versions in GitHub as fallback entry points until the
offloaded replacement has run reliably through at least one normal operating
cycle.

### Runner Safety Rules

* Private/NAS runners must only execute trusted branch, tag, or manually
  approved operational jobs.
* Pull-request jobs from forks or untrusted branches must stay on GitHub-hosted
  runners.
* Secret-bearing jobs must redact connection strings, tokens, webhook URLs, and
  private host details from logs.
* Offloaded workflows must write concise public-safe status summaries back to
  the repo only when the output contains no private paths, hostnames, or secrets.
* Prefer isolated containers or disposable VMs for jobs that execute repository
  code. Avoid direct host execution for code-running jobs.
* Keep a rollback path: each offloaded job should have a documented GitHub
  manual-dispatch equivalent until the replacement is proven.

## Pros and Cons of the Options

### Keep Everything On GitHub With Stricter Gates

* Good, because it has the least operational complexity
* Good, because PR status reporting remains native
* Bad, because it does not solve recurring runner pressure if schedules are
  restored
* Bad, because manual-only operations leave freshness dependent on human action

### Self-Hosted GitHub Runners

* Good, because existing GitHub Actions workflow syntax and status reporting can
  mostly remain intact
* Good, because GitHub can remain the single visible automation surface
* Bad, because a private runner must be isolated from untrusted PR code
* Bad, because runner registration, updates, log handling, and outage recovery
  become maintainer responsibilities

### Forgejo Actions On The NAS

* Good, because it can move scheduled operational workloads away from
  GitHub-hosted runners and align with existing self-hosted infrastructure
* Good, because it gives the project an independent automation control plane for
  trusted operations
* Bad, because workflow compatibility and status reporting back to GitHub need
  explicit implementation
* Bad, because unsafe runner modes can execute directly on the host without
  isolation and must be avoided for code-running jobs

### Third-Party External CI

* Good, because it can offload compute without operating a home runner
* Good, because some providers offer native GitHub PR integration
* Bad, because it adds another vendor, credential store, and billing surface
* Bad, because production-adjacent secrets and health-adjacent operations need
  another security review

### Hybrid Model

* Good, because it targets the workflows that created the most observed
  historical runtime first
* Good, because it keeps public PR quality gates simple and visible
* Good, because it lets operational jobs migrate incrementally with fallback
* Bad, because it leaves the project with more than one automation surface
* Bad, because it requires discipline to prevent private runner scope creep

## Links

* [GitHub Actions billing and usage](https://docs.github.com/en/actions/concepts/billing-and-usage)
* [GitHub Actions billing details](https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions)
* [Forgejo Actions administrator guide](https://forgejo.org/docs/latest/admin/actions/)
* [Forgejo runner configuration](https://forgejo.org/docs/latest/admin/actions/configuration/)
* [ADR-0026: Public Documentation Boundary](0026-public-documentation-boundary.md)
* [Roadmap](../planning/roadmap.md)
* [Manual tasks](../planning/manual-tasks.md)

## Additional Information

The repository is public on GitHub as of this decision. GitHub's current public
documentation says standard GitHub-hosted runner usage for public repositories
and self-hosted runner usage are free, while GitHub-hosted runner billing and
storage depend on account/repository context. This ADR still treats Actions
usage as an operational bottleneck because the project has experienced free-tier
pressure and because heavy scheduled jobs create avoidable queueing, noise, and
operational coupling even when direct billing is not the only concern.
