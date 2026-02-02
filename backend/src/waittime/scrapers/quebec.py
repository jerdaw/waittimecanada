"""Quebec MSSS wait time scraper.

Source: Ministère de la Santé et des Services sociaux
URL: https://www.quebec.ca/sante/systeme-et-services-de-sante/urgences

Methodology (per ADR-0002):
- metric_family: TIME_TO_PROVIDER
- start_event: REGISTRATION (clock starts at administrative check-in)
- end_event: PHYSICIAN
- statistic_type: ROLLING_AVG (moving average, window unspecified)
"""

import logging
import re
from typing import Any

from bs4 import BeautifulSoup, Tag

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

    Quebec's data portal provides wait times for each hospital
    in a structured HTML table or embedded JSON data.
    """

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

    def parse(self, html: str) -> list[Measurement]:
        """Parse Quebec health portal HTML into measurements.

        Args:
            html: Raw HTML from Quebec data portal

        Returns:
            List of Measurement objects tagged with Quebec methodology

        Raises:
            ValueError: If HTML structure is unexpected
        """
        soup = BeautifulSoup(html, "html.parser")
        measurements: list[Measurement] = []

        payload_hash = self.hash_payload(html)
        payload_snippet = self.snippet(html)

        # Try multiple parsing strategies
        # Strategy 1: Look for data table with hospital rows
        measurements.extend(self._parse_table_format(soup, payload_hash, payload_snippet))

        # Strategy 2: Look for embedded JSON data
        if not measurements:
            measurements.extend(self._parse_json_format(soup, payload_hash, payload_snippet))

        # Strategy 3: Look for card/list format
        if not measurements:
            measurements.extend(self._parse_card_format(soup, payload_hash, payload_snippet))

        if not measurements:
            logger.warning(
                f"No measurements found for {self.source.id}. HTML structure may have changed."
            )

        return measurements

    def _parse_table_format(
        self, soup: BeautifulSoup, payload_hash: str, payload_snippet: str
    ) -> list[Measurement]:
        """Parse table-based HTML format."""
        measurements: list[Measurement] = []

        # Look for tables with wait time data
        tables = soup.find_all("table")
        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    measurement = self._extract_from_row(cells, payload_hash, payload_snippet)
                    if measurement:
                        measurements.append(measurement)

        return measurements

    def _parse_json_format(
        self, soup: BeautifulSoup, payload_hash: str, payload_snippet: str
    ) -> list[Measurement]:
        """Parse embedded JSON data format."""
        measurements: list[Measurement] = []

        # Look for script tags with JSON data
        scripts = soup.find_all("script", {"type": "application/json"})
        for script in scripts:
            if script.string:
                try:
                    import json

                    data = json.loads(script.string)
                    measurements.extend(
                        self._extract_from_json(data, payload_hash, payload_snippet)
                    )
                except json.JSONDecodeError:
                    continue

        return measurements

    def _parse_card_format(
        self, soup: BeautifulSoup, payload_hash: str, payload_snippet: str
    ) -> list[Measurement]:
        """Parse card/list based HTML format."""
        measurements: list[Measurement] = []

        # Look for common card patterns
        cards = soup.find_all(class_=re.compile(r"card|hospital|urgence|wait", re.I))
        for card in cards:
            measurement = self._extract_from_card(card, payload_hash, payload_snippet)
            if measurement:
                measurements.append(measurement)

        return measurements

    def _extract_from_row(
        self, cells: list[Tag], payload_hash: str, payload_snippet: str
    ) -> Measurement | None:
        """Extract measurement from table row cells."""
        if len(cells) < 2:
            return None

        # First cell typically contains hospital name
        hospital_name = cells[0].get_text(strip=True)

        # Find wait time value (look for numbers followed by optional units)
        for cell in cells[1:]:
            text = cell.get_text(strip=True)
            wait_time = self._extract_wait_time(text)
            if wait_time is not None:
                hospital_id = self._normalize_hospital_id(hospital_name)
                if hospital_id:
                    return self._create_measurement(
                        hospital_id, wait_time, payload_hash, payload_snippet
                    )

        return None

    def _extract_from_card(
        self, card: Tag, payload_hash: str, payload_snippet: str
    ) -> Measurement | None:
        """Extract measurement from a card element."""
        # Look for hospital name
        name_elem = card.find(class_=re.compile(r"name|title|hospital", re.I))
        if not name_elem:
            name_elem = card.find(["h2", "h3", "h4", "strong"])

        if not name_elem:
            return None

        hospital_name = name_elem.get_text(strip=True)

        # Look for wait time
        time_elem = card.find(class_=re.compile(r"time|wait|attente|duration", re.I))
        if time_elem:
            wait_time = self._extract_wait_time(time_elem.get_text(strip=True))
            if wait_time is not None:
                hospital_id = self._normalize_hospital_id(hospital_name)
                if hospital_id:
                    return self._create_measurement(
                        hospital_id, wait_time, payload_hash, payload_snippet
                    )

        return None

    def _extract_from_json(
        self, data: Any, payload_hash: str, payload_snippet: str
    ) -> list[Measurement]:
        """Extract measurements from JSON data structure."""
        measurements: list[Measurement] = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    measurement = self._extract_from_json_item(item, payload_hash, payload_snippet)
                    if measurement:
                        measurements.append(measurement)
        elif isinstance(data, dict):
            # Check for nested data arrays
            for key in ["hospitals", "data", "results", "urgences", "etablissements"]:
                if key in data and isinstance(data[key], list):
                    measurements.extend(
                        self._extract_from_json(data[key], payload_hash, payload_snippet)
                    )

        return measurements

    def _extract_from_json_item(
        self, item: dict[str, Any], payload_hash: str, payload_snippet: str
    ) -> Measurement | None:
        """Extract measurement from a JSON object."""
        # Common field names for hospital name
        name_fields = ["name", "nom", "hospital", "etablissement", "hospital_name"]
        hospital_name = None
        for field in name_fields:
            if field in item:
                hospital_name = str(item[field])
                break

        # Common field names for wait time
        time_fields = ["wait_time", "temps_attente", "attente", "wait", "time", "minutes"]
        wait_time = None
        for field in time_fields:
            if field in item:
                wait_time = self._extract_wait_time(str(item[field]))
                if wait_time is not None:
                    break

        if hospital_name and wait_time is not None:
            hospital_id = self._normalize_hospital_id(hospital_name)
            if hospital_id:
                return self._create_measurement(
                    hospital_id, wait_time, payload_hash, payload_snippet
                )

        return None

    def _extract_wait_time(self, text: str) -> float | None:
        """Extract numeric wait time from text.

        Handles formats like:
        - "120 min"
        - "2h 30min"
        - "2:30"
        - "150"
        - "2 heures 30 minutes"
        """
        text = text.strip().lower()

        # Pattern: "Xh Ymin" or "X heures Y minutes"
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
            logger.warning(
                f"Unknown hospital '{name}' - generated ID 'ca-qc-{slug}'. "
                "Needs manual verification."
            )
            return f"ca-qc-{slug}"

        return None

    def _create_measurement(
        self, hospital_id: str, value: float, payload_hash: str, payload_snippet: str
    ) -> Measurement:
        """Create a Measurement with Quebec's methodology tags."""
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


def create_quebec_source() -> Source:
    """Create Quebec source configuration."""
    return Source(
        id="quebec-msss",
        name="Ministère de la Santé et des Services sociaux",
        province="QC",
        url="https://www.quebec.ca/sante/systeme-et-services-de-sante/urgences",
        methodology_url=None,
        telehealth_name="Info-Santé 811",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.REGISTRATION,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.ROLLING_AVG,
    )
