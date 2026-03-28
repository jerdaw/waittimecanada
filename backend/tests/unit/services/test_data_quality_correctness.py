"""Tests for DataQualityService correctness fix."""

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


class TestHospitalOnboardingLogic:
    """Tests that verify we respect hospital onboarding dates."""

    @pytest.mark.unit
    def test_new_hospital_does_not_skew_history(self, service, mock_db):
        """
        Scenario:
        - Analysis Period: 3 days (Days 1, 2, 3)
        - Hospital A: Active since Day 1
        - Hospital B: Active since Day 3 (New!)

        Expected Calculation:
        - Day 1: Only Hospital A expected (1 * 24)
        - Day 2: Only Hospital A expected (1 * 24)
        - Day 3: Both A and B expected (2 * 24)
        - Total Expected: 24 + 24 + 48 = 96

        Old/Buggy Calculation:
        - Assumes A and B active for all 3 days
        - Total Expected: 2 * 24 * 3 = 144
        """
        start = datetime(2026, 2, 1, tzinfo=UTC)  # Day 1
        end = datetime(2026, 2, 4, tzinfo=UTC)  # Day 4 (Exclusive)

        # Mock Hospitals
        hosp_a = Mock(id="hosp-a")
        hosp_b = Mock(id="hosp-b")
        mock_db.get_hospitals_by_source.return_value = [hosp_a, hosp_b]

        # Mock Onboarding Dates (The new method we will implement)
        # Hospital A seen since Day 1
        # Hospital B seen since Day 3
        mock_db.get_hospital_onboarding_dates.return_value = {
            "hosp-a": start,
            "hosp-b": start + timedelta(days=2),
        }

        # Mock Measurements (Actuals)
        # Hospital A: Perfect data for 3 days (24 * 3 = 72)
        # Hospital B: Perfect data for 1 day (24 * 1 = 24)
        # Total Actual: 96
        mock_db.get_measurement_count_by_hospital.return_value = {
            "hosp-a": 72,
            "hosp-b": 24,
        }

        # Execute
        result = service.compute_source_quality("test-source", start, end)

        # Assertions
        assert result["total_actual"] == 96

        # The Key Assertion:
        # If incorrectly calculating (old way), expected would be 144.
        # If correctly calculating (new way), expected should be 96.
        assert result["total_expected"] == 96, (
            f"Expected 96 (dynamic), got {result['total_expected']}"
        )

        # Success rate should be 100% because everyone reported perfectly
        # for the time they were active.
        assert result["overall_success_rate"] == 1.0
