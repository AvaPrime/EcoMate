"""Tests for Google Maps API integration.

These tests require GOOGLE_API_KEY environment variable to be set.
Some tests are marked as integration tests and may be skipped in CI.
"""

import os
import pytest
from unittest.mock import patch, AsyncMock

from services.utils.google_maps import (
    GoogleMapsClient,
    Location,
    DistanceResult,
    ElevationResult,
    get_site_logistics_cost,
    validate_site_accessibility
)


class TestGoogleMapsClient:
    """Test cases for GoogleMapsClient."""
    
    def test_init_without_api_key(self):
        """Test that client raises error without API key."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Google Maps API key is required"):
                GoogleMapsClient()
    
    def test_init_with_api_key(self):
        """Test that client initializes with API key."""
        client = GoogleMapsClient(api_key="test_key")
        assert client.api_key == "test_key"
        assert client.base_url == "https://maps.googleapis.com/maps/api"
    
    def test_init_with_env_var(self):
        """Test that client uses environment variable."""
        with patch.dict(os.environ, {'GOOGLE_API_KEY': 'env_test_key'}):
            client = GoogleMapsClient()
            assert client.api_key == "env_test_key"


class TestGoogleMapsIntegration:
    """Integration tests for Google Maps API.
    
    These tests require a valid GOOGLE_API_KEY and make real API calls.
    They may be skipped in CI environments.
    """
    
    @pytest.fixture
    def client(self):
        """Create a client for integration tests."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set - skipping integration tests")
        return GoogleMapsClient(api_key=api_key)
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_geocode_cape_town(self, client):
        """Test geocoding Cape Town address."""
        location = await client.geocode("Cape Town, South Africa")
        
        assert location is not None
        assert isinstance(location, Location)
        assert -34.0 < location.latitude < -33.5  # Approximate Cape Town latitude
        assert 18.0 < location.longitude < 19.0   # Approximate Cape Town longitude
        assert "Cape Town" in location.formatted_address
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_reverse_geocode(self, client):
        """Test reverse geocoding Cape Town coordinates."""
        # Cape Town City Hall coordinates
        address = await client.reverse_geocode(-33.9249, 18.4241)
        
        assert address is not None
        assert "Cape Town" in address
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_calculate_distance(self, client):
        """Test distance calculation between two Cape Town locations."""
        result = await client.calculate_distance(
            "Cape Town City Hall, South Africa",
            "Table Mountain, Cape Town, South Africa"
        )
        
        assert result is not None
        assert isinstance(result, DistanceResult)
        assert result.status == "OK"
        assert 0 < result.distance_km < 20  # Should be reasonable distance
        assert 0 < result.duration_minutes < 60  # Should be reasonable time
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_elevation(self, client):
        """Test elevation API for Table Mountain."""
        # Table Mountain peak coordinates
        locations = [(-33.9628, 18.4098)]
        results = await client.get_elevation(locations)
        
        assert len(results) == 1
        result = results[0]
        assert isinstance(result, ElevationResult)
        assert 800 < result.elevation_m < 1200  # Table Mountain is ~1085m
        assert result.location.latitude == -33.9628
        assert result.location.longitude == 18.4098


class TestUtilityFunctions:
    """Test utility functions that use Google Maps API."""
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_site_logistics_cost(self):
        """Test logistics cost calculation."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set - skipping integration tests")
        
        result = await get_site_logistics_cost(
            "Stellenbosch, South Africa",
            "Cape Town, South Africa"
        )
        
        assert "error" not in result
        assert "site_coordinates" in result
        assert "distance_km" in result
        assert "logistics_cost_zar" in result
        assert result["distance_km"] > 0
        assert result["logistics_cost_zar"] > 0
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_validate_site_accessibility(self):
        """Test site accessibility validation."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            pytest.skip("GOOGLE_API_KEY not set - skipping integration tests")
        
        result = await validate_site_accessibility("Cape Town, South Africa")
        
        assert "accessible" in result
        assert "elevation_m" in result
        assert "coordinates" in result
        assert result["accessible"] is True  # Cape Town should be accessible
        assert 0 <= result["elevation_m"] < 500  # Cape Town is at sea level


class TestMockedGoogleMaps:
    """Test Google Maps functionality with mocked responses."""
    
    @pytest.mark.asyncio
    async def test_geocode_success(self):
        """Test successful geocoding with mocked response."""
        mock_response = {
            "status": "OK",
            "results": [{
                "formatted_address": "Cape Town, South Africa",
                "geometry": {
                    "location": {
                        "lat": -33.9249,
                        "lng": 18.4241
                    }
                }
            }]
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response_obj
            
            client = GoogleMapsClient(api_key="test_key")
            location = await client.geocode("Cape Town, South Africa")
            
            assert location is not None
            assert location.latitude == -33.9249
            assert location.longitude == 18.4241
            assert location.formatted_address == "Cape Town, South Africa"
    
    @pytest.mark.asyncio
    async def test_geocode_not_found(self):
        """Test geocoding when address is not found."""
        mock_response = {
            "status": "ZERO_RESULTS",
            "results": []
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response_obj
            
            client = GoogleMapsClient(api_key="test_key")
            location = await client.geocode("Invalid Address 12345")
            
            assert location is None


if __name__ == "__main__":
    # Run basic tests
    pytest.main(["-v", __file__, "-m", "not integration"])