"""CLI for inspecting relation storage growth."""

import argparse
import json
import sys
from typing import Any

import psycopg2

from waittime.services.database import DatabaseService, PreservationInventorySchemaError


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
            "always emits value-free JSON"
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
            inventory = DatabaseService().get_measurement_preservation_inventory()
            print(json.dumps(inventory, sort_keys=True))
            return 0
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
