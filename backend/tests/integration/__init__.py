"""Integration tests for Wait Time Canada.

These tests verify the full stack with real database interactions.
They require a PostgreSQL database connection via DATABASE_URL environment variable.

To run only integration tests:
    pytest -m integration

To skip integration tests:
    pytest -m "not integration"
"""
