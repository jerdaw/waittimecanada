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
    AggregateGap,
    Hospital,
    Measurement,
    MeasurementAggregate,
    PublicDataSource,
    PublicHealthAlert,
    PublicHealthSourceAlertState,
    PublicHealthSystemMetric,
    ResourceLocation,
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
    "AggregateGap",
    "Measurement",
    "MeasurementAggregate",
    "Hospital",
    "Source",
    "PublicHealthAlert",
    "PublicHealthSystemMetric",
    "PublicDataSource",
    "PublicHealthSourceAlertState",
    "ResourceLocation",
    "ScraperAlertState",
    "ScraperStatus",
    # Functions
    "are_comparable",
    "generate_divergence_brief",
]
