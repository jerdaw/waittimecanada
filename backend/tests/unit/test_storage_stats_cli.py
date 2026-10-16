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
def test_storage_stats_cli_preservation_inventory_is_explicit_value_free_json(mock_db, capsys):
    mock_db.return_value.get_measurement_preservation_inventory.return_value = {
        "status": "complete",
        "transaction_read_only": True,
        "raw_measurements": {"groups": [{"source_id": "test-source", "row_count": 4}]},
        "aggregates": {"groups": []},
        "purge_execution_history": "not_assessed",
        "provider_backup_pitr_restore_evidence": "not_assessed",
    }

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["transaction_read_only"] is True
    assert payload["raw_measurements"]["groups"][0]["row_count"] == 4
    assert payload["purge_execution_history"] == "not_assessed"
    mock_db.return_value.get_measurement_preservation_inventory.assert_called_once_with()


@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_preservation_inventory_sanitizes_database_errors(mock_db, capsys):
    mock_db.return_value.get_measurement_preservation_inventory.side_effect = RuntimeError(
        "database diagnostic sentinel"
    )

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 1

    captured = capsys.readouterr()
    assert json.loads(captured.err) == {
        "error_class": "inventory_failed",
        "status": "error",
    }
    assert "database diagnostic sentinel" not in captured.err


@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_exception(mock_db, capsys):
    mock_db.return_value.get_relation_storage_stats.side_effect = ValueError("boom")

    with patch.object(sys, "argv", ["storage_stats"]):
        assert main() == 1

    captured = capsys.readouterr()
    assert "storage stats failed: boom" in captured.err
