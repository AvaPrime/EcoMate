"""Google Maps API utilities for geospatial data integration.

This module provides functions for interacting with Google Maps Platform APIs
including Geocoding, Distance Matrix, and Elevation services.

Requires GOOGLE_API_KEY environment variable to be set.
"""

import os
import httpx
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Location:
    """Represents a geographic location."""
    latitude: float
    longitude: float
    address: Optional[str] = None
    formatted_address: Optional[str] = None


@dataclass
class DistanceResult:
    """Represents distance calculation result."""
    distance_km: float
    duration_minutes: float
    status: str


@dataclass
class ElevationResult:
    """Represents elevation data."""
    elevation_m: float
    resolution: float
    location: Location


class GoogleMapsClient:
    """Client for Google Maps Platform APIs."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Google Maps client.
        
        Args:
            api_key: Google Maps API key. If not provided, will use GOOGLE_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google Maps API key is required. Set GOOGLE_API_KEY environment variable.")
        
        self.base_url = "https://maps.googleapis.com/maps/api"
    
    async def geocode(self, address: str) -> Optional[Location]:
        """Geocode an address to get coordinates.
        
        Args:
            address: Address to geocode
            
        Returns:
            Location object with coordinates, or None if not found
        """
        url = f"{self.base_url}/geocode/json"
        params = {
            "address": address,
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
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
                        formatted_address=result["formatted_address"]
                    )
                    
            except Exception as e:
                print(f"Geocoding error for '{address}': {e}")
                
        return None
    
    async def reverse_geocode(self, latitude: float, longitude: float) -> Optional[str]:
        """Reverse geocode coordinates to get address.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Formatted address string, or None if not found
        """
        url = f"{self.base_url}/geocode/json"
        params = {
            "latlng": f"{latitude},{longitude}",
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK" and data["results"]:
                    return data["results"][0]["formatted_address"]
                    
            except Exception as e:
                print(f"Reverse geocoding error for {latitude},{longitude}: {e}")
                
        return None
    
    async def calculate_distance(self, origin: str, destination: str) -> Optional[DistanceResult]:
        """Calculate distance and travel time between two locations.
        
        Args:
            origin: Origin address or coordinates
            destination: Destination address or coordinates
            
        Returns:
            DistanceResult with distance and duration, or None if calculation failed
        """
        url = f"{self.base_url}/distancematrix/json"
        params = {
            "origins": origin,
            "destinations": destination,
            "units": "metric",
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK" and data["rows"]:
                    element = data["rows"][0]["elements"][0]
                    
                    if element["status"] == "OK":
                        distance_m = element["distance"]["value"]
                        duration_s = element["duration"]["value"]
                        
                        return DistanceResult(
                            distance_km=distance_m / 1000,
                            duration_minutes=duration_s / 60,
                            status="OK"
                        )
                    else:
                        return DistanceResult(
                            distance_km=0,
                            duration_minutes=0,
                            status=element["status"]
                        )
                        
            except Exception as e:
                print(f"Distance calculation error: {e}")
                
        return None
    
    async def get_elevation(self, locations: List[Tuple[float, float]]) -> List[ElevationResult]:
        """Get elevation data for multiple locations.
        
        Args:
            locations: List of (latitude, longitude) tuples
            
        Returns:
            List of ElevationResult objects
        """
        url = f"{self.base_url}/elevation/json"
        
        # Convert locations to string format
        locations_str = "|".join([f"{lat},{lng}" for lat, lng in locations])
        
        params = {
            "locations": locations_str,
            "key": self.api_key
        }
        
        results = []
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data["status"] == "OK":
                    for i, result in enumerate(data["results"]):
                        lat, lng = locations[i]
                        results.append(ElevationResult(
                            elevation_m=result["elevation"],
                            resolution=result["resolution"],
                            location=Location(latitude=lat, longitude=lng)
                        ))
                        
            except Exception as e:
                print(f"Elevation API error: {e}")
                
        return results


# Convenience functions for common operations
async def get_site_logistics_cost(site_address: str, depot_address: str = "Cape Town, South Africa") -> Dict:
    """Calculate logistics cost for a site installation.
    
    Args:
        site_address: Installation site address
        depot_address: Equipment depot address
        
    Returns:
        Dictionary with distance, travel time, and estimated logistics cost
    """
    client = GoogleMapsClient()
    
    # Get site coordinates for terrain analysis
    site_location = await client.geocode(site_address)
    if not site_location:
        return {"error": "Could not geocode site address"}
    
    # Calculate distance from depot
    distance_result = await client.calculate_distance(depot_address, site_address)
    if not distance_result:
        return {"error": "Could not calculate distance"}
    
    # Get elevation for terrain difficulty assessment
    elevation_results = await client.get_elevation([(site_location.latitude, site_location.longitude)])
    elevation = elevation_results[0].elevation_m if elevation_results else 0
    
    # Basic logistics cost calculation (can be enhanced with more factors)
    base_cost_per_km = 15.0  # ZAR per km
    terrain_multiplier = 1.0
    
    # Adjust for elevation (higher elevation = more difficult access)
    if elevation > 1500:  # High altitude
        terrain_multiplier = 1.3
    elif elevation > 1000:  # Medium altitude
        terrain_multiplier = 1.15
    
    logistics_cost = distance_result.distance_km * base_cost_per_km * terrain_multiplier
    
    return {
        "site_coordinates": {
            "latitude": site_location.latitude,
            "longitude": site_location.longitude
        },
        "distance_km": distance_result.distance_km,
        "travel_time_minutes": distance_result.duration_minutes,
        "elevation_m": elevation,
        "terrain_multiplier": terrain_multiplier,
        "logistics_cost_zar": round(logistics_cost, 2),
        "formatted_address": site_location.formatted_address
    }


async def validate_site_accessibility(site_address: str) -> Dict:
    """Validate if a site is accessible for equipment installation.
    
    Args:
        site_address: Site address to validate
        
    Returns:
        Dictionary with accessibility assessment
    """
    client = GoogleMapsClient()
    
    site_location = await client.geocode(site_address)
    if not site_location:
        return {"accessible": False, "reason": "Address not found"}
    
    # Get elevation data
    elevation_results = await client.get_elevation([(site_location.latitude, site_location.longitude)])
    elevation = elevation_results[0].elevation_m if elevation_results else 0
    
    # Basic accessibility rules (can be enhanced)
    accessible = True
    warnings = []
    
    if elevation > 2000:
        accessible = False
        warnings.append("Site elevation too high for standard equipment")
    elif elevation > 1500:
        warnings.append("High elevation may require specialized equipment")
    
    return {
        "accessible": accessible,
        "elevation_m": elevation,
        "warnings": warnings,
        "coordinates": {
            "latitude": site_location.latitude,
            "longitude": site_location.longitude
        },
        "formatted_address": site_location.formatted_address
    }