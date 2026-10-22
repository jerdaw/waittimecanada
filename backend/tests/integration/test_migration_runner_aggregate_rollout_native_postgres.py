"""Exercise atomic aggregate migration application through the real runner."""

from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, cast

import psycopg2
import pytest
from native_postgres_archive import (  # type: ignore[import-untyped]
    NativePostgresCluster,
    NativePostgresDatabase,
)
from psycopg2.extensions import make_dsn

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
