"""Alberta Health Services emergency wait time scraper.

Data Source: https://www.albertahealthservices.ca/waittimes/Page14230.aspx
Methodology: Triage to Physician (estimated, updated every 2 minutes)
Coverage: 6+ cities across Alberta
"""

import logging
import re
import unicodedata

from bs4 import BeautifulSoup, Tag
from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright
from tenacity import retry, stop_after_attempt

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
from waittime.scrapers.observability import (
    HTTP_FETCH_ATTEMPTS,
    PLAYWRIGHT_PAGE_TIMEOUT_MS,
    PLAYWRIGHT_RENDER_WAIT_MS,
    PLAYWRIGHT_SELECTOR_TIMEOUT_MS,
    fetch_retry_wait,
)

logger = logging.getLogger(__name__)


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

    @retry(
        stop=stop_after_attempt(HTTP_FETCH_ATTEMPTS),
        wait=fetch_retry_wait(),
    )
    def fetch(self, url: str | None = None) -> str:
        """
        Fetch wait time data using Playwright.

        Args:
            url: Optional URL override (defaults to self.URL)

        Returns:
            Raw HTML content with rendered wait times

        Note:
            AHS uses JavaScript to dynamically load wait times.
            We need Playwright to wait for the content to render.
        """
        target_url = url or self.source.url
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(target_url, timeout=PLAYWRIGHT_PAGE_TIMEOUT_MS)

                # Wait for wait time content to load
                # The page structure may vary, so we'll wait for common elements
                try:
                    # Wait for AHS wait-time cards to render.
                    page.wait_for_selector(
                        "div.wt-well, div.wt-times",
                        timeout=PLAYWRIGHT_SELECTOR_TIMEOUT_MS,
                    )
                except PlaywrightTimeout:
                    logger.warning("Wait time elements not found, capturing full page")

                # Give extra time for dynamic content
                page.wait_for_timeout(PLAYWRIGHT_RENDER_WAIT_MS)

                html = page.content()
                return html
            finally:
                browser.close()

    def parse(self, html: str) -> list[Measurement]:
        """
        Parse Alberta wait times from rendered HTML.

        Args:
            html: Rendered HTML from Playwright

        Returns:
            List of Measurement objects
        """
        soup = BeautifulSoup(html, "html.parser")
        measurements: list[Measurement] = []
        seen_hospitals: set[str] = set()

        payload_hash = self.hash_payload(html)
        payload_snippet = self.snippet(html)

        for card in soup.select("div.well.wt-well"):
            measurement = self._extract_from_card(card, payload_hash, payload_snippet)
            if not measurement:
                continue

            # Deduplicate in case the page repeats a facility card.
            if measurement.hospital_id in seen_hospitals:
                continue

            seen_hospitals.add(measurement.hospital_id)
            measurements.append(measurement)

        logger.info("Parsed %d Alberta emergency measurements", len(measurements))
        return measurements

    def _extract_from_card(
        self, card: Tag, payload_hash: str, payload_snippet: str
    ) -> Measurement | None:
        """Extract a single emergency wait-time card."""
        category_elem = card.select_one(".hospitalCateg .wt-category")
        category_text = category_elem.get_text(" ", strip=True).lower() if category_elem else ""
        if "emergency" not in category_text:
            return None

        name_elem = card.select_one("p.hospitalName a") or card.select_one("p.hospitalName")
        if not name_elem:
            return None
        hospital_name = name_elem.get_text(" ", strip=True)
        if not hospital_name:
            return None

        wait_text = self._extract_wait_text(card)
        wait_minutes = self._extract_wait_minutes(wait_text)
        if wait_minutes is None:
            # Skip cards like "Wait times unavailable".
            return None

        hospital_id = self._normalize_hospital_id(hospital_name)
        if not hospital_id:
            return None

        return Measurement(
            hospital_id=hospital_id,
            source_id=self.source.id,
            value=float(wait_minutes),
            metric_family=self.METRIC_FAMILY,
            start_event=self.START_EVENT,
            end_event=self.END_EVENT,
            statistic_type=self.STATISTIC_TYPE,
            patient_scope=self.PATIENT_SCOPE,
            raw_payload_hash=payload_hash,
            raw_payload_snippet=payload_snippet,
            parser_version="v1.0",
        )

    def _extract_wait_text(self, card: Tag) -> str:
        """Extract wait-time text from a card.

        Some facilities expose both adult and pediatric emergency wait times.
        We use Adult Emergency to keep a single consistent metric.
        """
        if card.select_one(".dbl-wt"):
            spans = card.select(".dbl-wt span")
            for span in spans:
                text = str(span.get_text(" ", strip=True))
                if "adult emergency" in text.lower():
                    return text
            if spans:
                return str(spans[0].get_text(" ", strip=True))

        wait_span = card.select_one(".wt-times span")
        if wait_span:
            return str(wait_span.get_text(" ", strip=True))

        wait_container = card.select_one(".wt-times")
        if wait_container:
            return str(wait_container.get_text(" ", strip=True))
        return ""

    def _extract_wait_minutes(self, text: str) -> int | None:
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

        if total_minutes > 0:
            return total_minutes

        # Fallback for values that are plain minutes.
        numeric_match = re.search(r"\b(\d+)\b", text)
        if numeric_match:
            return int(numeric_match.group(1))
        return None

    def _normalize_hospital_id(self, hospital_name: str) -> str | None:
        """Convert hospital name to a standardized Alberta hospital ID."""
        normalized = unicodedata.normalize("NFKD", hospital_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
        if not slug:
            return None
        return f"ca-ab-{slug}"

    def _generate_hospital_id(self, hospital_name: str, city: str = "") -> str:
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

        if city:
            city_normalized = re.sub(r"[^\w\s-]", "", city.lower())
            city_normalized = re.sub(r"[\s_]+", "-", city_normalized)
            return f"ca-ab-{city_normalized}-{normalized}"

        return f"ca-ab-{normalized}"


def create_alberta_source() -> Source:
    """Create Alberta source configuration."""
    return Source(
        id="alberta-ahs",
        name="Alberta Health Services",
        province="AB",
        url="https://www.albertahealthservices.ca/waittimes/Page14230.aspx",
        methodology_url="https://www.albertahealthservices.ca/waittimes/Page14230.aspx",
        telehealth_name="Health Link 811",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.TRIAGE,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.POINT_ESTIMATE,
    )
