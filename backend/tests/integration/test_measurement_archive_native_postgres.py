"""Opt-in native PostgreSQL 17 validation using synthetic rows only.

Run only after the coordinator has reviewed the isolated harness and authorized
execution, supplying both explicit options. These tests never use DATABASE_URL.
"""

from __future__ import annotations

import json
import re
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from native_postgres_archive import (
    FIXTURE_ENUM_VALUES,
    WAIT_TIME_ONTOLOGY,
    NativePostgresCluster,
    NativePostgresDatabase,
    canonical_measurement_row,
)
from psycopg2 import sql
from psycopg2.extensions import TRANSACTION_STATUS_IDLE

from waittime.services.measurement_archive import (
    ARCHIVE_FILE,
    MEASUREMENT_QUERY,
    ArchiveUsePolicy,
    MeasurementArchiveError,
    export_measurement_archive,
)

pytestmark = [pytest.mark.integration, pytest.mark.native_postgres]


def test_native_fixture_ontology_literals_are_members_of_actual_enum_migration() -> None:
    migration = Path(__file__).resolve().parents[2] / "migrations" / "001_create_enums.sql"
    contents = migration.read_text(encoding="utf-8")
    enum_pattern = re.compile(
        r"CREATE\s+TYPE\s+(\w+)\s+AS\s+ENUM\s*\((.*?)\)\s*;",
        re.IGNORECASE | re.DOTALL,
    )
    migration_values = {
        enum_name: frozenset(re.findall(r"'([^']+)'", body))
        for enum_name, body in enum_pattern.findall(contents)
    }
    for enum_name, fixture_values in FIXTURE_ENUM_VALUES.items():
        assert enum_name in migration_values
        assert fixture_values <= migration_values[enum_name]


@pytest.fixture
def native_pg_database(native_pg_cluster: NativePostgresCluster):
    database = native_pg_cluster.create_database()
    try:
        yield database
    finally:
        database.drop()


def _policy() -> ArchiveUsePolicy:
    return ArchiveUsePolicy(
        policy_reference="synthetic-native-test-policy",
        access_control_reference="private-local-test-directory",
        expires_at_utc=datetime.now(UTC) + timedelta(days=1),
    )


def _archive_rows(archive_directory: Path) -> list[dict[str, object]]:
    with (archive_directory / ARCHIVE_FILE).open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def test_named_cursor_repeatable_read_excludes_concurrent_insert_and_update(
    native_pg_cluster: NativePostgresCluster,
    native_pg_database: NativePostgresDatabase,
) -> None:
    database = native_pg_database
    original_ids = database.insert_synthetic_measurements(3)
    first_batch_fetched = threading.Event()
    writer_committed = threading.Event()
    writer_errors: list[BaseException] = []
    inserted_ids: list[int] = []

    def concurrent_writer() -> None:
        try:
            if not first_batch_fetched.wait(timeout=15):
                raise AssertionError("archive did not fetch its first named-cursor batch")
            with database.admin_connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE measurements SET value = 777.0, "
                        "raw_payload_snippet = 'updated after snapshot' WHERE id = %s",
                        (original_ids[0],),
                    )
                    cursor.execute(
                        """
                        INSERT INTO measurements (
                            hospital_id, timestamp_utc, value, metric_family,
                            start_event, end_event, statistic_type, patient_scope,
                            source_id, raw_payload_hash, raw_payload_snippet,
                            parser_version, created_at
                        ) VALUES (
                            'wtc-native-hospital', %s, 999.0, %s, %s, %s, %s, %s,
                            'wtc-native-source', %s, 'inserted after snapshot',
                            'native-writer-v1', %s
                        ) RETURNING id
                        """,
                        (
                            datetime(2026, 10, 18, 13, 0, tzinfo=UTC),
                            *WAIT_TIME_ONTOLOGY,
                            "b" * 64,
                            datetime(2026, 10, 18, 13, 0, 1, tzinfo=UTC),
                        ),
                    )
                    inserted = cursor.fetchone()
                    assert inserted is not None
                    inserted_ids.append(int(inserted[0]))
            writer_committed.set()
        except BaseException as exc:  # surfaced in the test thread after join
            writer_errors.append(exc)
            writer_committed.set()

    def after_first_fetch() -> None:
        first_batch_fetched.set()
        if not writer_committed.wait(timeout=15):
            raise AssertionError("concurrent synthetic writer did not finish")
        if writer_errors:
            raise AssertionError("concurrent synthetic writer failed") from writer_errors[0]

    writer = threading.Thread(target=concurrent_writer, name="wtc-native-archive-writer")
    writer.start()
    destination = native_pg_cluster.archive_destination("repeatable-read")
    service = database.archive_service(after_first_fetch=after_first_fetch)
    try:
        verification = export_measurement_archive(
            service,
            destination,
            policy=_policy(),
            fetch_batch_size=1,
            max_snapshot_seconds=20,
        )
    finally:
        writer.join(timeout=20)

    assert not writer.is_alive(), "synthetic writer did not terminate"
    assert not writer_errors
    assert len(inserted_ids) == 1
    exported = _archive_rows(destination)
    assert [row["id"] for row in exported] == original_ids
    assert exported[0]["value"] == 120.0
    assert exported[0]["raw_payload_snippet"] == "synthetic archive fixture row 0"
    assert service.last_session_settings == {"isolation_level": "REPEATABLE READ", "readonly": True}
    assert verification.row_count == len(original_ids)

    current_rows = {row["id"]: row for row in database.read_measurements()}
    assert current_rows[original_ids[0]]["value"] == 777.0
    assert current_rows[original_ids[0]]["raw_payload_snippet"] == "updated after snapshot"
    assert inserted_ids[0] in current_rows and current_rows[inserted_ids[0]]["value"] == 999.0
    native_pg_cluster.record_archive_verification("repeatable_read", verification)
    native_pg_cluster.record_assertion(
        "repeatable_read_concurrent_write",
        {"snapshot_rows": len(exported), "concurrent_insert_rows": 1, "concurrent_update_rows": 1},
    )


def test_added_measurement_column_is_rejected_before_data_query(
    native_pg_cluster: NativePostgresCluster,
    native_pg_database: NativePostgresDatabase,
) -> None:
    native_pg_database.insert_synthetic_measurements(1)
    with native_pg_database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE measurements ADD COLUMN unapproved_fixture_column TEXT")

    destination = native_pg_cluster.archive_destination("schema-drift")
    service = native_pg_database.archive_service()
    with pytest.raises(MeasurementArchiveError, match="schema does not match"):
        export_measurement_archive(service, destination, policy=_policy())

    normalized_measurement_query = " ".join(MEASUREMENT_QUERY.split())
    assert normalized_measurement_query not in service.executed_queries
    assert not destination.exists()
    assert service.rollback_performed
    assert service.transaction_status_after_rollback == TRANSACTION_STATUS_IDLE
    native_pg_cluster.record_assertion(
        "schema_drift_rejected_before_measurement_read",
        {"data_query_started": False, "partial_archive_published": False, "rollback": True},
    )


def test_statement_cancellation_rolls_back_and_removes_partial_archive(
    native_pg_cluster: NativePostgresCluster,
    native_pg_database: NativePostgresDatabase,
) -> None:
    database = native_pg_database
    database.insert_synthetic_measurements(1)
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE FUNCTION native_archive_test_delay_policy() RETURNS BOOLEAN
                LANGUAGE plpgsql VOLATILE AS $$
                BEGIN
                    PERFORM pg_sleep(7);
                    RETURN TRUE;
                END;
                $$
                """
            )
            cursor.execute("ALTER TABLE measurements ENABLE ROW LEVEL SECURITY")
            cursor.execute("ALTER TABLE measurements FORCE ROW LEVEL SECURITY")
            cursor.execute(
                "CREATE POLICY native_archive_test_delay "
                "ON measurements USING (native_archive_test_delay_policy())"
            )
            cursor.execute(
                sql.SQL(
                    "GRANT EXECUTE ON FUNCTION native_archive_test_delay_policy() TO {}"
                ).format(sql.Identifier(database.reader_role))
            )

    destination = native_pg_cluster.archive_destination("statement-cancellation")
    service = database.archive_service()
    with pytest.raises(MeasurementArchiveError, match="database archive read failed"):
        export_measurement_archive(
            service,
            destination,
            policy=_policy(),
            fetch_batch_size=1,
            max_snapshot_seconds=3,
        )

    assert service.last_error_type == "QueryCanceled"
    assert service.rollback_performed
    assert service.transaction_status_after_rollback == TRANSACTION_STATUS_IDLE
    assert not destination.exists()
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM measurements")
            assert cursor.fetchone()[0] == 1
    native_pg_cluster.record_assertion(
        "statement_timeout_cleanup",
        {
            "server_error": service.last_error_type,
            "rollback": service.rollback_performed,
            "transaction_idle": service.transaction_status_after_rollback
            == TRANSACTION_STATUS_IDLE,
            "partial_archive_published": destination.exists(),
        },
    )


def test_export_restores_exact_rows_to_a_separate_native_database(
    native_pg_cluster: NativePostgresCluster,
    native_pg_database: NativePostgresDatabase,
) -> None:
    source_database = native_pg_database
    source_database.insert_synthetic_measurements(3)
    expected = [canonical_measurement_row(row) for row in source_database.read_measurements()]
    destination = native_pg_cluster.archive_destination("separate-database-restore")
    verification = export_measurement_archive(
        source_database.archive_service(),
        destination,
        policy=_policy(),
        fetch_batch_size=2,
    )
    archived_rows = _archive_rows(destination)
    assert archived_rows == expected

    restore_database = native_pg_cluster.create_database()
    try:
        restore_database.insert_archive_rows(archived_rows)
        restored = [canonical_measurement_row(row) for row in restore_database.read_measurements()]
        assert restored == archived_rows
        assert verification.row_count == len(expected)
    finally:
        restore_database.drop()

    native_pg_cluster.record_archive_verification("separate_database_restore", verification)
    native_pg_cluster.record_assertion(
        "separate_database_exact_restore",
        {"source_rows": len(expected), "restored_rows": len(restored), "exact_rows_match": True},
    )
