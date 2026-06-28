"""Core domain models with Pydantic validation.

These models enforce the metric ontology at the application layer,
complementing the database-level constraints.
"""

from datetime import UTC, date, datetime
from typing import ClassVar, Literal, Self

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
    value: float = Field(ge=0, description="The measured value (usually minutes)")
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

    # Occupancy Metrics (Optional)
    patients_waiting: int | None = Field(
        default=None, ge=0, description="Number of patients waiting"
    )
    patients_in_treatment: int | None = Field(
        default=None, ge=0, description="Number of patients in treatment"
    )
    total_treatment_spaces: int | None = Field(default=None, ge=0, description="Total ER capacity")

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

    # Anomaly detection metadata (flagged but never excluded)
    is_anomaly: bool = Field(
        default=False,
        description="Whether this measurement was flagged as anomalous",
    )
    anomaly_reason: str | None = Field(
        default=None,
        description="Human-readable explanation if flagged as anomaly",
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


class PublicDataSource(BaseModel):
    """Metadata contract and sync state for public-health-hub sources."""

    source_id: str = Field(description="Stable internal source identifier")
    domain: Literal[
        "provider_facility",
        "aed",
        "safety_alert",
        "health_product_reference",
        "environmental_overlay",
        "system_context",
    ]
    source_name: str = Field(min_length=1, max_length=255)
    scope: Literal["canada", "ontario", "regional", "municipal", "institution"]
    jurisdiction_level: Literal[
        "federal",
        "provincial",
        "municipal",
        "regional",
        "institution",
        "nonprofit_other",
    ]
    connector_type: Literal[
        "api",
        "feed",
        "open_data_portal",
        "file_download",
        "dashboard_only",
        "request_based",
        "partner_only",
        "crowdsourced_registry",
    ]
    access_route: str = Field(min_length=1)
    license_reuse_status: Literal[
        "approved",
        "approved_with_conditions",
        "blocked",
    ]
    attribution_requirement: str = Field(min_length=1)
    update_cadence: str = Field(min_length=1)
    freshness_sensitivity: Literal["low", "medium", "high"]
    operational_risk: Literal["low", "medium", "high"]
    recommended_usage_mode: Literal[
        "live_ui",
        "scheduled_ingest",
        "analytics_only",
        "research_only",
        "do_not_use",
    ]
    provenance_url: str = Field(min_length=1)
    last_verified_at: date
    notes: str | None = None
    fallback_source_id: str | None = None
    public_methodology_note: str | None = None
    last_refreshed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ResourceLocation(BaseModel):
    """Normalized public-health resource location stored in the hub tables."""

    id: str
    source_id: str
    kind: Literal["facility", "aed"]
    source_record_id: str | None = None
    name: str = Field(min_length=1, max_length=255)
    province: str = Field(min_length=2, max_length=2)
    city: str | None = None
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    address: str | None = None
    postal_code: str | None = None
    phone: str | None = None
    website_url: str | None = None
    reference_status: Literal["directory_only"] | None = None
    location_description: str | None = None
    access_notes: str | None = None
    crowdsourced: bool = False
    completeness_status: Literal["incomplete"] | None = None
    provenance_url: str
    last_refreshed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PublicHealthAlert(BaseModel):
    """Normalized public health alert stored for the hub module."""

    id: str
    source_id: str
    title: str = Field(min_length=1, max_length=500)
    summary: str = Field(min_length=1)
    alert_type: str = Field(min_length=1, max_length=100)
    published_at: datetime
    source_updated_at: datetime | None = None
    affected_products: list[dict[str, str | None]] = Field(default_factory=list)
    provenance_url: str
    last_refreshed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PublicHealthSystemMetric(BaseModel):
    """Normalized public health system-context metric stored for the hub module."""

    id: str
    source_id: str
    series_key: str = Field(min_length=1, max_length=100)
    province: str = Field(min_length=2, max_length=2)
    geography_type: str = Field(min_length=1, max_length=100)
    geography_name: str = Field(min_length=1, max_length=255)
    reporting_year: int = Field(ge=1900, le=3000)
    dimension_label: str | None = None
    metrics: dict[str, float | int | str | None]
    provenance_url: str
    last_refreshed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class MeasurementAggregate(BaseModel):
    """Aggregated statistics for a hospital over a time period.

    Permanent summaries that keep longitudinal research and long-range trend
    analysis efficient even when raw measurements are preserved indefinitely.

    Ontology tags are denormalized intentionally: if a source changes
    methodology, historical aggregates preserve what the methodology
    was at the time of aggregation.
    """

    VALID_PERIOD_TYPES: ClassVar[set[str]] = {"hourly", "daily", "weekly", "monthly"}

    hospital_id: str = Field(description="Hospital this aggregate covers")
    source_id: str = Field(description="Data source at time of aggregation")

    # Time period
    period_type: str = Field(description="Granularity: hourly, daily, weekly, or monthly")
    period_start: datetime = Field(description="Start of the aggregation window")
    period_end: datetime = Field(description="End of the aggregation window")

    # Summary statistics
    mean_value: float = Field(description="Mean wait time in minutes")
    median_value: float | None = Field(
        default=None,
        description="Median wait time (None if < 3 samples)",
    )
    p90_value: float | None = Field(
        default=None,
        description="90th percentile wait time (None if < 3 samples)",
    )
    min_value: float = Field(description="Minimum observed wait time")
    max_value: float = Field(description="Maximum observed wait time")
    std_dev: float | None = Field(
        default=None,
        description="Standard deviation (None if < 3 samples)",
    )
    sample_count: int = Field(gt=0, description="Number of raw measurements aggregated")

    # Ontology snapshot (denormalized from source at aggregation time)
    metric_family: str = Field(description="Metric family at time of aggregation")
    start_event: str = Field(description="Start event at time of aggregation")
    end_event: str = Field(description="End event at time of aggregation")
    statistic_type: str = Field(description="Statistic type at time of aggregation")

    created_at: datetime | None = None

    @model_validator(mode="after")
    def validate_period(self) -> Self:
        """Ensure period_type is valid and period_end is after period_start."""
        if self.period_type not in self.VALID_PERIOD_TYPES:
            raise ValueError(
                f"period_type must be one of {self.VALID_PERIOD_TYPES}, got '{self.period_type}'"
            )
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start")
        return self


class ScraperStatus(BaseModel):
    """Heartbeat record for monitoring scraper health."""

    source_id: str
    last_run: datetime
    status: str = Field(pattern="^(healthy|error|stale)$")
    error_message: str | None = None
    measurements_count: int = Field(ge=0, default=0)
    last_success_run: datetime | None = None
    last_success_measurements_count: int | None = Field(default=None, ge=0)
    last_error_run: datetime | None = None
    last_error_category: str | None = Field(
        default=None,
        pattern="^(upstream_unavailable|parser_breakage|infra_runtime|persistence_failure|unknown)$",
    )
    last_error_stage: str | None = Field(
        default=None,
        pattern="^(fetch|parse|before_save|persist|heartbeat|orchestration)$",
    )
    consecutive_failures: int = Field(ge=0, default=0)
    last_run_duration_ms: int | None = Field(default=None, ge=0)


class ScraperAlertState(BaseModel):
    """Persistent alert state for scraper incident deduplication."""

    source_id: str
    active_incident_kind: str | None = Field(default=None, pattern="^(stale|error)$")
    active_incident_fingerprint: str | None = None
    opened_at: datetime | None = None
    last_notified_at: datetime | None = None
    active_incident_notified_tier: str | None = Field(default=None, pattern="^P[0-3]$")
    active_incident_notified_at: datetime | None = None
    last_resolved_at: datetime | None = None
    updated_at: datetime | None = None


class PublicHealthSourceAlertState(BaseModel):
    """Persistent alert state for public-health ingest incident deduplication."""

    source_id: str
    active_incident_kind: str | None = Field(default=None, pattern="^(degraded)$")
    active_incident_fingerprint: str | None = None
    opened_at: datetime | None = None
    last_notified_at: datetime | None = None
    active_incident_notified_tier: str | None = Field(default=None, pattern="^P[0-3]$")
    active_incident_notified_at: datetime | None = None
    last_resolved_at: datetime | None = None
    updated_at: datetime | None = None


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
