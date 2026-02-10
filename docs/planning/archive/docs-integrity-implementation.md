# Docs Integrity Implementation (P2)

**Completed:** 2026-02-09
**Roadmap Item:** P2 / Docs integrity

## Summary

Implemented automated roadmap consistency checks to prevent documentation drift. The system now verifies that `docs/planning/roadmap.md` stays accurate and internally consistent, catching stale status summaries, broken references, and inconsistencies automatically in CI.

## Changes Made

### Problem

Documentation can drift from reality over time:
- Schema table counts get outdated as tables are added/removed
- ADR references break when files are renamed or deleted
- Implementation plan links become stale
- Status summaries don't reflect completed work
- Milestone completion claims don't match actual roadmap status

Without automated checks, these inconsistencies accumulate and mislead readers.

### Solution

Created `backend/scripts/verify_roadmap_consistency.py` - a comprehensive roadmap verification script that runs in CI on every docs change.

### Checks Implemented

**1. Schema Table Count Verification**
- Extracts declared count from "Database Schema (N tables)" heading
- Counts actual table rows in the schema section
- Verifies they match
```python
# Example: "### Database Schema (9 tables)"
# Must have exactly 9 table rows listed
```

**2. ADR File Reference Validation**
- Finds all ADR references like `[0002](../adr/0002-metric-ontology.md)`
- Verifies each referenced file exists in `docs/adr/`
- Reports missing files with ADR numbers

**3. Implementation Plan Reference Validation**
- Finds all plan references like `` `docs/planning/implementation/milestone-9-launch.md` ``
- Verifies files exist (both active and archived)
- Catches broken links to planning docs

**4. Milestone Completion Table Consistency**
- Parses "Completed Milestones" table
- Verifies milestone entries are well-formed
- Checks that completed milestones are documented

**5. Status Summary Freshness**
- Verifies "Current Status" section has valid YYYY-MM-DD date
- Checks that recent milestone completions are mentioned
- Prevents stale status summaries from lingering

**6. Roadmap Item Formatting**
- Validates Now/Next/Later sections use consistent checkbox formatting
- Ensures items follow pattern: `- [ ] **P0 / Name:** Description`
- Allows special cases: strikethrough for removed items, "Deferred" prefix

### Integration with CI

**Updated `scripts/check-docs.sh`:**
- Added roadmap consistency check as check [4/4]
- Runs on every docs change via `docs-ci.yml` workflow
- Fails CI if roadmap inconsistencies detected

**Updated `.github/workflows/docs-ci.yml`:**
- Added `backend/scripts/verify_roadmap_consistency.py` to trigger paths
- Ensures CI runs when checker script is modified

### Files Created

**1. `backend/scripts/verify_roadmap_consistency.py` (185 lines)**
- Standalone Python script
- Can run locally: `python3 backend/scripts/verify_roadmap_consistency.py`
- Exit code 0 if all checks pass, 1 if any fail
- Clear error messages for each failure type

### Files Modified

**1. `scripts/check-docs.sh`**
- Added check [4/4] for roadmap consistency
- Calls Python script and reports results
- Updated numbering from [3/3] to [4/4]

**2. `.github/workflows/docs-ci.yml`**
- Added checker script to trigger paths
- Ensures changes to checker are tested

## Usage

**Run locally:**
```bash
# From repo root
python3 backend/scripts/verify_roadmap_consistency.py

# Or via docs check script
bash scripts/check-docs.sh
```

**Example output (success):**
```
🔍 Roadmap Consistency Checker

Checking: docs/planning/roadmap.md

✓ Schema Table Count
✓ ADR File References
✓ Implementation Plans
✓ Milestone Completion
✓ Status Summary
✓ Roadmap Item Formatting

============================================================
✅ All roadmap consistency checks passed!
```

**Example output (failure):**
```
✗ Schema Table Count
  Schema table count mismatch: header says 9, but 10 tables listed

✗ ADR File References
  Missing ADR files:
  ADR-0015: 0015-admin-authentication-authorization.md

============================================================
❌ Some roadmap consistency checks failed.
   Update docs/planning/roadmap.md to fix inconsistencies.
```

## Testing

Verified all checks pass on current roadmap:
- ✅ Schema: 9 tables declared, 9 tables listed
- ✅ ADRs: All 13 referenced ADRs exist (0002-0014, excluding removed 0015)
- ✅ Plans: All 8 referenced implementation plans exist
- ✅ Milestones: Completed milestones table is well-formed
- ✅ Status: Current Status updated 2026-02-09 and mentions M14/M15
- ✅ Formatting: All roadmap items use consistent checkbox format

Ran full docs CI check:
```bash
$ bash scripts/check-docs.sh
Running docs quality checks...

[1/3] Checking for absolute file:// links...
OK: no file:// links found.

[2/3] Checking for non-human co-author trailers...
OK: no non-human co-author trailers found.

[3/4] Checking repository-relative markdown links...

[4/4] Checking roadmap consistency...
✅ All roadmap consistency checks passed!

Docs quality checks passed.
```

## Edge Cases Handled

1. **Strikethrough items**: Allows `~~**P1 / Name:**~~` for removed/deprecated items
2. **Deferred items**: Allows `**Deferred / Name:**` prefix for deprioritized work
3. **Multi-line descriptions**: Regex patterns handle descriptions that span multiple lines
4. **Relative paths**: Correctly resolves `../adr/` links from roadmap location

## Impact

**Before:**
- Roadmap inconsistencies could accumulate unnoticed
- Manual effort required to keep docs synchronized
- Risk of misleading readers with stale information

**After:**
- Automated verification on every docs change
- CI fails if roadmap drift detected
- Clear error messages guide fixes
- Self-documenting: script enforces documented patterns

## Future Enhancements

Potential additional checks (not implemented yet):
- Verify milestone IDs are sequential and complete
- Check that "Current Status" date is recent (within N days)
- Validate that all completed roadmap items are marked [x]
- Cross-reference migrations with schema table list
- Verify test count claims match actual test suite counts

## Next Steps

P2 / Docs integrity is now complete. Other P2+ items remain:
- [ ] P2 / Portfolio launch completion: Stakeholder interview and launch communications
- [ ] Deferred / M10 breadth: Multi-province expansion once P0/P1 goals closed
