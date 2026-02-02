# Quebec Emergency Department Data Sources

> Research findings for real-time ED wait time data in Quebec.

## Primary Data Sources

### 1. Index Santé (Recommended for Scraping)

**URL:** https://www.indexsante.ca/urgences/

**Overview:**
- Third-party aggregator covering all Quebec regions
- Updates every hour (from provincial Console provinciale des urgences)
- Free, publicly accessible
- French language

**Data Fields:**
| Field | French Name | Description |
|-------|-------------|-------------|
| `total_persons` | Nombre total de personnes | Total people at ED |
| `awaiting_physician` | En attente de prise en charge | Waiting to see doctor |
| `functional_stretchers` | Civières fonctionnelles | Available stretchers |
| `occupied_stretchers` | Civières occupées | Occupied stretchers |
| `occupancy_rate` | Taux d'occupation | Stretcher occupancy % |
| `over_24h` | +24 heures sur civière | On stretcher >24 hours |
| `over_48h` | +48 heures sur civière | On stretcher >48 hours |

**Regions Covered:**
- Montréal (18+ hospitals)
- Capitale-Nationale (12+ hospitals)
- Laval
- Montérégie
- Laurentides
- Lanaudière
- Outaouais
- And 10 more regions

**Data Format:**
- HTML tables organized by region
- No JSON API (HTML scraping required)
- Includes trend charts (visual only)

**Technical Notes:**
- Server-rendered HTML (no JavaScript required)
- Simple BeautifulSoup parsing should work
- French text requires unicode handling

---

### 2. MSSS Official Data (Government Source)

**URL:** https://msss.gouv.qc.ca/professionnels/statistiques/documents/urgences/Rap_horaire_SituatUrgence1.pdf

**Overview:**
- Official Ministry of Health data
- PDF format (harder to parse)
- Updated hourly
- Same data that Index Santé aggregates

**Metrics:**
- Patients on stretcher per hour
- Patients >24h on stretcher
- Patients >48h on stretcher

**Limitations:**
- PDF format requires special parsing
- Less convenient than Index Santé HTML

---

### 3. CHU de Québec Real-Time

**URL:** https://statistiques.chudequebec.ca/

**Overview:**
- Hospital-specific portal for CHU de Québec facilities
- Real-time ambulatory and stretcher data

---

### 4. Quebec Government Portal

**URL:** https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec

**Overview:**
- Government information page
- Links to data sources
- Not for scraping

---

## Recommended Approach

### For MVP: Use Index Santé

1. **Fetch URL:** `https://www.indexsante.ca/urgences/`
2. **Parse Method:** BeautifulSoup (server-rendered HTML)
3. **Frequency:** Hourly (matches their update cycle)

### Regional URLs

Index Santé has region-specific pages for targeted scraping:

| Region | URL |
|--------|-----|
| Montréal | https://www.indexsante.ca/urgences/montreal.php |
| Capitale-Nationale | https://www.indexsante.ca/urgences/capitale-nationale.php |
| Laval | https://www.indexsante.ca/urgences/laval.php |
| Montérégie | https://www.indexsante.ca/urgences/monteregie.php |

### Scraper Configuration

```python
# backend/src/waittime/scrapers/quebec.py

SOURCE_CONFIG = {
    "id": "qc-indexsante",
    "name": "Index Santé Quebec",
    "url": "https://www.indexsante.ca/urgences/",
    "province": "Quebec",
    "methodology_url": "https://msss.gouv.qc.ca/professionnels/statistiques-donnees-services-sante-services-sociaux/donnees-urgences/",
    "update_frequency_minutes": 60,
}

# Ontology mapping
ONTOLOGY = {
    "metric_family": "TIME_TO_PROVIDER",  # Estimated wait time
    "start_event": "REGISTRATION",  # Quebec counts from registration
    "end_event": "PROVIDER",  # First provider contact
    "statistic_type": "ROLLING_AVG",  # Averaged estimate
    "patient_scope": "ALL",
}
```

### Data Extraction Strategy

```python
# Pseudocode for Index Santé extraction

def parse_quebec_page(html: str) -> list[dict]:
    soup = BeautifulSoup(html, 'html.parser')
    hospitals = []

    # Find all hospital rows in tables
    for region_section in soup.select('.region-urgences'):
        region_name = region_section.select_one('h2').text.strip()

        for row in region_section.select('table tbody tr'):
            cells = row.select('td')
            if len(cells) >= 7:
                hospitals.append({
                    'name': cells[0].text.strip(),
                    'region': region_name,
                    'total_persons': parse_int(cells[1].text),
                    'awaiting_physician': parse_int(cells[2].text),
                    'functional_stretchers': parse_int(cells[3].text),
                    'occupied_stretchers': parse_int(cells[4].text),
                    'occupancy_rate': parse_percent(cells[5].text),
                    'over_24h': parse_int(cells[6].text),
                    'over_48h': parse_int(cells[7].text) if len(cells) > 7 else 0,
                })

    return hospitals
```

---

## Ontology Mapping

| Index Santé Field | Our Ontology | Notes |
|-------------------|--------------|-------|
| `en attente de prise en charge` | `value` | Primary wait metric |
| Hourly estimate | `statistic_type: ROLLING_AVG` | Not real-time |
| Registration-based | `start_event: REGISTRATION` | Quebec starts from registration |

**Important Methodology Differences from Ontario:**

| Aspect | Quebec | Ontario |
|--------|--------|---------|
| Start Event | Registration | Triage |
| Update Frequency | Hourly | Every 15 min |
| Statistic Type | Rolling Average | Point Estimate |
| Primary Metric | Stretcher occupancy | Wait time to MD |

These differences mean **Quebec and Ontario data are NOT directly comparable** and should trigger methodology divergence warnings.

---

## Metric Interpretation

Quebec's primary focus is **stretcher occupancy**, not wait time:

- `Taux d'occupation` (occupancy rate) is the headline metric
- `En attente` (waiting) is secondary
- `+24h` and `+48h` indicate system strain

For our `TIME_TO_PROVIDER` metric family, we should use the `en attente de prise en charge` count and estimate wait time based on historical patterns.

---

## Next Steps

1. [ ] Verify current Quebec scraper URL is correct
2. [ ] Update parsing to match current Index Santé HTML structure
3. [ ] Map hospital names to our standardized IDs (unicode handling)
4. [ ] Update source record with correct ontology values
5. [ ] Test with real data

---

*Research conducted: February 2026*
