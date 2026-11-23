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
from typing import Any

import structlog
from bs4 import BeautifulSoup, Tag
from tenacity import retry, stop_after_attempt

from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    Source,
    StartEvent,
    StatisticType,
)
from waittime.scrapers.base import BaseScraper
from waittime.scrapers.hospital_matching import (
    MatchReport,
    find_colliding_ids,
    match_source_name,
)
from waittime.scrapers.observability import HTTP_FETCH_ATTEMPTS, fetch_retry_wait

logger = logging.getLogger(__name__)

_ALLOWED_CONTENT_TYPES = frozenset({"text/html", "text/plain"})

# One source facility card: (source name, hospital ID, measurements extracted from it).
_FacilityRow = tuple[str, str, list[Measurement]]


def _safe_content_type(value: str | None) -> str:
    """Return an allowlisted media type without logging parameters."""
    if not value:
        return "missing"
    media_type = value.split(";", maxsplit=1)[0].strip().lower()
    if media_type not in _ALLOWED_CONTENT_TYPES:
        return "other"
    return media_type


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
        # Source spelling of an entry above (same facility, without the CHU prefix).
        "Hôpital de l'Enfant-Jésus": "ca-qc-enfant-jesus",
    }

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.match_report = MatchReport()

    def run(
        self,
        save_to_db: bool = True,
        before_save: Callable[[list[Measurement]], None] | None = None,
    ) -> list[Measurement]:
        """Fetch all pages of measurements and execute shared persistence hooks."""
        logger.info(f"Starting scrape for {self.source.id}")
        start_time = datetime.now(UTC)
        failure_recorded = False
        max_pages = 20
        self.match_report.clear()

        try:
            all_rows: list[_FacilityRow] = []

            # We need to iterate through pages.
            # There are typically ~12 pages (116 results, 10 per page).
            # We'll stop when we get no results or hit a safety limit.
            for page in range(1, max_pages + 1):
                logger.info(f"Fetching page {page}...")

                try:
                    html = self._fetch_page(page)
                except Exception as error:
                    self._record_failure(error, "fetch", start_time)
                    failure_recorded = True
                    raise

                # If page is out of range, endpoint returns fragment without hospital rows.
                if not html or "hospital_element" not in html:
                    if page == 1:
                        parse_error = ValueError("No hospital elements found on first Quebec page")
                        self._record_failure(parse_error, "parse", start_time)
                        failure_recorded = True
                        raise parse_error

                    logger.info(f"No results on page {page}, stopping.")
                    break

                try:
                    page_rows = self._parse_rows(html)
                    page_measurements = [m for _, _, ms in page_rows for m in ms]
                except Exception as error:
                    self._record_failure(error, "parse", start_time)
                    failure_recorded = True
                    raise

                if not page_measurements:
                    if page == 1:
                        parse_error = ValueError("No measurements parsed from first Quebec page")
                        self._record_failure(parse_error, "parse", start_time)
                        failure_recorded = True
                        raise parse_error

                    logger.info(f"No measurements on page {page}, stopping.")
                    break

                all_rows.extend(page_rows)

                # Be nice to the server
                time.sleep(1)

            # Collisions are checked across all pages: a hospital ID claimed by
            # more than one source facility is ambiguous and nothing is written.
            measurements = self._drop_colliding_rows(all_rows)

            if not measurements:
                parse_error = ValueError("No measurements collected from Quebec source")
                self._record_failure(parse_error, "parse", start_time)
                failure_recorded = True
                raise parse_error

            if self.db is not None and measurements:
                self._check_anomalies(measurements)

            if save_to_db and self.db is not None and measurements:
                if before_save is not None:
                    try:
                        before_save(measurements)
                    except Exception as error:
                        self._record_failure(error, "before_save", start_time)
                        failure_recorded = True
                        raise

                try:
                    inserted_count = self.db.insert_measurements(measurements)
                except Exception as error:
                    self._record_failure(error, "persist", start_time)
                    failure_recorded = True
                    raise
                inserted_count = self._normalize_inserted_count(inserted_count, len(measurements))
                duplicate_count = len(measurements) - inserted_count
                if duplicate_count > 0:
                    logger.info(
                        "Persisted %s measurements to database (%s exact duplicates skipped)",
                        inserted_count,
                        duplicate_count,
                    )
                else:
                    logger.info("Persisted %s measurements to database", inserted_count)

            run_duration_ms = self._elapsed_ms(start_time)
            if self._heartbeat is not None:
                try:
                    self._heartbeat.record_success(
                        source_id=self.source.id,
                        measurements_count=len(measurements),
                        run_duration_ms=run_duration_ms,
                    )
                except Exception as error:
                    self._record_failure(error, "heartbeat", start_time)
                    failure_recorded = True
                    raise

            elapsed = (datetime.now(UTC) - start_time).total_seconds()
            logger.info(
                f"Completed scrape for {self.source.id}: "
                f"{len(measurements)} measurements in {elapsed:.2f}s"
            )
            return measurements

        except Exception as error:
            if not failure_recorded:
                self._record_failure(error, "orchestration", start_time)
            raise

    @retry(
        stop=stop_after_attempt(HTTP_FETCH_ATTEMPTS),
        wait=fetch_retry_wait(),
    )
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

        response = self.client.get(self.BASE_URL, params=params)
        body = response.text
        structlog.get_logger(__name__).info(
            "Quebec page response metadata",
            page=page_num,
            status=response.status_code,
            content_type=_safe_content_type(response.headers.get("content-type")),
            body_bytes=len(response.content),
            hospital_element_marker_count=body.count("hospital_element"),
        )
        response.raise_for_status()
        return body

    def parse(self, html: str) -> list[Measurement]:
        """Parse Quebec health portal HTML fragments into measurements.

        Args:
            html: Raw HTML fragment containing hospital list

        Returns:
            List of Measurement objects tagged with Quebec methodology
        """
        self.match_report.clear()
        return self._drop_colliding_rows(self._parse_rows(html))

    def _parse_rows(self, html: str) -> list[_FacilityRow]:
        """Parse an HTML fragment into one row per facility card, before collision checks."""
        soup = BeautifulSoup(html, "html.parser")
        rows: list[_FacilityRow] = []

        payload_hash = self.hash_payload(html)
        payload_snippet = self.snippet(html)

        # Container is div.hospital_element
        for facility in soup.find_all("div", class_="hospital_element"):
            row = self._extract_row(facility, payload_hash, payload_snippet)
            if row is not None:
                rows.append(row)

        return rows

    def _drop_colliding_rows(self, rows: list[_FacilityRow]) -> list[Measurement]:
        """Drop every facility whose hospital ID was claimed by more than one facility."""
        claims = [(name, hospital_id) for name, hospital_id, ms in rows if ms]
        collisions = find_colliding_ids(claims)
        for hospital_id, names in collisions.items():
            logger.warning(
                "Skipping %d source facilities that map to the same hospital ID %s: %s",
                len(names),
                hospital_id,
                "; ".join(names),
            )
            for name in names:
                self.match_report.skipped.append((name, f"collision on {hospital_id}"))
        return [m for _, hospital_id, ms in rows if hospital_id not in collisions for m in ms]

    def _extract_from_facility(
        self, facility: Tag, payload_hash: str, payload_snippet: str
    ) -> list[Measurement]:
        """Extract measurements from a facility card (no cross-facility collision check)."""
        row = self._extract_row(facility, payload_hash, payload_snippet)
        return row[2] if row else []

    def _extract_row(
        self, facility: Tag, payload_hash: str, payload_snippet: str
    ) -> _FacilityRow | None:
        """Extract (name, hospital ID, measurements) from a facility card.

        Extracts both wait time and occupancy measurements if available. Returns
        None when the card has no name or cannot be matched to exactly one hospital.
        """
        measurements: list[Measurement] = []

        # 1. Extract Name
        # <div class="font-weight-bold textual-content">Name</div>
        name_div = facility.find("div", class_="font-weight-bold")
        if not name_div:
            return None

        hospital_name = name_div.get_text(strip=True)
        hospital_id = self._normalize_hospital_id(hospital_name)
        if not hospital_id:
            return None

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

        return hospital_name, hospital_id, measurements

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
        """Convert a source facility name to a hospital ID, or None to skip it.

        Only an exact (case/whitespace-insensitive) match to ``HOSPITAL_MAPPING``
        resolves to a mapped ID. Aggregate rows and names that only partially
        overlap a mapped name (for example "Hôpital Notre-Dame-du-Lac" versus
        "Hôpital Notre-Dame") are skipped and logged rather than guessed. Names
        unrelated to every mapped name keep the pre-existing behaviour of a
        generated ``ca-qc-{slug}`` ID.

        Args:
            name: Facility name from the source

        Returns:
            Hospital ID, or None when the facility must be skipped
        """
        outcome = match_source_name(name, self.HOSPITAL_MAPPING)

        if outcome.status == "exact" and outcome.hospital_id is not None:
            self.match_report.mapped.append((name, outcome.hospital_id))
            return outcome.hospital_id

        if outcome.status == "aggregate":
            logger.warning("Skipping aggregate row '%s': not a hospital", name)
            self.match_report.skipped.append((name, "aggregate row"))
            return None

        if outcome.status == "ambiguous":
            logger.warning(
                "Skipping '%s': does not exactly match a known hospital and overlaps %s",
                name,
                ", ".join(outcome.candidates),
            )
            self.match_report.skipped.append(
                (name, "ambiguous; overlaps " + ", ".join(outcome.candidates))
            )
            return None

        # No relationship to any mapped hospital: generate an ID from the name
        # (existing behaviour). Normalize accents: ô→o, é→e, à→a, etc.
        import unicodedata

        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")

        if not slug:
            self.match_report.skipped.append((name, "no usable name"))
            return None

        generated_id = f"ca-qc-{slug}"
        if generated_id in set(self.HOSPITAL_MAPPING.values()):
            logger.warning(
                "Skipping '%s': generated ID %s belongs to a mapped hospital", name, generated_id
            )
            self.match_report.skipped.append((name, f"generated ID {generated_id} is a mapped ID"))
            return None

        self.match_report.generated.append((name, generated_id))
        return generated_id

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
            value = float(match.group(1))
            # Per roadmap: Treat 0% occupancy as a suppressed/non-reporting signal.
            # This prevents 0.0 values from potentially skewing data quality or causing
            # downstream validation issues if constraints are tightened.
            if value == 0.0:
                return None
            return value
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
