"""Tests for geospatial services.

This module contains comprehensive tests for the geospatial service components
including unit tests, integration tests, and mock tests.
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from .client import GeospatialClient, GeospatialAPIError
from .models import (
    AccessibilityLevel,
    BatchGeospatialRequest,
    CoordinateSystem,
    ElevationData,
    GeospatialQuery,
    Location,
    SlopeData,
    SoilData,
    SoilType,
    TerrainType,
)
from .service import GeospatialService


class TestGeospatialClient:
    """Test cases for GeospatialClient."""
    
    def test_client_initialization(self):
        """Test client initialization with different configurations."""
        # Test with no API keys
        client = GeospatialClient()
        assert client.google_api_key is None
        assert client.timeout == 30
        
        # Test with API keys
        client = GeospatialClient(
            google_api_key="test_key",
            timeout=60
        )
        assert client.google_api_key == "test_key"
        assert client.timeout == 60
    
    @pytest.mark.asyncio
    async def test_geocode_success(self):
        """Test successful geocoding."""
        client = GeospatialClient(google_api_key="test_key")
        
        mock_response = {
            "status": "OK",
            "results": [{
                "formatted_address": "New York, NY, USA",
                "geometry": {
                    "location": {
                        "lat": 40.7128,
                        "lng": -74.0060
                    }
                }
            }]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            location = await client.geocode("New York")
            
            assert location is not None
            assert location.latitude == 40.7128
            assert location.longitude == -74.0060
            assert location.formatted_address == "New York, NY, USA"
    
    @pytest.mark.asyncio
    async def test_geocode_not_found(self):
        """Test geocoding when address not found."""
        client = GeospatialClient(google_api_key="test_key")
        
        mock_response = {
            "status": "ZERO_RESULTS",
            "results": []
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            location = await client.geocode("Invalid Address")
            assert location is None
    
    @pytest.mark.asyncio
    async def test_geocode_no_api_key(self):
        """Test geocoding without API key."""
        client = GeospatialClient()
        
        with pytest.raises(GeospatialAPIError, match="Google API key required"):
            await client.geocode("New York")
    
    @pytest.mark.asyncio
    async def test_elevation_google_success(self):
        """Test successful elevation data retrieval from Google."""
        client = GeospatialClient(google_api_key="test_key")
        
        mock_response = {
            "status": "OK",
            "results": [{
                "elevation": 10.5,
                "resolution": 9.5
            }]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            elevations = await client.get_elevation_google([(40.7128, -74.0060)])
            
            assert len(elevations) == 1
            assert elevations[0].elevation_m == 10.5
            assert elevations[0].resolution_m == 9.5
            assert elevations[0].data_source == "Google Elevation API"
    
    @pytest.mark.asyncio
    async def test_elevation_usgs_success(self):
        """Test successful elevation data retrieval from USGS."""
        client = GeospatialClient()
        
        mock_response = {
            "USGS_Elevation_Point_Query_Service": {
                "Elevation_Query": {
                    "Elevation": "15.2"
                }
            }
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            elevation = await client.get_elevation_usgs(40.7128, -74.0060)
            
            assert elevation is not None
            assert elevation.elevation_m == 15.2
            assert elevation.data_source == "USGS Elevation Point Query Service"
    
    @pytest.mark.asyncio
    async def test_slope_calculation_success(self):
        """Test successful slope calculation."""
        client = GeospatialClient(google_api_key="test_key")
        
        # Mock elevation responses for slope calculation
        mock_response = {
            "status": "OK",
            "results": [
                {"elevation": 105.0, "resolution": 9.5},  # North
                {"elevation": 95.0, "resolution": 9.5},   # South
                {"elevation": 102.0, "resolution": 9.5},  # East
                {"elevation": 98.0, "resolution": 9.5},   # West
                {"elevation": 100.0, "resolution": 9.5}   # Center
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            slope_data = await client.calculate_slope(40.7128, -74.0060)
            
            assert slope_data is not None
            assert slope_data.slope_degrees > 0
            assert slope_data.terrain_type in TerrainType
            assert 0 <= slope_data.aspect_degrees < 360
    
    @pytest.mark.asyncio
    async def test_soil_data_success(self):
        """Test successful soil data retrieval."""
        client = GeospatialClient()
        
        mock_response = {
            "properties": [
                {
                    "name": "clay",
                    "depths": [{"values": {"mean": 250}}]  # 25% clay
                },
                {
                    "name": "sand",
                    "depths": [{"values": {"mean": 400}}]  # 40% sand
                },
                {
                    "name": "silt",
                    "depths": [{"values": {"mean": 350}}]  # 35% silt
                },
                {
                    "name": "phh2o",
                    "depths": [{"values": {"mean": 65}}]   # pH 6.5
                }
            ]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            soil_data = await client.get_soil_data(40.7128, -74.0060)
            
            assert soil_data is not None
            assert soil_data.clay_percent == 25.0
            assert soil_data.sand_percent == 40.0
            assert soil_data.silt_percent == 35.0
            assert soil_data.ph_level == 6.5
            assert soil_data.soil_type == SoilType.LOAM
    
    @pytest.mark.asyncio
    async def test_distance_matrix_success(self):
        """Test successful distance matrix calculation."""
        client = GeospatialClient(google_api_key="test_key")
        
        mock_response = {
            "status": "OK",
            "rows": [{
                "elements": [{
                    "status": "OK",
                    "distance": {"value": 5000},  # 5 km
                    "duration": {"value": 600}    # 10 minutes
                }]
            }]
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = MagicMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            origin = Location(latitude=40.7128, longitude=-74.0060)
            destination = Location(latitude=40.7589, longitude=-73.9851)
            
            distance_matrix = await client.calculate_distance_matrix(origin, destination)
            
            assert distance_matrix is not None
            assert distance_matrix.distance_km == 5.0
            assert distance_matrix.duration_minutes == 10.0
            assert distance_matrix.status == "OK"


class TestGeospatialService:
    """Test cases for GeospatialService."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock GeospatialClient."""
        client = MagicMock(spec=GeospatialClient)
        return client
    
    @pytest.fixture
    def service(self, mock_client):
        """Create a GeospatialService with mock client."""
        return GeospatialService(client=mock_client)
    
    @pytest.mark.asyncio
    async def test_assess_site_success(self, service, mock_client):
        """Test successful site assessment."""
        # Mock comprehensive analysis
        mock_analysis = MagicMock()
        mock_analysis.installation_feasibility = True
        mock_analysis.accessibility = AccessibilityLevel.GOOD
        mock_analysis.terrain_difficulty_score = 3.0
        mock_analysis.warnings = []
        mock_analysis.recommendations = []
        
        mock_client.analyze_site_comprehensive.return_value = mock_analysis
        
        location = Location(latitude=40.7128, longitude=-74.0060)
        assessment = await service.assess_site(location, include_logistics=False)
        
        assert assessment is not None
        assert assessment.project_viable is True
        mock_client.analyze_site_comprehensive.assert_called_once_with(location)
    
    @pytest.mark.asyncio
    async def test_calculate_logistics_cost_success(self, service, mock_client):
        """Test successful logistics cost calculation."""
        # Mock distance matrix
        mock_distance_matrix = MagicMock()
        mock_distance_matrix.distance_km = 10.0
        mock_distance_matrix.duration_minutes = 30.0
        
        mock_client.calculate_distance_matrix.return_value = mock_distance_matrix
        
        # Mock elevation data
        mock_elevation = MagicMock()
        mock_elevation.elevation_m = 500.0
        mock_client.get_elevation_google.return_value = [mock_elevation]
        
        # Mock slope data
        mock_slope = MagicMock()
        mock_slope.slope_degrees = 5.0
        mock_slope.terrain_type = TerrainType.ROLLING
        mock_client.calculate_slope.return_value = mock_slope
        
        origin = Location(latitude=40.7128, longitude=-74.0060)
        destination = Location(latitude=40.7589, longitude=-73.9851)
        
        logistics_cost = await service.calculate_logistics_cost(origin, destination)
        
        assert logistics_cost is not None
        assert logistics_cost.total_cost_usd > 0
        assert logistics_cost.distance_km == 10.0
        assert logistics_cost.travel_time_hours == 0.5
    
    @pytest.mark.asyncio
    async def test_process_geospatial_query_success(self, service, mock_client):
        """Test successful geospatial query processing."""
        # Mock geocoding
        mock_location = Location(latitude=40.7128, longitude=-74.0060)
        mock_client.geocode.return_value = mock_location
        
        # Mock elevation data
        mock_elevation = ElevationData(
            location=mock_location,
            elevation_m=10.5,
            data_source="Test",
            timestamp=datetime.utcnow()
        )
        mock_client.get_elevation_google.return_value = [mock_elevation]
        
        query = GeospatialQuery(
            query_id=str(uuid4()),
            locations=[Location(address="New York")],
            data_types=["elevation"],
            timestamp=datetime.utcnow()
        )
        
        response = await service.process_geospatial_query(query)
        
        assert response is not None
        assert response.total_locations == 1
        assert response.successful_locations == 1
    
    @pytest.mark.asyncio
    async def test_process_batch_request_success(self, service):
        """Test successful batch request processing."""
        # Mock the process_geospatial_query method
        mock_response = MagicMock()
        service.process_geospatial_query = AsyncMock(return_value=mock_response)
        
        queries = [
            GeospatialQuery(
                query_id=str(uuid4()),
                locations=[Location(latitude=40.7128, longitude=-74.0060)],
                data_types=["elevation"],
                timestamp=datetime.utcnow()
            )
        ]
        
        batch_request = BatchGeospatialRequest(
            batch_id=str(uuid4()),
            queries=queries,
            max_concurrent_requests=5,
            timestamp=datetime.utcnow()
        )
        
        batch_response = await service.process_batch_request(batch_request)
        
        assert batch_response is not None
        assert batch_response.total_queries == 1
        assert batch_response.successful_queries == 1
        assert batch_response.failed_queries_count == 0
    
    @pytest.mark.asyncio
    async def test_find_optimal_sites_success(self, service):
        """Test successful optimal site finding."""
        # Mock assess_site method
        mock_assessment = MagicMock()
        mock_assessment.project_viable = True
        mock_assessment.geospatial_analysis.accessibility = AccessibilityLevel.GOOD
        mock_assessment.geospatial_analysis.terrain_difficulty_score = 3.0
        mock_assessment.logistics_cost.total_cost_usd = 1000.0
        
        service.assess_site = AsyncMock(return_value=mock_assessment)
        
        candidate_locations = [
            Location(latitude=40.7128, longitude=-74.0060),
            Location(latitude=40.7589, longitude=-73.9851)
        ]
        depot_location = Location(latitude=40.7500, longitude=-74.0000)
        
        optimal_sites = await service.find_optimal_sites(
            candidate_locations, depot_location, max_sites=2
        )
        
        assert len(optimal_sites) <= 2
        assert all(site.project_viable for site in optimal_sites)


class TestModels:
    """Test cases for Pydantic models."""
    
    def test_location_model(self):
        """Test Location model validation."""
        location = Location(
            latitude=40.7128,
            longitude=-74.0060,
            address="New York, NY"
        )
        
        assert location.latitude == 40.7128
        assert location.longitude == -74.0060
        assert location.address == "New York, NY"
        assert location.coordinate_system == CoordinateSystem.WGS84
    
    def test_location_validation(self):
        """Test Location model validation errors."""
        with pytest.raises(ValueError):
            Location(latitude=91.0, longitude=0.0)  # Invalid latitude
        
        with pytest.raises(ValueError):
            Location(latitude=0.0, longitude=181.0)  # Invalid longitude
    
    def test_elevation_data_model(self):
        """Test ElevationData model."""
        location = Location(latitude=40.7128, longitude=-74.0060)
        elevation = ElevationData(
            location=location,
            elevation_m=10.5,
            data_source="Test",
            timestamp=datetime.utcnow()
        )
        
        assert elevation.elevation_m == 10.5
        assert elevation.location == location
    
    def test_slope_data_model(self):
        """Test SlopeData model with percentage calculation."""
        location = Location(latitude=40.7128, longitude=-74.0060)
        slope = SlopeData(
            location=location,
            slope_degrees=15.0,
            aspect_degrees=180.0,
            terrain_type=TerrainType.HILLY,
            data_source="Test",
            timestamp=datetime.utcnow()
        )
        
        assert slope.slope_degrees == 15.0
        assert abs(slope.slope_percentage - 26.79) < 0.1  # tan(15°) * 100
    
    def test_soil_data_model(self):
        """Test SoilData model."""
        location = Location(latitude=40.7128, longitude=-74.0060)
        soil = SoilData(
            location=location,
            soil_type=SoilType.LOAM,
            ph_level=6.5,
            clay_percent=25.0,
            sand_percent=40.0,
            silt_percent=35.0,
            data_source="Test",
            timestamp=datetime.utcnow()
        )
        
        assert soil.soil_type == SoilType.LOAM
        assert soil.ph_level == 6.5
        assert soil.clay_percent == 25.0


@pytest.mark.integration
class TestIntegration:
    """Integration tests requiring actual API keys."""
    
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_API_KEY'),
        reason="GOOGLE_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_geocoding(self):
        """Test real geocoding with Google API."""
        client = GeospatialClient()
        location = await client.geocode("Times Square, New York")
        
        assert location is not None
        assert 40.7 < location.latitude < 40.8
        assert -74.1 < location.longitude < -73.9
    
    @pytest.mark.skipif(
        not os.getenv('GOOGLE_API_KEY'),
        reason="GOOGLE_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_elevation(self):
        """Test real elevation data retrieval."""
        client = GeospatialClient()
        elevations = await client.get_elevation_google([(40.7128, -74.0060)])
        
        assert len(elevations) == 1
        assert elevations[0].elevation_m is not None
        assert elevations[0].data_source == "Google Elevation API"
    
    @pytest.mark.asyncio
    async def test_real_usgs_elevation(self):
        """Test real USGS elevation data retrieval."""
        client = GeospatialClient()
        elevation = await client.get_elevation_usgs(40.7128, -74.0060)
        
        # USGS should work without API key
        assert elevation is not None
        assert elevation.elevation_m is not None
        assert elevation.data_source == "USGS Elevation Point Query Service"
    
    @pytest.mark.asyncio
    async def test_real_soil_data(self):
        """Test real soil data retrieval."""
        client = GeospatialClient()
        soil_data = await client.get_soil_data(40.7128, -74.0060)
        
        # SoilGrids should work without API key
        assert soil_data is not None
        assert soil_data.soil_type in SoilType
        assert soil_data.data_source == "SoilGrids API"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])