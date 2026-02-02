"""Comparison service for analyzing methodology differences between hospitals.

Provides utilities for:
- Fetching latest measurements for comparison
- Determining comparability
- Generating divergence briefs
"""

import logging
from datetime import UTC, datetime

from waittime.core import Measurement, are_comparable, generate_divergence_brief
from waittime.services.database import DatabaseService

logger = logging.getLogger(__name__)


class ComparisonService:
    """Service for comparing wait time measurements across hospitals."""

    def __init__(self, db: DatabaseService) -> None:
        """Initialize with database service.

        Args:
            db: DatabaseService instance for data access
        """
        self.db = db

    def compare_hospitals(
        self,
        hospital_a_id: str,
        hospital_b_id: str,
    ) -> dict:
        """Compare two hospitals and analyze methodology differences.

        Args:
            hospital_a_id: First hospital identifier
            hospital_b_id: Second hospital identifier

        Returns:
            Dict with comparison results:
            {
                'hospital_a': {...},  # Hospital + latest measurement
                'hospital_b': {...},
                'comparable': bool,
                'divergence_brief': str | None,
                'comparison_timestamp': str
            }

        Raises:
            ValueError: If either hospital not found or has no measurements
        """
        # Fetch hospitals with latest measurements
        hospital_a = self._get_hospital_with_measurement(hospital_a_id)
        hospital_b = self._get_hospital_with_measurement(hospital_b_id)

        if not hospital_a:
            raise ValueError(f"Hospital not found or has no data: {hospital_a_id}")
        if not hospital_b:
            raise ValueError(f"Hospital not found or has no data: {hospital_b_id}")

        # Build Measurement objects
        measurement_a = self._dict_to_measurement(hospital_a["measurement"])
        measurement_b = self._dict_to_measurement(hospital_b["measurement"])

        # Check comparability
        comparable = are_comparable(measurement_a, measurement_b)

        # Generate divergence brief if not comparable
        divergence_brief = None
        if not comparable:
            divergence_brief = generate_divergence_brief(measurement_a, measurement_b)

        return {
            "hospital_a": {
                "id": hospital_a["id"],
                "name": hospital_a["name"],
                "province": hospital_a["province"],
                "city": hospital_a["city"],
                "wait_time": hospital_a["measurement"]["value"],
                "last_updated": hospital_a["measurement"]["timestamp_utc"],
                "methodology": {
                    "metric_family": hospital_a["measurement"]["metric_family"],
                    "start_event": hospital_a["measurement"]["start_event"],
                    "end_event": hospital_a["measurement"]["end_event"],
                    "statistic_type": hospital_a["measurement"]["statistic_type"],
                },
            },
            "hospital_b": {
                "id": hospital_b["id"],
                "name": hospital_b["name"],
                "province": hospital_b["province"],
                "city": hospital_b["city"],
                "wait_time": hospital_b["measurement"]["value"],
                "last_updated": hospital_b["measurement"]["timestamp_utc"],
                "methodology": {
                    "metric_family": hospital_b["measurement"]["metric_family"],
                    "start_event": hospital_b["measurement"]["start_event"],
                    "end_event": hospital_b["measurement"]["end_event"],
                    "statistic_type": hospital_b["measurement"]["statistic_type"],
                },
            },
            "comparable": comparable,
            "divergence_brief": divergence_brief,
            "comparison_timestamp": datetime.now(UTC).isoformat(),
        }

    def _get_hospital_with_measurement(self, hospital_id: str) -> dict | None:
        """Fetch hospital with its latest measurement.

        Args:
            hospital_id: Hospital identifier

        Returns:
            Dict with hospital info and measurement, or None if not found
        """
        with self.db.get_connection() as conn:
            with self.db.get_cursor(conn) as cur:
                cur.execute(
                    """
                    SELECT
                        h.id,
                        h.name,
                        h.province,
                        h.city,
                        h.latitude,
                        h.longitude,
                        m.value,
                        m.timestamp_utc,
                        m.metric_family,
                        m.start_event,
                        m.end_event,
                        m.statistic_type,
                        m.patient_scope
                    FROM hospitals h
                    INNER JOIN LATERAL (
                        SELECT *
                        FROM measurements
                        WHERE hospital_id = h.id
                        ORDER BY timestamp_utc DESC
                        LIMIT 1
                    ) m ON true
                    WHERE h.id = %s
                      AND h.is_visible = true
                      AND h.is_verified = true
                    """,
                    (hospital_id,),
                )
                row = cur.fetchone()

                if not row:
                    return None

                return {
                    "id": row["id"],
                    "name": row["name"],
                    "province": row["province"],
                    "city": row["city"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "measurement": {
                        "value": float(row["value"]),
                        "timestamp_utc": row["timestamp_utc"].isoformat(),
                        "metric_family": row["metric_family"],
                        "start_event": row["start_event"],
                        "end_event": row["end_event"],
                        "statistic_type": row["statistic_type"],
                        "patient_scope": row["patient_scope"],
                    },
                }

    def _dict_to_measurement(self, data: dict) -> Measurement:
        """Convert database dict to Measurement model.

        Args:
            data: Dict with measurement fields

        Returns:
            Measurement instance
        """
        from waittime.core import (
            EndEvent,
            MetricFamily,
            PatientScope,
            StartEvent,
            StatisticType,
        )

        return Measurement(
            hospital_id="temp",  # Not used for comparison
            value=data["value"],
            timestamp_utc=datetime.fromisoformat(data["timestamp_utc"]),
            metric_family=MetricFamily(data["metric_family"]),
            start_event=StartEvent(data["start_event"]),
            end_event=EndEvent(data["end_event"]),
            statistic_type=StatisticType(data["statistic_type"]),
            patient_scope=PatientScope(data["patient_scope"]),
            source_id="temp",  # Not used for comparison
            raw_payload_hash="0" * 64,  # Not used for comparison
            parser_version="temp",  # Not used for comparison
        )
