# UX Polish & SEO Implementation Plan

> Milestone 7: Features for improving SEO and user experience

**Created:** 2026-02-04
**Status:** Draft - Awaiting Review

---

## Background

This milestone focuses on improving the application's discoverability through SEO enhancements and polishing the user experience with modern loading patterns, search functionality, and location-based features.

---

## User Review Required

> [!IMPORTANT]
> Please review the priority ordering and scope of features. Some optional items can be deferred if time-constrained.

---

## Proposed Changes

### Phase 1: SEO & Structured Data (High Priority)

Schema.org structured data significantly improves search result appearance (rich snippets, FAQ dropdowns, "HowTo" cards).

---

#### [NEW] [structured-data.tsx](file:///home/jer/localsync/waittimecanada/frontend/app/structured-data.tsx)

New component containing JSON-LD scripts for schema.org markup:
- `FAQPage` - 5-6 methodology Q&A pairs for rich snippet dropdowns
- `MedicalWebPage` - Healthcare classification for Google Health Search
- `Organization` - Publisher info with social links
- `HowTo` - Step-by-step usage guide for featured snippets

---

#### [MODIFY] [layout.tsx](file:///home/jer/localsync/waittimecanada/frontend/app/layout.tsx)

Add healthcare-specific meta tags:
```tsx
// New metadata additions
other: {
  'geo.region': 'CA-ON',
  'geo.placename': 'Ontario', 
  'geo.position': '43.6532;-79.3832',
  'revisit-after': '1 day',
  'category': 'health',
  'classification': 'Healthcare Information',
}
```

Import and render `StructuredData` component in layout.

---

### Phase 2: Loading States (Medium Priority)

Skeleton screens improve perceived performance by showing content-shaped placeholders.

---

#### [NEW] [components/skeletons/](file:///home/jer/localsync/waittimecanada/frontend/components/skeletons/)

Create skeleton directory with:

- **HospitalCardSkeleton.tsx** - Matches HospitalList card dimensions
- **HeroSkeleton.tsx** - Matches Hero component layout  
- **MapSkeleton.tsx** - Already exists, may enhance

Skeleton pattern:
```tsx
<div className="h-4 w-3/4 rounded bg-muted animate-pulse mb-1" />
```

---

#### [MODIFY] [HospitalList.tsx](file:///home/jer/localsync/waittimecanada/frontend/components/HospitalList.tsx)

Add loading state prop and render skeletons when `loading={true}`.

---

### Phase 3: Search & Filter (Medium Priority)

Allow users to quickly find hospitals by name or city.

---

#### [MODIFY] [HospitalList.tsx](file:///home/jer/localsync/waittimecanada/frontend/components/HospitalList.tsx)

Add search functionality:
- Search input above list (sticky header)
- Filter by `hospital.name` or `hospital.city`
- Case-insensitive substring matching
- Clear button to reset filter

---

#### [MODIFY] [page.tsx](file:///home/jer/localsync/waittimecanada/frontend/app/page.tsx)

Lift search state to page level if needed for map synchronization.

---

### Phase 4: Geolocation Sorting (Medium Priority)

"Near Me" feature sorts hospitals by distance from user's location.

---

#### [NEW] [utils/distance.ts](file:///home/jer/localsync/waittimecanada/frontend/utils/distance.ts)

Haversine distance calculation:
```typescript
export function calculateDistance(
  lat1: number, lon1: number,
  lat2: number, lon2: number
): number {
  // Returns distance in km
}
```

---

#### [MODIFY] [page.tsx](file:///home/jer/localsync/waittimecanada/frontend/app/page.tsx)

Add geolocation state:
```tsx
const [userLocation, setUserLocation] = useState<{lat: number, lon: number} | null>(null);
const [sortByDistance, setSortByDistance] = useState(false);

// Request permission on user action
const requestLocation = () => {
  navigator.geolocation.getCurrentPosition(
    (pos) => setUserLocation({lat: pos.coords.latitude, lon: pos.coords.longitude}),
    (err) => console.log('Location denied:', err)
  );
};
```

---

#### [MODIFY] [HospitalList.tsx](file:///home/jer/localsync/waittimecanada/frontend/components/HospitalList.tsx)

- Accept `userLocation` prop
- When available, display distance in km next to each hospital
- Add sort toggle: "Nearest" vs default ordering

---

### Phase 5: Enhanced Live Indicators (Low Priority)

More prominent "LIVE" badges on hospitals with fresh data.

---

#### [MODIFY] [HospitalList.tsx](file:///home/jer/localsync/waittimecanada/frontend/components/HospitalList.tsx)

Add live indicator to each card:
```tsx
{hospital.last_updated && isRecent(hospital.last_updated) && (
  <span className="flex items-center gap-1 text-xs text-emerald-600">
    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
    LIVE
  </span>
)}
```

Helper function:
```tsx
function isRecent(dateStr: string): boolean {
  const updated = new Date(dateStr);
  const now = new Date();
  return (now.getTime() - updated.getTime()) < 30 * 60 * 1000; // 30 min
}
```

---

## Verification Plan

### Automated Tests

#### Existing Tests to Run
All existing component tests should continue passing after changes:

```bash
# Frontend unit tests (Vitest)
cd frontend && npm run test:unit
```

Expected: All 10+ component tests pass (Hero.test.tsx, HospitalList.test.tsx if exists, etc.)

---

#### New Tests to Add

1. **Skeleton Component Tests** - New file: `tests/components/skeletons.test.tsx`
   - Test skeleton renders with animate-pulse class
   - Test matching dimensions to actual components

2. **Search Filter Tests** - Add to `HospitalList.test.tsx` (or create if not exists)
   - Test filtering by hospital name
   - Test filtering by city
   - Test clear button resets filter
   - Test empty results message

3. **Distance Utility Tests** - New file: `tests/utils/distance.test.ts`
   - Test known distance calculation (Toronto-Ottawa ≈ 400km)
   - Test edge cases (same point = 0)

4. **Structured Data Tests** - New file: `tests/components/StructuredData.test.tsx`
   - Test JSON-LD renders valid structure
   - Test required schema.org types present

Run new tests:
```bash
cd frontend && npm run test:unit
```

---

### Manual Verification

#### SEO Structured Data
1. Run `npm run dev` in frontend
2. Open http://localhost:3000
3. View Page Source (Ctrl+U)
4. Search for `application/ld+json`
5. Verify FAQPage, MedicalWebPage, Organization schemas present
6. Validate at https://validator.schema.org/ (paste URL or JSON)

#### Skeleton Loading
1. Open browser DevTools → Network tab
2. Set throttling to "Slow 3G"
3. Refresh http://localhost:3000
4. Observe skeleton screens appear before content loads
5. Verify skeletons match final content dimensions

#### Search/Filter
1. Load homepage with hospitals visible
2. Type hospital name in search box
3. Verify list filters in real-time
4. Type city name → verify filtering works
5. Click clear → verify list resets

#### Geolocation Sorting
1. Click "Near Me" or location button
2. Accept browser permission prompt
3. Verify hospitals reorder by distance
4. Verify distance (e.g., "5.2 km") shows on each card
5. Test with location denied → verify graceful fallback

#### Live Indicators
1. View hospital list
2. Identify hospitals with `last_updated` < 30 minutes ago
3. Verify green pulsing "LIVE" badge appears
4. Verify hospitals with old data don't show badge

---

## Files Changed Summary

| File | Action | Description |
|------|--------|-------------|
| `app/structured-data.tsx` | NEW | Schema.org JSON-LD components |
| `app/layout.tsx` | MODIFY | Add meta tags, import structured data |
| `components/skeletons/` | NEW | Skeleton loading components |
| `components/HospitalList.tsx` | MODIFY | Add search, distance, skeletons, live badges |
| `app/page.tsx` | MODIFY | Add geolocation state, search state |
| `utils/distance.ts` | NEW | Haversine distance calculation |
| `tests/components/skeletons.test.tsx` | NEW | Skeleton tests |
| `tests/components/HospitalList.test.tsx` | NEW/MODIFY | Search/filter tests |
| `tests/utils/distance.test.ts` | NEW | Distance utility tests |
| `tests/components/StructuredData.test.tsx` | NEW | Schema validation tests |

---

## Implementation Order

1. **Phase 1: SEO** - Independent, can deploy immediately
2. **Phase 2: Skeletons** - Independent, visual improvement
3. **Phase 3: Search** - Depends on list structure
4. **Phase 4: Geolocation** - Depends on Phase 3 sorting logic
5. **Phase 5: Live Indicators** - Independent, can parallelize

**Estimated Effort:** 2-3 days for all phases

---

## Out of Scope

Items intentionally NOT included:
- Removing methodology transparency (our differentiator)
- Ontario-only branding (we're multi-province)
- MapTiler migration (Mapbox is equivalent)
- Full PWA enhancements (already have manifest/SW)
