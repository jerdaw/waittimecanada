"""Unit tests for core domain models."""


import pytest
from waittime.core import (
    EndEvent,
    Hospital,
    Measurement,
    MetricFamily,
    PatientScope,
    StartEvent,
    StatisticType,
    are_comparable,
    generate_divergence_brief,
)


@pytest.mark.unit
class TestMeasurement:
    """Tests for Measurement model validation."""

    def test_valid_measurement(self) -> None:
        """A measurement with valid ontology fields should be accepted."""
        m = Measurement(
            hospital_id="ca-qc-chum",
            value=120.0,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.REGISTRATION,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            source_id="quebec-msss",
            raw_payload_hash="a" * 64,
        )
        assert m.value == 120.0
        assert m.metric_family == MetricFamily.TIME_TO_PROVIDER

    def test_value_must_be_positive(self) -> None:
        """Measurement value must be greater than zero."""
        with pytest.raises(ValueError, match="greater than"):
            Measurement(
                hospital_id="ca-qc-chum",
                value=0,
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.REGISTRATION,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.MEAN,
                source_id="quebec-msss",
                raw_payload_hash="a" * 64,
            )

    def test_hash_must_be_64_chars(self) -> None:
        """Raw payload hash must be exactly 64 characters (SHA256)."""
        with pytest.raises(ValueError):
            Measurement(
                hospital_id="ca-qc-chum",
                value=120.0,
                metric_family=MetricFamily.TIME_TO_PROVIDER,
                start_event=StartEvent.REGISTRATION,
                end_event=EndEvent.PHYSICIAN,
                statistic_type=StatisticType.MEAN,
                source_id="quebec-msss",
                raw_payload_hash="tooshort",
            )

    def test_default_patient_scope_is_all(self) -> None:
        """Patient scope defaults to ALL if not specified."""
        m = Measurement(
            hospital_id="ca-qc-chum",
            value=120.0,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.REGISTRATION,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            source_id="quebec-msss",
            raw_payload_hash="a" * 64,
        )
        assert m.patient_scope == PatientScope.ALL


@pytest.mark.unit
class TestHospital:
    """Tests for Hospital model validation."""

    def test_hospital_cannot_be_visible_without_verification(self) -> None:
        """A hospital must be verified before it can be visible."""
        with pytest.raises(ValueError, match="verified"):
            Hospital(
                id="ca-qc-chum",
                name="CHUM",
                province="QC",
                city="Montreal",
                latitude=45.5088,
                longitude=-73.5878,
                is_verified=False,
                is_visible=True,  # This should fail
                source_id="quebec-msss",
            )

    def test_verified_hospital_can_be_visible(self) -> None:
        """A verified hospital can be made visible."""
        h = Hospital(
            id="ca-qc-chum",
            name="CHUM",
            province="QC",
            city="Montreal",
            latitude=45.5088,
            longitude=-73.5878,
            is_verified=True,
            is_visible=True,
            source_id="quebec-msss",
        )
        assert h.is_visible is True


@pytest.mark.unit
class TestComparability:
    """Tests for the comparability logic - core architectural feature."""

    @pytest.fixture
    def quebec_measurement(self) -> Measurement:
        """Quebec uses Registration-to-Physician with MEAN."""
        return Measurement(
            hospital_id="ca-qc-chum",
            value=120.0,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.REGISTRATION,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            source_id="quebec-msss",
            raw_payload_hash="a" * 64,
        )

    @pytest.fixture
    def alberta_measurement(self) -> Measurement:
        """Alberta uses Triage-to-Physician with P90."""
        return Measurement(
            hospital_id="ca-ab-foothills",
            value=90.0,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.TRIAGE,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.P90,
            source_id="alberta-ahs",
            raw_payload_hash="b" * 64,
        )

    @pytest.fixture
    def another_quebec_measurement(self) -> Measurement:
        """Another Quebec hospital with same methodology."""
        return Measurement(
            hospital_id="ca-qc-jewish",
            value=150.0,
            metric_family=MetricFamily.TIME_TO_PROVIDER,
            start_event=StartEvent.REGISTRATION,
            end_event=EndEvent.PHYSICIAN,
            statistic_type=StatisticType.MEAN,
            source_id="quebec-msss",
            raw_payload_hash="c" * 64,
        )

    def test_same_methodology_is_comparable(
        self, quebec_measurement: Measurement, another_quebec_measurement: Measurement
    ) -> None:
        """Two measurements with identical ontology should be comparable."""
        assert are_comparable(quebec_measurement, another_quebec_measurement) is True

    def test_different_start_event_not_comparable(
        self, quebec_measurement: Measurement, alberta_measurement: Measurement
    ) -> None:
        """Different start events make measurements incomparable."""
        assert are_comparable(quebec_measurement, alberta_measurement) is False

    def test_divergence_brief_returns_none_when_comparable(
        self, quebec_measurement: Measurement, another_quebec_measurement: Measurement
    ) -> None:
        """No divergence brief needed for comparable measurements."""
        brief = generate_divergence_brief(quebec_measurement, another_quebec_measurement)
        assert brief is None

    def test_divergence_brief_explains_differences(
        self, quebec_measurement: Measurement, alberta_measurement: Measurement
    ) -> None:
        """Divergence brief should explain methodology differences."""
        brief = generate_divergence_brief(quebec_measurement, alberta_measurement)

        assert brief is not None
        assert "Methodology Divergence" in brief
        assert "REGISTRATION" in brief
        assert "TRIAGE" in brief
        assert "MEAN" in brief
        assert "P90" in brief
