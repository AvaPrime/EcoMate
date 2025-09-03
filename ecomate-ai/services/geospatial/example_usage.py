#!/usr/bin/env python3
"""
Geospatial Service Usage Examples

This script demonstrates the comprehensive capabilities of the EcoMate AI
geospatial service, including site assessment, batch processing, and
optimal site selection.

Requirements:
- GOOGLE_API_KEY environment variable (recommended)
- Internet connection for API calls
- All dependencies from requirements.txt

Usage:
    python services/geospatial/example_usage.py
"""

import asyncio
import os
from datetime import datetime
from uuid import uuid4

from client import GeospatialClient
from models import (
    BatchGeospatialRequest,
    GeospatialQuery,
    Location,
)
from service import GeospatialService


async def demonstrate_basic_geocoding():
    """Demonstrate basic geocoding and reverse geocoding."""
    print("\n=== Basic Geocoding Demo ===")
    
    client = GeospatialClient()
    
    # Geocode an address
    address = "Times Square, New York, NY"
    print(f"Geocoding: {address}")
    
    location = await client.geocode(address)
    if location:
        print(f"  Coordinates: {location.latitude:.6f}, {location.longitude:.6f}")
        print(f"  Formatted Address: {location.formatted_address}")
        
        # Reverse geocode the coordinates
        print(f"\nReverse geocoding: {location.latitude:.6f}, {location.longitude:.6f}")
        reverse_location = await client.reverse_geocode(location.latitude, location.longitude)
        if reverse_location:
            print(f"  Address: {reverse_location.formatted_address}")
    else:
        print("  Geocoding failed")


async def demonstrate_elevation_analysis():
    """Demonstrate elevation data retrieval from multiple sources."""
    print("\n=== Elevation Analysis Demo ===")
    
    client = GeospatialClient()
    
    # Test coordinates (Mount Washington, NH)
    test_coords = [(44.2706, -71.3033)]
    print(f"Analyzing elevation at: {test_coords[0]}")
    
    # Google Elevation API (if available)
    if client.google_api_key:
        print("\nGoogle Elevation API:")
        try:
            elevations = await client.get_elevation_google(test_coords)
            if elevations:
                elevation = elevations[0]
                print(f"  Elevation: {elevation.elevation_m:.1f}m")
                print(f"  Resolution: {elevation.resolution_m:.1f}m")
                print(f"  Source: {elevation.data_source}")
        except Exception as e:
            print(f"  Error: {e}")
    
    # USGS Elevation (free, US only)
    print("\nUSGS Elevation Service:")
    try:
        elevation = await client.get_elevation_usgs(test_coords[0][0], test_coords[0][1])
        if elevation:
            print(f"  Elevation: {elevation.elevation_m:.1f}m")
            print(f"  Source: {elevation.data_source}")
    except Exception as e:
        print(f"  Error: {e}")


async def demonstrate_terrain_analysis():
    """Demonstrate slope calculation and terrain classification."""
    print("\n=== Terrain Analysis Demo ===")
    
    client = GeospatialClient()
    
    # Test location (hilly area)
    lat, lng = 40.7128, -74.0060  # New York City
    print(f"Analyzing terrain at: {lat:.6f}, {lng:.6f}")
    
    if client.google_api_key:
        try:
            slope_data = await client.calculate_slope(lat, lng)
            if slope_data:
                print(f"  Slope: {slope_data.slope_degrees:.2f}° ({slope_data.slope_percentage:.1f}%)")
                print(f"  Aspect: {slope_data.aspect_degrees:.1f}°")
                print(f"  Terrain Type: {slope_data.terrain_type.value}")
                print(f"  Source: {slope_data.data_source}")
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print("  Google API key required for slope analysis")


async def demonstrate_soil_analysis():
    """Demonstrate soil data retrieval and analysis."""
    print("\n=== Soil Analysis Demo ===")
    
    client = GeospatialClient()
    
    # Test location (agricultural area)
    lat, lng = 40.7128, -74.0060
    print(f"Analyzing soil at: {lat:.6f}, {lng:.6f}")
    
    try:
        soil_data = await client.get_soil_data(lat, lng)
        if soil_data:
            print(f"  Soil Type: {soil_data.soil_type.value}")
            print(f"  pH Level: {soil_data.ph_level:.1f}")
            print(f"  Clay: {soil_data.clay_percent:.1f}%")
            print(f"  Sand: {soil_data.sand_percent:.1f}%")
            print(f"  Silt: {soil_data.silt_percent:.1f}%")
            print(f"  Source: {soil_data.data_source}")
    except Exception as e:
        print(f"  Error: {e}")


async def demonstrate_comprehensive_site_assessment():
    """Demonstrate comprehensive site assessment."""
    print("\n=== Comprehensive Site Assessment Demo ===")
    
    client = GeospatialClient()
    service = GeospatialService(client=client)
    
    # Test location
    location = Location(latitude=40.7128, longitude=-74.0060, address="New York, NY")
    depot_location = Location(latitude=40.7500, longitude=-74.0000, address="Depot Location")
    
    print(f"Assessing site: {location.address}")
    print(f"Depot location: {depot_location.address}")
    
    try:
        assessment = await service.assess_site(
            location=location,
            include_logistics=True,
            depot_location=depot_location
        )
        
        print(f"\nAssessment Results:")
        print(f"  Project Viable: {assessment.project_viable}")
        print(f"  Confidence Score: {assessment.confidence_score:.2f}")
        
        if assessment.geospatial_analysis:
            analysis = assessment.geospatial_analysis
            print(f"  Accessibility: {analysis.accessibility.value}")
            print(f"  Installation Feasibility: {analysis.installation_feasibility}")
            print(f"  Terrain Difficulty: {analysis.terrain_difficulty_score:.1f}/10")
            
            if analysis.warnings:
                print(f"  Warnings: {', '.join(analysis.warnings)}")
            
            if analysis.recommendations:
                print(f"  Recommendations: {', '.join(analysis.recommendations)}")
        
        if assessment.logistics_cost:
            cost = assessment.logistics_cost
            print(f"\nLogistics Analysis:")
            print(f"  Distance: {cost.distance_km:.1f} km")
            print(f"  Travel Time: {cost.travel_time_hours:.1f} hours")
            print(f"  Total Cost: ${cost.total_cost_usd:.2f}")
            print(f"  Base Cost: ${cost.base_cost_usd:.2f}")
            print(f"  Distance Cost: ${cost.distance_cost_usd:.2f}")
            print(f"  Time Cost: ${cost.time_cost_usd:.2f}")
            print(f"  Elevation Cost: ${cost.elevation_cost_usd:.2f}")
            print(f"  Terrain Cost: ${cost.terrain_cost_usd:.2f}")
    
    except Exception as e:
        print(f"  Error: {e}")


async def demonstrate_batch_processing():
    """Demonstrate batch processing of multiple geospatial queries."""
    print("\n=== Batch Processing Demo ===")
    
    client = GeospatialClient()
    service = GeospatialService(client=client)
    
    # Create multiple queries
    locations = [
        Location(address="New York, NY"),
        Location(address="Los Angeles, CA"),
        Location(address="Chicago, IL"),
        Location(latitude=40.7128, longitude=-74.0060),
        Location(latitude=34.0522, longitude=-118.2437)
    ]
    
    queries = []
    for i, location in enumerate(locations):
        query = GeospatialQuery(
            query_id=f"query-{i+1:03d}",
            locations=[location],
            data_types=["elevation", "slope", "soil"],
            timestamp=datetime.utcnow()
        )
        queries.append(query)
    
    batch_request = BatchGeospatialRequest(
        batch_id=str(uuid4()),
        queries=queries,
        max_concurrent_requests=3,
        timestamp=datetime.utcnow()
    )
    
    print(f"Processing batch with {len(queries)} queries...")
    
    try:
        batch_response = await service.process_batch_request(batch_request)
        
        print(f"\nBatch Results:")
        print(f"  Total Queries: {batch_response.total_queries}")
        print(f"  Successful: {batch_response.successful_queries}")
        print(f"  Failed: {batch_response.failed_queries_count}")
        print(f"  Processing Time: {batch_response.processing_time_seconds:.2f}s")
        
        if batch_response.failed_queries:
            print(f"  Failed Query IDs: {', '.join(batch_response.failed_queries)}")
    
    except Exception as e:
        print(f"  Error: {e}")


async def demonstrate_optimal_site_selection():
    """Demonstrate optimal site selection from multiple candidates."""
    print("\n=== Optimal Site Selection Demo ===")
    
    client = GeospatialClient()
    service = GeospatialService(client=client)
    
    # Candidate locations
    candidate_locations = [
        Location(latitude=40.7128, longitude=-74.0060, address="New York, NY"),
        Location(latitude=40.7589, longitude=-73.9851, address="Central Park, NY"),
        Location(latitude=40.6892, longitude=-74.0445, address="Statue of Liberty, NY"),
        Location(latitude=40.7505, longitude=-73.9934, address="Times Square, NY"),
        Location(latitude=40.7282, longitude=-73.7949, address="JFK Airport, NY")
    ]
    
    depot_location = Location(latitude=40.7500, longitude=-74.0000, address="Depot")
    
    print(f"Evaluating {len(candidate_locations)} candidate sites...")
    print(f"Depot location: {depot_location.address}")
    
    try:
        optimal_sites = await service.find_optimal_sites(
            candidate_locations=candidate_locations,
            depot_location=depot_location,
            max_sites=3,
            weights={
                "accessibility": 0.3,
                "cost": 0.4,
                "terrain": 0.3
            }
        )
        
        print(f"\nTop {len(optimal_sites)} Optimal Sites:")
        for i, site in enumerate(optimal_sites, 1):
            print(f"\n  Rank {i}: {site.geospatial_analysis.location.address}")
            print(f"    Viable: {site.project_viable}")
            print(f"    Confidence: {site.confidence_score:.2f}")
            print(f"    Accessibility: {site.geospatial_analysis.accessibility.value}")
            if site.logistics_cost:
                print(f"    Cost: ${site.logistics_cost.total_cost_usd:.2f}")
                print(f"    Distance: {site.logistics_cost.distance_km:.1f} km")
    
    except Exception as e:
        print(f"  Error: {e}")


async def demonstrate_distance_matrix():
    """Demonstrate distance matrix calculations."""
    print("\n=== Distance Matrix Demo ===")
    
    client = GeospatialClient()
    
    if not client.google_api_key:
        print("  Google API key required for distance matrix")
        return
    
    origin = Location(latitude=40.7128, longitude=-74.0060, address="New York, NY")
    destination = Location(latitude=40.7589, longitude=-73.9851, address="Central Park, NY")
    
    print(f"Calculating distance from {origin.address} to {destination.address}")
    
    try:
        distance_matrix = await client.calculate_distance_matrix(origin, destination)
        
        if distance_matrix:
            print(f"  Distance: {distance_matrix.distance_km:.2f} km")
            print(f"  Duration: {distance_matrix.duration_minutes:.1f} minutes")
            print(f"  Status: {distance_matrix.status}")
    
    except Exception as e:
        print(f"  Error: {e}")


async def main():
    """Run all demonstration functions."""
    print("EcoMate AI Geospatial Service Demonstration")
    print("===========================================")
    
    # Check for API key
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if google_api_key:
        print(f"✓ Google API Key found (length: {len(google_api_key)})")
    else:
        print("⚠ Google API Key not found - some features will be limited")
        print("  Set GOOGLE_API_KEY environment variable for full functionality")
    
    # Run demonstrations
    demonstrations = [
        demonstrate_basic_geocoding,
        demonstrate_elevation_analysis,
        demonstrate_terrain_analysis,
        demonstrate_soil_analysis,
        demonstrate_distance_matrix,
        demonstrate_comprehensive_site_assessment,
        demonstrate_batch_processing,
        demonstrate_optimal_site_selection
    ]
    
    for demo_func in demonstrations:
        try:
            await demo_func()
        except Exception as e:
            print(f"\nError in {demo_func.__name__}: {e}")
        
        # Small delay between demonstrations
        await asyncio.sleep(1)
    
    print("\n=== Demonstration Complete ===")
    print("\nFor more information:")
    print("- Check README.md for detailed documentation")
    print("- Run tests with: pytest test_geospatial.py")
    print("- View API endpoints in router.py")


if __name__ == "__main__":
    # Check if running in the correct directory
    if not os.path.exists("client.py"):
        print("Error: Please run this script from the services/geospatial directory")
        print("Usage: cd services/geospatial && python example_usage.py")
        exit(1)
    
    # Run the demonstration
    asyncio.run(main())