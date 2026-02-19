"""Tests for MethodologyChangeDetector.

Covers detection of large distributional shifts, handling of small shifts,
insufficient data, explanation format, and multi-source checking.
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from waittime.services.methodology_change import MethodologyChangeDetector


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def detector(mock_db):
    """Create a MethodologyChangeDetector with mock DB."""
    return MethodologyChangeDetector(mock_db)


def _make_measurements(mean: float, count: int) -> list[dict]:
    """Create mock measurement rows with a specific mean."""
    return [{"value": mean, "timestamp_utc": datetime.now(UTC)} for _ in range(count)]


def _make_hospitals(count: int) -> list[Mock]:
    """Create mock Hospital objects."""
    hospitals = []
    for i in range(count):
        h = Mock()
        h.id = f"hosp-{i}"
        hospitals.append(h)
    return hospitals


class TestCheckSource:
    """Tests for check_source()."""

    @pytest.mark.unit
    def test_no_change_stable_data(self, detector, mock_db):
        """Both periods similar yields no change detected."""
        mock_db.get_hospitals_by_source.return_value = _make_hospitals(6)

        # Both periods have mean ~60
        mock_db.get_measurements_in_range.return_value = _make_measurements(60.0, 50)

        result = detector.check_source("ontario-er")

        assert result["source_id"] == "ontario-er"
        assert result["change_detected"] is False
        assert result["details"] is None

    @pytest.mark.unit
    def test_change_detected_large_shift(self, detector, mock_db):
        """30% shift should trigger change detection."""
        hospitals = _make_hospitals(6)
        mock_db.get_hospitals_by_source.return_value = hospitals

        # Alternate between current (mean=130) and previous (mean=100) periods
        call_count = 0

        def mock_measurements(hospital_id, start, end):
            nonlocal call_count
            call_count += 1
            # Even calls = current period (higher), Odd = previous (lower)
            if call_count % 2 == 1:  # current
                return _make_measurements(130.0, 50)
            else:  # previous
                return _make_measurements(100.0, 50)

        mock_db.get_measurements_in_range.side_effect = mock_measurements
        mock_db.insert_methodology_change.return_value = 1

        result = detector.check_source("ontario-er")

        assert result["change_detected"] is True
        assert result["details"] is not None
        assert result["details"]["shift_percent"] == 30.0
        assert result["details"]["hospitals_analyzed"] == 6
        mock_db.insert_methodology_change.assert_called_once()

    @pytest.mark.unit
    def test_change_not_detected_small_shift(self, detector, mock_db):
        """10% shift should be below threshold."""
        hospitals = _make_hospitals(6)
        mock_db.get_hospitals_by_source.return_value = hospitals

        call_count = 0

        def mock_measurements(hospital_id, start, end):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:  # current
                return _make_measurements(110.0, 50)
            else:  # previous
                return _make_measurements(100.0, 50)

        mock_db.get_measurements_in_range.side_effect = mock_measurements

        result = detector.check_source("ontario-er")

        assert result["change_detected"] is False
        mock_db.insert_methodology_change.assert_not_called()

    @pytest.mark.unit
    def test_insufficient_hospitals(self, detector, mock_db):
        """<5 hospitals should skip detection entirely."""
        mock_db.get_hospitals_by_source.return_value = _make_hospitals(3)

        result = detector.check_source("small-source")

        assert result["change_detected"] is False
        assert result["details"] is None
        # Should not even query measurements
        mock_db.get_measurements_in_range.assert_not_called()

    @pytest.mark.unit
    def test_insufficient_data_in_period(self, detector, mock_db):
        """Not enough hospitals with data should not trigger detection."""
        hospitals = _make_hospitals(6)
        mock_db.get_hospitals_by_source.return_value = hospitals

        call_count = 0

        def mock_measurements(hospital_id, start, end):
            nonlocal call_count
            call_count += 1
            # Only first 3 hospitals have current data, none have previous
            if call_count <= 3:
                return _make_measurements(100.0, 50)
            return []

        mock_db.get_measurements_in_range.side_effect = mock_measurements

        result = detector.check_source("sparse-source")

        assert result["change_detected"] is False


class TestExplanation:
    """Tests for explanation format."""

    @pytest.mark.unit
    def test_explanation_is_human_readable(self, detector, mock_db):
        """Explanation should be descriptive and readable."""
        hospitals = _make_hospitals(6)
        mock_db.get_hospitals_by_source.return_value = hospitals

        call_count = 0

        def mock_measurements(hospital_id, start, end):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:
                return _make_measurements(150.0, 50)
            else:
                return _make_measurements(100.0, 50)

        mock_db.get_measurements_in_range.side_effect = mock_measurements
        mock_db.insert_methodology_change.return_value = 1

        result = detector.check_source("ontario-er")

        assert result["change_detected"] is True
        explanation = result["details"]["explanation"]
        assert isinstance(explanation, str)
        assert "increased" in explanation or "decreased" in explanation
        assert "%" in explanation
        assert "hospitals" in explanation
        assert "methodology" in explanation.lower()

    @pytest.mark.unit
    def test_decrease_explanation(self, detector, mock_db):
        """Decrease should say 'decreased'."""
        hospitals = _make_hospitals(6)
        mock_db.get_hospitals_by_source.return_value = hospitals

        call_count = 0

        def mock_measurements(hospital_id, start, end):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 1:  # current
                return _make_measurements(50.0, 50)
            else:  # previous
                return _make_measurements(100.0, 50)

        mock_db.get_measurements_in_range.side_effect = mock_measurements
        mock_db.insert_methodology_change.return_value = 1

        result = detector.check_source("ontario-er")

        assert result["change_detected"] is True
        assert "decreased" in result["details"]["explanation"]


class TestCheckAllSources:
    """Tests for check_all_sources()."""

    @pytest.mark.unit
    def test_checks_all_sources(self, detector, mock_db):
        """Should check every source."""
        mock_db.get_all_source_ids.return_value = ["src-1", "src-2"]
        # Both sources have too few hospitals → no detection
        mock_db.get_hospitals_by_source.return_value = _make_hospitals(2)

        results = detector.check_all_sources()

        assert len(results) == 2
        assert results[0]["source_id"] == "src-1"
        assert results[1]["source_id"] == "src-2"

    @pytest.mark.unit
    def test_empty_sources(self, detector, mock_db):
        """No sources returns empty list."""
        mock_db.get_all_source_ids.return_value = []

        results = detector.check_all_sources()

        assert results == []


class TestGetChangeHistory:
    """Tests for get_change_history()."""

    @pytest.mark.unit
    def test_delegates_to_db(self, detector, mock_db):
        """Should delegate to db.get_methodology_changes."""
        mock_db.get_methodology_changes.return_value = [
            {"source_id": "test", "shift_percent": 25.0}
        ]

        result = detector.get_change_history(source_id="test")

        assert len(result) == 1
        mock_db.get_methodology_changes.assert_called_once_with(source_id="test")
