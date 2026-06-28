from datetime import date, timedelta
from unittest.mock import MagicMock, Mock

import pytest

from waittime.services.quality_diff import QualityDiffService


@pytest.fixture
def mock_conn():
    conn = Mock()
    cursor = MagicMock()
    conn.cursor.return_value = cursor
    cursor.__enter__.return_value = cursor
    return conn


@pytest.fixture
def service(mock_conn):
    return QualityDiffService(mock_conn)


def _mock_trend_rows(cursor, rows: list[tuple]):
    # description is a sequence of 7-item sequences. We only care about the first item (column name)
    cursor.description = [
        ("snapshot_date",),
        ("source_id",),
        ("hospitals_snapshotted",),
        ("avg_success_rate",),
        ("min_success_rate",),
        ("hospitals_critical",),
        ("worst_gap_minutes",),
    ]
    cursor.fetchall.return_value = rows


class TestQualityDiffService:
    def test_get_source_trend_returns_daily_rows(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        _mock_trend_rows(
            cursor,
            [
                (today, "ontario-er", 100, 0.95, 0.8, 5, 120),
                (today - timedelta(days=1), "ontario-er", 100, 0.94, 0.7, 6, 130),
            ],
        )

        trend = service.get_source_trend("ontario-er", days=30)

        assert len(trend) == 2
        assert trend[0]["snapshot_date"] == today
        assert trend[0]["avg_success_rate"] == 0.95

        # Verify SQL execution
        call_args = cursor.execute.call_args
        assert call_args is not None
        query, params = call_args[0]
        assert "data_quality_snapshots" in query
        assert params == ("ontario-er", 30)

    def test_get_source_trend_empty_when_no_snapshots(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        _mock_trend_rows(cursor, [])
        trend = service.get_source_trend("ontario-er")
        assert len(trend) == 0

    def test_get_source_diff_improved(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        # Mocking get_source_trend which requests compare_days + 1
        _mock_trend_rows(
            cursor,
            [
                (today, "ontario-er", 105, 0.96, 0.85, 2, 90),  # Current
                (
                    today - timedelta(days=7),
                    "ontario-er",
                    100,
                    0.80,
                    0.5,
                    10,
                    240,
                ),  # Baseline (7 days ago)
            ],
        )

        diff = service.get_source_diff("ontario-er", compare_days=7)

        assert diff["has_baseline"] is True
        assert diff["deltas"]["success_rate_delta"] == pytest.approx(0.16)
        assert diff["deltas"]["hospitals_reporting_delta"] == 5
        assert diff["deltas"]["worst_gap_delta"] == -150

        assert "Coverage improved by 16.0%" in diff["summary"]
        assert "delta: +5" in diff["summary"]

    def test_get_source_diff_degraded(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        _mock_trend_rows(
            cursor,
            [
                (today, "ontario-er", 100, 0.80, 0.5, 10, 240),  # Current
                (today - timedelta(days=7), "ontario-er", 100, 0.95, 0.8, 5, 120),  # Baseline
            ],
        )

        diff = service.get_source_diff("ontario-er", compare_days=7)

        assert diff["has_baseline"] is True
        assert diff["deltas"]["success_rate_delta"] == pytest.approx(-0.15)
        assert "Coverage degraded by 15.0%" in diff["summary"]

    def test_get_source_diff_stable_when_success_delta_is_below_threshold(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        _mock_trend_rows(
            cursor,
            [
                (today, "ontario-er", 100, 0.951, 0.8, 0, 120),  # Current
                (
                    today - timedelta(days=7),
                    "ontario-er",
                    100,
                    0.95,
                    0.8,
                    0,
                    120,
                ),  # Baseline
            ],
        )

        diff = service.get_source_diff("ontario-er", compare_days=7)

        assert diff["has_baseline"] is True
        assert diff["deltas"]["success_rate_delta"] == pytest.approx(0.001)
        assert diff["deltas"]["hospitals_reporting_delta"] == 0
        assert diff["deltas"]["worst_gap_delta"] == 0
        assert "Coverage stable" in diff["summary"]

    def test_get_source_diff_handles_null_gap_values(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        _mock_trend_rows(
            cursor,
            [
                (today, "ontario-er", 100, 0.95, 0.8, 0, None),  # Current
                (
                    today - timedelta(days=7),
                    "ontario-er",
                    100,
                    0.95,
                    0.8,
                    0,
                    None,
                ),  # Baseline
            ],
        )

        diff = service.get_source_diff("ontario-er", compare_days=7)

        assert diff["current_metrics"]["worst_gap_minutes"] == 0.0
        assert diff["baseline_metrics"]["worst_gap_minutes"] == 0.0
        assert diff["deltas"]["worst_gap_delta"] == 0.0
        assert "Coverage stable" in diff["summary"]

    def test_get_source_diff_handles_zero_baseline_values(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        _mock_trend_rows(
            cursor,
            [
                (today, "ontario-er", 0, 0.0, 0.0, 0, 0),  # Current
                (
                    today - timedelta(days=7),
                    "ontario-er",
                    0,
                    0.0,
                    0.0,
                    0,
                    0,
                ),  # Baseline
            ],
        )

        diff = service.get_source_diff("ontario-er", compare_days=7)

        assert diff["has_baseline"] is True
        assert diff["baseline_metrics"]["avg_success_rate"] == 0.0
        assert diff["current_metrics"]["avg_success_rate"] == 0.0
        assert diff["deltas"]["success_rate_delta"] == 0.0
        assert diff["deltas"]["hospitals_reporting_delta"] == 0
        assert "Coverage stable" in diff["summary"]

    def test_get_source_diff_no_baseline(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        # Trend returns nothing
        _mock_trend_rows(cursor, [])
        diff = service.get_source_diff("ontario-er", compare_days=7)
        assert diff["has_baseline"] is False

    def test_get_source_diff_insufficient_history(self, service, mock_conn):
        cursor = mock_conn.cursor.return_value.__enter__.return_value
        today = date(2026, 2, 19)
        # Trend returns only 1 row (current day), so baseline == current
        _mock_trend_rows(cursor, [(today, "ontario-er", 100, 0.95, 0.8, 5, 120)])
        diff = service.get_source_diff("ontario-er", compare_days=7)
        assert diff["has_baseline"] is False
        assert "Insufficient historical snapshot data" in diff["summary"]
