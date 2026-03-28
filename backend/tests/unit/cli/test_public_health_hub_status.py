from datetime import UTC, datetime

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
        "latest_alert_published_at": None,
    }
    base.update(overrides)
    return PublicHealthSourceStatus(**base)


def test_render_markdown_includes_counts_and_timestamps():
    from waittime.cli.public_health_hub_status import _render_markdown, assess_source_status

    rendered = _render_markdown(
        [
            assess_source_status(_make_status(), now=datetime(2026, 3, 27, 20, 0, tzinfo=UTC)),
            assess_source_status(
                _make_status(
                    source_id="health-canada-recalls",
                    source_name="Health Canada Recalls",
                    domain="safety_alert",
                    resource_record_count=0,
                    alert_record_count=42,
                    latest_alert_published_at=datetime(2026, 3, 27, 18, 30, tzinfo=UTC),
                ),
                now=datetime(2026, 3, 27, 20, 0, tzinfo=UTC),
            ),
        ],
        generated_at=datetime(2026, 3, 27, 20, 0, tzinfo=UTC),
    )

    assert "## Public Health Hub Source Status" in rendered
    assert "Overall state: `healthy`" in rendered
    assert "`mohserlo`<br>MOHSERLO" in rendered
    assert "✅ healthy" in rendered
    assert "| provider_facility | 2026-03-27T19:05:00+00:00 | 321 | 0 | never |" in rendered
    assert "Health Canada Recalls" in rendered
    assert "2026-03-27T18:30:00+00:00" in rendered


def test_render_text_handles_empty_statuses():
    from waittime.cli.public_health_hub_status import _render_text

    rendered = _render_text([], generated_at=datetime(2026, 3, 27, 20, 0, tzinfo=UTC))

    assert "Public Health Hub Status" in rendered
    assert "No public health hub sources found." in rendered


def test_assess_source_status_marks_best_effort_aed_as_partial_when_empty():
    from waittime.cli.public_health_hub_status import assess_source_status

    assessment = assess_source_status(
        _make_status(
            source_id="osm-aed",
            source_name="OpenStreetMap AED",
            domain="aed",
            last_refreshed_at=None,
            resource_record_count=0,
        ),
        now=datetime(2026, 3, 27, 20, 0, tzinfo=UTC),
    )

    assert assessment.state == "partial"
    assert "No successful refresh recorded yet" in assessment.reasons
    assert "No normalized resource rows available" in assessment.reasons


def test_assess_source_status_marks_stale_alert_feed_as_degraded():
    from waittime.cli.public_health_hub_status import assess_source_status

    assessment = assess_source_status(
        _make_status(
            source_id="health-canada-recalls",
            source_name="Health Canada Recalls",
            domain="safety_alert",
            resource_record_count=0,
            alert_record_count=12,
            last_refreshed_at=datetime(2026, 3, 24, 20, 0, tzinfo=UTC),
            latest_alert_published_at=datetime(2026, 3, 24, 19, 0, tzinfo=UTC),
        ),
        now=datetime(2026, 3, 27, 20, 0, tzinfo=UTC),
    )

    assert assessment.state == "degraded"
    assert any("suppress threshold" in reason for reason in assessment.reasons)
