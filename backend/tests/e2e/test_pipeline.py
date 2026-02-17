import hashlib
import logging
import time
from collections.abc import Generator
from datetime import UTC, datetime

import pytest
import requests
from waittime.core import (
    EndEvent,
    Measurement,
    MetricFamily,
    PatientScope,
    StartEvent,
    StatisticType,
)
from waittime.services.database import DatabaseService

# Configuration for logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.fixture
def db_service() -> Generator[DatabaseService, None, None]:
    """Fixture to provide database service."""
    service = DatabaseService()
    yield service
    # Cleanup logic could go here if needed, but we used a unique ID to avoid collisions


def test_pipeline_flow(db_service: DatabaseService) -> None:
    """
    End-to-End Smoke Test:
    1. Generate a unique test hospital payload.
    2. Insert it directly into the DB using DatabaseService (simulating a scrape).
    3. Poll the local Next.js API until the data appears.
    4. Verify the API returns the exact values inserted.
    """
    # 0. Pre-flight: Check if local server is running
    api_url = "http://localhost:3000/api/hospitals"
    try:
        requests.get("http://localhost:3000/api/health", timeout=1)
    except requests.RequestException:
        pytest.skip("Local server not running at localhost:3000; skipping E2E smoke test")

    # 1. Setup Data
    # test_id = f"e2e-test-{uuid.uuid4().hex[:8]}" # Unused
    test_hospital_id = "ca-on-e2e-hospital"
    timestamp = datetime.now(UTC)
    expected_wait_minutes = 42

    # Calculate hash for Measurement model
    payload_str = "mock-payload"
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    # Create the measurement object
    measurement = Measurement(
        hospital_id=test_hospital_id,
        timestamp_utc=timestamp,
        value=expected_wait_minutes,
        metric_family=MetricFamily.TIME_TO_PROVIDER,
        start_event=StartEvent.TRIAGE,
        end_event=EndEvent.PHYSICIAN,
        statistic_type=StatisticType.P90,
        patient_scope=PatientScope.ALL,
        source_id="on-health",
        raw_payload_hash=payload_hash,
        raw_payload_snippet=payload_str,
        parser_version="e2e-v1",
    )

    logger.info(f"\n[Setup] Inserting test measurement for {test_hospital_id}...")

    # 2. Action: Simulate Scrape (DB Insert)
    # We need to ensure the hospital exists first, or the foreign key constraint will fail.
    # For this test, we'll assume the hospital might not exist, so let's try to upsert it or use a known one.
    # Actually, let's just insert a dummy hospital row first to be safe.
    try:
        with db_service.get_connection() as conn:
            with conn.cursor() as cur:
                # Ensure source exists
                cur.execute(
                    """
                        INSERT INTO sources (id, name, province, url, telehealth_name, default_metric_family, default_start_event, default_end_event, default_statistic_type)
                        VALUES ('on-health', 'Ontario Health', 'ON', 'http://example.com', 'Telehealth', 'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN', 'P90')
                        ON CONFLICT (id) DO NOTHING
                    """
                )

                cur.execute(
                    """
                        INSERT INTO hospitals (id, name, province, city, latitude, longitude, is_visible, source_id, is_verified)
                        VALUES (%s, %s, 'ON', 'Ottawa', 45.0, -75.0, true, 'on-health', true)
                        ON CONFLICT (id) DO NOTHING
                    """,
                    (test_hospital_id, "E2E Test Hospital"),
                )
    except Exception as e:
        pytest.fail(f"Failed to setup test hospital: {e}")

    # Now insert the measurement
    try:
        db_service.insert_measurement(measurement)
        logger.info("[Action] Database insert successful.")
    except Exception as e:
        pytest.fail(f"Failed to save measurement: {e}")

    # 3. Action: Poll API
    # Note: There is no /api/hospitals/{id} endpoint. We must hit the list endpoint.
    api_url = "http://localhost:3000/api/hospitals"
    logger.info(f"[Action] Polling API at {api_url}...")

    max_retries = 10
    found = False

    for _ in range(max_retries):
        try:
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # data['data'] is the list of hospitals
                hospitals = data.get("data", [])

                # Find our test hospital
                target_hospital = next((h for h in hospitals if h["id"] == test_hospital_id), None)

                if target_hospital:
                    # Check if we have wait time data
                    # The API returns 'current_wait_time' (snake_case) or camelCase depending on serialization.
                    # Looking at route.ts, it returns raw SQL results which are usually snake_case,
                    # but let's check both to be safe or debug.
                    logger.debug(f"[Debug] Found hospital: {target_hospital}")

                    wait_time = target_hospital.get("current_wait_time")

                    if wait_time == expected_wait_minutes:
                        logger.info(f"[Success] API returned expected wait time: {wait_time}")
                        found = True
                        break
                    else:
                        logger.info(
                            f"[Info] API returned {wait_time}, expected {expected_wait_minutes}. Retrying..."
                        )
                else:
                    logger.info("[Info] Test hospital not found in list yet. Retrying...")
            else:
                logger.info(f"[Info] API returned status {response.status_code}. Retrying...")
                logger.debug(f"[Debug] Response body: {response.text}")
        except requests.RequestException as e:
            logger.warning(f"[Warning] API request failed: {e}")

        time.sleep(1)  # Wait 1s between retries

    # 4. Assertion
    assert found, f"API did not return the expected wait time of {expected_wait_minutes} within {max_retries} seconds."

    # 5. Teardown (Optional but good practice)
    # Using a DELETE cleanup would be nice to keep the DB clean
    try:
        with db_service.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM measurements WHERE hospital_id = %s", (test_hospital_id,))
                cur.execute("DELETE FROM hospitals WHERE id = %s", (test_hospital_id,))
        logger.info("[Teardown] Test data cleaned up.")
    except Exception as e:
        logger.warning(f"[Warning] Teardown failed: {e}")
