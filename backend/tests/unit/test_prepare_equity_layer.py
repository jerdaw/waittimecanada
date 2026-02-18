import csv
import json
from pathlib import Path

from scripts.prepare_equity_layer import (
    _calculate_quintile_cut_points,
    _load_income_records,
    process_ontario_real_data,
)


def _write_boundary_geojson(path: Path) -> None:
    payload = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"CTUID": "0001", "CTNAME": "Tract A", "PRUID": "35"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-79.40, 43.64],
                            [-79.38, 43.64],
                            [-79.38, 43.66],
                            [-79.40, 43.66],
                            [-79.40, 43.64],
                        ]
                    ],
                },
            },
            {
                "type": "Feature",
                "properties": {"CTUID": "0002", "CTNAME": "Tract B", "PRUID": "35"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [-79.50, 43.74],
                            [-79.48, 43.74],
                            [-79.48, 43.76],
                            [-79.50, 43.76],
                            [-79.50, 43.74],
                        ]
                    ],
                },
            },
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_income_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["CTUID", "median_household_income", "population_2021"],
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_profile_income_csv(path: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "CENSUS_YEAR",
        "DGUID",
        "ALT_GEO_CODE",
        "GEO_LEVEL",
        "GEO_NAME",
        "TNR_SF",
        "TNR_LF",
        "DATA_QUALITY_FLAG",
        "CHARACTERISTIC_ID",
        "CHARACTERISTIC_NAME",
        "CHARACTERISTIC_NOTE",
        "C1_COUNT_TOTAL",
        "SYMBOL",
    ]
    with path.open("w", newline="", encoding="latin-1") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_calculate_quintile_cut_points_fallback_for_small_series() -> None:
    cuts = _calculate_quintile_cut_points([100.0, 200.0, 300.0])
    assert len(cuts) == 4
    assert cuts[0] < cuts[-1]


def test_process_ontario_real_data_include_no_data_true(tmp_path: Path) -> None:
    geo_path = tmp_path / "boundaries.geojson"
    income_path = tmp_path / "income.csv"
    output_path = tmp_path / "out.geojson"
    manifest_path = tmp_path / "manifest.json"

    _write_boundary_geojson(geo_path)
    _write_income_csv(
        income_path,
        [
            {"CTUID": "0001", "median_household_income": "50000", "population_2021": "1200"},
            {"CTUID": "0002", "median_household_income": "", "population_2021": "900"},
        ],
    )

    process_ontario_real_data(
        census_geo=geo_path,
        census_shp=None,
        income_path=income_path,
        output_path=output_path,
        optimized_output_path=None,
        manifest_path=manifest_path,
        tolerance=0.0,
        optimized_tolerance=0.001,
        include_no_data=True,
        size_warning_bytes=2_000_000,
        source_boundary_url=None,
        source_income_url=None,
    )

    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["type"] == "FeatureCollection"
    assert len(output["features"]) == 2

    no_data_feature = next(
        feature for feature in output["features"] if feature["properties"]["tract_id"] == "0002"
    )
    assert no_data_feature["properties"]["income_quintile"] == 0
    assert no_data_feature["properties"]["median_household_income"] is None

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["output"]["feature_count"] == 2
    assert manifest["output"]["quintile_distribution"]["0"] == 1


def test_process_ontario_real_data_include_no_data_false(tmp_path: Path) -> None:
    geo_path = tmp_path / "boundaries.geojson"
    income_path = tmp_path / "income.csv"
    output_path = tmp_path / "out.geojson"
    manifest_path = tmp_path / "manifest.json"

    _write_boundary_geojson(geo_path)
    _write_income_csv(
        income_path,
        [
            {"CTUID": "0001", "median_household_income": "50000", "population_2021": "1200"},
            {"CTUID": "0002", "median_household_income": "", "population_2021": "900"},
        ],
    )

    process_ontario_real_data(
        census_geo=geo_path,
        census_shp=None,
        income_path=income_path,
        output_path=output_path,
        optimized_output_path=None,
        manifest_path=manifest_path,
        tolerance=0.0,
        optimized_tolerance=0.001,
        include_no_data=False,
        size_warning_bytes=2_000_000,
        source_boundary_url=None,
        source_income_url=None,
    )

    output = json.loads(output_path.read_text(encoding="utf-8"))
    assert output["type"] == "FeatureCollection"
    assert len(output["features"]) == 1
    assert output["features"][0]["properties"]["tract_id"] == "0001"


def test_load_income_records_profile_export_format(tmp_path: Path) -> None:
    income_path = tmp_path / "profile.csv"
    _write_profile_income_csv(
        income_path,
        [
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05079320001.00",
                "ALT_GEO_CODE": "9320001.00",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "9320001.00",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "1",
                "CHARACTERISTIC_NAME": "Population, 2021",
                "CHARACTERISTIC_NOTE": "1",
                "C1_COUNT_TOTAL": "3100",
                "SYMBOL": "",
            },
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05079320001.00",
                "ALT_GEO_CODE": "9320001.00",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "9320001.00",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "243",
                "CHARACTERISTIC_NAME": "Median total income of household in 2020 ($)",
                "CHARACTERISTIC_NOTE": "",
                "C1_COUNT_TOTAL": "86400",
                "SYMBOL": "",
            },
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S0503932",
                "ALT_GEO_CODE": "932",
                "GEO_LEVEL": "Census metropolitan area",
                "GEO_NAME": "Abbotsford - Mission",
                "TNR_SF": "2.7",
                "TNR_LF": "3.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "243",
                "CHARACTERISTIC_NAME": "Median total income of household in 2020 ($)",
                "CHARACTERISTIC_NOTE": "",
                "C1_COUNT_TOTAL": "81700",
                "SYMBOL": "",
            },
        ],
    )

    records = _load_income_records(income_path)
    assert records["9320001.00"].income == 86400.0
    assert records["9320001.00"].population_2021 == 3100
    assert records["9320001.00"].short_income_suppressed is False
    assert records["9320001.00"].long_income_suppressed is False


def test_load_income_records_profile_export_suppression_flags(tmp_path: Path) -> None:
    income_path = tmp_path / "profile_suppression.csv"
    _write_profile_income_csv(
        income_path,
        [
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05079320001.00",
                "ALT_GEO_CODE": "9320001.00",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "9320001.00",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00009",
                "CHARACTERISTIC_ID": "243",
                "CHARACTERISTIC_NAME": "Median total income of household in 2020 ($)",
                "CHARACTERISTIC_NOTE": "",
                "C1_COUNT_TOTAL": "x",
                "SYMBOL": "x",
            }
        ],
    )

    records = _load_income_records(income_path)
    record = records["9320001.00"]
    assert record.income is None
    assert record.short_income_suppressed is False
    assert record.long_income_suppressed is True


def test_process_ontario_real_data_quintiles_use_on_boundary_scope(tmp_path: Path) -> None:
    geo_path = tmp_path / "boundaries.geojson"
    income_path = tmp_path / "income_profile.csv"
    output_path = tmp_path / "out.geojson"
    manifest_path = tmp_path / "manifest.json"

    _write_boundary_geojson(geo_path)
    _write_profile_income_csv(
        income_path,
        [
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05070001",
                "ALT_GEO_CODE": "0001",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "0001",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "1",
                "CHARACTERISTIC_NAME": "Population, 2021",
                "CHARACTERISTIC_NOTE": "1",
                "C1_COUNT_TOTAL": "1200",
                "SYMBOL": "",
            },
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05070001",
                "ALT_GEO_CODE": "0001",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "0001",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "243",
                "CHARACTERISTIC_NAME": "Median total income of household in 2020 ($)",
                "CHARACTERISTIC_NOTE": "",
                "C1_COUNT_TOTAL": "50000",
                "SYMBOL": "",
            },
            # Non-ON/irrelevant records that should not influence ON quintiles.
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05079999",
                "ALT_GEO_CODE": "9999",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "9999",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "243",
                "CHARACTERISTIC_NAME": "Median total income of household in 2020 ($)",
                "CHARACTERISTIC_NOTE": "",
                "C1_COUNT_TOTAL": "1",
                "SYMBOL": "",
            },
            {
                "CENSUS_YEAR": "2021",
                "DGUID": "2021S05079998",
                "ALT_GEO_CODE": "9998",
                "GEO_LEVEL": "Census tract",
                "GEO_NAME": "9998",
                "TNR_SF": "4.7",
                "TNR_LF": "5.7",
                "DATA_QUALITY_FLAG": "00000",
                "CHARACTERISTIC_ID": "243",
                "CHARACTERISTIC_NAME": "Median total income of household in 2020 ($)",
                "CHARACTERISTIC_NOTE": "",
                "C1_COUNT_TOTAL": "999999",
                "SYMBOL": "",
            },
        ],
    )

    process_ontario_real_data(
        census_geo=geo_path,
        census_shp=None,
        income_path=income_path,
        output_path=output_path,
        optimized_output_path=None,
        manifest_path=manifest_path,
        tolerance=0.0,
        optimized_tolerance=0.001,
        include_no_data=True,
        size_warning_bytes=2_000_000,
        source_boundary_url=None,
        source_income_url=None,
    )

    output = json.loads(output_path.read_text(encoding="utf-8"))
    by_id = {feature["properties"]["tract_id"]: feature for feature in output["features"]}
    assert by_id["0001"]["properties"]["income_quintile"] == 1

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["processing"]["quintile_scope"] == "ON_BOUNDARY_MATCHED"
    assert manifest["processing"]["income_characteristic_id_used"] == 243
    assert manifest["processing"]["population_characteristic_id_used"] == 1


def test_process_ontario_real_data_writes_optimized_output_and_manifest_metrics(
    tmp_path: Path,
) -> None:
    geo_path = tmp_path / "boundaries.geojson"
    income_path = tmp_path / "income.csv"
    output_path = tmp_path / "out.geojson"
    optimized_output_path = tmp_path / "out.optimized.geojson"
    manifest_path = tmp_path / "manifest.json"

    _write_boundary_geojson(geo_path)
    _write_income_csv(
        income_path,
        [
            {"CTUID": "0001", "median_household_income": "50000", "population_2021": "1200"},
            {"CTUID": "0002", "median_household_income": "70000", "population_2021": "900"},
        ],
    )

    process_ontario_real_data(
        census_geo=geo_path,
        census_shp=None,
        income_path=income_path,
        output_path=output_path,
        optimized_output_path=optimized_output_path,
        manifest_path=manifest_path,
        tolerance=0.0,
        optimized_tolerance=0.01,
        include_no_data=True,
        size_warning_bytes=2_000_000,
        source_boundary_url=None,
        source_income_url=None,
    )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["output"]["optimized_path"] == str(optimized_output_path)
    assert manifest["output"]["optimized_feature_count"] == 2
    assert manifest["output"]["optimized_size_bytes"] is not None
    assert manifest["output"]["size_reduction_bytes"] is not None
