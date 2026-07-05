"""Tests for Source Consistency (P0).

Ensures that the canonical JSON seed files match the hardcoded values in scraper factories.
This prevents drift between the database source of truth and the scraper code.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from waittime.core import Source
from waittime.scrapers import (
    create_alberta_source,
    create_bc_source,
    create_ontario_source,
    create_quebec_source,
)

# Factories to test
FACTORIES = {
    "ontario-health": create_ontario_source,
    "quebec-msss": create_quebec_source,
    "alberta-ahs": create_alberta_source,
    "bc-phsa": create_bc_source,
}

# Path to JSON source files
SOURCES_DIR = Path(__file__).parents[2] / "data" / "sources"


def load_source_json(source_id: str) -> dict[str, Any]:
    """Load the JSON definition for a source."""
    file_path = SOURCES_DIR / f"{source_id}.json"
    if not file_path.exists():
        pytest.fail(f"Missing seed file for {source_id}: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.unit
class TestSourceConsistency:
    """Verify JSON seeds match Python factories."""

    @pytest.mark.parametrize("source_id, factory_func", FACTORIES.items())
    def test_json_matches_factory(self, source_id, factory_func):
        """JSON definition must exactly match the factory output."""
        # 1. Load JSON
        json_data = load_source_json(source_id)
        json_source = Source(**json_data)

        # 2. Create from factory
        code_source = factory_func()

        # 3. Assert relevant fields match
        # We compare field by field for better error messages

        errors = []

        # ID
        if json_source.id != code_source.id:
            errors.append(f"ID mismatch: JSON={json_source.id}, Code={code_source.id}")

        # Name
        if json_source.name != code_source.name:
            errors.append(f"Name mismatch: JSON='{json_source.name}', Code='{code_source.name}'")

        # Province
        if json_source.province != code_source.province:
            errors.append(
                f"Province mismatch: JSON={json_source.province}, Code={code_source.province}"
            )

        # URL (normalized by stripping trailing slash)
        json_url = (json_source.url or "").rstrip("/")
        code_url = (code_source.url or "").rstrip("/")
        if json_url != code_url:
            errors.append(f"URL mismatch: JSON={json_url}, Code={code_url}")

        # Methodology URL
        json_meth = (json_source.methodology_url or "").rstrip("/")
        code_meth = (code_source.methodology_url or "").rstrip("/")
        if json_meth != code_meth:
            errors.append(f"Methodology URL mismatch: JSON={json_meth}, Code={code_meth}")

        # Telehealth
        if json_source.telehealth_number != code_source.telehealth_number:
            errors.append(
                f"Telehealth Number mismatch: JSON={json_source.telehealth_number}, Code={code_source.telehealth_number}"
            )

        if json_source.telehealth_name != code_source.telehealth_name:
            errors.append(
                f"Telehealth Name mismatch: JSON='{json_source.telehealth_name}', Code='{code_source.telehealth_name}'"
            )

        # Ontology
        ontology_fields = [
            "default_metric_family",
            "default_start_event",
            "default_end_event",
            "default_statistic_type",
        ]

        for field in ontology_fields:
            json_val = getattr(json_source, field)
            code_val = getattr(code_source, field)
            # Source model validation converts ontology fields to comparable enum values.
            if json_val != code_val:
                errors.append(f"{field} mismatch: JSON={json_val}, Code={code_val}")

        if errors:
            pytest.fail("\n".join(errors))
