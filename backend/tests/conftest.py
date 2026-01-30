"""Pytest configuration and shared fixtures."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Fast tests with no I/O")
    config.addinivalue_line("markers", "integration: Tests with database or HTTP")
    config.addinivalue_line("markers", "e2e: End-to-end workflow tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
