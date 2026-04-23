"""Normalization and ingest helpers for Ontario EMS system-context data."""

import csv
import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import httpx

from waittime.core import PublicDataSource, PublicHealthSystemMetric
from waittime.services.database import DatabaseService

HTTP_TIMEOUT_SECONDS = 30.0
ONTARIO_LAND_AMBULANCE_LAST_VERIFIED_AT = date(2026, 4, 20)
ONTARIO_LAND_AMBULANCE_DATASET_URL = (
    "https://data.ontario.ca/en/dataset/land-ambulance-response-time-standard-response-times"
)
ONTARIO_LAND_AMBULANCE_AVERAGE_RESPONSE_TIMES_URL = (
    "https://data.ontario.ca/dataset/0c4c8e2d-5e72-4a72-9101-1570e5a28677/"
    "resource/feaebc4c-a197-44ba-84e7-bd19c358e87c/download/"
    "average_response_times_and_call_volumes.csv"
)
ONTARIO_LAND_AMBULANCE_AVERAGE_RESPONSE_TIMES_RESOURCE_URL = (
    "https://data.ontario.ca/dataset/land-ambulance-response-time-standard-response-times/"
    "resource/feaebc4c-a197-44ba-84e7-bd19c358e87c"
)
ONTARIO_LAND_AMBULANCE_PARAMEDIC_PERFORMANCE_URL = (
    "https://data.ontario.ca/dataset/0c4c8e2d-5e72-4a72-9101-1570e5a28677/"
    "resource/f278a64b-3df3-4984-a894-ed7c6e1d191b/download/"
    "paramedic_services_response_time_plans_and_performance.csv"
)
ONTARIO_LAND_AMBULANCE_PARAMEDIC_PERFORMANCE_RESOURCE_URL = (
    "https://data.ontario.ca/dataset/land-ambulance-response-time-standard-response-times/"
    "resource/f278a64b-3df3-4984-a894-ed7c6e1d191b"
)

ONTARIO_LAND_AMBULANCE_RESPONSE_TIMES_SOURCE = PublicDataSource(
    source_id="ontario-land-ambulance-response-times",
    domain="system_context",
    source_name="Ontario Land Ambulance Response Times",
    scope="ontario",
    jurisdiction_level="provincial",
    connector_type="open_data_portal",
    access_route="Ontario Data Catalogue CSV downloads",
    license_reuse_status="approved_with_conditions",
    attribution_requirement="Open Government Licence - Ontario attribution required.",
    update_cadence="annual",
    freshness_sensitivity="low",
    operational_risk="low",
    recommended_usage_mode="analytics_only",
    provenance_url=ONTARIO_LAND_AMBULANCE_DATASET_URL,
    last_verified_at=ONTARIO_LAND_AMBULANCE_LAST_VERIFIED_AT,
    public_methodology_note=(
        "Official Ontario ambulance response-time reporting for context only. "
        "This is not live EMS availability or dispatch guidance."
    ),
)


@dataclass(frozen=True)
class SystemContextIngestSummary:
    """Summary of one system-context ingest pass."""

    source_id: str
    records_loaded: int


class PublicHealthSystemContextService:
    """Service for normalizing and persisting Ontario EMS system-context data."""

    def __init__(self, db: DatabaseService | None = None):
        self.db = db

    def ensure_system_context_sources(self) -> PublicDataSource:
        """Persist the approved EMS system-context source metadata."""
        return self._require_db().upsert_public_data_source(
            ONTARIO_LAND_AMBULANCE_RESPONSE_TIMES_SOURCE
        )

    def ingest_ontario_land_ambulance_context(
        self,
        average_response_times_csv: str,
        paramedic_performance_csv: str,
        refreshed_at: datetime | None = None,
    ) -> SystemContextIngestSummary:
        """Normalize and persist the Ontario EMS system-context source."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        db = self._require_db()
        db.upsert_public_data_source(
            ONTARIO_LAND_AMBULANCE_RESPONSE_TIMES_SOURCE.model_copy(
                update={"last_refreshed_at": effective_refreshed_at}
            )
        )
        system_metrics = normalize_average_response_times_and_call_volumes(
            average_response_times_csv,
            refreshed_at=effective_refreshed_at,
        ) + normalize_paramedic_service_response_time_plans_and_performance(
            paramedic_performance_csv,
            refreshed_at=effective_refreshed_at,
        )
        count = db.replace_public_health_system_metrics(
            "ontario-land-ambulance-response-times",
            system_metrics,
        )
        db.mark_public_data_source_refreshed(
            "ontario-land-ambulance-response-times",
            refreshed_at=effective_refreshed_at,
        )
        return SystemContextIngestSummary(
            source_id="ontario-land-ambulance-response-times",
            records_loaded=count,
        )

    def fetch_average_response_times_and_call_volumes_csv(self) -> str:
        """Fetch the approved Ontario CACC average response-time CSV."""
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(
                ONTARIO_LAND_AMBULANCE_AVERAGE_RESPONSE_TIMES_URL,
                headers={"Accept": "text/csv, text/plain"},
            )
            response.raise_for_status()
            return response.text

    def _require_db(self) -> DatabaseService:
        if self.db is None:
            raise RuntimeError("Database service is required for this operation.")
        return self.db

    def fetch_paramedic_service_response_time_plans_and_performance_csv(self) -> str:
        """Fetch the approved Ontario paramedic-service response-time CSV."""
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(
                ONTARIO_LAND_AMBULANCE_PARAMEDIC_PERFORMANCE_URL,
                headers={"Accept": "text/csv, text/plain"},
            )
            response.raise_for_status()
            return response.text


def load_system_context_payload(file_path: Path) -> str:
    """Read a UTF-8 text file for EMS system-context ingest."""
    return file_path.read_text(encoding="utf-8-sig")


def normalize_average_response_times_and_call_volumes(
    csv_text: str,
    refreshed_at: datetime,
) -> list[PublicHealthSystemMetric]:
    """Normalize Ontario CACC response-time summary rows."""
    rows = csv.DictReader(io.StringIO(csv_text))
    normalized: list[PublicHealthSystemMetric] = []

    for raw_row in rows:
        row = _normalize_row(raw_row)
        geography_name = _clean_value(row.get("cacc location"))
        reporting_year = _parse_reporting_year(row.get("reporting year"))
        if not geography_name or reporting_year is None:
            continue

        normalized.append(
            PublicHealthSystemMetric(
                id=_build_system_metric_id(
                    source_id="ontario-land-ambulance-response-times",
                    series_key="cacc_average_response_times",
                    geography_name=geography_name,
                    reporting_year=reporting_year,
                    dimension_label=None,
                ),
                source_id="ontario-land-ambulance-response-times",
                series_key="cacc_average_response_times",
                province="ON",
                geography_type="dispatch_centre",
                geography_name=geography_name,
                reporting_year=reporting_year,
                dimension_label=None,
                metrics={
                    "average_response_time_minutes": _parse_numeric(
                        row.get("average response time")
                    ),
                    "call_volume": _parse_numeric(row.get("call volume")),
                },
                provenance_url=ONTARIO_LAND_AMBULANCE_AVERAGE_RESPONSE_TIMES_RESOURCE_URL,
                last_refreshed_at=refreshed_at,
            )
        )

    return _dedupe_exact_system_metrics(normalized)


def normalize_paramedic_service_response_time_plans_and_performance(
    csv_text: str,
    refreshed_at: datetime,
) -> list[PublicHealthSystemMetric]:
    """Normalize Ontario paramedic-service response-time plan rows."""
    rows = csv.DictReader(io.StringIO(csv_text))
    normalized: list[PublicHealthSystemMetric] = []

    for raw_row in rows:
        row = _normalize_row(raw_row)
        geography_name = _clean_value(row.get("ambulance service coverage area"))
        reporting_year = _parse_reporting_year(row.get("reporting year"))
        if not geography_name or reporting_year is None:
            continue

        dimension_label = _clean_value(row.get("patient severity"))
        response_time_plan_minutes = _parse_numeric(row.get("response time plan (minutes)"))
        planned_response_pct = _parse_numeric(row.get("planned response (%)"))
        performance_pct = _parse_numeric(row.get("performance (%)"))
        metrics: dict[str, float | int | str | None] = {
            "response_time_plan_minutes": response_time_plan_minutes,
            "planned_response_pct": planned_response_pct,
            "performance_pct": performance_pct,
        }
        normalized.append(
            PublicHealthSystemMetric(
                id=_build_system_metric_id(
                    source_id="ontario-land-ambulance-response-times",
                    series_key="paramedic_service_response_performance",
                    geography_name=geography_name,
                    reporting_year=reporting_year,
                    dimension_label=dimension_label,
                    metrics_fingerprint=(
                        response_time_plan_minutes,
                        planned_response_pct,
                        performance_pct,
                    ),
                ),
                source_id="ontario-land-ambulance-response-times",
                series_key="paramedic_service_response_performance",
                province="ON",
                geography_type="ambulance_service_coverage_area",
                geography_name=geography_name,
                reporting_year=reporting_year,
                dimension_label=dimension_label,
                metrics=metrics,
                provenance_url=ONTARIO_LAND_AMBULANCE_PARAMEDIC_PERFORMANCE_RESOURCE_URL,
                last_refreshed_at=refreshed_at,
            )
        )

    return _dedupe_exact_system_metrics(normalized)


def _normalize_row(row: dict[str, str | None]) -> dict[str, str | None]:
    return {
        re.sub(r"\s+", " ", key.strip().lower()): value
        for key, value in row.items()
        if key is not None
    }


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = " ".join(value.split()).strip()
    return cleaned or None


def _parse_reporting_year(value: str | None) -> int | None:
    cleaned = _clean_value(value)
    if not cleaned:
        return None
    match = re.search(r"\d{4}", cleaned)
    if not match:
        return None
    return int(match.group(0))


def _parse_numeric(value: str | None) -> float | int | None:
    cleaned = _clean_value(value)
    if not cleaned:
        return None
    normalized = cleaned.replace(",", "").replace("%", "")
    try:
        numeric = float(normalized)
    except ValueError:
        return None
    if numeric.is_integer():
        return int(numeric)
    return numeric


def _build_system_metric_id(
    *,
    source_id: str,
    series_key: str,
    geography_name: str,
    reporting_year: int,
    dimension_label: str | None,
    metrics_fingerprint: tuple[float | int | None, ...] = (),
) -> str:
    slug = _slugify(geography_name)[:40]
    dimension_slug = _slugify(dimension_label or "all")[:24]
    digest = hashlib.sha256(
        (
            f"{series_key}|{geography_name}|{reporting_year}|{dimension_label or ''}|"
            + "|".join("" if value is None else str(value) for value in metrics_fingerprint)
        ).encode("utf-8")
    ).hexdigest()[:10]
    return f"{source_id}-{series_key}-{reporting_year}-{slug}-{dimension_slug}-{digest}"


def _dedupe_exact_system_metrics(
    system_metrics: list[PublicHealthSystemMetric],
) -> list[PublicHealthSystemMetric]:
    deduped: dict[str, PublicHealthSystemMetric] = {}
    for system_metric in system_metrics:
        deduped[system_metric.id] = system_metric
    return list(deduped.values())


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "system-context"
