"""Alberta Health Services emergency wait time scraper.

Data Source: https://www.albertahealthservices.ca/waittimes/Page14230.aspx
Methodology: Triage to Physician (estimated, updated every 2 minutes)
Coverage: 6+ cities across Alberta
"""

import re
from datetime import datetime, timezone
from typing import Optional

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    StartEvent,
    StatisticType,
    PatientScope,
)
from waittime.scrapers.base import BaseScraper


class AlbertaScraper(BaseScraper):
    """Scraper for Alberta Health Services ER wait times."""

    SOURCE_ID = "alberta-ahs"
    URL = "https://www.albertahealthservices.ca/waittimes/Page14230.aspx"

    # Ontology for Alberta data
    # Based on AHS methodology: "Triage nurse assessment to physician"
    METRIC_FAMILY = MetricFamily.TIME_TO_PROVIDER
    START_EVENT = StartEvent.TRIAGE
    END_EVENT = EndEvent.PHYSICIAN
    STATISTIC_TYPE = StatisticType.POINT_ESTIMATE  # Updated every 2 minutes
    PATIENT_SCOPE = PatientScope.ALL

    def fetch(self) -> str:
        """
        Fetch wait time data using Playwright.

        Returns:
            Raw HTML content with rendered wait times

        Note:
            AHS uses JavaScript to dynamically load wait times.
            We need Playwright to wait for the content to render.
        """
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(self.URL, timeout=30000)

                # Wait for wait time content to load
                # The page structure may vary, so we'll wait for common elements
                try:
                    # Wait for either a table, list, or specific wait time elements
                    page.wait_for_selector(
                        "table, .wait-time, .facility, [class*='wait']",
                        timeout=15000
                    )
                except PlaywrightTimeout:
                    print("Warning: Wait time elements not found, capturing full page")

                # Give extra time for dynamic content
                page.wait_for_timeout(2000)

                html = page.content()
                return html
            finally:
                browser.close()

    def parse(self, content: str) -> list[Measurement]:
        """
        Parse Alberta wait times from rendered HTML.

        Args:
            content: Rendered HTML from Playwright

        Returns:
            List of Measurement objects

        Note:
            This implementation needs to be updated once we inspect
            the actual page structure. Alberta's format may differ
            from Ontario's table-based layout.
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(content, "html.parser")
        measurements: list[Measurement] = []

        # Save HTML snippet for debugging (first run)
        print("Alberta HTML snippet (first 500 chars):")
        print(content[:500])

        # TODO: Implement parsing logic once we see the actual structure
        # Expected structure to look for:
        # - Hospital/facility names
        # - Wait times in minutes or hours
        # - Possible city/region grouping

        # For now, return empty list and log for manual inspection
        print(f"Alberta scraper needs structure analysis. HTML length: {len(content)}")

        return measurements

    def _extract_wait_minutes(self, text: str) -> Optional[int]:
        """
        Extract wait time in minutes from text.

        Args:
            text: Text containing wait time (e.g., "45 min", "2 hours")

        Returns:
            Wait time in minutes, or None if not found
        """
        text = text.lower().strip()

        # Match patterns like "45 min", "45 minutes", "1 hour 30 min"
        hour_match = re.search(r"(\d+)\s*(?:hour|hr)s?", text)
        min_match = re.search(r"(\d+)\s*(?:minute|min)s?", text)

        hours = int(hour_match.group(1)) if hour_match else 0
        minutes = int(min_match.group(1)) if min_match else 0

        total_minutes = (hours * 60) + minutes

        return total_minutes if total_minutes > 0 else None

    def _generate_hospital_id(self, hospital_name: str, city: str) -> str:
        """
        Generate standardized hospital ID.

        Args:
            hospital_name: Hospital name from source
            city: City name

        Returns:
            Standardized ID like "ca-ab-calgary-rockyview"
        """
        # Normalize name: lowercase, replace spaces/punctuation with hyphens
        normalized = re.sub(r"[^\w\s-]", "", hospital_name.lower())
        normalized = re.sub(r"[\s_]+", "-", normalized)

        # Normalize city
        city_normalized = re.sub(r"[^\w\s-]", "", city.lower())
        city_normalized = re.sub(r"[\s_]+", "-", city_normalized)

        return f"ca-ab-{city_normalized}-{normalized}"
