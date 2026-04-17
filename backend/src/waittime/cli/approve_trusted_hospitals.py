"""CLI to approve hospitals from trusted government sources.

All four current provincial data sources (Health Quality Ontario, Quebec MSSS,
Alberta AHS, BC PHSA) are official government health authority websites.
Hospitals scraped from these sources should be auto-approved (is_verified=true,
is_visible=true) per project policy.  Quality is enforced through automated
controls: anomaly detection, payload hashing, parser versioning, and heartbeat
monitoring.

This command is a one-time backfill for hospitals that were created before
the auto-approval policy was implemented in the scraper CLI.

Usage:
    python -m waittime.cli.approve_trusted_hospitals --dry-run
    python -m waittime.cli.approve_trusted_hospitals
"""

import argparse
import logging
import sys

from waittime.services.database import DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# All current sources are trusted government health authority websites.
TRUSTED_SOURCE_IDS = [
    "alberta-ahs",
    "bc-phsa",
    "ontario-health",
    "quebec-msss",
]


def main() -> int:
    """Approve all hospitals from trusted government sources."""
    parser = argparse.ArgumentParser(
        description="Approve hospitals from trusted government data sources",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying the database",
    )
    args = parser.parse_args()

    try:
        db = DatabaseService()
    except ValueError as e:
        logger.error(str(e))
        return 1

    total_approved = 0
    total_already = 0

    for source_id in TRUSTED_SOURCE_IDS:
        hospitals = db.get_hospitals_by_source(source_id)
        needs_approval = [h for h in hospitals if not h.is_verified or not h.is_visible]

        if not needs_approval:
            already = len(hospitals)
            total_already += already
            logger.info(f"{source_id}: {already} hospital(s) already approved, 0 to update")
            continue

        if args.dry_run:
            for h in needs_approval:
                logger.info(f"  [DRY RUN] Would approve: {h.name} ({h.id})")
            logger.info(f"{source_id}: {len(needs_approval)} hospital(s) would be approved")
        else:
            for h in needs_approval:
                db.verify_hospital(h.id, make_visible=True)
                logger.info(f"  Approved: {h.name} ({h.id})")
            logger.info(f"{source_id}: {len(needs_approval)} hospital(s) approved")

        total_approved += len(needs_approval)
        total_already += len(hospitals) - len(needs_approval)

    action = "would approve" if args.dry_run else "approved"
    logger.info(f"Done: {action} {total_approved} hospital(s), {total_already} already approved")
    return 0


if __name__ == "__main__":
    sys.exit(main())
