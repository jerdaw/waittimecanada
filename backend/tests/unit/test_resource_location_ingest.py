from datetime import UTC, datetime
from pathlib import Path

from waittime.services.public_health_resources import (
    MOHSERLO_SOURCE,
    ODHF_SOURCE,
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
