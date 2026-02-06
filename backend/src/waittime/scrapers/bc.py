"""BC PHSA wait time scraper.

Source: Provincial Health Services Authority
URL: https://edwaittimes.ca/legacy

Methodology (per bc-methodology.md):
- metric_family: TIME_TO_PROVIDER
- start_event: TRIAGE (after triage nurse assessment)
- end_event: PHYSICIAN (seeing doctor or nurse practitioner)
- statistic_type: P90 (90th percentile - "9 out of 10 patients seen within this time")
- patient_scope: ALL
- update_frequency: Every 5 minutes

Note: BC also provides ELOS (Estimated Length of Stay) which uses:
- start_event: DOOR, end_event: DISCHARGE, statistic: P75
We store only the TIME_TO_PROVIDER metric for comparability with other provinces.
"""

import json
import logging
import re

import requests
from bs4 import BeautifulSoup

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


class BCScraper(BaseScraper):
    """Scraper for BC PHSA emergency wait times.

    Extracts data from __NEXT_DATA__ JSON embedded in the legacy page.
    """

    BASE_URL = "https://edwaittimes.ca/legacy"

    # Hospital ID mapping: BC name → standardized ID
    # Format: ca-bc-{slug}
    # Based on the official slugs from the BC website
    HOSPITAL_MAPPING: dict[str, str] = {
        # Vancouver Coastal Health
        "St. Paul's Hospital": "ca-bc-st-pauls",
        "Vancouver General Hospital": "ca-bc-vgh",
        "BC Children's Hospital": "ca-bc-bc-childrens",
        "Richmond Hospital": "ca-bc-richmond",
        "Lions Gate Hospital": "ca-bc-lions-gate",
        "Mount Saint Joseph Hospital": "ca-bc-mount-saint-joseph",
        "UBC Hospital": "ca-bc-ubc",
        "Whistler Health Care Centre": "ca-bc-whistler",
        "Pemberton Health Centre": "ca-bc-pemberton",
        # Fraser Health
        "Ridge Meadows Hospital": "ca-bc-ridge-meadows",
        "Burnaby Hospital": "ca-bc-burnaby",
        "Royal Columbian Hospital": "ca-bc-royal-columbian",
        "Eagle Ridge Hospital": "ca-bc-eagle-ridge",
        "Peace Arch Hospital": "ca-bc-peace-arch",
        "Delta Hospital": "ca-bc-delta",
        "Chilliwack General Hospital": "ca-bc-chilliwack",
        "Langley Memorial Hospital": "ca-bc-langley",
        "Abbotsford Regional Hospital": "ca-bc-abbotsford",
        "Surrey Memorial Hospital (Adult Emergency)": "ca-bc-surrey-memorial-adult",
        "Surrey Memorial Hospital (Pediatrics Emergency)": "ca-bc-surrey-memorial-pediatrics",
    }

    def fetch(self, url: str | None = None) -> str:
        """Fetch the legacy page containing __NEXT_DATA__ JSON."""
        target_url = url or self.BASE_URL
        try:
            response = requests.get(
                target_url,
                timeout=30,
                headers={"User-Agent": "WaitTimeCanada/1.0 (Health Data Research)"},
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Failed to fetch BC data: {e}")
            raise

    def parse(self, html: str) -> list[Measurement]:
        """Parse __NEXT_DATA__ JSON to extract wait times.

        Args:
            html: Raw HTML containing __NEXT_DATA__ script tag

        Returns:
            List of Measurement objects
        """
        measurements: list[Measurement] = []

        try:
            soup = BeautifulSoup(html, "html.parser")

            # Find the __NEXT_DATA__ script tag
            next_data_script = soup.find("script", id="__NEXT_DATA__")
            if not next_data_script:
                logger.error("Could not find __NEXT_DATA__ script tag")
                return measurements

            # Parse JSON
            try:
                script_content = next_data_script.string
                if not script_content:
                    logger.error("__NEXT_DATA__ script tag is empty")
                    return measurements
                next_data = json.loads(script_content)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse __NEXT_DATA__ JSON: {e}")
                return measurements

            # Extract locations from pageProps
            try:
                locations = next_data["props"]["pageProps"]["locationsWithWaitTimes"]
            except KeyError as e:
                logger.error(f"Unexpected __NEXT_DATA__ structure: {e}")
                return measurements

            # Process each location
            for location in locations:
                measurement = self._parse_location(location)
                if measurement:
                    measurements.append(measurement)

            logger.info(f"Parsed {len(measurements)} measurements from BC PHSA")

        except Exception as e:
            logger.error(f"Error parsing BC data: {e}", exc_info=True)

        return measurements

    def _parse_location(self, location: dict) -> Measurement | None:
        """Parse a single location entry into a Measurement.

        Args:
            location: Location dict from __NEXT_DATA__ JSON

        Returns:
            Measurement object or None if invalid
        """
        try:
            # Extract basic info
            name = location.get("name", "").strip()
            location_type = location.get("type", "")

            # Only process emergency departments
            if location_type != "ed":
                logger.debug(f"Skipping non-ED location: {name} (type={location_type})")
                return None

            # Get wait time data
            wait_time_data = location.get("waitTime")
            if not wait_time_data:
                logger.debug(f"No wait time data for {name}")
                return None

            wait_time_minutes = wait_time_data.get("waitTimeMinutes")
            if wait_time_minutes is None:
                logger.debug(f"No waitTimeMinutes for {name}")
                return None

            # Map to standardized hospital ID
            hospital_id = self.HOSPITAL_MAPPING.get(name)
            if not hospital_id:
                # Auto-generate ID from name for new hospitals
                slug = self._generate_slug(name)
                hospital_id = f"ca-bc-{slug}"
                logger.warning(
                    f"Hospital '{name}' not in mapping, using auto-generated ID: {hospital_id}"
                )

            # Create measurement
            location_json = json.dumps(location)
            measurement = Measurement(
                hospital_id=hospital_id,
                source_id=self.source.id,
                value=float(wait_time_minutes),
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.TRIAGE,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.P90,
                raw_payload_hash=self.hash_payload(location_json),
                raw_payload_snippet=location_json[:200],
                parser_version="v1.0",
            )

            return measurement

        except Exception as e:
            logger.error(f"Error parsing location {location.get('name', 'UNKNOWN')}: {e}")
            return None

    def _generate_slug(self, name: str) -> str:
        """Generate a slug from hospital name.

        Args:
            name: Hospital name

        Returns:
            Slug suitable for hospital ID
        """
        # Remove special characters, convert to lowercase
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        # Replace spaces with hyphens
        slug = re.sub(r"[\s_]+", "-", slug)
        # Remove duplicate hyphens
        slug = re.sub(r"-+", "-", slug)
        # Strip leading/trailing hyphens
        slug = slug.strip("-")
        return slug


def create_bc_source() -> Source:
    """Create BC source configuration."""
    return Source(
        id="bc-phsa",
        name="Provincial Health Services Authority",
        province="BC",
        url="https://edwaittimes.ca",
        methodology_url="https://www.edwaittimes.ca/about",
        telehealth_name="HealthLink BC",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.TRIAGE,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.P90,
    )
