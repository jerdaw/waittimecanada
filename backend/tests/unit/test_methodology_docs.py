"""Tests for methodology documentation validation."""

import json
import pytest
from pathlib import Path


class TestOntarioMethodologyJSON:
    """Validate Ontario methodology reference JSON structure."""

    @pytest.fixture
    def ontario_json(self):
        """Load Ontario methodology JSON."""
        json_path = (
            Path(__file__).parents[2]
            / "docs"
            / "methodologies"
            / "ontario-reference.json"
        )
        with open(json_path) as f:
            return json.load(f)

    def test_has_required_top_level_fields(self, ontario_json):
        """Should have all required top-level fields."""
        required_fields = [
            "province",
            "province_code",
            "sources",
            "telehealth",
            "triage_system",
            "comparability",
            "references",
        ]

        for field in required_fields:
            assert field in ontario_json, f"Missing required field: {field}"

    def test_province_info_correct(self, ontario_json):
        """Should have correct province information."""
        assert ontario_json["province"] == "Ontario"
        assert ontario_json["province_code"] == "ON"
        assert "last_updated" in ontario_json

    def test_has_two_data_sources(self, ontario_json):
        """Should document both ER Watch and HQO sources."""
        sources = ontario_json["sources"]
        assert len(sources) == 2

        source_ids = {s["id"] for s in sources}
        assert "on-erwatch" in source_ids
        assert "on-hqo" in source_ids

    def test_source_has_methodology(self, ontario_json):
        """Each source should have complete methodology specification."""
        for source in ontario_json["sources"]:
            methodology = source["methodology"]

            assert "metric_family" in methodology
            assert "start_event" in methodology
            assert "end_event" in methodology
            assert "statistic_type" in methodology
            assert "patient_scope" in methodology

    def test_erwatch_is_point_estimate(self, ontario_json):
        """ER Watch should use POINT_ESTIMATE statistic type."""
        erwatch = next(s for s in ontario_json["sources"] if s["id"] == "on-erwatch")

        assert erwatch["methodology"]["statistic_type"] == "POINT_ESTIMATE"
        assert erwatch["type"] == "real-time"

    def test_hqo_is_p90(self, ontario_json):
        """HQO should use P90 statistic type."""
        hqo = next(s for s in ontario_json["sources"] if s["id"] == "on-hqo")

        assert hqo["methodology"]["statistic_type"] == "P90"
        assert hqo["type"] == "historical"

    def test_both_use_time_to_provider(self, ontario_json):
        """Both sources should use TIME_TO_PROVIDER metric."""
        for source in ontario_json["sources"]:
            assert source["methodology"]["metric_family"] == "TIME_TO_PROVIDER"
            assert source["methodology"]["start_event"] == "TRIAGE"
            assert source["methodology"]["end_event"] == "PHYSICIAN"

    def test_telehealth_has_811(self, ontario_json):
        """Should document Health Connect Ontario (811)."""
        telehealth = ontario_json["telehealth"]

        assert telehealth["phone"] == "811"
        assert "Health Connect Ontario" in telehealth["name"]
        assert "url" in telehealth

    def test_triage_system_has_five_levels(self, ontario_json):
        """CTAS should have 5 triage levels."""
        triage = ontario_json["triage_system"]

        assert triage["name"] == "Canadian Triage and Acuity Scale (CTAS)"
        assert len(triage["levels"]) == 5

        # Verify levels 1-5 exist
        levels = {level["level"] for level in triage["levels"]}
        assert levels == {1, 2, 3, 4, 5}

    def test_comparability_documented(self, ontario_json):
        """Should document comparability scenarios."""
        comparability = ontario_json["comparability"]

        assert "within_province" in comparability
        assert "cross_province_examples" in comparability

        # Should document ER Watch vs HQO incompatibility
        within = comparability["within_province"]
        assert "er_watch_vs_hqo" in within
        assert within["er_watch_vs_hqo"]["compatible"] is False

    def test_has_validation_checklist(self, ontario_json):
        """Should have validation checklist for measurements."""
        checklist = ontario_json["validation_checklist"]

        assert len(checklist) > 0
        assert any("hospital" in item.lower() for item in checklist)
        assert any("ontology" in item.lower() or "metric" in item.lower() for item in checklist)

    def test_has_references(self, ontario_json):
        """Should have reference URLs."""
        references = ontario_json["references"]

        assert len(references) >= 3

        # Should have at least one official government reference
        assert any(ref["type"] == "official" for ref in references)

        # All references should have URLs
        for ref in references:
            assert "url" in ref
            assert "title" in ref
            assert ref["url"].startswith("http")

    def test_json_structure_is_valid(self, ontario_json):
        """JSON should be parseable and well-formed."""
        # If we got here, JSON is valid (loaded successfully in fixture)
        assert isinstance(ontario_json, dict)

        # Test that it can be serialized back to JSON
        json_str = json.dumps(ontario_json, indent=2)
        assert len(json_str) > 0
        assert json.loads(json_str) == ontario_json


class TestMethodologyDocumentationExists:
    """Verify methodology documentation files exist."""

    def test_ontario_markdown_exists(self):
        """Ontario methodology markdown should exist."""
        doc_path = (
            Path(__file__).parents[2]
            / "docs"
            / "methodologies"
            / "ontario-methodology.md"
        )
        assert doc_path.exists(), "Ontario methodology.md not found"

    def test_methodologies_readme_exists(self):
        """Methodologies README should exist."""
        readme_path = (
            Path(__file__).parents[2] / "docs" / "methodologies" / "README.md"
        )
        assert readme_path.exists(), "Methodologies README.md not found"

    def test_ontario_json_exists(self):
        """Ontario JSON reference should exist."""
        json_path = (
            Path(__file__).parents[2]
            / "docs"
            / "methodologies"
            / "ontario-reference.json"
        )
        assert json_path.exists(), "ontario-reference.json not found"
