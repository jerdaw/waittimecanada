"""Unit tests for the storage_stats CLI."""

import json
import sys
from copy import deepcopy
from unittest.mock import patch

import pytest

from waittime.cli.storage_stats import main
from waittime.core.enums import EndEvent, MetricFamily, PatientScope, StartEvent, StatisticType

SOURCE_IDS = ["alberta-ahs", "bc-phsa", "ontario-health", "quebec-msss"]


def _empty_inventory():
    return {
        "status": "complete",
        "transaction_read_only": True,
        "statement_timeout": "5000ms",
        "snapshot_at_utc": "2026-10-18T12:00:00Z",
        "retention_threshold_days": 30,
        "retention_cutoff_utc": "2026-09-18T12:00:00Z",
        "retention_threshold_basis": "30 elapsed 24-hour days from the UTC snapshot",
        "raw_measurements": {
            "groups": [],
            "sources_without_measurements": [],
            "provenance_schema_nullable": {
                "source_id": False,
                "raw_payload_hash": True,
                "parser_version": True,
                "raw_payload_snippet": True,
            },
        },
        "aggregates": {
            "groups": [],
            "scope": "summary-row coverage only; not a raw-measurement backup",
        },
        "purge_execution_history": "not_assessed",
        "provider_backup_pitr_restore_evidence": "not_assessed",
    }


def _raw_group():
    return {
        "source_id": "alberta-ahs",
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "P90",
        "patient_scope": "ALL",
        "row_count": 2,
        "oldest_timestamp_utc": "2026-10-18T10:00:00.123456Z",
        "newest_timestamp_utc": "2026-10-18T11:00:00Z",
        "rows_older_than_30_days": 0,
        "future_timestamp_rows": 0,
        "missing_source_id_count": 0,
        "missing_payload_hash_count": 0,
        "missing_parser_version_count": 0,
        "absent_optional_payload_snippet_count": 2,
    }


def _aggregate_group():
    return {
        "source_id": "alberta-ahs",
        "period_type": "hourly",
        "metric_family": "TIME_TO_PROVIDER",
        "start_event": "TRIAGE",
        "end_event": "PHYSICIAN",
        "statistic_type": "P90",
        "aggregate_row_count": 2,
        "aggregate_sample_count_sum": 8,
        "oldest_period_start_utc": "2026-10-18T10:00:00Z",
        "newest_period_end_utc": "2026-10-18T12:00:00Z",
        "newest_aggregate_created_at_utc": "2026-10-18T12:01:00Z",
    }


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


@pytest.mark.parametrize("timeout_value", ["5s", "5000ms"])
@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_preservation_inventory_accepts_empty_inventory(
    mock_db, capsys, timeout_value
):
    inventory = _empty_inventory()
    inventory["statement_timeout"] = timeout_value
    mock_db.return_value.get_measurement_preservation_inventory.return_value = inventory

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["transaction_read_only"] is True
    assert payload["statement_timeout"] == "5000ms"
    assert payload["raw_measurements"]["groups"] == []
    assert payload["aggregates"]["groups"] == []
    assert payload["purge_execution_history"] == "not_assessed"
    assert captured.err == ""
    mock_db.return_value.get_measurement_preservation_inventory.assert_called_once_with()


@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_preservation_inventory_accepts_approved_vocabulary_and_nulls(
    mock_db, capsys
):
    inventory = _empty_inventory()
    metric_families = [item.value for item in MetricFamily]
    start_events = [item.value for item in StartEvent]
    end_events = [item.value for item in EndEvent]
    statistic_types = [item.value for item in StatisticType]
    patient_scopes = [item.value for item in PatientScope]
    period_types = ["hourly", "daily", "weekly", "monthly"]

    inventory["raw_measurements"]["groups"] = [
        {
            **_raw_group(),
            "source_id": SOURCE_IDS[index % len(SOURCE_IDS)],
            "metric_family": metric_families[index % len(metric_families)],
            "start_event": start_events[index % len(start_events)],
            "end_event": end_events[index % len(end_events)],
            "statistic_type": statistic_types[index % len(statistic_types)],
            "patient_scope": patient_scopes[index % len(patient_scopes)],
        }
        for index in range(
            max(
                len(SOURCE_IDS),
                len(metric_families),
                len(start_events),
                len(end_events),
                len(statistic_types),
                len(patient_scopes),
            )
        )
    ]
    inventory["raw_measurements"]["groups"].append(
        {
            **_raw_group(),
            "source_id": None,
            "metric_family": None,
            "start_event": None,
            "end_event": None,
            "statistic_type": None,
            "patient_scope": None,
            "oldest_timestamp_utc": None,
            "newest_timestamp_utc": None,
        }
    )
    inventory["raw_measurements"]["sources_without_measurements"] = SOURCE_IDS.copy()
    inventory["aggregates"]["groups"] = [
        {
            **_aggregate_group(),
            "source_id": SOURCE_IDS[index % len(SOURCE_IDS)],
            "period_type": period_types[index % len(period_types)],
            "metric_family": metric_families[index % len(metric_families)],
            "start_event": start_events[index % len(start_events)],
            "end_event": end_events[index % len(end_events)],
            "statistic_type": statistic_types[index % len(statistic_types)],
        }
        for index in range(
            max(
                len(SOURCE_IDS),
                len(period_types),
                len(metric_families),
                len(start_events),
                len(end_events),
                len(statistic_types),
            )
        )
    ]
    inventory["aggregates"]["groups"].append(
        {
            **_aggregate_group(),
            "source_id": None,
            "period_type": None,
            "metric_family": None,
            "start_event": None,
            "end_event": None,
            "statistic_type": None,
            "oldest_period_start_utc": None,
            "newest_period_end_utc": None,
            "newest_aggregate_created_at_utc": None,
        }
    )
    original = deepcopy(inventory)
    mock_db.return_value.get_measurement_preservation_inventory.return_value = inventory

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == original


@pytest.mark.parametrize(
    ("location", "field"),
    [
        ("raw", "source_id"),
        ("raw", "metric_family"),
        ("raw", "start_event"),
        ("raw", "end_event"),
        ("raw", "statistic_type"),
        ("raw", "patient_scope"),
        ("source_list", None),
        ("aggregate", "source_id"),
        ("aggregate", "period_type"),
        ("aggregate", "metric_family"),
        ("aggregate", "start_event"),
        ("aggregate", "end_event"),
        ("aggregate", "statistic_type"),
    ],
)
@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_rejects_unapproved_output_labels_without_partial_report(
    mock_db, capsys, location, field
):
    inventory = _empty_inventory()
    if location == "raw":
        inventory["raw_measurements"]["groups"] = [_raw_group()]
        inventory["raw_measurements"]["groups"][0][field] = "unapproved-label"
    elif location == "source_list":
        inventory["raw_measurements"]["sources_without_measurements"] = ["unapproved-label"]
    else:
        inventory["aggregates"]["groups"] = [_aggregate_group()]
        inventory["aggregates"]["groups"][0][field] = "unapproved-label"
    mock_db.return_value.get_measurement_preservation_inventory.return_value = inventory

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error_class": "output_contract_mismatch",
        "status": "error",
    }
    assert "unapproved-label" not in captured.err


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.update(extra_field="unexpected"),
        lambda payload: payload["raw_measurements"].update(extra_field="unexpected"),
        lambda payload: payload["raw_measurements"]["groups"].append(
            {**_raw_group(), "raw_payload_snippet": "private text"}
        ),
        lambda payload: payload["aggregates"]["groups"].append(
            {**_aggregate_group(), "unexpected": "private text"}
        ),
    ],
)
@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_rejects_unknown_output_keys_without_partial_report(
    mock_db, capsys, mutation
):
    inventory = _empty_inventory()
    mutation(inventory)
    mock_db.return_value.get_measurement_preservation_inventory.return_value = inventory

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error_class": "output_contract_mismatch",
        "status": "error",
    }
    assert "private text" not in captured.err


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload["raw_measurements"]["groups"].append(
            {**_raw_group(), "row_count": True}
        ),
        lambda payload: payload.update(transaction_read_only=1),
        lambda payload: payload.update(statement_timeout=[]),
        lambda payload: payload.update(statement_timeout="1s"),
        lambda payload: payload.update(snapshot_at_utc="not-a-timestamp"),
        lambda payload: payload["raw_measurements"].update(groups=()),
        lambda payload: payload["raw_measurements"]["provenance_schema_nullable"].update(
            source_id=1
        ),
        lambda payload: payload.update(status="unexpected"),
        lambda payload: payload["aggregates"].update(scope="unexpected"),
    ],
)
@patch("waittime.cli.storage_stats.DatabaseService")
def test_storage_stats_cli_rejects_wrong_output_types_without_partial_report(
    mock_db, capsys, mutation
):
    inventory = _empty_inventory()
    mutation(inventory)
    mock_db.return_value.get_measurement_preservation_inventory.return_value = inventory

    with patch.object(sys, "argv", ["storage_stats", "--preservation-inventory"]):
        assert main() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "error_class": "output_contract_mismatch",
        "status": "error",
    }


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
