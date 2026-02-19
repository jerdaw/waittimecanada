"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest markers."""
    # Ensure `backend/` is ahead of repo root on sys.path so imports like
    # `scripts.*` resolve to `backend/scripts/*` (not the repo-root `scripts/`).
    backend_dir = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(backend_dir))

    config.addinivalue_line("markers", "unit: Fast tests with no I/O")
    config.addinivalue_line("markers", "integration: Tests with database or HTTP")
    config.addinivalue_line("markers", "e2e: End-to-end workflow tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
