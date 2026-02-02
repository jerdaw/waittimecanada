"""Core domain models with Pydantic validation.

These models enforce the metric ontology at the application layer,
complementing the database-level constraints.
"""

from datetime import UTC, datetime
from typing import Self

from pydantic import BaseModel, Field, model_validator

from waittime.core.enums import (
    EndEvent,
    MetricFamily,
    PatientScope,
    StartEvent,
    StatisticType,
)


class Measurement(BaseModel):
    """A single wait time measurement with full ontology tagging.

    This is the core data structure. Every measurement must declare
    its methodology via the ontology fields to enable comparability analysis.
    """

    hospital_id: str = Field(
        description="Unique hospital identifier (format: ca-{province}-{slug})"
    )
    value: float = Field(gt=0, description="The measured value (usually minutes)")
    timestamp_utc: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="When this measurement was recorded",
    )

    # Ontology fields - required for comparability analysis
    metric_family: MetricFamily
    start_event: StartEvent
    end_event: EndEvent
    statistic_type: StatisticType
    patient_scope: PatientScope = PatientScope.ALL

    # Provenance tracking
    source_id: str = Field(description="Foreign key to sources table")
    raw_payload_hash: str = Field(
        min_length=64,
        max_length=64,
        description="SHA256 hash of the raw HTML payload",
    )
    raw_payload_snippet: str | None = Field(
        default=None,
        max_length=200,
        description="First 200 chars of payload for debugging",
    )
    parser_version: str = Field(
        default="v1.0",
        description="Version of the parser that created this measurement",
    )


class Hospital(BaseModel):
    """A healthcare facility that reports wait times."""

    id: str = Field(description="Unique identifier (format: ca-{province}-{slug})")
    name: str = Field(min_length=1, max_length=255)
    province: str = Field(min_length=2, max_length=2, description="Two-letter code")
    city: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    # Verification workflow - never auto-publish
    is_verified: bool = Field(
        default=False,
        description="Has been manually verified by admin",
    )
    is_visible: bool = Field(
        default=False,
        description="Visible on the public site",
    )

    source_id: str = Field(description="Data source this hospital belongs to")

    @model_validator(mode="after")
    def verify_before_visible(self) -> Self:
        """Ensure hospital is verified before being made visible."""
        if self.is_visible and not self.is_verified:
            raise ValueError("Hospital must be verified before being made visible")
        return self


class Source(BaseModel):
    """A provincial data source with provenance information."""

    id: str = Field(description="Unique identifier (e.g., 'quebec-msss')")
    name: str = Field(description="Display name")
    province: str = Field(min_length=2, max_length=2)
    url: str = Field(description="Official data portal URL")
    methodology_url: str | None = Field(
        default=None,
        description="Link to methodology documentation",
    )

    # Telehealth routing info
    telehealth_name: str = Field(description="e.g., 'Health Link 811'")
    telehealth_number: str = Field(description="e.g., '811'")

    # Default ontology for this source (scrapers can override)
    default_metric_family: MetricFamily
    default_start_event: StartEvent
    default_end_event: EndEvent
    default_statistic_type: StatisticType


class ScraperStatus(BaseModel):
    """Heartbeat record for monitoring scraper health."""

    source_id: str
    last_run: datetime
    status: str = Field(pattern="^(healthy|error|stale)$")
    error_message: str | None = None
    measurements_count: int = Field(ge=0, default=0)


def are_comparable(a: Measurement, b: Measurement) -> bool:
    """Determine if two measurements can be directly compared.

    Two measurements are comparable if and only if they use the same
    methodology across all ontology dimensions.

    See ADR-0002 for the full rationale.
    """
    return (
        a.metric_family == b.metric_family
        and a.start_event == b.start_event
        and a.end_event == b.end_event
        and a.statistic_type == b.statistic_type
    )


def generate_divergence_brief(a: Measurement, b: Measurement) -> str | None:
    """Generate a human-readable explanation of why two measurements differ.

    Returns None if the measurements are comparable.
    """
    if are_comparable(a, b):
        return None

    differences: list[str] = []

    if a.metric_family != b.metric_family:
        differences.append(f"Different metrics: {a.metric_family.value} vs {b.metric_family.value}")

    if a.start_event != b.start_event:
        differences.append(
            f"Different start points: {a.start_event.value} vs {b.start_event.value}"
        )

    if a.end_event != b.end_event:
        differences.append(f"Different end points: {a.end_event.value} vs {b.end_event.value}")

    if a.statistic_type != b.statistic_type:
        differences.append(
            f"Different statistics: {a.statistic_type.value} vs {b.statistic_type.value}"
        )

    return (
        "Methodology Divergence: Direct comparison is scientifically invalid. "
        + "; ".join(differences)
        + "."
    )
