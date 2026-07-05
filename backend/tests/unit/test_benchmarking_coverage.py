from typing import Any
from unittest.mock import MagicMock

import pytest

from waittime.services.benchmarking import BenchmarkingService


class TestBenchmarkingServiceCoverage:
    """Targeted tests to increase coverage for benchmarking.py."""

    @pytest.fixture
    def service(self) -> BenchmarkingService:
        db = MagicMock()
        return BenchmarkingService(db)

    def test_compute_percentile(self, service: Any) -> None:
        """Test _compute_percentile."""
        # limit case
        assert service._compute_percentile(1, 0) == 0
        # rank 1 of 10 -> top 10%? No, method does rank/total.
        # 1/10 = 10th percentile.
        # Wait, usually rank 1 is best.
        # Code: int(round((rank / total) * 100))
        # 1/100 -> 1.
        # 1/1 -> 100.
        assert service._compute_percentile(1, 100) == 1
        assert service._compute_percentile(50, 100) == 50
        assert service._compute_percentile(100, 100) == 100
        # clamping
        assert service._compute_percentile(0, 100) == 1  # max(1, ...)
        assert service._compute_percentile(101, 100) == 100  # min(..., 100)

    def test_compute_quartile(self, service: Any) -> None:
        """Test _compute_quartile."""
        assert service._compute_quartile(10) == 1
        assert service._compute_quartile(25) == 1
        assert service._compute_quartile(26) == 2
        assert service._compute_quartile(50) == 2
        assert service._compute_quartile(51) == 3
        assert service._compute_quartile(75) == 3
        assert service._compute_quartile(76) == 4
        assert service._compute_quartile(100) == 4

    def test_compute_trend(self, service: Any) -> None:
        """Test _compute_trend."""
        assert service._compute_trend(100, None) == "stable"
        assert service._compute_trend(100, 0) == "stable"
        # (100 - 110) / 110 = -0.09 -> -9% -> improving (< -5)
        assert service._compute_trend(100, 110) == "improving"
        # (110 - 100) / 100 = 0.1 -> 10% -> worsening (> 5)
        assert service._compute_trend(110, 100) == "worsening"
        # (104 - 100) / 100 = 4% -> stable
        assert service._compute_trend(104, 100) == "stable"

    def test_compute_trend_change_percent(self, service: Any) -> None:
        """Test _compute_trend_change_percent."""
        assert service._compute_trend_change_percent(100, None) == 0.0
        assert service._compute_trend_change_percent(110, 100) == 10.0

    def test_period_label(self, service: Any) -> None:
        """Test _period_label."""
        assert service._period_label(1) == "24h"
        assert service._period_label(7) == "7d"

    def test_compute_summary_stats_empty(self, service: Any) -> None:
        """Test _compute_summary_stats with empty list."""
        stats = service._compute_summary_stats([])
        assert stats["mean"] is None

    def test_compute_summary_stats_values(self, service: Any) -> None:
        """Test _compute_summary_stats with values."""
        stats = service._compute_summary_stats([10, 20, 30])
        assert stats["mean"] == 20
        assert stats["min"] == 10
        assert stats["max"] == 30

    def test_compute_benchmarks_invalid_period(self, service: Any) -> None:
        """Test invalid period."""
        with pytest.raises(ValueError):
            service.compute_benchmarks("ON", period_days=0)

    def test_get_hospital_benchmark_not_found(self, service: Any) -> None:
        """Test get_hospital_benchmark when hospital not found."""
        # Mock _get_province_for_hospital to return None
        # Since it's an instance method that queries DB, we mock the DB result
        service.db.get_connection.return_value.__enter__.return_value = MagicMock()
        service.db.get_cursor.return_value.__enter__.return_value.fetchone.return_value = None

        with pytest.raises(ValueError, match="Hospital not found"):
            service.get_hospital_benchmark("h1")

    def test_compute_benchmarks_auto_ontology(self, service: Any) -> None:
        """Test compute_benchmarks when ontology must be determined."""
        # Mock _get_dominant_ontology DB query
        # And _query_benchmark_rows DB query

        # We need to distinguish calls.
        # First call: _get_dominant_ontology
        # Second call: _query_benchmark_rows

        mock_cursor = MagicMock()
        service.db.get_cursor.return_value.__enter__.return_value = mock_cursor

        # _get_dominant_ontology returns None (fallback to None? or error?)
        # Code: if not row: return None.
        # Then selected_ontology is None.
        # _query_benchmark_rows called with ontology=None.

        mock_cursor.fetchone.side_effect = [None, None]
        mock_cursor.fetchall.return_value = []

        result = service.compute_benchmarks("ON")
        assert result["hospital_count"] == 0
        assert result["ontology"] == {}

    def test_query_benchmark_rows_dynamic_sql(self, service: Any) -> None:
        """Test that _query_benchmark_rows constructs SQL correctly (coverage)."""
        from datetime import datetime

        # Exercise the dynamic SQL branch that applies ontology filters.
        ontology = {
            "metric_family": "MF",
            "start_event": "SE",
            "end_event": "EE",
            "statistic_type": "ST",
        }

        mock_cursor = MagicMock()
        service.db.get_cursor.return_value.__enter__.return_value = mock_cursor
        mock_cursor.fetchall.return_value = []

        service._query_benchmark_rows(
            "ON", datetime.now(), datetime.now(), datetime.now(), datetime.now(), ontology=ontology
        )
        # Verify execute was called (hitting the string formatting lines)
        assert mock_cursor.execute.called
