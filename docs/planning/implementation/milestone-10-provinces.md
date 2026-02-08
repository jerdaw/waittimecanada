# Milestone 10: Multi-Province Expansion

> **Priority:** HIGH - Proves methodology heterogeneity actually works
> **Estimated Effort:** 4-5 days
> **Admissions Appeal:** Scholar (demonstrates ontology works), Leader (scaling)

---

## Overview

This milestone proves that the metric ontology system works across provinces with genuinely different methodologies. Alberta is the target because their methodology differs from both Ontario and Quebec, creating a three-way comparison matrix.

---

## Research Phase (Day 1)

### 1.1 Alberta Health Services Portal Research

**Primary Source:** https://www.albertahealthservices.ca/waittimes/waittimes.aspx

**Research Tasks:**
- [ ] Document the URL structure for ER wait times
- [ ] Identify if JavaScript rendering is required (check view-source vs rendered)
- [ ] List all data fields available (wait time, patients waiting, hospital name, etc.)
- [ ] Find methodology documentation (link to "How we calculate wait times")
- [ ] Note update frequency ("Updated every X minutes")

**Expected Methodology (to verify):**
- `metric_family`: TIME_TO_PROVIDER
- `start_event`: TRIAGE (Alberta typically uses triage as start)
- `end_event`: PHYSICIAN
- `statistic_type`: POINT_ESTIMATE or MEDIAN (verify)
- `patient_scope`: ALL

### 1.2 Methodology Documentation

**File:** `docs/methodologies/alberta-methodology.md`

```markdown
# Alberta Health Services ER Wait Time Methodology

## Source
Alberta Health Services Wait Times Portal
URL: https://www.albertahealthservices.ca/waittimes/waittimes.aspx

## Measurement Definition

### What is measured?
[From AHS documentation]

### Start Event
[TRIAGE / REGISTRATION / etc.]

### End Event
[PHYSICIAN / PROVIDER / etc.]

### Statistic Type
[POINT_ESTIMATE / MEDIAN / P90 / etc.]

### Update Frequency
[Every X minutes]

## Comparison Notes

### vs Ontario
- Ontario uses: TRIAGE → PHYSICIAN, P90 (90th percentile)
- Alberta uses: [document]
- **Comparable:** [Yes/No and why]

### vs Quebec
- Quebec uses: REGISTRATION → PHYSICIAN, ROLLING_AVG
- Alberta uses: [document]
- **Comparable:** [Yes/No and why]

## Data Source Citation
[Official methodology page URL]
```

---

## Phase 1: Alberta Scraper Implementation (Day 2-3)

### Implementation Status (2026-02-08)

- [x] Implemented Alberta parser for real AHS `wt-well` card structure (Emergency-only filtering, unavailable wait-time skip, adult-vs-child handling for dual cards).
- [x] Added `create_alberta_source()` and exported Alberta scraper/source from `waittime.scrapers`.
- [x] Registered Alberta in runtime scraper CLI (`python -m waittime.cli.scraper --all`) so scheduled cron runs now include it.
- [x] Added Alberta unit tests (`backend/tests/unit/test_alberta_scraper.py`) and validated with targeted pytest run.

### 1.1 Add Alberta Source

**SQL Migration or seed script:**

```sql
INSERT INTO sources (
  id, name, province, url, methodology_url,
  default_metric_family, default_start_event, default_end_event,
  default_statistic_type, telehealth_name, telehealth_phone
) VALUES (
  'alberta-ahs',
  'Alberta Health Services',
  'AB',
  'https://www.albertahealthservices.ca/waittimes/waittimes.aspx',
  'https://www.albertahealthservices.ca/waittimes/Page14230.aspx', -- Verify this
  'TIME_TO_PROVIDER',
  'TRIAGE',  -- Verify
  'PHYSICIAN',
  'POINT_ESTIMATE',  -- Verify
  'Health Link 811',
  '811'
);
```

### 1.2 Scraper Implementation

**File:** `backend/src/waittime/scrapers/alberta.py`

```python
"""Alberta Health Services ER wait time scraper."""
import hashlib
import re
from datetime import datetime
from typing import Optional

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

from waittime.core.models import Measurement, Hospital
from waittime.core.enums import (
    MetricFamily, StartEvent, EndEvent, StatisticType, PatientScope
)
from waittime.scrapers.base import BaseScraper


class AlbertaScraper(BaseScraper):
    """Scraper for Alberta Health Services ER wait times."""

    SOURCE_ID = "alberta-ahs"
    BASE_URL = "https://www.albertahealthservices.ca/waittimes/waittimes.aspx"

    # Alberta's methodology (verify during research)
    METRIC_FAMILY = MetricFamily.TIME_TO_PROVIDER
    START_EVENT = StartEvent.TRIAGE
    END_EVENT = EndEvent.PHYSICIAN
    STATISTIC_TYPE = StatisticType.POINT_ESTIMATE
    PATIENT_SCOPE = PatientScope.ALL

    async def fetch(self) -> str:
        """Fetch the wait times page using Playwright if needed."""
        # First try simple fetch
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(self.BASE_URL) as response:
                html = await response.text()

        # Check if data is present (adjust selector based on actual page)
        if self._has_data(html):
            return html

        # Fall back to Playwright for JS-rendered content
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(self.BASE_URL)
            await page.wait_for_selector('[data-wait-time]')  # Adjust selector
            html = await page.content()
            await browser.close()
            return html

    def _has_data(self, html: str) -> bool:
        """Check if HTML contains wait time data."""
        soup = BeautifulSoup(html, 'html.parser')
        # Adjust based on actual page structure
        return bool(soup.find_all(class_='wait-time'))

    def parse(self, content: str) -> list[Measurement]:
        """Parse HTML into measurements."""
        soup = BeautifulSoup(content, 'html.parser')
        measurements = []

        # Adjust selectors based on actual page structure
        for row in soup.select('.hospital-row'):
            try:
                name = row.select_one('.hospital-name').text.strip()
                wait_text = row.select_one('.wait-time').text.strip()
                wait_minutes = self._parse_wait_time(wait_text)

                if wait_minutes is None:
                    continue

                # Generate hospital ID
                hospital_id = self._generate_hospital_id(name)

                measurement = Measurement(
                    hospital_id=hospital_id,
                    value=wait_minutes,
                    metric_family=self.METRIC_FAMILY,
                    start_event=self.START_EVENT,
                    end_event=self.END_EVENT,
                    statistic_type=self.STATISTIC_TYPE,
                    patient_scope=self.PATIENT_SCOPE,
                    raw_payload_hash=hashlib.sha256(content.encode()).hexdigest(),
                    raw_payload_snippet=content[:200],
                    parser_version="v1.0",
                    timestamp_utc=datetime.utcnow(),
                )
                measurements.append(measurement)

            except Exception as e:
                self.logger.warning(f"Failed to parse row: {e}")
                continue

        return measurements

    def _parse_wait_time(self, text: str) -> Optional[int]:
        """Parse wait time text like '2h 30m' or '45 min' into minutes."""
        text = text.lower().strip()

        # Try "Xh Ym" format
        match = re.match(r'(\d+)\s*h(?:our)?s?\s*(\d+)?\s*m(?:in)?', text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2) or 0)
            return hours * 60 + minutes

        # Try "X min" format
        match = re.match(r'(\d+)\s*m(?:in)?', text)
        if match:
            return int(match.group(1))

        # Try just hours "X hours"
        match = re.match(r'(\d+)\s*h(?:our)?s?', text)
        if match:
            return int(match.group(1)) * 60

        return None

    def _generate_hospital_id(self, name: str) -> str:
        """Generate a consistent hospital ID from name."""
        # Normalize: lowercase, remove special chars, replace spaces with hyphens
        normalized = re.sub(r'[^a-z0-9\s]', '', name.lower())
        normalized = re.sub(r'\s+', '-', normalized.strip())
        return f"ca-ab-{normalized}"

    def discover_hospitals(self, content: str) -> list[Hospital]:
        """Discover new hospitals from page content."""
        soup = BeautifulSoup(content, 'html.parser')
        hospitals = []

        for row in soup.select('.hospital-row'):
            try:
                name = row.select_one('.hospital-name').text.strip()
                city = row.select_one('.hospital-city').text.strip() if row.select_one('.hospital-city') else None

                hospital = Hospital(
                    id=self._generate_hospital_id(name),
                    source_id=self.SOURCE_ID,
                    name=name,
                    province="AB",
                    city=city,
                    is_verified=False,  # Requires manual approval
                    is_visible=False,
                )
                hospitals.append(hospital)

            except Exception as e:
                self.logger.warning(f"Failed to discover hospital: {e}")
                continue

        return hospitals
```

### 1.3 Register Scraper

**Update:** `backend/src/waittime/scrapers/__init__.py`

```python
from .quebec import QuebecScraper
from .ontario import OntarioScraper
from .alberta import AlbertaScraper

SCRAPERS = {
    'quebec-msss': QuebecScraper,
    'ontario-health': OntarioScraper,
    'alberta-ahs': AlbertaScraper,
}
```

### 1.4 Unit Tests

**File:** `backend/tests/unit/test_alberta_scraper.py`

```python
"""Tests for Alberta scraper."""
import pytest
from waittime.scrapers.alberta import AlbertaScraper
from waittime.core.enums import MetricFamily, StartEvent, EndEvent, StatisticType


class TestAlbertaScraper:
    """Test Alberta scraper parsing."""

    @pytest.fixture
    def scraper(self):
        return AlbertaScraper()

    def test_parse_wait_time_hours_minutes(self, scraper):
        assert scraper._parse_wait_time("2h 30m") == 150
        assert scraper._parse_wait_time("1 hour 15 min") == 75

    def test_parse_wait_time_minutes_only(self, scraper):
        assert scraper._parse_wait_time("45 min") == 45
        assert scraper._parse_wait_time("30m") == 30

    def test_parse_wait_time_hours_only(self, scraper):
        assert scraper._parse_wait_time("2 hours") == 120
        assert scraper._parse_wait_time("1h") == 60

    def test_generate_hospital_id(self, scraper):
        assert scraper._generate_hospital_id("Foothills Medical Centre") == "ca-ab-foothills-medical-centre"
        assert scraper._generate_hospital_id("Peter Lougheed Centre") == "ca-ab-peter-lougheed-centre"

    def test_ontology_values(self, scraper):
        """Verify Alberta uses correct ontology tags."""
        assert scraper.METRIC_FAMILY == MetricFamily.TIME_TO_PROVIDER
        assert scraper.START_EVENT == StartEvent.TRIAGE
        assert scraper.END_EVENT == EndEvent.PHYSICIAN
        # Note: Verify these match actual Alberta methodology

    def test_parse_sample_html(self, scraper, sample_alberta_html):
        """Test parsing actual-like HTML structure."""
        measurements = scraper.parse(sample_alberta_html)
        assert len(measurements) > 0
        for m in measurements:
            assert m.metric_family == MetricFamily.TIME_TO_PROVIDER
            assert m.start_event == StartEvent.TRIAGE


@pytest.fixture
def sample_alberta_html():
    """Sample HTML matching Alberta page structure."""
    return """
    <div class="hospital-row">
        <span class="hospital-name">Foothills Medical Centre</span>
        <span class="hospital-city">Calgary</span>
        <span class="wait-time">2h 30m</span>
    </div>
    <div class="hospital-row">
        <span class="hospital-name">Royal Alexandra Hospital</span>
        <span class="hospital-city">Edmonton</span>
        <span class="wait-time">1h 45m</span>
    </div>
    """
```

---

## Phase 2: Geocoding Alberta Hospitals (Day 3)

### 2.1 Hospital Data Collection

**Approach:** Same as Ontario - systematic research + Nominatim geocoding

**File:** `backend/data/hospitals/alberta-seed.json`

```json
{
  "source_id": "alberta-ahs",
  "hospitals": [
    {
      "name": "Foothills Medical Centre",
      "city": "Calgary",
      "address": "1403 29 St NW, Calgary, AB"
    },
    {
      "name": "Royal Alexandra Hospital",
      "city": "Edmonton",
      "address": "10240 Kingsway NW, Edmonton, AB"
    }
    // ... more hospitals from research
  ]
}
```

### 2.2 Geocoding Script

**Reuse existing:** `backend/scripts/import_hospitals.py`

```bash
cd backend
python scripts/import_hospitals.py \
  --input data/hospitals/alberta-seed.json \
  --output data/hospitals/alberta-geocoded.csv
```

### 2.3 Database Import

```bash
python -m waittime.cli.seed data/hospitals/alberta-geocoded.csv
```

---

## Phase 3: Frontend Updates (Day 4)

### 3.1 Province Filter Component

**File:** `frontend/components/ProvinceFilter.tsx`

```tsx
'use client';

interface ProvinceFilterProps {
  selected: string | 'all';
  onChange: (province: string | 'all') => void;
  provinces: { code: string; name: string; count: number }[];
}

export function ProvinceFilter({ selected, onChange, provinces }: ProvinceFilterProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm text-slate-500">Province:</label>
      <select
        value={selected}
        onChange={(e) => onChange(e.target.value)}
        className="px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700
                   bg-white dark:bg-slate-800 text-sm"
      >
        <option value="all">All Provinces ({provinces.reduce((a, p) => a + p.count, 0)})</option>
        {provinces.map((p) => (
          <option key={p.code} value={p.code}>
            {p.name} ({p.count})
          </option>
        ))}
      </select>
    </div>
  );
}
```

### 3.2 Update Hospital List

**Edit:** `frontend/components/HospitalList.tsx`

Add province filter state and pass through:

```tsx
const [provinceFilter, setProvinceFilter] = useState<string | 'all'>('all');

const filteredHospitals = hospitals.filter(h =>
  provinceFilter === 'all' || h.province === provinceFilter
);
```

### 3.3 Update Map Bounds

**Edit:** `frontend/components/Map.tsx`

When multiple provinces, adjust map bounds to show all:

```tsx
useEffect(() => {
  if (hospitals.length === 0 || !mapRef.current) return;

  const bounds = hospitals.reduce(
    (bounds, h) => bounds.extend([h.longitude, h.latitude]),
    new mapboxgl.LngLatBounds()
  );

  mapRef.current.fitBounds(bounds, { padding: 50 });
}, [hospitals]);
```

### 3.4 Cross-Province Comparison Warning Test

**Verify:** When comparing an Ontario hospital to an Alberta hospital, the divergence warning should appear explaining:

- Ontario: TRIAGE → PHYSICIAN, P90
- Alberta: TRIAGE → PHYSICIAN, POINT_ESTIMATE (or whatever Alberta uses)
- Conclusion: Not directly comparable due to different statistic types

---

## Phase 4: Documentation & Testing (Day 5)

### 4.1 Update Comparability Matrix

The `/methods` page should auto-update because it reads from the `sources` table. Verify that Alberta appears correctly.

### 4.2 Integration Tests

**File:** `backend/tests/integration/test_cross_province.py`

```python
"""Test cross-province comparability detection."""
import pytest
from waittime.services.comparison import ComparisonService


class TestCrossProvinceComparison:
    """Test that methodology differences are detected across provinces."""

    def test_ontario_vs_quebec_not_comparable(self, db_service):
        """Ontario P90 vs Quebec ROLLING_AVG should not be comparable."""
        comparison = ComparisonService(db_service)

        result = comparison.compare(
            hospital_a="ca-on-toronto-general",
            hospital_b="ca-qc-chum"
        )

        assert result.is_comparable is False
        assert "statistic_type" in result.divergence_brief.lower() or \
               "start_event" in result.divergence_brief.lower()

    def test_ontario_vs_alberta_comparison(self, db_service):
        """Test Ontario vs Alberta comparison detects methodology differences."""
        comparison = ComparisonService(db_service)

        result = comparison.compare(
            hospital_a="ca-on-toronto-general",
            hospital_b="ca-ab-foothills-medical-centre"
        )

        # Result depends on actual Alberta methodology
        # If statistic_type differs, should not be comparable
        if result.is_comparable:
            assert result.divergence_brief is None
        else:
            assert result.divergence_brief is not None
```

### 4.3 Update README

Add Alberta to the coverage section:

```markdown
### Current Coverage

**Ontario:** 213 hospitals | Methodology: TRIAGE → PHYSICIAN, P90
**Quebec:** Scraper ready | Methodology: REGISTRATION → PHYSICIAN, ROLLING_AVG
**Alberta:** XX hospitals | Methodology: TRIAGE → PHYSICIAN, POINT_ESTIMATE
```

---

## Verification Checklist

- [ ] Alberta methodology documented in `docs/methodologies/`
- [ ] Alberta source added to `sources` table
- [x] Alberta scraper implemented and passing tests
- [ ] Alberta hospitals geocoded and imported
- [ ] Province filter working in UI
- [ ] Map shows Alberta hospitals
- [ ] Cross-province comparison warnings working
- [ ] Comparability matrix updated on /methods page
- [ ] README updated with Alberta coverage

---

## Success Criteria

1. **50+ Alberta hospitals** in database with valid coordinates
2. **Scraper running** and collecting fresh data
3. **Methodology differences** correctly detected (AB vs QC should show divergence)
4. **Province filter** allows selecting Ontario, Quebec, or Alberta
5. **Comparability matrix** on /methods shows three provinces

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| AHS page requires auth | High | Check robots.txt, may need alternative approach |
| AHS uses different data format | Medium | Adjust scraper, document format |
| AHS methodology not documented | Medium | Contact AHS, make reasonable assumptions |
| Geocoding fails for rural hospitals | Low | Use city centroids as fallback |

---

## Time Estimate

| Task | Hours |
|------|-------|
| Research AHS portal | 2-3 |
| Document methodology | 1 |
| Implement scraper | 3-4 |
| Write scraper tests | 2 |
| Geocode hospitals | 2-3 |
| Frontend updates | 2-3 |
| Integration testing | 2 |
| Documentation | 1 |
| **Total** | **15-19 hours** |
