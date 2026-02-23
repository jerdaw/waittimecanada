"""Shared observability and reliability helpers for scraper execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import httpx
import psycopg2
import requests
from tenacity import RetryError, wait_exponential, wait_random

try:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeout
except Exception:  # pragma: no cover - optional in some test environments
    PlaywrightError = Exception  # type: ignore[assignment,misc]
    PlaywrightTimeout = Exception  # type: ignore[assignment,misc]

FailureCategory = Literal[
    "upstream_unavailable",
    "parser_breakage",
    "infra_runtime",
    "persistence_failure",
    "unknown",
]
FailureStage = Literal[
    "fetch",
    "parse",
    "before_save",
    "persist",
    "heartbeat",
    "orchestration",
]


HTTP_FETCH_ATTEMPTS = 3
FETCH_WAIT_MIN_SECONDS = 2
FETCH_WAIT_MAX_SECONDS = 20
FETCH_WAIT_JITTER_SECONDS = 2

DEFAULT_HTTP_CONNECT_TIMEOUT_SECONDS = 10.0
DEFAULT_HTTP_READ_TIMEOUT_SECONDS = 30.0
DEFAULT_HTTP_WRITE_TIMEOUT_SECONDS = 30.0
DEFAULT_HTTP_POOL_TIMEOUT_SECONDS = 30.0

PLAYWRIGHT_PAGE_TIMEOUT_MS = 30_000
PLAYWRIGHT_SELECTOR_TIMEOUT_MS = 15_000
PLAYWRIGHT_RENDER_WAIT_MS = 2_000


def fetch_retry_wait() -> Any:
    """Return the shared backoff strategy used by fetch retries."""
    return wait_exponential(
        multiplier=1,
        min=FETCH_WAIT_MIN_SECONDS,
        max=FETCH_WAIT_MAX_SECONDS,
    ) + wait_random(0, FETCH_WAIT_JITTER_SECONDS)


@dataclass(frozen=True)
class ClassifiedFailure:
    """Structured failure metadata for heartbeat and alerting."""

    category: FailureCategory
    stage: FailureStage
    message: str


def _unwrap_retry_error(error: Exception) -> Exception:
    """Return inner exception for tenacity retry wrappers when available."""
    if not isinstance(error, RetryError):
        return error

    try:
        inner = error.last_attempt.exception()
    except Exception:
        return cast(Exception, error)

    if isinstance(inner, Exception):
        return inner
    return cast(Exception, error)


def classify_scraper_failure(error: Exception, stage: FailureStage) -> ClassifiedFailure:
    """Classify scraper failures by source and pipeline stage."""
    root_error = _unwrap_retry_error(error)
    message = str(root_error) or root_error.__class__.__name__

    if stage in {"persist", "before_save", "heartbeat"}:
        return ClassifiedFailure("persistence_failure", stage, message)

    if isinstance(root_error, psycopg2.Error):
        return ClassifiedFailure("persistence_failure", stage, message)

    if stage == "parse":
        return ClassifiedFailure("parser_breakage", stage, message)

    if stage == "fetch":
        if isinstance(root_error, PlaywrightTimeout):
            return ClassifiedFailure("upstream_unavailable", stage, message)
        if isinstance(root_error, PlaywrightError):
            return ClassifiedFailure("infra_runtime", stage, message)
        if isinstance(root_error, httpx.HTTPError | requests.RequestException):
            return ClassifiedFailure("upstream_unavailable", stage, message)

    return ClassifiedFailure("unknown", stage, message)
