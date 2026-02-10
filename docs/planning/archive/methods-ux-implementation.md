# Methods UX Implementation (P1)

**Completed:** 2026-02-09
**Roadmap Item:** P1 / Methods UX

## Summary

Enhanced the `/methods` page with three new features to improve methodology transparency and researcher workflow.

## Features Implemented

### 1. CSV Export for Comparability Matrix

**File:** `frontend/components/methods/ComparabilityMatrix.tsx`

Added export functionality to download the provincial comparability matrix as a CSV file:
- Export button in the matrix legend area
- Generates CSV with province names and comparability labels
- Filename includes date: `comparability-matrix-YYYY-MM-DD.csv`
- Works client-side without server call

**Benefits:** Researchers can easily import the matrix into spreadsheet tools for analysis and documentation.

### 2. Deep-Linkable Comparisons

**File:** `frontend/components/methods/ComparabilityMatrix.tsx`

Added URL parameter support for pre-selecting province comparisons:
- URL format: `/methods?compare=Ontario,Quebec`
- Automatically highlights and expands comparison on page load
- Updates URL when user clicks matrix cells (shareable links)
- Uses Next.js `useSearchParams` and `useRouter` hooks

**Benefits:** Users can share specific province comparisons via URL. Supports direct linking from external documentation or research papers.

### 3. Methodology Timeline

**Files:**
- `frontend/components/methods/MethodologyTimeline.tsx` (new component)
- `frontend/app/methods/page.tsx` (updated to include timeline)
- `frontend/app/api/methodology/route.ts` (already existed from M14)

Displays a visual timeline of detected methodology changes:
- Fetches from `methodology_change_events` table
- Shows detection date, shift percentage, period comparisons
- Filter by province
- Color-coded severity badges (red >20%, amber >10%, blue <10%)
- Empty state with explanation when no changes detected

**Benefits:** Provides transparency about data quality events. Demonstrates system monitoring capabilities. Shows historical context for methodology divergence.

## Testing

**Tests Added:** 4 new tests in `frontend/tests/components/methods/ComparabilityMatrix.test.tsx`
- CSV export button renders
- CSV export button is clickable
- Deep-linking pre-selects cells from URL params
- URL updates when cells are clicked

**Test Results:**
- 16/16 tests passing for ComparabilityMatrix
- 269/271 overall frontend tests passing (2 pre-existing equity-layer failures)
- No regressions introduced

## Technical Details

### CSV Export Implementation
- Client-side generation using Blob API
- Downloads via temporary `<a>` tag
- No server roundtrip required

### Deep-Linking Implementation
- Uses Next.js App Router navigation hooks
- Preserves other query parameters
- Non-blocking URL updates (`scroll: false`)

### Timeline Implementation
- Fetches from existing `/api/methodology` route
- Responsive timeline layout with vertical line
- Province filter dropdown
- Timeline events sorted by detection date (newest first)

## Files Modified

1. `frontend/components/methods/ComparabilityMatrix.tsx` - CSV export + deep-linking
2. `frontend/app/methods/page.tsx` - Added timeline section
3. `frontend/tests/components/methods/ComparabilityMatrix.test.tsx` - Added 4 tests
4. `docs/planning/roadmap.md` - Marked P1/Methods UX as complete

## Files Created

1. `frontend/components/methods/MethodologyTimeline.tsx` - New timeline component

## User Impact

- **Researchers:** Can export matrix data for papers and analysis
- **Stakeholders:** Can share specific province comparisons via URL
- **Data Quality Reviewers:** Can see historical methodology changes
- **Medical School Admissions:** Demonstrates Scholar narrative competency

## Next Steps

Remaining P1 items in roadmap:
- P1 / CI hardening
- P1 / Security debt
