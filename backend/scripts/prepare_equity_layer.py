#!/usr/bin/env python3
"""
Prepare census tract equity layer for Mapbox.

Usage:
    python backend/scripts/prepare_equity_layer.py --dummy
    python backend/scripts/prepare_equity_layer.py --census-geo data/boundaries/ontario.geojson --income data/census/income.csv --output backend/data/layers/ontario-equity-layer.geojson
"""

import argparse
import csv
import json
import math
import random
import statistics
from pathlib import Path
from typing import Any


def calculate_quintiles(values: list[float]) -> list[float]:
    """Return cut points for 5 quintiles."""
    return [statistics.quantiles(values, n=5)[i] for i in range(4)]


def get_quintile(value: float, cut_points: list[float]) -> int:
    """Return 1-5 quintile for a value."""
    for i, cut in enumerate(cut_points):
        if value <= cut:
            return i + 1
    return 5


def generate_dummy_data(output_path: Path) -> None:
    """Generate dummy Ontario census tracts with random income data."""
    print(f"Generating dummy equity layer at {output_path}...")

    # Simple grid of polygons near Toronto/Ottawa roughly
    features = []

    # Toronto-ish area
    base_lat = 43.65
    base_lon = -79.38

    for i in range(10):
        for j in range(10):
            lat = base_lat + (i * 0.05)
            lon = base_lon + (j * 0.05)

            income = random.randint(30000, 150000)
            quintile = random.randint(1, 5)  # Randomized for dummy

            feature = {
                "type": "Feature",
                "properties": {
                    "CTUID": f"5350{i}{j}",
                    "median_household_income": income,
                    "income_quintile": quintile,
                    "pop_2021": random.randint(2000, 8000)
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [lon, lat],
                        [lon + 0.05, lat],
                        [lon + 0.05, lat + 0.05],
                        [lon, lat + 0.05],
                        [lon, lat]
                    ]]
                }
            }
            features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, "w") as f:
        json.dump(geojson, f)

    print(f"Created {len(features)} dummy census tracts.")


def process_real_data(geo_path: Path, income_path: Path, output_path: Path) -> None:
    """Process real StatsCan data."""
    print(f"Loading geometry from {geo_path}...")
    with open(geo_path) as f:
        geo_data = json.load(f)

    print(f"Loading income data from {income_path}...")
    income_map = {}
    incomes = []

    with open(income_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Adjust column names based on actual StatsCan CSV format
            ctuid = row.get("CTUID") or row.get("GEO_ID")
            income_str = row.get("median_household_income") or row.get("COL0")

            if ctuid and income_str and income_str.strip():
                try:
                    income = float(income_str.replace(",", ""))
                    income_map[ctuid] = income
                    incomes.append(income)
                except ValueError:
                    continue

    if not incomes:
        print("Error: No valid income data found.")
        return

    cut_points = calculate_quintiles(incomes)
    print(f"Income cut points: {cut_points}")

    processed_features = []
    for feature in geo_data["features"]:
        props = feature["properties"]
        ctuid = props.get("CTUID") or props.get("ctuid")

        if ctuid in income_map:
            income = income_map[ctuid]
            props["median_household_income"] = income
            props["income_quintile"] = get_quintile(income, cut_points)
            processed_features.append(feature)

    geo_data["features"] = processed_features

    print(f"Saving {len(processed_features)} merged features to {output_path}...")
    with open(output_path, "w") as f:
        json.dump(geo_data, f)


def main():
    parser = argparse.ArgumentParser(description="Prepare equity layer GeoJSON")
    parser.add_argument("--dummy", action="store_true", help="Generate dummy data")
    parser.add_argument("--census-geo", type=Path, help="Path to Census Tracts GeoJSON")
    parser.add_argument("--income", type=Path, help="Path to Income CSV")
    parser.add_argument("--output", type=Path, default=Path("backend/data/layers/ontario-equity-layer.geojson"))

    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.dummy:
        generate_dummy_data(args.output)
    elif args.census_geo and args.income:
        process_real_data(args.census_geo, args.income, args.output)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
