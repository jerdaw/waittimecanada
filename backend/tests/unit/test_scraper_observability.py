"""Tests for scraper observability classification helpers."""

from unittest.mock import Mock

import httpx
import psycopg2

from waittime.scrapers.observability import (
    ClassifiedFailure,
    classify_scraper_failure,
    fetch_retry_wait,
)


def test_classifies_parse_failure_as_parser_breakage() -> None:
    result = classify_scraper_failure(ValueError("Unexpected HTML shape"), "parse")
    assert isinstance(result, ClassifiedFailure)
    assert result.category == "parser_breakage"
    assert result.stage == "parse"


def test_classifies_fetch_http_error_as_upstream_unavailable() -> None:
    http_error = httpx.HTTPStatusError("503", request=Mock(), response=Mock(status_code=503))
    result = classify_scraper_failure(http_error, "fetch")
    assert result.category == "upstream_unavailable"
    assert result.stage == "fetch"


def test_classifies_persistence_errors() -> None:
    db_error = psycopg2.OperationalError("DB unavailable")
    result = classify_scraper_failure(db_error, "persist")
    assert result.category == "persistence_failure"
    assert result.stage == "persist"


def test_classifies_unknown_orchestration_errors() -> None:
    result = classify_scraper_failure(RuntimeError("Unexpected"), "orchestration")
    assert result.category == "unknown"
    assert result.stage == "orchestration"


def test_fetch_retry_wait_returns_strategy() -> None:
    strategy = fetch_retry_wait()
    assert strategy is not None
