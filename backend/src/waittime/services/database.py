"""Database service layer for PostgreSQL.

Handles all database operations including:
- Writing measurements
- Updating scraper heartbeats
- Managing hospital verification status
"""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg2
import psycopg2.extras
from psycopg2 import sql

from waittime.core import (
    Hospital,
    Measurement,
    MeasurementAggregate,
    PublicDataSource,
    PublicHealthAlert,
    PublicHealthSourceAlertState,
    PublicHealthSystemMetric,
    ResourceLocation,
    ScraperAlertState,
    ScraperStatus,
    Source,
)
from waittime.services.runtime_config import get_heartbeat_stale_threshold_minutes

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PublicHealthSourceStatus:
    """Operational summary for one public-health-hub source."""

    source_id: str
    source_name: str
    domain: str
    recommended_usage_mode: str
    freshness_sensitivity: str
    last_refreshed_at: datetime | None
    resource_record_count: int
    alert_record_count: int
    system_metric_record_count: int
    latest_alert_published_at: datetime | None


class DatabaseService:
    """Service for interacting with PostgreSQL database.

    Uses direct psycopg2 connections for maximum compatibility.
    """

    MEASUREMENT_CONFLICT_COLUMNS = (
        "hospital_id, timestamp_utc, metric_family, start_event, end_event, "
        "statistic_type, patient_scope, source_id, value, raw_payload_hash"
    )

    def __init__(self, database_url: str | None = None, conn: Any = None) -> None:
        """Initialize database connection.

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
            conn: Optional existing connection to reuse
        """
        self.database_url = database_url or os.environ.get("DATABASE_URL")
        self._provided_conn = conn

        if not self.database_url and not self._provided_conn:
            raise ValueError("Database URL or connection required.")

    @contextmanager
    def get_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:
        """Get a database connection context manager."""
        if self._provided_conn:
            yield self._provided_conn
            return

        conn = psycopg2.connect(self.database_url)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def get_cursor(self, conn: psycopg2.extensions.connection) -> psycopg2.extras.RealDictCursor:
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
                if row is None:
                    return None
                return self._row_to_source(dict(row))

    def list_sources(self) -> list[Source]:
        """List all data sources."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT * FROM sources")
                return [self._row_to_source(dict(row)) for row in cur.fetchall()]

    def get_public_data_source(self, source_id: str) -> PublicDataSource | None:
        """Get a public-health-hub source metadata record by ID."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    "SELECT * FROM public_data_sources WHERE source_id = %s",
                    (source_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_public_data_source(dict(row))

    def list_public_data_sources(self, domain: str | None = None) -> list[PublicDataSource]:
        """List public-health-hub sources with an optional domain filter."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                query = "SELECT * FROM public_data_sources"
                params: list[Any] = []

                if domain:
                    query += " WHERE domain = %s"
                    params.append(domain)

                query += " ORDER BY domain, source_name"
                cur.execute(query, params)
                return [self._row_to_public_data_source(dict(row)) for row in cur.fetchall()]

    def list_public_health_source_statuses(self) -> list[PublicHealthSourceStatus]:
        """List operational status summaries for all public-health-hub sources."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        public_data_sources.source_id,
                        public_data_sources.source_name,
                        public_data_sources.domain,
                        public_data_sources.recommended_usage_mode,
                        public_data_sources.freshness_sensitivity,
                        public_data_sources.last_refreshed_at,
                        COALESCE(resource_counts.resource_record_count, 0) AS resource_record_count,
                        COALESCE(alert_counts.alert_record_count, 0) AS alert_record_count,
                        COALESCE(system_metric_counts.system_metric_record_count, 0) AS system_metric_record_count,
                        alert_counts.latest_alert_published_at
                    FROM public_data_sources
                    LEFT JOIN (
                        SELECT
                            source_id,
                            COUNT(*)::integer AS resource_record_count
                        FROM resource_locations
                        GROUP BY source_id
                    ) AS resource_counts
                        ON resource_counts.source_id = public_data_sources.source_id
                    LEFT JOIN (
                        SELECT
                            source_id,
                            COUNT(*)::integer AS alert_record_count,
                            MAX(published_at) AS latest_alert_published_at
                        FROM public_health_alerts
                        GROUP BY source_id
                    ) AS alert_counts
                        ON alert_counts.source_id = public_data_sources.source_id
                    LEFT JOIN (
                        SELECT
                            source_id,
                            COUNT(*)::integer AS system_metric_record_count
                        FROM public_health_system_metrics
                        GROUP BY source_id
                    ) AS system_metric_counts
                        ON system_metric_counts.source_id = public_data_sources.source_id
                    ORDER BY public_data_sources.domain, public_data_sources.source_name
                    """
                )
                return [
                    PublicHealthSourceStatus(
                        source_id=str(row["source_id"]),
                        source_name=str(row["source_name"]),
                        domain=str(row["domain"]),
                        recommended_usage_mode=str(row["recommended_usage_mode"]),
                        freshness_sensitivity=str(row["freshness_sensitivity"]),
                        last_refreshed_at=row["last_refreshed_at"],
                        resource_record_count=int(row["resource_record_count"] or 0),
                        alert_record_count=int(row["alert_record_count"] or 0),
                        system_metric_record_count=int(row["system_metric_record_count"] or 0),
                        latest_alert_published_at=row["latest_alert_published_at"],
                    )
                    for row in cur.fetchall()
                ]

    def upsert_public_data_source(self, source: PublicDataSource) -> PublicDataSource:
        """Insert or update a public-health-hub source metadata record."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO public_data_sources (
                        source_id,
                        domain,
                        source_name,
                        scope,
                        jurisdiction_level,
                        connector_type,
                        access_route,
                        license_reuse_status,
                        attribution_requirement,
                        update_cadence,
                        freshness_sensitivity,
                        operational_risk,
                        recommended_usage_mode,
                        provenance_url,
                        last_verified_at,
                        notes,
                        fallback_source_id,
                        public_methodology_note,
                        last_refreshed_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        domain = EXCLUDED.domain,
                        source_name = EXCLUDED.source_name,
                        scope = EXCLUDED.scope,
                        jurisdiction_level = EXCLUDED.jurisdiction_level,
                        connector_type = EXCLUDED.connector_type,
                        access_route = EXCLUDED.access_route,
                        license_reuse_status = EXCLUDED.license_reuse_status,
                        attribution_requirement = EXCLUDED.attribution_requirement,
                        update_cadence = EXCLUDED.update_cadence,
                        freshness_sensitivity = EXCLUDED.freshness_sensitivity,
                        operational_risk = EXCLUDED.operational_risk,
                        recommended_usage_mode = EXCLUDED.recommended_usage_mode,
                        provenance_url = EXCLUDED.provenance_url,
                        last_verified_at = EXCLUDED.last_verified_at,
                        notes = EXCLUDED.notes,
                        fallback_source_id = EXCLUDED.fallback_source_id,
                        public_methodology_note = EXCLUDED.public_methodology_note,
                        last_refreshed_at = COALESCE(
                            EXCLUDED.last_refreshed_at,
                            public_data_sources.last_refreshed_at
                        ),
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        source.source_id,
                        source.domain,
                        source.source_name,
                        source.scope,
                        source.jurisdiction_level,
                        source.connector_type,
                        source.access_route,
                        source.license_reuse_status,
                        source.attribution_requirement,
                        source.update_cadence,
                        source.freshness_sensitivity,
                        source.operational_risk,
                        source.recommended_usage_mode,
                        source.provenance_url,
                        source.last_verified_at,
                        source.notes,
                        source.fallback_source_id,
                        source.public_methodology_note,
                        source.last_refreshed_at,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to upsert public data source {source.source_id}")
                return self._row_to_public_data_source(dict(row))

    def mark_public_data_source_refreshed(
        self,
        source_id: str,
        refreshed_at: datetime | None = None,
    ) -> PublicDataSource:
        """Update the last successful refresh timestamp for a public data source."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE public_data_sources
                    SET last_refreshed_at = %s,
                        updated_at = NOW()
                    WHERE source_id = %s
                    RETURNING *
                    """,
                    (effective_refreshed_at, source_id),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Public data source {source_id} not found")
                return self._row_to_public_data_source(dict(row))

    def list_resource_locations(
        self,
        kind: str | None = None,
        source_id: str | None = None,
    ) -> list[ResourceLocation]:
        """List normalized resource locations with optional filters."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                query = "SELECT * FROM resource_locations WHERE 1 = 1"
                params: list[Any] = []

                if kind:
                    query += " AND kind = %s"
                    params.append(kind)

                if source_id:
                    query += " AND source_id = %s"
                    params.append(source_id)

                query += " ORDER BY name"
                cur.execute(query, params)
                return [self._row_to_resource_location(dict(row)) for row in cur.fetchall()]

    def replace_resource_locations(
        self,
        source_id: str,
        kind: str,
        locations: list[ResourceLocation],
    ) -> int:
        """Replace resource rows for one source/kind pair with a fresh normalized batch."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    DELETE FROM resource_locations
                    WHERE source_id = %s AND kind = %s
                    """,
                    (source_id, kind),
                )

                if not locations:
                    return 0

                insert_query = """
                    INSERT INTO resource_locations (
                        id,
                        source_id,
                        kind,
                        source_record_id,
                        name,
                        province,
                        city,
                        latitude,
                        longitude,
                        address,
                        postal_code,
                        phone,
                        website_url,
                        reference_status,
                        location_description,
                        access_notes,
                        crowdsourced,
                        completeness_status,
                        provenance_url,
                        last_refreshed_at
                    ) VALUES %s
                """

                rows = [
                    (
                        location.id,
                        location.source_id,
                        location.kind,
                        location.source_record_id,
                        location.name,
                        location.province,
                        location.city,
                        location.latitude,
                        location.longitude,
                        location.address,
                        location.postal_code,
                        location.phone,
                        location.website_url,
                        location.reference_status,
                        location.location_description,
                        location.access_notes,
                        location.crowdsourced,
                        location.completeness_status,
                        location.provenance_url,
                        location.last_refreshed_at,
                    )
                    for location in locations
                ]

                psycopg2.extras.execute_values(cur, insert_query, rows)
                return len(rows)

    def list_public_health_alerts(self, source_id: str | None = None) -> list[PublicHealthAlert]:
        """List normalized public health alerts with an optional source filter."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                query = "SELECT * FROM public_health_alerts"
                params: list[Any] = []

                if source_id:
                    query += " WHERE source_id = %s"
                    params.append(source_id)

                query += " ORDER BY published_at DESC"
                cur.execute(query, params)
                return [self._row_to_public_health_alert(dict(row)) for row in cur.fetchall()]

    def replace_public_health_alerts(
        self,
        source_id: str,
        alerts: list[PublicHealthAlert],
    ) -> int:
        """Replace normalized alert rows for one source with a fresh batch."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    DELETE FROM public_health_alerts
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )

                if not alerts:
                    return 0

                insert_query = """
                    INSERT INTO public_health_alerts (
                        id,
                        source_id,
                        title,
                        summary,
                        alert_type,
                        published_at,
                        source_updated_at,
                        affected_products,
                        provenance_url,
                        last_refreshed_at
                    ) VALUES %s
                """
                rows = [
                    (
                        alert.id,
                        alert.source_id,
                        alert.title,
                        alert.summary,
                        alert.alert_type,
                        alert.published_at,
                        alert.source_updated_at,
                        psycopg2.extras.Json(alert.affected_products),
                        alert.provenance_url,
                        alert.last_refreshed_at,
                    )
                    for alert in alerts
                ]
                psycopg2.extras.execute_values(cur, insert_query, rows)
                return len(rows)

    def list_public_health_system_metrics(
        self,
        source_id: str | None = None,
        series_key: str | None = None,
    ) -> list[PublicHealthSystemMetric]:
        """List normalized system-context metrics with optional filters."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                query = "SELECT * FROM public_health_system_metrics WHERE 1 = 1"
                params: list[Any] = []

                if source_id:
                    query += " AND source_id = %s"
                    params.append(source_id)

                if series_key:
                    query += " AND series_key = %s"
                    params.append(series_key)

                query += (
                    " ORDER BY geography_name, reporting_year DESC, dimension_label NULLS FIRST"
                )
                cur.execute(query, params)
                return [
                    self._row_to_public_health_system_metric(dict(row)) for row in cur.fetchall()
                ]

    def replace_public_health_system_metrics(
        self,
        source_id: str,
        system_metrics: list[PublicHealthSystemMetric],
    ) -> int:
        """Replace normalized system-context metric rows for one source."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    DELETE FROM public_health_system_metrics
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )

                if not system_metrics:
                    return 0

                insert_query = """
                    INSERT INTO public_health_system_metrics (
                        id,
                        source_id,
                        series_key,
                        province,
                        geography_type,
                        geography_name,
                        reporting_year,
                        dimension_label,
                        metrics,
                        provenance_url,
                        last_refreshed_at
                    ) VALUES %s
                """
                rows = [
                    (
                        system_metric.id,
                        system_metric.source_id,
                        system_metric.series_key,
                        system_metric.province,
                        system_metric.geography_type,
                        system_metric.geography_name,
                        system_metric.reporting_year,
                        system_metric.dimension_label,
                        psycopg2.extras.Json(system_metric.metrics),
                        system_metric.provenance_url,
                        system_metric.last_refreshed_at,
                    )
                    for system_metric in system_metrics
                ]
                psycopg2.extras.execute_values(cur, insert_query, rows)
                return len(rows)

    def upsert_source(self, source: Source) -> Source:
        """Insert or update a source."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO sources (
                        id, name, province, url, methodology_url,
                        telehealth_name, telehealth_number,
                        default_metric_family, default_start_event,
                        default_end_event, default_statistic_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        province = EXCLUDED.province,
                        url = EXCLUDED.url,
                        methodology_url = EXCLUDED.methodology_url,
                        telehealth_name = EXCLUDED.telehealth_name,
                        telehealth_number = EXCLUDED.telehealth_number,
                        default_metric_family = EXCLUDED.default_metric_family,
                        default_start_event = EXCLUDED.default_start_event,
                        default_end_event = EXCLUDED.default_end_event,
                        default_statistic_type = EXCLUDED.default_statistic_type,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        source.id,
                        source.name,
                        source.province,
                        source.url,
                        source.methodology_url,
                        source.telehealth_name,
                        source.telehealth_number,
                        source.default_metric_family.value,
                        source.default_start_event.value,
                        source.default_end_event.value,
                        source.default_statistic_type.value,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to upsert source {source.id}")
                return self._row_to_source(dict(row))

    # ─────────────────────────────────────────────────────────────────
    # Hospitals
    # ─────────────────────────────────────────────────────────────────

    def get_hospital(self, hospital_id: str) -> Hospital | None:
        """Get a hospital by ID."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT * FROM hospitals WHERE id = %s", (hospital_id,))
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_hospital(dict(row))

    def upsert_hospital(self, hospital: Hospital) -> Hospital:
        """Insert or update a hospital.

        Note: ON CONFLICT intentionally does NOT update is_verified or
        is_visible.  This prevents scraper re-runs from downgrading a
        hospital that was already approved (either via seed data or a
        previous insert).  Only name, city, and coordinates are refreshed.
        """
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
                if row is None:
                    raise ValueError(f"Failed to upsert hospital {hospital.id}")
                return self._row_to_hospital(dict(row))

    def insert_hospital(self, hospital: Hospital) -> Hospital:
        """Insert a new hospital (raises error if already exists)."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO hospitals (
                        id, name, province, city, latitude, longitude,
                        is_verified, is_visible, source_id
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                if row is None:
                    raise ValueError(f"Failed to insert hospital {hospital.id}")
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

    def get_hospitals_by_source(self, source_id: str) -> list[Hospital]:
        """Get all hospitals for a specific data source."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    "SELECT * FROM hospitals WHERE source_id = %s ORDER BY name",
                    (source_id,),
                )
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
                if row is None:
                    raise ValueError(f"Failed to verify hospital {hospital_id}")
                return self._row_to_hospital(dict(row))

    # ─────────────────────────────────────────────────────────────────
    # Measurements
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _measurement_conflict_key(measurement: Measurement) -> tuple[Any, ...]:
        """Return the exact-observation identity tuple used for idempotent inserts."""
        return (
            measurement.hospital_id,
            measurement.timestamp_utc,
            measurement.metric_family.value,
            measurement.start_event.value,
            measurement.end_event.value,
            measurement.statistic_type.value,
            measurement.patient_scope.value,
            measurement.source_id,
            measurement.value,
            measurement.raw_payload_hash,
        )

    def insert_measurement(self, measurement: Measurement) -> dict[str, Any]:
        """Insert a new measurement.

        Exact duplicate observations are ignored and the existing row is returned.
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO measurements (
                        hospital_id, timestamp_utc, value,
                        metric_family, start_event, end_event, statistic_type, patient_scope,
                        patients_waiting, patients_in_treatment, total_treatment_spaces,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version,
                        is_anomaly, anomaly_reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hospital_id, timestamp_utc, metric_family, start_event, end_event,
                                 statistic_type, patient_scope, source_id, value, raw_payload_hash)
                    DO NOTHING
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
                        measurement.patients_waiting,
                        measurement.patients_in_treatment,
                        measurement.total_treatment_spaces,
                        measurement.source_id,
                        measurement.raw_payload_hash,
                        measurement.raw_payload_snippet,
                        measurement.parser_version,
                        measurement.is_anomaly,
                        measurement.anomaly_reason,
                    ),
                )
                row = cur.fetchone()
                if row is not None:
                    return dict(row)

                cur.execute(
                    """
                    SELECT * FROM measurements
                    WHERE hospital_id = %s
                      AND timestamp_utc = %s
                      AND metric_family = %s
                      AND start_event = %s
                      AND end_event = %s
                      AND statistic_type = %s
                      AND patient_scope = %s
                      AND source_id = %s
                      AND value = %s
                      AND raw_payload_hash = %s
                    ORDER BY id
                    LIMIT 1
                    """,
                    self._measurement_conflict_key(measurement),
                )
                existing_row = cur.fetchone()
                if existing_row is None:
                    raise ValueError("Failed to insert or retrieve measurement")
                return dict(existing_row)

    def insert_measurements(self, measurements: list[Measurement]) -> int:
        """Insert multiple measurements in batch.

        Returns the number of newly inserted rows; exact duplicates are skipped.
        """
        if not measurements:
            return 0

        unique_measurements = list(
            {
                self._measurement_conflict_key(measurement): measurement
                for measurement in measurements
            }.values()
        )

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
                        m.patients_waiting,
                        m.patients_in_treatment,
                        m.total_treatment_spaces,
                        m.source_id,
                        m.raw_payload_hash,
                        m.raw_payload_snippet,
                        m.parser_version,
                        m.is_anomaly,
                        m.anomaly_reason,
                    )
                    for m in unique_measurements
                ]

                inserted = psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO measurements (
                        hospital_id, timestamp_utc, value,
                        metric_family, start_event, end_event, statistic_type, patient_scope,
                        patients_waiting, patients_in_treatment, total_treatment_spaces,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version,
                        is_anomaly, anomaly_reason
                    ) VALUES %s
                    ON CONFLICT (hospital_id, timestamp_utc, metric_family, start_event, end_event,
                                 statistic_type, patient_scope, source_id, value, raw_payload_hash)
                    DO NOTHING
                    RETURNING 1
                    """,
                    data,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    fetch=True,
                )
                return len(inserted)

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
                if row is None:
                    return None
                return self._row_to_measurement(dict(row))

    def cleanup_old_measurements(
        self,
        retention_days: int = 30,
        batch_size: int = 5000,
        max_batches: int | None = None,
    ) -> int:
        """Delete measurements older than retention period in bounded batches.

        IMPORTANT: this is now an explicit purge path, not the default retention
        policy. Callers should use it only when an operator deliberately intends
        to delete historical raw data. Aggregated analytics should be computed
        before deletion.

        Args:
            retention_days: Number of days to retain raw measurements before an explicit purge
            batch_size: Maximum number of rows to delete per transaction
            max_batches: Optional cap on the number of delete batches to execute

        Returns:
            Number of measurements deleted

        Example:
            >>> db = DatabaseService()
            >>> deleted = db.cleanup_old_measurements(retention_days=30)
            >>> logger.info(f"Deleted {deleted} old measurements")
        """
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")
        if max_batches is not None and max_batches <= 0:
            raise ValueError("max_batches must be positive when provided")

        cutoff = datetime.now(UTC) - timedelta(days=retention_days)
        deleted_count = 0
        batches_run = 0

        while max_batches is None or batches_run < max_batches:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cur:
                    cur.execute(
                        """
                        WITH rows_to_delete AS (
                            SELECT id
                            FROM measurements
                            WHERE timestamp_utc < %s
                            LIMIT %s
                        )
                        DELETE FROM measurements m
                        USING rows_to_delete d
                        WHERE m.id = d.id
                        """,
                        (cutoff, batch_size),
                    )
                    batch_deleted = cur.rowcount or 0

            if batch_deleted == 0:
                break

            batches_run += 1
            deleted_count += batch_deleted
            logger.info(
                "Cleanup batch %s deleted %s measurements older than %s days (%s total)",
                batches_run,
                batch_deleted,
                retention_days,
                deleted_count,
            )

            if batch_deleted < batch_size:
                break

        if max_batches is not None and batches_run >= max_batches:
            logger.info(
                "Cleanup stopped after reaching the configured batch cap (%s batches, %s rows)",
                max_batches,
                deleted_count,
            )

        logger.info(
            "Cleaned up %s measurements older than %s days",
            deleted_count,
            retention_days,
        )
        return deleted_count

    def get_measurement_age_stats(self, older_than_days: int = 30) -> dict[str, Any]:
        """Get statistics about measurement ages for monitoring retention policy.

        Returns:
            Dict with oldest/newest age, total rows, and count older than a caller-selected threshold.
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        EXTRACT(EPOCH FROM (NOW() - MIN(timestamp_utc))) / 86400 as oldest_age_days,
                        EXTRACT(EPOCH FROM (NOW() - MAX(timestamp_utc))) / 86400 as newest_age_days,
                        COUNT(*) as total_measurements,
                        COUNT(*) FILTER (
                            WHERE timestamp_utc < NOW() - (%s * INTERVAL '1 day')
                        ) as measurements_older_than_threshold
                    FROM measurements
                    """,
                    (older_than_days,),
                )
                row = cur.fetchone()

                if not row or row["total_measurements"] == 0:
                    return {
                        "oldest_measurement_age_days": None,
                        "newest_measurement_age_days": None,
                        "total_measurements": 0,
                        "older_than_days_threshold": older_than_days,
                        "measurements_older_than_threshold": 0,
                    }

                return {
                    "oldest_measurement_age_days": round(float(row["oldest_age_days"]), 1)
                    if row["oldest_age_days"]
                    else None,
                    "newest_measurement_age_days": round(float(row["newest_age_days"]), 1)
                    if row["newest_age_days"]
                    else None,
                    "total_measurements": row["total_measurements"],
                    "older_than_days_threshold": older_than_days,
                    "measurements_older_than_threshold": row["measurements_older_than_threshold"],
                }

    def get_relation_storage_stats(
        self, relation_name: str = "measurements", exact_count: bool = False
    ) -> dict[str, Any]:
        """Get size and row-count metadata for a table or partitioned relation."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        c.relname AS relation_name,
                        COALESCE(s.n_live_tup, c.reltuples)::bigint AS estimated_row_count,
                        pg_table_size(c.oid) AS table_bytes,
                        pg_indexes_size(c.oid) AS index_bytes,
                        pg_total_relation_size(c.oid) AS total_bytes
                    FROM pg_class c
                    LEFT JOIN pg_stat_user_tables s ON s.relid = c.oid
                    WHERE c.relname = %s
                      AND c.relkind IN ('r', 'p')
                    ORDER BY c.relnamespace = 'public'::regnamespace DESC, c.oid
                    LIMIT 1
                    """,
                    (relation_name,),
                )
                row = cur.fetchone()

                if row is None:
                    raise ValueError(f"Relation not found: {relation_name}")

                exact_row_count = None
                if exact_count:
                    cur.execute(
                        sql.SQL("SELECT COUNT(*) AS exact_row_count FROM {}").format(
                            sql.Identifier(relation_name)
                        )
                    )
                    count_row = cur.fetchone()
                    exact_row_count = int(count_row["exact_row_count"]) if count_row else 0

                table_bytes = int(row["table_bytes"])
                index_bytes = int(row["index_bytes"])
                total_bytes = int(row["total_bytes"])

                return {
                    "relation_name": row["relation_name"],
                    "estimated_row_count": int(row["estimated_row_count"] or 0),
                    "exact_row_count": exact_row_count,
                    "table_bytes": table_bytes,
                    "index_bytes": index_bytes,
                    "total_bytes": total_bytes,
                }

    # ─────────────────────────────────────────────────────────────────
    # Measurement Aggregates
    # ─────────────────────────────────────────────────────────────────

    def get_measurements_in_range(
        self, hospital_id: str, start: datetime, end: datetime
    ) -> list[dict[str, Any]]:
        """Get raw measurement values for a hospital within a time range.

        Args:
            hospital_id: Hospital to query
            start: Range start (inclusive)
            end: Range end (exclusive)

        Returns:
            List of dicts with 'value' and 'timestamp_utc' keys, ordered chronologically
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT value, timestamp_utc, source_id,
                           metric_family, start_event, end_event, statistic_type
                    FROM measurements
                    WHERE hospital_id = %s
                      AND timestamp_utc >= %s
                      AND timestamp_utc < %s
                    ORDER BY timestamp_utc
                    """,
                    (hospital_id, start, end),
                )
                return [dict(row) for row in cur.fetchall()]

    def get_measurement_baseline_stats(
        self, hospital_id: str, start: datetime, end: datetime
    ) -> dict[str, Any] | None:
        """Get summary stats used for anomaly detection without transferring raw rows."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        COUNT(*)::int AS sample_count,
                        AVG(value)::float8 AS mean_value,
                        STDDEV_SAMP(value)::float8 AS std_dev,
                        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY value)::float8 AS q1,
                        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY value)::float8 AS q3
                    FROM measurements
                    WHERE hospital_id = %s
                      AND timestamp_utc >= %s
                      AND timestamp_utc < %s
                      AND metric_family = 'TIME_TO_PROVIDER'
                    """,
                    (hospital_id, start, end),
                )
                row = cur.fetchone()
                if row is None:
                    return None

                sample_count = int(row["sample_count"] or 0)
                if sample_count == 0:
                    return None

                return {
                    "sample_count": sample_count,
                    "mean_value": float(row["mean_value"])
                    if row["mean_value"] is not None
                    else None,
                    "std_dev": float(row["std_dev"]) if row["std_dev"] is not None else None,
                    "q1": float(row["q1"]) if row["q1"] is not None else None,
                    "q3": float(row["q3"]) if row["q3"] is not None else None,
                }

    def get_measurement_baseline_stats_batch(
        self, hospital_windows: list[tuple[str, datetime, datetime]]
    ) -> dict[str, dict[str, Any]]:
        """Get anomaly-detection baseline stats for multiple hospitals in one query."""
        if not hospital_windows:
            return {}

        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                rows = psycopg2.extras.execute_values(
                    cur,
                    """
                    SELECT
                        q.hospital_id,
                        COALESCE(stats.sample_count, 0)::int AS sample_count,
                        stats.mean_value,
                        stats.std_dev,
                        stats.q1,
                        stats.q3
                    FROM (
                        VALUES %s
                    ) AS q(hospital_id, start_time, end_time)
                    LEFT JOIN LATERAL (
                        SELECT
                            COUNT(*)::int AS sample_count,
                            AVG(m.value)::float8 AS mean_value,
                            STDDEV_SAMP(m.value)::float8 AS std_dev,
                            PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY m.value)::float8 AS q1,
                            PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY m.value)::float8 AS q3
                        FROM measurements m
                        WHERE m.hospital_id = q.hospital_id
                          AND m.timestamp_utc >= q.start_time
                          AND m.timestamp_utc < q.end_time
                          AND m.metric_family = 'TIME_TO_PROVIDER'
                    ) AS stats ON TRUE
                    """,
                    hospital_windows,
                    template="(%s, %s, %s)",
                    fetch=True,
                )

                results: dict[str, dict[str, Any]] = {}
                for row in rows:
                    sample_count = int(row["sample_count"] or 0)
                    if sample_count == 0:
                        continue

                    results[row["hospital_id"]] = {
                        "sample_count": sample_count,
                        "mean_value": float(row["mean_value"])
                        if row["mean_value"] is not None
                        else None,
                        "std_dev": float(row["std_dev"]) if row["std_dev"] is not None else None,
                        "q1": float(row["q1"]) if row["q1"] is not None else None,
                        "q3": float(row["q3"]) if row["q3"] is not None else None,
                    }

                return results

    def insert_aggregate(self, aggregate: MeasurementAggregate) -> bool:
        """Insert an aggregate, skipping if a duplicate already exists.

        Uses ON CONFLICT DO NOTHING on the (hospital_id, period_type, period_start, metric_family)
        unique constraint.

        Returns:
            True if inserted, False if it already existed
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO measurement_aggregates (
                        hospital_id, source_id,
                        period_type, period_start, period_end,
                        mean_value, median_value, p90_value,
                        min_value, max_value, std_dev, sample_count,
                        metric_family, start_event, end_event, statistic_type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hospital_id, period_type, period_start, metric_family) DO NOTHING
                    """,
                    (
                        aggregate.hospital_id,
                        aggregate.source_id,
                        aggregate.period_type,
                        aggregate.period_start,
                        aggregate.period_end,
                        aggregate.mean_value,
                        aggregate.median_value,
                        aggregate.p90_value,
                        aggregate.min_value,
                        aggregate.max_value,
                        aggregate.std_dev,
                        aggregate.sample_count,
                        aggregate.metric_family,
                        aggregate.start_event,
                        aggregate.end_event,
                        aggregate.statistic_type,
                    ),
                )
                return cur.rowcount > 0

    def insert_aggregates(self, aggregates: list[MeasurementAggregate]) -> int:
        """Insert multiple aggregates in one batch.

        Returns the number of newly inserted rows.
        """
        if not aggregates:
            return 0

        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                rows = [
                    (
                        aggregate.hospital_id,
                        aggregate.source_id,
                        aggregate.period_type,
                        aggregate.period_start,
                        aggregate.period_end,
                        aggregate.mean_value,
                        aggregate.median_value,
                        aggregate.p90_value,
                        aggregate.min_value,
                        aggregate.max_value,
                        aggregate.std_dev,
                        aggregate.sample_count,
                        aggregate.metric_family,
                        aggregate.start_event,
                        aggregate.end_event,
                        aggregate.statistic_type,
                    )
                    for aggregate in aggregates
                ]

                inserted = psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO measurement_aggregates (
                        hospital_id, source_id,
                        period_type, period_start, period_end,
                        mean_value, median_value, p90_value,
                        min_value, max_value, std_dev, sample_count,
                        metric_family, start_event, end_event, statistic_type
                    ) VALUES %s
                    ON CONFLICT (hospital_id, period_type, period_start, metric_family) DO NOTHING
                    RETURNING 1
                    """,
                    rows,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    fetch=True,
                )
                return len(inserted)

    def get_aggregates(
        self,
        hospital_id: str,
        period_type: str,
        start: datetime,
        end: datetime,
    ) -> list[MeasurementAggregate]:
        """Query stored aggregates for a hospital, period type, and time range.

        Args:
            hospital_id: Hospital to query
            period_type: 'hourly', 'daily', 'weekly', or 'monthly'
            start: Range start (inclusive)
            end: Range end (inclusive)

        Returns:
            List of MeasurementAggregate, ordered by period_start ascending
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM measurement_aggregates
                    WHERE hospital_id = %s
                      AND period_type = %s
                      AND period_start >= %s
                      AND period_start <= %s
                    ORDER BY period_start
                    """,
                    (hospital_id, period_type, start, end),
                )
                return [self._row_to_aggregate(dict(row)) for row in cur.fetchall()]

    def get_existing_aggregate_periods(
        self,
        hospital_id: str,
        period_type: str,
        start: datetime,
        end: datetime,
    ) -> set[datetime]:
        """Return period_start values that already have aggregates.

        Used by backfill to skip already-computed periods efficiently.
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT period_start FROM measurement_aggregates
                    WHERE hospital_id = %s
                      AND period_type = %s
                      AND period_start >= %s
                      AND period_start <= %s
                    """,
                    (hospital_id, period_type, start, end),
                )
                return {row["period_start"] for row in cur.fetchall()}

    def get_all_hospital_ids(self, visible_only: bool = True) -> list[str]:
        """Return all hospital IDs.

        Args:
            visible_only: If True, only return verified and visible hospitals
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                if visible_only:
                    cur.execute(
                        "SELECT id FROM hospitals WHERE is_verified = true AND is_visible = true ORDER BY id"
                    )
                else:
                    cur.execute("SELECT id FROM hospitals ORDER BY id")
                return [row["id"] for row in cur.fetchall()]

    def get_hospital_ids_with_measurements_since(
        self, since: datetime, visible_only: bool = True
    ) -> list[str]:
        """Return hospital IDs that have raw measurements at or after ``since``."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                if visible_only:
                    cur.execute(
                        """
                        SELECT DISTINCT m.hospital_id
                        FROM measurements m
                        JOIN hospitals h ON h.id = m.hospital_id
                        WHERE m.timestamp_utc >= %s
                          AND h.is_verified = true
                          AND h.is_visible = true
                        ORDER BY m.hospital_id
                        """,
                        (since,),
                    )
                else:
                    cur.execute(
                        """
                        SELECT DISTINCT hospital_id
                        FROM measurements
                        WHERE timestamp_utc >= %s
                        ORDER BY hospital_id
                        """,
                        (since,),
                    )
                return [row["hospital_id"] for row in cur.fetchall()]

    def upsert_aggregates(self, aggregates: list[MeasurementAggregate]) -> int:
        """Insert or refresh multiple aggregates in one batch."""
        if not aggregates:
            return 0

        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                rows = [
                    (
                        aggregate.hospital_id,
                        aggregate.source_id,
                        aggregate.period_type,
                        aggregate.period_start,
                        aggregate.period_end,
                        aggregate.mean_value,
                        aggregate.median_value,
                        aggregate.p90_value,
                        aggregate.min_value,
                        aggregate.max_value,
                        aggregate.std_dev,
                        aggregate.sample_count,
                        aggregate.metric_family,
                        aggregate.start_event,
                        aggregate.end_event,
                        aggregate.statistic_type,
                    )
                    for aggregate in aggregates
                ]

                refreshed = psycopg2.extras.execute_values(
                    cur,
                    """
                    INSERT INTO measurement_aggregates (
                        hospital_id, source_id,
                        period_type, period_start, period_end,
                        mean_value, median_value, p90_value,
                        min_value, max_value, std_dev, sample_count,
                        metric_family, start_event, end_event, statistic_type
                    ) VALUES %s
                    ON CONFLICT (hospital_id, period_type, period_start, metric_family)
                    DO UPDATE SET
                        source_id = EXCLUDED.source_id,
                        period_end = EXCLUDED.period_end,
                        mean_value = EXCLUDED.mean_value,
                        median_value = EXCLUDED.median_value,
                        p90_value = EXCLUDED.p90_value,
                        min_value = EXCLUDED.min_value,
                        max_value = EXCLUDED.max_value,
                        std_dev = EXCLUDED.std_dev,
                        sample_count = EXCLUDED.sample_count,
                        start_event = EXCLUDED.start_event,
                        end_event = EXCLUDED.end_event,
                        statistic_type = EXCLUDED.statistic_type
                    RETURNING 1
                    """,
                    rows,
                    template="(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    fetch=True,
                )
                return len(refreshed)

    def _row_to_aggregate(self, row: dict[str, Any]) -> MeasurementAggregate:
        """Convert database row to MeasurementAggregate model."""
        return MeasurementAggregate(
            hospital_id=row["hospital_id"],
            source_id=row["source_id"],
            period_type=row["period_type"],
            period_start=row["period_start"],
            period_end=row["period_end"],
            mean_value=row["mean_value"],
            median_value=row.get("median_value"),
            p90_value=row.get("p90_value"),
            min_value=row["min_value"],
            max_value=row["max_value"],
            std_dev=row.get("std_dev"),
            sample_count=row["sample_count"],
            metric_family=row["metric_family"],
            start_event=row["start_event"],
            end_event=row["end_event"],
            statistic_type=row["statistic_type"],
            created_at=row.get("created_at"),
        )

    # ─────────────────────────────────────────────────────────────────
    # Data Quality
    # ─────────────────────────────────────────────────────────────────

    def get_measurement_timestamps(
        self, hospital_id: str, start: datetime, end: datetime
    ) -> list[datetime]:
        """Get just the timestamps of measurements for gap analysis.

        Args:
            hospital_id: Hospital to query
            start: Range start (inclusive)
            end: Range end (exclusive)

        Returns:
            List of timestamp_utc values ordered chronologically
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT timestamp_utc FROM measurements
                    WHERE hospital_id = %s
                      AND timestamp_utc >= %s
                      AND timestamp_utc < %s
                    ORDER BY timestamp_utc
                    """,
                    (hospital_id, start, end),
                )
                return [row["timestamp_utc"] for row in cur.fetchall()]

    def get_measurement_count_by_hospital(
        self, source_id: str, start: datetime, end: datetime
    ) -> dict[str, int]:
        """Get measurement counts grouped by hospital_id for a source.

        Args:
            source_id: Source to query
            start: Range start (inclusive)
            end: Range end (exclusive)

        Returns:
            Dict mapping hospital_id to measurement count
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT hospital_id, COUNT(*) as cnt
                    FROM measurements
                    WHERE source_id = %s
                      AND timestamp_utc >= %s
                      AND timestamp_utc < %s
                    GROUP BY hospital_id
                    """,
                    (source_id, start, end),
                )
                return {row["hospital_id"]: row["cnt"] for row in cur.fetchall()}

    def get_scrape_window_timestamps(
        self, hospital_id: str, start: datetime, end: datetime
    ) -> list[datetime]:
        """Get distinct UTC hourly scrape windows for a hospital.

        Data-quality logic measures scraper coverage by hourly collection windows,
        not by raw measurement rows. A single scraper pass may emit multiple
        measurement rows for different metric families.
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT DATE_TRUNC('hour', timestamp_utc AT TIME ZONE 'UTC')
                        AS scrape_window_utc
                    FROM measurements
                    WHERE hospital_id = %s
                      AND timestamp_utc >= %s
                      AND timestamp_utc < %s
                    ORDER BY scrape_window_utc
                    """,
                    (hospital_id, start, end),
                )
                return [
                    row["scrape_window_utc"].replace(tzinfo=UTC)
                    if row["scrape_window_utc"].tzinfo is None
                    else row["scrape_window_utc"]
                    for row in cur.fetchall()
                ]

    def get_scrape_window_count_by_hospital(
        self, source_id: str, start: datetime, end: datetime
    ) -> dict[str, int]:
        """Get distinct UTC hourly scrape-window counts grouped by hospital."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        hospital_id,
                        COUNT(DISTINCT DATE_TRUNC('hour', timestamp_utc AT TIME ZONE 'UTC')) AS cnt
                    FROM measurements
                    WHERE source_id = %s
                      AND timestamp_utc >= %s
                      AND timestamp_utc < %s
                    GROUP BY hospital_id
                    """,
                    (source_id, start, end),
                )
                return {row["hospital_id"]: row["cnt"] for row in cur.fetchall()}

    def get_hospital_onboarding_dates(self, source_id: str) -> dict[str, datetime]:
        """Get the earliest measurement timestamp for each hospital in a source.

        Used to determine when a hospital was "onboarded" so that historical
        data quality metrics don't penalize hospitals for not existing yet.

        Args:
            source_id: Source to analyze

        Returns:
            Dict mapping hospital_id to first seen timestamp (UTC)
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT hospital_id, MIN(timestamp_utc) as first_seen
                    FROM measurements
                    WHERE source_id = %s
                    GROUP BY hospital_id
                    """,
                    (source_id,),
                )
                return {row["hospital_id"]: row["first_seen"] for row in cur.fetchall()}

    def insert_quality_snapshot(self, snapshot: dict[str, Any]) -> bool:
        """Insert a data quality snapshot (ON CONFLICT DO NOTHING).

        Args:
            snapshot: Dict with hospital_id, source_id, snapshot_date,
                      expected_scrapes, actual_scrapes, success_rate,
                      longest_gap_minutes, mean_gap_minutes

        Returns:
            True if inserted, False if duplicate
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO data_quality_snapshots (
                        hospital_id, source_id, snapshot_date,
                        expected_scrapes, actual_scrapes, success_rate,
                        longest_gap_minutes, mean_gap_minutes
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (hospital_id, snapshot_date) DO NOTHING
                    """,
                    (
                        snapshot["hospital_id"],
                        snapshot["source_id"],
                        snapshot["snapshot_date"],
                        snapshot["expected_scrapes"],
                        snapshot["actual_scrapes"],
                        snapshot["success_rate"],
                        snapshot.get("longest_gap_minutes"),
                        snapshot.get("mean_gap_minutes"),
                    ),
                )
                return cur.rowcount > 0

    def get_quality_snapshots(
        self, hospital_id: str, start_date: datetime, end_date: datetime
    ) -> list[dict[str, Any]]:
        """Get cached quality snapshots for a hospital and date range.

        Args:
            hospital_id: Hospital to query
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of snapshot dicts ordered by date descending
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT * FROM data_quality_snapshots
                    WHERE hospital_id = %s
                      AND snapshot_date >= %s
                      AND snapshot_date <= %s
                    ORDER BY snapshot_date DESC
                    """,
                    (hospital_id, start_date, end_date),
                )
                return [dict(row) for row in cur.fetchall()]

    # ─────────────────────────────────────────────────────────────────
    # Regions
    # ─────────────────────────────────────────────────────────────────

    def upsert_region(
        self,
        region_id: str,
        province: str,
        name: str,
        code: str,
        sort_order: int = 0,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert or update a region row."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO regions (id, province, name, code, sort_order, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        province = EXCLUDED.province,
                        name = EXCLUDED.name,
                        code = EXCLUDED.code,
                        sort_order = EXCLUDED.sort_order,
                        metadata = EXCLUDED.metadata,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        region_id,
                        province.upper(),
                        name,
                        code.upper(),
                        sort_order,
                        psycopg2.extras.Json(metadata or {}),
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to upsert region {region_id}")
                return dict(row)

    def get_region(self, region_id: str) -> dict[str, Any] | None:
        """Get a region by ID."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT * FROM regions WHERE id = %s", (region_id,))
                row = cur.fetchone()
                return dict(row) if row else None

    def list_regions(self, province: str | None = None) -> list[dict[str, Any]]:
        """List regions, optionally scoped by province."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                if province:
                    cur.execute(
                        """
                        SELECT * FROM regions
                        WHERE province = %s
                        ORDER BY sort_order, name
                        """,
                        (province.upper(),),
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM regions
                        ORDER BY province, sort_order, name
                        """
                    )
                return [dict(row) for row in cur.fetchall()]

    def list_hospital_regions(self, province: str | None = None) -> list[dict[str, Any]]:
        """List hospital-to-region mappings."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                if province:
                    cur.execute(
                        """
                        SELECT
                            hr.region_id,
                            hr.hospital_id,
                            hr.is_primary,
                            hr.assigned_at
                        FROM hospital_regions hr
                        JOIN regions r ON r.id = hr.region_id
                        WHERE r.province = %s
                        ORDER BY r.sort_order, hr.hospital_id
                        """,
                        (province.upper(),),
                    )
                else:
                    cur.execute(
                        """
                        SELECT
                            hr.region_id,
                            hr.hospital_id,
                            hr.is_primary,
                            hr.assigned_at
                        FROM hospital_regions hr
                        JOIN regions r ON r.id = hr.region_id
                        ORDER BY r.province, r.sort_order, hr.hospital_id
                        """
                    )
                return [dict(row) for row in cur.fetchall()]

    def clear_hospital_regions_for_province(self, province: str) -> int:
        """Delete all region mappings for a province."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    DELETE FROM hospital_regions hr
                    USING regions r
                    WHERE hr.region_id = r.id
                      AND r.province = %s
                    """,
                    (province.upper(),),
                )
                return cur.rowcount or 0

    def upsert_hospital_region(
        self, region_id: str, hospital_id: str, is_primary: bool = True
    ) -> dict[str, Any]:
        """Assign a hospital to a region."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO hospital_regions (region_id, hospital_id, is_primary)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (hospital_id) DO UPDATE SET
                        region_id = EXCLUDED.region_id,
                        is_primary = EXCLUDED.is_primary,
                        assigned_at = NOW()
                    RETURNING *
                    """,
                    (region_id, hospital_id, is_primary),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(
                        f"Failed to assign hospital {hospital_id} to region {region_id}"
                    )
                return dict(row)

    def get_region_benchmark_rows(
        self,
        province: str,
        current_start: datetime,
        current_end: datetime,
        previous_start: datetime,
        previous_end: datetime,
    ) -> list[dict[str, Any]]:
        """Return region-level wait stats and trend baselines for a province."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    WITH current_period AS (
                        SELECT
                            ma.hospital_id,
                            AVG(ma.mean_value)::float AS period_mean
                        FROM measurement_aggregates ma
                        WHERE ma.period_type = 'daily'
                          AND ma.period_start >= %s
                          AND ma.period_start < %s
                        GROUP BY ma.hospital_id
                    ),
                    previous_period AS (
                        SELECT
                            ma.hospital_id,
                            AVG(ma.mean_value)::float AS period_mean
                        FROM measurement_aggregates ma
                        WHERE ma.period_type = 'daily'
                          AND ma.period_start >= %s
                          AND ma.period_start < %s
                        GROUP BY ma.hospital_id
                    )
                    SELECT
                        r.id AS region_id,
                        r.name AS region_name,
                        r.code AS region_code,
                        r.sort_order,
                        COUNT(hr.hospital_id)::int AS hospital_count,
                        COUNT(cp.hospital_id)::int AS reporting_count,
                        AVG(cp.period_mean)::float AS period_mean,
                        PERCENTILE_CONT(0.5) WITHIN GROUP
                            (ORDER BY cp.period_mean)::float AS period_median,
                        MIN(cp.period_mean)::float AS best_wait,
                        MAX(cp.period_mean)::float AS worst_wait,
                        AVG(pp.period_mean)::float AS previous_period_mean,
                        ARRAY_AGG(hr.hospital_id ORDER BY hr.hospital_id) AS hospital_ids
                    FROM regions r
                    LEFT JOIN hospital_regions hr ON hr.region_id = r.id
                    LEFT JOIN current_period cp ON cp.hospital_id = hr.hospital_id
                    LEFT JOIN previous_period pp ON pp.hospital_id = hr.hospital_id
                    WHERE r.province = %s
                    GROUP BY r.id, r.name, r.code, r.sort_order
                    ORDER BY r.sort_order, r.name
                    """,
                    (
                        current_start,
                        current_end,
                        previous_start,
                        previous_end,
                        province.upper(),
                    ),
                )
                return [dict(row) for row in cur.fetchall()]

    def get_all_source_ids(self) -> list[str]:
        """Return all source IDs."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute("SELECT id FROM sources ORDER BY id")
                return [row["id"] for row in cur.fetchall()]

    def flag_measurement_anomaly(self, measurement_id: int, reason: str) -> None:
        """Mark a measurement as anomalous in the database.

        Args:
            measurement_id: The measurement's primary key
            reason: Human-readable explanation
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    UPDATE measurements
                    SET is_anomaly = TRUE, anomaly_reason = %s
                    WHERE id = %s
                    """,
                    (reason, measurement_id),
                )

    def get_recent_anomalies(
        self, source_id: str | None = None, days: int = 7
    ) -> list[dict[str, Any]]:
        """Get recent anomalous measurements with hospital info.

        Args:
            source_id: Optional filter by source
            days: Lookback period (default 7)

        Returns:
            List of anomaly dicts with hospital name, value, reason, etc.
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                query = """
                    SELECT m.id, m.hospital_id, m.value, m.timestamp_utc,
                           m.anomaly_reason, m.source_id,
                           h.name as hospital_name, h.province
                    FROM measurements m
                    JOIN hospitals h ON h.id = m.hospital_id
                    WHERE m.is_anomaly = TRUE
                      AND m.timestamp_utc >= NOW() - INTERVAL '%s days'
                """
                params: list[Any] = [days]

                if source_id is not None:
                    query += " AND m.source_id = %s"
                    params.append(source_id)

                query += " ORDER BY m.timestamp_utc DESC"

                cur.execute(query, params)
                return [dict(row) for row in cur.fetchall()]

    # ─────────────────────────────────────────────────────────────────
    # Methodology Change Events
    # ─────────────────────────────────────────────────────────────────

    def insert_methodology_change(self, event: dict[str, Any]) -> int:
        """Insert a methodology change event.

        Args:
            event: Dict with source_id, previous/current period dates,
                   previous/current means, shift_percent, hospitals_analyzed,
                   explanation

        Returns:
            The ID of the inserted row
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO methodology_change_events (
                        source_id,
                        previous_period_start, previous_period_end,
                        current_period_start, current_period_end,
                        previous_mean, current_mean,
                        shift_percent, hospitals_analyzed, explanation
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        event["source_id"],
                        event["previous_period_start"],
                        event["previous_period_end"],
                        event["current_period_start"],
                        event["current_period_end"],
                        event["previous_mean"],
                        event["current_mean"],
                        event["shift_percent"],
                        event["hospitals_analyzed"],
                        event["explanation"],
                    ),
                )
                row = cur.fetchone()
                if not row:
                    return 0
                event_id = row.get("id")
                return int(event_id) if event_id is not None else 0

    def get_methodology_changes(
        self, source_id: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent methodology change events.

        Args:
            source_id: Optional filter by source
            limit: Max results

        Returns:
            List of event dicts ordered by detected_at descending
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                if source_id:
                    cur.execute(
                        """
                        SELECT * FROM methodology_change_events
                        WHERE source_id = %s
                        ORDER BY detected_at DESC
                        LIMIT %s
                        """,
                        (source_id, limit),
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM methodology_change_events
                        ORDER BY detected_at DESC
                        LIMIT %s
                        """,
                        (limit,),
                    )
                return [dict(row) for row in cur.fetchall()]

    # ─────────────────────────────────────────────────────────────────
    # Scraper Status (Heartbeat)
    # ─────────────────────────────────────────────────────────────────

    def update_heartbeat(
        self,
        source_id: str,
        status: str = "healthy",
        error_message: str | None = None,
        measurements_count: int = 0,
        failure_category: str | None = None,
        failure_stage: str | None = None,
        run_duration_ms: int | None = None,
    ) -> ScraperStatus:
        """Update scraper heartbeat status."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO scraper_status (
                        source_id,
                        last_run,
                        status,
                        error_message,
                        measurements_count,
                        last_success_run,
                        last_success_measurements_count,
                        last_error_run,
                        last_error_category,
                        last_error_stage,
                        consecutive_failures,
                        last_run_duration_ms
                    ) VALUES (
                        %s,
                        NOW(),
                        %s,
                        %s,
                        %s,
                        CASE WHEN %s = 'healthy' THEN NOW() ELSE NULL END,
                        CASE WHEN %s = 'healthy' THEN %s ELSE NULL END,
                        CASE WHEN %s = 'error' THEN NOW() ELSE NULL END,
                        CASE WHEN %s = 'error' THEN %s ELSE NULL END,
                        CASE WHEN %s = 'error' THEN %s ELSE NULL END,
                        CASE WHEN %s = 'error' THEN 1 ELSE 0 END,
                        %s
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        last_run = NOW(),
                        status = EXCLUDED.status,
                        error_message = EXCLUDED.error_message,
                        measurements_count = EXCLUDED.measurements_count,
                        last_success_run = CASE
                            WHEN EXCLUDED.status = 'healthy' THEN NOW()
                            ELSE scraper_status.last_success_run
                        END,
                        last_success_measurements_count = CASE
                            WHEN EXCLUDED.status = 'healthy' THEN EXCLUDED.measurements_count
                            ELSE scraper_status.last_success_measurements_count
                        END,
                        last_error_run = CASE
                            WHEN EXCLUDED.status = 'error' THEN NOW()
                            ELSE scraper_status.last_error_run
                        END,
                        last_error_category = CASE
                            WHEN EXCLUDED.status = 'error' THEN EXCLUDED.last_error_category
                            ELSE scraper_status.last_error_category
                        END,
                        last_error_stage = CASE
                            WHEN EXCLUDED.status = 'error' THEN EXCLUDED.last_error_stage
                            ELSE scraper_status.last_error_stage
                        END,
                        consecutive_failures = CASE
                            WHEN EXCLUDED.status = 'error' THEN scraper_status.consecutive_failures + 1
                            ELSE 0
                        END,
                        last_run_duration_ms = EXCLUDED.last_run_duration_ms,
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (
                        source_id,
                        status,
                        error_message,
                        measurements_count,
                        status,
                        status,
                        measurements_count,
                        status,
                        status,
                        failure_category,
                        status,
                        failure_stage,
                        status,
                        run_duration_ms,
                    ),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to update heartbeat for {source_id}")
                row_dict = dict(row)
                return ScraperStatus(
                    source_id=row_dict["source_id"],
                    last_run=row_dict["last_run"],
                    status=row_dict["status"],
                    error_message=row_dict.get("error_message"),
                    measurements_count=row_dict["measurements_count"],
                    last_success_run=row_dict.get("last_success_run"),
                    last_success_measurements_count=row_dict.get("last_success_measurements_count"),
                    last_error_run=row_dict.get("last_error_run"),
                    last_error_category=row_dict.get("last_error_category"),
                    last_error_stage=row_dict.get("last_error_stage"),
                    consecutive_failures=row_dict.get("consecutive_failures") or 0,
                    last_run_duration_ms=row_dict.get("last_run_duration_ms"),
                )

    def get_stale_scrapers(self, threshold_minutes: int | None = None) -> list[ScraperStatus]:
        """Get scrapers that haven't run recently."""
        if threshold_minutes is None:
            threshold_minutes = get_heartbeat_stale_threshold_minutes()
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
                        last_success_run=row.get("last_success_run"),
                        last_success_measurements_count=row.get("last_success_measurements_count"),
                        last_error_run=row.get("last_error_run"),
                        last_error_category=row.get("last_error_category"),
                        last_error_stage=row.get("last_error_stage"),
                        consecutive_failures=row.get("consecutive_failures") or 0,
                        last_run_duration_ms=row.get("last_run_duration_ms"),
                    )
                    for row in cur.fetchall()
                ]

    def get_scraper_alert_state(self, source_id: str) -> ScraperAlertState | None:
        """Get the current persisted alert state for a scraper source."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM scraper_alert_state
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_scraper_alert_state(dict(row))

    def open_scraper_alert_incident(
        self,
        source_id: str,
        incident_kind: str,
        incident_fingerprint: str,
    ) -> ScraperAlertState:
        """Persist a newly opened active alert incident."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO scraper_alert_state (
                        source_id,
                        active_incident_kind,
                        active_incident_fingerprint,
                        opened_at,
                        last_notified_at
                    ) VALUES (
                        %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        active_incident_kind = EXCLUDED.active_incident_kind,
                        active_incident_fingerprint = EXCLUDED.active_incident_fingerprint,
                        opened_at = NOW(),
                        last_notified_at = NOW(),
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (source_id, incident_kind, incident_fingerprint),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to open alert incident for {source_id}")
                return self._row_to_scraper_alert_state(dict(row))

    def resolve_scraper_alert_incident(self, source_id: str) -> ScraperAlertState:
        """Clear the active incident and record the latest resolution time."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO scraper_alert_state (
                        source_id,
                        active_incident_kind,
                        active_incident_fingerprint,
                        last_resolved_at
                    ) VALUES (
                        %s, NULL, NULL, NOW()
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        active_incident_kind = NULL,
                        active_incident_fingerprint = NULL,
                        opened_at = NULL,
                        last_notified_at = NULL,
                        last_resolved_at = NOW(),
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (source_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to resolve alert incident for {source_id}")
                return self._row_to_scraper_alert_state(dict(row))

    def get_public_health_source_alert_state(
        self,
        source_id: str,
    ) -> PublicHealthSourceAlertState | None:
        """Get the current persisted alert state for a public-health source."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM public_health_source_alert_state
                    WHERE source_id = %s
                    """,
                    (source_id,),
                )
                row = cur.fetchone()
                if row is None:
                    return None
                return self._row_to_public_health_source_alert_state(dict(row))

    def open_public_health_source_alert_incident(
        self,
        source_id: str,
        incident_kind: str,
        incident_fingerprint: str,
    ) -> PublicHealthSourceAlertState:
        """Persist a newly opened active public-health alert incident."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO public_health_source_alert_state (
                        source_id,
                        active_incident_kind,
                        active_incident_fingerprint,
                        opened_at,
                        last_notified_at
                    ) VALUES (
                        %s, %s, %s, NOW(), NOW()
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        active_incident_kind = EXCLUDED.active_incident_kind,
                        active_incident_fingerprint = EXCLUDED.active_incident_fingerprint,
                        opened_at = NOW(),
                        last_notified_at = NOW(),
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (source_id, incident_kind, incident_fingerprint),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(f"Failed to open public health alert incident for {source_id}")
                return self._row_to_public_health_source_alert_state(dict(row))

    def resolve_public_health_source_alert_incident(
        self,
        source_id: str,
    ) -> PublicHealthSourceAlertState:
        """Clear the active public-health incident and record the latest resolution time."""
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO public_health_source_alert_state (
                        source_id,
                        active_incident_kind,
                        active_incident_fingerprint,
                        last_resolved_at
                    ) VALUES (
                        %s, NULL, NULL, NOW()
                    )
                    ON CONFLICT (source_id) DO UPDATE SET
                        active_incident_kind = NULL,
                        active_incident_fingerprint = NULL,
                        opened_at = NULL,
                        last_notified_at = NULL,
                        last_resolved_at = NOW(),
                        updated_at = NOW()
                    RETURNING *
                    """,
                    (source_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise ValueError(
                        f"Failed to resolve public health alert incident for {source_id}"
                    )
                return self._row_to_public_health_source_alert_state(dict(row))

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

    def _row_to_public_data_source(self, row: dict[str, Any]) -> PublicDataSource:
        """Convert database row to PublicDataSource model."""
        return PublicDataSource(
            source_id=row["source_id"],
            domain=row["domain"],
            source_name=row["source_name"],
            scope=row["scope"],
            jurisdiction_level=row["jurisdiction_level"],
            connector_type=row["connector_type"],
            access_route=row["access_route"],
            license_reuse_status=row["license_reuse_status"],
            attribution_requirement=row["attribution_requirement"],
            update_cadence=row["update_cadence"],
            freshness_sensitivity=row["freshness_sensitivity"],
            operational_risk=row["operational_risk"],
            recommended_usage_mode=row["recommended_usage_mode"],
            provenance_url=row["provenance_url"],
            last_verified_at=row["last_verified_at"],
            notes=row.get("notes"),
            fallback_source_id=row.get("fallback_source_id"),
            public_methodology_note=row.get("public_methodology_note"),
            last_refreshed_at=row.get("last_refreshed_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_resource_location(self, row: dict[str, Any]) -> ResourceLocation:
        """Convert database row to ResourceLocation model."""
        return ResourceLocation(
            id=row["id"],
            source_id=row["source_id"],
            kind=row["kind"],
            source_record_id=row.get("source_record_id"),
            name=row["name"],
            province=row["province"],
            city=row.get("city"),
            latitude=row["latitude"],
            longitude=row["longitude"],
            address=row.get("address"),
            postal_code=row.get("postal_code"),
            phone=row.get("phone"),
            website_url=row.get("website_url"),
            reference_status=row.get("reference_status"),
            location_description=row.get("location_description"),
            access_notes=row.get("access_notes"),
            crowdsourced=bool(row.get("crowdsourced")),
            completeness_status=row.get("completeness_status"),
            provenance_url=row["provenance_url"],
            last_refreshed_at=row.get("last_refreshed_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_public_health_alert(self, row: dict[str, Any]) -> PublicHealthAlert:
        """Convert database row to PublicHealthAlert model."""
        affected_products = row.get("affected_products") or []
        return PublicHealthAlert(
            id=row["id"],
            source_id=row["source_id"],
            title=row["title"],
            summary=row["summary"],
            alert_type=row["alert_type"],
            published_at=row["published_at"],
            source_updated_at=row.get("source_updated_at"),
            affected_products=affected_products,
            provenance_url=row["provenance_url"],
            last_refreshed_at=row.get("last_refreshed_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_public_health_system_metric(
        self,
        row: dict[str, Any],
    ) -> PublicHealthSystemMetric:
        """Convert database row to PublicHealthSystemMetric model."""
        return PublicHealthSystemMetric(
            id=row["id"],
            source_id=row["source_id"],
            series_key=row["series_key"],
            province=row["province"],
            geography_type=row["geography_type"],
            geography_name=row["geography_name"],
            reporting_year=int(row["reporting_year"]),
            dimension_label=row.get("dimension_label"),
            metrics=dict(row.get("metrics") or {}),
            provenance_url=row["provenance_url"],
            last_refreshed_at=row.get("last_refreshed_at"),
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_scraper_alert_state(self, row: dict[str, Any]) -> ScraperAlertState:
        """Convert database row to ScraperAlertState model."""
        return ScraperAlertState(
            source_id=row["source_id"],
            active_incident_kind=row.get("active_incident_kind"),
            active_incident_fingerprint=row.get("active_incident_fingerprint"),
            opened_at=row.get("opened_at"),
            last_notified_at=row.get("last_notified_at"),
            last_resolved_at=row.get("last_resolved_at"),
            updated_at=row.get("updated_at"),
        )

    def _row_to_public_health_source_alert_state(
        self,
        row: dict[str, Any],
    ) -> PublicHealthSourceAlertState:
        """Convert database row to PublicHealthSourceAlertState model."""
        return PublicHealthSourceAlertState(
            source_id=row["source_id"],
            active_incident_kind=row.get("active_incident_kind"),
            active_incident_fingerprint=row.get("active_incident_fingerprint"),
            opened_at=row.get("opened_at"),
            last_notified_at=row.get("last_notified_at"),
            last_resolved_at=row.get("last_resolved_at"),
            updated_at=row.get("updated_at"),
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
            patients_waiting=row.get("patients_waiting"),
            patients_in_treatment=row.get("patients_in_treatment"),
            total_treatment_spaces=row.get("total_treatment_spaces"),
            source_id=row["source_id"],
            raw_payload_hash=row["raw_payload_hash"],
            raw_payload_snippet=row.get("raw_payload_snippet"),
            parser_version=row["parser_version"],
            is_anomaly=row.get("is_anomaly", False),
            anomaly_reason=row.get("anomaly_reason"),
        )
