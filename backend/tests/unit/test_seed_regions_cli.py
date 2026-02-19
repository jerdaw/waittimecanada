"""Tests for region seeding CLI tool."""

import json
from pathlib import Path
from unittest.mock import Mock

import pytest
from waittime.cli.seed_regions import load_regions_from_json, seed_regions


@pytest.fixture
def sample_region_payload() -> dict[str, object]:
    """Sample region payload for testing."""
    return {
        "province": "ON",
        "regions": [
            {
                "id": "ca-on-region-east",
                "name": "East Health Region",
                "code": "EAST",
                "sort_order": 1,
                "description": "Eastern Ontario",
                "hospitals": ["h1", "h2"],
            },
            {
                "id": "ca-on-region-toronto",
                "name": "Toronto Health Region",
                "code": "TORONTO",
                "sort_order": 2,
                "hospitals": ["h3"],
            },
        ],
    }


def test_load_regions_from_json_success(
    tmp_path: Path, sample_region_payload: dict[str, object]
) -> None:
    """Load and normalize valid region payload."""
    json_file = tmp_path / "regions.json"
    json_file.write_text(json.dumps(sample_region_payload))

    payload = load_regions_from_json(json_file)

    assert payload["province"] == "ON"
    assert len(payload["regions"]) == 2
    assert payload["regions"][0]["code"] == "EAST"
    assert payload["regions"][0]["metadata"]["description"] == "Eastern Ontario"


def test_load_regions_from_json_with_override(
    tmp_path: Path, sample_region_payload: dict[str, object]
) -> None:
    """Province override should replace JSON province."""
    json_file = tmp_path / "regions.json"
    json_file.write_text(json.dumps(sample_region_payload))

    payload = load_regions_from_json(json_file, province_override="qc")

    assert payload["province"] == "QC"


def test_load_regions_from_json_missing_file() -> None:
    """Missing files should raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_regions_from_json(Path("does-not-exist.json"))


def test_load_regions_from_json_invalid_region(tmp_path: Path) -> None:
    """Missing required region fields should fail validation."""
    json_file = tmp_path / "regions.json"
    json_file.write_text(
        json.dumps(
            {
                "province": "ON",
                "regions": [
                    {
                        "id": "ca-on-region-east",
                        "name": "East",
                    }
                ],
            }
        )
    )

    with pytest.raises(ValueError, match="missing fields"):
        load_regions_from_json(json_file)


def test_seed_regions_dry_run() -> None:
    """Dry run should not call write operations."""
    mock_db = Mock()

    regions = [
        {
            "id": "ca-on-region-east",
            "name": "East",
            "code": "EAST",
            "sort_order": 1,
            "metadata": {"description": ""},
            "hospitals": ["h1", "h2"],
        }
    ]

    region_count, mapping_count, missing = seed_regions(
        db=mock_db,
        province="ON",
        regions=regions,
        dry_run=True,
    )

    assert region_count == 1
    assert mapping_count == 2
    assert missing == 0
    mock_db.clear_hospital_regions_for_province.assert_not_called()
    mock_db.upsert_region.assert_not_called()
    mock_db.upsert_hospital_region.assert_not_called()


def test_seed_regions_skips_unknown_hospitals() -> None:
    """Unknown hospitals should be counted and skipped."""
    mock_db = Mock()
    mock_db.get_hospital.side_effect = [None, object()]

    regions = [
        {
            "id": "ca-on-region-east",
            "name": "East",
            "code": "EAST",
            "sort_order": 1,
            "metadata": {"description": ""},
            "hospitals": ["missing", "h2"],
        }
    ]

    region_count, mapping_count, missing = seed_regions(
        db=mock_db,
        province="ON",
        regions=regions,
        dry_run=False,
    )

    assert region_count == 1
    assert mapping_count == 1
    assert missing == 1

    mock_db.clear_hospital_regions_for_province.assert_called_once_with("ON")
    mock_db.upsert_region.assert_called_once()
    mock_db.upsert_hospital_region.assert_called_once_with(
        region_id="ca-on-region-east",
        hospital_id="h2",
    )
