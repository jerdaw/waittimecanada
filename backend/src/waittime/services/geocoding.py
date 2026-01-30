"""Geocoding service for hospital addresses using Mapbox."""

import logging
import os
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

    Uses Mapbox Geocoding API with generous free tier (100k requests/month).
    """

    def __init__(self, mapbox_token: str | None = None):
        """Initialize geocoding service.

        Args:
            mapbox_token: Mapbox API token (defaults to MAPBOX_TOKEN env var)
        """
        self.mapbox_token = mapbox_token or os.environ.get("MAPBOX_TOKEN")
        if not self.mapbox_token:
            logger.warning(
                "MAPBOX_TOKEN not set - geocoding will fail. "
                "Set environment variable or pass token directly."
            )

        self.base_url = "https://api.mapbox.com/geocoding/v5/mapbox.places"

    def geocode_hospital(
        self, hospital_name: str, province: str, country: str = "Canada"
    ) -> GeocodingResult | None:
        """Geocode a hospital name to coordinates.

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
        if not self.mapbox_token:
            logger.error("Cannot geocode without MAPBOX_TOKEN")
            return None

        # Build search query: "Hospital Name, Province, Country"
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
            url = f"{self.base_url}/{encoded_query}.json"

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

    def _extract_city(self, feature: dict) -> str:
        """Extract city name from geocoding feature context."""
        # Try place_name first (often includes city)
        place_name = feature.get("place_name", "")
        if "," in place_name:
            # Format: "Hospital Name, City, Province, Country"
            parts = [p.strip() for p in place_name.split(",")]
            if len(parts) >= 2:
                return parts[1]  # Second part is usually city

        # Try context array
        context = feature.get("context", [])
        for ctx in context:
            ctx_id = ctx.get("id", "")
            if ctx_id.startswith("place."):
                return ctx.get("text", "Unknown")

        return "Unknown"
