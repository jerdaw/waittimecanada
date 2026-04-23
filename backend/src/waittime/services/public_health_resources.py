"""Normalization and ingest helpers for the public health hub."""

import csv
import hashlib
import io
import json
import logging
import re
import unicodedata
import zipfile
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import httpx

from waittime.core import PublicDataSource, ResourceLocation
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)

PUBLIC_HEALTH_HUB_LAST_VERIFIED_AT = date(2026, 3, 27)
HTTP_TIMEOUT_SECONDS = 30.0
MOHSERLO_FEATURE_LAYER_URL = (
    "https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/"
    "LIO_OPEN_DATA/LIO_Open09/MapServer/26/query"
)
MOHSERLO_PAGE_SIZE = 2000
OSM_OVERPASS_API_URLS = (
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
)
ODHF_DOWNLOAD_URL = "https://www150.statcan.gc.ca/n1/en/pub/13-26-0001/2020001/ODHF_v1.1.zip"
ONTARIO_AED_OVERPASS_QUERY = """
[out:json][timeout:90];
area["ISO3166-2"="CA-ON"]->.searchArea;
(
  node["emergency"="defibrillator"](area.searchArea);
  way["emergency"="defibrillator"](area.searchArea);
  relation["emergency"="defibrillator"](area.searchArea);
);
out center tags;
""".strip()

MOHSERLO_SOURCE = PublicDataSource(
    source_id="mohserlo",
    domain="provider_facility",
    source_name="MOHSERLO",
    scope="ontario",
    jurisdiction_level="provincial",
    connector_type="open_data_portal",
    access_route="Ontario Data Catalogue / Ontario GeoHub export",
    license_reuse_status="approved_with_conditions",
    attribution_requirement="Open Government Licence - Ontario attribution required.",
    update_cadence="yearly",
    freshness_sensitivity="low",
    operational_risk="low",
    recommended_usage_mode="scheduled_ingest",
    provenance_url="https://data.ontario.ca/dataset/ministry-of-health-service-provider-locations-mohserlo",
    last_verified_at=PUBLIC_HEALTH_HUB_LAST_VERIFIED_AT,
    public_methodology_note="Reference directory data. This is not a live operational status feed.",
)

ODHF_SOURCE = PublicDataSource(
    source_id="odhf",
    domain="provider_facility",
    source_name="Open Database of Healthcare Facilities",
    scope="canada",
    jurisdiction_level="federal",
    connector_type="file_download",
    access_route="Statistics Canada ODHF CSV download",
    license_reuse_status="approved_with_conditions",
    attribution_requirement="Open Government Licence - Canada attribution required.",
    update_cadence="periodic",
    freshness_sensitivity="low",
    operational_risk="low",
    recommended_usage_mode="scheduled_ingest",
    provenance_url="https://www.statcan.gc.ca/en/lode/databases/odhf",
    last_verified_at=PUBLIC_HEALTH_HUB_LAST_VERIFIED_AT,
    public_methodology_note="Secondary facility cross-check dataset. Not the primary Ontario directory source.",
)

OSM_AED_SOURCE = PublicDataSource(
    source_id="osm-aed",
    domain="aed",
    source_name="OpenStreetMap AED",
    scope="ontario",
    jurisdiction_level="nonprofit_other",
    connector_type="crowdsourced_registry",
    access_route="OpenStreetMap / Overpass export",
    license_reuse_status="approved_with_conditions",
    attribution_requirement="OpenStreetMap attribution and ODbL disclosure required.",
    update_cadence="on-demand export",
    freshness_sensitivity="high",
    operational_risk="medium",
    recommended_usage_mode="scheduled_ingest",
    provenance_url="https://www.openstreetmap.org",
    last_verified_at=PUBLIC_HEALTH_HUB_LAST_VERIFIED_AT,
    public_methodology_note="Crowdsourced AED data. Locations may be incomplete or outdated. In an emergency, call 911 immediately.",
)


@dataclass(frozen=True)
class FacilityIngestSummary:
    """Summary of one facility ingest pass."""

    source_id: str
    records_loaded: int


class PublicHealthResourceService:
    """Service for normalizing and persisting public health hub resources."""

    def __init__(self, db: DatabaseService | None):
        self.db = db

    def ensure_batch_a_facility_sources(self) -> list[PublicDataSource]:
        """Persist the Batch A facility source metadata records."""
        return [
            self._require_db().upsert_public_data_source(MOHSERLO_SOURCE),
            self._require_db().upsert_public_data_source(ODHF_SOURCE),
        ]

    def ensure_aed_sources(self) -> list[PublicDataSource]:
        """Persist the approved AED source metadata record."""
        return [self._require_db().upsert_public_data_source(OSM_AED_SOURCE)]

    def ingest_mohserlo_csv(
        self,
        csv_text: str,
        refreshed_at: datetime | None = None,
    ) -> FacilityIngestSummary:
        """Normalize and persist a MOHSERLO file."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        db = self._require_db()
        db.upsert_public_data_source(
            MOHSERLO_SOURCE.model_copy(update={"last_refreshed_at": effective_refreshed_at})
        )
        records = normalize_mohserlo_csv(csv_text, effective_refreshed_at)
        count = db.replace_resource_locations("mohserlo", "facility", records)
        db.mark_public_data_source_refreshed("mohserlo", effective_refreshed_at)
        return FacilityIngestSummary(source_id="mohserlo", records_loaded=count)

    def ingest_mohserlo_geojson(
        self,
        payload: str,
        refreshed_at: datetime | None = None,
    ) -> FacilityIngestSummary:
        """Normalize and persist a live MOHSERLO GeoJSON export."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        db = self._require_db()
        db.upsert_public_data_source(
            MOHSERLO_SOURCE.model_copy(update={"last_refreshed_at": effective_refreshed_at})
        )
        records = normalize_mohserlo_geojson(payload, effective_refreshed_at)
        count = db.replace_resource_locations("mohserlo", "facility", records)
        db.mark_public_data_source_refreshed("mohserlo", effective_refreshed_at)
        return FacilityIngestSummary(source_id="mohserlo", records_loaded=count)

    def ingest_odhf_csv(
        self,
        csv_text: str,
        refreshed_at: datetime | None = None,
    ) -> FacilityIngestSummary:
        """Normalize and persist an ODHF file."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        db = self._require_db()
        db.upsert_public_data_source(
            ODHF_SOURCE.model_copy(update={"last_refreshed_at": effective_refreshed_at})
        )
        records = normalize_odhf_csv(csv_text, effective_refreshed_at)
        count = db.replace_resource_locations("odhf", "facility", records)
        db.mark_public_data_source_refreshed("odhf", effective_refreshed_at)
        return FacilityIngestSummary(source_id="odhf", records_loaded=count)

    def ingest_osm_aed_overpass_json(
        self,
        payload: str,
        refreshed_at: datetime | None = None,
    ) -> FacilityIngestSummary:
        """Normalize and persist an OSM Overpass-style AED export."""
        effective_refreshed_at = refreshed_at or datetime.now(UTC)
        db = self._require_db()
        db.upsert_public_data_source(
            OSM_AED_SOURCE.model_copy(update={"last_refreshed_at": effective_refreshed_at})
        )
        records = normalize_osm_aed_overpass_json(payload, effective_refreshed_at)
        count = db.replace_resource_locations("osm-aed", "aed", records)
        db.mark_public_data_source_refreshed("osm-aed", effective_refreshed_at)
        return FacilityIngestSummary(source_id="osm-aed", records_loaded=count)

    def fetch_mohserlo_geojson(self) -> str:
        """Fetch the live MOHSERLO feature layer as GeoJSON."""
        features: list[dict[str, Any]] = []
        result_offset = 0

        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            while True:
                response = client.get(
                    MOHSERLO_FEATURE_LAYER_URL,
                    params={
                        "where": "1=1",
                        "outFields": "*",
                        "f": "geojson",
                        "resultOffset": result_offset,
                        "resultRecordCount": MOHSERLO_PAGE_SIZE,
                    },
                    headers={"Accept": "application/geo+json, application/json"},
                )
                response.raise_for_status()
                payload = response.json()
                page_features = payload.get("features", [])
                if not isinstance(page_features, list) or not page_features:
                    break

                features.extend(page_features)

                exceeded = bool(
                    payload.get("exceededTransferLimit")
                    or payload.get("properties", {}).get("exceededTransferLimit")
                )
                if not exceeded or len(page_features) < MOHSERLO_PAGE_SIZE:
                    break

                result_offset += len(page_features)

        return json.dumps({"type": "FeatureCollection", "features": features})

    def fetch_osm_aed_overpass_json(self) -> str:
        """Fetch the approved Ontario AED fallback query from Overpass."""
        errors: list[str] = []

        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            for endpoint in OSM_OVERPASS_API_URLS:
                try:
                    response = client.get(
                        endpoint,
                        params={"data": ONTARIO_AED_OVERPASS_QUERY},
                        headers={"Accept": "application/json"},
                    )
                    response.raise_for_status()
                    return response.text
                except httpx.HTTPError as exc:
                    error_detail = f"{endpoint}: {exc}"
                    errors.append(error_detail)
                    logger.warning("OSM AED fetch failed for endpoint %s: %s", endpoint, exc)

        error_summary = "; ".join(errors) if errors else "unknown error"
        raise RuntimeError(f"All Overpass AED endpoints failed: {error_summary}")

    def fetch_odhf_csv(self) -> str:
        """Fetch and decode the approved Statistics Canada ODHF CSV archive."""
        with httpx.Client(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = client.get(
                ODHF_DOWNLOAD_URL,
                headers={"Accept": "application/zip, application/octet-stream"},
            )
            response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
            if not csv_names:
                raise RuntimeError("ODHF archive did not contain a CSV payload.")

            return _decode_odhf_csv_bytes(archive.read(csv_names[0]))

    def _require_db(self) -> DatabaseService:
        if self.db is None:
            raise RuntimeError("Database service is required for this operation.")
        return self.db


def load_text_file(file_path: Path) -> str:
    """Read a UTF-8 text file for ingest."""
    return file_path.read_text(encoding="utf-8-sig")


def load_odhf_csv_file(file_path: Path) -> str:
    """Read and decode an ODHF CSV export from disk."""
    return _decode_odhf_csv_bytes(file_path.read_bytes())


def normalize_mohserlo_csv(
    csv_text: str,
    refreshed_at: datetime,
) -> list[ResourceLocation]:
    """Normalize MOHSERLO CSV rows into facility resource records."""
    rows = csv.DictReader(io.StringIO(csv_text))
    return _normalize_facility_rows(
        rows=rows,
        source_id="mohserlo",
        default_province="ON",
        provenance_url=MOHSERLO_SOURCE.provenance_url,
        refreshed_at=refreshed_at,
        name_keys=[
            "service_provider_name",
            "english_name",
            "name",
            "facility_name",
            "organization_name",
        ],
        city_keys=["community_name", "city", "municipality", "locality"],
        latitude_keys=["latitude", "y", "lat"],
        longitude_keys=["longitude", "x", "lon", "lng"],
        address_keys=[
            "full_address",
            "address1",
            "street_address",
            "address",
            "site_address",
        ],
        postal_code_keys=["postal_code", "postcode"],
        phone_keys=["phone", "telephone", "telephone_number"],
        website_keys=["website", "website_url", "web_url"],
        record_id_keys=["provider_id", "location_id", "id", "globalid", "objectid"],
        description_keys=["service_type", "provider_type", "facility_type", "category"],
    )


def normalize_mohserlo_geojson(
    payload: str,
    refreshed_at: datetime,
) -> list[ResourceLocation]:
    """Normalize MOHSERLO GeoJSON features into facility resource records."""
    decoded = json.loads(payload)
    features = decoded.get("features", []) if isinstance(decoded, dict) else []

    rows: list[dict[str, str | None]] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties") or {}
        geometry = feature.get("geometry") or {}
        coordinates = geometry.get("coordinates") if isinstance(geometry, dict) else None

        if (
            not isinstance(properties, dict)
            or not isinstance(coordinates, list)
            or len(coordinates) < 2
        ):
            continue

        rows.append(
            {
                "ENGLISH_NAME": str(properties.get("ENGLISH_NAME") or ""),
                "ENGLISH_NAME_ALT": str(properties.get("ENGLISH_NAME_ALT") or ""),
                "SERVICE_TYPE": str(properties.get("SERVICE_TYPE") or ""),
                "SERVICE_TYPE_DETAIL": str(properties.get("SERVICE_TYPE_DETAIL") or ""),
                "COMMUNITY": str(properties.get("COMMUNITY") or ""),
                "ADDRESS_LINE_1": str(properties.get("ADDRESS_LINE_1") or ""),
                "ADDRESS_LINE_2": str(properties.get("ADDRESS_LINE_2") or ""),
                "POSTAL_CODE": str(properties.get("POSTAL_CODE") or ""),
                "MOH_SERVICE_PROVIDER_IDENT": str(
                    properties.get("MOH_SERVICE_PROVIDER_IDENT") or properties.get("OBJECTID") or ""
                ),
                "LONGITUDE": str(coordinates[0]),
                "LATITUDE": str(coordinates[1]),
            }
        )

    return _normalize_facility_rows(
        rows=rows,
        source_id="mohserlo",
        default_province="ON",
        provenance_url=MOHSERLO_SOURCE.provenance_url,
        refreshed_at=refreshed_at,
        name_keys=["ENGLISH_NAME", "ENGLISH_NAME_ALT"],
        city_keys=["COMMUNITY"],
        latitude_keys=["LATITUDE"],
        longitude_keys=["LONGITUDE"],
        address_keys=["ADDRESS_LINE_1", "ADDRESS_LINE_2"],
        postal_code_keys=["POSTAL_CODE"],
        phone_keys=[],
        website_keys=[],
        record_id_keys=["MOH_SERVICE_PROVIDER_IDENT"],
        description_keys=["SERVICE_TYPE_DETAIL", "SERVICE_TYPE"],
    )


def normalize_odhf_csv(
    csv_text: str,
    refreshed_at: datetime,
) -> list[ResourceLocation]:
    """Normalize ODHF CSV rows into facility resource records."""
    rows = csv.DictReader(io.StringIO(csv_text))
    return _normalize_facility_rows(
        rows=rows,
        source_id="odhf",
        default_province=None,
        provenance_url=ODHF_SOURCE.provenance_url,
        refreshed_at=refreshed_at,
        name_keys=["facility_name", "name", "provider_name"],
        city_keys=["city", "municipality"],
        latitude_keys=["latitude", "lat"],
        longitude_keys=["longitude", "lon", "lng"],
        address_keys=["address", "street_address", "full_address"],
        postal_code_keys=["postal_code", "postcode"],
        phone_keys=["phone", "telephone"],
        website_keys=["website", "website_url"],
        record_id_keys=["facility_id", "id", "record_id", "index"],
        description_keys=["facility_type", "subtype", "naics_name"],
        province_keys=["province", "province_code", "pruid"],
    )


def normalize_osm_aed_overpass_json(
    payload: str,
    refreshed_at: datetime,
) -> list[ResourceLocation]:
    """Normalize an Overpass-style OSM AED payload into resource rows."""
    decoded = json.loads(payload)
    elements = decoded.get("elements", []) if isinstance(decoded, dict) else []

    normalized_rows: list[ResourceLocation] = []
    for element in elements:
        if not isinstance(element, dict):
            continue

        tags = element.get("tags") or {}
        latitude = element.get("lat")
        longitude = element.get("lon")
        if (latitude is None or longitude is None) and isinstance(element.get("center"), dict):
            latitude = element["center"].get("lat")
            longitude = element["center"].get("lon")
        if latitude is None or longitude is None:
            continue

        name = (
            tags.get("name")
            or tags.get("defibrillator:location")
            or tags.get("operator")
            or "Public AED"
        )
        source_record_id = str(element.get("id")) if element.get("id") is not None else None
        province = (
            _normalize_province_code(
                tags.get("addr:province") or tags.get("province") or tags.get("is_in:state_code")
            )
            or "ON"
        )
        address = _compose_address(tags)
        access_notes = tags.get("access") or tags.get("opening_hours")

        normalized_rows.append(
            ResourceLocation(
                id=_build_resource_id("osm-aed", province, name, source_record_id),
                source_id="osm-aed",
                kind="aed",
                source_record_id=source_record_id,
                name=name,
                province=province,
                city=tags.get("addr:city"),
                latitude=float(latitude),
                longitude=float(longitude),
                address=address,
                postal_code=tags.get("addr:postcode"),
                phone=tags.get("phone"),
                website_url=tags.get("website"),
                location_description=tags.get("indoor") == "yes" and "Indoor AED" or "AED",
                access_notes=access_notes,
                crowdsourced=True,
                completeness_status="incomplete",
                provenance_url=(
                    f"https://www.openstreetmap.org/node/{source_record_id}"
                    if source_record_id
                    else OSM_AED_SOURCE.provenance_url
                ),
                last_refreshed_at=refreshed_at,
            )
        )

    return normalized_rows


def _normalize_facility_rows(
    *,
    rows: Iterable[dict[str, str | None]],
    source_id: str,
    default_province: str | None,
    provenance_url: str,
    refreshed_at: datetime,
    name_keys: list[str],
    city_keys: list[str],
    latitude_keys: list[str],
    longitude_keys: list[str],
    address_keys: list[str],
    postal_code_keys: list[str],
    phone_keys: list[str],
    website_keys: list[str],
    record_id_keys: list[str],
    description_keys: list[str],
    province_keys: list[str] | None = None,
) -> list[ResourceLocation]:
    normalized_rows: list[ResourceLocation] = []

    for raw_row in rows:
        row = {_normalize_key(key): _clean_value(value) for key, value in raw_row.items() if key}
        name = _pick_first(row, name_keys)
        latitude = _coerce_float(_pick_first(row, latitude_keys))
        longitude = _coerce_float(_pick_first(row, longitude_keys))

        if not name or latitude is None or longitude is None:
            continue

        province = (
            _normalize_province_code(_pick_first(row, province_keys or []))
            if province_keys
            else None
        ) or default_province
        if not province:
            continue

        source_record_id = _pick_first(row, record_id_keys)
        city = _pick_first(row, city_keys)
        description = _pick_first(row, description_keys)
        address = _pick_first(row, address_keys)
        postal_code = _pick_first(row, postal_code_keys)
        phone = _pick_first(row, phone_keys)
        website = _pick_first(row, website_keys)

        normalized_rows.append(
            ResourceLocation(
                id=_build_resource_id(source_id, province, name, source_record_id),
                source_id=source_id,
                kind="facility",
                source_record_id=source_record_id,
                name=name,
                province=province,
                city=city,
                latitude=latitude,
                longitude=longitude,
                address=address,
                postal_code=postal_code,
                phone=phone,
                website_url=website,
                reference_status="directory_only",
                location_description=description,
                provenance_url=provenance_url,
                last_refreshed_at=refreshed_at,
            )
        )

    return normalized_rows


def _normalize_key(key: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", key.strip().lower()).strip("_")


def _clean_value(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _pick_first(row: dict[str, str | None], keys: Iterable[str]) -> str | None:
    for key in keys:
        value = row.get(_normalize_key(key))
        if value:
            return value
    return None


def _coerce_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _normalize_province_code(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().upper()
    if cleaned.isdigit():
        code_map = {
            "10": "NL",
            "11": "PE",
            "12": "NS",
            "13": "NB",
            "24": "QC",
            "35": "ON",
            "46": "MB",
            "47": "SK",
            "48": "AB",
            "59": "BC",
            "60": "YT",
            "61": "NT",
            "62": "NU",
        }
        return code_map.get(cleaned)
    return cleaned[:2]


def _decode_odhf_csv_bytes(payload: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeDecodeError(
        "odhf",
        payload,
        0,
        1,
        "Unable to decode ODHF CSV payload as utf-8-sig or cp1252.",
    )


def _build_resource_id(
    source_id: str,
    province: str,
    name: str,
    source_record_id: str | None,
) -> str:
    slug = _slugify(name)[:48]
    if source_record_id:
        normalized_record = _slugify(source_record_id)[:24]
        return f"{source_id}-{province.lower()}-{slug}-{normalized_record}"

    digest = hashlib.sha256(f"{province}|{name}".encode()).hexdigest()[:10]
    return f"{source_id}-{province.lower()}-{slug}-{digest}"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "resource"


def _compose_address(tags: dict[str, Any]) -> str | None:
    house_number = tags.get("addr:housenumber")
    street = tags.get("addr:street")
    if house_number and street:
        return f"{house_number} {street}"
    if street:
        return str(street)
    return None
