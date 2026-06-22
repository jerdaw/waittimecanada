#!/usr/bin/env python3
"""Import geocoded hospitals into PostgreSQL database.

Usage:
    python scripts/import_hospitals_to_db.py
"""

import csv
import os
from pathlib import Path

import psycopg2


def main():
    """Main entry point."""
    # Load database URL from environment
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL environment variable not set")
        print("   Export DATABASE_URL in the current shell before running this script")
        return

    # Load CSV
    base_dir = Path(__file__).parent.parent.parent
    csv_path = base_dir / "docs" / "hospitals-geocoded.csv"

    print(f"Loading hospitals from {csv_path}...")
    hospitals = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        hospitals = list(reader)

    print(f"  Found {len(hospitals)} hospitals")

    # Connect to database
    print("\nConnecting to database...")
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Upsert hospitals
            print("Importing hospitals (upsert)...")
            upserted = 0
            for h in hospitals:
                cur.execute(
                    """
                    INSERT INTO hospitals (id, name, city, latitude, longitude, province, source_id, is_verified, is_visible)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, TRUE)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        city = EXCLUDED.city,
                        latitude = EXCLUDED.latitude,
                        longitude = EXCLUDED.longitude,
                        province = EXCLUDED.province,
                        is_verified = TRUE,
                        is_visible = TRUE
                """,
                    (
                        h["id"],
                        h["name"],
                        h["city"],
                        float(h["latitude"]),
                        float(h["longitude"]),
                        h["province"],
                        "ontario-health",  # All Ontario hospitals
                    ),
                )
                upserted += 1
                if upserted % 50 == 0:
                    print(f"  {upserted} hospitals processed...")

            conn.commit()

            # Verify
            cur.execute(
                "SELECT COUNT(*) FROM hospitals WHERE is_verified = TRUE AND is_visible = TRUE"
            )
            count = cur.fetchone()[0]
            print(f"\n✅ Done! {count} verified and visible hospitals in database")

            # Show a few samples
            cur.execute(
                """
                SELECT name, city, latitude, longitude
                FROM hospitals
                WHERE is_verified = TRUE
                ORDER BY name
                LIMIT 5
            """
            )
            print("\nSample hospitals:")
            for row in cur.fetchall():
                print(f"  {row[0]} ({row[1]}): {row[2]:.4f}, {row[3]:.4f}")


if __name__ == "__main__":
    main()
