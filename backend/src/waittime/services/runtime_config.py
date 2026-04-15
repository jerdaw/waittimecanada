"""Shared runtime configuration helpers for backend operational defaults."""

import os

DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES = 120


def get_heartbeat_stale_threshold_minutes() -> int:
    """Return the live heartbeat stale threshold, honoring env overrides."""
    return int(
        os.environ.get(
            "HEARTBEAT_STALE_THRESHOLD_MINUTES",
            str(DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES),
        )
    )
