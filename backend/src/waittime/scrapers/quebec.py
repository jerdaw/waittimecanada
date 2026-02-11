"""Quebec MSSS wait time scraper.

Source: Ministère de la Santé et des Services sociaux
URL: https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec

Methodology (per ADR-0002):
- metric_family: TIME_TO_PROVIDER
- start_event: REGISTRATION (clock starts at administrative check-in)
- end_event: PHYSICIAN
- statistic_type: ROLLING_AVG (moving average, window unspecified)
"""

import logging
import re
import time
from collections.abc import Callable
from datetime import UTC, datetime

import requests  # type: ignore[import-untyped]
from bs4 import BeautifulSoup, Tag  # type: ignore[import-untyped]

from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    Source,
    StartEvent,
    StatisticType,
)
from waittime.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class QuebecScraper(BaseScraper):
    """Scraper for Quebec MSSS emergency wait times.

    Uses the typo3 AJAX endpoint that powers the search interface.
    The endpoint returns HTML fragments for the facility list.
    """

    # Base URL for the AJAX endpoint
    # Parameters needed: id, type, tx_solr[page]
    BASE_URL = (
        "https://www.quebec.ca/en/health/health-system-and-services/"
        "service-organization/quebec-health-system-and-its-services/"
        "situation-in-emergency-rooms-in-quebec"
    )

    # Hospital ID mapping: Quebec name → standardized ID
    # Format: ca-qc-{slug}
    HOSPITAL_MAPPING: dict[str, str] = {
        "CHUM": "ca-qc-chum",
        "Centre hospitalier universitaire de Montréal": "ca-qc-chum",
        "Hôpital général juif": "ca-qc-jewish-general",
        "Jewish General Hospital": "ca-qc-jewish-general",
        "Hôpital Maisonneuve-Rosemont": "ca-qc-maisonneuve-rosemont",
        "Hôpital du Sacré-Coeur": "ca-qc-sacre-coeur",
        "Hôpital Notre-Dame": "ca-qc-notre-dame",
        "Hôpital Saint-Luc": "ca-qc-saint-luc",
        "Hôtel-Dieu de Montréal": "ca-qc-hotel-dieu",
        "CHU de Québec - Hôpital de l'Enfant-Jésus": "ca-qc-enfant-jesus",
        "CHU de Québec - CHUL": "ca-qc-chul",
        "Hôpital de la Cité-de-la-Santé": "ca-qc-cite-sante",
        "Hôpital Charles-Le Moyne": "ca-qc-charles-lemoyne",
        "Hôpital Pierre-Boucher": "ca-qc-pierre-boucher",
        "Hôpital Anna-Laberge": "ca-qc-anna-laberge",
        "Hôpital du Haut-Richelieu": "ca-qc-haut-richelieu",
        "Hôpital Honoré-Mercier": "ca-qc-honore-mercier",
        "Hôpital de Verdun": "ca-qc-verdun",
        "Hôpital LaSalle": "ca-qc-lasalle",
        "Hôpital de Lachine": "ca-qc-lachine",
        "Hôpital Santa Cabrini": "ca-qc-santa-cabrini",
        "Hôpital Jean-Talon": "ca-qc-jean-talon",
        "Hôpital Fleury": "ca-qc-fleury",
    }

    def run(
        self,
        save_to_db: bool = True,
        before_save: Callable[[list[Measurement]], None] | None = None,
    ) -> list[Measurement]:
        """Fetch all pages of measurements and execute shared persistence hooks."""
        logger.info(f"Starting scrape for {self.source.id}")
        start_time = datetime.now(UTC)
        measurements: list[Measurement] = []
        max_pages = 20

        try:
            # We need to iterate through pages.
            # There are typically ~12 pages (116 results, 10 per page).
            # We'll stop when we get no results or hit a safety limit.
            for page in range(1, max_pages + 1):
                try:
                    logger.info(f"Fetching page {page}...")
                    html = self._fetch_page(page)

                    # Check if we got valid content (if page is out of range, it might return empty or error)
                    if not html or "hospital_element" not in html:
                        if page > 1:
                            logger.info(f"No results on page {page}, stopping.")
                            break

                    page_measurements = self.parse(html)
                    if not page_measurements:
                        if page > 1:
                            logger.info(f"No measurements on page {page}, stopping.")
                            break

                    measurements.extend(page_measurements)

                    # Be nice to the server
                    time.sleep(1)

                except Exception as e:
                    logger.error(f"Error fetching page {page}: {e}")
                    # Stop on page-level failure to avoid silently mixing stale/partial pages.
                    break

            if self.db is not None and measurements:
                self._check_anomalies(measurements)

            if save_to_db and self.db is not None and measurements:
                if before_save is not None:
                    before_save(measurements)
                self.db.insert_measurements(measurements)
                logger.info(f"Saved {len(measurements)} measurements to database")

            if self._heartbeat is not None:
                self._heartbeat.record_success(
                    source_id=self.source.id,
                    measurements_count=len(measurements),
                )

            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"Completed scrape for {self.source.id}: "
                f"{len(measurements)} measurements in {elapsed:.2f}s"
            )
            return measurements

        except Exception as e:
            if self._heartbeat is not None:
                self._heartbeat.record_failure(
                    source_id=self.source.id,
                    error_message=str(e),
                )
            logger.error(f"Scrape failed for {self.source.id}: {e}")
            raise

    def _fetch_page(self, page_num: int) -> str:
        """Fetch a single page of results."""
        params = {
            "id": "24981",
            "tx_solr[location]": "",
            "tx_solr[pt]": "",
            "tx_solr[sfield]": "geolocation_location",
            "tx_solr[page]": str(page_num),
            "type": "7382",
        }

        # Use existing session if available (from base class context manager)
        # But BaseScraper doesn't expose the session directly easily if we don't assume requests.
        # We'll just plain requests here for simplicity as we aren't using the BaseScraper.fetch mechanism
        # exactly the same way (due to pagination).
        response = requests.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.text

    def parse(self, html: str) -> list[Measurement]:
        """Parse Quebec health portal HTML fragments into measurements.

        Args:
            html: Raw HTML fragment containing hospital list

        Returns:
            List of Measurement objects tagged with Quebec methodology
        """
        soup = BeautifulSoup(html, "html.parser")
        measurements: list[Measurement] = []

        payload_hash = self.hash_payload(html)
        payload_snippet = self.snippet(html)

        # Container is div.hospital_element
        facilities = soup.find_all("div", class_="hospital_element")

        for facility in facilities:
            facility_measurements = self._extract_from_facility(
                facility, payload_hash, payload_snippet
            )
            measurements.extend(facility_measurements)

        return measurements

    def _extract_from_facility(
        self, facility: Tag, payload_hash: str, payload_snippet: str
    ) -> list[Measurement]:
        """Extract measurements from a facility card.

        Extracts both wait time and occupancy measurements if available.

        Returns:
            List of Measurement objects (may include wait time and/or occupancy)
        """
        measurements: list[Measurement] = []

        # 1. Extract Name
        # <div class="font-weight-bold textual-content">Name</div>
        name_div = facility.find("div", class_="font-weight-bold")
        if not name_div:
            return measurements

        hospital_name = name_div.get_text(strip=True)
        hospital_id = self._normalize_hospital_id(hospital_name)
        if not hospital_id:
            return measurements

        # 2. Extract metrics from list items
        items = facility.find_all("li", class_="hopital-item")
        wait_time_val = None
        occupancy_val = None

        for item in items:
            text = item.get_text(" ", strip=True).lower()

            # Look for wait time keywords (English or French)
            if (
                "waiting time" in text or "temps d'attente" in text or "attente estimé" in text
            ) and ("stretcher" not in text and "civiere" not in text):
                # Found the wait time line
                # Example: "Estimated waiting time for non-priority cases : 4 h 15 min"
                if ":" in text:
                    value_text = text.split(":", 1)[1]
                else:
                    value_text = text
                wait_time_val = self._extract_wait_time(value_text)

            # Look for occupancy keywords (English or French)
            elif (
                "occupancy rate" in text
                or "taux d'occupation" in text
                or ("occupation" in text and ("stretcher" in text or "civiere" in text))
            ):
                # Found occupancy line
                # Example: "Occupancy rate: 110%" or "Taux d'occupation sur civière: 127%"
                occupancy_val = self._extract_occupancy_percentage(text)

        # Create wait time measurement if available
        if wait_time_val is not None:
            measurements.append(
                self._create_measurement(hospital_id, wait_time_val, payload_hash, payload_snippet)
            )

        # Create occupancy measurement if available
        if occupancy_val is not None:
            measurements.append(
                self._create_occupancy_measurement(
                    hospital_id, occupancy_val, payload_hash, payload_snippet
                )
            )

        return measurements

    def _extract_wait_time(self, text: str) -> float | None:
        """Extract numeric wait time from text.

        Handles formats like:
        - "120 min"
        - "2h 30min"
        - "2:30"
        - "4 h 15 min"
        """
        text = text.strip().lower()

        # Pattern: "X h Y min" or "Xh Ymin" with optional spaces
        match = re.search(r"(\d+)\s*h(?:eure)?s?\s*(\d+)?\s*m?i?n?", text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2)) if match.group(2) else 0
            return float(hours * 60 + minutes)

        # Pattern: "X:YY" (time format)
        match = re.search(r"(\d+):(\d{2})", text)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            return float(hours * 60 + minutes)

        # Pattern: "XXX min" or just number
        match = re.search(r"(\d+(?:\.\d+)?)\s*(?:min|minute)?", text)
        if match:
            return float(match.group(1))

        return None

    def _normalize_hospital_id(self, name: str) -> str | None:
        """Convert hospital name to standardized ID.

        Args:
            name: Hospital name from source

        Returns:
            Standardized ID (ca-qc-{slug}) or None if not recognized
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
        # Normalize accents: ô→o, é→e, à→a, etc.
        import unicodedata

        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")

        if slug:
            # We log this but accept it. Data quality monitoring will flag anomalies.
            return f"ca-qc-{slug}"

        return None

    def _extract_occupancy_percentage(self, text: str) -> float | None:
        """Extract occupancy percentage from text.

        Handles formats like:
        - "Occupancy rate: 110%"
        - "Taux d'occupation: 127%"
        - "150%"

        Returns:
            Percentage value (e.g., 110.0 for 110%) or None if not found
        """
        # Look for percentage pattern (number followed by %)
        match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
        if match:
            return float(match.group(1))
        return None

    def _create_measurement(
        self, hospital_id: str, value: float, payload_hash: str, payload_snippet: str
    ) -> Measurement:
        """Create a wait time Measurement with Quebec's methodology tags."""
        return Measurement(
            hospital_id=hospital_id,
            value=value,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.REGISTRATION,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.ROLLING_AVG,
            source_id=self.source.id,
            raw_payload_hash=payload_hash,
            raw_payload_snippet=payload_snippet,
        )

    def _create_occupancy_measurement(
        self, hospital_id: str, occupancy_percentage: float, payload_hash: str, payload_snippet: str
    ) -> Measurement:
        """Create an occupancy Measurement with STRETCHER_OCCUPANCY ontology.

        Args:
            hospital_id: Hospital identifier
            occupancy_percentage: Occupancy rate as percentage (e.g., 110.0 for 110%)
            payload_hash: SHA256 hash of raw HTML
            payload_snippet: First 200 chars of HTML

        Returns:
            Measurement tagged with STRETCHER_OCCUPANCY metric family
        """
        return Measurement(
            hospital_id=hospital_id,
            value=occupancy_percentage,
            metric_family=MetricFamily.STRETCHER_OCCUPANCY,
            start_event=StartEvent.UNKNOWN,  # Occupancy is a point-in-time snapshot
            end_event=EndEvent.PHYSICIAN,  # Use PHYSICIAN as placeholder for consistency
            statistic_type=StatisticType.POINT_ESTIMATE,
            source_id=self.source.id,
            raw_payload_hash=payload_hash,
            raw_payload_snippet=payload_snippet,
        )


def create_quebec_source() -> Source:
    """Create Quebec source configuration."""
    return Source(
        id="quebec-msss",
        name="Ministère de la Santé et des Services sociaux",
        province="QC",
        # New dynamic URL
        url="https://www.quebec.ca/en/health/health-system-and-services/service-organization/quebec-health-system-and-its-services/situation-in-emergency-rooms-in-quebec",
        methodology_url=None,
        telehealth_name="Info-Santé 811",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.REGISTRATION,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.ROLLING_AVG,
    )
