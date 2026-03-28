"""Tests for DataQualityService.

Covers hospital quality computation, gap detection, source quality,
system quality, coverage timeline, and snapshot caching.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from waittime.services.data_quality import DataQualityService


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def service(mock_db):
    """Create a DataQualityService with mock DB."""
    return DataQualityService(mock_db)


def _make_timestamps(day: datetime, count: int, interval_minutes: int = 60):
    """Generate evenly-spaced timestamps starting from day_start."""
    start = datetime(day.year, day.month, day.day, tzinfo=UTC)
    return [start + timedelta(minutes=i * interval_minutes) for i in range(count)]


class TestComputeHospitalQuality:
    """Tests for compute_hospital_quality()."""

    @pytest.mark.unit
    def test_full_coverage(self, service, mock_db):
        """24/24 scrapes yields success_rate=1.0, no gaps."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        timestamps = _make_timestamps(day, 24, interval_minutes=60)
        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.compute_hospital_quality("ca-on-test", day)

        assert result["hospital_id"] == "ca-on-test"
        assert result["expected_scrapes"] == 24
        assert result["actual_scrapes"] == 24
        assert result["success_rate"] == 1.0
        assert result["gaps"] == []
        assert result["longest_gap_minutes"] is None
        assert result["mean_gap_minutes"] is None

    @pytest.mark.unit
    def test_partial_coverage(self, service, mock_db):
        """18/24 scrapes yields 0.75 success rate."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        timestamps = _make_timestamps(day, 18, interval_minutes=60)
        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.compute_hospital_quality("ca-on-test", day)

        assert result["actual_scrapes"] == 18
        assert result["success_rate"] == 18 / 24
        # Should have at least one gap (from last timestamp to end of day)
        assert len(result["gaps"]) >= 1

    @pytest.mark.unit
    def test_no_data(self, service, mock_db):
        """0 scrapes yields success_rate=0.0 and one full-day gap."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        mock_db.get_measurement_timestamps.return_value = []

        result = service.compute_hospital_quality("ca-on-test", day)

        assert result["actual_scrapes"] == 0
        assert result["success_rate"] == 0.0
        assert len(result["gaps"]) == 1
        assert result["gaps"][0]["duration_minutes"] == 1440  # 24 hours

    @pytest.mark.unit
    def test_over_count_capped_at_one(self, service, mock_db):
        """More than 24 scrapes still caps success_rate at 1.0."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        timestamps = _make_timestamps(day, 30, interval_minutes=30)
        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.compute_hospital_quality("ca-on-test", day)

        assert result["actual_scrapes"] == 30
        assert result["success_rate"] == 1.0


class TestGapDetection:
    """Tests for _compute_gaps() and gap analysis."""

    @pytest.mark.unit
    def test_single_gap(self, service, mock_db):
        """Missing data from 02:00-05:00 should be detected as one gap."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        start = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)

        # Create timestamps with a 3-hour gap (02:00-05:00)
        timestamps = []
        # 00:00 to 01:00 (2 measurements)
        for i in range(2):
            timestamps.append(start + timedelta(minutes=i * 60))
        # Skip 02:00-04:00
        # 05:00 onward (19 measurements)
        for i in range(19):
            timestamps.append(start + timedelta(hours=5 + i))

        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.compute_hospital_quality("ca-on-test", day)

        # With hourly measurements, the detected gap spans from 01:00 to 05:00.
        gap_durations = [g["duration_minutes"] for g in result["gaps"]]
        assert any(230 <= d <= 250 for d in gap_durations), (
            f"Expected a ~240 min gap, got durations: {gap_durations}"
        )

    @pytest.mark.unit
    def test_multiple_gaps(self, service, mock_db):
        """Multiple gaps should all be detected."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        start = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)

        # Measurements at: 00:00, 01:00, 04:00, 05:00
        timestamps = [
            start,
            start + timedelta(hours=1),
            start + timedelta(hours=4),
            start + timedelta(hours=5),
        ]
        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.compute_hospital_quality("ca-on-test", day)

        # Should have multiple gaps
        assert len(result["gaps"]) >= 2
        assert result["longest_gap_minutes"] is not None
        assert result["mean_gap_minutes"] is not None

    @pytest.mark.unit
    def test_no_gaps_with_regular_interval(self):
        """Evenly spaced timestamps below threshold produce no gaps."""
        day_start = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)
        timestamps = _make_timestamps(datetime(2026, 2, 1, tzinfo=UTC), 24, 60)

        gaps = DataQualityService._compute_gaps(timestamps, day_start, day_end)
        assert gaps == []

    @pytest.mark.unit
    def test_gap_from_start_of_day(self):
        """Late first measurement creates a gap from day start."""
        day_start = datetime(2026, 2, 1, 0, 0, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)

        # First measurement at 02:00
        timestamps = [day_start + timedelta(hours=2)]

        gaps = DataQualityService._compute_gaps(timestamps, day_start, day_end)

        # Should have gap from 00:00 to 02:00
        assert len(gaps) >= 1
        assert gaps[0]["duration_minutes"] == 120


class TestComputeSourceQuality:
    """Tests for compute_source_quality()."""

    @pytest.mark.unit
    def test_source_quality_with_hospitals(self, service, mock_db):
        """Source quality aggregates across hospitals."""
        start = datetime(2026, 2, 1, tzinfo=UTC)
        end = datetime(2026, 2, 2, tzinfo=UTC)

        mock_hospital_1 = Mock()
        mock_hospital_1.id = "ca-on-hosp-1"
        mock_hospital_2 = Mock()
        mock_hospital_2.id = "ca-on-hosp-2"
        mock_db.get_hospitals_by_source.return_value = [
            mock_hospital_1,
            mock_hospital_2,
        ]

        # Total counts: 24 + 12 = 36 out of 2 * 24 = 48 expected
        mock_db.get_measurement_count_by_hospital.return_value = {
            "ca-on-hosp-1": 24,
            "ca-on-hosp-2": 12,
        }
        # Mock onboarding dates (all hospitals active before period start)
        mock_db.get_hospital_onboarding_dates.return_value = {
            "ca-on-hosp-1": start - timedelta(days=1),
            "ca-on-hosp-2": start - timedelta(days=1),
        }

        result = service.compute_source_quality("ontario-er", start, end)

        assert result["source_id"] == "ontario-er"
        assert result["total_hospitals"] == 2
        assert result["total_expected"] == 48
        assert result["total_actual"] == 36
        assert result["overall_success_rate"] == 36 / 48
        assert result["hospitals_with_data_today"] == 2
        assert result["coverage_rate"] == 1.0

    @pytest.mark.unit
    def test_source_quality_no_hospitals(self, service, mock_db):
        """Source with no hospitals yields zero metrics."""
        start = datetime(2026, 2, 1, tzinfo=UTC)
        end = datetime(2026, 2, 2, tzinfo=UTC)

        mock_db.get_hospitals_by_source.return_value = []
        mock_db.get_measurement_count_by_hospital.return_value = {}
        mock_db.get_hospital_onboarding_dates.return_value = {}

        result = service.compute_source_quality("empty-source", start, end)

        assert result["total_hospitals"] == 0
        assert result["total_expected"] == 0
        assert result["overall_success_rate"] == 0.0
        assert result["coverage_rate"] == 0.0

    @pytest.mark.unit
    def test_source_quality_partial_coverage(self, service, mock_db):
        """Only some hospitals reporting data."""
        start = datetime(2026, 2, 1, tzinfo=UTC)
        end = datetime(2026, 2, 2, tzinfo=UTC)

        mock_hospitals = [Mock() for _ in range(4)]
        for i, h in enumerate(mock_hospitals):
            h.id = f"hosp-{i}"
        mock_db.get_hospitals_by_source.return_value = mock_hospitals

        # Only 2 out of 4 hospitals have data
        mock_db.get_measurement_count_by_hospital.return_value = {
            "hosp-0": 20,
            "hosp-2": 18,
        }
        # All hospitals onboarded early
        mock_db.get_hospital_onboarding_dates.return_value = {
            f"hosp-{i}": start - timedelta(days=1) for i in range(4)
        }

        result = service.compute_source_quality("test-source", start, end)

        assert result["hospitals_with_data_today"] == 2
        assert result["total_hospitals"] == 4
        assert result["coverage_rate"] == 0.5


class TestComputeSystemQuality:
    """Tests for compute_system_quality()."""

    @pytest.mark.unit
    def test_healthy_system(self, service, mock_db):
        """All sources above 95% yields 'healthy'."""
        mock_db.get_all_source_ids.return_value = ["ontario-health"]

        mock_hospitals = [Mock()]
        mock_hospitals[0].id = "h-1"
        mock_db.get_hospitals_by_source.return_value = mock_hospitals
        mock_db.get_measurement_count_by_hospital.return_value = {"h-1": 24}

        # Mock onboarding date
        mock_db.get_hospital_onboarding_dates.return_value = {
            "h-1": datetime(2025, 1, 1, tzinfo=UTC)
        }

        mock_source = Mock()
        mock_source.province = "ON"
        mock_db.get_source.return_value = mock_source
        mock_db.get_stale_scrapers.return_value = []

        result = service.compute_system_quality()

        assert result["overall_status"] == "healthy"
        assert len(result["sources"]) == 1

    @pytest.mark.unit
    def test_critical_system(self, service, mock_db):
        """Sources below 80% yields 'critical'."""
        mock_db.get_all_source_ids.return_value = ["quebec-msss"]

        mock_hospitals = [Mock()]
        mock_hospitals[0].id = "h-1"
        mock_db.get_hospitals_by_source.return_value = mock_hospitals
        # Very few measurements
        mock_db.get_measurement_count_by_hospital.return_value = {"h-1": 10}

        # Mock onboarding date
        mock_db.get_hospital_onboarding_dates.return_value = {
            "h-1": datetime(2025, 1, 1, tzinfo=UTC)
        }

        mock_source = Mock()
        mock_source.province = "QC"
        mock_db.get_source.return_value = mock_source
        mock_db.get_stale_scrapers.return_value = []

        result = service.compute_system_quality()

        assert result["overall_status"] == "critical"

    @pytest.mark.unit
    def test_no_sources(self, service, mock_db):
        """No sources yields 'critical'."""
        mock_db.get_all_source_ids.return_value = []

        result = service.compute_system_quality()

        assert result["overall_status"] == "critical"
        assert result["sources"] == []


class TestCoverageTimeline:
    """Tests for get_coverage_timeline()."""

    @pytest.mark.unit
    def test_timeline_30_days(self, service, mock_db):
        """Returns 30 daily entries."""
        mock_db.get_measurement_timestamps.return_value = []

        result = service.get_coverage_timeline("ca-on-test", days=30)

        assert len(result) == 30
        for entry in result:
            assert "date" in entry
            assert "scrape_count" in entry
            assert "success_rate" in entry
            assert "has_gaps" in entry

    @pytest.mark.unit
    def test_timeline_detects_gaps(self, service, mock_db):
        """Days with large gaps have has_gaps=True."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        # Timestamps with a 180-min gap (>= 120 min threshold = 2x60)
        timestamps = [
            day,
            day + timedelta(hours=1),
            day + timedelta(hours=4),  # 180-min gap from previous
        ]
        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.get_coverage_timeline("ca-on-test", days=1)

        assert len(result) == 1
        assert result[0]["has_gaps"] is True

    @pytest.mark.unit
    def test_timeline_no_gaps(self, service, mock_db):
        """Evenly spaced timestamps have has_gaps=False."""
        day = datetime(2026, 2, 1, tzinfo=UTC)
        timestamps = _make_timestamps(day, 24, interval_minutes=60)
        mock_db.get_measurement_timestamps.return_value = timestamps

        result = service.get_coverage_timeline("ca-on-test", days=1)

        assert len(result) == 1
        assert result[0]["has_gaps"] is False
        assert result[0]["success_rate"] == 1.0


class TestSnapshotDailyQuality:
    """Tests for snapshot_daily_quality()."""

    @pytest.mark.unit
    def test_snapshot_saves(self, service, mock_db):
        """Snapshots are saved for each hospital."""
        mock_db.get_all_hospital_ids.return_value = ["h-1", "h-2"]
        mock_db.get_measurement_timestamps.return_value = []

        mock_hospital = Mock()
        mock_hospital.source_id = "src-1"
        mock_db.get_hospital.return_value = mock_hospital
        mock_db.insert_quality_snapshot.return_value = True

        day = datetime(2026, 2, 1, tzinfo=UTC)
        saved = service.snapshot_daily_quality(day)

        assert saved == 2
        assert mock_db.insert_quality_snapshot.call_count == 2

    @pytest.mark.unit
    def test_snapshot_idempotent(self, service, mock_db):
        """Second snapshot run returns 0 when all already exist."""
        mock_db.get_all_hospital_ids.return_value = ["h-1"]
        mock_db.get_measurement_timestamps.return_value = []

        mock_hospital = Mock()
        mock_hospital.source_id = "src-1"
        mock_db.get_hospital.return_value = mock_hospital
        # ON CONFLICT DO NOTHING → returns False
        mock_db.insert_quality_snapshot.return_value = False

        day = datetime(2026, 2, 1, tzinfo=UTC)
        saved = service.snapshot_daily_quality(day)

        assert saved == 0

    @pytest.mark.unit
    def test_snapshot_skips_missing_hospital(self, service, mock_db):
        """Hospital not found in DB is skipped."""
        mock_db.get_all_hospital_ids.return_value = ["h-missing"]
        mock_db.get_measurement_timestamps.return_value = []
        mock_db.get_hospital.return_value = None

        day = datetime(2026, 2, 1, tzinfo=UTC)
        saved = service.snapshot_daily_quality(day)

        assert saved == 0
        mock_db.insert_quality_snapshot.assert_not_called()
