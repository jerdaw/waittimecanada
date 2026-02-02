"""Tests for hospital seeding CLI tool."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from waittime.cli.seed import (
    load_hospitals_from_json,
    seed_hospitals,
)
from waittime.core import Hospital


@pytest.fixture
def sample_hospital_data():
    """Sample hospital data for testing."""
    return {
        "source_id": "test-source",
        "hospitals": [
            {
                "id": "ca-on-test-hospital",
                "name": "Test Hospital",
                "province": "ON",
                "city": "TestCity",
                "latitude": 45.0,
                "longitude": -75.0,
                "source_id": "test-source",
                "is_verified": True,
                "is_visible": True,
            },
            {
                "id": "ca-on-another-hospital",
                "name": "Another Hospital",
                "province": "ON",
                "city": "TestCity",
                "latitude": 45.1,
                "longitude": -75.1,
                "source_id": "test-source",
                "is_verified": False,
                "is_visible": False,
            },
        ],
    }


def test_load_hospitals_from_json_success(tmp_path, sample_hospital_data):
    """Test loading hospitals from valid JSON file."""
    # Create temp JSON file
    json_file = tmp_path / "test_hospitals.json"
    json_file.write_text(json.dumps(sample_hospital_data))

    # Load hospitals
    hospitals = load_hospitals_from_json(json_file, None)

    assert len(hospitals) == 2
    assert all(isinstance(h, Hospital) for h in hospitals)
    assert hospitals[0].name == "Test Hospital"
    assert hospitals[1].name == "Another Hospital"


def test_load_hospitals_from_json_with_source_override(tmp_path, sample_hospital_data):
    """Test loading hospitals with source ID override."""
    json_file = tmp_path / "test_hospitals.json"
    json_file.write_text(json.dumps(sample_hospital_data))

    hospitals = load_hospitals_from_json(json_file, "override-source")

    assert all(h.source_id == "override-source" for h in hospitals)


def test_load_hospitals_from_json_missing_file():
    """Test loading from non-existent file."""
    with pytest.raises(FileNotFoundError):
        load_hospitals_from_json(Path("nonexistent.json"), "test-source")


def test_load_hospitals_from_json_no_source_id(tmp_path):
    """Test loading when source_id is missing."""
    data = {"hospitals": []}
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="source_id must be provided"):
        load_hospitals_from_json(json_file, None)


def test_load_hospitals_from_json_invalid_hospital(tmp_path):
    """Test loading with invalid hospital data."""
    data = {
        "source_id": "test-source",
        "hospitals": [
            {
                "id": "test",
                "name": "Test",
                # Missing required fields
            }
        ],
    }
    json_file = tmp_path / "test.json"
    json_file.write_text(json.dumps(data))

    with pytest.raises(ValueError, match="validation failed"):
        load_hospitals_from_json(json_file, None)


def test_seed_hospitals_dry_run():
    """Test seeding in dry run mode."""
    mock_db = Mock()
    hospitals = [
        Hospital(
            id="test",
            name="Test",
            province="ON",
            city="City",
            latitude=45.0,
            longitude=-75.0,
            source_id="test",
        )
    ]

    inserted, skipped = seed_hospitals(mock_db, hospitals, dry_run=True)

    assert inserted == 1
    assert skipped == 0
    mock_db.get_hospital.assert_not_called()
    mock_db.insert_hospital.assert_not_called()


def test_seed_hospitals_new_hospital():
    """Test seeding a new hospital."""
    mock_db = Mock()
    mock_db.get_hospital.return_value = None

    hospital = Hospital(
        id="test",
        name="Test",
        province="ON",
        city="City",
        latitude=45.0,
        longitude=-75.0,
        source_id="test",
    )

    inserted, skipped = seed_hospitals(mock_db, [hospital], dry_run=False)

    assert inserted == 1
    assert skipped == 0
    mock_db.get_hospital.assert_called_once_with("test")
    mock_db.insert_hospital.assert_called_once_with(hospital)


def test_seed_hospitals_existing_hospital():
    """Test seeding when hospital already exists."""
    mock_db = Mock()
    mock_db.get_hospital.return_value = Hospital(
        id="test",
        name="Existing",
        province="ON",
        city="City",
        latitude=45.0,
        longitude=-75.0,
        source_id="test",
    )

    hospital = Hospital(
        id="test",
        name="Test",
        province="ON",
        city="City",
        latitude=45.0,
        longitude=-75.0,
        source_id="test",
    )

    inserted, skipped = seed_hospitals(mock_db, [hospital], dry_run=False)

    assert inserted == 0
    assert skipped == 1
    mock_db.insert_hospital.assert_not_called()


def test_seed_hospitals_multiple():
    """Test seeding multiple hospitals."""
    mock_db = Mock()
    existing_hospital = Hospital(
        id="h2",
        name="Existing H2",
        province="ON",
        city="C",
        latitude=45.0,
        longitude=-75.0,
        source_id="s",
    )
    mock_db.get_hospital.side_effect = [None, existing_hospital, None]

    hospitals = [
        Hospital(id="h1", name="H1", province="ON", city="C", latitude=45.0, longitude=-75.0, source_id="s"),
        Hospital(id="h2", name="H2", province="ON", city="C", latitude=45.0, longitude=-75.0, source_id="s"),
        Hospital(id="h3", name="H3", province="ON", city="C", latitude=45.0, longitude=-75.0, source_id="s"),
    ]

    inserted, skipped = seed_hospitals(mock_db, hospitals, dry_run=False)

    assert inserted == 2
    assert skipped == 1
