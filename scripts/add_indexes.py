import logging
import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("add_indexes")

# Load environment
env_file = Path(__file__).parents[1] / "backend/.env.local"
if not env_file.exists():
    env_file = Path(__file__).parents[1] / "backend/.env"
load_dotenv(env_file)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL not set")
    sys.exit(1)


def add_indexes():
    logger.info("Connecting to database...")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        cur = conn.cursor()

        indexes = [
            (
                "idx_measurements_hospital_date",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_measurements_hospital_date ON measurements (hospital_id, timestamp_utc DESC);",
            ),
            (
                "idx_measurements_source_date",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_measurements_source_date ON measurements (source_id, timestamp_utc);",
            ),
            (
                "idx_hospitals_province_visible",
                "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_hospitals_province_visible ON hospitals (province) WHERE is_visible = true;",
            ),
        ]

        for idx_name, sql in indexes:
            logger.info(f"Applying index: {idx_name}")
            try:
                cur.execute(sql)
                logger.info(f"Successfully applied {idx_name}")
            except Exception as e:
                logger.error(f"Failed to apply {idx_name}: {e}")

        cur.close()
        conn.close()
        logger.info("Done.")

    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    add_indexes()
