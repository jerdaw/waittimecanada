#!/usr/bin/env python3
import os
import sys
import psycopg2
from datetime import datetime, timezone

# Target Hospitals for Verification
TARGETS = {
    "ON": "ca-on-alexandra-hospital",
    "QC": "ca-qc-enfant-jesus",  # Try different QC hospital
    "AB": "ca-ab-foothills-medical-centre",
    "BC": "ca-bc-vgh",
}


def get_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("Error: DATABASE_URL not set")
        sys.exit(1)
    return psycopg2.connect(db_url)


def verify_target(cursor, province, hospital_id):
    print(f"\n--- Verifying {province} ({hospital_id}) ---")

    query = """
    SELECT
        m.value,
        m.metric_family,
        m.start_event,
        m.end_event,
        m.timestamp_utc,
        h.name
    FROM measurements m
    JOIN hospitals h ON m.hospital_id = h.id
    WHERE m.hospital_id = %s
    ORDER BY m.timestamp_utc DESC
    LIMIT 1;
    """

    cursor.execute(query, (hospital_id,))
    row = cursor.fetchone()

    if row:
        value, metric, start, end, collected_at, name = row
        # Calculate age
        now = datetime.now(timezone.utc)
        age = now - collected_at
        age_minutes = age.total_seconds() / 60

        print(f"Hospital: {name}")
        print(f"Latest Measurement: {collected_at} ({age_minutes:.1f} minutes ago)")
        print(f"Metric: {metric} ({start} -> {end})")
        print(f"Value: {value}")

        if age_minutes > 120:
            print("⚠️  WARNING: Data is stale (> 2 hours)")
        else:
            print("✅ Data is fresh")

    else:
        print(f"❌ No measurements found for {hospital_id}")


def main():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        for prov, hid in TARGETS.items():
            verify_target(cursor, prov, hid)

        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
