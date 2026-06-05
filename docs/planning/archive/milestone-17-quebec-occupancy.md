# Milestone 17: Quebec Occupancy Implementation

**Status:** ✅ COMPLETE (2026-02-11)
**ADR:** [0012-occupancy-availability-contract](../../adr/0012-occupancy-availability-contract.md)

---

## Objective

Implement end-to-end occupancy data collection and API for Quebec emergency departments, extracting real-time stretcher occupancy percentages from the MSSS portal.

## Success Criteria

- [x] Quebec scraper extracts stretcher occupancy percentages (e.g., "127%", "110%")
- [x] Measurements stored with `STRETCHER_OCCUPANCY` metric family
- [x] API endpoint `/api/analytics/occupancy?province=QC` returns real-time data
- [x] Comprehensive unit tests (17 total for Quebec scraper)
- [x] Backend tests passing (375 total)

## Implementation Summary

### Backend Changes

**Files Modified:**
- `backend/src/waittime/scrapers/quebec.py`
  - Modified `_extract_from_facility()` to return list of measurements
  - Added `_extract_occupancy_percentage()` method for parsing percentage strings
  - Added `_create_occupancy_measurement()` method for STRETCHER_OCCUPANCY measurements
  - Parse logic handles both English and French text

- `backend/tests/unit/test_quebec_scraper.py`
  - Added 4 new occupancy-specific tests
  - Updated existing tests to expect occupancy measurements
  - Coverage: 86% for quebec.py

**Key Implementation:**
```python
def _extract_occupancy_percentage(self, text: str) -> float | None:
    """Extract occupancy percentage from text like '127%' or '95.5%'."""
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if match:
        return float(match.group(1))
    return None

def _create_occupancy_measurement(
    self, facility_id: str, occupancy_percentage: float,
    payload_hash: str, payload_snippet: str
) -> Measurement:
    """Create a stretcher occupancy measurement."""
    return Measurement(
        hospital_id=facility_id,
        value=occupancy_percentage,
        metric_family="STRETCHER_OCCUPANCY",
        start_event="UNKNOWN",
        end_event="UNKNOWN",
        statistic_type="POINT_ESTIMATE",
        patient_scope="ALL",
        timestamp_utc=datetime.now(timezone.utc),
        raw_payload_hash=payload_hash,
        raw_payload_snippet=payload_snippet,
        parser_version="v2.1",  # Incremented for occupancy support
        source_id=self.source.id,
    )
```

### API Changes

**Files Modified:**
- `frontend/app/api/analytics/occupancy/route.ts`
  - Added check for STRETCHER_OCCUPANCY measurements
  - Returns percentage-based data for Quebec
  - Supports both percentage and raw count formats (future provinces)

- `frontend/tests/api/analytics-occupancy.test.ts`
  - Updated 6 tests to match new query structure
  - Added mocks for STRETCHER_OCCUPANCY queries

**API Response Format:**
```json
{
  "province": "QC",
  "timestamp": "2026-02-11T15:30:00Z",
  "occupancy_percentage": {
    "average": 108.5,
    "min": 85.0,
    "max": 145.0,
    "hospitals_reporting": 95,
    "note": "Stretcher occupancy rate as percentage. >100% indicates overcrowding."
  }
}
```

## Test Results

**Backend:**
- Quebec scraper: 17/17 tests passing
- Total backend: 375 tests passing
- Coverage: 77% overall, 86% for quebec.py

**Frontend:**
- Occupancy API: 6/6 tests passing
- Total frontend: 285/287 tests passing (2 pre-existing failures)

## Documentation

**Files Created/Updated:**
- `backend/docs/methodologies/quebec-methodology.md` - Updated with occupancy details
- `IMPLEMENTATION_SUMMARY.md` - Added Phase 5 section

## Clinical Context

**Stretcher Occupancy Metric:**
- **Definition:** Current ED patients / stretcher capacity
- **Interpretation:**
  - <90%: Below capacity, good access
  - 90-110%: Near/at capacity
  - >110%: Overcrowded, extended waits likely
- **Correlation:** Strong predictor of wait times
- **Quebec-specific:** Only province reporting this metric publicly

## Known Limitations

1. **Province Coverage:** Quebec only (ON/AB/BC do not publish occupancy data)
2. **Data Format:** Percentage-based (not raw counts)
3. **Update Frequency:** Matches wait time updates (~15 minutes)

## Future Enhancements

1. Frontend visualization (M18)
2. Historical occupancy trends
3. Occupancy-based system-pressure indicators
4. Alert thresholds for overcrowding

## Effort Estimate vs Actual

**Estimated:** 2-3 hours
**Actual:** ~2.5 hours

## References

- ADR-0012: Occupancy Availability Contract
- Quebec MSSS Portal: https://www.quebec.ca/sante/systeme-et-services-de-sante/urgences
- Metric Ontology: STRETCHER_OCCUPANCY metric family

---

**Completed:** 2026-02-11
**Delivered By:** M17 milestone
