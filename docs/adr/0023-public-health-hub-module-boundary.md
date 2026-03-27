# 0023. Public Health Hub Module Boundary

Date: 2026-03-27

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: Public health data hub planning package

## Context and Problem Statement

Wait Time Canada now has a validated planning package for an Ontario-first public-health-data-hub expansion path. The project needs a formal decision on whether Batch A should live inside the existing product as a module or trigger a broader information architecture or separate product direction.

## Decision Drivers

* Preserve the current observatory identity and methodological credibility
* Avoid premature product sprawl and brand dilution
* Keep implementation scope coherent for Batch A
* Maintain strong portfolio and employer signal without overclaiming breadth

## Considered Options

* Keep the public-health-hub work as a module inside Wait Time Canada
* Expand Wait Time Canada into a broader information architecture immediately
* Create a separate broader public-health product surface now

## Decision Outcome

Chosen option: "Keep the public-health-hub work as a module inside Wait Time Canada", because it best preserves narrative coherence, keeps scope manageable for Batch A, and avoids overextending the product before adjacent domains are proven.

### Positive Consequences

* Batch A can be planned as an extension of the current product rather than a rebrand
* Existing trust signals, routes, and documentation posture remain relevant
* The team can stop or redirect the expansion later without product-fragmentation cost

### Negative Consequences

* The broader public-health vision remains partially constrained by the current product framing
* A larger IA revision may still be needed later if multiple batches succeed

## Pros and Cons of the Options

### Keep as a module inside Wait Time Canada

* Good, because it aligns with the current public-interest observatory thesis
* Good, because it minimizes brand dilution and planning overhead
* Bad, because it may eventually constrain broader navigation or positioning

### Broaden the current product IA immediately

* Good, because it creates more room for future non-wait-time modules
* Good, because it may reduce future restructuring if the hub expands quickly
* Bad, because it asks the product to look broader before the new domains are proven

### Create a separate broader product now

* Good, because it offers maximal branding flexibility
* Good, because it could eventually support a more generic public-health utility platform
* Bad, because it weakens current narrative coherence and introduces unnecessary product sprawl now

## Links

* [Related to] [ADR-0017](0017-domain-rebrand-wait-time-ca.md)

## Additional Information

Revisit this ADR only if Batch A ships successfully and at least one additional adjacent batch is justified, or if the number of non-wait-time modules materially exceeds the original observatory surface.
