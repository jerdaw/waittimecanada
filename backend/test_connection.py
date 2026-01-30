#!/usr/bin/env python3
"""Test database connection."""

from waittime.services import DatabaseService

try:
    db = DatabaseService()
    print("✓ Database connection string loaded")

    # Test connection
    with db.get_connection() as conn:
        with db.get_cursor(conn) as cur:
            cur.execute("SELECT version()")
            version = cur.fetchone()
            print(f"✓ Connected to PostgreSQL")
            print(f"  Version: {version['version'][:50]}...")

    print("\n✅ Database connection successful!")

except Exception as e:
    print(f"\n❌ Connection failed: {e}")
    exit(1)
