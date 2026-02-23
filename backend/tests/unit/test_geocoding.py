import time
from unittest.mock import MagicMock, mock_open, patch

import httpx
import pytest

from waittime.services.geocoding import GeocodingResult, GeocodingService


@pytest.fixture
def geocoding_service():
    # Pass a dummy token to test Mapbox fallback path
    return GeocodingService(mapbox_token="test_token")


# --- Manual Override Tests ---


def test_load_manual_overrides_success(geocoding_service):
    """Verify that overrides are loaded from CSV if it exists."""
    csv_content = "hospital_id,latitude,longitude,city\nca-on-test,44.0,-79.0,Test City\n"

    with patch("builtins.open", mock_open(read_data=csv_content)):
        with patch("pathlib.Path.exists", return_value=True):
            overrides = geocoding_service._load_manual_overrides()
            assert "ca-on-test" in overrides
            assert overrides["ca-on-test"].latitude == 44.0
            assert overrides["ca-on-test"].city == "Test City"


def test_load_manual_overrides_missing_file(geocoding_service):
    """Verify graceful handling if CSV is missing."""
    with patch("pathlib.Path.exists", return_value=False):
        overrides = geocoding_service._load_manual_overrides()
        assert overrides == {}


def test_load_manual_overrides_malformed_csv(geocoding_service):
    """Verify handling of invalid rows."""
    csv_content = "hospital_id,latitude,longitude,city\nca-on-bad,invalid,coords,City\n"

    with patch("builtins.open", mock_open(read_data=csv_content)):
        with patch("pathlib.Path.exists", return_value=True):
            overrides = geocoding_service._load_manual_overrides()
            assert overrides == {}


def test_load_manual_overrides_id_missing(geocoding_service):
    """Verify that rows without IDs are skipped."""
    csv_content = "hospital_id,latitude,longitude,city\n,44.0,-79.0,No ID City\n"

    with patch("builtins.open", mock_open(read_data=csv_content)):
        with patch("pathlib.Path.exists", return_value=True):
            overrides = geocoding_service._load_manual_overrides()
            assert overrides == {}


# --- Geocoding Flow Tests ---


def test_geocode_hospital_manual_priority(geocoding_service):
    """Verify that manual override takes precedence over network calls."""
    geocoding_service._manual_overrides = {
        "ca-on-manual": GeocodingResult(44.0, -79.0, "Manual City", 1.0)
    }

    with patch.object(geocoding_service, "_geocode_with_nominatim") as mock_nom:
        result = geocoding_service.geocode_hospital(
            "Test Hospital", "ON", hospital_id="ca-on-manual"
        )
        assert result.city == "Manual City"
        mock_nom.assert_not_called()


def test_geocode_hospital_fallback_chain(geocoding_service):
    """Test the full chain: Nominatim (low confidence) -> Mapbox."""
    nom_result = GeocodingResult(45.0, -75.0, "Nom City", 0.5)
    mapbox_result = GeocodingResult(45.1, -75.1, "Mapbox City", 0.9)

    with patch.object(geocoding_service, "_geocode_with_nominatim", return_value=nom_result):
        with patch.object(geocoding_service, "_geocode_with_mapbox", return_value=mapbox_result):
            result = geocoding_service.geocode_hospital("Test", "ON")
            assert result.city == "Mapbox City"


def test_geocode_hospital_nominatim_high_confidence(geocoding_service):
    """Nominatim high confidence should return immediately."""
    nom_result = GeocodingResult(45.0, -75.0, "Nom City", 0.9)

    with patch.object(geocoding_service, "_geocode_with_nominatim", return_value=nom_result):
        with patch.object(geocoding_service, "_geocode_with_mapbox") as mock_mapbox:
            result = geocoding_service.geocode_hospital("Test", "ON")
            assert result.city == "Nom City"
            mock_mapbox.assert_not_called()


def test_geocode_hospital_low_confidence_no_mapbox_token(geocoding_service):
    """Return low confidence Nom result if mapbox token is missing."""
    geocoding_service.mapbox_token = None
    nom_result = GeocodingResult(45.0, -75.0, "Nom City", 0.5)

    with patch.object(geocoding_service, "_geocode_with_nominatim", return_value=nom_result):
        result = geocoding_service.geocode_hospital("Test", "ON")
        assert result.city == "Nom City"
        assert result.confidence == 0.5


def test_geocode_hospital_all_fail(geocoding_service):
    """Geocode hospital returns None if all providers fail."""
    with patch.object(geocoding_service, "_geocode_with_nominatim", return_value=None):
        result = geocoding_service.geocode_hospital("Test", "ON")
        assert result is None


# --- Nominatim Integration Tests ---


def test_nominatim_success(geocoding_service):
    """Verify Nominatim API integration with mocked response."""
    mock_response = MagicMock()
    mock_response.json.return_value = [
        {
            "lat": "45.0",
            "lon": "-75.0",
            "display_name": "Test Hospital, Test Street, Ottawa, ON, Canada",
            "importance": 0.8,
        }
    ]
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = geocoding_service._geocode_with_nominatim("Test Hospital", "ON", "Canada")
        assert result.latitude == 45.0
        assert result.city == "Ottawa"
        assert result.confidence == 0.8


def test_nominatim_rate_limiting(geocoding_service):
    """Verify Nominatim 1 request per second rate limiting."""
    mock_response = MagicMock()
    mock_response.json.return_value = []

    geocoding_service._last_nominatim_request = time.time()

    with patch("httpx.get", return_value=mock_response):
        with patch("time.sleep") as mock_sleep:
            geocoding_service._geocode_with_nominatim("Test", "ON", "CA")
            mock_sleep.assert_called_once()


# --- Mapbox Integration Tests ---


def test_mapbox_success(geocoding_service):
    """Verify Mapbox API integration with mocked response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [
            {
                "geometry": {"coordinates": [-75.0, 45.0]},
                "place_name": "Test Hospital, Ottawa, ON, Canada",
                "context": [{"id": "place.123", "text": "Ottawa"}],
                "relevance": 0.9,
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = geocoding_service._geocode_with_mapbox("Test Hospital", "ON", "Canada")
        assert result.latitude == 45.0
        assert result.longitude == -75.0
        assert result.city == "Ottawa"
        assert result.confidence == 0.9


def test_mapbox_with_city_hint(geocoding_service):
    """Verify Mapbox query building with city hint."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response) as mock_get:
        geocoding_service._geocode_with_mapbox("Ottawa Hospital", "ON", "Canada")
        # Check that Ottawa was in the query part of the URL
        assert "Ottawa" in mock_get.call_args[0][0]


# --- City Extraction Tests ---


def test_extract_city_from_display_name(geocoding_service):
    """Test various display name formats from Nominatim."""
    # Known city
    assert geocoding_service._extract_city_from_display_name("A, B, Toronto, ON") == "Toronto"
    # Fallback to 3rd component
    assert (
        geocoding_service._extract_city_from_display_name("Hosp, Street, SmallTown, Region, ON")
        == "SmallTown"
    )
    # Unknown
    assert geocoding_service._extract_city_from_display_name("A, B") == "Unknown"


def test_extract_city_hint(geocoding_service):
    """Test city hint extraction from hospital names."""
    assert geocoding_service._extract_city_hint("Ottawa Hospital Civic", "ON") == "Ottawa"
    assert geocoding_service._extract_city_hint("Toronto General", "ON") == "Toronto"
    assert geocoding_service._extract_city_hint("No City Hospital", "ON") is None


def test_extract_city_mapbox(geocoding_service):
    """Test city extraction from Mapbox feature."""
    feature = {
        "place_name": "Hosp, CityName, Prov, Country",
        "context": [{"id": "place.1", "text": "CityName"}],
    }
    assert geocoding_service._extract_city(feature) == "CityName"


def test_extract_city_mapbox_no_context(geocoding_service):
    """Test city extraction from Mapbox feature without context."""
    feature = {"place_name": "Major City", "context": []}
    assert geocoding_service._extract_city(feature) == "Unknown"


def test_extract_city_mapbox_short_name(geocoding_service):
    """Test city extraction from Mapbox feature with short place_name."""
    feature = {"place_name": "HospitalOnly", "context": []}
    assert geocoding_service._extract_city(feature) == "Unknown"


def test_extract_city_mapbox_context_fallback(geocoding_service):
    """Test city extraction from Mapbox context when place_name format is unexpected."""
    feature = {
        "place_name": "UnexpectedFormat",
        "context": [{"id": "place.123", "text": "ContextCity"}],
    }
    assert geocoding_service._extract_city(feature) == "ContextCity"


# --- Error Handling & Branching Tests ---


def test_load_manual_overrides_exception(geocoding_service):
    """Verify handling of unexpected exceptions during override load."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", side_effect=Exception("File Error")):
            overrides = geocoding_service._load_manual_overrides()
            assert overrides == {}


def test_nominatim_exception(geocoding_service):
    """Verify Nominatim handles network exceptions."""
    with patch("httpx.get", side_effect=httpx.HTTPError("Network Error")):
        result = geocoding_service._geocode_with_nominatim("Test", "ON", "CA")
        assert result is None


def test_nominatim_query_branching(geocoding_service):
    """Test query building branches for different provinces/hints."""
    # Ontario with city hint
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = []
        geocoding_service._geocode_with_nominatim("Ottawa Hospital", "ON", "CA")
        # Check that Ottawa was in the query
        assert "Ottawa" in mock_get.call_args_list[0][1]["params"]["q"]

    # Ontario without city hint (major city fallback loop)
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = []
        geocoding_service._geocode_with_nominatim("Generic Hospital", "ON", "CA")
        # Should try multiple queries
        assert mock_get.call_count >= 3

    # Other province
    with patch("httpx.get") as mock_get:
        mock_get.return_value.json.return_value = []
        geocoding_service._geocode_with_nominatim("Montreal General", "QC", "CA")
        assert mock_get.call_count == 1


def test_mapbox_no_results(geocoding_service):
    """Verify Mapbox handles empty results."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"features": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=mock_response):
        result = geocoding_service._geocode_with_mapbox("Test", "ON", "CA")
        assert result is None


def test_mapbox_exception(geocoding_service):
    """Verify Mapbox handles network exceptions."""
    with patch("httpx.get", side_effect=httpx.HTTPError("API Error")):
        result = geocoding_service._geocode_with_mapbox("Test", "ON", "CA")
        assert result is None

    with patch("httpx.get", return_value=MagicMock(side_effect=ValueError("Parse Error"))):
        # This tests the second except block in _geocode_with_mapbox
        with patch.object(httpx.Response, "json", side_effect=ValueError("Bad JSON")):
            result = geocoding_service._geocode_with_mapbox("Test", "ON", "CA")
            assert result is None
