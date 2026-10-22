"""Unit coverage for per-family aggregate gap classification."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from waittime.services.aggregation import AggregationService


def _service() -> AggregationService:
    return AggregationService(MagicMock())


def _row(
    *,
    metric_family: str,
    source_id: str = "ontario-health",
    start_event: str = "TRIAGE",
    patient_scope: str = "ALL",
) -> dict[str, object]:
    return {
        "value": 90.0,
        "timestamp_utc": datetime(2026, 10, 17, 12, tzinfo=UTC),
        "source_id": source_id,
        "metric_family": metric_family,
        "start_event": start_event,
        "end_event": "PHYSICIAN",
        "statistic_type": "P90",
        "patient_scope": patient_scope,
    }


@pytest.mark.unit
def test_ambiguous_family_is_gapped_without_suppressing_valid_sibling() -> None:
    service = _service()
    period_start = datetime(2026, 10, 17, tzinfo=UTC)
    rows = [
        _row(metric_family="TIME_TO_PROVIDER"),
        _row(metric_family="TIME_TO_PROVIDER", source_id="bc-phsa"),
        _row(metric_family="STRETCHER_OCCUPANCY", start_event="UNKNOWN"),
    ]

    aggregates, gaps = service._compute_period_outcome(
        "hospital-1", "daily", period_start, period_start + timedelta(days=1), rows
    )

    assert [aggregate.metric_family for aggregate in aggregates] == ["STRETCHER_OCCUPANCY"]
    assert [(gap.metric_family, gap.reason, gap.signature_count) for gap in gaps] == [
        ("TIME_TO_PROVIDER", "ambiguous_methodology", 2)
    ]
    assert len(gaps[0].fingerprint) == 64


@pytest.mark.unit
def test_gap_fingerprint_is_stable_for_same_signatures_in_any_row_order() -> None:
    service = _service()
    period_start = datetime(2026, 10, 17, tzinfo=UTC)
    rows = [
        _row(metric_family="TIME_TO_PROVIDER"),
        _row(metric_family="TIME_TO_PROVIDER", source_id="bc-phsa"),
    ]

    first = service._compute_period_outcome(
        "hospital-1", "daily", period_start, period_start + timedelta(days=1), rows
    )[1][0]
    second = service._compute_period_outcome(
        "hospital-1", "daily", period_start, period_start + timedelta(days=1), rows[::-1]
    )[1][0]

    assert first.fingerprint == second.fingerprint


@pytest.mark.unit
def test_unsupported_scope_is_a_gap_not_an_aggregate() -> None:
    service = _service()
    period_start = datetime(2026, 10, 17, tzinfo=UTC)
    aggregates, gaps = service._compute_period_outcome(
        "hospital-1",
        "daily",
        period_start,
        period_start + timedelta(days=1),
        [_row(metric_family="TIME_TO_PROVIDER", patient_scope="MID_ACUITY")],
    )

    assert aggregates == []
    assert len(gaps) == 1
    assert gaps[0].reason == "unsupported_patient_scope"
    assert gaps[0].signature_count == 1
