# Public Health Data Hub Scoring Matrix

**Created:** 2026-03-27
**Status:** Planning artifact
**Related:** `docs/research/public-health-data-hub-source-shortlist.md`

---

## Scoring Method

All candidate domains are scored on a 100-point weighted rubric:

| Dimension | Weight |
|---|---:|
| User value | 15 |
| Legal clarity | 15 |
| Machine readability | 15 |
| Freshness | 10 |
| Maintenance burden | 10 |
| Safety risk | 10 |
| Narrative fit with Wait Time Canada | 10 |
| Geographic coverage | 5 |
| Differentiation | 5 |
| Employer signal | 5 |

### Scoring Rules

- Higher is better in all categories.
- `Maintenance burden` and `Safety risk` are scored as **favorable conditions**, not raw burden/risk.
- Domain scores are based on the strongest validated source set currently available for that domain.
- Domains that fail hard gates are not eligible for Batch A even if their value is conceptually high.

### Hard Gates

A domain is blocked from Batch A if:

1. there is no primary-source-validated access path
2. there is no acceptable reuse posture
3. all validated sources fall into `research_only` or `do_not_use`
4. the intended consumer use is freshness-sensitive but only brittle view-only access exists

### Score Bands

- `80+`: Batch A candidate
- `65-79`: Batch B candidate
- `50-64`: conditional / park unless strategically necessary
- `<50`: defer

---

## Domain Scores

| Domain | User | Legal | Machine | Freshness | Maintainability | Safety | Fit | Coverage | Differentiation | Employer | Total | Gate result | Recommendation |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Provider / facility baseline | 14 | 14 | 13 | 7 | 8 | 9 | 10 | 5 | 4 | 4 | **88** | Pass | Batch A |
| AED strategy | 15 | 9 | 9 | 7 | 6 | 6 | 10 | 4 | 5 | 5 | **76** | Pass with dual-track constraint | Batch A, but strategy-first |
| Recalls / safety alerts / product reference | 14 | 14 | 14 | 9 | 9 | 8 | 9 | 5 | 4 | 5 | **91** | Pass | Batch A |
| Environmental overlay | 12 | 13 | 14 | 9 | 8 | 8 | 8 | 5 | 3 | 4 | **84** | Pass | Batch A |
| EMS / system context | 9 | 13 | 12 | 5 | 8 | 9 | 8 | 5 | 3 | 4 | **76** | Pass | Batch B |
| Naloxone access | 13 | 8 | 5 | 6 | 5 | 5 | 9 | 5 | 4 | 4 | **64** | Conditional | Batch B / park until reuse path improves |

---

## Source Notes Behind The Scores

### Provider / facility baseline

- **Why high:** MOHSERLO and ODHF together provide a strong Ontario-first and Canada-wide baseline with clear official provenance and low operational risk.
- **Main limitation:** update cadence is not real-time and likely supports directory/navigation use, not dynamic operational status.

### AED strategy

- **Why not higher:** public value is extremely high, but the strongest Ontario registry path is not yet validated for direct reuse.
- **What makes it viable:** OSM provides an open fallback, which is enough to keep the domain alive if clearly labeled and scoped carefully.
- **Constraint:** Batch A should treat AED as a source strategy plus fallback data plan, not as a finished “official Ontario AED map” promise.

### Recalls / safety alerts / product reference

- **Why highest:** federal sources are unusually strong here: daily feeds, RSS, and a structured API.
- **Main limitation:** product-reference enrichment is easy; shortage data is weaker than recall data and should not define the domain strategy.

### Environmental overlay

- **Why high:** AQHI is current, official, machine-readable, and easy to interpret.
- **Main limitation:** some other environmental overlays are narrower or more fragmented; AQHI should be the first one, not an all-at-once package.

### EMS / system context

- **Why deferred:** the reporting is useful and official, but it is better as a later context layer than as a first public-utility launch feature.
- **Main limitation:** annual or slower reporting cadence limits immediate consumer value.

### Naloxone access

- **Why conditional:** high public value, but current validation only confirms a public map/table route, not a durable product ingestion path.
- **Decision:** keep it warm, but do not allow it into Batch A unless a structured access route is verified.

---

## Provisional Batch A Recommendation

### Recommended Batch A domains

1. provider / facility baseline
2. AED strategy
3. recalls / safety alerts / product reference
4. AQHI as the first environmental overlay

### Recommended Batch B domains

1. EMS / system context
2. naloxone access, only if a stronger reuse path is confirmed

### Parked for later broader scanning

- inspections and municipal compliance data
- infectious disease and immunization tools
- long-term care reporting
- broader environmental and advisory overlays beyond AQHI

These remain interesting, but they are not required to choose the first milestone-planning target.
