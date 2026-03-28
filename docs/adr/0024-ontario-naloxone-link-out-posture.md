# 0024. Ontario Naloxone Link-Out Posture

Date: 2026-03-28

Status: Accepted

Deciders: Jeremy Dawson

Technical Story: Public Health Hub Batch B source review and naloxone reuse decision

## Context and Problem Statement

Wait Time Canada's public-health-hub Batch B review confirmed that Ontario's naloxone kit locator is technically accessible through a public ArcGIS-backed map and queryable feature layer. The unresolved issue is not technical access, but whether ingesting and republishing that data inside Wait Time Canada would exceed the reuse rights that are clearly granted on Ontario.ca.

The immediate question is: **how should Wait Time Canada handle the Ontario naloxone source before explicit reuse clarity is established?**

## Decision Drivers

* Avoid reusing Crown content beyond clearly permitted rights
* Preserve the project's methodology-first and provenance-first credibility
* Prefer low-risk public utility over legally ambiguous ingestion
* Keep future options open if explicit reuse clearance is later obtained
* Maintain clear communication to users about what is official and what is not

## Considered Options

* Link out to the official Ontario naloxone page only
* Embed or frame the official Ontario map without native ingestion
* Ingest and republish the Ontario naloxone dataset under a non-commercial, no-alteration interpretation
* Seek explicit permission or rights clarification before any native ingestion or proxying

## Decision Outcome

Chosen option: "Link out to the official Ontario naloxone page only until explicit reuse clarity is established", because it provides public value without asking the product to rely on an uncertain interpretation of Crown-content reuse rights.

In practice, this means:

* Wait Time Canada may reference the Ontario naloxone resource and send users to the official Ontario source.
* Wait Time Canada should not ingest, normalize, store, proxy, or republish the Ontario naloxone dataset as a first-party product layer at this time.
* A future re-evaluation is allowed if the source is later published under clearly reusable terms or explicit permission is obtained.

### Positive Consequences

* The project avoids overreaching on reuse rights for a sensitive public-health source
* Users can still reach the official Ontario naloxone locator immediately
* The team preserves a clean decision trail for future re-evaluation
* The public-health-hub expansion stays aligned with the repo's safety-first and provenance-first posture

### Negative Consequences

* Wait Time Canada does not gain a native naloxone map/search experience yet
* The `/resources` module remains less comprehensive than it could be
* Some future product work is deferred until rights are clearer

## Pros and Cons of the Options

### Link out to the official Ontario naloxone page only

* Good, because it is the lowest-risk option from a reuse-rights perspective
* Good, because it still provides immediate user value through the official source
* Bad, because it does not create a native Wait Time Canada experience

### Embed or frame the official Ontario map without native ingestion

* Good, because it may preserve more of the official presentation and reduce data-handling risk
* Good, because it could create a more integrated user experience than a plain link
* Bad, because it still depends on technical and legal assumptions that were not resolved in this review

### Ingest and republish the Ontario naloxone dataset under a non-commercial, no-alteration interpretation

* Good, because it would produce the strongest product experience
* Good, because the underlying technical connector path is real and queryable
* Bad, because the product behavior would likely go beyond simple unchanged reproduction and create unnecessary legal ambiguity

### Seek explicit permission or rights clarification before any native ingestion or proxying

* Good, because it is the cleanest path to a later native implementation
* Good, because it would let the product move forward with clearer operational confidence
* Bad, because it depends on external response time and may not produce a usable answer quickly

## Links

* [Related to] [ADR-0023](0023-public-health-hub-module-boundary.md)

## Additional Information

This ADR does not block future naloxone work permanently. It establishes a conservative interim posture:

1. link to the official Ontario source now
2. document the reason clearly in planning and methods materials
3. re-evaluate later only if reuse rights become clearer

This decision is intentionally narrower than a general policy on Ontario public data. It applies specifically to the current Ontario naloxone source posture, where technical access is stronger than explicit reuse permission.
