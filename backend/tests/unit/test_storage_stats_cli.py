"""Unit tests for the storage_stats CLI."""

import json
import sys
from unittest.mock import patch

from waittime.cli.storage_stats import main


@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_text_output(mock_db, capsys):
    mock_db.return_value.get_relation_storage_stats.return_value = {
        "relation_name": "measurements",
        "estimated_row_count": 1234,
        "exact_row_count": None,
        "table_bytes": 2048,
        "index_bytes": 1024,
        "total_bytes": 3072,
    }

    with patch.object(sys, "argv", ["storage_stats"]):
        assert main() == 0

    captured = capsys.readouterr()
    assert "Relation: measurements" in captured.out
    assert "Estimated rows: 1234" in captured.out
    assert "Total size:" in captured.out


@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_json_output(mock_db, capsys):
    mock_db.return_value.get_relation_storage_stats.return_value = {
        "relation_name": "measurements",
        "estimated_row_count": 1234,
        "exact_row_count": 1234,
        "table_bytes": 2048,
        "index_bytes": 1024,
        "total_bytes": 3072,
    }

    with patch.object(sys, "argv", ["storage_stats", "--json", "--exact-count"]):
        assert main() == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["relation_name"] == "measurements"
    assert payload["exact_row_count"] == 1234


@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_exception(mock_db, capsys):
    mock_db.return_value.get_relation_storage_stats.side_effect = ValueError("boom")

    with patch.object(sys, "argv", ["storage_stats"]):
        assert main() == 1

    captured = capsys.readouterr()
    assert "storage stats failed: boom" in captured.err
