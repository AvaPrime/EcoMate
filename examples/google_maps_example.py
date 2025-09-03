#!/usr/bin/env python3
"""Example script demonstrating Google Maps API integration.

This script shows how to use the GOOGLE_API_KEY environment variable
with the EcoMate Google Maps utilities for geospatial operations.

Usage:
    1. Set your GOOGLE_API_KEY environment variable
    2. Run: python examples/google_maps_example.py

Requirements:
    - Valid Google Maps Platform API key
    - Enabled APIs: Geocoding, Distance Matrix, Elevation
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the ecomate-ai services to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "ecomate-ai"))

from services.utils.google_maps import (
    GoogleMapsClient,
    get_site_logistics_cost,
    validate_site_accessibility
)


async def demonstrate_geocoding():
    """Demonstrate address geocoding."""
    print("\n=== Geocoding Demo ===")
    
    client = GoogleMapsClient()
    
    # Test addresses in South Africa
    addresses = [
        "Cape Town, South Africa",
        "Johannesburg, South Africa",
        "Stellenbosch University, South Africa",
        "Table Mountain, Cape Town"
    ]
    
    for address in addresses:
        print(f"\nGeocoding: {address}")
        location = await client.geocode(address)
        
        if location:
            print(f"  ✓ Coordinates: {location.latitude:.4f}, {location.longitude:.4f}")
            print(f"  ✓ Formatted: {location.formatted_address}")
            
            # Reverse geocode to verify
            reverse_address = await client.reverse_geocode(location.latitude, location.longitude)
            print(f"  ✓ Reverse: {reverse_address}")
        else:
            print(f"  ✗ Could not geocode address")


async def demonstrate_distance_calculation():
    """Demonstrate distance and travel time calculation."""
    print("\n=== Distance Calculation Demo ===")
    
    client = GoogleMapsClient()
    
    # Calculate distances between major South African cities
    routes = [
        ("Cape Town, South Africa", "Stellenbosch, South Africa"),
        ("Cape Town, South Africa", "Johannesburg, South Africa"),
        ("Cape Town City Hall", "Table Mountain, Cape Town"),
        ("University of Cape Town", "Stellenbosch University")
    ]
    
    for origin, destination in routes:
        print(f"\nRoute: {origin} → {destination}")
        result = await client.calculate_distance(origin, destination)
        
        if result and result.status == "OK":
            print(f"  ✓ Distance: {result.distance_km:.1f} km")
            print(f"  ✓ Travel time: {result.duration_minutes:.0f} minutes")
            print(f"  ✓ Status: {result.status}")
        else:
            status = result.status if result else "API Error"
            print(f"  ✗ Could not calculate distance: {status}")


async def demonstrate_elevation_data():
    """Demonstrate elevation data retrieval."""
    print("\n=== Elevation Data Demo ===")
    
    client = GoogleMapsClient()
    
    # Test locations with varying elevations
    locations = [
        (-33.9249, 18.4241, "Cape Town City Hall"),
        (-33.9628, 18.4098, "Table Mountain Peak"),
        (-26.2041, 28.0473, "Johannesburg"),
        (-33.9321, 18.8602, "Stellenbosch")
    ]
    
    coords = [(lat, lng) for lat, lng, _ in locations]
    results = await client.get_elevation(coords)
    
    for i, (lat, lng, name) in enumerate(locations):
        if i < len(results):
            result = results[i]
            print(f"\n{name}:")
            print(f"  ✓ Coordinates: {lat:.4f}, {lng:.4f}")
            print(f"  ✓ Elevation: {result.elevation_m:.1f} meters")
            print(f"  ✓ Resolution: {result.resolution:.1f} meters")
        else:
            print(f"\n{name}: ✗ No elevation data")


async def demonstrate_site_logistics():
    """Demonstrate site logistics cost calculation."""
    print("\n=== Site Logistics Demo ===")
    
    # Test sites at different locations and elevations
    sites = [
        "Stellenbosch, South Africa",
        "Hermanus, South Africa",
        "Ceres, South Africa",  # Higher elevation
        "George, South Africa"
    ]
    
    depot = "Cape Town, South Africa"
    
    for site in sites:
        print(f"\nSite: {site}")
        result = await get_site_logistics_cost(site, depot)
        
        if "error" not in result:
            print(f"  ✓ Distance from depot: {result['distance_km']:.1f} km")
            print(f"  ✓ Travel time: {result['travel_time_minutes']:.0f} minutes")
            print(f"  ✓ Elevation: {result['elevation_m']:.0f} meters")
            print(f"  ✓ Terrain multiplier: {result['terrain_multiplier']:.2f}")
            print(f"  ✓ Logistics cost: R{result['logistics_cost_zar']:.2f}")
            print(f"  ✓ Coordinates: {result['site_coordinates']['latitude']:.4f}, {result['site_coordinates']['longitude']:.4f}")
        else:
            print(f"  ✗ Error: {result['error']}")


async def demonstrate_site_accessibility():
    """Demonstrate site accessibility validation."""
    print("\n=== Site Accessibility Demo ===")
    
    # Test sites with different accessibility challenges
    sites = [
        "Cape Town, South Africa",  # Sea level, accessible
        "Stellenbosch, South Africa",  # Low elevation, accessible
        "Ceres, South Africa",  # Medium elevation
        "Sutherland, South Africa",  # High elevation, may have warnings
    ]
    
    for site in sites:
        print(f"\nSite: {site}")
        result = await validate_site_accessibility(site)
        
        if result.get("accessible") is not None:
            accessibility = "✓ Accessible" if result["accessible"] else "✗ Not Accessible"
            print(f"  {accessibility}")
            print(f"  ✓ Elevation: {result['elevation_m']:.0f} meters")
            
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print(f"  ⚠ Warning: {warning}")
            
            print(f"  ✓ Coordinates: {result['coordinates']['latitude']:.4f}, {result['coordinates']['longitude']:.4f}")
        else:
            print(f"  ✗ Could not validate accessibility")


async def main():
    """Run all demonstration functions."""
    print("Google Maps API Integration Demo")
    print("=" * 40)
    
    # Check if API key is available
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("\n❌ ERROR: GOOGLE_API_KEY environment variable not set!")
        print("\nTo run this demo:")
        print("1. Get a Google Maps Platform API key from: https://console.cloud.google.com/")
        print("2. Enable the following APIs:")
        print("   - Geocoding API")
        print("   - Distance Matrix API")
        print("   - Elevation API")
        print("3. Set the environment variable:")
        print("   export GOOGLE_API_KEY='your-api-key-here'")
        print("4. Run this script again")
        return
    
    print(f"\n✓ Using API key: {api_key[:8]}...{api_key[-4:]}")
    
    try:
        # Run all demonstrations
        await demonstrate_geocoding()
        await demonstrate_distance_calculation()
        await demonstrate_elevation_data()
        await demonstrate_site_logistics()
        await demonstrate_site_accessibility()
        
        print("\n" + "=" * 40)
        print("✅ Demo completed successfully!")
        print("\nNext steps:")
        print("- Integrate these utilities into your EcoMate services")
        print("- Use geocoding for address validation in proposals")
        print("- Calculate logistics costs for site installations")
        print("- Validate site accessibility before equipment deployment")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("\nTroubleshooting:")
        print("- Verify your API key is valid")
        print("- Check that required APIs are enabled")
        print("- Ensure you have sufficient API quota")
        print("- Check your internet connection")


if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(main())