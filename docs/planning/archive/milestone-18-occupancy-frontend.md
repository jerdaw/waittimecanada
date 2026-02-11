# Milestone 18: Occupancy Frontend UI

**Status:** ✅ COMPLETE (2026-02-11)
**Depends On:** M17 (Quebec Occupancy Implementation)

---

## Objective

Create visual indicators for Quebec hospital stretcher occupancy on the frontend, displaying color-coded badges and integrating occupancy data into the hospital list.

## Success Criteria

- [x] OccupancyBadge component with color-coded indicators
- [x] Hospital API returns occupancy data via LATERAL join
- [x] Occupancy displayed on Quebec hospital cards
- [x] Methodology information banner for Quebec hospitals
- [x] Comprehensive unit tests (15 tests for OccupancyBadge)
- [x] Frontend tests passing (285/287)

## Implementation Summary

### Component Creation

**Files Created:**
- `frontend/components/OccupancyBadge.tsx` - Reusable badge component
- `frontend/tests/components/OccupancyBadge.test.tsx` - 15 unit tests

**Component Features:**
```tsx
interface OccupancyBadgeProps {
  percentage: number;
  size?: "sm" | "md";
  className?: string;
}

// Color thresholds:
// - Green (<90%): Below capacity
// - Yellow (90-110%): Near capacity
// - Red (>110%): Overcrowded with pulse animation
```

**Visual Indicators:**
- Color-coded dot (green/yellow/red)
- Percentage text display
- Pulse animation for overcrowded (>110%)
- Hover tooltips with context
- Responsive sizing (sm/md)

### API Integration

**Files Modified:**
- `frontend/app/api/hospitals/route.ts`
  - Added `occupancy_percentage` and `occupancy_updated` to Hospital interface
  - Implemented LATERAL join to fetch latest STRETCHER_OCCUPANCY measurement
  - Query optimized for performance

**Query Implementation:**
```sql
LEFT JOIN LATERAL (
  SELECT value, timestamp_utc
  FROM measurements
  WHERE hospital_id = h.id
    AND metric_family = 'STRETCHER_OCCUPANCY'
  ORDER BY timestamp_utc DESC
  LIMIT 1
) occ ON true
```

### UI Integration

**Files Modified:**
- `frontend/components/HospitalList.tsx`
  - Imported and integrated OccupancyBadge component
  - Added conditional display (Quebec only)
  - Added methodology information banner
  - Positioned badge below wait time display

**User Experience:**
```tsx
{hospital.occupancy_percentage !== undefined && (
  <div className="mt-1">
    <OccupancyBadge
      percentage={hospital.occupancy_percentage}
      size="sm"
    />
  </div>
)}

{/* Methodology banner for Quebec */}
{selectedProvince === "QC" && hasOccupancyData && (
  <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
    <p className="text-sm text-blue-900">
      <strong>Stretcher Occupancy:</strong> Quebec reports real-time ED capacity...
    </p>
  </div>
)}
```

## Test Results

**OccupancyBadge Component:**
- 15/15 tests passing
- Tested color thresholds (90%, 110%)
- Validated animation behavior
- Verified tooltips and accessibility
- Confirmed responsive sizing

**Integration Tests:**
- Hospital API includes occupancy fields
- HospitalList renders OccupancyBadge correctly
- Methodology banner displays when appropriate

**Overall Frontend:**
- 285/287 tests passing (2 pre-existing failures unrelated to occupancy)

## Visual Design

### Color Scheme
- **Green** (`text-green-600`): <90% occupancy - "Below capacity"
- **Yellow** (`text-yellow-600`): 90-110% occupancy - "Near capacity"
- **Red** (`text-red-600`): >110% occupancy - "Overcrowded"

### Animation
- Red badges include `animate-pulse` for visual emphasis
- Draws attention to overcrowded hospitals
- Provides immediate visual feedback

### Typography
- Small badge: `text-xs` for compact display
- Medium badge: `text-sm` for prominence
- Consistent with existing hospital card design

## Documentation

**Files Updated:**
- `IMPLEMENTATION_SUMMARY.md` - Added Phase 6 section
- `README.md` - Added occupancy to feature list

## User Impact

**Benefits:**
1. **Immediate Capacity Awareness:** Users see ED crowding at a glance
2. **Better Decision Making:** Overcrowded hospitals visible before visiting
3. **Educational:** Methodology banner explains >100% = overcrowding
4. **Quebec-Specific:** Only shown where data is available

**Safety:**
- Maintains emergency disclaimer prominence
- Occupancy is informational, not prescriptive
- Does not replace medical triage judgment

## Known Limitations

1. **Province Coverage:** Quebec only (other provinces don't publish this data)
2. **Historical Trends:** No timeline view yet (future enhancement)
3. **Recommendation Logic:** No automated "avoid this ER" suggestions

## Future Enhancements

1. **Historical Trends:** Daily/weekly occupancy patterns
2. **Smart Recommendations:** Suggest less crowded nearby hospitals
3. **Alert Thresholds:** Notify when favorite hospital becomes overcrowded
4. **Additional Provinces:** If ON/AB/BC start publishing occupancy data

## Effort Estimate vs Actual

**Estimated:** 1-2 hours
**Actual:** ~1.5 hours

## Dependencies

- M17: Quebec Occupancy Implementation (backend)
- Database: STRETCHER_OCCUPANCY measurements
- API: Occupancy data in Hospital response

## References

- Component: `frontend/components/OccupancyBadge.tsx`
- Tests: `frontend/tests/components/OccupancyBadge.test.tsx`
- API: `frontend/app/api/hospitals/route.ts`
- Integration: `frontend/components/HospitalList.tsx`

---

**Completed:** 2026-02-11
**Delivered By:** M18 milestone
