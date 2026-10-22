"""Offline verification for private measurement archives.

This command opens only local archive files. It has no export, database, or
cleanup subcommand; an offline read-back check is not an actual PostgreSQL
restore.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from waittime.services.measurement_archive import (
    MeasurementArchiveError,
    verify_measurement_archive,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify a private Wait Time Canada measurement archive"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("verify", "restore-check"):
        command_parser = subparsers.add_parser(
            command,
            help=(
                "verify archive hashes and exact rows"
                if command == "verify"
                else "verify offline parse/serialize read-back (not a PostgreSQL restore)"
            ),
        )
        command_parser.add_argument("archive_directory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        result = verify_measurement_archive(args.archive_directory)
    except MeasurementArchiveError:
        print("Measurement archive verification failed.", file=sys.stderr)
        return 2

    output = {
        "status": "verified",
        "check": "offline_readback" if args.command == "restore-check" else "integrity",
        "actual_postgresql_restore": False,
        "row_count": result.row_count,
        "first_measurement_id": result.first_measurement_id,
        "last_measurement_id": result.last_measurement_id,
        "artifact_sha256": result.artifact_sha256,
        "manifest_sha256": result.manifest_sha256,
        "snapshot_id": result.snapshot_id,
        "offline_readback_verified": result.offline_readback_verified,
    }
    print(json.dumps(output, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
