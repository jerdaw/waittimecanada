from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

from waittime.cli.check_heartbeat import (
    _build_error_fingerprint,
    _format_incident_duration,
    _get_sources_to_check,
    evaluate_source_status,
    reconcile_incident_state,
)


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


def test_evaluate_source_status_marks_missing_heartbeat_as_stale():
    evaluation = evaluate_source_status(
        "ontario-health",
        None,
        max_age=120,
        max_consecutive_failures=1,
        now=datetime.now(UTC),
    )

    assert evaluation.ok is False
    assert evaluation.incident is not None
    assert evaluation.incident.kind == "stale"
    assert evaluation.incident.fingerprint == "stale:ontario-health"


def test_error_fingerprint_normalizes_whitespace_noise():
    fingerprint_a = _build_error_fingerprint(
        "ontario-health",
        "upstream_unavailable",
        "fetch",
        "Timed out\nwhile   connecting",
    )
    fingerprint_b = _build_error_fingerprint(
        "ontario-health",
        "upstream_unavailable",
        "fetch",
        "timed out while connecting",
    )

    assert fingerprint_a == fingerprint_b


def test_reconcile_incident_state_opens_new_incident():
    alerts = MagicMock()
    alerts.should_send_operational_notification.return_value = True
    alerts.alert_scraper_stale.return_value = True
    db = MagicMock()
    evaluation = evaluate_source_status(
        "ontario-health",
        {
            "last_run": datetime.now(UTC) - timedelta(minutes=140),
            "status": "healthy",
            "measurements_count": 1,
            "consecutive_failures": 0,
            "last_success_run": None,
            "last_success_measurements_count": None,
            "last_error_run": None,
            "last_error_category": None,
            "last_error_stage": None,
        },
        max_age=120,
        max_consecutive_failures=1,
        now=datetime.now(UTC),
    )

    reconcile_incident_state(
        "ontario-health",
        evaluation,
        None,
        alerts=alerts,
        db=db,
        run_url=None,
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_scraper_stale.assert_called_once()
    db.open_scraper_alert_incident.assert_called_once_with(
        "ontario-health",
        "stale",
        "stale:ontario-health",
        "P2",
    )


def test_reconcile_incident_state_suppresses_duplicate_incident():
    alerts = MagicMock()
    alerts.config.operational_notification_mode = "normal"
    db = MagicMock()
    evaluation = evaluate_source_status(
        "ontario-health",
        {
            "last_run": datetime.now(UTC) - timedelta(minutes=140),
            "status": "healthy",
            "measurements_count": 1,
            "consecutive_failures": 0,
            "last_success_run": None,
            "last_success_measurements_count": None,
            "last_error_run": None,
            "last_error_category": None,
            "last_error_stage": None,
        },
        max_age=120,
        max_consecutive_failures=1,
        now=datetime.now(UTC),
    )

    reconcile_incident_state(
        "ontario-health",
        evaluation,
        {
            "active_incident_kind": "stale",
            "active_incident_fingerprint": "stale:ontario-health",
            "opened_at": datetime.now(UTC) - timedelta(minutes=20),
        },
        alerts=alerts,
        db=db,
        run_url=None,
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_scraper_stale.assert_not_called()
    alerts.alert_scraper_resolved.assert_not_called()
    db.open_scraper_alert_incident.assert_not_called()
    db.resolve_scraper_alert_incident.assert_not_called()


def test_reconcile_incident_state_resolves_on_recovery():
    alerts = MagicMock()
    alerts.config.operational_notification_mode = "normal"
    db = MagicMock()
    evaluation = evaluate_source_status(
        "ontario-health",
        {
            "last_run": datetime.now(UTC) - timedelta(minutes=30),
            "status": "healthy",
            "measurements_count": 10,
            "consecutive_failures": 0,
            "last_success_run": datetime.now(UTC) - timedelta(minutes=30),
            "last_success_measurements_count": 10,
            "last_error_run": None,
            "last_error_category": None,
            "last_error_stage": None,
        },
        max_age=120,
        max_consecutive_failures=1,
        now=datetime.now(UTC),
    )

    reconcile_incident_state(
        "ontario-health",
        evaluation,
        {
            "active_incident_kind": "stale",
            "active_incident_fingerprint": "stale:ontario-health",
            "opened_at": datetime.now(UTC) - timedelta(hours=2, minutes=5),
        },
        alerts=alerts,
        db=db,
        run_url="https://github.com/example/run",
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_scraper_resolved.assert_called_once()
    db.resolve_scraper_alert_incident.assert_called_once_with("ontario-health")


def test_reconcile_incident_state_switches_between_incident_types():
    alerts = MagicMock()
    alerts.config.operational_notification_mode = "normal"
    alerts.should_send_operational_notification.return_value = True
    alerts.alert_scraper_error.return_value = True
    db = MagicMock()
    evaluation = evaluate_source_status(
        "ontario-health",
        {
            "last_run": datetime.now(UTC) - timedelta(minutes=3),
            "status": "error",
            "error_message": "timed out",
            "measurements_count": 0,
            "consecutive_failures": 2,
            "last_success_run": datetime.now(UTC) - timedelta(hours=3),
            "last_success_measurements_count": 10,
            "last_error_run": datetime.now(UTC) - timedelta(minutes=3),
            "last_error_category": "upstream_unavailable",
            "last_error_stage": "fetch",
        },
        max_age=120,
        max_consecutive_failures=1,
        now=datetime.now(UTC),
    )

    reconcile_incident_state(
        "ontario-health",
        evaluation,
        {
            "active_incident_kind": "stale",
            "active_incident_fingerprint": "stale:ontario-health",
            "opened_at": datetime.now(UTC) - timedelta(hours=1),
        },
        alerts=alerts,
        db=db,
        run_url="https://github.com/example/run",
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_scraper_resolved.assert_called_once()
    alerts.alert_scraper_error.assert_called_once()
    db.open_scraper_alert_incident.assert_called_once_with(
        "ontario-health",
        "error",
        evaluation.incident.fingerprint,
        "P2",
    )


def test_reconcile_incident_state_tracks_suppressed_incident_in_critical_only():
    alerts = MagicMock()
    alerts.config.operational_notification_mode = "critical_only"
    alerts.should_send_operational_notification.return_value = False
    db = MagicMock()
    evaluation = evaluate_source_status(
        "ontario-health",
        {
            "last_run": datetime.now(UTC) - timedelta(minutes=800),
            "status": "healthy",
            "measurements_count": 1,
            "consecutive_failures": 0,
            "last_success_run": None,
            "last_success_measurements_count": None,
            "last_error_run": None,
            "last_error_category": None,
            "last_error_stage": None,
        },
        max_age=720,
        max_consecutive_failures=6,
        now=datetime.now(UTC),
    )

    reconcile_incident_state(
        "ontario-health",
        evaluation,
        None,
        alerts=alerts,
        db=db,
        run_url=None,
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_scraper_stale.assert_not_called()
    db.open_scraper_alert_incident.assert_called_once_with(
        "ontario-health",
        "stale",
        "stale:ontario-health",
        None,
    )


def test_reconcile_incident_state_suppresses_recovery_without_prior_critical_page():
    alerts = MagicMock()
    alerts.config.operational_notification_mode = "critical_only"
    db = MagicMock()
    evaluation = evaluate_source_status(
        "ontario-health",
        {
            "last_run": datetime.now(UTC) - timedelta(minutes=30),
            "status": "healthy",
            "measurements_count": 10,
            "consecutive_failures": 0,
            "last_success_run": datetime.now(UTC) - timedelta(minutes=30),
            "last_success_measurements_count": 10,
            "last_error_run": None,
            "last_error_category": None,
            "last_error_stage": None,
        },
        max_age=720,
        max_consecutive_failures=6,
        now=datetime.now(UTC),
    )

    reconcile_incident_state(
        "ontario-health",
        evaluation,
        {
            "active_incident_kind": "stale",
            "active_incident_fingerprint": "stale:ontario-health",
            "opened_at": datetime.now(UTC) - timedelta(hours=2),
            "active_incident_notified_tier": None,
        },
        alerts=alerts,
        db=db,
        run_url="https://github.com/example/run",
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_scraper_resolved.assert_not_called()
    db.resolve_scraper_alert_incident.assert_called_once_with("ontario-health")


def test_format_incident_duration_compacts_elapsed_time():
    now = datetime.now(UTC)
    assert _format_incident_duration(now - timedelta(minutes=5), now) == "5m"
    assert _format_incident_duration(now - timedelta(hours=2), now) == "2h"
    assert _format_incident_duration(now - timedelta(hours=2, minutes=5), now) == "2h 5m"
