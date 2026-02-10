"""Tests for Ontology Safety in Benchmarking."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, Mock, call

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
            "statistic_type": "mean"
        }

        benchmark_rows = [] # empty is fine, we care about the query params

        # We use side_effect to return different things for different calls
        # checks based on query string presence? Or just order.
        # Order: 1. get_prov (maybe), 2. get_dominant, 3. get_rows
        # Actually compute_benchmarks calls:
        # 1. _get_dominant_ontology
        # 2. _query_benchmark_rows

        mock_cursor.fetchone.side_effect = [
            dominant_ontology_row, # for _get_dominant_ontology
        ]

        mock_cursor.fetchall.side_effect = [
            benchmark_rows, # for _query_benchmark_rows
        ]

        # Execute
        result = bs.compute_benchmarks("ON", period_days=7)

        # Verification
        # Check that execute was called with correct params
        # We expect at least 2 execute calls.

        calls = mock_cursor.execute.call_args_list

        # First call: Dominant Ontology Query
        assert len(calls) >= 2
        dominant_query_call = calls[0]
        assert "SELECT" in dominant_query_call[0][0]
        assert "COUNT(*)" in dominant_query_call[0][0] # ensure it's the counting query

        # Second call: Benchmark Query
        benchmark_query_call = calls[1]
        query_sql = benchmark_query_call[0][0]
        query_params = benchmark_query_call[0][1]

        # The query SQL should contain the ontology filter placeholders
        assert "AND metric_family = %s" in query_sql

        # The params should include the dominant ontology values
        # logic: 2 timestamps + 4 ontology params + 2 timestamps + 4 ontology params + 3 ontology (measurements) + province
        # We just check existence of "nurse_seen" in params
        assert "nurse_seen" in query_params
        assert "wait_time" in query_params

        # Verify result contains ontology info
        assert result["ontology"] == dominant_ontology_row
