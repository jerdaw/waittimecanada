"""Metric Ontology Enums.

These enums define the strict ontology system for tagging measurements.
Every measurement must be tagged with these values to enable comparability analysis.

See ADR-0002 for the full rationale behind this design decision.
"""

from enum import StrEnum


class MetricFamily(StrEnum):
    """What is being measured?"""

    TIME_TO_PROVIDER = "TIME_TO_PROVIDER"
    """Wait time until seeing a healthcare provider."""

    TOTAL_LOS = "TOTAL_LOS"
    """Total length of stay in the emergency department."""

    STRETCHER_OCCUPANCY = "STRETCHER_OCCUPANCY"
    """Current occupancy rate of ED stretchers."""


class StartEvent(StrEnum):
    """When does the clock start?"""

    TRIAGE = "TRIAGE"
    """After initial triage assessment (most strict)."""

    REGISTRATION = "REGISTRATION"
    """After administrative check-in."""

    DOOR = "DOOR"
    """Upon physical arrival at ED entrance."""

    UNKNOWN = "UNKNOWN"
    """Source doesn't specify start point."""


class EndEvent(StrEnum):
    """When does the clock stop?"""

    PHYSICIAN = "PHYSICIAN"
    """Initial physician assessment."""

    PROVIDER = "PROVIDER"
    """Any provider contact (doctor, NP, PA)."""

    DISCHARGE = "DISCHARGE"
    """Patient leaves the ED."""

    FIRST_ASSESSMENT = "FIRST_ASSESSMENT"
    """First clinical contact of any kind."""


class StatisticType(StrEnum):
    """How is the value calculated?"""

    P90 = "P90"
    """90th percentile (CIHI standard)."""

    MEDIAN = "MEDIAN"
    """50th percentile."""

    MEAN = "MEAN"
    """Simple average."""

    ROLLING_AVG = "ROLLING_AVG"
    """Moving average (window unspecified)."""

    ALGORITHMIC = "ALGORITHMIC"
    """Proprietary calculation method."""

    POINT_ESTIMATE = "POINT_ESTIMATE"
    """Current real-time value."""


class PatientScope(StrEnum):
    """Which patients are included in the metric?"""

    ALL = "ALL"
    """All ED patients."""

    MID_ACUITY = "MID_ACUITY"
    """CTAS 3-4 patients (mid-acuity)."""

    NON_PRIORITY = "NON_PRIORITY"
    """Non-urgent patients only."""

    HIGH_ACUITY = "HIGH_ACUITY"
    """CTAS 1-2 patients (high-acuity)."""
