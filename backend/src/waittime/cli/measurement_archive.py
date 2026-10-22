"""Opt-in export and offline verification for measurement archives.

Export requires an explicit destination, policy references, expiry, and an
intent flag. It is not a database backup or PostgreSQL restore. Verification
commands open only local archive files; offline read-back is not an actual
PostgreSQL restore.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import NoReturn

from waittime.services.database import DatabaseService
from waittime.services.measurement_archive import (
    ArchiveUsePolicy,
    MeasurementArchiveError,
    export_measurement_archive,
    verify_measurement_archive,
)


class _SafeArgumentParser(argparse.ArgumentParser):
    """Avoid echoing invalid argument values, which may contain sensitive text."""

    def error(self, message: str) -> NoReturn:
        del message
        self.print_usage(sys.stderr)
        self.exit(2, f"{self.prog}: invalid arguments\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = _SafeArgumentParser(
        description="Export or verify a private Wait Time Canada measurement archive"
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
    export_parser = subparsers.add_parser(
        "export",
        help="explicitly export stored measurements to a new archive directory",
        description=(
            "Create a private measurements-only archive. This is not a database backup "
            "or PostgreSQL restore. Separate authorization is required."
        ),
    )
    export_parser.add_argument("--destination", type=Path, required=True)
    export_parser.add_argument("--policy-reference", required=True)
    export_parser.add_argument("--access-control-reference", required=True)
    export_parser.add_argument(
        "--expires-at-utc",
        required=True,
        help="timezone-aware ISO 8601 expiry timestamp, for example 2027-10-18T12:00:00Z",
    )
    export_parser.add_argument(
        "--confirm-export",
        action="store_true",
        required=True,
        help="confirm explicit export intent (does not establish authorization)",
    )
    return parser


def _validate_export_arguments(args: argparse.Namespace) -> ArchiveUsePolicy:
    policy_reference = args.policy_reference.strip()
    access_reference = args.access_control_reference.strip()
    for reference in (policy_reference, access_reference):
        if (
            not reference
            or len(reference) > 256
            or any(ord(character) < 32 or ord(character) == 127 for character in reference)
        ):
            raise ValueError("invalid policy reference")

    try:
        expires_at = datetime.fromisoformat(args.expires_at_utc.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid expiry timestamp") from exc
    if expires_at.tzinfo is None or expires_at.utcoffset() is None:
        raise ValueError("expiry timestamp must include a timezone")
    if expires_at.astimezone(UTC) <= datetime.now(UTC):
        raise ValueError("expiry timestamp must be in the future")

    destination: Path = args.destination
    if not destination.name or destination.name in {".", ".."}:
        raise ValueError("invalid destination")
    try:
        parent = destination.parent.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("destination parent is unavailable") from exc
    if not parent.is_dir() or os.path.lexists(parent / destination.name):
        raise ValueError("destination is unavailable")

    return ArchiveUsePolicy(
        policy_reference=policy_reference,
        access_control_reference=access_reference,
        expires_at_utc=expires_at,
    )


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    if args.command == "export":
        try:
            policy = _validate_export_arguments(args)
        except (OSError, ValueError):
            print(
                json.dumps({"error": "invalid_export_options", "status": "failed"}),
                file=sys.stderr,
            )
            return 2

        try:
            result = export_measurement_archive(
                DatabaseService(),
                args.destination,
                policy=policy,
            )
        except Exception:
            # Driver, path, and configuration exceptions can contain connection
            # details or archive paths. Keep CLI failures fixed and value-free.
            print(json.dumps({"error": "export_failed", "status": "failed"}), file=sys.stderr)
            return 2

        print(
            json.dumps(
                {
                    "status": "exported",
                    "row_count": result.row_count,
                    "artifact_sha256": result.artifact_sha256,
                    "manifest_sha256": result.manifest_sha256,
                    "offline_readback_verified": result.offline_readback_verified,
                    "actual_postgresql_restore": False,
                },
                sort_keys=True,
            )
        )
        return 0

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
