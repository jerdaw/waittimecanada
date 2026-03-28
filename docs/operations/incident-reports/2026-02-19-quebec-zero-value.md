# Quebec Zero-Value Incident Post-Mortem

**Incident date:** 2026-02-19
**Report date:** 2026-03-28
**Scope:** Quebec MSSS scraper persistence and validation path
**Status:** Resolved

## Executive Summary

On 2026-02-19, the Quebec MSSS scraper encountered a correctness problem around zero-valued measurements. The platform's shared `Measurement` contract and database constraint both assumed that all measurements must be **strictly positive**. That assumption held for most wait-time data, but it did not hold for Quebec's stretcher occupancy feed and did not reliably hold for every wait-time edge case.

The core problem was not a network failure or a broken parser. It was a **validation and persistence contract mismatch**: the Quebec source could legitimately expose `0%` occupancy and occasional `0`-minute values, while the platform still treated all zero values as invalid.

The immediate resolution was commit [`0738054`](https://github.com/jerdaw/waittimecanada/commit/0738054963891dcbe8ce10ff4c43de5cf32058fa), which relaxed the measurement value contract from `> 0` to `>= 0` in both the application model and the database schema. Later follow-up work tightened the interpretation again for one specific case: the current Quebec scraper now treats `0%` occupancy as a suppressed/non-reporting signal rather than a hard failure or automatically stored live occupancy reading.

## Incident Summary

### What failed

- The shared `Measurement` model required `value > 0`.
- The `measurements` table enforced the same assumption through `measurements_value_check`.
- Quebec occupancy and wait-time parsing could produce `0` as a valid parsed number.
- When that happened, the persistence layer treated the measurement as invalid.

### What did not fail

- The Quebec source itself was reachable.
- The scraper parsing logic still understood the source format.
- The ontology tags for Quebec methodology were not the issue.

This was therefore a **data-contract bug**, not a scraper-fetch incident.

## Impact

### Direct impact

- Legitimate Quebec zero-valued measurements could not be represented by the shared measurement contract.
- Quebec scraper runs risked failing or dropping measurements when zero-valued rows appeared.
- The issue created a mismatch between source reality and platform assumptions during the early occupancy rollout period.

### Product and stewardship impact

- The platform could incorrectly treat a real published source value as invalid.
- This weakened trust in the persistence path for Quebec-specific metrics.
- It exposed a broader design risk: assumptions that are safe for one metric family can become invalid when the platform expands to richer operational measures.

## Detection

The incident was surfaced during Quebec scraper/occupancy work and resolved in commit `0738054`, titled:

> Fix quebec-msss scraper by allowing zero measurement values for occupancy and wait times

The key signal was that the system's persistence rules did not match the range of values the source could legitimately emit.

## Timeline

### Before the fix

- Quebec occupancy support had expanded the kinds of values the platform needed to ingest.
- Shared validation still assumed all measurement values must be strictly positive.
- That assumption was never formally revalidated against zero-valued source cases.

### 2026-02-19

- The issue was addressed in commit `0738054`.
- The `Measurement.value` field changed from `gt=0` to `ge=0`.
- Database migration `014_relax_value_constraint.sql` dropped the old `measurements_value_check` constraint and replaced it with `CHECK (value >= 0)`.
- Unit tests were updated to prove that `0.0` is accepted and negative values remain rejected.
- Quebec scraper tests were expanded to cover `0` wait times and `0%` occupancy parsing.

### Later follow-up

- The Quebec scraper was later refined so that `0%` occupancy is treated as a suppressed/non-reporting signal in the parser layer, rather than being blindly surfaced as a live occupancy observation.
- That later choice did **not** undo the February fix. The February fix corrected the shared storage contract; the later change added a source-specific interpretation rule for occupancy.

## Root Cause

The root cause was a **bad global assumption**:

- original assumption: all measurements must be strictly positive
- actual reality: some valid public health-system measurements can be zero

This assumption leaked into two layers at once:

1. application-level validation in `backend/src/waittime/core/models.py`
2. database-level enforcement in `measurements_value_check`

That meant the system had no safe way to represent a legitimate zero value even when the parser successfully extracted it.

## Contributing Factors

### 1. Expansion from wait-time-only thinking to broader operational metrics

Strictly positive values are an easy assumption to make when most attention is on long wait-time numbers. That assumption became fragile once Quebec occupancy was added.

### 2. Shared contract reused across multiple metric families

The same `Measurement.value` field is used for:

- wait times in minutes
- occupancy percentages
- future metric families that may have different edge cases

A global positivity rule was too blunt for that broader scope.

### 3. Missing explicit zero-value test coverage earlier

Before the fix, there was no direct unit coverage proving that:

- `0` wait values should be handled explicitly
- `0%` occupancy values should be handled explicitly

## Resolution

The immediate fix in commit `0738054` did three things:

1. relaxed the Pydantic measurement contract from `gt=0` to `ge=0`
2. relaxed the database constraint from `value > 0` to `value >= 0`
3. added regression tests for zero-value parsing and validation

This restored alignment between:

- what the source could publish
- what the parser could extract
- what the platform could persist

## Why This Was the Right Immediate Fix

The February fix corrected the shared data model at the right architectural layer.

If the source can legitimately emit zero, the storage contract must be able to represent zero. Rejecting it at the core model would force later logic to encode workarounds or silently discard source reality.

The later Quebec-specific suppression rule for `0%` occupancy is a separate stewardship choice. That later rule answers:

- "Should this particular source value be surfaced as a meaningful live operational reading?"

The February fix answered the more fundamental question:

- "Can the platform's shared measurement model represent zero at all?"

Those are different decisions, and the immediate fix addressed the correct one first.

## Validation

The fix was backed by:

- migration `014_relax_value_constraint.sql`
- updated model validation tests in `backend/tests/unit/test_models.py`
- expanded Quebec scraper tests in `backend/tests/unit/test_quebec_scraper.py`

The regression coverage now explicitly checks that:

- zero values are accepted
- negative values are still rejected
- Quebec parsing recognizes `0` wait time strings
- Quebec parsing recognizes `0%` occupancy strings

## Follow-Up Actions

### Completed

- Relaxed shared validation and database constraints to allow zero values.
- Added direct unit coverage for zero-value cases.
- Later refined Quebec occupancy handling so `0%` occupancy is treated as a suppressed/non-reporting signal rather than a hard runtime failure.

### Lessons carried forward

- Do not assume one metric family's normal range applies to all metric families.
- When adding a new public metric class, explicitly re-check core validation rules.
- Zero, null, missing, and suppressed are different states and should not be collapsed together without a documented reason.

## What This Incident Demonstrates

This incident is useful because it is specific and honest:

- the source was not "broken"
- the platform's own assumption was wrong
- the fix required changing both application and database contracts
- the later refinement distinguished between representability and interpretation

That is the real lesson: operational health-data systems fail as much from bad assumptions at the boundary of interpretation as from obvious scraper breakage.

## Bottom Line

The Quebec zero-value incident was a shared-contract bug caused by assuming that all public measurements must be strictly positive. The immediate fix correctly widened the platform's data contract to represent legitimate zero values. Later work added a source-specific suppression rule for `0%` occupancy, but only after the underlying model had been corrected. The result is a more defensible distinction between:

- what the platform can represent
- what a specific source value probably means
- what should actually be surfaced to users
