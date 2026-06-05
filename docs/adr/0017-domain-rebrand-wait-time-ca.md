# 0017. Domain Rebrand to `wait-time.ca`

Date: 2026-02-19

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` (deployment posture) + rebrand implementation sweep

## Context and Problem Statement

The project needs to align public-facing branding and canonical URLs with the
domain `wait-time.ca` while preserving existing repository identifiers and
legacy inbound links.

## Decision Drivers

* Canonical domain clarity for SEO, citations, and exports
* Preserve continuity for existing links (legacy domains, GitHub repo slug)
* Minimal operational risk (safe redirects, explicit deployment posture)
* Cost control for non-essential deployment activity

## Considered Options

* Keep the existing domain as canonical
* Rebrand product name to match the domain exactly everywhere
* Keep the product name human-readable, and treat `wait-time.ca` as the canonical domain

## Decision Outcome

Chosen option: "Keep the product name human-readable (Wait Time Canada), and treat `wait-time.ca` as the canonical domain", because it preserves a clear product identity while allowing a clean, stable canonical URL for SEO and citations.

### Positive Consequences

* User-facing copy remains readable and consistent ("Wait Time Canada")
* Canonical URL is consistent across metadata, sitemap/robots, and data exports
* Legacy domains can permanently redirect without breaking old links

### Negative Consequences

* Requires coordinated external configuration (DNS, hosting, secrets)
* Canonical domain changes require deployment coordination outside this ADR

## Pros and Cons of the Options

### Keep the existing domain as canonical

* Good, because it avoids operational changes
* Bad, because it does not match the new domain strategy and complicates future branding

### Rebrand product name to match the domain everywhere

* Good, because it tightly couples the product to the domain
* Bad, because it weakens a clear human-readable product name and forces unnecessary copy churn

### Keep the product name human-readable, and treat `wait-time.ca` as canonical

* Good, because it preserves brand readability while standardizing canonical URLs
* Good, because internal identifiers (repo slug, package/module names) remain stable
* Bad, because it requires explicit redirect + environment configuration

## Additional Information

Implementation includes:

- Canonical base URL support via `NEXT_PUBLIC_BASE_URL` for metadata/sitemap/robots
- Legacy host redirects at the edge (Next.js middleware) when hosting is active
- Documentation and roadmap updates that treat deployment coordination as
  environment-specific maintainer work
