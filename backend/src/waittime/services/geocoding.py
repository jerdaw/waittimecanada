"""Geocoding service for hospital addresses.

Uses OpenStreetMap Nominatim API (free, no API key required).
Falls back to Mapbox if Nominatim fails and MAPBOX_TOKEN is available.
"""

import logging
import os
import time
from typing import NamedTuple

import httpx

logger = logging.getLogger(__name__)


class GeocodingResult(NamedTuple):
    """Result from geocoding a location."""

    latitude: float
    longitude: float
    city: str
    confidence: float  # 0.0 to 1.0


class GeocodingService:
    """Service for geocoding hospital names to coordinates.

    Primary: OpenStreetMap Nominatim (free, no API key, 1 req/sec limit)
    Fallback: Mapbox Geocoding API (optional, requires MAPBOX_TOKEN)
    """

    def __init__(self, mapbox_token: str | None = None):
        """Initialize geocoding service.

        Args:
            mapbox_token: Optional Mapbox API token for fallback (defaults to MAPBOX_TOKEN env var)
        """
        self.mapbox_token = mapbox_token or os.environ.get("MAPBOX_TOKEN")
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.mapbox_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"

        # Rate limiting for Nominatim (1 request/second)
        self._last_nominatim_request = 0.0

    def geocode_hospital(
        self, hospital_name: str, province: str, country: str = "Canada"
    ) -> GeocodingResult | None:
        """Geocode a hospital name to coordinates.

        Tries Nominatim first (free, accurate for POIs).
        Falls back to Mapbox if Nominatim fails and token is available.

        Args:
            hospital_name: Name of the hospital
            province: Province code (e.g., "ON", "QC")
            country: Country name (default: "Canada")

        Returns:
            GeocodingResult with coordinates and city, or None if geocoding fails

        Example:
            >>> service = GeocodingService()
            >>> result = service.geocode_hospital("CHEO", "ON")
            >>> print(f"{result.latitude}, {result.longitude}")
            45.4023, -75.6452
        """
        # Try Nominatim first (free, no API key needed)
        result = self._geocode_with_nominatim(hospital_name, province, country)
        if result and result.confidence > 0.7:
            return result

        # Fall back to Mapbox if available
        if self.mapbox_token:
            logger.info(f"Nominatim failed for {hospital_name}, trying Mapbox")
            return self._geocode_with_mapbox(hospital_name, province, country)

        logger.warning(f"Failed to geocode {hospital_name} (no Mapbox fallback)")
        return None

    def _geocode_with_nominatim(
        self, hospital_name: str, province: str, country: str
    ) -> GeocodingResult | None:
        """Geocode using OpenStreetMap Nominatim API (free).

        Rate limit: 1 request per second.
        Usage policy: https://operations.osmfoundation.org/policies/nominatim/
        """
        # Respect rate limit (1 request/second)
        now = time.time()
        time_since_last = now - self._last_nominatim_request
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_nominatim_request = time.time()

        # Extract city hint for better results
        city_hint = self._extract_city_hint(hospital_name, province)

        # Build query: "Hospital Name City Province"
        # For Ontario, if no city found, try major cities in order
        if city_hint:
            queries_to_try = [f"{hospital_name} {city_hint} {province}"]
        elif province == "ON":
            # Try major Ontario cities in order of likelihood
            queries_to_try = [
                f"{hospital_name} Ottawa {province}",
                f"{hospital_name} Toronto {province}",
                f"{hospital_name} {province}",  # Fallback without city
            ]
        else:
            queries_to_try = [f"{hospital_name} {province}"]

        # Try each query until we get a result
        for query in queries_to_try:
            try:
                params: dict[str, str | int] = {
                    "q": query,
                    "format": "json",
                    "limit": 1,
                    "countrycodes": "ca",
                }
                headers = {"User-Agent": "WaitTimeCanada/1.0"}

                response = httpx.get(
                    self.nominatim_url, params=params, headers=headers, timeout=10.0
                )
                response.raise_for_status()
                data = response.json()

                if not data:
                    continue  # Try next query

                result = data[0]
                latitude = float(result["lat"])
                longitude = float(result["lon"])
                display_name = result.get("display_name", "")
                city = self._extract_city_from_display_name(display_name)
                importance = result.get("importance", 0.0)
                confidence = min(importance, 1.0)

                logger.info(
                    f"✅ Nominatim: {hospital_name} → ({latitude:.4f}, {longitude:.4f}) {city}"
                )

                return GeocodingResult(
                    latitude=latitude,
                    longitude=longitude,
                    city=city,
                    confidence=confidence,
                )

            except Exception as e:
                logger.debug(f"Nominatim query failed: {query} - {e}")
                continue

        return None

    def _geocode_with_mapbox(
        self, hospital_name: str, province: str, country: str
    ) -> GeocodingResult | None:
        """Geocode using Mapbox API (requires MAPBOX_TOKEN)."""
        # Try to extract city from hospital name
        city_hint = self._extract_city_hint(hospital_name, province)

        # Build search query with city hint if available
        if city_hint:
            query = f"{hospital_name}, {city_hint}, {province}, {country}"
        else:
            # Fall back to just province
            query = f"{hospital_name}, {province}, {country}"

        # Mapbox Geocoding API parameters
        params = {
            "access_token": self.mapbox_token,
            "country": "CA",  # Limit to Canada
            "types": "poi,address",  # Points of interest and addresses
            "limit": 1,  # Only need top result
        }

        try:
            # Encode query for URL
            encoded_query = httpx.QueryParams({"q": query})["q"]
            url = f"{self.mapbox_url}/{encoded_query}.json"

            logger.debug(f"Geocoding: {query}")

            response = httpx.get(url, params=params, timeout=10.0)
            response.raise_for_status()

            data = response.json()

            if not data.get("features"):
                logger.warning(f"No geocoding results for: {query}")
                return None

            # Get top result
            feature = data["features"][0]
            coords = feature["geometry"]["coordinates"]
            longitude, latitude = coords  # GeoJSON is [lng, lat]

            # Extract city from context
            city = self._extract_city(feature)

            # Relevance score (0.0 to 1.0)
            confidence = feature.get("relevance", 0.0)

            logger.info(
                f"✅ Geocoded {hospital_name}: "
                f"({latitude:.4f}, {longitude:.4f}) "
                f"confidence={confidence:.2f}"
            )

            return GeocodingResult(
                latitude=latitude,
                longitude=longitude,
                city=city or "Unknown",
                confidence=confidence,
            )

        except httpx.HTTPError as e:
            logger.error(f"Geocoding API error for {query}: {e}")
            return None
        except (KeyError, IndexError, ValueError) as e:
            logger.error(f"Failed to parse geocoding response for {query}: {e}")
            return None

    def _extract_city_from_display_name(self, display_name: str) -> str:
        """Extract city from Nominatim display_name.

        Format: "Hospital, Street, City, Region, Province, Postal, Country"
        City is usually the 3rd or 4th component.
        """
        parts = [p.strip() for p in display_name.split(",")]

        # Common Ontario cities to look for
        known_cities = [
            "Ottawa",
            "Toronto",
            "Hamilton",
            "London",
            "Kingston",
            "Windsor",
            "Mississauga",
            "Brampton",
            "Kitchener",
            "Waterloo",
        ]

        for part in parts:
            if any(city in part for city in known_cities):
                return part

        # Fall back to 3rd component if no known city found
        if len(parts) >= 3:
            return parts[2]

        return "Unknown"

    def _extract_city_hint(self, hospital_name: str, province: str) -> str | None:
        """Extract city name hint from hospital name.

        Args:
            hospital_name: Name like "Ottawa Hospital Civic" or "Toronto General"
            province: Province code for context

        Returns:
            City name if found, None otherwise
        """
        # Common Ontario cities (most hospitals are in major cities)
        ontario_cities = [
            "Ottawa",
            "Toronto",
            "Hamilton",
            "London",
            "Kingston",
            "Windsor",
            "Mississauga",
            "Brampton",
            "Kitchener",
            "Waterloo",
            "Guelph",
            "Cambridge",
            "Barrie",
            "Oshawa",
            "St. Catharines",
            "Niagara",
            "Thunder Bay",
            "Sudbury",
            "Sault Ste. Marie",
            "Peterborough",
            "Sarnia",
            "Cornwall",
        ]

        # Check if any city name appears in the hospital name
        name_lower = hospital_name.lower()
        for city in ontario_cities:
            if city.lower() in name_lower:
                return city

        return None

    def _extract_city(self, feature: dict) -> str:
        """Extract city name from geocoding feature context."""
        # Try place_name first (often includes city)
        place_name: str = feature.get("place_name", "")
        if "," in place_name:
            # Format: "Hospital Name, City, Province, Country"
            parts = [p.strip() for p in place_name.split(",")]
            if len(parts) >= 2:
                return str(parts[1])  # Second part is usually city

        # Try context array
        context = feature.get("context", [])
        for ctx in context:
            ctx_id: str = ctx.get("id", "")
            if ctx_id.startswith("place."):
                return str(ctx.get("text", "Unknown"))

        return "Unknown"
