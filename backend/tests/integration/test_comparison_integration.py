"""Integration tests for ComparisonService with real database.

These tests verify the comparison feature works end-to-end with real seeded data.
"""

from datetime import datetime

import pytest
from waittime.services.comparison import ComparisonService
from waittime.services.database import DatabaseService


@pytest.fixture
def comparison_service(db_service: DatabaseService) -> ComparisonService:
    """Create ComparisonService with real database connection."""
    return ComparisonService(db_service)


class TestComparisonWithRealData:
    """Test comparison feature with real seeded Ontario hospitals."""

    def test_compare_two_ontario_hospitals_same_methodology(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should compare two Ontario hospitals with identical methodology."""
        # Get two Ontario hospitals from seeded data
        with db_transaction.get_connection() as conn:
            with db_transaction.get_cursor(conn) as cur:
                # Find two Ontario hospitals with measurements
                cur.execute(
                    """
                    SELECT DISTINCT h.id
                    FROM hospitals h
                    INNER JOIN measurements m ON m.hospital_id = h.id
                    WHERE h.province = 'ON'
                      AND h.is_verified = true
                      AND h.is_visible = true
                    ORDER BY h.id
                    LIMIT 2
                    """
                )
                rows = cur.fetchall()

                if len(rows) < 2:
                    pytest.skip("Need at least 2 Ontario hospitals with measurements")

                hospital_a_id = rows[0]["id"]
                hospital_b_id = rows[1]["id"]

        # Perform comparison
        result = comparison_service.compare_hospitals(hospital_a_id, hospital_b_id)

        # Verify comparison result
        assert result["comparable"] is True, "Ontario hospitals should be comparable"
        assert result["divergence_brief"] is None, "Should not have divergence brief"

        # Verify hospital A data
        assert result["hospital_a"]["id"] == hospital_a_id
        assert result["hospital_a"]["province"] == "ON"
        assert "wait_time" in result["hospital_a"]
        assert result["hospital_a"]["wait_time"] > 0

        # Verify hospital B data
        assert result["hospital_b"]["id"] == hospital_b_id
        assert result["hospital_b"]["province"] == "ON"
        assert "wait_time" in result["hospital_b"]
        assert result["hospital_b"]["wait_time"] > 0

        # Verify methodology is identical
        method_a = result["hospital_a"]["methodology"]
        method_b = result["hospital_b"]["methodology"]

        assert method_a["metric_family"] == method_b["metric_family"]
        assert method_a["start_event"] == method_b["start_event"]
        assert method_a["end_event"] == method_b["end_event"]
        assert method_a["statistic_type"] == method_b["statistic_type"]

        # Verify comparison fields
        comp_a = result["hospital_a"]["methodology"]
        comp_b = result["hospital_b"]["methodology"]
        assert comp_a["metric_family"] == "TIME_TO_PROVIDER"
        assert comp_a["statistic_type"] == "MEAN"
        assert comp_b["metric_family"] == "TIME_TO_PROVIDER"
        assert comp_b["statistic_type"] == "MEAN"

        # Verify timestamp
        assert "comparison_timestamp" in result
        assert result["comparison_timestamp"].endswith("Z") or "+" in result["comparison_timestamp"]

    def test_compare_hospitals_with_different_methodologies(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should detect methodology divergence when methodologies differ."""
        # Create test hospitals with different methodologies
        with db_transaction.get_connection() as conn:
            with db_transaction.get_cursor(conn) as cur:
                # Insert test source
                cur.execute(
                    """
                    INSERT INTO sources (
                        id, name, province, url, telehealth_name, telehealth_number,
                        default_metric_family, default_start_event,
                        default_end_event, default_statistic_type
                    ) VALUES (
                        'test-integration-source', 'Test Source', 'ON',
                        'https://test.example.com', 'Test Telehealth', '811',
                        'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN', 'P90'
                    )
                    ON CONFLICT (id) DO NOTHING
                    """
                )

                # Insert test hospital A with TRIAGE→PHYSICIAN P90
                cur.execute(
                    """
                    INSERT INTO hospitals (
                        id, name, province, city, latitude, longitude,
                        is_verified, is_visible, source_id
                    ) VALUES (
                        'test-hospital-a', 'Test Hospital A', 'ON', 'TestCity',
                        45.0, -75.0, true, true, 'test-integration-source'
                    )
                    ON CONFLICT (id) DO UPDATE SET is_verified = true, is_visible = true
                    """
                )

                # Insert test hospital B with REGISTRATION→PHYSICIAN ROLLING_AVG
                cur.execute(
                    """
                    INSERT INTO hospitals (
                        id, name, province, city, latitude, longitude,
                        is_verified, is_visible, source_id
                    ) VALUES (
                        'test-hospital-b', 'Test Hospital B', 'QC', 'TestCity',
                        45.0, -75.0, true, true, 'test-integration-source'
                    )
                    ON CONFLICT (id) DO UPDATE SET is_verified = true, is_visible = true
                    """
                )

                # Insert measurement for hospital A (TRIAGE→PHYSICIAN P90)
                cur.execute(
                    """
                    INSERT INTO measurements (
                        hospital_id, value, timestamp_utc, metric_family,
                        start_event, end_event, statistic_type, patient_scope,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version
                    ) VALUES (
                        'test-hospital-a', 120, NOW(), 'TIME_TO_PROVIDER',
                        'TRIAGE', 'PHYSICIAN', 'P90', 'ALL',
                        'test-integration-source', 'test-hash-a', 'test snippet', 'v1.0'
                    )
                    """
                )

                # Insert measurement for hospital B (REGISTRATION→PHYSICIAN ROLLING_AVG)
                cur.execute(
                    """
                    INSERT INTO measurements (
                        hospital_id, value, timestamp_utc, metric_family,
                        start_event, end_event, statistic_type, patient_scope,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version
                    ) VALUES (
                        'test-hospital-b', 90, NOW(), 'TIME_TO_PROVIDER',
                        'REGISTRATION', 'PHYSICIAN', 'ROLLING_AVG', 'ALL',
                        'test-integration-source', 'test-hash-b', 'test snippet', 'v1.0'
                    )
                    """
                )

        # Perform comparison
        result = comparison_service.compare_hospitals("test-hospital-a", "test-hospital-b")

        # Verify divergence detection
        assert (
            result["comparable"] is False
        ), "Hospitals with different methodologies should not be comparable"
        assert result["divergence_brief"] is not None, "Should have divergence brief"
        assert "TRIAGE vs REGISTRATION" in result["divergence_brief"]
        assert "P90 vs ROLLING_AVG" in result["divergence_brief"]

        # Verify both hospitals returned
        assert result["hospital_a"]["id"] == "test-hospital-a"
        assert result["hospital_b"]["id"] == "test-hospital-b"

        # Verify methodology differences
        assert result["hospital_a"]["methodology"]["start_event"] == "TRIAGE"
        assert result["hospital_b"]["methodology"]["start_event"] == "REGISTRATION"
        assert result["hospital_a"]["methodology"]["statistic_type"] == "P90"
        assert result["hospital_b"]["methodology"]["statistic_type"] == "ROLLING_AVG"

    def test_compare_nonexistent_hospital(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should raise ValueError when hospital doesn't exist."""
        with pytest.raises(ValueError, match="Hospital not found"):
            comparison_service.compare_hospitals("nonexistent-hospital-a", "nonexistent-hospital-b")

    def test_compare_with_unverified_hospital(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should raise ValueError when trying to compare unverified hospital."""
        # Create unverified test hospital
        with db_transaction.get_connection() as conn:
            with db_transaction.get_cursor(conn) as cur:
                cur.execute(
                    """
                    INSERT INTO sources (
                        id, name, province, url, telehealth_name, telehealth_number,
                        default_metric_family, default_start_event,
                        default_end_event, default_statistic_type
                    ) VALUES (
                        'test-unverified-source', 'Test Source', 'ON',
                        'https://test.example.com', 'Test Telehealth', '811',
                        'TIME_TO_PROVIDER', 'TRIAGE', 'PHYSICIAN', 'P90'
                    )
                    ON CONFLICT (id) DO NOTHING
                    """
                )

                cur.execute(
                    """
                    INSERT INTO hospitals (
                        id, name, province, city, latitude, longitude,
                        is_verified, is_visible, source_id
                    ) VALUES (
                        'test-unverified-hospital', 'Unverified Hospital', 'ON', 'TestCity',
                        45.0, -75.0, false, false, 'test-unverified-source'
                    )
                    ON CONFLICT (id) DO UPDATE SET is_verified = false, is_visible = false
                    """
                )

                cur.execute(
                    """
                    INSERT INTO measurements (
                        hospital_id, value, timestamp_utc, metric_family,
                        start_event, end_event, statistic_type, patient_scope,
                        source_id, raw_payload_hash, raw_payload_snippet, parser_version
                    ) VALUES (
                        'test-unverified-hospital', 100, NOW(), 'TIME_TO_PROVIDER',
                        'TRIAGE', 'PHYSICIAN', 'P90', 'ALL',
                        'test-unverified-source', 'test-hash', 'test snippet', 'v1.0'
                    )
                    """
                )

        # Try to compare with unverified hospital
        with pytest.raises(ValueError, match="Hospital not found"):
            comparison_service.compare_hospitals("test-unverified-hospital", "test-hospital-a")

    def test_comparison_includes_all_required_fields(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should include all required fields in comparison result."""
        # Get two Ontario hospitals
        with db_transaction.get_connection() as conn:
            with db_transaction.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT h.id
                    FROM hospitals h
                    INNER JOIN measurements m ON m.hospital_id = h.id
                    WHERE h.province = 'ON'
                      AND h.is_verified = true
                      AND h.is_visible = true
                    ORDER BY h.id
                    LIMIT 2
                    """
                )
                rows = cur.fetchall()

                if len(rows) < 2:
                    pytest.skip("Need at least 2 Ontario hospitals with measurements")

                hospital_a_id = rows[0]["id"]
                hospital_b_id = rows[1]["id"]

        result = comparison_service.compare_hospitals(hospital_a_id, hospital_b_id)

        # Verify all required top-level fields
        required_fields = [
            "hospital_a",
            "hospital_b",
            "comparable",
            "divergence_brief",
            "comparison_timestamp",
        ]
        for field in required_fields:
            assert field in result, f"Missing required field: {field}"

        # Verify hospital A has all required fields
        hospital_a_fields = [
            "id",
            "name",
            "province",
            "city",
            "wait_time",
            "last_updated",
            "methodology",
        ]
        for field in hospital_a_fields:
            assert field in result["hospital_a"], f"Missing field in hospital_a: {field}"

        # Verify methodology has all required fields
        methodology_fields = [
            "metric_family",
            "start_event",
            "end_event",
            "statistic_type",
        ]
        for field in methodology_fields:
            assert (
                field in result["hospital_a"]["methodology"]
            ), f"Missing methodology field: {field}"

    def test_wait_times_are_numeric(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should return wait times as numeric values."""
        # Get two Ontario hospitals
        with db_transaction.get_connection() as conn:
            with db_transaction.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT h.id
                    FROM hospitals h
                    INNER JOIN measurements m ON m.hospital_id = h.id
                    WHERE h.province = 'ON'
                      AND h.is_verified = true
                      AND h.is_visible = true
                    ORDER BY h.id
                    LIMIT 2
                    """
                )
                rows = cur.fetchall()

                if len(rows) < 2:
                    pytest.skip("Need at least 2 Ontario hospitals with measurements")

                hospital_a_id = rows[0]["id"]
                hospital_b_id = rows[1]["id"]

        result = comparison_service.compare_hospitals(hospital_a_id, hospital_b_id)

        # Verify wait times are numeric
        assert isinstance(result["hospital_a"]["wait_time"], int | float)
        assert isinstance(result["hospital_b"]["wait_time"], int | float)
        assert result["hospital_a"]["wait_time"] > 0
        assert result["hospital_b"]["wait_time"] > 0

    def test_timestamps_are_iso_format(
        self, db_transaction: DatabaseService, comparison_service: ComparisonService
    ):
        """Should return timestamps in ISO format."""
        # Get two Ontario hospitals
        with db_transaction.get_connection() as conn:
            with db_transaction.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT DISTINCT h.id
                    FROM hospitals h
                    INNER JOIN measurements m ON m.hospital_id = h.id
                    WHERE h.province = 'ON'
                      AND h.is_verified = true
                      AND h.is_visible = true
                    ORDER BY h.id
                    LIMIT 2
                    """
                )
                rows = cur.fetchall()

                if len(rows) < 2:
                    pytest.skip("Need at least 2 Ontario hospitals with measurements")

                hospital_a_id = rows[0]["id"]
                hospital_b_id = rows[1]["id"]

        result = comparison_service.compare_hospitals(hospital_a_id, hospital_b_id)

        # Verify timestamps are ISO format
        assert isinstance(result["hospital_a"]["last_updated"], str)
        assert isinstance(result["hospital_b"]["last_updated"], str)
        assert isinstance(result["comparison_timestamp"], str)

        # Should be parseable as datetime

        datetime.fromisoformat(result["hospital_a"]["last_updated"].replace("Z", "+00:00"))
        datetime.fromisoformat(result["hospital_b"]["last_updated"].replace("Z", "+00:00"))
        datetime.fromisoformat(result["comparison_timestamp"].replace("Z", "+00:00"))
