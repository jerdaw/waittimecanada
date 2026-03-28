# Public Health Hub Municipal Inspection Pilot Decision

**Created:** 2026-03-28
**Status:** Active decision memo
**Scope:** Whether Wait Time Canada should pursue a Toronto-first municipal inspection/compliance pilot as the next public-health-hub expansion step
**Related:** `docs/research/public-health-data-hub-batch-b-source-review.md`, `docs/planning/roadmap.md`, `docs/planning/post-launch-growth-strategy.md`

---

## Summary

Current recommendation: **do not pursue a Toronto-only inspection/compliance pilot now.**

Toronto's inspection datasets are technically stronger than the early planning pass assumed. DineSafe and BodySafe are machine-readable, current, and available through the city's open-data stack. The blocker is not raw access. The blocker is **product fit**.

Wait Time Canada's public-health-hub module is currently strongest when it stays:

- Ontario-first
- location-aware
- operationally useful in the moment
- coherent as an emergency-access and safety-adjacent utility surface

A Toronto-only inspection pilot would add more fragmentation than leverage at this stage.

---

## What Was Considered

### Option 1: Start a Toronto-only inspection pilot now

Examples:

- DineSafe
- BodySafe
- later possible SwimSafe or adjacent municipal inspection feeds

### Option 2: Defer the pilot and keep inspections out of the near-term hub

This means:

- no implementation work now
- keep the research findings
- only reopen if the scope becomes less fragmented or the product strategy changes

---

## Decision

Choose **Option 2: defer the municipal inspection pilot for now**.

This is the better decision because the current project does not need a Toronto-only sidecar badly enough to justify:

- a scope break inside an Ontario-first module
- new municipal-specific connectors and support burden
- a less coherent public story for `/resources`

The inspection data is real and potentially useful. It is just not the right next expansion step.

---

## Why This Is The Right Call

### 1. The scope is too fragmented

The strongest inspection datasets validated so far are municipal, not Ontario-wide.

That creates an awkward product shape:

- strong Toronto coverage
- no equivalent Ontario-wide inspection surface
- likely pressure to add city-by-city exceptions

That is exactly the kind of fragmentation the hub planning process was designed to avoid.

### 2. User value is real, but less immediate than other candidates

Inspection results are useful, but they are not as tightly aligned to the current `/resources` thesis as:

- facility search
- AED lookup
- official safety alerts
- AQHI
- official naloxone link-outs

Those existing slices are more obviously “what can I use right now?” utilities.

### 3. The narrative gets messier

The current public-health-hub module still reads clearly:

- emergency-access adjacent
- safety-aware
- provenance-first
- Ontario-first

A Toronto-only inspection pilot would push the module closer to a generic civic-health directory before the broader Ontario story is ready.

### 4. The operations burden is not trivial

A municipal inspection pilot would likely need:

- Toronto-specific ingestion and normalization
- Toronto-specific caveats and public wording
- future judgment calls about whether to add Ottawa, Hamilton, Niagara, and others

That means more connector sprawl without a correspondingly strong product payoff.

---

## What This Decision Does Not Mean

This is **not** a claim that inspection data is weak or unusable.

It means:

- the data is good enough to keep on the strategic map
- the data is not the best next move for this product right now

Toronto inspection data remains a credible future candidate if one of these changes:

1. a second or third Ontario jurisdiction is validated strongly enough to support a broader inspection strategy
2. the product intentionally chooses a Toronto-first civic-health sidecar
3. the public-health hub expands beyond emergency-access-adjacent use cases in a deliberate later phase

---

## Recommended Roadmap Posture

1. Mark the municipal inspection pilot decision as complete
2. Remove it from the near-term open decision queue
3. Reopen inspection work only if broader Ontario inspection coverage or a stronger strategic reason emerges

---

## Practical Outcome

Near-term public-health-hub work should continue to favor:

- stability and polish for `/resources`
- official link-outs where reuse is sensitive
- Ontario-wide sources over municipal fragments
- additions that improve the existing emergency/safety/access thesis rather than broadening the module for its own sake

---

## Re-evaluation Trigger

Revisit this decision only if at least one of the following becomes true:

- another Ontario municipal or regional inspection dataset is validated at the same quality level as Toronto
- a broader Ontario inspection connector strategy is drafted
- the product direction explicitly broadens beyond the current emergency-access-adjacent framing
