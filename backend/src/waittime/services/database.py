"""Database service layer for PostgreSQL (Neon).

Handles all database operations including:
- Writing measurements
- Updating scraper heartbeats
- Managing hospital verification status
"""

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

from waittime.core import Hospital, Measurement, MeasurementAggregate, ScraperStatus, Source

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
                "Database URL required. Set DATABASE_URL environment variable or pass it directly."
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
                        url = EXCLUDED.url,
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

    def insert_measurement(self, measurement: Measurement) -> dict[str, Any]:
        """Insert a new measurement."""
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
                if row is None:
                    raise ValueError("Failed to insert measurement")
                return dict(row)

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
                    for m in measurements
                ]

                psycopg2.extras.execute_batch(
                    cur,
                    """
                    INSERT INTO measurements (
                        hospital_id, timestamp_utc, value,
                        metric_family, start_event, end_event, statistic_type, patient_scope,
                        patients_waiting, patients_in_treatment, total_treatment_spaces,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version,
                        is_anomaly, anomaly_reason
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
                if row is None:
                    return None
                return self._row_to_measurement(dict(row))

    def cleanup_old_measurements(self, retention_days: int = 30) -> int:
        """Delete measurements older than retention period.

        IMPORTANT: This implements the storage safety policy from strategic plan.
        We only keep raw measurements for retention_days, then delete them to prevent
        database bloat. Aggregated analytics should be computed before deletion.

        Args:
            retention_days: Number of days to retain raw measurements (default: 30)

        Returns:
            Number of measurements deleted

        Example:
            >>> db = DatabaseService()
            >>> deleted = db.cleanup_old_measurements(retention_days=30)
            >>> logger.info(f"Deleted {deleted} old measurements")
        """
        with self.get_connection() as conn:
            with self.get_cursor(conn) as cur:
                cur.execute(
                    """
                    DELETE FROM measurements
                    WHERE timestamp_utc < NOW() - INTERVAL '%s days'
                    """,
                    (retention_days,),
                )
                deleted_count = cur.rowcount or 0
                logger.info(
                    f"Cleaned up {deleted_count} measurements older than {retention_days} days"
                )
                return deleted_count

    def get_measurement_age_stats(self) -> dict[str, Any]:
        """Get statistics about measurement ages for monitoring retention policy.

        Returns:
            Dict with oldest_measurement_age_days, newest_measurement_age_days,
            total_measurements, and measurements_older_than_30_days
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
                            WHERE timestamp_utc < NOW() - INTERVAL '30 days'
                        ) as measurements_older_than_30_days
                    FROM measurements
                    """
                )
                row = cur.fetchone()

                if not row or row["total_measurements"] == 0:
                    return {
                        "oldest_measurement_age_days": None,
                        "newest_measurement_age_days": None,
                        "total_measurements": 0,
                        "measurements_older_than_30_days": 0,
                    }

                return {
                    "oldest_measurement_age_days": round(float(row["oldest_age_days"]), 1)
                    if row["oldest_age_days"]
                    else None,
                    "newest_measurement_age_days": round(float(row["newest_age_days"]), 1)
                    if row["newest_age_days"]
                    else None,
                    "total_measurements": row["total_measurements"],
                    "measurements_older_than_30_days": row["measurements_older_than_30_days"],
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

    def insert_aggregate(self, aggregate: MeasurementAggregate) -> bool:
        """Insert an aggregate, skipping if a duplicate already exists.

        Uses ON CONFLICT DO NOTHING on the (hospital_id, period_type, period_start)
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
                    ON CONFLICT (hospital_id, period_type, period_start) DO NOTHING
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
                return row["id"] if row else 0

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
