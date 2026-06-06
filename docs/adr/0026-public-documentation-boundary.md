# 0026. Public Documentation Boundary

Date: 2026-06-04

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: Public repository cleanup and long-term documentation hygiene

## Context and Problem Statement

Wait Time Canada is public, but some historical notes mixed public project
documentation with private/shared operations material, personal planning
material, and environment-specific runbooks. That made the public documentation
harder to maintain and increased the chance that future contributors would
accidentally publish sensitive operational context or stale non-product
planning notes.

The repository needs a durable boundary between public, reproducible project
documentation and private/shared operations material.

## Decision Drivers

* Keep public documentation focused on app behavior, methodology, limitations,
  public sources, and local development
* Keep credentials, private runbooks, deployment paths, alerting setup, and
  personal planning material out of tracked public docs
* Preserve historical/private material in the private/shared operations source
  of truth without committing it to this public repo
* Keep emergency disclaimers, source attribution, and methodology caveats
  visible and current
* Ensure only human contributors are listed as authors or co-authors

## Considered Options

* Leave historical and operational notes in public docs with warning banners
* Delete private or stale material outright
* Move private or stale material to a durable private/shared operations source,
  with ignored local `private/` folders allowed only as convenience copies, and
  keep the public docs focused on reproducible project information

## Decision Outcome

Chosen option: move private or stale material to the private/shared operations
source of truth, keep ignored local `private/` folders only as optional
convenience copies, and keep the public docs focused on reproducible project
information. This preserves maintainer context while reducing the public
repository's operational exposure and maintenance burden.

### Positive Consequences

* Public docs have a clear scope: methodology, public behavior, local
  development, data limitations, and contributor guidance
* Private runbooks, exact environment paths, and alerting configuration are not
  published as active project documentation
* Historical notes remain available through the private/shared operations
  source of truth
* The roadmap remains the single public status entry point
* Human-only authorship policy is explicit in shared agent guidance

### Negative Consequences

* Some historical implementation notes are no longer browsable in public docs
* Maintainer-only recovery details require access to the private/shared
  operations source of truth
* Future documentation changes must check whether material belongs in public
  docs or private/shared operations material

## Public Documentation Rules

Public docs may include:

* Current app behavior and API contracts
* Methodology and data-quality explanations
* Emergency and non-triage disclaimers
* Public source attribution and source caveats
* Reproducible local development instructions with placeholder credentials

Public docs must not include:

* Secrets, tokens, passwords, or private keys
* Exact private deployment paths, host access details, or private network notes
* Alerting provider credentials or private notification-routing details
* Personal planning material or application-oriented positioning
* Non-human author, co-author, or contributor attribution

## Links

* `docs/development/documentation-guidelines.md`
* `docs/planning/roadmap.md`
* `docs/planning/manual-tasks.md`
* `AGENTS.md`
