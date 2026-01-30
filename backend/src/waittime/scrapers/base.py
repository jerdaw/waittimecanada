"""Base scraper class for provincial data sources.

All provincial scrapers inherit from BaseScraper and implement
the parse() method to extract measurements from their data source.
"""

import hashlib
import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from waittime.core import Measurement, Source

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for provincial wait time scrapers.

    Subclasses must implement:
    - parse(html: str) -> list[Measurement]

    The base class handles:
    - HTTP fetching with retries
    - Payload hashing (for storage safety)
    - Error handling and logging
    """

    def __init__(self, source: Source) -> None:
        """Initialize scraper with source configuration.

        Args:
            source: Provincial data source configuration
        """
        self.source = source
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "User-Agent": "WaitTimeCanada/1.0 (Health Systems Observatory; +https://waittimecanada.ca)",
            },
        )

    def __enter__(self) -> "BaseScraper":
        return self

    def __exit__(self, *args: object) -> None:
        self.client.close()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
    )
    def fetch(self, url: str | None = None) -> str:
        """Fetch HTML content from the data source.

        Args:
            url: Optional override URL, defaults to source.url

        Returns:
            Raw HTML content

        Raises:
            httpx.HTTPError: If fetch fails after retries
        """
        target_url = url or self.source.url
        logger.info(f"Fetching {target_url}")

        response = self.client.get(target_url)
        response.raise_for_status()

        return response.text

    @abstractmethod
    def parse(self, html: str) -> list[Measurement]:
        """Parse HTML content into measurements.

        This method must be implemented by each provincial scraper.

        Args:
            html: Raw HTML from the data source

        Returns:
            List of Measurement objects with correct ontology tagging

        Raises:
            ValueError: If HTML structure is unexpected
        """
        ...

    def hash_payload(self, content: str) -> str:
        """Generate SHA256 hash of payload content.

        IMPORTANT: We hash, not store, raw payloads for storage safety.
        See strategic plan for rationale.

        Args:
            content: Raw HTML or JSON content

        Returns:
            64-character hex string (SHA256)
        """
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def snippet(self, content: str, max_length: int = 200) -> str:
        """Extract snippet for debugging purposes.

        Args:
            content: Raw content
            max_length: Maximum snippet length

        Returns:
            First N characters of content
        """
        return content[:max_length]

    def run(self) -> list[Measurement]:
        """Execute full scrape cycle: fetch → parse → return.

        Returns:
            List of parsed measurements

        Raises:
            Exception: If fetch or parse fails
        """
        logger.info(f"Starting scrape for {self.source.id}")
        start_time = datetime.now(UTC)

        html = self.fetch()
        measurements = self.parse(html)

        elapsed = (datetime.now(UTC) - start_time).total_seconds()
        logger.info(
            f"Completed scrape for {self.source.id}: "
            f"{len(measurements)} measurements in {elapsed:.2f}s"
        )

        return measurements
