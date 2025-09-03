"""Geospatial API client for EcoMate AI.

This module provides a unified client for accessing multiple geospatial APIs
including Google Maps, elevation data, slope analysis, and soil information.
"""

import asyncio
import math
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import httpx
import structlog
from pydantic import ValidationError

from .models import (
    AccessibilityLevel,
    CoordinateSystem,
    DistanceMatrix,
    ElevationData,
    GeospatialAnalysis,
    Location,
    LogisticsCost,
    SlopeData,
    SoilData,
    SoilType,
    TerrainType,
)

logger = structlog.get_logger(__name__)


class GeospatialAPIError(Exception):
    """Custom exception for geospatial API errors."""
    pass


class GeospatialClient:
    """Unified client for geospatial data APIs."""
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        usgs_api_key: Optional[str] = None,
        open_topo_api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """Initialize the geospatial client.
        
        Args:
            google_api_key: Google Maps Platform API key
            usgs_api_key: USGS API key for elevation data
            open_topo_api_key: OpenTopography API key
            timeout: Request timeout in seconds
        """
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.usgs_api_key = usgs_api_key or os.getenv('USGS_API_KEY')
        self.open_topo_api_key = open_topo_api_key or os.getenv('OPEN_TOPO_API_KEY')
        self.timeout = timeout
        
        # API endpoints
        self.google_base_url = "https://maps.googleapis.com/maps/api"
        self.usgs_elevation_url = "https://nationalmap.gov/epqs/pqs.php"
        self.open_topo_url = "https://cloud.sdsc.edu/v1/"
        self.soil_api_url = "https://rest.isric.org/soilgrids/v2.0/"
        
        logger.info("Geospatial client initialized", 
                   google_api=bool(self.google_api_key),
                   usgs_api=bool(self.usgs_api_key),
                   open_topo_api=bool(self.open_topo_api_key))
    
    async def geocode(self, address: str) -> Optional[Location]:
        """Geocode an address to coordinates using Google Maps.
        
        Args:
            address: Address to geocode
            
        Returns:
            Location object with coordinates, or None if not found
        """
        if not self.google_api_key:
            raise GeospatialAPIError("Google API key required for geocoding")
        
        url = f"{self.google_base_url}/geocode/json"
        params = {
            "address": address,
            "key": self.google_api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK" and data["results"]:
                    result = data["results"][0]
                    geometry = result["geometry"]["location"]
                    
                    return Location(
                        latitude=geometry["lat"],
                        longitude=geometry["lng"],
                        address=address,
                        formatted_address=result["formatted_address"],
                        coordinate_system=CoordinateSystem.WGS84
                    )
                    
            except Exception as e:
                logger.error("Geocoding failed", address=address, error=str(e))
                
        return None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """Reverse geocode coordinates to address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Formatted address string, or None if not found
        """
        if not self.google_api_key:
            raise GeospatialAPIError("Google API key required for reverse geocoding")
        
        url = f"{self.google_base_url}/geocode/json"
        params = {
            "latlng": f"{latitude},{longitude}",
            "key": self.google_api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK" and data["results"]:
                    return data["results"][0]["formatted_address"]
                    
            except Exception as e:
                logger.error("Reverse geocoding failed", 
                           latitude=latitude, longitude=longitude, error=str(e))
                
        return None
    
    async def get_elevation_google(self, locations: List[Tuple[float, float]]) -> List[ElevationData]:
        """Get elevation data using Google Elevation API.
        
        Args:
            locations: List of (latitude, longitude) tuples
            
        Returns:
            List of ElevationData objects
        """
        if not self.google_api_key:
            raise GeospatialAPIError("Google API key required for elevation data")
        
        url = f"{self.google_base_url}/elevation/json"
        locations_str = "|".join([f"{lat},{lng}" for lat, lng in locations])
        
        params = {
            "locations": locations_str,
            "key": self.google_api_key
        }
        
        results = []
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK":
                    for i, result in enumerate(data["results"]):
                        lat, lng = locations[i]
                        results.append(ElevationData(
                            location=Location(latitude=lat, longitude=lng),
                            elevation_m=result["elevation"],
                            resolution_m=result["resolution"],
                            data_source="Google Elevation API",
                            timestamp=datetime.utcnow()
                        ))
                        
            except Exception as e:
                logger.error("Google elevation API failed", error=str(e))
                
        return results
    
    async def get_elevation_usgs(self, latitude: float, longitude: float) -> Optional[ElevationData]:
        """Get elevation data using USGS Elevation Point Query Service.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            ElevationData object or None if failed
        """
        params = {
            "x": longitude,
            "y": latitude,
            "units": "Meters",
            "output": "json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(self.usgs_elevation_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "USGS_Elevation_Point_Query_Service" in data:
                    elevation_data = data["USGS_Elevation_Point_Query_Service"]
                    if "Elevation_Query" in elevation_data:
                        elevation = elevation_data["Elevation_Query"]["Elevation"]
                        
                        return ElevationData(
                            location=Location(latitude=latitude, longitude=longitude),
                            elevation_m=float(elevation),
                            data_source="USGS Elevation Point Query Service",
                            timestamp=datetime.utcnow()
                        )
                        
            except Exception as e:
                logger.error("USGS elevation API failed", 
                           latitude=latitude, longitude=longitude, error=str(e))
                
        return None
    
    async def calculate_slope(self, center_lat: float, center_lng: float, 
                            radius_m: float = 100) -> Optional[SlopeData]:
        """Calculate slope using elevation data from surrounding points.
        
        Args:
            center_lat: Center latitude
            center_lng: Center longitude
            radius_m: Radius for slope calculation in meters
            
        Returns:
            SlopeData object or None if calculation failed
        """
        # Create a grid of points around the center
        points = []
        lat_offset = radius_m / 111320  # Approximate meters to degrees
        lng_offset = radius_m / (111320 * math.cos(math.radians(center_lat)))
        
        # Sample points in cardinal directions
        sample_points = [
            (center_lat + lat_offset, center_lng),  # North
            (center_lat - lat_offset, center_lng),  # South
            (center_lat, center_lng + lng_offset),  # East
            (center_lat, center_lng - lng_offset),  # West
            (center_lat, center_lng)  # Center
        ]
        
        # Get elevation data for all points
        elevations = await self.get_elevation_google(sample_points)
        
        if len(elevations) < 5:
            return None
        
        # Calculate slope using finite difference method
        try:
            north_elev = elevations[0].elevation_m
            south_elev = elevations[1].elevation_m
            east_elev = elevations[2].elevation_m
            west_elev = elevations[3].elevation_m
            
            # Calculate gradients
            ns_gradient = (north_elev - south_elev) / (2 * radius_m)
            ew_gradient = (east_elev - west_elev) / (2 * radius_m)
            
            # Calculate slope magnitude and direction
            slope_radians = math.atan(math.sqrt(ns_gradient**2 + ew_gradient**2))
            slope_degrees = math.degrees(slope_radians)
            
            # Calculate aspect (direction of steepest descent)
            aspect_radians = math.atan2(ew_gradient, ns_gradient)
            aspect_degrees = (math.degrees(aspect_radians) + 360) % 360
            
            # Classify terrain type based on slope
            if slope_degrees < 2:
                terrain_type = TerrainType.FLAT
            elif slope_degrees < 8:
                terrain_type = TerrainType.ROLLING
            elif slope_degrees < 20:
                terrain_type = TerrainType.HILLY
            else:
                terrain_type = TerrainType.MOUNTAINOUS
            
            return SlopeData(
                location=Location(latitude=center_lat, longitude=center_lng),
                slope_degrees=slope_degrees,
                slope_percentage=math.tan(slope_radians) * 100,
                aspect_degrees=aspect_degrees,
                terrain_type=terrain_type,
                data_source="Calculated from Google Elevation API",
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Slope calculation failed", 
                       latitude=center_lat, longitude=center_lng, error=str(e))
            return None
    
    async def get_soil_data(self, latitude: float, longitude: float) -> Optional[SoilData]:
        """Get soil data using SoilGrids API.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            SoilData object or None if failed
        """
        # SoilGrids API endpoint for properties at specific location
        url = f"{self.soil_api_url}properties/query"
        params = {
            "lon": longitude,
            "lat": latitude,
            "property": "clay,sand,silt,phh2o,ocd",  # Clay, sand, silt, pH, organic carbon
            "depth": "0-5cm",  # Surface layer
            "value": "mean"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if "properties" in data:
                    props = data["properties"]
                    
                    # Extract soil composition
                    clay_percent = None
                    sand_percent = None
                    silt_percent = None
                    ph_level = None
                    organic_matter = None
                    
                    for prop in props:
                        if prop["name"] == "clay" and prop["depths"]:
                            clay_percent = prop["depths"][0]["values"]["mean"] / 10  # Convert to percentage
                        elif prop["name"] == "sand" and prop["depths"]:
                            sand_percent = prop["depths"][0]["values"]["mean"] / 10
                        elif prop["name"] == "silt" and prop["depths"]:
                            silt_percent = prop["depths"][0]["values"]["mean"] / 10
                        elif prop["name"] == "phh2o" and prop["depths"]:
                            ph_level = prop["depths"][0]["values"]["mean"] / 10
                        elif prop["name"] == "ocd" and prop["depths"]:
                            organic_matter = prop["depths"][0]["values"]["mean"] / 10
                    
                    # Determine dominant soil type
                    soil_type = SoilType.UNKNOWN
                    if clay_percent and sand_percent and silt_percent:
                        if clay_percent > 40:
                            soil_type = SoilType.CLAY
                        elif sand_percent > 70:
                            soil_type = SoilType.SAND
                        elif silt_percent > 40:
                            soil_type = SoilType.SILT
                        else:
                            soil_type = SoilType.LOAM
                    
                    return SoilData(
                        location=Location(latitude=latitude, longitude=longitude),
                        soil_type=soil_type,
                        ph_level=ph_level,
                        organic_matter_percent=organic_matter,
                        clay_percent=clay_percent,
                        sand_percent=sand_percent,
                        silt_percent=silt_percent,
                        data_source="SoilGrids API",
                        timestamp=datetime.utcnow()
                    )
                    
            except Exception as e:
                logger.error("Soil data API failed", 
                           latitude=latitude, longitude=longitude, error=str(e))
                
        return None
    
    async def calculate_distance_matrix(self, origin: Location, 
                                      destination: Location) -> Optional[DistanceMatrix]:
        """Calculate distance and travel time between locations.
        
        Args:
            origin: Origin location
            destination: Destination location
            
        Returns:
            DistanceMatrix object or None if calculation failed
        """
        if not self.google_api_key:
            raise GeospatialAPIError("Google API key required for distance calculation")
        
        url = f"{self.google_base_url}/distancematrix/json"
        params = {
            "origins": f"{origin.latitude},{origin.longitude}",
            "destinations": f"{destination.latitude},{destination.longitude}",
            "units": "metric",
            "key": self.google_api_key
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK" and data["rows"]:
                    element = data["rows"][0]["elements"][0]
                    
                    if element["status"] == "OK":
                        distance_m = element["distance"]["value"]
                        duration_s = element["duration"]["value"]
                        
                        return DistanceMatrix(
                            origin=origin,
                            destination=destination,
                            distance_km=distance_m / 1000,
                            duration_minutes=duration_s / 60,
                            route_type="driving",
                            status="OK"
                        )
                        
            except Exception as e:
                logger.error("Distance matrix calculation failed", error=str(e))
                
        return None
    
    async def analyze_site_comprehensive(self, location: Location) -> GeospatialAnalysis:
        """Perform comprehensive geospatial analysis of a site.
        
        Args:
            location: Site location to analyze
            
        Returns:
            GeospatialAnalysis with all available data
        """
        logger.info("Starting comprehensive site analysis", 
                   latitude=location.latitude, longitude=location.longitude)
        
        # Gather all geospatial data concurrently
        tasks = [
            self.get_elevation_google([(location.latitude, location.longitude)]),
            self.calculate_slope(location.latitude, location.longitude),
            self.get_soil_data(location.latitude, location.longitude)
        ]
        
        try:
            elevation_results, slope_data, soil_data = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process elevation data
            elevation_data = None
            if isinstance(elevation_results, list) and elevation_results:
                elevation_data = elevation_results[0]
            
            # Handle exceptions in results
            if isinstance(slope_data, Exception):
                logger.warning("Slope calculation failed", error=str(slope_data))
                slope_data = None
            
            if isinstance(soil_data, Exception):
                logger.warning("Soil data retrieval failed", error=str(soil_data))
                soil_data = None
            
            # Calculate terrain difficulty and accessibility
            difficulty_score = self._calculate_terrain_difficulty(
                elevation_data, slope_data, soil_data
            )
            
            accessibility = self._determine_accessibility(difficulty_score, slope_data)
            
            # Generate warnings and recommendations
            warnings = []
            recommendations = []
            
            if elevation_data and elevation_data.elevation_m > 2000:
                warnings.append("High altitude site may require specialized equipment")
                recommendations.append("Consider altitude-rated equipment and acclimatization")
            
            if slope_data and slope_data.slope_degrees > 15:
                warnings.append("Steep terrain may complicate installation")
                recommendations.append("Plan for specialized access equipment and safety measures")
            
            if soil_data and soil_data.soil_type == SoilType.CLAY:
                warnings.append("Clay soil may affect foundation stability")
                recommendations.append("Consider soil stabilization or alternative foundation methods")
            
            # Determine installation feasibility
            feasible = difficulty_score < 8 and accessibility != AccessibilityLevel.INACCESSIBLE
            
            # Calculate cost multiplier
            cost_multiplier = 1.0 + (difficulty_score / 10)
            
            return GeospatialAnalysis(
                location=location,
                elevation=elevation_data,
                slope=slope_data,
                soil=soil_data,
                accessibility=accessibility,
                terrain_difficulty_score=difficulty_score,
                installation_feasibility=feasible,
                estimated_cost_multiplier=cost_multiplier,
                warnings=warnings,
                recommendations=recommendations,
                analysis_timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error("Comprehensive site analysis failed", error=str(e))
            raise GeospatialAPIError(f"Site analysis failed: {str(e)}")
    
    def _calculate_terrain_difficulty(self, elevation: Optional[ElevationData], 
                                    slope: Optional[SlopeData], 
                                    soil: Optional[SoilData]) -> float:
        """Calculate terrain difficulty score (0-10)."""
        score = 0.0
        
        # Elevation factor
        if elevation:
            if elevation.elevation_m > 2500:
                score += 3.0
            elif elevation.elevation_m > 1500:
                score += 2.0
            elif elevation.elevation_m > 1000:
                score += 1.0
        
        # Slope factor
        if slope:
            if slope.slope_degrees > 25:
                score += 4.0
            elif slope.slope_degrees > 15:
                score += 2.5
            elif slope.slope_degrees > 8:
                score += 1.5
        
        # Soil factor
        if soil:
            if soil.soil_type in [SoilType.ROCK, SoilType.PEAT]:
                score += 2.0
            elif soil.soil_type == SoilType.CLAY:
                score += 1.0
        
        return min(score, 10.0)
    
    def _determine_accessibility(self, difficulty_score: float, 
                               slope: Optional[SlopeData]) -> AccessibilityLevel:
        """Determine site accessibility level."""
        if difficulty_score >= 8:
            return AccessibilityLevel.INACCESSIBLE
        elif difficulty_score >= 6:
            return AccessibilityLevel.DIFFICULT
        elif difficulty_score >= 4:
            return AccessibilityLevel.MODERATE
        elif difficulty_score >= 2:
            return AccessibilityLevel.GOOD
        else:
            return AccessibilityLevel.EXCELLENT