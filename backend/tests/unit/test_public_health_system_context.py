from datetime import UTC, datetime

from waittime.services.public_health_system_context import (
    ONTARIO_LAND_AMBULANCE_AVERAGE_RESPONSE_TIMES_RESOURCE_URL,
    ONTARIO_LAND_AMBULANCE_PARAMEDIC_PERFORMANCE_RESOURCE_URL,
    normalize_average_response_times_and_call_volumes,
    normalize_paramedic_service_response_time_plans_and_performance,
)


def test_normalize_average_response_times_and_call_volumes_parses_numeric_fields() -> None:
    csv_text = """CACC Location,Reporting Year,Average Response Time,Call Volume,Organization ID
Toronto CACC,2024,8.4,"10,123",ORG-1
Ottawa CACC,2023,10,9876,ORG-2
"""

    records = normalize_average_response_times_and_call_volumes(
        csv_text,
        refreshed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 2
    assert records[0].series_key == "cacc_average_response_times"
    assert records[0].geography_name == "Toronto CACC"
    assert records[0].reporting_year == 2024
    assert records[0].metrics["average_response_time_minutes"] == 8.4
    assert records[0].metrics["call_volume"] == 10123
    assert records[0].provenance_url == ONTARIO_LAND_AMBULANCE_AVERAGE_RESPONSE_TIMES_RESOURCE_URL


def test_normalize_average_response_times_and_call_volumes_preserves_blank_metrics() -> None:
    csv_text = """CACC Location,Reporting Year,Average Response Time,Call Volume,Organization ID
Kingston CACC,2024,,,
"""

    records = normalize_average_response_times_and_call_volumes(
        csv_text,
        refreshed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 1
    assert records[0].metrics["average_response_time_minutes"] is None
    assert records[0].metrics["call_volume"] is None


def test_normalize_paramedic_performance_builds_stable_ids() -> None:
    csv_text = """Ambulance Service Coverage Area,Reporting Year,Patient Severity,Response Time Plan (minutes),Planned Response (%),Performance (%)
Durham Region,2024,CTAS 1,8,90,87.5
"""

    first = normalize_paramedic_service_response_time_plans_and_performance(
        csv_text,
        refreshed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
    )
    second = normalize_paramedic_service_response_time_plans_and_performance(
        csv_text,
        refreshed_at=datetime(2026, 4, 20, 12, 5, tzinfo=UTC),
    )

    assert len(first) == 1
    assert first[0].id == second[0].id
    assert first[0].series_key == "paramedic_service_response_performance"


def test_normalize_paramedic_performance_parses_blank_and_percent_values() -> None:
    csv_text = """Ambulance Service Coverage Area,Reporting Year,Patient Severity,Response Time Plan (minutes),Planned Response (%),Performance (%)
Peel Region,2024,CTAS 2,12,85%,
"""

    records = normalize_paramedic_service_response_time_plans_and_performance(
        csv_text,
        refreshed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 1
    assert records[0].dimension_label == "CTAS 2"
    assert records[0].metrics["response_time_plan_minutes"] == 12
    assert records[0].metrics["planned_response_pct"] == 85
    assert records[0].metrics["performance_pct"] is None
    assert records[0].provenance_url == ONTARIO_LAND_AMBULANCE_PARAMEDIC_PERFORMANCE_RESOURCE_URL


def test_normalize_paramedic_performance_keeps_metric_variants_for_same_severity() -> None:
    csv_text = """Ambulance Service Coverage Area,Reporting Year,Patient Severity ,Response Time Plan (minutes),Planned Response (%),Performance (%)
Thunder Bay (City),2013,CTAS 2,15,0.9,95.71%
Thunder Bay (City),2013,CTAS 2,25,0.9,86.34%
"""

    records = normalize_paramedic_service_response_time_plans_and_performance(
        csv_text,
        refreshed_at=datetime(2026, 4, 20, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 2
    assert records[0].id != records[1].id
    assert [record.metrics["response_time_plan_minutes"] for record in records] == [15, 25]
