"""PostgreSQL behavior tests for the opt-in preservation inventory."""

from __future__ import annotations

import json
import os
import sys
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import psycopg2
import pytest
from psycopg2.extensions import make_dsn, parse_dsn
from psycopg2.sql import SQL, Identifier

from waittime.cli.storage_stats import main as storage_stats_main
from waittime.services.database import DatabaseService


@pytest.fixture
def synthetic_inventory_database():
    """Create only isolated synthetic tables in a local *_test database."""
    database_url = os.environ.get("WTC_PRESERVATION_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("WTC_PRESERVATION_TEST_DATABASE_URL is not set")

    dsn_fields = parse_dsn(database_url)
    if dsn_fields.get("host") not in {"localhost", "127.0.0.1", "::1"}:
        pytest.fail("preservation integration tests require a loopback PostgreSQL host")
    if not dsn_fields.get("dbname", "").endswith("_test"):
        pytest.fail("preservation integration tests require a *_test database")

    schema_name = f"preservation_test_{uuid4().hex}"
    connection = psycopg2.connect(database_url, connect_timeout=3)
    connection.autocommit = True
    try:
        with connection.cursor() as cursor:
            cursor.execute(SQL("CREATE SCHEMA {}").format(Identifier(schema_name)))
            cursor.execute(
                SQL(
                    "CREATE TYPE {}.metric_family_enum AS ENUM "
                    "('TIME_TO_PROVIDER', 'TOTAL_LOS', 'STRETCHER_OCCUPANCY')"
                ).format(Identifier(schema_name))
            )
            cursor.execute(
                SQL(
                    "CREATE TYPE {}.start_event_enum AS ENUM "
                    "('TRIAGE', 'REGISTRATION', 'DOOR', 'UNKNOWN')"
                ).format(Identifier(schema_name))
            )
            cursor.execute(
                SQL(
                    "CREATE TYPE {}.end_event_enum AS ENUM "
                    "('PHYSICIAN', 'PROVIDER', 'DISCHARGE', 'FIRST_ASSESSMENT')"
                ).format(Identifier(schema_name))
            )
            cursor.execute(
                SQL(
                    "CREATE TYPE {}.statistic_type_enum AS ENUM "
                    "('P90', 'MEDIAN', 'MEAN', 'ROLLING_AVG', 'ALGORITHMIC', 'POINT_ESTIMATE')"
                ).format(Identifier(schema_name))
            )
            cursor.execute(
                SQL(
                    "CREATE TYPE {}.patient_scope_enum AS ENUM "
                    "('ALL', 'MID_ACUITY', 'NON_PRIORITY', 'HIGH_ACUITY')"
                ).format(Identifier(schema_name))
            )
            cursor.execute(
                SQL(
                    """
                    CREATE TABLE {}.sources (
                        id text PRIMARY KEY
                    )
                    """
                ).format(Identifier(schema_name))
            )
            cursor.execute(
                SQL(
                    """
                    CREATE TABLE {}.measurements (
                        id bigserial PRIMARY KEY,
                        source_id text NOT NULL,
                        timestamp_utc timestamptz NOT NULL,
                        metric_family {}.metric_family_enum NOT NULL,
                        start_event {}.start_event_enum NOT NULL,
                        end_event {}.end_event_enum NOT NULL,
                        statistic_type {}.statistic_type_enum NOT NULL,
                        patient_scope {}.patient_scope_enum NOT NULL,
                        raw_payload_hash char(64) NOT NULL,
                        raw_payload_snippet text,
                        parser_version text NOT NULL
                    )
                    """
                ).format(*[Identifier(schema_name)] * 6)
            )
            cursor.execute(
                SQL(
                    """
                    CREATE TABLE {}.measurement_aggregates (
                        id bigserial PRIMARY KEY,
                        source_id text NOT NULL,
                        period_type text NOT NULL,
                        period_start timestamptz NOT NULL,
                        period_end timestamptz NOT NULL,
                        sample_count integer NOT NULL,
                        metric_family text NOT NULL,
                        start_event text NOT NULL,
                        end_event text NOT NULL,
                        statistic_type text NOT NULL,
                        created_at timestamptz NOT NULL
                    )
                    """
                ).format(Identifier(schema_name))
            )

        def test_dsn(timezone: str) -> str:
            options = f"-c search_path={schema_name},public -c timezone={timezone}"
            return make_dsn(database_url, options=options)

        def service(timezone: str) -> DatabaseService:
            return DatabaseService(test_dsn(timezone))

        yield {"service": service, "test_dsn": test_dsn, "schema_name": schema_name}
    finally:
        with connection.cursor() as cursor:
            cursor.execute(SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(Identifier(schema_name)))
        connection.close()


def _insert_source(service: DatabaseService, source_id: str) -> None:
    with service.get_connection() as connection:
        with service.get_cursor(connection) as cursor:
            cursor.execute("INSERT INTO sources (id) VALUES (%s)", (source_id,))


def test_preservation_inventory_handles_empty_tables_and_reports_read_only(
    synthetic_inventory_database, monkeypatch, capsys
):
    service = synthetic_inventory_database["service"]("UTC")
    _insert_source(service, "test-empty-source")

    inventory = service.get_measurement_preservation_inventory(
        _as_of_utc=datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
    )

    assert inventory["transaction_read_only"] is True
    assert inventory["statement_timeout"]
    assert inventory["raw_measurements"]["groups"] == []
    assert inventory["raw_measurements"]["sources_without_measurements"] == ["test-empty-source"]
    assert inventory["aggregates"]["groups"] == []
    assert inventory["purge_execution_history"] == "not_assessed"
    assert inventory["provider_backup_pitr_restore_evidence"] == "not_assessed"

    monkeypatch.setenv("DATABASE_URL", synthetic_inventory_database["test_dsn"]("UTC"))
    monkeypatch.setattr(sys, "argv", ["storage_stats", "--preservation-inventory"])
    assert storage_stats_main() == 0
    cli_payload = json.loads(capsys.readouterr().out)
    assert cli_payload["transaction_read_only"] is True
    assert cli_payload["raw_measurements"]["groups"] == []


def test_preservation_inventory_counts_ties_provenance_and_elapsed_utc_cutoff(
    synthetic_inventory_database,
):
    utc_service = synthetic_inventory_database["service"]("UTC")
    lord_howe_service = synthetic_inventory_database["service"]("Australia/Lord_Howe")
    source_id = "test-preservation-source"
    snapshot = datetime(2026, 10, 13, 12, 0, tzinfo=UTC)
    cutoff = snapshot - timedelta(days=30)
    tied_timestamp = snapshot - timedelta(hours=3)
    lord_howe = ZoneInfo("Australia/Lord_Howe")
    assert snapshot.astimezone(lord_howe).utcoffset() != cutoff.astimezone(lord_howe).utcoffset()

    _insert_source(utc_service, source_id)
    with utc_service.get_connection() as connection:
        with utc_service.get_cursor(connection) as cursor:
            rows = [
                (cutoff - timedelta(hours=1), "", "", None),
                # Lord Howe's 2026 DST transition occurred in this 30-day
                # interval. This row is newer than 720 elapsed hours but can
                # be older than a session-local calendar subtraction.
                (cutoff + timedelta(minutes=15), "b" * 64, "v1", "payload sentinel"),
                (tied_timestamp, "c" * 64, "v2", None),
                (tied_timestamp, "d" * 64, "v2", "private snippet sentinel"),
                (snapshot + timedelta(hours=1), "e" * 64, "v2", "future sentinel"),
            ]
            for timestamp, payload_hash, parser_version, snippet in rows:
                cursor.execute(
                    """
                    INSERT INTO measurements (
                        source_id, timestamp_utc, metric_family, start_event, end_event,
                        statistic_type, patient_scope, raw_payload_hash,
                        raw_payload_snippet, parser_version
                    ) VALUES (%s, %s, 'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN',
                              'MEAN', 'ALL', %s, %s, %s)
                    """,
                    (source_id, timestamp, payload_hash, snippet, parser_version),
                )
            cursor.execute(
                """
                INSERT INTO measurements (
                    source_id, timestamp_utc, metric_family, start_event, end_event,
                    statistic_type, patient_scope, raw_payload_hash,
                    raw_payload_snippet, parser_version
                ) VALUES (%s, %s, 'TOTAL_LOS', 'DOOR', 'DISCHARGE',
                          'MEDIAN', 'ALL', %s, %s, %s)
                """,
                (source_id, snapshot - timedelta(hours=2), "f" * 64, None, "v3"),
            )
            for period_start, sample_count in (
                (snapshot - timedelta(days=2), 4),
                (snapshot - timedelta(days=1), 2),
            ):
                cursor.execute(
                    """
                    INSERT INTO measurement_aggregates (
                        source_id, period_type, period_start, period_end, sample_count,
                        metric_family, start_event, end_event, statistic_type, created_at
                    ) VALUES (%s, 'daily', %s, %s, %s, 'TIME_TO_PROVIDER',
                              'TRIAGE', 'PHYSICIAN', 'MEAN', %s)
                    """,
                    (
                        source_id,
                        period_start,
                        period_start + timedelta(days=1),
                        sample_count,
                        period_start + timedelta(hours=2),
                    ),
                )

    utc_report = utc_service.get_measurement_preservation_inventory(_as_of_utc=snapshot)
    lord_howe_report = lord_howe_service.get_measurement_preservation_inventory(_as_of_utc=snapshot)

    assert utc_report == lord_howe_report
    assert utc_report["retention_cutoff_utc"] == "2026-09-13T12:00:00Z"
    assert utc_report["transaction_read_only"] is True
    assert len(utc_report["raw_measurements"]["groups"]) == 2

    time_to_provider = next(
        group
        for group in utc_report["raw_measurements"]["groups"]
        if group["metric_family"] == "TIME_TO_PROVIDER"
    )
    assert time_to_provider["row_count"] == 5
    assert time_to_provider["rows_older_than_30_days"] == 1
    assert time_to_provider["future_timestamp_rows"] == 1
    assert time_to_provider["oldest_timestamp_utc"] == "2026-09-13T11:00:00Z"
    assert time_to_provider["newest_timestamp_utc"] == "2026-10-13T13:00:00Z"
    assert time_to_provider["missing_payload_hash_count"] == 1
    assert time_to_provider["missing_parser_version_count"] == 1
    assert time_to_provider["absent_optional_payload_snippet_count"] == 2
    assert utc_report["raw_measurements"]["provenance_schema_nullable"] == {
        "source_id": False,
        "raw_payload_hash": False,
        "parser_version": False,
        "raw_payload_snippet": True,
    }

    aggregate = utc_report["aggregates"]["groups"][0]
    assert aggregate["aggregate_row_count"] == 2
    assert aggregate["aggregate_sample_count_sum"] == 6
    assert aggregate["oldest_period_start_utc"] == "2026-10-11T12:00:00Z"
    assert aggregate["newest_period_end_utc"] == "2026-10-13T12:00:00Z"

    serialized = str(utc_report)
    assert "private snippet sentinel" not in serialized
    assert "payload sentinel" not in serialized
    assert "future sentinel" not in serialized
    assert "hospital_id" not in serialized
    assert "b" * 64 not in serialized
    assert "c" * 64 not in serialized
