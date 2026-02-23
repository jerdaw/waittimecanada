from typing import Any
from unittest.mock import MagicMock, Mock

import pytest

from waittime.services.trends import SystemTrendService


class TestSystemTrendServiceCoverage:
    """Targeted tests to increase coverage for trends.py."""

    @pytest.fixture
    def service(self) -> SystemTrendService:
        db = MagicMock()
        return SystemTrendService(db)

    def test_weighted_mean_edge_cases(self, service: Any) -> None:
        """Test _weighted_mean static method edge cases."""
        # Empty inputs
        assert service._weighted_mean([], []) is None
        # Mismatched lengths
        assert service._weighted_mean([1], []) is None
        # Zero total weight
        assert service._weighted_mean([10], [0]) is None
        # Valid case
        assert service._weighted_mean([10, 20], [1, 1]) == 15.0

    def test_percent_change_edge_cases(self, service: Any) -> None:
        """Test _percent_change static method."""
        # Divide by zero protection
        assert service._percent_change(100, 0) == 0.0
        assert service._percent_change(100, -5) == 0.0
        # Normal
        assert service._percent_change(110, 100) == 10.0

    def test_classify_direction(self, service: Any) -> None:
        """Test _classify_direction."""
        assert service._classify_direction(-6.0) == "improving"
        assert service._classify_direction(6.0) == "worsening"
        assert service._classify_direction(4.0) == "stable"
        assert service._classify_direction(-4.0) == "stable"

    def test_lookback_label(self, service: Any) -> None:
        """Test _lookback_label."""
        assert service._lookback_label(12) == "1 year"
        assert service._lookback_label(6) == "6 months"

    def test_province_name(self, service: Any) -> None:
        """Test _province_name."""
        assert service._province_name("ON") == "Ontario"
        assert service._province_name("XX") == "XX"

    def test_generate_narrative_branches(self, service: Any) -> None:
        """Test narrative generation branches."""
        # Not enough data
        assert "Not enough data" in service.generate_narrative(
            "ON", "stable", 0.0, None, None, "6 months"
        )

        # Improving
        msg_imp = service.generate_narrative("ON", "improving", -10.0, 100.0, 90.0, "6 months")
        assert "decreased approximately 10.0%" in msg_imp

        # Worsening
        msg_wors = service.generate_narrative("ON", "worsening", 10.0, 90.0, 100.0, "6 months")
        assert "increased approximately 10.0%" in msg_wors

        # Stable
        msg_stable = service.generate_narrative("ON", "stable", 1.0, 100.0, 100.0, "6 months")
        assert "remained stable" in msg_stable

    def test_compute_quantile_edge_cases(self, service: Any) -> None:
        """Test _compute_quantile edge cases."""
        assert service._compute_quantile([], 0.9) == 0.0
        assert service._compute_quantile([10], 0.9) == 10.0
        # Simple interpolation
        # [10, 20], 0.5 -> 15.0
        assert service._compute_quantile([10.0, 20.0], 0.5) == 15.0

    def test_province_trend_invalid_inputs(self, service: Any) -> None:
        """Test input validation."""
        with pytest.raises(ValueError):
            service.province_trend("ON", period_type="daily")
        with pytest.raises(ValueError):
            service.province_trend("ON", lookback_months=0)

    def test_province_trend_empty_results(self, service: Any) -> None:
        """Test when no rows are returned."""
        service.db.get_connection.return_value.__enter__.return_value = Mock()
        service.db.get_cursor.return_value.__enter__.return_value.fetchall.return_value = []

        result = service.province_trend("ON")
        assert result["data_points"] == []
        assert result["trend_summary"]["direction"] == "stable"
