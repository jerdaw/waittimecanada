"""Database service layer for PostgreSQL (Neon).

Handles all database operations including:
- Writing measurements
- Updating scraper heartbeats
- Managing hospital verification status
"""

import logging
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Generator

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from waittime.core import Hospital, Measurement, ScraperStatus, Source

# Load environment variables from .env.local (preferred) or .env
env_file = Path(__file__).parents[3] / ".env.local"
if not env_file.exists():
    env_file = Path(__file__).parents[3] / ".env"
load_dotenv(env_file)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for interacting with PostgreSQL database.

    Uses direct psycopg2 connections for maximum compatibility.
    """

    def __init__(self, database_url: str | None = None) -> None:
        """Initialize database connection.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)

        Raises:
            ValueError: If connection string is not provided
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")

        if not self.database_url:
            raise ValueError(
                "Database URL required. Set DATABASE_URL environment variable "
                "or pass it directly."
            )

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get a database connection context manager."""
        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_cursor(
        self, conn: psycopg2.extensions.connection
    ) -> psycopg2.extras.RealDictCursor:
        """Get a cursor that returns rows as dictionaries."""
        return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # ─────────────────────────────────────────────────────────────────
    # Sources
    # ─────────────────────────────────────────────────────────────────

    def get_source(self, source_id: str) -> Source | None:
        """Get a source by ID."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT * FROM sources WHERE id = %s", (source_id,))
                row = cur.fetchone()
                return self._row_to_source(dict(row)) if row else None

    def list_sources(self) -> list[Source]:
        """List all data sources."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT * FROM sources")
                return [self._row_to_source(dict(row)) for row in cur.fetchall()]

    # ─────────────────────────────────────────────────────────────────
    # Hospitals
    # ─────────────────────────────────────────────────────────────────

    def get_hospital(self, hospital_id: str) -> Hospital | None:
        """Get a hospital by ID."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT * FROM hospitals WHERE id = %s", (hospital_id,))
                row = cur.fetchone()
                return self._row_to_hospital(dict(row)) if row else None

    def upsert_hospital(self, hospital: Hospital) -> Hospital:
        """Insert or update a hospital."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO hospitals (
                        id, name, province, city, latitude, longitude,
                        is_verified, is_visible, source_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        city = EXCLUDED.city,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        hospital.id,
                        hospital.name,
                        hospital.province,
                        hospital.city,
                        hospital.latitude,
                        hospital.longitude,
                        hospital.is_verified,
                        hospital.is_visible,
                        hospital.source_id,
                    ),
                )
                row = cur.fetchone()
                return self._row_to_hospital(dict(row))

    def list_hospitals(
        self, province: str | None = None, visible_only: bool = False
    ) -> list[Hospital]:
        """List hospitals with optional filters."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                query = "SELECT * FROM hospitals WHERE 1=1"
                params: list[Any] = []

                if province:
                    query += " AND province = %s"
                    params.append(province)
                if visible_only:
                    query += " AND is_visible = true AND is_verified = true"

                cur.execute(query, params)
                return [self._row_to_hospital(dict(row)) for row in cur.fetchall()]

    def verify_hospital(self, hospital_id: str, make_visible: bool = True) -> Hospital:
        """Mark a hospital as verified (admin action)."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE hospitals
                    SET is_verified = true, is_visible = %s, updated_at = NOW()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (make_visible, hospital_id),
                )
                row = cur.fetchone()
                return self._row_to_hospital(dict(row))

    # ─────────────────────────────────────────────────────────────────
    # Measurements
    # ─────────────────────────────────────────────────────────────────

    def insert_measurement(self, measurement: Measurement) -> dict[str, Any]:
        """Insert a new measurement."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO measurements (
                        hospital_id, timestamp_utc, value,
                        metric_family, start_event, end_event, statistic_type, patient_scope,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        measurement.hospital_id,
                        measurement.timestamp_utc,
                        measurement.value,
                        measurement.metric_family.value,
                        measurement.start_event.value,
                        measurement.end_event.value,
                        measurement.statistic_type.value,
                        measurement.patient_scope.value,
                        measurement.source_id,
                        measurement.raw_payload_hash,
                        measurement.raw_payload_snippet,
                        measurement.parser_version,
                    ),
                )
                return dict(cur.fetchone())

    def insert_measurements(self, measurements: list[Measurement]) -> int:
        """Insert multiple measurements in batch."""
        if not measurements:
            return 0

        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                data = [
                    (
                        m.hospital_id,
                        m.timestamp_utc,
                        m.value,
                        m.metric_family.value,
                        m.start_event.value,
                        m.end_event.value,
                        m.statistic_type.value,
                        m.patient_scope.value,
                        m.source_id,
                        m.raw_payload_hash,
                        m.raw_payload_snippet,
                        m.parser_version,
                    )
                    for m in measurements
                ]

                psycopg2.extras.execute_batch(
                    cur,
                    """
                    INSERT INTO measurements (
                        hospital_id, timestamp_utc, value,
                        metric_family, start_event, end_event, statistic_type, patient_scope,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    data,
                )
                return len(measurements)

    def get_latest_measurement(self, hospital_id: str) -> Measurement | None:
        """Get the most recent measurement for a hospital."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM measurements
                    WHERE hospital_id = %s
                    ORDER BY timestamp_utc DESC
                    LIMIT 1
                    """,
                    (hospital_id,),
                )
                row = cur.fetchone()
                return self._row_to_measurement(dict(row)) if row else None

    # ─────────────────────────────────────────────────────────────────
    # Scraper Status (Heartbeat)
    # ─────────────────────────────────────────────────────────────────

    def update_heartbeat(
        self,
        source_id: str,
        status: str = "healthy",
        error_message: str | None = None,
        measurements_count: int = 0,
    ) -> ScraperStatus:
        """Update scraper heartbeat status."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO scraper_status (
                        source_id, last_run, status, error_message, measurements_count
                    ) VALUES (%s, NOW(), %s, %s, %s)
                    ON CONFLICT (source_id) DO UPDATE SET
                        last_run = NOW(),
                        status = EXCLUDED.status,
                        error_message = EXCLUDED.error_message,
                        measurements_count = EXCLUDED.measurements_count,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (source_id, status, error_message, measurements_count),
                )
                row = dict(cur.fetchone())
                return ScraperStatus(
                    source_id=row["source_id"],
                    last_run=row["last_run"],
                    status=row["status"],
                    error_message=row.get("error_message"),
                    measurements_count=row["measurements_count"],
                )

    def get_stale_scrapers(self, threshold_minutes: int = 60) -> list[ScraperStatus]:
        """Get scrapers that haven't run recently."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM scraper_status
                    WHERE last_run < NOW() - INTERVAL '%s minutes'
                       OR status = 'error'
                    """,
                    (threshold_minutes,),
                )
                return [
                    ScraperStatus(
                        source_id=row["source_id"],
                        last_run=row["last_run"],
                        status=row["status"],
                        error_message=row.get("error_message"),
                        measurements_count=row["measurements_count"],
                    )
                    for row in cur.fetchall()
                ]

    # ─────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────

    def _row_to_source(self, row: dict[str, Any]) -> Source:
        """Convert database row to Source model."""
        from waittime.core import (
            EndEvent,
            MetricFamily,
            StartEvent,
            StatisticType,
        )

        return Source(
            id=row["id"],
            name=row["name"],
            province=row["province"],
            url=row["url"],
            methodology_url=row.get("methodology_url"),
            telehealth_name=row["telehealth_name"],
            telehealth_number=row["telehealth_number"],
            default_metric_family=MetricFamily(row["default_metric_family"]),
            default_start_event=StartEvent(row["default_start_event"]),
            default_end_event=EndEvent(row["default_end_event"]),
            default_statistic_type=StatisticType(row["default_statistic_type"]),
        )

    def _row_to_hospital(self, row: dict[str, Any]) -> Hospital:
        """Convert database row to Hospital model."""
        return Hospital(
            id=row["id"],
            name=row["name"],
            province=row["province"],
            city=row["city"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            is_verified=row["is_verified"],
            is_visible=row["is_visible"],
            source_id=row["source_id"],
        )

    def _row_to_measurement(self, row: dict[str, Any]) -> Measurement:
        """Convert database row to Measurement model."""
        from waittime.core import (
            EndEvent,
            MetricFamily,
            PatientScope,
            StartEvent,
            StatisticType,
        )

        return Measurement(
            hospital_id=row["hospital_id"],
            value=row["value"],
            timestamp_utc=row["timestamp_utc"],
            metric_family=MetricFamily(row["metric_family"]),
            start_event=StartEvent(row["start_event"]),
            end_event=EndEvent(row["end_event"]),
            statistic_type=StatisticType(row["statistic_type"]),
            patient_scope=PatientScope(row["patient_scope"]),
            source_id=row["source_id"],
            raw_payload_hash=row["raw_payload_hash"],
            raw_payload_snippet=row.get("raw_payload_snippet"),
            parser_version=row["parser_version"],
        )
