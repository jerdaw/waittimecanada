# Occupancy Statistics Research

**Research Date:** February 6, 2026

## Executive Summary

Of the three provinces currently implemented, **only Quebec provides occupancy data**. Ontario and BC focus exclusively on wait time metrics.

---

## Quebec MSSS

### Available: ✅ Yes

**Metric Name:** "Occupancy rate of stretchers" (Taux d'occupation sur civière)

**Location:** Same data source as wait times
**URL:** https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec

**Format:** Percentage (e.g., "127%", "150%")

**Definition:** Current patients or occupied stretchers divided by total stretcher capacity. Values >100% indicate overcapacity (hallway medicine, patients on gurneys).

**Sample Data (from live site):**
| Hospital | Occupancy Rate |
|----------|----------------|
| CHUM (Montreal) | 127% |
| St. Mary's (Montreal) | 150% |
| CHUL (Quebec City) | 95% |
| Centre de santé de Chibougamau | 167% |
| **Province-wide Average** | **110%** |

**Update Frequency:** Real-time (same as wait times)

**Current Implementation Status:**
- Data is available in Quebec scraper HTML
- Currently filtered out (line 187 in `quebec.py` comments: "We only store TIME_TO_PROVIDER metrics")
- Can be easily added with `STRETCHER_OCCUPANCY` metric family

**Data Structure in HTML:**
```html
<li class="hopital-item">
    Occupancy rate of stretchers:
    <span class="font-weight-bold">127%</span>
</li>
```

**Clinical Significance:**
- Values >100% indicate hospital overcrowding
- Strong correlation with wait times
- Useful for "avoid this ER" recommendations

---

## Ontario HQO

### Available: ❌ No

**URL:** https://www.hqontario.ca/System-Performance/Time-Spent-in-Emergency-Departments

**Available Metrics:**
1. Wait time to first assessment
2. Length of stay for low-urgency patients (P90)
3. Length of stay for high-urgency patients (P90)
4. Length of stay for admitted patients (P90)

**Data Type:** Historical monthly aggregates (not real-time)

**Latest Data:** August 2024

**No Capacity/Occupancy Data:** The HQO portal does not provide:
- Current patient counts
- Beds available
- Occupancy percentages
- Stretcher counts

**Why Not Available:**
Ontario's methodology focuses on process times (wait, length of stay) rather than capacity utilization. This may be due to:
- Privacy concerns (patient counts)
- Different operational definitions across hospitals
- Focus on outcome metrics vs. input metrics

**Alternative Data Sources (Not Real-Time):**
- Canadian Institute for Health Information (CIHI) NACRS database
- Monthly hospital reports (not publicly accessible)

---

## BC PHSA

### Available: ❌ No

**URL:** https://edwaittimes.ca

**Available Metrics:**
1. Wait time to physician (P90)
2. Estimated length of stay (P75)

**Data Structure (from `__NEXT_DATA__` JSON):**
```json
{
  "waitTime": {
    "waitTimeMinutes": 282,
    "elosMinutes": 601,
    "status": "normal",
    "createdAt": "2026-02-06T20:38:00.000Z"
  }
}
```

**No Occupancy Fields:** The JSON payload contains:
- `status` field (values: "normal", possibly "busy"/"closed")
- No patient counts, bed availability, or occupancy percentages

**Why Not Available:**
Similar to Ontario, BC focuses on wait time transparency rather than capacity metrics. The `status` field provides a qualitative indicator but not quantitative occupancy.

---

## Comparability Analysis

### Metric Family Ontology

If Quebec occupancy data is implemented:

```python
MetricFamily.STRETCHER_OCCUPANCY = "STRETCHER_OCCUPANCY"
```

**Ontology Tags:**
- **metric_family:** STRETCHER_OCCUPANCY
- **start_event:** N/A (snapshot metric)
- **end_event:** N/A
- **statistic_type:** POINT_ESTIMATE (current value)
- **unit:** PERCENT (%)

**Comparability:**
- ❌ **Cannot compare across provinces** (ON/BC don't provide this metric)
- ✅ **Can compare across Quebec hospitals** (same methodology)
- ✅ **Can track trends over time** (occupancy vs. wait time correlation)

---

## Recommendations

### Implement Now

**Quebec Occupancy Data - Estimated Effort: 2-3 hours**

**Why:**
1. Already available in existing HTML
2. Provides clinical context ("150% occupancy explains 4-hour wait")
3. Demonstrates "stretcher occupancy" metric family for schema completeness
4. Useful for future provinces (Alberta may have similar data)

**Implementation Steps:**
1. Update Quebec scraper to extract occupancy percentage
2. Create measurements with `STRETCHER_OCCUPANCY` metric family
3. Update frontend to display occupancy badge on Quebec hospitals
4. Add occupancy to comparability matrix (note: QC-only metric)

**Code Changes:**
```python
# In quebec.py parse method
occupancy_match = re.search(
    r"Occupancy rate.*?(\d+)\s*%",
    li_text,
    re.IGNORECASE
)
if occupancy_match:
    occupancy_pct = float(occupancy_match.group(1))
    occupancy_measurement = Measurement(
        hospital_id=hospital_id,
        source_id=self.source.id,
        value=occupancy_pct,
        metric_family=MetricFamily.STRETCHER_OCCUPANCY,
        start_event=StartEvent.NONE,
        end_event=EndEvent.NONE,
        statistic_type=StatisticType.POINT_ESTIMATE,
        ...
    )
```

### Defer

**Ontario & BC Occupancy** - Not publicly available

These provinces would need to:
- Add occupancy metrics to their official portals
- Define consistent methodology
- Provide real-time updates

**Monitor for future availability** - Check portal updates quarterly.

---

## Database Schema Impact

### Required Changes

**Add to `core/enums.py`:**
```python
class MetricFamily(str, Enum):
    TIME_TO_PROVIDER = "TIME_TO_PROVIDER"
    TOTAL_LOS = "TOTAL_LOS"
    STRETCHER_OCCUPANCY = "STRETCHER_OCCUPANCY"  # NEW
```

**Add to `core/enums.py` (for non-temporal metrics):**
```python
class StartEvent(str, Enum):
    TRIAGE = "TRIAGE"
    REGISTRATION = "REGISTRATION"
    DOOR = "DOOR"
    UNKNOWN = "UNKNOWN"
    NONE = "NONE"  # NEW - for snapshot metrics
```

**Database Migration:**
- No schema changes needed (enums are application-level)
- Measurements table already supports all required fields
- CHECK constraint validates metric_family enum

---

## Frontend Display Ideas

### Hospital Card Enhancement (Quebec Only)

```tsx
{hospital.province === 'QC' && hospital.occupancy && (
  <div className={clsx(
    "text-xs px-2 py-1 rounded",
    hospital.occupancy > 100 ? "bg-danger/10 text-danger" : "bg-muted"
  )}>
    {hospital.occupancy}% occupancy
  </div>
)}
```

### Divergence Warning

When comparing Quebec hospital with ON/BC:
> ⚠️ Occupancy data available for Quebec only. Ontario and BC do not publish capacity metrics.

---

## Future Research

### Alberta (If Implemented)

Check if Alberta Health Services provides:
- Emergency department occupancy
- Beds available/total beds
- "Zone capacity" status (Red/Yellow/Green)

**URL to investigate:** Alberta Health Services Emergency Wait Times portal

### National Comparison

**CIHI NACRS Database** includes occupancy metrics but:
- Historical data only (not real-time)
- Requires data request/agreement
- Aggregated monthly (not hospital-specific live data)

---

## Sources

1. Quebec MSSS Emergency Room Portal: https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec
2. Ontario HQO System Performance: https://www.hqontario.ca/System-Performance/Time-Spent-in-Emergency-Departments
3. BC PHSA Emergency Wait Times: https://edwaittimes.ca
4. CIHI NACRS: https://www.cihi.ca/en/national-ambulatory-care-reporting-system-nacrs

---

## Conclusion

**Occupancy data is available and ready to implement for Quebec.**

The metric would:
- ✅ Demonstrate schema completeness (all metric families functional)
- ✅ Provide clinical context for high wait times
- ✅ Enable "avoid this ER" logic (e.g., "150% occupancy - consider alternative facility")
- ❌ Not comparable across provinces (Quebec-only data)

**Next Steps:**
1. Add `STRETCHER_OCCUPANCY` to metric family enum
2. Update Quebec scraper to extract and store occupancy
3. Add occupancy badge to hospital cards (frontend)
4. Document in methodology that this is a Quebec-specific metric

**Estimated Total Implementation:** 2-3 hours (scraper + frontend + tests)
