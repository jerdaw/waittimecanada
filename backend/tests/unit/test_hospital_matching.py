"""Unit tests for the shared hospital-name matching helpers."""

import pytest

from waittime.scrapers.hospital_matching import (
    find_colliding_ids,
    is_aggregate_name,
    match_source_name,
    normalize_source_name,
)

MAPPING = {
    "Hamilton Health Sciences": "ca-on-hamilton-health",
    "Children's Hospital of Eastern Ontario": "ca-on-cheo",
    "CHEO": "ca-on-cheo",
    "Sunnybrook Health Sciences Centre": "ca-on-sunnybrook",
}


@pytest.mark.unit
class TestMatchSourceName:
    def test_exact_match(self):
        outcome = match_source_name("Sunnybrook Health Sciences Centre", MAPPING)
        assert (outcome.status, outcome.hospital_id) == ("exact", "ca-on-sunnybrook")

    def test_exact_match_normalizes_case_space_and_apostrophe(self):
        outcome = match_source_name("children’s  hospital OF eastern ontario ", MAPPING)
        assert (outcome.status, outcome.hospital_id) == ("exact", "ca-on-cheo")

    def test_campus_of_mapped_corporation_is_ambiguous(self):
        outcome = match_source_name("Hamilton Health Sciences Corp-Juravinski", MAPPING)
        assert outcome.status == "ambiguous"
        assert outcome.hospital_id is None
        assert outcome.candidates == ("ca-on-hamilton-health",)

    def test_name_contained_in_mapped_key_is_ambiguous(self):
        assert match_source_name("Eastern Ontario", MAPPING).status == "ambiguous"

    def test_unrelated_name_is_unmapped(self):
        assert match_source_name("Espanola General Hospital", MAPPING).status == "unmapped"

    def test_empty_name_is_unmapped(self):
        assert match_source_name("   ", MAPPING).status == "unmapped"

    def test_alias_keys_with_conflicting_ids_are_ambiguous(self):
        mapping = {"Foo": "a", "foo": "b"}
        assert match_source_name("FOO", mapping).status == "ambiguous"


@pytest.mark.unit
class TestAggregateNames:
    @pytest.mark.parametrize(
        "name", ["Ontario", "ONTARIO", "Québec", "Quebec", "Provincial average", "Moyenne"]
    )
    def test_aggregates(self, name):
        assert is_aggregate_name(name)
        assert match_source_name(name, MAPPING).status == "aggregate"

    @pytest.mark.parametrize("name", ["Ontario Shores Centre", "Hôpital de Québec", "CHEO"])
    def test_facilities_are_not_aggregates(self, name):
        assert not is_aggregate_name(name)


@pytest.mark.unit
def test_normalize_source_name_preserves_accents():
    assert normalize_source_name(" Hôpital  Notre–Dame ") == "hôpital notre-dame"


@pytest.mark.unit
def test_find_colliding_ids():
    rows = [("A", "x"), ("B", "y"), ("C", "x")]
    assert find_colliding_ids(rows) == {"x": ["A", "C"]}
    assert find_colliding_ids([("A", "x"), ("B", "y")]) == {}
