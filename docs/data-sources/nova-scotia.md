# Nova Scotia Health Authority

## Source Details
- **Provider:** Nova Scotia Health / YourHealthNS
- **URLs:**
  - `https://yourhealthns.ca/` (Consumer portal)
  - `https://www.nshealth.ca/` (Main health authority)
- **Data available:** Estimated emergency department wait times for selected hospitals
- **Update Frequency:** Hourly

## Methodology
- **Metric classification:** `TIME_TO_PROVIDER`
- **Statistic Type:** `ALGORITHMIC` (Predicted using combination of historical and current data, acuity, and physicians on duty)
- **Patient Scope:** `NON_PRIORITY` (Specifically targeted to CTAS levels 3, 4, 5. CTAS 1 and 2 are seen immediately).

## Scraper Considerations
- Because it's a modern predictor application (YourHealthNS), the data is most likely served via a JSON API to the frontend app/website.
- A Playwright scraper might be required if it's heavily JS-rendered or requires complex interaction, but if the API endpoint can be discovered (e.g., via network panel), a lightweight HTTP/JSON scraper (like the BC scraper) should be used.
