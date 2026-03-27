"""Normalization and ingest helpers for public health alerts."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx
from defusedxml import ElementTree

from waittime.core import PublicDataSource, PublicHealthAlert
from waittime.services.database import DatabaseService

PUBLIC_HEALTH_ALERTS_LAST_VERIFIED_AT = date(2026, 3, 27)
HTTP_TIMEOUT_SECONDS = 30.0
HEALTH_CANADA_RECALLS_RSS_URL = (
    "https://recalls-rappels.canada.ca/en/feed/health-products-alerts-recalls"
)

HEALTH_CANADA_RECALLS_SOURCE = PublicDataSource(
    source_id="health-canada-recalls",
    domain="safety_alert",
    source_name="Health Canada Recalls and Safety Alerts",
    scope="canada",
    jurisdiction_level="federal",
    connector_type="feed",
    access_route="Health Canada recalls dataset / RSS feed",
    license_reuse_status="approved_with_conditions",
    attribution_requirement="Keep Health Canada provenance and refresh timestamps visible.",
    update_cadence="hourly",
    freshness_sensitivity="high",
    operational_risk="medium",
    recommended_usage_mode="scheduled_ingest",
    provenance_url="https://recalls-rappels.canada.ca/en",
    last_verified_at=PUBLIC_HEALTH_ALERTS_LAST_VERIFIED_AT,
    public_methodology_note="Official recall and safety alert data from Health Canada.",
)


@dataclass(frozen=True)
class AlertIngestSummary:
    """Summary of one alert ingest pass."""

    source_id: str
    records_loaded: int


class PublicHealthAlertService:
    """Service for normalizing and persisting public alert feeds."""

    def __init__(self, db: DatabaseService):
        self.db = db

    def ensure_alert_sources(self) -> PublicDataSource:
        """Persist the approved recall source metadata."""
        return self.db.upsert_public_data_source(HEALTH_CANADA_RECALLS_SOURCE)

    def ingest_health_canada_recall_feed(
        self,
        payload: str,
        refreshed_at: datetime | None = None,
    ) -> AlertIngestSummary:
        """Normalize and persist a Health Canada alert payload."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        self.db.upsert_public_data_source(
            HEALTH_CANADA_RECALLS_SOURCE.model_copy(
                update={"last_refreshed_at": effective_refreshed_at}
            )
        )
        alerts = normalize_health_canada_recall_feed(payload, effective_refreshed_at)
        count = self.db.replace_public_health_alerts("health-canada-recalls", alerts)
        self.db.mark_public_data_source_refreshed("health-canada-recalls", effective_refreshed_at)
        return AlertIngestSummary(
            source_id="health-canada-recalls",
            records_loaded=count,
        )

    def ingest_health_canada_recall_rss(
        self,
        payload: str,
        refreshed_at: datetime | None = None,
    ) -> AlertIngestSummary:
        """Normalize and persist a Health Canada recalls RSS payload."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        self.db.upsert_public_data_source(
            HEALTH_CANADA_RECALLS_SOURCE.model_copy(
                update={"last_refreshed_at": effective_refreshed_at}
            )
        )
        alerts = normalize_health_canada_recall_rss(payload, effective_refreshed_at)
        count = self.db.replace_public_health_alerts("health-canada-recalls", alerts)
        self.db.mark_public_data_source_refreshed("health-canada-recalls", effective_refreshed_at)
        return AlertIngestSummary(
            source_id="health-canada-recalls",
            records_loaded=count,
        )

    def fetch_health_canada_recall_rss(self) -> str:
        """Fetch the approved Health Canada recalls RSS feed."""
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(
                HEALTH_CANADA_RECALLS_RSS_URL,
                headers={"Accept": "application/rss+xml, application/xml, text/xml"},
            )
            response.raise_for_status()
            return response.text


def load_alert_payload(file_path: Path) -> str:
    """Read a JSON alert payload from disk."""
    return file_path.read_text(encoding="utf-8")


def normalize_health_canada_recall_feed(
    payload: str,
    refreshed_at: datetime,
) -> list[PublicHealthAlert]:
    """Normalize a Health Canada alert dataset payload."""
    decoded = json.loads(payload)

    if isinstance(decoded, dict):
        items = decoded.get("results") or decoded.get("items") or decoded.get("data") or []
    elif isinstance(decoded, list):
        items = decoded
    else:
        items = []

    normalized: list[PublicHealthAlert] = []
    for item in items:
        if not isinstance(item, dict):
            continue

        title = _pick(item, ["title", "alert_title", "product_name"])
        summary = _pick(item, ["summary", "description", "short_description"])
        published_at = _parse_datetime(
            _pick(item, ["published_at", "date_posted", "published_date"])
        )
        if not title or not summary or published_at is None:
            continue

        provenance_url = _pick(item, ["provenance_url", "url", "link"]) or (
            HEALTH_CANADA_RECALLS_SOURCE.provenance_url
        )
        alert_identifier = _pick(item, ["id", "alert_id", "recall_id"])
        alert_type = _pick(item, ["alert_type", "category", "type"]) or "safety_alert"
        updated_at = _parse_datetime(_pick(item, ["updated_at", "date_modified", "last_updated"]))
        affected_products = _normalize_affected_products(
            item.get("affected_products"),
            item.get("brand_name"),
            item.get("din"),
        )

        normalized.append(
            PublicHealthAlert(
                id=_build_alert_id(alert_identifier, title, published_at),
                source_id="health-canada-recalls",
                title=title,
                summary=summary,
                alert_type=alert_type,
                published_at=published_at,
                source_updated_at=updated_at,
                affected_products=affected_products,
                provenance_url=provenance_url,
                last_refreshed_at=refreshed_at,
            )
        )

    return normalized


def normalize_health_canada_recall_rss(
    payload: str,
    refreshed_at: datetime,
) -> list[PublicHealthAlert]:
    """Normalize a Health Canada recalls RSS feed into alert rows."""
    root = ElementTree.fromstring(payload)
    namespace = {"dc": "http://purl.org/dc/elements/1.1/"}

    normalized: list[PublicHealthAlert] = []
    for item in root.findall("./channel/item"):
        title = _clean_xml_text(item.findtext("title"))
        summary = _clean_xml_text(item.findtext("description"))
        published_at = _parse_datetime(_clean_xml_text(item.findtext("pubDate")))
        if not title or not summary or published_at is None:
            continue

        provenance_url = _clean_xml_text(item.findtext("link")) or (
            HEALTH_CANADA_RECALLS_SOURCE.provenance_url
        )
        alert_identifier = _clean_xml_text(item.findtext("guid"))
        alert_type = _clean_xml_text(item.findtext("dc:creator", namespaces=namespace))
        if not alert_type:
            alert_type = "safety_alert"

        normalized.append(
            PublicHealthAlert(
                id=_build_alert_id(alert_identifier, title, published_at),
                source_id="health-canada-recalls",
                title=title,
                summary=summary,
                alert_type=alert_type,
                published_at=published_at,
                source_updated_at=None,
                affected_products=[],
                provenance_url=provenance_url,
                last_refreshed_at=refreshed_at,
            )
        )

    return normalized


def _pick(item: dict[str, Any], keys: list[str]) -> str | None:
    for key in keys:
        value = item.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _clean_xml_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _normalize_affected_products(
    products: Any,
    brand_name: Any,
    din: Any,
) -> list[dict[str, str | None]]:
    if isinstance(products, list):
        normalized: list[dict[str, str | None]] = []
        for product in products:
            if not isinstance(product, dict):
                continue
            brand = product.get("brand_name") or product.get("name")
            if not brand:
                continue
            normalized.append(
                {
                    "brand_name": str(brand),
                    "din": str(product.get("din")) if product.get("din") else None,
                }
            )
        if normalized:
            return normalized

    if isinstance(brand_name, str) and brand_name.strip():
        return [{"brand_name": brand_name.strip(), "din": str(din) if din else None}]

    return []


def _build_alert_id(
    alert_identifier: str | None,
    title: str,
    published_at: datetime,
) -> str:
    if alert_identifier:
        return f"recall-{alert_identifier.strip()}"

    digest = hashlib.sha256(f"{title}|{published_at.isoformat()}".encode()).hexdigest()[:12]
    return f"recall-{digest}"
