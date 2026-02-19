"""Base scraper class for provincial data sources.

All provincial scrapers inherit from BaseScraper and implement
the parse() method to extract measurements from their data source.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx
from tenacity import retry, stop_after_attempt

from waittime.core import Measurement, Source
from waittime.scrapers.observability import (
    DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_HTTP_POOL_TIMEOUT_SECONDS,
    DEFAULT_HTTP_READ_TIMEOUT_SECONDS,
    DEFAULT_HTTP_WRITE_TIMEOUT_SECONDS,
    HTTP_FETCH_ATTEMPTS,
    FailureStage,
    classify_scraper_failure,
    fetch_retry_wait,
)

if TYPE_CHECKING:
    from waittime.services.database import DatabaseService
    from waittime.services.heartbeat import HeartbeatService

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for provincial wait time scrapers.

    Subclasses must implement:
    - parse(html: str) -> list[Measurement]

    The base class handles:
    - HTTP fetching with retries
    - Payload hashing (for storage safety)
    - Error handling and logging
    - Heartbeat recording (when db is provided)
    """

    def __init__(
        self,
        source: Source,
        db: DatabaseService | None = None,
    ) -> None:
        """Initialize scraper with source configuration.

        Args:
            source: Provincial data source configuration
            db: Optional DatabaseService for persistence and heartbeat recording
        """
        self.source = source
        self.db = db
        self._heartbeat: HeartbeatService | None = None

        # Initialize heartbeat service if database is provided
        if db is not None:
            from waittime.services.heartbeat import HeartbeatService

            self._heartbeat = HeartbeatService(db)

        self.client = httpx.Client(
            timeout=httpx.Timeout(
                connect=DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS,
                read=DEFAULT_HTTP_READ_TIMEOUT_SECONDS,
                write=DEFAULT_HTTP_WRITE_TIMEOUT_SECONDS,
                pool=DEFAULT_HTTP_POOL_TIMEOUT_SECONDS,
            ),
            headers={
                "User-Agent": "WaitTimeCanada/1.0 (Health Systems Observatory; +https://wait-time.ca)",
            },
        )

    def __enter__(self) -> BaseScraper:
        return self

    def __exit__(self, *args: object) -> None:
        self.client.close()

    @retry(  # type: ignore[misc]
        stop=stop_after_attempt(HTTP_FETCH_ATTEMPTS),
        wait=fetch_retry_wait(),
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

    def run(
        self,
        save_to_db: bool = True,
        before_save: Callable[[list[Measurement]], None] | None = None,
    ) -> list[Measurement]:
        """Execute full scrape cycle: fetch → parse → save → heartbeat.

        Args:
            save_to_db: If True and db is configured, save measurements to database
            before_save: Optional callback executed before database insert. Useful for
                prerequisites like hospital upserts that must exist before measurements.

        Returns:
            List of parsed measurements

        Raises:
            Exception: If fetch or parse fails (heartbeat records the failure)
        """
        logger.info(f"Starting scrape for {self.source.id}")
        start_time = datetime.now(UTC)
        failure_recorded = False

        try:
            try:
                html = self.fetch()
            except Exception as error:
                self._record_failure(error, "fetch", start_time)
                failure_recorded = True
                raise

            try:
                measurements = self.parse(html)
            except Exception as error:
                self._record_failure(error, "parse", start_time)
                failure_recorded = True
                raise

            # Check for anomalies before saving
            if self.db is not None and measurements:
                self._check_anomalies(measurements)

            # Save measurements to database if configured
            if save_to_db and self.db is not None and measurements:
                if before_save is not None:
                    try:
                        before_save(measurements)
                    except Exception as error:
                        self._record_failure(error, "before_save", start_time)
                        failure_recorded = True
                        raise

                try:
                    self.db.insert_measurements(measurements)
                except Exception as error:
                    self._record_failure(error, "persist", start_time)
                    failure_recorded = True
                    raise

                logger.info(f"Saved {len(measurements)} measurements to database")

            run_duration_ms = self._elapsed_ms(start_time)

            # Record successful heartbeat
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

    def _elapsed_ms(self, start_time: datetime) -> int:
        """Get elapsed runtime in milliseconds."""
        return max(int((datetime.now(UTC) - start_time).total_seconds() * 1000), 0)

    def _record_failure(self, error: Exception, stage: FailureStage, start_time: datetime) -> None:
        """Record a structured failure heartbeat when available."""
        classified = classify_scraper_failure(error, stage)
        run_duration_ms = self._elapsed_ms(start_time)

        if self._heartbeat is not None:
            self._heartbeat.record_failure(
                source_id=self.source.id,
                error_message=classified.message,
                failure_category=classified.category,
                failure_stage=classified.stage,
                run_duration_ms=run_duration_ms,
            )

        logger.error(
            "Scrape failed for %s [%s/%s]: %s",
            self.source.id,
            classified.category,
            classified.stage,
            classified.message,
        )

    def _check_anomalies(self, measurements: list[Measurement]) -> None:
        """Check measurements for anomalies and flag them in-place.

        Anomalies are flagged but never excluded from saving — the flag
        is metadata that enables data quality transparency.
        """
        if self.db is None:
            return

        try:
            from waittime.core import MetricFamily
            from waittime.services.anomaly_detection import AnomalyDetectionService

            anomaly_service = AnomalyDetectionService(self.db)
            candidate_indices = [
                idx
                for idx, measurement in enumerate(measurements)
                if measurement.metric_family == MetricFamily.TIME_TO_PROVIDER
            ]
            if not candidate_indices:
                return

            batch_payload = [
                {
                    "hospital_id": measurements[idx].hospital_id,
                    "value": measurements[idx].value,
                    "timestamp": measurements[idx].timestamp_utc,
                }
                for idx in candidate_indices
            ]
            results = anomaly_service.check_batch(batch_payload)

            for idx, result in zip(candidate_indices, results, strict=False):
                measurement = measurements[idx]
                if result["is_anomaly"]:
                    measurement.is_anomaly = True
                    measurement.anomaly_reason = result["reason"]
                    logger.warning(
                        "Anomaly detected: %s value=%.0f (%s)",
                        measurement.hospital_id,
                        measurement.value,
                        result["reason"],
                    )
        except Exception:
            # Never let anomaly detection break the scraper pipeline
            logger.exception("Anomaly detection failed, continuing without it")
