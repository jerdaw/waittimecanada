"""Tests for Ontology Safety in Benchmarking."""

from unittest.mock import MagicMock, Mock

import pytest

from waittime.services.benchmarking import BenchmarkingService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def bs(mock_db):
    return BenchmarkingService(mock_db)


class TestBenchmarkingOntologySafety:
    """Verify strictly separated benchmarks."""

    @pytest.mark.unit
    def test_benchmarks_use_dominant_ontology_by_default(self, bs, mock_db):
        """
        Scenario:
        - compute_benchmarks("ON") is called without explicit ontology.
        - Service should query for dominant ontology.
        - Service should then query benchmarks using that ontology.
        """
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()

        # Mock context managers explicitly
        mock_conn_cm = Mock()
        mock_conn_cm.__enter__ = Mock(return_value=mock_conn)
        mock_conn_cm.__exit__ = Mock(return_value=None)
        mock_db.get_connection.return_value = mock_conn_cm

        mock_cursor_cm = Mock()
        mock_cursor_cm.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_cm.__exit__ = Mock(return_value=None)
        mock_db.get_cursor.return_value = mock_cursor_cm

        # Setup return values for queries
        # 1. _get_dominant_ontology query
        # 2. _query_benchmark_rows query

        dominant_ontology_row = {
            "metric_family": "wait_time",
            "start_event": "triage",
            "end_event": "nurse_seen",
            "statistic_type": "mean",
        }

        benchmark_rows = []  # empty is fine, we care about the query params

        mock_cursor.fetchone.side_effect = [
            dominant_ontology_row,  # for _get_dominant_ontology
        ]

        mock_cursor.fetchall.side_effect = [
            benchmark_rows,  # for _query_benchmark_rows
        ]

        result = bs.compute_benchmarks("ON", period_days=7)

        calls = mock_cursor.execute.call_args_list

        assert len(calls) >= 2
        dominant_query_call = calls[0]
        assert "SELECT" in dominant_query_call[0][0]
        assert "COUNT(*)" in dominant_query_call[0][0]  # ensure it's the counting query

        benchmark_query_call = calls[1]
        query_sql = benchmark_query_call[0][0]
        query_params = benchmark_query_call[0][1]

        # The query SQL should contain the ontology filter placeholders
        assert "AND metric_family = %s" in query_sql

        # Dominant ontology values must be threaded into the benchmark query params.
        assert "nurse_seen" in query_params
        assert "wait_time" in query_params

        assert result["ontology"] == dominant_ontology_row
