from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from waittime.cli.check_public_health_hub_ingest import (
    _build_degraded_fingerprint,
    _format_incident_duration,
    _get_sources_to_check,
    evaluate_source_status,
    reconcile_incident_state,
)
from waittime.cli.public_health_hub_status import SourceOperationalAssessment
from waittime.core import PublicHealthSourceAlertState
from waittime.services.database import PublicHealthSourceStatus


def _make_status(**overrides) -> PublicHealthSourceStatus:
    base = {
        "source_id": "mohserlo",
        "source_name": "MOHSERLO",
        "domain": "provider_facility",
        "recommended_usage_mode": "scheduled_ingest",
        "freshness_sensitivity": "low",
        "last_refreshed_at": datetime(2026, 3, 27, 19, 5, tzinfo=UTC),
        "resource_record_count": 321,
        "alert_record_count": 0,
        "system_metric_record_count": 0,
        "latest_alert_published_at": None,
    }
    base.update(overrides)
    return PublicHealthSourceStatus(**base)


def _make_assessment(
    *,
    state: str,
    reasons: list[str],
    **status_overrides,
) -> SourceOperationalAssessment:
    return SourceOperationalAssessment(
        status=_make_status(**status_overrides),
        state=state,
        reasons=reasons,
    )


def test_get_sources_to_check_defaults_to_hard_fail_sources():
    assert _get_sources_to_check([]) == [
        "health-canada-recalls",
        "mohserlo",
        "ontario-land-ambulance-response-times",
    ]


def test_build_degraded_fingerprint_normalizes_reason_whitespace():
    fingerprint_a = _build_degraded_fingerprint(
        "mohserlo",
        ["Refresh age exceeds suppress threshold (4d)\n", "No   normalized rows"],
    )
    fingerprint_b = _build_degraded_fingerprint(
        "mohserlo",
        ["refresh age exceeds suppress threshold (4d)", "no normalized rows"],
    )

    assert fingerprint_a == fingerprint_b


def test_evaluate_source_status_marks_degraded_assessment_as_incident():
    evaluation = evaluate_source_status(
        _make_assessment(
            state="degraded",
            reasons=["No normalized resource rows available"],
            resource_record_count=0,
        )
    )

    assert evaluation.ok is False
    assert evaluation.incident is not None
    assert evaluation.incident.kind == "degraded"
    assert "degraded" in evaluation.summary
    assert "system_metrics=0" in evaluation.details[0]


def test_reconcile_incident_state_opens_new_degraded_incident():
    alerts = MagicMock()
    db = MagicMock()
    evaluation = evaluate_source_status(
        _make_assessment(
            state="degraded",
            reasons=["No normalized alert rows available"],
            source_id="health-canada-recalls",
            source_name="Health Canada Recalls and Safety Alerts",
            domain="safety_alert",
            alert_record_count=0,
        )
    )

    reconcile_incident_state(
        "health-canada-recalls",
        "Health Canada Recalls and Safety Alerts",
        evaluation,
        None,
        alerts=alerts,
        db=db,
        run_url="https://github.com/example/run",
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_public_health_source_degraded.assert_called_once()
    db.open_public_health_source_alert_incident.assert_called_once()


def test_reconcile_incident_state_resolves_recovered_incident():
    alerts = MagicMock()
    db = MagicMock()
    evaluation = evaluate_source_status(
        _make_assessment(
            state="healthy",
            reasons=["Freshness and normalized row checks passed"],
        )
    )

    reconcile_incident_state(
        "mohserlo",
        "MOHSERLO",
        evaluation,
        PublicHealthSourceAlertState(
            source_id="mohserlo",
            active_incident_kind="degraded",
            active_incident_fingerprint="degraded:mohserlo:abc123",
            opened_at=datetime.now(UTC) - timedelta(hours=2, minutes=5),
        ),
        alerts=alerts,
        db=db,
        run_url="https://github.com/example/run",
        dry_run=False,
        now=datetime.now(UTC),
    )

    alerts.alert_public_health_source_resolved.assert_called_once()
    db.resolve_public_health_source_alert_incident.assert_called_once_with("mohserlo")


def test_format_incident_duration_compacts_elapsed_time():
    now = datetime.now(UTC)
    assert _format_incident_duration(now - timedelta(minutes=5), now) == "5m"
    assert _format_incident_duration(now - timedelta(hours=2), now) == "2h"
    assert _format_incident_duration(now - timedelta(hours=2, minutes=5), now) == "2h 5m"
