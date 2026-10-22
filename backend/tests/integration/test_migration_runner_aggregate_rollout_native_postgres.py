"""Exercise atomic aggregate migration application through the real runner."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

import psycopg2
import pytest
from native_postgres_archive import (  # type: ignore[import-untyped]
    NativePostgresCluster,
    NativePostgresDatabase,
)
from psycopg2.extensions import make_dsn

from waittime.cli import bootstrap_analytics
from waittime.services.database import DatabaseService  # type: ignore[import-untyped]

pytestmark = [pytest.mark.integration, pytest.mark.native_postgres]

RUNNER_PATH = Path(__file__).resolve().parents[2] / "run_migrations.py"
SPEC = importlib.util.spec_from_file_location("native_test_run_migrations", RUNNER_PATH)
assert SPEC is not None
assert SPEC.loader is not None
run_migrations = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_migrations
SPEC.loader.exec_module(run_migrations)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
SETUP_MIGRATION_NAMES = (
    "006_create_measurement_aggregates.sql",
    "015_add_metric_family_to_aggregates.sql",
)
CONSOLIDATED_MIGRATION_NAME = "023_add_measurement_aggregate_gaps.sql"
LEGACY_AGGREGATES = (
    (datetime(2020, 1, 2, tzinfo=UTC), 45.0),
    (datetime(2020, 1, 3, tzinfo=UTC), 46.0),
)


def _runner_database_service(database: NativePostgresDatabase) -> DatabaseService:
    parameters = database.cluster._connection_parameters(
        database.name,
        database.cluster.owner,
        timeout=5,
    )
    return DatabaseService(database_url=make_dsn(**parameters))


def _insert_legacy_aggregates(database: NativePostgresDatabase) -> None:
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            for period_start, mean_value in LEGACY_AGGREGATES:
                cursor.execute(
                    """
                    INSERT INTO measurement_aggregates (
                        hospital_id, source_id, period_type, period_start, period_end,
                        mean_value, min_value, max_value, sample_count, metric_family,
                        start_event, end_event, statistic_type
                    ) VALUES (
                        'wtc-native-hospital', 'wtc-native-source', 'daily', %s, %s,
                        %s, 40.0, 50.0, 1, 'TIME_TO_PROVIDER', 'TRIAGE',
                        'PHYSICIAN', 'P90'
                    )
                    """,
                    (period_start, period_start + timedelta(days=1), mean_value),
                )


def _stored_aggregate_rows(database: NativePostgresDatabase) -> list[tuple[Any, ...]]:
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, period_start, period_end, mean_value, min_value, max_value,
                       sample_count, metric_family, start_event, end_event, statistic_type
                FROM measurement_aggregates
                WHERE hospital_id = 'wtc-native-hospital'
                ORDER BY period_start
                """
            )
            return cast(list[tuple[Any, ...]], cursor.fetchall())


def test_runner_rolls_back_all_of_023_then_hides_preserved_legacy_rows(
    native_pg_cluster: NativePostgresCluster,
    tmp_path: Path,
) -> None:
    """The consolidated migration is atomic on failure and preserves legacy values."""
    database = native_pg_cluster.create_database()
    try:
        service = _runner_database_service(database)
        setup_paths = [MIGRATIONS_DIR / name for name in SETUP_MIGRATION_NAMES]
        setup_results = run_migrations.run_migrations(service, setup_paths)
        assert [result.status for result in setup_results] == ["applied", "applied"]

        _insert_legacy_aggregates(database)
        original_rows = _stored_aggregate_rows(database)
        assert len(original_rows) == len(LEGACY_AGGREGATES)

        migration = MIGRATIONS_DIR / CONSOLIDATED_MIGRATION_NAME
        failing_migration = tmp_path / CONSOLIDATED_MIGRATION_NAME
        failing_migration.write_text(
            migration.read_text(encoding="utf-8") + "\nSELECT 1 / 0;\n",
            encoding="utf-8",
        )

        with pytest.raises(psycopg2.errors.DivisionByZero):
            run_migrations.run_migrations(service, [failing_migration])

        # The late error rolls back the complete file, including its ledger row.
        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT to_regclass('public.measurement_aggregate_gaps'),
                           to_regclass('public.measurement_aggregates_usable')
                    """
                )
                assert cursor.fetchone() == (None, None)
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'measurement_aggregates'
                      AND column_name IN ('verification_state', 'verified_at')
                    ORDER BY column_name
                    """
                )
                assert cursor.fetchall() == []
                cursor.execute("SELECT filename FROM schema_migrations ORDER BY filename")
                assert cursor.fetchall() == [(name,) for name in SETUP_MIGRATION_NAMES]

        assert _stored_aggregate_rows(database) == original_rows

        # Applying the unmodified file creates the complete usable-read contract.
        results = run_migrations.run_migrations(service, [migration])
        assert [(result.filename, result.status) for result in results] == [
            (CONSOLIDATED_MIGRATION_NAME, "applied")
        ]
        assert _stored_aggregate_rows(database) == original_rows

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT verification_state, verified_at, COUNT(*)
                    FROM measurement_aggregates
                    WHERE hospital_id = 'wtc-native-hospital'
                    GROUP BY verification_state, verified_at
                    """
                )
                assert cursor.fetchall() == [("legacy_unverified", None, len(original_rows))]
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM measurement_aggregates_usable
                    WHERE hospital_id = 'wtc-native-hospital'
                    """
                )
                assert cursor.fetchone() == (0,)
                cursor.execute("SELECT filename FROM schema_migrations ORDER BY filename")
                assert cursor.fetchall() == [
                    (name,) for name in (*SETUP_MIGRATION_NAMES, CONSOLIDATED_MIGRATION_NAME)
                ]
    finally:
        database.drop()


def test_runner_rejects_023_after_partial_duplicate_collision_without_adoption(
    native_pg_cluster: NativePostgresCluster,
) -> None:
    """A partial collision cannot count as completion of migration 023."""
    database = native_pg_cluster.create_database()
    try:
        service = _runner_database_service(database)
        setup_paths = [MIGRATIONS_DIR / name for name in SETUP_MIGRATION_NAMES]
        setup_results = run_migrations.run_migrations(service, setup_paths)
        assert [result.status for result in setup_results] == ["applied", "applied"]

        # The name collision triggers PostgreSQL 42P07 at the first statement
        # in 023, before its verification columns and usable view are created.
        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE TABLE measurement_aggregate_gaps (collision_id INTEGER)")

        with pytest.raises(psycopg2.errors.DuplicateTable):
            run_migrations.run_migrations(service, [MIGRATIONS_DIR / CONSOLIDATED_MIGRATION_NAME])

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT filename FROM schema_migrations ORDER BY filename",
                )
                assert cursor.fetchall() == [(name,) for name in SETUP_MIGRATION_NAMES]
                cursor.execute(
                    "SELECT checksum_sha256 FROM schema_migrations WHERE filename = %s",
                    (CONSOLIDATED_MIGRATION_NAME,),
                )
                assert cursor.fetchone() is None
                cursor.execute(
                    """
                    SELECT to_regclass('public.measurement_aggregates_usable'),
                           EXISTS (
                               SELECT 1 FROM information_schema.columns
                               WHERE table_schema = 'public'
                                 AND table_name = 'measurement_aggregates'
                                 AND column_name = 'verification_state'
                           )
                    """
                )
                # The conflict leaves 023 wholly unapplied and preserves only
                # the pre-existing placeholder object.
                assert cursor.fetchone() == (None, False)
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'measurement_aggregate_gaps'
                    ORDER BY ordinal_position
                    """
                )
                assert cursor.fetchall() == [("collision_id",)]
    finally:
        database.drop()


def test_bootstrap_rejects_023_after_partial_duplicate_collision(
    native_pg_cluster: NativePostgresCluster,
) -> None:
    """The documented bootstrap consumer must not silently adopt a partial 023."""
    database = native_pg_cluster.create_database()
    try:
        service = _runner_database_service(database)
        setup_paths = [MIGRATIONS_DIR / name for name in SETUP_MIGRATION_NAMES]
        setup_results = run_migrations.run_migrations(service, setup_paths)
        assert [result.status for result in setup_results] == ["applied", "applied"]

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("CREATE TABLE measurement_aggregate_gaps (collision_id INTEGER)")

        migration = MIGRATIONS_DIR / CONSOLIDATED_MIGRATION_NAME
        with patch.object(bootstrap_analytics, "_migration_files", return_value=[migration]):
            with pytest.raises(psycopg2.errors.DuplicateTable):
                bootstrap_analytics.apply_migrations(service)

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT filename FROM schema_migrations ORDER BY filename")
                assert cursor.fetchall() == [(name,) for name in SETUP_MIGRATION_NAMES]
                cursor.execute(
                    """
                    SELECT to_regclass('public.measurement_aggregates_usable'),
                           EXISTS (
                               SELECT 1 FROM information_schema.columns
                               WHERE table_schema = 'public'
                                 AND table_name = 'measurement_aggregates'
                                 AND column_name = 'verification_state'
                           )
                    """
                )
                assert cursor.fetchone() == (None, False)
                cursor.execute(
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'measurement_aggregate_gaps'
                    ORDER BY ordinal_position
                    """
                )
                assert cursor.fetchall() == [("collision_id",)]
    finally:
        database.drop()


def test_bootstrap_023_is_ledgered_and_canonical_runner_skips_it(
    native_pg_cluster: NativePostgresCluster,
) -> None:
    """Successful bootstrap migration is checksum-ledgered and idempotent."""
    database = native_pg_cluster.create_database()
    try:
        service = _runner_database_service(database)
        setup_paths = [MIGRATIONS_DIR / name for name in SETUP_MIGRATION_NAMES]
        setup_results = run_migrations.run_migrations(service, setup_paths)
        assert [result.status for result in setup_results] == ["applied", "applied"]

        migration = MIGRATIONS_DIR / CONSOLIDATED_MIGRATION_NAME
        with patch.object(bootstrap_analytics, "_migration_files", return_value=[migration]):
            assert bootstrap_analytics.apply_migrations(service) == 1

        next_run = run_migrations.run_migrations(service, [migration])
        assert [(result.filename, result.status) for result in next_run] == [
            (CONSOLIDATED_MIGRATION_NAME, "skipped")
        ]

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT checksum_sha256 FROM schema_migrations WHERE filename = %s",
                    (CONSOLIDATED_MIGRATION_NAME,),
                )
                assert cursor.fetchone() == (
                    run_migrations.migration_checksum(migration.read_text(encoding="utf-8")),
                )
                cursor.execute(
                    """
                    SELECT to_regclass('public.measurement_aggregate_gaps'),
                           to_regclass('public.measurement_aggregates_usable')
                    """
                )
                assert cursor.fetchone() == (
                    "measurement_aggregate_gaps",
                    "measurement_aggregates_usable",
                )
    finally:
        database.drop()
