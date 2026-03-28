# Public Health Data Hub Identity Memo

**Created:** 2026-03-27
**Status:** Archived after Batch A delivery
**Related:** `docs/planning/archive/public-health-data-hub-decision-brief.md`

---

## Decision

**Recommendation:** keep the public-health-data-hub track inside Wait Time Canada as a module for Batch A.

Do **not** spin this into a separate product or separate branding surface now.

---

## Options Compared

| Option | Narrative coherence | Maintainability | User comprehension | Brand dilution risk | Employer signal | Current recommendation |
|---|---|---|---|---|---|---|
| Module inside Wait Time Canada | High | High | High | Low | High | **Choose now** |
| Broader information architecture inside Wait Time Canada | Medium | Medium | Medium | Medium | High | Revisit after Batch B |
| Separate broader product surface | Low now | Low now | Low now | High | High | Do not choose now |

---

## Why The Module Approach Wins Now

### 1. Narrative fit

The new domains under consideration are strongest when framed as extensions of the current observatory identity:

- emergency access
- public safety alerts
- environmental health context
- public health infrastructure visibility

That is still recognizably Wait Time Canada. A broader standalone product would blur the project before the first adjacent batch is even proven.

### 2. Reduced brand dilution

The repo already has a strong thesis: methodology-aware public health observability.

Keeping the hub work as a module preserves that thesis while allowing adjacent public-utility features to emerge. Spinning out too early would make the project sound broader than the validated data foundation justifies.

### 3. Better planning discipline

The modular choice forces the team to earn broader scope by shipping coherent additions one batch at a time.

It also makes it easier to stop the expansion if validation or maintenance burden turns out weaker than expected.

### 4. Employer signal is still strong

Future employers do not need a separate brand to understand the signal here.

A well-scoped module inside an already mature health-data platform still demonstrates:

- source validation discipline
- connector architecture thinking
- public-data product strategy
- health-tech and civic-tech judgment

---

## When To Revisit This Decision

Revisit product identity only if one or more of the following becomes true:

1. Batch A ships and a second batch is also clearly justified.
2. The number of non-wait-time public health modules begins to exceed the original wait-time observatory surface.
3. The navigation, IA, or homepage positioning becomes confusing if everything remains under the current framing.
4. A partnership or audience signal emerges that clearly favors a broader product identity.

Until then, the default should remain:

**Wait Time Canada with a carefully scoped public-health-data-hub module.**

---

## Immediate Implication For Planning

The next milestone plan should assume:

- no separate product name
- no new repo split
- no rebrand ADR yet
- no homepage rewrite around “all public health data”

Instead, the next milestone plan should describe Batch A as a module or feature area within Wait Time Canada.
