import io
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import httpx

from waittime.services.public_health_resources import (
    MOHSERLO_SOURCE,
    ODHF_DOWNLOAD_URL,
    ODHF_SOURCE,
    OSM_OVERPASS_API_URLS,
    PublicHealthResourceService,
    load_odhf_csv_file,
    normalize_mohserlo_csv,
    normalize_mohserlo_geojson,
    normalize_odhf_csv,
    normalize_osm_aed_overpass_json,
)

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "public_health_hub"


def test_normalize_mohserlo_csv_creates_directory_only_facilities() -> None:
    csv_text = (FIXTURES_DIR / "mohserlo_sample.csv").read_text(encoding="utf-8")

    records = normalize_mohserlo_csv(
        csv_text,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 2
    assert records[0].source_id == "mohserlo"
    assert records[0].province == "ON"
    assert records[0].reference_status == "directory_only"
    assert records[0].location_description == "Hospital"
    assert records[0].provenance_url == MOHSERLO_SOURCE.provenance_url


def test_normalize_odhf_csv_preserves_province_codes() -> None:
    csv_text = (FIXTURES_DIR / "odhf_sample.csv").read_text(encoding="utf-8")

    records = normalize_odhf_csv(
        csv_text,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 2
    assert records[0].source_id == "odhf"
    assert records[0].province == "ON"
    assert records[1].province == "QC"
    assert records[0].provenance_url == ODHF_SOURCE.provenance_url
    assert records[0].reference_status == "directory_only"


def test_load_odhf_csv_file_decodes_cp1252_exports(tmp_path: Path) -> None:
    odhf_file = tmp_path / "odhf.csv"
    odhf_file.write_bytes(
        (
            "index,facility_name,province,latitude,longitude\n1,H\u00f4pital Test,on,43.65,-79.38\n"
        ).encode("cp1252")
    )

    decoded = load_odhf_csv_file(odhf_file)

    assert "H\u00f4pital Test" in decoded


def test_normalize_mohserlo_geojson_creates_directory_only_facilities() -> None:
    payload = """
    {
      "type": "FeatureCollection",
      "features": [
        {
          "type": "Feature",
          "geometry": {
            "type": "Point",
            "coordinates": [-79.3832, 43.6532]
          },
          "properties": {
            "MOH_SERVICE_PROVIDER_IDENT": "12345",
            "ENGLISH_NAME": "Toronto General Hospital",
            "SERVICE_TYPE": "Hospital",
            "SERVICE_TYPE_DETAIL": "Teaching Hospital",
            "ADDRESS_LINE_1": "200 Elizabeth St",
            "COMMUNITY": "Toronto",
            "POSTAL_CODE": "M5G2C4"
          }
        }
      ]
    }
    """

    records = normalize_mohserlo_geojson(
        payload,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 1
    assert records[0].source_id == "mohserlo"
    assert records[0].province == "ON"
    assert records[0].reference_status == "directory_only"
    assert records[0].location_description == "Teaching Hospital"
    assert records[0].provenance_url == MOHSERLO_SOURCE.provenance_url


def test_normalize_osm_aed_overpass_json_marks_crowdsourced_records() -> None:
    payload = (FIXTURES_DIR / "osm_aed_sample.json").read_text(encoding="utf-8")

    records = normalize_osm_aed_overpass_json(
        payload,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 2
    assert records[0].source_id == "osm-aed"
    assert records[0].kind == "aed"
    assert records[0].crowdsourced is True
    assert records[0].completeness_status == "incomplete"
    assert records[0].provenance_url.endswith("/1001001")


def test_normalize_osm_aed_overpass_json_uses_center_for_way_records() -> None:
    payload = """
    {
      "elements": [
        {
          "type": "way",
          "id": 2002002,
          "center": {"lat": 43.651, "lon": -79.347},
          "tags": {
            "emergency": "defibrillator",
            "name": "Community Centre AED",
            "addr:city": "Toronto"
          }
        }
      ]
    }
    """

    records = normalize_osm_aed_overpass_json(
        payload,
        refreshed_at=datetime(2026, 3, 27, 12, 0, tzinfo=UTC),
    )

    assert len(records) == 1
    assert records[0].name == "Community Centre AED"
    assert records[0].latitude == 43.651
    assert records[0].longitude == -79.347


def test_fetch_osm_aed_overpass_json_falls_back_to_secondary_endpoint(
    monkeypatch,
) -> None:
    payload = '{"elements":[]}'
    called_urls: list[str] = []

    def fake_get(self, url, params=None, headers=None):  # type: ignore[no-untyped-def]
        called_urls.append(url)
        request = httpx.Request("GET", url, params=params, headers=headers)
        if url == OSM_OVERPASS_API_URLS[0]:
            return httpx.Response(504, request=request)
        return httpx.Response(200, request=request, text=payload)

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    service = PublicHealthResourceService(db=None)  # type: ignore[arg-type]

    result = service.fetch_osm_aed_overpass_json()

    assert result == payload
    assert called_urls == [OSM_OVERPASS_API_URLS[0], OSM_OVERPASS_API_URLS[1]]


def test_fetch_osm_aed_overpass_json_raises_after_all_endpoints_fail(
    monkeypatch,
) -> None:
    def fake_get(self, url, params=None, headers=None):  # type: ignore[no-untyped-def]
        request = httpx.Request("GET", url, params=params, headers=headers)
        return httpx.Response(504, request=request)

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    service = PublicHealthResourceService(db=None)  # type: ignore[arg-type]

    try:
        service.fetch_osm_aed_overpass_json()
    except RuntimeError as exc:
        message = str(exc)
        assert "All Overpass AED endpoints failed" in message
        for endpoint in OSM_OVERPASS_API_URLS:
            assert endpoint in message
    else:
        raise AssertionError("Expected all-endpoint Overpass failure to raise")


def test_fetch_odhf_csv_extracts_archive_and_decodes_cp1252(monkeypatch) -> None:
    archive_buffer = io.BytesIO()
    with zipfile.ZipFile(archive_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "ODHF_v1.1/odhf_v1.1.csv",
            (
                "index,facility_name,province,latitude,longitude\n"
                "1,H\u00f4pital Test,on,43.65,-79.38\n"
            ).encode("cp1252"),
        )

    def fake_get(self, url, headers=None):  # type: ignore[no-untyped-def]
        request = httpx.Request("GET", url, headers=headers)
        return httpx.Response(200, request=request, content=archive_buffer.getvalue())

    monkeypatch.setattr(httpx.Client, "get", fake_get)

    service = PublicHealthResourceService(db=None)  # type: ignore[arg-type]

    result = service.fetch_odhf_csv()

    assert "H\u00f4pital Test" in result
    assert ODHF_DOWNLOAD_URL.startswith("https://www150.statcan.gc.ca/")
