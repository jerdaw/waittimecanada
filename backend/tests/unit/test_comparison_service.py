"""Tests for ComparisonService."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest

from waittime.core import EndEvent, MetricFamily, PatientScope, StartEvent, StatisticType
from waittime.services.comparison import ComparisonService


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return Mock()


@pytest.fixture
def comparison_service(mock_db):
    """Create ComparisonService with mocked database."""
    return ComparisonService(mock_db)


def create_hospital_row(hospital_id, wait_time, start_event="TRIAGE", statistic_type="P90"):
    """Helper to create a mock hospital row."""
    return {
        "id": hospital_id,
        "name": f"Hospital {hospital_id}",
        "province": "ON",
        "city": "Ottawa",
        "latitude": 45.4,
        "longitude": -75.7,
        "value": wait_time,
        "timestamp_utc": datetime.now(UTC),
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": start_event,
        "end_event": "PHYSICIAN",
        "statistic_type": statistic_type,
        "patient_scope": "ALL",
    }


def setup_db_mock(mock_db, hospital_a_row, hospital_b_row=None):
    """Setup database mock to return hospital rows."""
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = Mock(return_value=mock_cursor)
    mock_cursor.__exit__ = Mock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.__enter__ = Mock(return_value=mock_conn)
    mock_conn.__exit__ = Mock(return_value=False)

    mock_db.get_connection.return_value = mock_conn
    mock_db.get_cursor.return_value = mock_cursor

    # Set up fetchone to return different values on subsequent calls
    if hospital_b_row is not None:
        mock_cursor.fetchone.side_effect = [hospital_a_row, hospital_b_row]
    else:
        mock_cursor.fetchone.return_value = hospital_a_row

    return mock_cursor


class TestCompareHospitals:
    """Test hospital comparison functionality."""

    def test_compare_compatible_hospitals(self, comparison_service, mock_db):
        """Should return comparable=True for hospitals with same methodology."""
        hospital_a = create_hospital_row("ca-on-ottawa", 120)
        hospital_b = create_hospital_row("ca-on-toronto", 90)

        setup_db_mock(mock_db, hospital_a, hospital_b)

        result = comparison_service.compare_hospitals("ca-on-ottawa", "ca-on-toronto")

        assert result["comparable"] is True
        assert result["divergence_brief"] is None
        assert result["hospital_a"]["wait_time"] == 120
        assert result["hospital_b"]["wait_time"] == 90

    def test_compare_incompatible_hospitals(self, comparison_service, mock_db):
        """Should return comparable=False and divergence brief for different methodologies."""
        hospital_a = create_hospital_row("ca-on-ottawa", 120, "TRIAGE", "P90")
        hospital_b = create_hospital_row("ca-qc-montreal", 90, "REGISTRATION", "ROLLING_AVG")

        setup_db_mock(mock_db, hospital_a, hospital_b)

        result = comparison_service.compare_hospitals("ca-on-ottawa", "ca-qc-montreal")

        assert result["comparable"] is False
        assert result["divergence_brief"] is not None
        assert "TRIAGE vs REGISTRATION" in result["divergence_brief"]
        assert "P90 vs ROLLING_AVG" in result["divergence_brief"]

    def test_raises_when_hospital_a_not_found(self, comparison_service, mock_db):
        """Should raise ValueError if hospital A not found."""
        setup_db_mock(mock_db, None)

        with pytest.raises(ValueError, match="Hospital not found.*ca-on-missing"):
            comparison_service.compare_hospitals("ca-on-missing", "ca-on-ottawa")

    def test_raises_when_hospital_b_not_found(self, comparison_service, mock_db):
        """Should raise ValueError if hospital B not found."""
        hospital_a = create_hospital_row("ca-on-ottawa", 120)

        # Need to create separate mocks for each call
        mock_cursor_a = MagicMock()
        mock_cursor_a.fetchone.return_value = hospital_a
        mock_cursor_a.__enter__ = Mock(return_value=mock_cursor_a)
        mock_cursor_a.__exit__ = Mock(return_value=False)

        mock_cursor_b = MagicMock()
        mock_cursor_b.fetchone.return_value = None
        mock_cursor_b.__enter__ = Mock(return_value=mock_cursor_b)
        mock_cursor_b.__exit__ = Mock(return_value=False)

        mock_conn = MagicMock()
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)

        mock_db.get_connection.return_value = mock_conn
        mock_db.get_cursor.side_effect = [mock_cursor_a, mock_cursor_b]

        with pytest.raises(ValueError, match="Hospital not found.*ca-on-missing"):
            comparison_service.compare_hospitals("ca-on-ottawa", "ca-on-missing")

    def test_includes_methodology_details(self, comparison_service, mock_db):
        """Should include full methodology details in response."""
        hospital_a = create_hospital_row("ca-on-ottawa", 120)
        hospital_b = create_hospital_row("ca-on-toronto", 90)

        setup_db_mock(mock_db, hospital_a, hospital_b)

        result = comparison_service.compare_hospitals("ca-on-ottawa", "ca-on-toronto")

        # Check hospital A methodology
        assert result["hospital_a"]["methodology"]["metric_family"] == "TIME_TO_PROVIDER"
        assert result["hospital_a"]["methodology"]["start_event"] == "TRIAGE"
        assert result["hospital_a"]["methodology"]["end_event"] == "PHYSICIAN"
        assert result["hospital_a"]["methodology"]["statistic_type"] == "P90"

        # Check hospital B methodology
        assert result["hospital_b"]["methodology"]["metric_family"] == "TIME_TO_PROVIDER"

    def test_includes_timestamp(self, comparison_service, mock_db):
        """Should include comparison timestamp."""
        hospital_a = create_hospital_row("ca-on-ottawa", 120)
        hospital_b = create_hospital_row("ca-on-toronto", 90)

        setup_db_mock(mock_db, hospital_a, hospital_b)

        result = comparison_service.compare_hospitals("ca-on-ottawa", "ca-on-toronto")

        assert "comparison_timestamp" in result
        assert result["comparison_timestamp"].endswith("Z") or "+" in result["comparison_timestamp"]

    def test_includes_hospital_details(self, comparison_service, mock_db):
        """Should include hospital name, province, city."""
        hospital_a = create_hospital_row("ca-on-ottawa", 120)
        hospital_b = create_hospital_row("ca-on-toronto", 90)

        setup_db_mock(mock_db, hospital_a, hospital_b)

        result = comparison_service.compare_hospitals("ca-on-ottawa", "ca-on-toronto")

        assert result["hospital_a"]["id"] == "ca-on-ottawa"
        assert result["hospital_a"]["name"] == "Hospital ca-on-ottawa"
        assert result["hospital_a"]["province"] == "ON"
        assert result["hospital_a"]["city"] == "Ottawa"

        assert result["hospital_b"]["id"] == "ca-on-toronto"


class TestGetHospitalWithMeasurement:
    """Test fetching hospital with latest measurement."""

    def test_returns_hospital_with_measurement(self, comparison_service, mock_db):
        """Should return dict with hospital and measurement data."""
        hospital_row = create_hospital_row("ca-on-ottawa", 120)
        setup_db_mock(mock_db, hospital_row)

        result = comparison_service._get_hospital_with_measurement("ca-on-ottawa")

        assert result is not None
        assert result["id"] == "ca-on-ottawa"
        assert result["name"] == "Hospital ca-on-ottawa"
        assert result["measurement"]["value"] == 120
        assert result["measurement"]["metric_family"] == "TIME_TO_PROVIDER"

    def test_returns_none_when_not_found(self, comparison_service, mock_db):
        """Should return None if hospital not found."""
        setup_db_mock(mock_db, None)

        result = comparison_service._get_hospital_with_measurement("ca-on-missing")

        assert result is None

    def test_queries_only_visible_verified_hospitals(self, comparison_service, mock_db):
        """Should filter by is_visible and is_verified."""
        hospital_row = create_hospital_row("ca-on-ottawa", 120)
        mock_cursor = setup_db_mock(mock_db, hospital_row)

        comparison_service._get_hospital_with_measurement("ca-on-ottawa")

        # Check that query includes visibility/verification filters
        query = mock_cursor.execute.call_args[0][0]
        assert "is_visible = true" in query
        assert "is_verified = true" in query


class TestDictToMeasurement:
    """Test conversion from dict to Measurement model."""

    def test_converts_dict_to_measurement(self, comparison_service):
        """Should create Measurement object from dict."""
        data = {
            "value": 120,
            "timestamp_utc": "2026-01-01T12:00:00+00:00",
            "metric_family": "TIME_TO_PROVIDER",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "P90",
            "patient_scope": "ALL",
        }

        measurement = comparison_service._dict_to_measurement(data)

        assert measurement.value == 120
        assert measurement.metric_family == MetricFamily.TIME_TO_PROVIDER
        assert measurement.start_event == StartEvent.TRIAGE
        assert measurement.end_event == EndEvent.PHYSICIAN
        assert measurement.statistic_type == StatisticType.P90
        assert measurement.patient_scope == PatientScope.ALL

    def test_handles_different_patient_scopes(self, comparison_service):
        """Should correctly parse different patient scopes."""
        data = {
            "value": 120,
            "timestamp_utc": "2026-01-01T12:00:00+00:00",
            "metric_family": "TIME_TO_PROVIDER",
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "statistic_type": "P90",
            "patient_scope": "MID_ACUITY",
        }

        measurement = comparison_service._dict_to_measurement(data)

        assert measurement.patient_scope == PatientScope.MID_ACUITY
