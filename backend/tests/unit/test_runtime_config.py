"""Tests for backend runtime configuration helpers."""

from __future__ import annotations

import pytest

from waittime.services.runtime_config import (
    DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES,
    get_heartbeat_stale_threshold_minutes,
)


@pytest.mark.unit
def test_heartbeat_stale_threshold_defaults_to_120_minutes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Missing override should use the documented heartbeat stale default."""
    monkeypatch.delenv("HEARTBEAT_STALE_THRESHOLD_MINUTES", raising=False)

    assert DEFAULT_HEARTBEAT_STALE_THRESHOLD_MINUTES == 120
    assert get_heartbeat_stale_threshold_minutes() == 120


@pytest.mark.unit
def test_heartbeat_stale_threshold_honors_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Runtime override should come from the process environment."""
    monkeypatch.setenv("HEARTBEAT_STALE_THRESHOLD_MINUTES", "45")

    assert get_heartbeat_stale_threshold_minutes() == 45
