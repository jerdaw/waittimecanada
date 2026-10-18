"""CLI for inspecting relation storage growth."""

import argparse
import json
import re
import sys
from datetime import datetime
from typing import Any

import psycopg2

from waittime.core.enums import EndEvent, MetricFamily, PatientScope, StartEvent, StatisticType
from waittime.services.database import DatabaseService, PreservationInventorySchemaError

_SOURCE_IDS = frozenset({"alberta-ahs", "bc-phsa", "ontario-health", "quebec-msss"})
_PERIOD_TYPES = frozenset({"hourly", "daily", "weekly", "monthly"})
_METRIC_FAMILIES = frozenset(item.value for item in MetricFamily)
_START_EVENTS = frozenset(item.value for item in StartEvent)
_END_EVENTS = frozenset(item.value for item in EndEvent)
_STATISTIC_TYPES = frozenset(item.value for item in StatisticType)
_PATIENT_SCOPES = frozenset(item.value for item in PatientScope)
_RAW_GROUP_KEYS = frozenset(
    {
        "source_id",
        "metric_family",
        "start_event",
        "end_event",
        "statistic_type",
        "patient_scope",
        "row_count",
        "oldest_timestamp_utc",
        "newest_timestamp_utc",
        "rows_older_than_30_days",
        "future_timestamp_rows",
        "missing_source_id_count",
        "missing_payload_hash_count",
        "missing_parser_version_count",
        "absent_optional_payload_snippet_count",
    }
)
_AGGREGATE_GROUP_KEYS = frozenset(
    {
        "source_id",
        "period_type",
        "metric_family",
        "start_event",
        "end_event",
        "statistic_type",
        "aggregate_row_count",
        "aggregate_sample_count_sum",
        "oldest_period_start_utc",
        "newest_period_end_utc",
        "newest_aggregate_created_at_utc",
    }
)
_UTC_TIMESTAMP_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{6})?Z")


class PreservationInventoryOutputContractError(Exception):
    """Raised when inventory output contains fields outside its public contract."""


def _require_exact_object(value: Any, keys: frozenset[str]) -> dict[str, Any]:
    if type(value) is not dict or value.keys() != keys:
        raise PreservationInventoryOutputContractError
    return value


def _require_label(value: Any, allowed: frozenset[str], *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str or value not in allowed:
        raise PreservationInventoryOutputContractError
    return value


def _require_count(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise PreservationInventoryOutputContractError
    return value


def _require_fixed_string(value: Any, expected: str) -> str:
    if type(value) is not str or value != expected:
        raise PreservationInventoryOutputContractError
    return value


def _require_timestamp(value: Any, *, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str or _UTC_TIMESTAMP_PATTERN.fullmatch(value) is None:
        raise PreservationInventoryOutputContractError
    try:
        parsed = datetime.fromisoformat(f"{value[:-1]}+00:00")
    except ValueError as exc:
        raise PreservationInventoryOutputContractError from exc
    if parsed.isoformat().replace("+00:00", "Z") != value:
        raise PreservationInventoryOutputContractError
    return value


def _validate_raw_group(value: Any) -> dict[str, Any]:
    group = _require_exact_object(value, _RAW_GROUP_KEYS)
    return {
        "source_id": _require_label(group["source_id"], _SOURCE_IDS, nullable=True),
        "metric_family": _require_label(group["metric_family"], _METRIC_FAMILIES, nullable=True),
        "start_event": _require_label(group["start_event"], _START_EVENTS, nullable=True),
        "end_event": _require_label(group["end_event"], _END_EVENTS, nullable=True),
        "statistic_type": _require_label(group["statistic_type"], _STATISTIC_TYPES, nullable=True),
        "patient_scope": _require_label(group["patient_scope"], _PATIENT_SCOPES, nullable=True),
        "row_count": _require_count(group["row_count"]),
        "oldest_timestamp_utc": _require_timestamp(group["oldest_timestamp_utc"], nullable=True),
        "newest_timestamp_utc": _require_timestamp(group["newest_timestamp_utc"], nullable=True),
        "rows_older_than_30_days": _require_count(group["rows_older_than_30_days"]),
        "future_timestamp_rows": _require_count(group["future_timestamp_rows"]),
        "missing_source_id_count": _require_count(group["missing_source_id_count"]),
        "missing_payload_hash_count": _require_count(group["missing_payload_hash_count"]),
        "missing_parser_version_count": _require_count(group["missing_parser_version_count"]),
        "absent_optional_payload_snippet_count": _require_count(
            group["absent_optional_payload_snippet_count"]
        ),
    }


def _validate_aggregate_group(value: Any) -> dict[str, Any]:
    group = _require_exact_object(value, _AGGREGATE_GROUP_KEYS)
    return {
        "source_id": _require_label(group["source_id"], _SOURCE_IDS, nullable=True),
        "period_type": _require_label(group["period_type"], _PERIOD_TYPES, nullable=True),
        "metric_family": _require_label(group["metric_family"], _METRIC_FAMILIES, nullable=True),
        "start_event": _require_label(group["start_event"], _START_EVENTS, nullable=True),
        "end_event": _require_label(group["end_event"], _END_EVENTS, nullable=True),
        "statistic_type": _require_label(group["statistic_type"], _STATISTIC_TYPES, nullable=True),
        "aggregate_row_count": _require_count(group["aggregate_row_count"]),
        "aggregate_sample_count_sum": _require_count(group["aggregate_sample_count_sum"]),
        "oldest_period_start_utc": _require_timestamp(
            group["oldest_period_start_utc"], nullable=True
        ),
        "newest_period_end_utc": _require_timestamp(group["newest_period_end_utc"], nullable=True),
        "newest_aggregate_created_at_utc": _require_timestamp(
            group["newest_aggregate_created_at_utc"], nullable=True
        ),
    }


def _validate_preservation_inventory(value: Any) -> dict[str, Any]:
    """Rebuild the public report from its fixed shape and approved label vocabularies."""
    inventory = _require_exact_object(
        value,
        frozenset(
            {
                "status",
                "transaction_read_only",
                "statement_timeout",
                "snapshot_at_utc",
                "retention_threshold_days",
                "retention_cutoff_utc",
                "retention_threshold_basis",
                "raw_measurements",
                "aggregates",
                "purge_execution_history",
                "provider_backup_pitr_restore_evidence",
            }
        ),
    )
    raw = _require_exact_object(
        inventory["raw_measurements"],
        frozenset({"groups", "sources_without_measurements", "provenance_schema_nullable"}),
    )
    aggregates = _require_exact_object(inventory["aggregates"], frozenset({"groups", "scope"}))
    nullable_schema = _require_exact_object(
        raw["provenance_schema_nullable"],
        frozenset({"source_id", "raw_payload_hash", "parser_version", "raw_payload_snippet"}),
    )

    if (
        type(inventory["transaction_read_only"]) is not bool
        or not inventory["transaction_read_only"]
    ):
        raise PreservationInventoryOutputContractError
    if (
        type(inventory["retention_threshold_days"]) is not int
        or inventory["retention_threshold_days"] != 30
    ):
        raise PreservationInventoryOutputContractError
    _require_fixed_string(inventory["status"], "complete")
    if type(inventory["statement_timeout"]) is not str or inventory["statement_timeout"] not in {
        "5s",
        "5000ms",
    }:
        raise PreservationInventoryOutputContractError
    _require_fixed_string(
        inventory["retention_threshold_basis"], "30 elapsed 24-hour days from the UTC snapshot"
    )
    _require_fixed_string(inventory["purge_execution_history"], "not_assessed")
    _require_fixed_string(inventory["provider_backup_pitr_restore_evidence"], "not_assessed")
    _require_fixed_string(
        aggregates["scope"], "summary-row coverage only; not a raw-measurement backup"
    )
    if type(raw["groups"]) is not list or type(aggregates["groups"]) is not list:
        raise PreservationInventoryOutputContractError
    if type(raw["sources_without_measurements"]) is not list:
        raise PreservationInventoryOutputContractError
    if any(type(value) is not bool for value in nullable_schema.values()):
        raise PreservationInventoryOutputContractError

    raw_groups = [_validate_raw_group(group) for group in raw["groups"]]
    aggregate_groups = [_validate_aggregate_group(group) for group in aggregates["groups"]]
    sources_without_measurements = [
        _require_label(source_id, _SOURCE_IDS) for source_id in raw["sources_without_measurements"]
    ]
    snapshot_at = _require_timestamp(inventory["snapshot_at_utc"])
    retention_cutoff = _require_timestamp(inventory["retention_cutoff_utc"])

    return {
        "status": "complete",
        "transaction_read_only": True,
        "statement_timeout": "5000ms",
        "snapshot_at_utc": snapshot_at,
        "retention_threshold_days": 30,
        "retention_cutoff_utc": retention_cutoff,
        "retention_threshold_basis": "30 elapsed 24-hour days from the UTC snapshot",
        "raw_measurements": {
            "groups": raw_groups,
            "sources_without_measurements": sources_without_measurements,
            "provenance_schema_nullable": {
                key: nullable_schema[key]
                for key in (
                    "source_id",
                    "raw_payload_hash",
                    "parser_version",
                    "raw_payload_snippet",
                )
            },
        },
        "aggregates": {
            "groups": aggregate_groups,
            "scope": "summary-row coverage only; not a raw-measurement backup",
        },
        "purge_execution_history": "not_assessed",
        "provider_backup_pitr_restore_evidence": "not_assessed",
    }


def _format_bytes(num_bytes: int) -> str:
    """Return a human-readable byte string."""
    units = ["B", "KiB", "MiB", "GiB", "TiB"]
    value = float(num_bytes)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{num_bytes} B"


def _build_output(stats: dict[str, Any]) -> dict[str, Any]:
    """Add human-readable size fields to storage stats."""
    return {
        **stats,
        "table_size_pretty": _format_bytes(int(stats["table_bytes"])),
        "index_size_pretty": _format_bytes(int(stats["index_bytes"])),
        "total_size_pretty": _format_bytes(int(stats["total_bytes"])),
    }


def main() -> int:
    """Print relation storage stats."""
    parser = argparse.ArgumentParser(
        description="Report row-count and storage metadata for a PostgreSQL relation."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--relation",
        default="measurements",
        help="Relation name to inspect (default: measurements)",
    )
    mode.add_argument(
        "--preservation-inventory",
        action="store_true",
        help=(
            "Opt in to an exact, bounded full-table raw-measurement and aggregate metadata scan; "
            "validates the fixed metadata-only output contract before emitting JSON"
        ),
    )
    parser.add_argument(
        "--exact-count",
        action="store_true",
        help="Also run COUNT(*) for an exact row count",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of text",
    )
    args = parser.parse_args()

    if args.preservation_inventory:
        if args.exact_count:
            parser.error("--exact-count is not applicable to --preservation-inventory")
        try:
            inventory = _validate_preservation_inventory(
                DatabaseService().get_measurement_preservation_inventory()
            )
            print(json.dumps(inventory, sort_keys=True))
            return 0
        except PreservationInventoryOutputContractError:
            print(
                json.dumps(
                    {"status": "error", "error_class": "output_contract_mismatch"},
                    sort_keys=True,
                ),
                file=sys.stderr,
            )
            return 1
        except Exception as exc:
            # Database errors can contain connection details or SQL fragments.
            # Return only a small fixed class, never the exception text.
            error_class = "inventory_failed"
            if isinstance(exc, psycopg2.Error):
                if exc.pgcode == "57014":
                    error_class = "statement_timeout"
                elif exc.pgcode in {"42703", "42P01", "42704"}:
                    error_class = "schema_mismatch"
                elif isinstance(exc, psycopg2.OperationalError):
                    error_class = "database_unavailable"
                else:
                    error_class = "database_query_failed"
            elif isinstance(exc, PreservationInventorySchemaError):
                error_class = "schema_mismatch"
            elif isinstance(exc, ValueError):
                error_class = "configuration_missing"
            print(
                json.dumps({"status": "error", "error_class": error_class}, sort_keys=True),
                file=sys.stderr,
            )
            return 1

    try:
        db = DatabaseService()
        stats = _build_output(
            db.get_relation_storage_stats(
                relation_name=args.relation,
                exact_count=args.exact_count,
            )
        )

        if args.json:
            print(json.dumps(stats, sort_keys=True))
        else:
            print(f"Relation: {stats['relation_name']}")
            print(f"Estimated rows: {stats['estimated_row_count']}")
            if stats["exact_row_count"] is not None:
                print(f"Exact rows: {stats['exact_row_count']}")
            print(f"Table size: {stats['table_size_pretty']}")
            print(f"Index size: {stats['index_size_pretty']}")
            print(f"Total size: {stats['total_size_pretty']}")
        return 0
    except Exception as exc:
        print(f"storage stats failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
