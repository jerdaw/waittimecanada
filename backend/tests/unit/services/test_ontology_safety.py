"""Tests for Ontology Safety (Metric Mixing Prevention)."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock

import pytest

from waittime.services.trends import SystemTrendService


@pytest.fixture
def mock_db():
    """Create a mock DatabaseService."""
    return MagicMock()


@pytest.fixture
def trend_service(mock_db):
    """Create a SystemTrendService with mock DB."""
    return SystemTrendService(mock_db)


class TestOntologyMixing:
    """Tests that verify we do NOT mix incompatible metrics."""

    @pytest.mark.unit
    def test_trend_mixes_ontologies_bug(self, trend_service, mock_db):
        """
        Verify that the implementation prevents mixing incompatible ontologies.

        Scenario:
        - Hospital A reports "Triage -> Nurse" (Ontology 1) with mean 30 mins
        - Hospital B reports "Triage -> Doctor" (Ontology 2) with mean 120 mins

        Behavior:
        - Should select the ontology with more measurements (dominant).
        """
        start = datetime(2026, 1, 1, tzinfo=UTC)
        end = datetime(2026, 2, 1, tzinfo=UTC)

        # Mock DB returning mixed rows
        mock_db_rows = [
            {
                "hospital_id": "hosp-a",
                "period_start": start,
                "period_end": end,
                "mean_value": 30.0,
                "min_value": 10.0,
                "max_value": 60.0,
                "sample_count": 1000, # Dominant (Triage->Nurse)
                "metric_family": "wait_time",
                "start_event": "triage",
                "end_event": "nurse_seen",
                "statistic_type": "mean",
            },
            {
                "hospital_id": "hosp-b",
                "period_start": start,
                "period_end": end,
                "mean_value": 120.0,
                "min_value": 60.0,
                "max_value": 240.0,
                "sample_count": 100, # Minority (Triage->Doctor)
                "metric_family": "wait_time",
                "start_event": "triage",
                "end_event": "doctor_seen",
                "statistic_type": "mean",
            }
        ]

        # We need to mock the context manager for get_connection/get_cursor
        mock_conn = Mock()
        mock_cursor = Mock()

        # Explicitly mock context managers
        mock_conn_cm = Mock()
        mock_conn_cm.__enter__ = Mock(return_value=mock_conn)
        mock_conn_cm.__exit__ = Mock(return_value=None)
        mock_db.get_connection.return_value = mock_conn_cm

        mock_cursor_cm = Mock()
        mock_cursor_cm.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_cm.__exit__ = Mock(return_value=None)
        mock_db.get_cursor.return_value = mock_cursor_cm

        mock_cursor.fetchall.return_value = mock_db_rows

        # Execute
        result = trend_service.province_trend("ON", "monthly", lookback_months=1)

        # The service should select the dominant ontology
        data_points = result["data_points"]
        assert len(data_points) == 1

        # Should match the dominant row (mean 30.0)
        # Should NOT be the mixed average of (30 + 120)/2 = 75
        combined_mean = data_points[0]["province_mean"]
        assert combined_mean == 30.0, f"Expected safe mean 30.0, got {combined_mean}"

        # verify ontology metadata
        assert result["ontology"]["end_event"] == "nurse_seen"
