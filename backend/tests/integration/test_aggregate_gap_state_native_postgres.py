"""Opt-in native PostgreSQL validation of aggregate gap containment."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from waittime.services.aggregation import AggregationService
from waittime.services.database import DatabaseService

from .native_postgres_archive import (
    OCCUPANCY_SNAPSHOT_ONTOLOGY,
    WAIT_TIME_ONTOLOGY,
    NativePostgresCluster,
    NativePostgresDatabase,
)

pytestmark = [pytest.mark.integration, pytest.mark.native_postgres]


@pytest.fixture
def native_aggregate_database(native_pg_cluster: NativePostgresCluster):
    database = native_pg_cluster.create_database()
    migration_directory = Path(__file__).resolve().parents[2] / "migrations"
    try:
        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                for filename in (
                    "006_create_measurement_aggregates.sql",
                    "015_add_metric_family_to_aggregates.sql",
                    "023_add_measurement_aggregate_gaps.sql",
                ):
                    cursor.execute((migration_directory / filename).read_text(encoding="utf-8"))
        yield database
    finally:
        database.drop()


def _insert_aggregate_row(
    database: NativePostgresDatabase,
    period_start: datetime,
    period_end: datetime,
) -> None:
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO measurement_aggregates (
                    hospital_id, source_id, period_type, period_start, period_end,
                    mean_value, min_value, max_value, sample_count, metric_family,
                    start_event, end_event, statistic_type
                ) VALUES (
                    'wtc-native-hospital', 'wtc-native-source', 'daily', %s, %s,
                    45.0, 40.0, 50.0, 2, 'TIME_TO_PROVIDER', 'TRIAGE',
                    'PHYSICIAN', 'P90'
                )
                """,
                (period_start, period_end),
            )


def _insert_measurement(
    database: NativePostgresDatabase,
    timestamp: datetime,
    value: float,
    ontology: tuple[str, str, str, str, str],
) -> None:
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO measurements (
                    hospital_id, timestamp_utc, value, metric_family, start_event,
                    end_event, statistic_type, patient_scope, source_id,
                    raw_payload_hash, raw_payload_snippet, parser_version
                ) VALUES (
                    'wtc-native-hospital', %s, %s, %s, %s, %s, %s, %s,
                    'wtc-native-source', %s, NULL, 'native-gap-test-v1'
                )
                """,
                (timestamp, value, *ontology, "a" * 64),
            )


def _refresh_bucket(
    database: NativePostgresDatabase,
    period_start: datetime,
    period_end: datetime,
) -> int:
    with database.admin_connection() as connection:
        service = AggregationService(DatabaseService(conn=connection))
        return service.db.refresh_aggregate_bucket(
            "wtc-native-hospital",
            "daily",
            period_start,
            period_end,
            lambda rows: service._compute_period_outcome(
                "wtc-native-hospital", "daily", period_start, period_end, rows
            ),
        )


def _force_backfill_bucket(
    database: NativePostgresDatabase,
    period_start: datetime,
    period_end: datetime,
) -> dict[str, int]:
    with database.admin_connection() as connection:
        service = AggregationService(DatabaseService(conn=connection))
        return service.backfill(
            hospital_id="wtc-native-hospital",
            start_date=period_start,
            end_date=period_end,
            period_types=["daily"],
            force=True,
        )


def test_open_gap_hides_and_preserves_aggregate_after_raw_evidence_loss(
    native_aggregate_database: NativePostgresDatabase,
) -> None:
    database = native_aggregate_database
    period_start = datetime(2026, 10, 17, tzinfo=UTC)
    period_end = period_start + timedelta(days=1)
    _insert_aggregate_row(database, period_start, period_end)

    _insert_measurement(database, period_start + timedelta(hours=2), 90.0, WAIT_TIME_ONTOLOGY)
    _insert_measurement(
        database,
        period_start + timedelta(hours=3),
        110.0,
        ("TIME_TO_PROVIDER", "DOOR", "PHYSICIAN", "P90", "ALL"),
    )
    _insert_measurement(
        database,
        period_start + timedelta(hours=4),
        42.0,
        OCCUPANCY_SNAPSHOT_ONTOLOGY,
    )

    refreshed = _refresh_bucket(database, period_start, period_end)
    assert refreshed == 1  # Only the valid occupancy sibling was written.

    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT metric_family, mean_value
                FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                ORDER BY metric_family
                """,
                (period_start,),
            )
            assert cursor.fetchall() == [("STRETCHER_OCCUPANCY", 42.0)]
            cursor.execute(
                """
                SELECT mean_value FROM measurement_aggregates
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (45.0,)
            cursor.execute(
                """
                SELECT state, reason, signature_count, fingerprint
                FROM measurement_aggregate_gaps
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            original_gap = cursor.fetchone()
            assert original_gap[:3] == ("open", "ambiguous_methodology", 2)

    # Partial removal leaves one signature, but that is not evidence that the
    # historical conflict was methodologically corrected.
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM measurements
                WHERE hospital_id = 'wtc-native-hospital'
                  AND timestamp_utc = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start + timedelta(hours=3),),
            )

    assert _refresh_bucket(database, period_start, period_end) == 0
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT state, reason, signature_count, fingerprint
                FROM measurement_aggregate_gaps
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == original_gap
            cursor.execute(
                """
                SELECT mean_value FROM measurement_aggregates
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (45.0,)
            cursor.execute(
                """
                SELECT COUNT(*) FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (0,)

    # Total loss followed by a new homogeneous row must not replace the stored
    # aggregate or clear its gap. Only a future explicit reviewed correction
    # path may resolve this historical gap.
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM measurements WHERE hospital_id = 'wtc-native-hospital' "
                "AND timestamp_utc >= %s AND timestamp_utc < %s "
                "AND metric_family = 'TIME_TO_PROVIDER'",
                (period_start, period_end),
            )
    _insert_measurement(database, period_start + timedelta(hours=5), 120.0, WAIT_TIME_ONTOLOGY)
    # Force backfill revisits the bucket but cannot resolve the gap or replace
    # the ambiguous family summary from a newly homogeneous current snapshot.
    # The unaffected verified occupancy sibling is still refreshed.
    assert _force_backfill_bucket(database, period_start, period_end) == {"daily": 1}
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mean_value, sample_count
                FROM measurement_aggregates
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (45.0, 2)
            cursor.execute(
                """
                SELECT state, reason, signature_count, fingerprint, resolved_at
                FROM measurement_aggregate_gaps
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            current_gap = cursor.fetchone()
            assert current_gap[:4] == original_gap
            assert current_gap[4] is None
            cursor.execute(
                """
                SELECT COUNT(*) FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (0,)


def test_force_backfill_does_not_promote_legacy_summary_without_complete_provenance(
    native_aggregate_database: NativePostgresDatabase,
) -> None:
    database = native_aggregate_database
    period_start = datetime(2026, 10, 17, tzinfo=UTC)
    period_end = period_start + timedelta(days=1)
    _insert_aggregate_row(database, period_start, period_end)

    assert _force_backfill_bucket(database, period_start, period_end) == {"daily": 0}

    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mean_value, verification_state, verified_at
                FROM measurement_aggregates
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            old_summary = cursor.fetchone()
            assert old_summary == (45.0, "legacy_unverified", None)
            cursor.execute(
                """
                SELECT COUNT(*) FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (0,)

    # A single current row cannot prove that the historical aggregate's raw
    # provenance was complete; force remains non-adjudicating.
    _insert_measurement(database, period_start + timedelta(hours=5), 120.0, WAIT_TIME_ONTOLOGY)
    assert _force_backfill_bucket(database, period_start, period_end) == {"daily": 0}

    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mean_value, verification_state, verified_at
                FROM measurement_aggregates
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (period_start,),
            )
            assert cursor.fetchone() == old_summary
            cursor.execute(
                """
                SELECT COUNT(*) FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (0,)
            cursor.execute(
                """
                SELECT COUNT(*) FROM measurement_aggregate_gaps
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                """,
                (period_start,),
            )
            assert cursor.fetchone() == (0,)

    clean_period_start = period_start + timedelta(days=1)
    clean_period_end = clean_period_start + timedelta(days=1)
    _insert_measurement(database, clean_period_start + timedelta(hours=5), 80.0, WAIT_TIME_ONTOLOGY)
    assert _refresh_bucket(database, clean_period_start, clean_period_end) == 1
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT mean_value, sample_count
                FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_type = 'daily' AND period_start = %s
                  AND metric_family = 'TIME_TO_PROVIDER'
                """,
                (clean_period_start,),
            )
            assert cursor.fetchone() == (80.0, 1)
