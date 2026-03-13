"""Unit tests for the aggregate CLI tool."""

from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from waittime.cli.aggregate import main


@pytest.fixture
def mock_backfill_counts():
    return {"hourly": 24, "daily": 1, "weekly": 0, "monthly": 0}


@pytest.mark.unit
class TestAggregateCLIBackfill:
    """Tests for --backfill mode."""

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_backfill_calls_service(self, mock_db_cls, mock_agg_cls, mock_backfill_counts):
        """--backfill should call backfill on the service."""
        mock_service = mock_agg_cls.return_value
        mock_service.backfill.return_value = mock_backfill_counts

        with patch("sys.argv", ["aggregate.py", "--backfill", "--days", "7"]):
            exit_code = main()

        assert exit_code == 0
        mock_service.backfill.assert_called_once()
        call_kwargs = mock_service.backfill.call_args.kwargs
        assert call_kwargs["dry_run"] is False
        assert call_kwargs["hospital_id"] is None

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_backfill_specific_hospital(self, mock_db_cls, mock_agg_cls, mock_backfill_counts):
        """--hospital should pass hospital_id to backfill."""
        mock_service = mock_agg_cls.return_value
        mock_service.backfill.return_value = mock_backfill_counts

        with patch("sys.argv", ["aggregate.py", "--backfill", "--hospital", "ca-on-test"]):
            exit_code = main()

        assert exit_code == 0
        call_kwargs = mock_service.backfill.call_args.kwargs
        assert call_kwargs["hospital_id"] == "ca-on-test"

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_backfill_specific_period(self, mock_db_cls, mock_agg_cls):
        """--period should filter to a single period type."""
        mock_service = mock_agg_cls.return_value
        mock_service.backfill.return_value = {"daily": 5}

        with patch("sys.argv", ["aggregate.py", "--backfill", "--period", "daily"]):
            exit_code = main()

        assert exit_code == 0
        call_kwargs = mock_service.backfill.call_args.kwargs
        assert call_kwargs["period_types"] == ["daily"]


@pytest.mark.unit
class TestAggregateCLIIncremental:
    """Tests for --incremental mode."""

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_incremental_uses_48h_window(self, mock_db_cls, mock_agg_cls, mock_backfill_counts):
        """--incremental should refresh recent current-period aggregates."""
        mock_service = mock_agg_cls.return_value
        mock_service.refresh_recent_periods.return_value = {
            "daily": 2,
            "weekly": 1,
            "monthly": 1,
        }

        with patch("sys.argv", ["aggregate.py", "--incremental"]):
            exit_code = main()

        assert exit_code == 0
        call_kwargs = mock_service.refresh_recent_periods.call_args.kwargs
        assert call_kwargs["period_types"] == ["daily", "weekly", "monthly"]
        delta = datetime.now(UTC) - call_kwargs["since"]
        assert 1.9 < delta.total_seconds() / 3600 < 2.1

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_incremental_specific_period(self, mock_db_cls, mock_agg_cls):
        """--incremental --period daily should narrow the refresh scope."""
        mock_service = mock_agg_cls.return_value
        mock_service.refresh_recent_periods.return_value = {"daily": 2}

        with patch("sys.argv", ["aggregate.py", "--incremental", "--period", "daily"]):
            exit_code = main()

        assert exit_code == 0
        call_kwargs = mock_service.refresh_recent_periods.call_args.kwargs
        assert call_kwargs["period_types"] == ["daily"]

    def test_incremental_rejects_hourly_period(self):
        """Routine incremental refresh should not maintain hourly aggregates."""
        with patch("sys.argv", ["aggregate.py", "--incremental", "--period", "hourly"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2


@pytest.mark.unit
class TestAggregateCLIDryRun:
    """Tests for --dry-run mode."""

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_dry_run_passed_to_service(self, mock_db_cls, mock_agg_cls, mock_backfill_counts):
        """--dry-run should pass dry_run=True to backfill."""
        mock_service = mock_agg_cls.return_value
        mock_service.backfill.return_value = mock_backfill_counts

        with patch("sys.argv", ["aggregate.py", "--backfill", "--dry-run"]):
            exit_code = main()

        assert exit_code == 0
        call_kwargs = mock_service.backfill.call_args.kwargs
        assert call_kwargs["dry_run"] is True


@pytest.mark.unit
class TestAggregateCLIErrors:
    """Tests for error handling."""

    def test_no_mode_specified_exits_with_error(self):
        """Should fail if neither --backfill nor --incremental is given."""
        with patch("sys.argv", ["aggregate.py"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # argparse error

    @patch("waittime.cli.aggregate.AggregationService")
    @patch("waittime.cli.aggregate.DatabaseService")
    def test_exception_returns_exit_code_1(self, mock_db_cls, mock_agg_cls):
        """Should return 1 on exception."""
        mock_service = mock_agg_cls.return_value
        mock_service.backfill.side_effect = Exception("DB error")

        with patch("sys.argv", ["aggregate.py", "--backfill"]):
            exit_code = main()

        assert exit_code == 1
