# Scraper Implementation Status Report

**Date:** 2026-02-04
**Author:** Development Team
**Status:** Ontario Working, Quebec Broken

---

## Executive Summary

The first production scraper run completed on 2026-02-04. Ontario data is successfully being collected and stored. Quebec scraper requires updates due to government website changes.

| Province | Status | Hospitals | Measurements | Issues |
|----------|--------|-----------|--------------|--------|
| Ontario | ✅ Working | 154 total (72 geocoded) | 164 per run | 82 hospitals with placeholder coords |
| Quebec | ❌ Broken | 0 | 0 | Government changed URL and page format |

---

## Ontario Scraper - Detailed Status

### What's Working

- **Data Collection:** Successfully scraping 164 measurements from 154 hospitals every 15 minutes
- **Source:** Health Quality Ontario (hqontario.ca)
- **Methodology:** Triage → Physician, 90th percentile (P90)
- **Heartbeat:** Writing status to database on successful runs

### Geocoding Results

| Category | Count | Percentage |
|----------|-------|------------|
| Successfully geocoded | 72 | 47% |
| Failed geocoding (placeholder) | 82 | 53% |
| **Total hospitals** | **154** | **100%** |

#### Why 82 Hospitals Failed Geocoding

1. **Complex hospital names**: Names like "Georgian Bay General Hosp Midland Site" or "Bluewater Health Charlotte Eleanor Englehart Petrolia" are too specific for Nominatim to find
2. **Multi-site health systems**: "Brightshores Health System-Owen Sound" doesn't match any POI in OpenStreetMap
3. **Abbreviated names**: "Trillium Health Partners-Queensway Hlth" uses non-standard abbreviations
4. **No Mapbox fallback**: MAPBOX_TOKEN not configured in GitHub Secrets

#### Sample Failed Hospitals (need manual coordinates)

| Hospital Name | Generated ID | Reason |
|--------------|--------------|--------|
| Georgian Bay General Hosp Midland Site | ca-on-georgian-bay-general-hosp-midland-site | Complex name |
| Bluewater Health Charlotte Eleanor Englehart Petrolia | ca-on-bluewater-health-charlotte-eleanor-englehart-petrolia | Long name |
| Chatham Kent Health Alliance Chatham | ca-on-chatham-kent-health-alliance-chatham | Multi-part name |
| Muskoka Algonquin Healthcare Bracebridge | ca-on-muskoka-algonquin-healthcare-bracebridge | Health system name |
| Sinai Health System Mount Sinai Site | ca-on-sinai-health-system-mount-sinai-site | Site suffix confuses geocoder |

### Performance Metrics

- **Scrape time:** ~5 seconds (Playwright)
- **Geocoding time:** ~7-8 minutes for 154 hospitals (first run)
- **Future runs:** Will skip geocoding for existing hospitals (< 1 minute expected)
- **Workflow timeout:** Increased to 20 minutes (from 10)

### Optimizations Applied (2026-02-04)

1. **Accept low-confidence Nominatim results:** Changed threshold from >0.7 to accept any result
2. **Skip existing hospitals:** Only geocode NEW hospitals that don't have valid coordinates
3. **Better logging:** Now shows "Geocoded X new, skipped Y existing"

---

## Quebec Scraper - Detailed Status

### The Problem

Quebec government **changed their URL and page format** sometime in early 2026:

| Attribute | Old (Broken) | New |
|-----------|-------------|-----|
| URL | `https://www.quebec.ca/sante/systeme-et-services-de-sante/urgences` | `https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec` |
| HTTP Status | **404 Not Found** | 200 OK |
| Data Format | HTML table | Dynamic searchable interface |
| Parsing | BeautifulSoup | Requires Playwright or API |

### New Page Characteristics

The new Quebec emergency room page uses:
- **Searchable facility list** (not a simple table)
- **Location-based search** with geolocation support
- **Individual facility cards** with icons
- **Metrics per facility:**
  - Estimated waiting time for non-priority cases
  - Number of people waiting to see a doctor
  - Total number of people in the emergency room
  - Occupancy rate of stretchers
  - Average previous-day wait times
- **Data source:** Console provinciale des urgences (CPU), MSSS
- **Update frequency:** Near real-time (noted as "February 3 at 7:00 p.m.")

### Required Changes

1. **Option A: Use Playwright** (Recommended)
   - Similar to Ontario scraper
   - Wait for JavaScript to load facility cards
   - Parse card content for wait times
   - Pros: Reliable, handles dynamic content
   - Cons: Slower, requires browser

2. **Option B: Find API Endpoint**
   - Inspect network requests on the page
   - Find underlying JSON/API endpoint
   - Parse structured data directly
   - Pros: Faster, no browser needed
   - Cons: May not exist or may change

3. **Option C: Different Data Source**
   - Check if MSSS has a data portal or open data
   - Look for provincial health data APIs
   - Pros: Official, structured data
   - Cons: May not be real-time

### Files Requiring Updates

| File | Change Required |
|------|-----------------|
| `backend/src/waittime/scrapers/quebec.py` | Rewrite parser for new format |
| `backend/migrations/004_seed_sources.sql` | ✅ URL updated |
| `backend/tests/unit/scrapers/test_quebec_scraper.py` | Update test fixtures |

---

## Geocoding Service - Issues & Improvements

### Current Architecture

```
Hospital Name
    ↓
GeocodingService.geocode_hospital()
    ↓
_geocode_with_nominatim() [FREE, 1 req/sec rate limit]
    ↓ (if confidence <= 0.7 and MAPBOX_TOKEN set)
_geocode_with_mapbox() [PAID, requires API token]
    ↓
GeocodingResult(latitude, longitude, city, confidence)
```

### Issues Identified

1. **Rate Limiting:** Nominatim requires 1 second between requests
   - 154 hospitals × ~3 queries each = ~462 seconds (7.7 minutes) minimum
   - Solution: Skip existing hospitals (implemented)

2. **Low Match Rate:** Only 47% of hospitals successfully geocoded
   - OpenStreetMap data quality varies
   - Hospital names don't match POI names exactly
   - Solution: Use Mapbox as fallback or manual coordinates

3. **Placeholder Coordinates:** Hospitals that fail geocoding get (0.0, 0.0)
   - These won't appear correctly on the map
   - Need manual intervention or better geocoding

### Improvement Options

| Option | Effort | Cost | Accuracy |
|--------|--------|------|----------|
| Add MAPBOX_TOKEN | Low | ~$5/month | High |
| Manual coordinates CSV | Medium | Free | 100% |
| Improve name parsing | Medium | Free | Variable |
| Use Google Places API | Low | Pay per use | Very High |

### Recommended: Manual Coordinates CSV

Create a CSV file with coordinates for the 82 failed hospitals:

```csv
hospital_id,latitude,longitude,city
ca-on-georgian-bay-general-hosp-midland-site,44.7457,-79.8829,Midland
ca-on-bluewater-health-charlotte-eleanor-englehart-petrolia,42.8778,-82.1363,Petrolia
...
```

Then update the scraper to check this CSV before geocoding.

---

## GitHub Actions Workflows

### scraper-cron.yml

| Setting | Value | Notes |
|---------|-------|-------|
| Schedule | `*/15 * * * *` | Every 15 minutes |
| Timeout | 20 minutes | Increased from 10 |
| Secrets Required | DATABASE_URL, PUSHOVER_USER_KEY, PUSHOVER_API_TOKEN | All configured |

### Current Behavior

- Runs both Ontario and Quebec scrapers
- If ONE scraper fails, workflow exits with code 1
- Ontario data is still written even if Quebec fails
- Pushover notification sent on failure

### Recommendation

Consider making scrapers independent:
- Continue even if one province fails
- Report partial success
- Only fail if ALL scrapers fail

---

## Verification Queue Status

All 154 Ontario hospitals are in the verification queue with:
- `is_verified = FALSE`
- `is_visible = FALSE`

**Action Required:** Admin must verify hospitals before they appear on the public map.

Access: `/admin/verify` on the frontend

---

## Action Items

### Immediate (Before Next Deploy)

- [x] Update Quebec URL in codebase
- [x] Increase GitHub Actions timeout
- [x] Fix geocoding to accept low-confidence results
- [x] Skip geocoding for existing hospitals
- [ ] Verify Ontario data appears on frontend

### Short-term (This Week)

- [ ] Verify sample Ontario hospitals in admin queue
- [ ] Test frontend map with real data
- [ ] Investigate Quebec page API endpoints
- [ ] Plan Quebec scraper rewrite

### Medium-term (Next 2 Weeks)

- [ ] Rewrite Quebec scraper for new format
- [ ] Create manual coordinates CSV for failed hospitals
- [ ] Add Mapbox token for better geocoding (optional)
- [ ] Make workflow tolerant of partial failures

### Long-term (Backlog)

- [ ] Add Alberta, Manitoba, BC scrapers
- [ ] Historical data analysis
- [ ] Wait time trend notifications

---

## Appendix: Error Logs

### Quebec Scraper Error (2026-02-04 01:23:04)

```
httpx.HTTPStatusError: Client error '404 Not Found' for url
'https://www.quebec.ca/sante/systeme-et-services-de-sante/urgences'
```

### Sample Geocoding Failures

```
2026-02-04 01:22:41 [WARNING] Failed to geocode Georgian Bay General Hosp Midland Site
2026-02-04 01:22:44 [WARNING] Failed to geocode Bluewater Health Charlotte Eleanor Englehart Petrolia
2026-02-04 01:22:48 [WARNING] Failed to geocode Chatham Kent Health Alliance Chatham
2026-02-04 01:22:54 [WARNING] Failed to geocode Muskoka Algonquin Healthcare Bracebridge
```

### Successful Geocoding (Low Confidence Accepted)

```
2026-02-04 01:22:51 [INFO] ✅ Nominatim: Wingham And District Hospital → (43.8849, -81.3067) Carling Terrace
2026-02-04 01:22:51 [INFO] Using Nominatim result for Wingham And District Hospital (confidence=0.00)
```

---

*This document should be updated after each significant scraper change or deployment.*
