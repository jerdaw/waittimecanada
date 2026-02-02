"""Ontario HQOntario wait time scraper.

Source: Health Quality Ontario (HQO)
URL: https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments

Methodology (per ontario-methodology.md):
- metric_family: TIME_TO_PROVIDER
- start_event: TRIAGE (clock starts after triage assessment)
- end_event: PHYSICIAN (first MD assessment, not NP/PA)
- statistic_type: MEAN (monthly average, not P90)
- patient_scope: ALL (all CTAS levels)
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    PatientScope,
    Source,
    StartEvent,
    StatisticType,
)
from waittime.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class OntarioScraper(BaseScraper):
    """Scraper for Ontario HQOntario emergency wait times.

    Uses Playwright to handle JavaScript-rendered content.
    HQOntario displays data in HTML tables that load dynamically.
    """

    # Hospital ID mapping: HQOntario name → standardized ID
    # Format: ca-on-{slug}
    HOSPITAL_MAPPING: dict[str, str] = {
        # Ottawa Hospitals
        "The Ottawa Hospital - Civic Campus": "ca-on-ottawa-civic",
        "The Ottawa Hospital - General Campus": "ca-on-ottawa-general",
        "The Ottawa Hospital - Riverside Campus": "ca-on-ottawa-riverside",
        "Queensway Carleton Hospital": "ca-on-queensway-carleton",
        "Montfort Hospital": "ca-on-montfort",
        "CHEO": "ca-on-cheo",
        "Children's Hospital of Eastern Ontario": "ca-on-cheo",
        # Toronto Hospitals
        "Toronto General Hospital": "ca-on-toronto-general",
        "University Health Network": "ca-on-toronto-general",
        "Mount Sinai Hospital": "ca-on-mount-sinai",
        "Sunnybrook Health Sciences Centre": "ca-on-sunnybrook",
        "St. Michael's Hospital": "ca-on-st-michaels",
        "The Hospital for Sick Children": "ca-on-sickkids",
        "SickKids": "ca-on-sickkids",
        "Toronto Western Hospital": "ca-on-toronto-western",
        "Princess Margaret Cancer Centre": "ca-on-princess-margaret",
        "North York General Hospital": "ca-on-north-york-general",
        "Scarborough Health Network": "ca-on-scarborough",
        # Other Major Ontario Hospitals
        "London Health Sciences Centre": "ca-on-london-health",
        "Hamilton Health Sciences": "ca-on-hamilton-health",
        "Kingston Health Sciences Centre": "ca-on-kingston-health",
        "Grand River Hospital": "ca-on-grand-river",
        "William Osler Health System": "ca-on-william-osler",
    }

    def fetch(self, url: str | None = None) -> str:
        """Fetch HTML using Playwright to handle JavaScript rendering.

        Overrides base class fetch() to use headless browser instead of httpx.

        Args:
            url: Optional override URL, defaults to source.url

        Returns:
            Rendered HTML after JavaScript execution

        Raises:
            PlaywrightTimeout: If page doesn't load within timeout
            Exception: If browser fails to launch
        """
        target_url = url or self.source.url
        logger.info(f"Fetching {target_url} with Playwright")

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()

                # Navigate to page
                page.goto(target_url, timeout=30000)

                # Wait for data table to load
                # HQOntario uses dynamic loading, so we need to wait
                page.wait_for_selector("table", timeout=15000)

                # Give extra time for all rows to render
                page.wait_for_timeout(2000)

                # Get rendered HTML
                html = page.content()

                browser.close()

                return html

        except PlaywrightTimeout as e:
            logger.error(f"Timeout waiting for page to load: {e}")
            raise
        except Exception as e:
            logger.error(f"Playwright fetch failed: {e}")
            raise

    def parse(self, html: str) -> list[Measurement]:
        """Parse HQOntario HTML into measurements.

        Args:
            html: Rendered HTML from HQOntario (after JavaScript execution)

        Returns:
            List of Measurement objects tagged with Ontario methodology

        Raises:
            ValueError: If HTML structure is unexpected
        """
        soup = BeautifulSoup(html, "html.parser")
        measurements: list[Measurement] = []

        payload_hash = self.hash_payload(html)
        payload_snippet = self.snippet(html)

        # Strategy 1: Look for data tables with hospital rows
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows[1:]:  # Skip header row
                cells = row.find_all(["td", "th"])

                if len(cells) >= 2:  # Need at least hospital name + wait time
                    measurement = self._extract_from_row(
                        cells, payload_hash, payload_snippet
                    )
                    if measurement:
                        measurements.append(measurement)

        if not measurements:
            logger.warning(
                f"No measurements found for {self.source.id}. "
                "HTML structure may have changed."
            )

        return measurements

    def _extract_from_row(
        self, cells: list[Any], payload_hash: str, payload_snippet: str
    ) -> Measurement | None:
        """Extract measurement from table row cells.

        Args:
            cells: List of td/th elements from table row
            payload_hash: SHA256 hash of raw HTML
            payload_snippet: First 200 chars for debugging

        Returns:
            Measurement if successfully parsed, None otherwise
        """
        if len(cells) < 2:
            return None

        # First cell: hospital name
        hospital_name = cells[0].get_text(strip=True)

        # Filter out date values (e.g., "202411", "202412")
        # Pattern: 6 digits (YYYYMM format)
        if re.match(r"^\d{6}$", hospital_name):
            return None

        # Second cell: wait time (likely in hours)
        wait_time_text = cells[1].get_text(strip=True)
        wait_time_hours = self._extract_wait_time_hours(wait_time_text)

        if wait_time_hours is None:
            return None

        # Convert hours to minutes
        wait_time_minutes = wait_time_hours * 60

        # Normalize hospital name to ID
        hospital_id = self._normalize_hospital_id(hospital_name)

        if not hospital_id:
            return None

        return self._create_measurement(
            hospital_id, wait_time_minutes, payload_hash, payload_snippet
        )

    def _extract_wait_time_hours(self, text: str) -> float | None:
        """Extract wait time from text in hours.

        HQOntario reports in hours (e.g., "2.5", "0.5", "1.0").

        Args:
            text: Text containing wait time

        Returns:
            Wait time in hours, or None if not parseable
        """
        text = text.strip()

        # Pattern: decimal number (e.g., "2.5", "0.5", "10.0")
        match = re.search(r"(\d+(?:\.\d+)?)", text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None

        return None

    def _normalize_hospital_id(self, name: str) -> str | None:
        """Convert hospital name to standardized ID.

        Args:
            name: Hospital name from HQOntario

        Returns:
            Standardized ID (ca-on-{slug}) or None if not recognized
        """
        # Check exact mapping first
        if name in self.HOSPITAL_MAPPING:
            return self.HOSPITAL_MAPPING[name]

        # Try fuzzy matching
        name_lower = name.lower()
        for known_name, hospital_id in self.HOSPITAL_MAPPING.items():
            if known_name.lower() in name_lower or name_lower in known_name.lower():
                return hospital_id

        # Generate ID from name if not in mapping (will need verification)
        import unicodedata

        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")

        if slug:
            logger.warning(
                f"Unknown hospital '{name}' - generated ID 'ca-on-{slug}'. "
                "Needs manual verification."
            )
            return f"ca-on-{slug}"

        return None

    def _create_measurement(
        self, hospital_id: str, value: float, payload_hash: str, payload_snippet: str
    ) -> Measurement:
        """Create a Measurement with Ontario's methodology tags.

        Args:
            hospital_id: Standardized hospital ID
            value: Wait time in minutes
            payload_hash: SHA256 hash
            payload_snippet: First 200 chars

        Returns:
            Measurement with correct Ontario ontology
        """
        return Measurement(
            hospital_id=hospital_id,
            value=value,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,  # Ontario uses MEAN, not P90
            patient_scope=PatientScope.ALL,
            source_id=self.source.id,
            raw_payload_hash=payload_hash,
            raw_payload_snippet=payload_snippet,
        )


def create_ontario_source() -> Source:
    """Create Ontario source configuration."""
    return Source(
        id="ontario-health",
        name="Health Quality Ontario",
        province="ON",
        url="https://www.hqontario.ca/system-performance/time-spent-in-emergency-departments",
        methodology_url="https://www.hqontario.ca/System-Performance/Emergency-Department-Performance",
        telehealth_name="Health811",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.TRIAGE,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.MEAN,
    )
