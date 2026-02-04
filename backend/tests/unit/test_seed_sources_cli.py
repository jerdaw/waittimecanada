import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path
from waittime.cli.seed_sources import load_source_from_json, seed_source, main

def test_load_source_from_json_success(tmp_path):
    """Verify loading source from valid JSON file."""
    source_data = {
        "id": "test-source",
        "name": "Test Source",
        "url": "http://example.com",
        "province": "ON",
        "telehealth_name": "Telehealth ON",
        "telehealth_number": "1-800-123-4567",
        "default_metric_family": "TIME_TO_PROVIDER",
        "default_start_event": "TRIAGE",
        "default_end_event": "PHYSICIAN",
        "default_statistic_type": "MEDIAN"
    }
    file_path = tmp_path / "source.json"
    file_path.write_text(json.dumps(source_data))
    
    source = load_source_from_json(file_path)
    assert source.id == "test-source"
    assert source.name == "Test Source"

def test_load_source_from_json_missing_file():
    """Verify exception when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_source_from_json(Path("non-existent.json"))

def test_load_source_from_json_invalid_data(tmp_path):
    """Verify exception when JSON data is invalid."""
    file_path = tmp_path / "invalid.json"
    file_path.write_text(json.dumps({"invalid": "data"}))
    
    with pytest.raises(ValueError):
        load_source_from_json(file_path)

def test_seed_source_dry_run():
    """Verify dry run behavior."""
    mock_db = MagicMock()
    mock_source = MagicMock(id="test", name="Test")
    result = seed_source(mock_db, mock_source, dry_run=True)
    assert result is True
    mock_db.upsert_source.assert_not_called()

def test_seed_source_success():
    """Verify successful seeding."""
    mock_db = MagicMock()
    mock_source = MagicMock(id="test", name="Test")
    result = seed_source(mock_db, mock_source, dry_run=False)
    assert result is True
    mock_db.upsert_source.assert_called_once_with(mock_source)

def test_main_list_mode():
    """Verify that --list mode works."""
    with patch("sys.argv", ["seed_sources.py", "--list"]):
        with patch("waittime.cli.seed_sources.DatabaseService") as mock_db:
            mock_db_instance = mock_db.return_value
            mock_db_instance.list_sources.return_value = []
            assert main() == 0
            mock_db_instance.list_sources.assert_called_once()

def test_main_seed_mode(tmp_path):
    """Verify that seeding via --file works."""
    source_data = {
        "id": "test-source",
        "name": "Test Source",
        "url": "http://example.com",
        "province": "ON",
        "telehealth_name": "Telehealth ON",
        "telehealth_number": "1-800-123-4567",
        "default_metric_family": "TIME_TO_PROVIDER",
        "default_start_event": "TRIAGE",
        "default_end_event": "PHYSICIAN",
        "default_statistic_type": "MEDIAN"
    }
    file_path = tmp_path / "source.json"
    file_path.write_text(json.dumps(source_data))
    
    with patch("sys.argv", ["seed_sources.py", "--file", str(file_path)]):
        with patch("waittime.cli.seed_sources.DatabaseService") as mock_db:
            assert main() == 0
            mock_db.return_value.upsert_source.assert_called_once()
