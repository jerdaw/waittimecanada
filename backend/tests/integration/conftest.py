"""Pytest fixtures for integration tests.

Integration tests require a real PostgreSQL database connection.
Set DATABASE_URL environment variable to run these tests.
"""

import os
from collections.abc import Generator

import pytest
from psycopg2 import sql

from waittime.services.database import DatabaseService


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
            _delete_if_table_exists(cur, "public_health_alerts", "id LIKE %s", ("test-%",))
            _delete_if_table_exists(cur, "resource_locations", "id LIKE %s", ("test-%",))
            _delete_if_table_exists(cur, "public_data_sources", "source_id LIKE %s", ("test-%",))
            cur.execute("DELETE FROM measurements WHERE hospital_id LIKE 'test-%'")
            cur.execute("DELETE FROM hospitals WHERE id LIKE 'test-%'")
            cur.execute("DELETE FROM scraper_status WHERE source_id LIKE 'test-%'")
            cur.execute("DELETE FROM sources WHERE id LIKE 'test-%'")
