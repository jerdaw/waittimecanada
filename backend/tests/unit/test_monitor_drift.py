"""Unit tests for the monitor_drift.py script.

Tests the run_drift_check() function in isolation using mocks,
without requiring a real database connection.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# We test the function directly, not via subprocess
from scripts.monitor_drift import run_drift_check


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock DatabaseService."""
    return MagicMock()


@pytest.fixture
def mock_detector() -> MagicMock:
    """Mock MethodologyChangeDetector."""
    return MagicMock()


class TestRunDriftCheck:
    """Tests for run_drift_check()."""

    @pytest.mark.unit
    def test_no_database_url_returns_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Missing DATABASE_URL should return exit code 1."""
        monkeypatch.delenv("DATABASE_URL", raising=False)

        result = run_drift_check()

        assert result == 1

    @pytest.mark.unit
    def test_no_sources_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """No sources to check should return exit code 0."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

        with (
            patch("scripts.monitor_drift.DatabaseService"),
            patch("scripts.monitor_drift.MethodologyChangeDetector") as mock_det_cls,
        ):
            mock_det = mock_det_cls.return_value
            mock_det.check_all_sources.return_value = []

            result = run_drift_check()

        assert result == 0

    @pytest.mark.unit
    def test_all_stable_returns_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """All sources stable should return exit code 0."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

        stable_results: list[dict[str, Any]] = [
            {"source_id": "ca-on-oh", "change_detected": False, "details": None},
            {"source_id": "ca-qc-msss", "change_detected": False, "details": None},
        ]

        with (
            patch("scripts.monitor_drift.DatabaseService"),
            patch("scripts.monitor_drift.MethodologyChangeDetector") as mock_det_cls,
        ):
            mock_det = mock_det_cls.return_value
            mock_det.check_all_sources.return_value = stable_results

            result = run_drift_check()

        assert result == 0

    @pytest.mark.unit
    def test_drift_detected_fail_on_change_true_returns_one(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Drift detected with fail_on_change=True should return exit code 1."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

        drift_results: list[dict[str, Any]] = [
            {
                "source_id": "ca-on-oh",
                "change_detected": True,
                "details": {
                    "shift_percent": 30.0,
                    "hospitals_analyzed": 6,
                    "explanation": "Province-wide mean increased by 30.0%",
                },
            }
        ]

        with (
            patch("scripts.monitor_drift.DatabaseService"),
            patch("scripts.monitor_drift.MethodologyChangeDetector") as mock_det_cls,
        ):
            mock_det = mock_det_cls.return_value
            mock_det.check_all_sources.return_value = drift_results

            result = run_drift_check(fail_on_change=True)

        assert result == 1

    @pytest.mark.unit
    def test_drift_detected_fail_on_change_false_returns_zero(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Drift detected with fail_on_change=False should still return exit code 0."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

        drift_results: list[dict[str, Any]] = [
            {
                "source_id": "ca-on-oh",
                "change_detected": True,
                "details": {
                    "shift_percent": 25.0,
                    "hospitals_analyzed": 5,
                    "explanation": "Province-wide mean increased by 25.0%",
                },
            }
        ]

        with (
            patch("scripts.monitor_drift.DatabaseService"),
            patch("scripts.monitor_drift.MethodologyChangeDetector") as mock_det_cls,
        ):
            mock_det = mock_det_cls.return_value
            mock_det.check_all_sources.return_value = drift_results

            result = run_drift_check(fail_on_change=False)

        assert result == 0

    @pytest.mark.unit
    def test_mixed_results_drift_detected_fail_on_change(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Mixed results with one drift source should still trigger fail_on_change."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

        mixed_results: list[dict[str, Any]] = [
            {"source_id": "ca-on-oh", "change_detected": False, "details": None},
            {
                "source_id": "ca-qc-msss",
                "change_detected": True,
                "details": {
                    "shift_percent": -22.0,
                    "hospitals_analyzed": 8,
                    "explanation": "Province-wide mean decreased by 22.0%",
                },
            },
            {"source_id": "ca-ab-ahs", "change_detected": False, "details": None},
        ]

        with (
            patch("scripts.monitor_drift.DatabaseService"),
            patch("scripts.monitor_drift.MethodologyChangeDetector") as mock_det_cls,
        ):
            mock_det = mock_det_cls.return_value
            mock_det.check_all_sources.return_value = mixed_results

            result = run_drift_check(fail_on_change=True)

        assert result == 1

    @pytest.mark.unit
    def test_detector_exception_returns_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Unhandled exception from detector should return exit code 1."""
        monkeypatch.setenv("DATABASE_URL", "postgresql://fake/db")

        with (
            patch("scripts.monitor_drift.DatabaseService"),
            patch("scripts.monitor_drift.MethodologyChangeDetector") as mock_det_cls,
        ):
            mock_det = mock_det_cls.return_value
            mock_det.check_all_sources.side_effect = RuntimeError("DB connection failed")

            result = run_drift_check()

        assert result == 1
