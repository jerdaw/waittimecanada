"""Core domain models and ontology.

This module exports the foundational types used throughout the application.
"""

from waittime.core.enums import (
    EndEvent,
    MetricFamily,
    PatientScope,
    StartEvent,
    StatisticType,
)
from waittime.core.models import (
    Hospital,
    Measurement,
    MeasurementAggregate,
    ScraperAlertState,
    ScraperStatus,
    Source,
    are_comparable,
    generate_divergence_brief,
)

__all__ = [
    # Enums
    "MetricFamily",
    "StartEvent",
    "EndEvent",
    "StatisticType",
    "PatientScope",
    # Models
    "Measurement",
    "MeasurementAggregate",
    "Hospital",
    "Source",
    "ScraperAlertState",
    "ScraperStatus",
    # Functions
    "are_comparable",
    "generate_divergence_brief",
]
