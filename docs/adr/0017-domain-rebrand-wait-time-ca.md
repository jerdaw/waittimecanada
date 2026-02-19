# 0017. Domain Rebrand to `wait-time.ca`

Date: 2026-02-19

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: `docs/planning/roadmap.md` (deployment posture) + rebrand implementation sweep

## Context and Problem Statement

The project needs to align public-facing branding and canonical URLs with the new domain `wait-time.ca` while preserving existing repository identifiers and legacy inbound links. At the same time, public hosting is intermittently unavailable due to cost-control posture (Netlify project paused).

## Decision Drivers

* Canonical domain clarity for SEO, citations, and exports
* Preserve continuity for existing links (legacy domains, GitHub repo slug)
* Minimal operational risk (safe redirects, explicit deployment posture)
* Cost control (public hosting can be intentionally offline)

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
* While public hosting is paused, the canonical domain cutover remains staged and must be treated as on hold

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
- Documentation/roadmap explicitly marking the Netlify paused posture and the March 9, 2026 target to re-enable public hosting
