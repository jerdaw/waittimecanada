
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from waittime.services.geocoding import GeocodingService, GeocodingResult

@pytest.fixture
def geocoding_service():
    # Use a mock to avoid loading the real CSV if we want to isolate, 
    # but here we can just test the override logic.
    return GeocodingService()

def test_load_manual_overrides(geocoding_service):
    """Verify that overrides are loaded from CSV if it exists."""
    # This tests that the dict is populated (assuming the CSV exists in the repo)
    assert isinstance(geocoding_service._manual_overrides, dict)
    # Our test case from Midland should be in there if file was written correctly
    assert "ca-on-georgian-bay-general-hosp-midland-site" in geocoding_service._manual_overrides

def test_geocode_hospital_override(geocoding_service):
    """Verify that manual override takes precedence."""
    hospital_id = "ca-on-georgian-bay-general-hosp-midland-site"
    
    # We don't need to patch Nominatim because manual override should return first
    with patch.object(geocoding_service, '_geocode_with_nominatim') as mock_nom:
        result = geocoding_service.geocode_hospital(
            "Test Hospital", 
            "ON", 
            hospital_id=hospital_id
        )
        
        assert result is not None
        assert result.confidence == 1.0
        assert result.latitude == 44.7422
        assert result.longitude == -79.9135
        mock_nom.assert_not_called()

def test_geocode_hospital_no_override(geocoding_service):
    """Verify that it falls back to Nominatim if no override exists."""
    hospital_id = "ca-on-non-existent"
    
    mock_result = GeocodingResult(
        latitude=45.0, 
        longitude=-75.0, 
        city="Test City", 
        confidence=0.8
    )
    
    with patch.object(geocoding_service, '_geocode_with_nominatim', return_value=mock_result) as mock_nom:
        result = geocoding_service.geocode_hospital(
            "Test Hospital", 
            "ON", 
            hospital_id=hospital_id
        )
        
        assert result == mock_result
        mock_nom.assert_called_once()
