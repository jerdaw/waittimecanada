from hypothesis import given
from hypothesis import strategies as st
from waittime.core import Measurement, are_comparable, generate_divergence_brief
from waittime.core.enums import EndEvent, MetricFamily, PatientScope, StartEvent, StatisticType

# Strategy to generate valid Measurement objects
measurement_strategy = st.builds(
    Measurement,
    hospital_id=st.just("ca-qc-test"),
    value=st.floats(min_value=0.1, max_value=1000.0),
    metric_family=st.sampled_from(MetricFamily),
    start_event=st.sampled_from(StartEvent),
    end_event=st.sampled_from(EndEvent),
    statistic_type=st.sampled_from(StatisticType),
    patient_scope=st.sampled_from(PatientScope),
    source_id=st.just("test-source"),
    raw_payload_hash=st.just("0" * 64),
    parser_version=st.just("v1.0"),
)


@given(measurement_strategy)
def test_comparability_reflexivity(m: Measurement) -> None:
    """Reflexivity: A measurement is always comparable to itself."""
    assert are_comparable(m, m)
    assert generate_divergence_brief(m, m) is None


@given(measurement_strategy, measurement_strategy)
def test_comparability_symmetry(a: Measurement, b: Measurement) -> None:
    """Symmetry: If a is comparable to b, b is comparable to a."""
    assert are_comparable(a, b) == are_comparable(b, a)


@given(measurement_strategy, measurement_strategy)
def test_divergence_brief_consistency(a: Measurement, b: Measurement) -> None:
    """Consistency: Divergence brief is generated ONLY when not comparable."""
    is_comparable = are_comparable(a, b)
    brief = generate_divergence_brief(a, b)

    if is_comparable:
        assert brief is None
    else:
        assert brief is not None
        assert "Direct comparison is scientifically invalid" in brief


@given(measurement_strategy, measurement_strategy, measurement_strategy)
def test_comparability_transitivity(a: Measurement, b: Measurement, c: Measurement) -> None:
    """Transitivity: If a ~ b and b ~ c, then a ~ c."""
    if are_comparable(a, b) and are_comparable(b, c):
        assert are_comparable(a, c)
