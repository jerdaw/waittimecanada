"""Pytest fixtures for integration tests.

Integration tests require a real PostgreSQL database connection.
Set DATABASE_URL environment variable to run these tests.
"""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path

import pytest
from native_postgres_archive import NativePostgresCluster, require_sanitized_database_environment
from psycopg2 import sql

from waittime.services.database import DatabaseService


def pytest_addoption(parser: pytest.Parser) -> None:
    group = parser.getgroup("isolated native PostgreSQL archive tests")
    group.addoption(
        "--run-native-archive-pg",
        action="store_true",
        default=False,
        help="explicitly enable the isolated native PostgreSQL 17 archive tests",
    )
    group.addoption(
        "--native-pg-bin-dir",
        type=Path,
        default=None,
        help="absolute directory containing the exact initdb, pg_ctl, and postgres binaries",
    )


@pytest.fixture(scope="session")
def native_pg_cluster(pytestconfig: pytest.Config) -> Generator[NativePostgresCluster, None, None]:
    """Start an owned socket-only cluster only after both explicit CLI gates."""
    if not pytestconfig.getoption("--run-native-archive-pg"):
        pytest.skip("native archive PostgreSQL tests require explicit coordinator-reviewed opt-in")
    binary_directory = pytestconfig.getoption("--native-pg-bin-dir")
    if binary_directory is None:
        raise pytest.UsageError(
            "--run-native-archive-pg requires --native-pg-bin-dir with an absolute PostgreSQL 17 bin path"
        )
    try:
        require_sanitized_database_environment(os.environ.keys())
    except RuntimeError as exc:
        raise pytest.UsageError(str(exc)) from exc
    cluster = NativePostgresCluster(binary_directory, explicitly_enabled=True)
    cluster.start()
    try:
        yield cluster
    finally:
        evidence_path = cluster.shutdown()
        if evidence_path is not None:
            reporter = pytestconfig.pluginmanager.get_plugin("terminalreporter")
            if reporter is not None:
                reporter.write_line(f"Native PostgreSQL archive evidence: {evidence_path}")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[object]):
    outcome = yield
    report = outcome.get_result()
    if item.get_closest_marker("native_postgres") is None:
        return
    cluster = item.funcargs.get("native_pg_cluster")
    if isinstance(cluster, NativePostgresCluster):
        cluster.record_test_result(item.name, report.when, report.outcome)


def _delete_if_table_exists(
    cur,
    table_name: str,
    where_sql: str,
    params: tuple[str, ...],
) -> None:
    cur.execute("SELECT to_regclass(%s) AS table_name", (table_name,))
    row = cur.fetchone()
    if row and row["table_name"] is not None:
        query = sql.SQL("DELETE FROM {table} WHERE {where_clause}").format(
            table=sql.Identifier(table_name),
            where_clause=sql.SQL(where_sql),
        )
        cur.execute(query, params)


@pytest.fixture(scope="session")
def database_url() -> str:
    """Get database URL from environment."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        pytest.skip("DATABASE_URL not set, skipping integration tests")
    return db_url


@pytest.fixture(scope="session")
def db_service(database_url: str) -> DatabaseService:
    """Create a DatabaseService instance for the test session."""
    return DatabaseService(database_url)


@pytest.fixture
def db_transaction(db_service: DatabaseService) -> Generator[DatabaseService, None, None]:
    """Provide a database service with transaction rollback.

    Each test gets a fresh transaction that is rolled back after the test,
    ensuring test isolation without affecting the database state.
    """
    conn = db_service.get_connection()
    conn.__enter__()  # Start transaction

    try:
        yield db_service
    finally:
        # Rollback transaction to clean up test data
        conn.__exit__(None, None, None)


@pytest.fixture
def clean_database(db_service: DatabaseService) -> Generator[DatabaseService, None, None]:
    """Provide a clean database by clearing test data before and after.

    WARNING: This fixture modifies the database. Use only with test databases.
    """
    # Clear any test data before test (delete in correct order due to foreign keys)
    with db_service.get_connection() as conn:
        with db_service.get_cursor(conn) as cur:
            _delete_if_table_exists(
                cur,
                "public_health_source_alert_state",
                "source_id LIKE %s",
                ("test-%",),
            )
            _delete_if_table_exists(
                cur,
                "public_health_system_metrics",
                "id LIKE %s",
                ("test-%",),
            )
            _delete_if_table_exists(cur, "public_health_alerts", "id LIKE %s", ("test-%",))
            _delete_if_table_exists(cur, "resource_locations", "id LIKE %s", ("test-%",))
            _delete_if_table_exists(cur, "public_data_sources", "source_id LIKE %s", ("test-%",))
            cur.execute("DELETE FROM measurements WHERE hospital_id LIKE 'test-%'")
            cur.execute("DELETE FROM hospitals WHERE id LIKE 'test-%'")
            cur.execute("DELETE FROM scraper_status WHERE source_id LIKE 'test-%'")
            cur.execute("DELETE FROM sources WHERE id LIKE 'test-%'")

    yield db_service

    # Clear test data after test (delete in correct order due to foreign keys)
    with db_service.get_connection() as conn:
        with db_service.get_cursor(conn) as cur:
            _delete_if_table_exists(
                cur,
                "public_health_source_alert_state",
                "source_id LIKE %s",
                ("test-%",),
            )
            _delete_if_table_exists(
                cur,
                "public_health_system_metrics",
                "id LIKE %s",
                ("test-%",),
            )
            _delete_if_table_exists(cur, "public_health_alerts", "id LIKE %s", ("test-%",))
            _delete_if_table_exists(cur, "resource_locations", "id LIKE %s", ("test-%",))
            _delete_if_table_exists(cur, "public_data_sources", "source_id LIKE %s", ("test-%",))
            cur.execute("DELETE FROM measurements WHERE hospital_id LIKE 'test-%'")
            cur.execute("DELETE FROM hospitals WHERE id LIKE 'test-%'")
            cur.execute("DELETE FROM scraper_status WHERE source_id LIKE 'test-%'")
            cur.execute("DELETE FROM sources WHERE id LIKE 'test-%'")
