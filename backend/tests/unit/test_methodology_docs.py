"""Tests for methodology documentation validation."""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[3]
ONTARIO_HEALTH_URL = (
    "https://ontariohealth.ca/system/reporting/performance/time-spent-in-emergency-departments"
)
OFFICIAL_START_TEXT = "triage or registration, whichever is earlier"
OFFICIAL_END_TEXT = (
    "first assessment by a doctor, nurse practitioner, physician assistant, or dentist"
)
COMPARISON_SAFETY_TEXT = "Direct cross-province comparison remains invalid."


class TestOntarioMethodologyJSON:
    """Validate Ontario methodology reference JSON structure."""

    @pytest.fixture
    def ontario_json(self):
        """Load Ontario methodology JSON."""
        json_path = Path(__file__).parents[2] / "docs" / "methodologies" / "ontario-reference.json"
        with open(json_path) as f:
            return json.load(f)

    def test_has_required_top_level_fields(self, ontario_json):
        """Should have all required top-level fields."""
        required_fields = [
            "province",
            "province_code",
            "sources",
            "methodology_revalidation",
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

    def test_has_current_data_source(self, ontario_json):
        """Should document the maintained Ontario source."""
        sources = ontario_json["sources"]
        assert len(sources) == 1

        source_ids = {s["id"] for s in sources}
        assert "ontario-health" in source_ids
        assert sources[0]["update_frequency"] == "Monthly public reporting"

    def test_source_has_methodology(self, ontario_json):
        """Each source should have complete methodology specification."""
        for source in ontario_json["sources"]:
            methodology = source["methodology"]

            assert "metric_family" in methodology
            assert "start_event" in methodology
            assert "end_event" in methodology
            assert "statistic_type" in methodology
            assert "patient_scope" in methodology

    def test_current_repository_mapping_is_documented(self, ontario_json):
        """The structured reference should preserve current implementation tags."""
        ontario_source = next(s for s in ontario_json["sources"] if s["id"] == "ontario-health")

        assert ontario_source["methodology"]["statistic_type"] == "MEAN"
        assert ontario_source["methodology"]["start_event"] == "TRIAGE"
        assert ontario_source["methodology"]["end_event"] == "PHYSICIAN"
        assert ontario_source["type"] == "historical_reporting"

    def test_source_uses_current_repository_event_tags(self, ontario_json):
        """The maintained source should preserve current implementation tags."""
        for source in ontario_json["sources"]:
            assert source["methodology"]["metric_family"] == "TIME_TO_PROVIDER"
            assert source["methodology"]["start_event"] == "TRIAGE"
            assert source["methodology"]["end_event"] == "PHYSICIAN"

    def test_telehealth_has_811(self, ontario_json):
        """Should document Health811 (811)."""
        telehealth = ontario_json["telehealth"]

        assert telehealth["phone"] == "811"
        assert "Health811" in telehealth["name"]
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

        within = comparability["within_province"]
        assert "ontario_vs_ontario" in within
        assert within["ontario_vs_ontario"]["compatible"] is True

        cross = comparability["cross_province_examples"]
        assert cross["ontario_vs_alberta"]["compatible"] is False
        assert cross["ontario_vs_quebec"]["compatible"] is False

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

    def test_official_definition_is_distinct_from_repository_mapping(self, ontario_json):
        """The legacy tags must not be presented as the exact official definition."""
        revalidation = ontario_json["methodology_revalidation"]

        assert revalidation["status"] == "required"
        assert revalidation["official_source_url"] == ONTARIO_HEALTH_URL
        assert revalidation["official_indicator_definition"] == {
            "start": "triage or registration, whichever is earlier",
            "end": (
                "first assessment by a doctor, nurse practitioner, physician assistant, or dentist"
            ),
            "statistic_type": "MEAN",
        }
        assert revalidation["repository_mapping"] == {
            "start_event": "TRIAGE",
            "end_event": "PHYSICIAN",
            "status": "LEGACY_IMPLEMENTATION_TAGS_PENDING_REVALIDATION",
        }
        assert "historical" in revalidation["resolution_required"].lower()

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
        doc_path = Path(__file__).parents[2] / "docs" / "methodologies" / "ontario-methodology.md"
        assert doc_path.exists(), "Ontario methodology.md not found"

    def test_methodologies_readme_exists(self):
        """Methodologies README should exist."""
        readme_path = Path(__file__).parents[2] / "docs" / "methodologies" / "README.md"
        assert readme_path.exists(), "Methodologies README.md not found"

    def test_ontario_json_exists(self):
        """Ontario JSON reference should exist."""
        json_path = Path(__file__).parents[2] / "docs" / "methodologies" / "ontario-reference.json"
        assert json_path.exists(), "ontario-reference.json not found"

    @pytest.mark.parametrize(
        "relative_path",
        [
            "backend/docs/methodologies/ontario-methodology.md",
            "docs/ontario-methodology.md",
            "docs/ontario-research-findings.md",
            "docs/case-studies/ottawa-gatineau-divergence.md",
            "docs/research/methodological-heterogeneity-four-province-audit-draft.md",
        ],
    )
    def test_ontario_revalidation_notice_is_visible(self, relative_path):
        """Affected public artifacts must expose the unresolved fidelity gap."""
        contents = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        normalized = " ".join(contents.replace(">", " ").split())

        assert "Ontario methodology revalidation required" in contents
        assert ONTARIO_HEALTH_URL in contents
        assert OFFICIAL_START_TEXT in normalized
        assert OFFICIAL_END_TEXT in normalized
        assert "`TRIAGE -> PHYSICIAN`" in contents

    @pytest.mark.parametrize(
        "relative_path",
        [
            "backend/docs/methodologies/ontario-methodology.md",
            "docs/ontario-methodology.md",
            "docs/case-studies/ottawa-gatineau-divergence.md",
            "docs/research/methodological-heterogeneity-four-province-audit-draft.md",
        ],
    )
    def test_comparative_artifacts_preserve_non_comparability(self, relative_path):
        """Comparative artifacts must retain the safe direct-comparison boundary."""
        contents = (REPO_ROOT / relative_path).read_text(encoding="utf-8")

        assert COMPARISON_SAFETY_TEXT in contents
