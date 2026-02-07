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
    "ScraperStatus",
    # Functions
    "are_comparable",
    "generate_divergence_brief",
]
