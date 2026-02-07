"""Tests for BenchmarkingService."""

from unittest.mock import Mock

import pytest

from waittime.services.benchmarking import BenchmarkingService


@pytest.fixture
def mock_db() -> Mock:
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def service(mock_db: Mock) -> BenchmarkingService:
    """Create BenchmarkingService with mocked database."""
    return BenchmarkingService(mock_db)


@pytest.mark.unit
class TestBenchmarkingService:
    """Unit tests for benchmark ranking and trend logic."""

    def test_compute_benchmarks_basic(self, service: BenchmarkingService) -> None:
        """Should rank hospitals by shorter period mean and compute quartiles/trends."""
        service._query_benchmark_rows = Mock(  # type: ignore[method-assign]
            return_value=[
                {
                    "hospital_id": "h1",
                    "hospital_name": "Hospital 1",
                    "city": "Ottawa",
                    "current_wait": 120.0,
                    "period_mean": 120.0,
                    "previous_period_mean": 140.0,
                },
                {
                    "hospital_id": "h2",
                    "hospital_name": "Hospital 2",
                    "city": "Ottawa",
                    "current_wait": 90.0,
                    "period_mean": 90.0,
                    "previous_period_mean": 89.0,
                },
                {
                    "hospital_id": "h3",
                    "hospital_name": "Hospital 3",
                    "city": "Toronto",
                    "current_wait": 200.0,
                    "period_mean": 200.0,
                    "previous_period_mean": 150.0,
                },
                {
                    "hospital_id": "h4",
                    "hospital_name": "Hospital 4",
                    "city": "Hamilton",
                    "current_wait": 110.0,
                    "period_mean": 110.0,
                    "previous_period_mean": 110.0,
                },
                {
                    "hospital_id": "h5",
                    "hospital_name": "Hospital 5",
                    "city": "London",
                    "current_wait": 75.0,
                    "period_mean": 75.0,
                    "previous_period_mean": 100.0,
                },
            ]
        )

        result = service.compute_benchmarks("on", period_days=7)

        assert result["province"] == "ON"
        assert result["period"] == "7d"
        assert result["hospital_count"] == 5

        hospital_ids = [hospital["hospital_id"] for hospital in result["hospitals"]]
        assert hospital_ids == ["h5", "h2", "h4", "h1", "h3"]

        # Rank 1 of 5 => 20th percentile, Q1
        assert result["hospitals"][0]["percentile"] == 20
        assert result["hospitals"][0]["quartile"] == 1
        assert result["hospitals"][0]["trend"] == "improving"

        # h3 worsened by >5%
        h3 = next(h for h in result["hospitals"] if h["hospital_id"] == "h3")
        assert h3["trend"] == "worsening"
        assert h3["trend_change_percent"] == 33.3

        # Province-level summary exists
        stats = result["province_stats"]
        assert stats["mean"] is not None
        assert stats["median"] is not None
        assert stats["p25"] is not None
        assert stats["p75"] is not None

    def test_compute_benchmarks_ignores_hospitals_without_period_mean(
        self, service: BenchmarkingService
    ) -> None:
        """Hospitals without aggregates in the window should be excluded from ranking."""
        service._query_benchmark_rows = Mock(  # type: ignore[method-assign]
            return_value=[
                {
                    "hospital_id": "h1",
                    "hospital_name": "Hospital 1",
                    "city": "Ottawa",
                    "current_wait": 120.0,
                    "period_mean": None,
                    "previous_period_mean": None,
                },
                {
                    "hospital_id": "h2",
                    "hospital_name": "Hospital 2",
                    "city": "Toronto",
                    "current_wait": 95.0,
                    "period_mean": 95.0,
                    "previous_period_mean": 96.0,
                },
            ]
        )

        result = service.compute_benchmarks("ON", period_days=7)

        assert result["hospital_count"] == 1
        assert result["hospitals"][0]["hospital_id"] == "h2"

    def test_percentile_calculation(self) -> None:
        """Rank 1 of 10 should be 10th percentile."""
        assert BenchmarkingService._compute_percentile(rank=1, total=10) == 10

    def test_quartile_assignment(self) -> None:
        """Quartiles should follow inclusive 25-point boundaries."""
        assert BenchmarkingService._compute_quartile(25) == 1
        assert BenchmarkingService._compute_quartile(26) == 2
        assert BenchmarkingService._compute_quartile(50) == 2
        assert BenchmarkingService._compute_quartile(51) == 3
        assert BenchmarkingService._compute_quartile(75) == 3
        assert BenchmarkingService._compute_quartile(76) == 4

    def test_trend_improving(self) -> None:
        """Large decrease in mean should be classified as improving."""
        trend = BenchmarkingService._compute_trend(current_mean=90.0, previous_mean=100.0)
        assert trend == "improving"

    def test_trend_stable(self) -> None:
        """Small movement within threshold should be stable."""
        trend = BenchmarkingService._compute_trend(current_mean=103.0, previous_mean=100.0)
        assert trend == "stable"

    def test_trend_worsening(self) -> None:
        """Large increase in mean should be classified as worsening."""
        trend = BenchmarkingService._compute_trend(current_mean=110.0, previous_mean=100.0)
        assert trend == "worsening"

    def test_get_hospital_benchmark(self, service: BenchmarkingService) -> None:
        """Should return benchmark payload scoped to one hospital."""
        service._get_province_for_hospital = Mock(return_value="ON")  # type: ignore[method-assign]
        service._query_benchmark_rows = Mock(  # type: ignore[method-assign]
            return_value=[
                {
                    "hospital_id": "h1",
                    "hospital_name": "Hospital 1",
                    "city": "Ottawa",
                    "current_wait": 90.0,
                    "period_mean": 90.0,
                    "previous_period_mean": 100.0,
                },
                {
                    "hospital_id": "h2",
                    "hospital_name": "Hospital 2",
                    "city": "Ottawa",
                    "current_wait": 130.0,
                    "period_mean": 130.0,
                    "previous_period_mean": 120.0,
                },
            ]
        )

        result = service.get_hospital_benchmark("h2", period_days=7)

        assert result["province"] == "ON"
        assert result["hospital_count"] == 2
        assert result["hospital"]["hospital_id"] == "h2"
        assert result["hospital"]["trend"] == "worsening"
