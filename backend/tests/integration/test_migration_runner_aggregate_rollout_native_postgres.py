"""Exercise aggregate migrations through the real runner on isolated PostgreSQL."""

from __future__ import annotations

import importlib.util
import sys
from collections.abc import Callable, Generator, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import psycopg2
import pytest
from native_postgres_archive import NativePostgresDatabase

from waittime.services.database import DatabaseService

pytestmark = [pytest.mark.integration, pytest.mark.native_postgres]

RUNNER_PATH = Path(__file__).resolve().parents[2] / "run_migrations.py"
SPEC = importlib.util.spec_from_file_location("native_test_run_migrations", RUNNER_PATH)
assert SPEC is not None
assert SPEC.loader is not None
run_migrations = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_migrations
SPEC.loader.exec_module(run_migrations)

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
AGGREGATE_MIGRATION_NAMES = (
    "006_create_measurement_aggregates.sql",
    "015_add_metric_family_to_aggregates.sql",
    "023_add_measurement_aggregate_gaps.sql",
    "024_add_aggregate_verification_state.sql",
)
LEGACY_PERIOD_START = "2020-01-02T00:00:00+00:00"


class CommitObservingDatabase(DatabaseService):
    """Use real owned test connections and observe after each committed runner scope."""

    def __init__(
        self,
        database: NativePostgresDatabase,
        after_commit: Callable[[int], None],
    ) -> None:
        super().__init__(database_url="native-test-only")
        self.database = database
        self.after_commit = after_commit
        self.connection_scopes = 0

    @contextmanager
    def get_connection(self, *, connect_timeout: int | None = None) -> Generator[Any, None, None]:
        del connect_timeout  # The native harness bounds connection setup itself.
        self.connection_scopes += 1
        scope_number = self.connection_scopes
        with self.database.admin_connection() as connection:
            yield connection
        self.after_commit(scope_number)


def _insert_legacy_aggregate(database: NativePostgresDatabase) -> None:
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO measurement_aggregates (
                    hospital_id, source_id, period_type, period_start, period_end,
                    mean_value, min_value, max_value, sample_count, metric_family,
                    start_event, end_event, statistic_type
                ) VALUES (
                    'wtc-native-hospital', 'wtc-native-source', 'daily', %s,
                    %s::timestamptz, 45.0, 40.0, 50.0, 1, 'TIME_TO_PROVIDER',
                    'TRIAGE', 'PHYSICIAN', 'P90'
                )
                """,
                (LEGACY_PERIOD_START, "2020-01-03T00:00:00+00:00"),
            )


def _usable_legacy_count(database: NativePostgresDatabase) -> int:
    with database.admin_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM measurement_aggregates_usable
                WHERE hospital_id = 'wtc-native-hospital'
                  AND period_start = %s::timestamptz
                """,
                (LEGACY_PERIOD_START,),
            )
            row = cursor.fetchone()
            assert row is not None
            return int(row[0])


def _run_real_aggregate_migrations(
    database: NativePostgresDatabase,
    after_commit: Callable[[int], None],
    migration_paths: Sequence[Path],
) -> tuple[list[Any], CommitObservingDatabase]:
    service = CommitObservingDatabase(database, after_commit)
    results = run_migrations.run_migrations(service, migration_paths)
    return results, service


def test_runner_commits_023_before_024_and_rolls_back_failed_024(
    native_pg_cluster,
    tmp_path: Path,
) -> None:
    """Capture the live 023-only view and prove 024's failure is file-local."""
    database = native_pg_cluster.create_database()
    try:
        migration_paths = [MIGRATIONS_DIR / name for name in AGGREGATE_MIGRATION_NAMES]
        failing_024 = tmp_path / AGGREGATE_MIGRATION_NAMES[-1]
        failing_024.write_text(
            migration_paths[-1].read_text(encoding="utf-8") + "\nSELECT 1 / 0;\n",
            encoding="utf-8",
        )

        visible_after_023: list[int] = []

        def observe_commits(scope_number: int) -> None:
            if scope_number == 3:
                # Runner scopes are ledger, 006, 015, 023, 024. This legacy row
                # exists before the safety view is introduced by migration 023.
                _insert_legacy_aggregate(database)
            elif scope_number == 4:
                visible_after_023.append(_usable_legacy_count(database))

        with pytest.raises(psycopg2.errors.DivisionByZero):
            _run_real_aggregate_migrations(
                database,
                observe_commits,
                [*migration_paths[:-1], failing_024],
            )

        # A separate native connection observed the actual post-commit schema,
        # not an uncommitted view within the migration transaction.
        assert visible_after_023 == [1]

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT filename
                    FROM schema_migrations
                    WHERE filename IN (%s, %s)
                    ORDER BY filename
                    """,
                    (AGGREGATE_MIGRATION_NAMES[2], AGGREGATE_MIGRATION_NAMES[3]),
                )
                assert cursor.fetchall() == [(AGGREGATE_MIGRATION_NAMES[2],)]
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'measurement_aggregates'
                      AND column_name = 'verification_state'
                    """
                )
                assert cursor.fetchone() == (0,)

        # 023 is durable and its view still exposes the legacy row after 024's
        # DDL and ledger insert roll back together.
        assert _usable_legacy_count(database) == 1

        # Apply the unmodified final migration through the same real runner.
        _, successful_runner = _run_real_aggregate_migrations(
            database,
            lambda _scope_number: None,
            [migration_paths[-1]],
        )
        assert successful_runner.connection_scopes == 2

        with database.admin_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT verification_state
                    FROM measurement_aggregates
                    WHERE hospital_id = 'wtc-native-hospital'
                      AND period_start = %s::timestamptz
                    """,
                    (LEGACY_PERIOD_START,),
                )
                assert cursor.fetchone() == ("legacy_unverified",)

        assert _usable_legacy_count(database) == 0
    finally:
        database.drop()
