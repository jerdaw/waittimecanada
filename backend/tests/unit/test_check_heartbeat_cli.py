from unittest.mock import patch

from waittime.cli.check_heartbeat import _get_sources_to_check


def test_get_sources_to_check_uses_operational_scrapers_by_default():
    with patch(
        "waittime.cli.check_heartbeat.SCRAPERS",
        {"quebec-msss": object(), "bc-phsa": object(), "alberta-ahs": object()},
    ):
        assert _get_sources_to_check(None) == ["alberta-ahs", "bc-phsa", "quebec-msss"]


def test_get_sources_to_check_respects_explicit_source():
    with patch(
        "waittime.cli.check_heartbeat.SCRAPERS",
        {"quebec-msss": object(), "bc-phsa": object()},
    ):
        assert _get_sources_to_check("manitoba-shared-health") == ["manitoba-shared-health"]
