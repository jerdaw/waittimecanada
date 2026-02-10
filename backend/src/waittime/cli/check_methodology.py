"""Check for methodology changes in data sources."""

import argparse
import logging
import sys

from waittime.services.database import DatabaseService
from waittime.services.methodology_change import MethodologyChangeDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Check for methodology changes and alert."""
    parser = argparse.ArgumentParser(description="Check for methodology changes")
    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Check specific source (default: all sources)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print status without saving events",
    )
    args = parser.parse_args()

    try:
        db = DatabaseService()
        detector = MethodologyChangeDetector(db)

        if args.source:
            logger.info(f"Checking source {args.source} for methodology changes...")
            result = detector.check_source(args.source)
            results = [result]
        else:
            logger.info("Checking all sources for methodology changes...")
            results = detector.check_all_sources()

        changes_found = 0
        for res in results:
            if res["change_detected"]:
                changes_found += 1
                details = res["details"]
                print(f"⚠️  CHANGE DETECTED for {res['source_id']}:")
                print(f"   {details['explanation']}")
                print(f"   Shift: {details['shift_percent']}%")
                print(f"   Previous Mean: {details['previous_period_mean']}")
                print(f"   Current Mean: {details['current_period_mean']}")
                print("-" * 40)
            else:
                logger.info(f"Analysis complete for {res['source_id']}: No change detected.")

        if changes_found > 0:
            print(f"\nFound {changes_found} potential methodology changes.")
            # We could add alerting here if needed (e.g., Slack/Email)
            sys.exit(1)  # Exit non-zero to indicate "something passed threshold"
        else:
            print("\nNo methodology changes detected.")
            sys.exit(0)

    except Exception as e:
        logger.exception(f"Methodology check failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
