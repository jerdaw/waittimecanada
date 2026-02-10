"""Tests for SystemTrendService."""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from waittime.services.trends import SystemTrendService


@pytest.fixture
def mock_db() -> Mock:
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def service(mock_db: Mock) -> SystemTrendService:
    """Create SystemTrendService with mocked database."""
    return SystemTrendService(mock_db)


@pytest.mark.unit
class TestSystemTrendService:
    """Unit tests for province-level trend computations."""

    def test_province_trend_monthly(self, service: SystemTrendService) -> None:
        """Should aggregate hospital rows into chronological province points."""
        service._query_period_rows = Mock(  # type: ignore[method-assign]
            return_value=[
                {
                    "hospital_id": "h1",
                    "period_start": datetime(2026, 1, 1, tzinfo=UTC),
                    "period_end": datetime(2026, 1, 31, tzinfo=UTC),
                    "mean_value": 100.0,
                    "min_value": 60.0,
                    "max_value": 180.0,
                    "sample_count": 200,
                    "metric_family": "wait_time",
                    "start_event": "triage",
                    "end_event": "nurse_seen",
                    "statistic_type": "mean",
                },
                {
                    "hospital_id": "h2",
                    "period_start": datetime(2026, 1, 1, tzinfo=UTC),
                    "period_end": datetime(2026, 1, 31, tzinfo=UTC),
                    "mean_value": 140.0,
                    "min_value": 80.0,
                    "max_value": 220.0,
                    "sample_count": 100,
                    "metric_family": "wait_time",
                    "start_event": "triage",
                    "end_event": "nurse_seen",
                    "statistic_type": "mean",
                },
                {
                    "hospital_id": "h1",
                    "period_start": datetime(2026, 2, 1, tzinfo=UTC),
                    "period_end": datetime(2026, 2, 28, tzinfo=UTC),
                    "mean_value": 120.0,
                    "min_value": 70.0,
                    "max_value": 200.0,
                    "sample_count": 210,
                    "metric_family": "wait_time",
                    "start_event": "triage",
                    "end_event": "nurse_seen",
                    "statistic_type": "mean",
                },
                {
                    "hospital_id": "h2",
                    "period_start": datetime(2026, 2, 1, tzinfo=UTC),
                    "period_end": datetime(2026, 2, 28, tzinfo=UTC),
                    "mean_value": 150.0,
                    "min_value": 90.0,
                    "max_value": 240.0,
                    "sample_count": 110,
                    "metric_family": "wait_time",
                    "start_event": "triage",
                    "end_event": "nurse_seen",
                    "statistic_type": "mean",
                },
            ]
        )

        result = service.province_trend("on", period_type="monthly", lookback_months=6)

        assert result["province"] == "ON"
        assert result["period"] == "monthly"
        assert result["lookback"] == "6 months"
        assert len(result["data_points"]) == 2

        jan = result["data_points"][0]
        feb = result["data_points"][1]

        assert jan["period_start"] == "2026-01-01"
        assert jan["province_mean"] == pytest.approx(113.3)
        assert jan["hospitals_reporting"] == 2
        assert jan["total_measurements"] == 300
        assert jan["range_min"] == 60.0
        assert jan["range_max"] == 220.0

        assert feb["period_start"] == "2026-02-01"
        assert feb["province_mean"] == pytest.approx(130.3)
        assert result["trend_summary"]["direction"] == "worsening"

    def test_trend_direction_improving(self) -> None:
        """Large negative change should be improving."""
        direction = SystemTrendService._classify_direction(-8.0)
        assert direction == "improving"

    def test_trend_direction_worsening(self) -> None:
        """Large positive change should be worsening."""
        direction = SystemTrendService._classify_direction(11.5)
        assert direction == "worsening"

    def test_trend_direction_stable(self) -> None:
        """Small change inside threshold should be stable."""
        direction = SystemTrendService._classify_direction(3.9)
        assert direction == "stable"

    def test_narrative_generation(self, service: SystemTrendService) -> None:
        """Narrative should include province, direction, and magnitudes."""
        narrative = service.generate_narrative(
            province="ON",
            direction="worsening",
            change_pct=12.4,
            start_mean=126.5,
            end_mean=142.3,
            lookback="6 months",
        )

        assert "Ontario ER wait times have increased" in narrative
        assert "12.4%" in narrative
        assert "126" in narrative
        assert "142" in narrative

    def test_weighted_mean(self) -> None:
        """Weighted mean should account for sample_count weighting."""
        result = SystemTrendService._weighted_mean(
            values=[100.0, 200.0],
            weights=[9, 1],
        )

        assert result == pytest.approx(110.0)

    def test_single_point_summary_stable(self, service: SystemTrendService) -> None:
        """One available period should produce stable summary with narrative."""
        single_point = [
            {
                "period_start": "2026-01-01",
                "period_end": "2026-01-31",
                "province_mean": 120.0,
                "province_median": 118.0,
                "province_p90": 140.0,
                "hospitals_reporting": 4,
                "total_measurements": 800,
                "range_min": 70.0,
                "range_max": 210.0,
            }
        ]

        summary = service._trend_summary(  # type: ignore[attr-defined]
            province="ON",
            data_points=single_point,
            lookback_months=3,
        )

        assert summary["direction"] == "stable"
        assert summary["change_percent"] == 0.0
        assert "remained stable" in summary["narrative"]
