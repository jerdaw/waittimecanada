#!/usr/bin/env python3
"""Import hospital data from CSV and geocode using Nominatim.

Usage:
    python scripts/import_hospitals.py
"""

import csv
import hashlib
import time
from pathlib import Path

import httpx


def load_csv(filepath: Path) -> list[dict]:
    """Load CSV file into list of dicts."""
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def merge_hospital_data(primary_data: list[dict], secondary_data: list[dict]) -> list[dict]:
    """Merge hospital data, preferring primary source but adding secondary lat/long where available."""
    # Index secondary data by hospital name for quick lookup
    secondary_by_name = {h["hospital_name"]: h for h in secondary_data}

    merged = []
    for hospital in primary_data:
        name = hospital["hospital_name"]
        result = hospital.copy()

        # If primary source doesn't have lat/long but secondary does, use secondary's
        if not hospital.get("latitude") and name in secondary_by_name:
            secondary_hospital = secondary_by_name[name]
            if secondary_hospital.get("latitude") and secondary_hospital.get("longitude"):
                result["latitude"] = secondary_hospital["latitude"]
                result["longitude"] = secondary_hospital["longitude"]

        merged.append(result)

    return merged


def geocode_nominatim(
    hospital_name: str, address: str, city: str, province: str = "Ontario"
) -> tuple[float, float] | None:
    """Geocode using OpenStreetMap Nominatim API.

    Rate limit: 1 request per second.
    """
    # Build query: "Address, City, Province, Canada"
    query = f"{address}, {city}, {province}, Canada"

    params = {
        "q": query,
        "format": "json",
        "limit": 1,
        "countrycodes": "ca",
    }
    headers = {"User-Agent": "WaitTimeCanada/1.0 (hospital data import)"}

    try:
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"  ✅ {hospital_name}: ({lat:.4f}, {lon:.4f})")
            return lat, lon

        # Try with just city if address fails
        params["q"] = f"{hospital_name}, {city}, {province}, Canada"
        response = httpx.get(
            "https://nominatim.openstreetmap.org/search",
            params=params,
            headers=headers,
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()

        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"  ✅ {hospital_name} (fallback): ({lat:.4f}, {lon:.4f})")
            return lat, lon

        print(f"  ❌ {hospital_name}: No results")
        return None

    except Exception as e:
        print(f"  ❌ {hospital_name}: Error - {e}")
        return None


def generate_hospital_id(name: str) -> str:
    """Generate stable hospital ID from name."""
    # Normalize name to slug
    slug = name.lower()
    slug = slug.replace("'", "")
    slug = slug.replace("(", "").replace(")", "")
    slug = slug.replace(" - ", "-").replace(" ", "-")
    slug = slug.replace("--", "-")
    return f"ca-on-{slug}"


def main():
    """Main entry point."""
    # Paths
    base_dir = Path(__file__).parent.parent.parent
    docs_dir = base_dir / "docs"
    chatgpt_csv = docs_dir / "hospital-data-primary.csv"
    gemini_csv = docs_dir / "hospital-data-secondary.csv"
    output_csv = docs_dir / "hospitals-geocoded.csv"

    print("Loading CSV files...")
    chatgpt_data = load_csv(chatgpt_csv)
    gemini_data = load_csv(gemini_csv)

    print(f"  Primary source: {len(chatgpt_data)} hospitals")
    print(f"  Secondary source: {len(gemini_data)} hospitals")

    print("\nMerging data...")
    merged_data = merge_hospital_data(chatgpt_data, gemini_data)

    # Count how many already have coordinates
    with_coords = sum(1 for h in merged_data if h.get("latitude") and h.get("longitude"))
    print(f"  {with_coords} hospitals already have coordinates from fallback source")

    print("\nGeocoding hospitals (1 request per second)...")
    results = []
    for i, hospital in enumerate(merged_data):
        name = hospital["hospital_name"]
        city = hospital.get("city", "")
        address = hospital.get("address", "")
        phone = hospital.get("phone", "")

        # Check if we already have coordinates
        lat = hospital.get("latitude", "")
        lon = hospital.get("longitude", "")

        if lat and lon:
            print(f"  ⏭️  {name}: Already has coordinates ({lat}, {lon})")
            lat = float(lat)
            lon = float(lon)
        else:
            # Rate limit: 1 request per second
            if i > 0:
                time.sleep(1.1)

            coords = geocode_nominatim(name, address, city)
            if coords:
                lat, lon = coords
            else:
                # Use city centroid as fallback
                lat, lon = 0.0, 0.0

        results.append({
            "id": generate_hospital_id(name),
            "name": name,
            "city": city,
            "address": address,
            "latitude": lat,
            "longitude": lon,
            "phone": phone,
            "province": "ON",
        })

    # Write output CSV
    print(f"\nWriting {len(results)} hospitals to {output_csv}...")
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["id", "name", "city", "address", "latitude", "longitude", "phone", "province"],
        )
        writer.writeheader()
        writer.writerows(results)

    # Summary
    geocoded = sum(1 for r in results if r["latitude"] != 0.0)
    print(f"\n✅ Done! {geocoded}/{len(results)} hospitals geocoded successfully")
    print(f"   Output: {output_csv}")


if __name__ == "__main__":
    main()
