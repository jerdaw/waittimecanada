"""Ontario Health wait time scraper.

Source: Ontario Health
URL: https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments

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

import httpx
from bs4 import BeautifulSoup
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
from waittime.scrapers.hospital_matching import (
    MatchReport,
    find_colliding_ids,
    match_source_name,
)
from waittime.scrapers.observability import (
    DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_HTTP_POOL_TIMEOUT_SECONDS,
    DEFAULT_HTTP_READ_TIMEOUT_SECONDS,
    DEFAULT_HTTP_WRITE_TIMEOUT_SECONDS,
    HTTP_FETCH_ATTEMPTS,
    fetch_retry_wait,
)

logger = logging.getLogger(__name__)


class OntarioScraper(BaseScraper):
    """Scraper for Ontario Health emergency wait times.

    Fetches the Ontario Health page directly over HTTP and parses the embedded HTML tables.
    """

    # Hospital ID mapping: Ontario Health name → standardized ID
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

    FALLBACK_HTTP_READ_TIMEOUT_SECONDS = 90.0

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.match_report = MatchReport()

    @retry(
        stop=stop_after_attempt(HTTP_FETCH_ATTEMPTS),
        wait=fetch_retry_wait(),
    )
    def fetch(self, url: str | None = None) -> str:
        """Fetch Ontario HTML with a timeout fallback for slow upstream responses.

        Args:
            url: Optional override URL, defaults to source.url

        Returns:
            HTML content for the Ontario page
        """
        target_url = url or self.source.url
        logger.info(f"Fetching {target_url}")

        try:
            return self._fetch_with_read_timeout(
                target_url, read_timeout_seconds=DEFAULT_HTTP_READ_TIMEOUT_SECONDS
            )
        except httpx.ReadTimeout:
            logger.warning(
                "Ontario fetch timed out after %.0fs; retrying with %.0fs read timeout",
                DEFAULT_HTTP_READ_TIMEOUT_SECONDS,
                self.FALLBACK_HTTP_READ_TIMEOUT_SECONDS,
            )
            return self._fetch_with_read_timeout(
                target_url, read_timeout_seconds=self.FALLBACK_HTTP_READ_TIMEOUT_SECONDS
            )

    def _fetch_with_read_timeout(self, target_url: str, read_timeout_seconds: float) -> str:
        """Fetch Ontario HTML with an explicit per-request read timeout."""
        response = self.client.get(
            target_url,
            timeout=httpx.Timeout(
                connect=DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS,
                read=read_timeout_seconds,
                write=DEFAULT_HTTP_WRITE_TIMEOUT_SECONDS,
                pool=DEFAULT_HTTP_POOL_TIMEOUT_SECONDS,
            ),
            follow_redirects=True,
        )
        response.raise_for_status()
        return response.text

    def parse(self, html: str) -> list[Measurement]:
        """Parse Ontario Health HTML into measurements.

        Args:
            html: HTML fetched from Ontario Health over HTTP

        Returns:
            List of Measurement objects tagged with Ontario methodology

        Raises:
            ValueError: If HTML structure is unexpected
        """
        soup = BeautifulSoup(html, "html.parser")
        self.match_report.clear()
        rows_out: list[tuple[str, Measurement]] = []

        payload_hash = self.hash_payload(html)
        payload_snippet = self.snippet(html)

        # Strategy 1: Look for data tables with hospital rows
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            for row in rows[1:]:  # Skip header row
                cells = row.find_all(["td", "th"])

                if len(cells) >= 2:  # Need at least hospital name + wait time
                    measurement = self._extract_from_row(cells, payload_hash, payload_snippet)
                    if measurement:
                        rows_out.append((cells[0].get_text(strip=True), measurement))

        measurements = self._drop_colliding_rows(rows_out)

        if not measurements:
            logger.warning(
                f"No measurements found for {self.source.id}. HTML structure may have changed."
            )

        return measurements

    def _drop_colliding_rows(self, rows: list[tuple[str, Measurement]]) -> list[Measurement]:
        """Drop every row whose hospital ID was claimed by more than one source row.

        A shared ID means the source rows cannot be told apart, so none of them is
        written. The skipped names are logged and recorded on ``match_report``.
        """
        collisions = find_colliding_ids([(name, m.hospital_id) for name, m in rows])
        for hospital_id, names in collisions.items():
            logger.warning(
                "Skipping %d source rows that map to the same hospital ID %s: %s",
                len(names),
                hospital_id,
                "; ".join(names),
            )
            for name in names:
                self.match_report.skipped.append((name, f"collision on {hospital_id}"))
        return [m for _, m in rows if m.hospital_id not in collisions]

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

        Ontario Health reports in hours (e.g., "2.5", "0.5", "1.0").

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
        """Convert a source row name to a hospital ID, or None to skip the row.

        Only an exact (case/whitespace-insensitive) match to ``HOSPITAL_MAPPING``
        resolves to a mapped ID. Aggregate rows (for example the provincial
        average) and names that only partially overlap a mapped name (typically a
        campus of a multi-site corporation) are skipped and logged rather than
        guessed. Names unrelated to every mapped name keep the pre-existing
        behaviour of a generated ``ca-on-{slug}`` ID.

        Args:
            name: Facility name from Ontario Health

        Returns:
            Hospital ID, or None when the row must be skipped
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
        # (existing behaviour; needs verification downstream).
        import unicodedata

        normalized = unicodedata.normalize("NFKD", name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
        slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")

        if not slug:
            self.match_report.skipped.append((name, "no usable name"))
            return None

        generated_id = f"ca-on-{slug}"
        if generated_id in set(self.HOSPITAL_MAPPING.values()):
            logger.warning(
                "Skipping '%s': generated ID %s belongs to a mapped hospital", name, generated_id
            )
            self.match_report.skipped.append((name, f"generated ID {generated_id} is a mapped ID"))
            return None

        logger.warning(
            f"Unknown hospital '{name}' - generated ID '{generated_id}'. Needs manual verification."
        )
        self.match_report.generated.append((name, generated_id))
        return generated_id

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
        url=(
            "https://ontariohealth.ca/system/reporting/performance/"
            "time-spent-in-emergency-departments"
        ),
        methodology_url="https://www.hqontario.ca/System-Performance/Emergency-Department-Performance",
        telehealth_name="Health811",
        telehealth_number="811",
        default_metric_family=MetricFamily.TIME_TO_PROVIDER,
        default_start_event=StartEvent.TRIAGE,
        default_end_event=EndEvent.PHYSICIAN,
        default_statistic_type=StatisticType.MEAN,
    )
