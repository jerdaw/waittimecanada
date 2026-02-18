#!/usr/bin/env python3
"""Prepare Ontario equity layer GeoJSON from census tract + income inputs.

The output contract is frontend-oriented:
    - tract_id
    - tract_name
    - income_quintile (0-5 where 0 is "No Data")
    - median_household_income
    - population_2021
    - is_placeholder
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import re
import statistics
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_VERSION = "1.4"
DEFAULT_OUTPUT = Path("backend/data/layers/ontario-equity-layer.geojson")
DEFAULT_OPTIMIZED_OUTPUT = Path("backend/data/layers/ontario-equity-layer.optimized.geojson")
DEFAULT_MANIFEST = Path("backend/data/layers/equity-manifest-on.json")


@dataclass(frozen=True)
class IncomeRecord:
    ctuid: str
    income: float | None
    population_2021: int | None
    short_income_suppressed: bool = False
    long_income_suppressed: bool = False


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _normalize_ctuid(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned if cleaned else None


def _normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _extract_by_alias(
    row: dict[str, str],
    aliases: tuple[str, ...],
) -> str | None:
    alias_set = {_normalize_key(alias) for alias in aliases}
    for key, value in row.items():
        if _normalize_key(key) in alias_set:
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _extract_income_field(row: dict[str, str]) -> str | None:
    priority_aliases = (
        "median_household_income",
        "medianincome",
        "median total income of household in 2020 ($)",
        "median total income of household in 2020",
        "v_med_total_inc_hh_2020",
        "col0",
    )
    aliased = _extract_by_alias(row, priority_aliases)
    if aliased is not None:
        return aliased

    for key, value in row.items():
        normalized_key = _normalize_key(key)
        if (
            "median" in normalized_key
            and "income" in normalized_key
            and "household" in normalized_key
        ):
            stripped = value.strip()
            if stripped:
                return stripped
    return None


def _parse_income(value: str | None) -> float | None:
    if value is None:
        return None
    cleaned = value.strip()
    if cleaned in {"", "x", "X", "f", "F", "..", "...", "n/a", "N/A"}:
        return None
    numeric = cleaned.replace(",", "").replace("$", "").replace(" ", "")
    try:
        return float(numeric)
    except ValueError:
        return None


def _parse_population(value: str | None) -> int | None:
    if value is None:
        return None
    cleaned = value.strip().replace(",", "").replace(" ", "")
    if cleaned in {"", "x", "X", "f", "F", "..", "...", "n/a", "N/A"}:
        return None
    try:
        return int(float(cleaned))
    except ValueError:
        return None


def _parse_income_suppression_flags(data_quality_flag: str | None) -> tuple[bool, bool]:
    if data_quality_flag is None:
        return (False, False)
    digits = re.sub(r"[^0-9]", "", data_quality_flag)
    if len(digits) < 5:
        return (False, False)
    short_income_suppressed = digits[2] == "9"
    long_income_suppressed = digits[4] == "9"
    return (short_income_suppressed, long_income_suppressed)


def _is_profile_export_format(fieldnames: list[str] | None) -> bool:
    if not fieldnames:
        return False
    normalized = {_normalize_key(name) for name in fieldnames}
    required = {"geolevel", "characteristicid", "c1counttotal"}
    return required.issubset(normalized)


def _normalize_csv_row(raw_row: dict[str | None, str | None]) -> dict[str, str]:
    return {key: value for key, value in raw_row.items() if key is not None and value is not None}


def _load_income_records_profile_export(reader: csv.DictReader) -> dict[str, IncomeRecord]:
    records: dict[str, IncomeRecord] = {}
    for raw_row in reader:
        row = _normalize_csv_row(raw_row)
        geo_level = (row.get("GEO_LEVEL") or row.get("geo_level") or "").strip().lower()
        if geo_level != "census tract":
            continue

        ctuid = _normalize_ctuid(
            row.get("ALT_GEO_CODE")
            or row.get("alt_geo_code")
            or row.get("GEO_NAME")
            or row.get("geo_name")
        )
        if ctuid is None:
            continue

        short_income_suppressed, long_income_suppressed = _parse_income_suppression_flags(
            row.get("DATA_QUALITY_FLAG") or row.get("data_quality_flag")
        )

        characteristic_raw = (
            row.get("CHARACTERISTIC_ID") or row.get("characteristic_id") or ""
        ).strip()
        if not characteristic_raw:
            continue
        try:
            characteristic_id = int(float(characteristic_raw))
        except ValueError:
            continue

        value = row.get("C1_COUNT_TOTAL") or row.get("c1_count_total")
        existing = records.get(ctuid, IncomeRecord(ctuid=ctuid, income=None, population_2021=None))

        income = existing.income
        population = existing.population_2021
        short_suppressed = existing.short_income_suppressed or short_income_suppressed
        long_suppressed = existing.long_income_suppressed or long_income_suppressed

        if characteristic_id == 243:  # Median total income of household in 2020 ($)
            income = _parse_income(value)
        elif characteristic_id == 1:  # Population, 2021
            population = _parse_population(value)

        records[ctuid] = IncomeRecord(
            ctuid=ctuid,
            income=income,
            population_2021=population,
            short_income_suppressed=short_suppressed,
            long_income_suppressed=long_suppressed,
        )
    return records


def _load_income_records_flat_export(reader: csv.DictReader) -> dict[str, IncomeRecord]:
    records: dict[str, IncomeRecord] = {}
    for raw_row in reader:
        row = _normalize_csv_row(raw_row)
        ctuid = _normalize_ctuid(
            _extract_by_alias(row, ("CTUID", "ctuid", "GEO_ID", "GEOUID", "GEO UID", "geo_code"))
        )
        if ctuid is None:
            continue

        income = _parse_income(_extract_income_field(row))
        population = _parse_population(
            _extract_by_alias(
                row,
                (
                    "pop_2021",
                    "population_2021",
                    "population, 2021",
                    "population 2021",
                ),
            )
        )
        records[ctuid] = IncomeRecord(ctuid=ctuid, income=income, population_2021=population)
    return records


def _calculate_quintile_cut_points(values: list[float]) -> list[float]:
    if len(values) < 5:
        minimum = min(values)
        maximum = max(values)
        if minimum == maximum:
            return [minimum, minimum, minimum, minimum]
        step = (maximum - minimum) / 5
        return [minimum + step, minimum + (step * 2), minimum + (step * 3), minimum + (step * 4)]
    return [statistics.quantiles(values, n=5, method="inclusive")[i] for i in range(4)]


def _get_quintile(value: float, cut_points: list[float]) -> int:
    for index, cut in enumerate(cut_points):
        if value <= cut:
            return index + 1
    return 5


def _load_geojson(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if payload.get("type") != "FeatureCollection":
        raise ValueError(f"{path} is not a GeoJSON FeatureCollection")
    if not isinstance(payload.get("features"), list):
        raise ValueError(f"{path} has invalid features list")
    return payload


def _load_shapefile_as_geojson(path: Path) -> dict[str, Any]:
    try:
        import geopandas as gpd
    except ImportError as exc:
        raise RuntimeError(
            "Shapefile input requires geopandas. Install with: "
            "cd backend && uv sync --extra equity"
        ) from exc

    gdf = gpd.read_file(path)
    return json.loads(gdf.to_json())


def _load_boundaries(census_geo: Path | None, census_shp: Path | None) -> dict[str, Any]:
    if census_geo and census_shp:
        raise ValueError("Provide only one of --census-geo or --census-shp")
    if census_geo is None and census_shp is None:
        raise ValueError("Provide one of --census-geo or --census-shp")
    if census_geo is not None:
        return _load_geojson(census_geo)
    if census_shp is None:
        raise ValueError("Shapefile path missing")
    return _load_shapefile_as_geojson(census_shp)


def _simplify_geometry(geometry: dict[str, Any], tolerance: float) -> dict[str, Any]:
    if tolerance <= 0:
        return geometry
    try:
        from shapely.geometry import mapping, shape
    except ImportError:
        return geometry
    return mapping(shape(geometry).simplify(tolerance=tolerance, preserve_topology=True))


def _load_income_records(path: Path) -> dict[str, IncomeRecord]:
    last_error: UnicodeDecodeError | None = None
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with path.open(encoding=encoding, newline="") as handle:
                reader = csv.DictReader(handle)
                if _is_profile_export_format(reader.fieldnames):
                    return _load_income_records_profile_export(reader)
                return _load_income_records_flat_export(reader)
        except UnicodeDecodeError as exc:
            last_error = exc

    if last_error is not None:
        raise last_error
    return {}


def _normalize_tract_name(properties: dict[str, Any], fallback_ctuid: str) -> str:
    for key in ("tract_name", "CTNAME", "ctname", "name", "Name"):
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return fallback_ctuid


def _normalize_ctuid_from_feature(properties: dict[str, Any]) -> str | None:
    for key in ("tract_id", "CTUID", "ctuid", "GEO_ID", "GEOUID", "geo_id"):
        value = properties.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, int):
            return str(value)
    return None


def _is_ontario_boundary_feature(properties: dict[str, Any]) -> bool:
    pruid = properties.get("PRUID")
    if isinstance(pruid, int):
        return pruid == 35
    if isinstance(pruid, str):
        cleaned = pruid.strip()
        if not cleaned:
            return False
        return cleaned.zfill(2) == "35"
    return False


def _build_output_feature(
    feature: dict[str, Any],
    income_record: IncomeRecord | None,
    include_no_data: bool,
    cut_points: list[float],
    tolerance: float,
) -> dict[str, Any] | None:
    source_properties = feature.get("properties", {})
    if not isinstance(source_properties, dict):
        return None

    ctuid = _normalize_ctuid_from_feature(source_properties)
    if ctuid is None:
        return None

    income = income_record.income if income_record is not None else None
    if income is None and not include_no_data:
        return None

    quintile = 0 if income is None else _get_quintile(income, cut_points)
    tract_name = _normalize_tract_name(source_properties, ctuid)
    population_2021 = income_record.population_2021 if income_record is not None else None
    short_income_suppressed = (
        income_record.short_income_suppressed if income_record is not None else None
    )
    long_income_suppressed = (
        income_record.long_income_suppressed if income_record is not None else None
    )
    geometry = feature.get("geometry")
    if not isinstance(geometry, dict):
        return None
    normalized_geometry = _simplify_geometry(geometry, tolerance=tolerance)

    return {
        "type": "Feature",
        "id": ctuid,
        "properties": {
            "tract_id": ctuid,
            "tract_name": tract_name,
            "income_quintile": quintile,
            "median_household_income": income,
            "population_2021": population_2021,
            "short_income_suppressed": short_income_suppressed,
            "long_income_suppressed": long_income_suppressed,
            "is_placeholder": False,
        },
        "geometry": normalized_geometry,
    }


def _quintile_distribution(features: list[dict[str, Any]]) -> dict[str, int]:
    distribution = {str(i): 0 for i in range(6)}
    for feature in features:
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        quintile_value = properties.get("income_quintile", 0)
        distribution[str(int(quintile_value))] = distribution.get(str(int(quintile_value)), 0) + 1
    return distribution


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=True, separators=(",", ":"))


def _build_optimized_features(
    features: list[dict[str, Any]],
    tolerance: float,
) -> list[dict[str, Any]]:
    optimized: list[dict[str, Any]] = []
    for feature in features:
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            continue
        optimized.append(
            {
                **feature,
                "geometry": _simplify_geometry(geometry, tolerance=tolerance),
            }
        )
    return optimized


def _generate_dummy_data(output_path: Path, manifest_path: Path, size_warning_bytes: int) -> None:
    print(f"Generating dummy equity layer at {output_path}...")
    features: list[dict[str, Any]] = []

    base_lat = 43.65
    base_lon = -79.38
    incomes: list[float] = []
    for i in range(10):
        for j in range(10):
            lat = base_lat + (i * 0.05)
            lon = base_lon + (j * 0.05)
            income = float(random.randint(30000, 150000))
            incomes.append(income)

    cut_points = _calculate_quintile_cut_points(incomes)
    income_index = 0
    for i in range(10):
        for j in range(10):
            lat = base_lat + (i * 0.05)
            lon = base_lon + (j * 0.05)
            ctuid = f"5350{i}{j}"
            income = incomes[income_index]
            income_index += 1
            feature = {
                "type": "Feature",
                "id": ctuid,
                "properties": {
                    "tract_id": ctuid,
                    "tract_name": f"Dummy tract {ctuid}",
                    "income_quintile": _get_quintile(income, cut_points),
                    "median_household_income": income,
                    "population_2021": random.randint(2000, 8000),
                    "is_placeholder": True,
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [lon, lat],
                            [lon + 0.05, lat],
                            [lon + 0.05, lat + 0.05],
                            [lon, lat + 0.05],
                            [lon, lat],
                        ]
                    ],
                },
            }
            features.append(feature)

    payload = {"type": "FeatureCollection", "features": features}
    _write_json(output_path, payload)
    output_size = output_path.stat().st_size
    if output_size > size_warning_bytes:
        print(f"Warning: output file is {output_size} bytes (> {size_warning_bytes})")

    manifest = {
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "province": "ON",
        "mode": "dummy",
        "inputs": {},
        "processing": {"tolerance": 0.0, "include_no_data": False},
        "output": {
            "path": str(output_path),
            "size_bytes": output_size,
            "feature_count": len(features),
            "quintile_distribution": _quintile_distribution(features),
        },
    }
    _write_json(manifest_path, manifest)
    print(f"Created {len(features)} dummy census tracts and manifest at {manifest_path}.")


def process_ontario_real_data(
    census_geo: Path | None,
    census_shp: Path | None,
    income_path: Path,
    output_path: Path,
    optimized_output_path: Path | None,
    manifest_path: Path,
    tolerance: float,
    optimized_tolerance: float,
    include_no_data: bool,
    size_warning_bytes: int,
    source_boundary_url: str | None,
    source_income_url: str | None,
) -> None:
    boundaries = _load_boundaries(census_geo=census_geo, census_shp=census_shp)
    income_records = _load_income_records(income_path)
    if not income_records:
        raise ValueError("No CTUID rows parsed from income CSV")

    features = boundaries.get("features", [])
    if not isinstance(features, list):
        raise ValueError("Boundary input has invalid 'features' payload")

    on_boundary_ctuids: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        if not _is_ontario_boundary_feature(properties):
            continue
        ctuid = _normalize_ctuid_from_feature(properties)
        if ctuid is not None:
            on_boundary_ctuids.add(ctuid)

    incomes = [
        income_records[ctuid].income
        for ctuid in on_boundary_ctuids
        if ctuid in income_records and income_records[ctuid].income is not None
    ]
    if not incomes:
        raise ValueError("No numeric income values parsed from income CSV")

    cut_points = _calculate_quintile_cut_points(incomes)
    output_features: list[dict[str, Any]] = []
    missing_income_count = 0
    missing_ctuid_count = 0
    skipped_non_ontario_count = 0
    missing_income_breakdown: dict[str, int] = {
        "no_income_record": 0,
        "suppressed_short": 0,
        "suppressed_long": 0,
        "suppressed_both": 0,
        "missing_or_non_numeric": 0,
    }

    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        if not _is_ontario_boundary_feature(properties):
            skipped_non_ontario_count += 1
            continue
        ctuid = _normalize_ctuid_from_feature(properties)
        if ctuid is None:
            missing_ctuid_count += 1
            continue
        income_record = income_records.get(ctuid)
        if income_record is None or income_record.income is None:
            missing_income_count += 1
            if income_record is None:
                missing_income_breakdown["no_income_record"] += 1
            elif income_record.short_income_suppressed and income_record.long_income_suppressed:
                missing_income_breakdown["suppressed_both"] += 1
            elif income_record.long_income_suppressed:
                missing_income_breakdown["suppressed_long"] += 1
            elif income_record.short_income_suppressed:
                missing_income_breakdown["suppressed_short"] += 1
            else:
                missing_income_breakdown["missing_or_non_numeric"] += 1

        normalized_feature = _build_output_feature(
            feature=feature,
            income_record=income_record,
            include_no_data=include_no_data,
            cut_points=cut_points,
            tolerance=tolerance,
        )
        if normalized_feature is not None:
            output_features.append(normalized_feature)

    payload = {"type": "FeatureCollection", "features": output_features}
    _write_json(output_path, payload)

    output_size = output_path.stat().st_size
    if output_size > size_warning_bytes:
        print(f"Warning: output file is {output_size} bytes (> {size_warning_bytes})")

    optimized_output_size: int | None = None
    optimized_feature_count: int | None = None
    if optimized_output_path is not None:
        optimized_features = _build_optimized_features(
            output_features,
            tolerance=optimized_tolerance,
        )
        optimized_payload = {"type": "FeatureCollection", "features": optimized_features}
        _write_json(optimized_output_path, optimized_payload)
        optimized_output_size = optimized_output_path.stat().st_size
        optimized_feature_count = len(optimized_features)
        if optimized_output_size > size_warning_bytes:
            print(
                f"Warning: optimized output file is "
                f"{optimized_output_size} bytes (> {size_warning_bytes})"
            )

    manifest = {
        "script_version": SCRIPT_VERSION,
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "province": "ON",
        "mode": "real",
        "inputs": {
            "census_geo": str(census_geo) if census_geo else None,
            "census_geo_sha256": _sha256(census_geo) if census_geo else None,
            "census_shp": str(census_shp) if census_shp else None,
            "census_shp_sha256": _sha256(census_shp) if census_shp else None,
            "income_csv": str(income_path),
            "income_csv_sha256": _sha256(income_path),
            "source_boundary_url": source_boundary_url,
            "source_income_url": source_income_url,
        },
        "processing": {
            "tolerance": tolerance,
            "optimized_tolerance": optimized_tolerance if optimized_output_path else None,
            "include_no_data": include_no_data,
            "quintile_scope": "ON_BOUNDARY_MATCHED",
            "income_characteristic_id_used": 243,
            "population_characteristic_id_used": 1,
            "income_cut_points": cut_points,
        },
        "output": {
            "path": str(output_path),
            "size_bytes": output_size,
            "feature_count": len(output_features),
            "optimized_path": str(optimized_output_path) if optimized_output_path else None,
            "optimized_size_bytes": optimized_output_size,
            "optimized_feature_count": optimized_feature_count,
            "size_reduction_bytes": (
                output_size - optimized_output_size if optimized_output_size is not None else None
            ),
            "size_reduction_percent": (
                round((output_size - optimized_output_size) / output_size, 6)
                if optimized_output_size is not None and output_size > 0
                else None
            ),
            "on_boundary_tract_count": len(on_boundary_ctuids),
            "missing_ctuid_features": missing_ctuid_count,
            "missing_income_features": missing_income_count,
            "missing_income_breakdown": missing_income_breakdown,
            "skipped_non_ontario_features": skipped_non_ontario_count,
            "quintile_distribution": _quintile_distribution(output_features),
        },
    }
    _write_json(manifest_path, manifest)
    print(f"Saved {len(output_features)} features to {output_path}")
    if optimized_output_path is not None:
        print(f"Saved {optimized_feature_count} optimized features to {optimized_output_path}")
    print(f"Manifest written to {manifest_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare Ontario equity layer GeoJSON")
    parser.add_argument("--province", default="ON", help="Province code (only ON supported in M28)")
    parser.add_argument("--dummy", action="store_true", help="Generate normalized dummy data")
    parser.add_argument("--census-geo", type=Path, help="Path to Census Tracts GeoJSON")
    parser.add_argument("--census-shp", type=Path, help="Path to Census Tracts SHP file")
    parser.add_argument("--income", type=Path, help="Path to Income CSV")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output GeoJSON path")
    parser.add_argument(
        "--optimized-output",
        type=Path,
        default=None,
        help="Optional optimized GeoJSON output path for map loading",
    )
    parser.add_argument(
        "--manifest-output", type=Path, default=DEFAULT_MANIFEST, help="Output manifest JSON path"
    )
    parser.add_argument(
        "--tolerance",
        type=float,
        default=0.0,
        help="Canonical geometry simplification tolerance (0 keeps full geometry)",
    )
    parser.add_argument(
        "--optimized-tolerance",
        type=float,
        default=0.001,
        help="Simplification tolerance for optimized output geometry",
    )
    parser.add_argument(
        "--include-no-data",
        action="store_true",
        help="Include tracts with missing/suppressed income as quintile 0",
    )
    parser.add_argument(
        "--size-warning-bytes",
        type=int,
        default=2_000_000,
        help="Warn if output file size exceeds this threshold",
    )
    parser.add_argument(
        "--source-boundary-url", type=str, default=None, help="Optional source URL for manifest"
    )
    parser.add_argument(
        "--source-income-url", type=str, default=None, help="Optional source URL for manifest"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    province = str(args.province).strip().upper()
    if province != "ON":
        raise ValueError("M28 implementation currently supports Ontario (ON) only")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_output.parent.mkdir(parents=True, exist_ok=True)
    if args.optimized_output is not None:
        args.optimized_output.parent.mkdir(parents=True, exist_ok=True)

    if args.dummy:
        _generate_dummy_data(
            output_path=args.output,
            manifest_path=args.manifest_output,
            size_warning_bytes=int(args.size_warning_bytes),
        )
        return

    if args.income is None:
        raise ValueError("--income is required for real data mode")

    process_ontario_real_data(
        census_geo=args.census_geo,
        census_shp=args.census_shp,
        income_path=args.income,
        output_path=args.output,
        optimized_output_path=args.optimized_output,
        manifest_path=args.manifest_output,
        tolerance=float(args.tolerance),
        optimized_tolerance=float(args.optimized_tolerance),
        include_no_data=bool(args.include_no_data),
        size_warning_bytes=int(args.size_warning_bytes),
        source_boundary_url=args.source_boundary_url,
        source_income_url=args.source_income_url,
    )


if __name__ == "__main__":
    main()
