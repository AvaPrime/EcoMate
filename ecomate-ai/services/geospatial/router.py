"""FastAPI router for geospatial services.

This module provides REST API endpoints for geospatial data and analysis.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import JSONResponse
import structlog

from .client import GeospatialClient, GeospatialAPIError
from .models import (
    BatchGeospatialRequest,
    BatchGeospatialResponse,
    GeospatialQuery,
    GeospatialResponse,
    Location,
    SiteAssessment,
)
from .service import GeospatialService

logger = structlog.get_logger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/geospatial", tags=["geospatial"])

# Initialize service
geospatial_service = GeospatialService()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "geospatial",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.post("/geocode")
async def geocode_address(address: str) -> Dict:
    """Geocode an address to coordinates.
    
    Args:
        address: Address to geocode
        
    Returns:
        Location data with coordinates
    """
    try:
        location = await geospatial_service.client.geocode(address)
        
        if not location:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Address not found: {address}"
            )
        
        return {
            "success": True,
            "location": location.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Geocoding failed", address=address, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/reverse-geocode")
async def reverse_geocode_coordinates(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
) -> Dict:
    """Reverse geocode coordinates to address.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Address information
    """
    try:
        address = await geospatial_service.client.reverse_geocode(latitude, longitude)
        
        if not address:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No address found for coordinates: {latitude}, {longitude}"
            )
        
        return {
            "success": True,
            "address": address,
            "coordinates": {
                "latitude": latitude,
                "longitude": longitude
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Reverse geocoding failed", 
                   latitude=latitude, longitude=longitude, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/elevation")
async def get_elevation_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    source: str = Query("google", regex="^(google|usgs)$")
) -> Dict:
    """Get elevation data for coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        source: Data source (google or usgs)
        
    Returns:
        Elevation data
    """
    try:
        if source == "google":
            elevation_data = await geospatial_service.client.get_elevation_google(
                [(latitude, longitude)]
            )
            elevation = elevation_data[0] if elevation_data else None
        else:  # usgs
            elevation = await geospatial_service.client.get_elevation_usgs(
                latitude, longitude
            )
        
        if not elevation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Elevation data not available for coordinates: {latitude}, {longitude}"
            )
        
        return {
            "success": True,
            "elevation": elevation.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Elevation data retrieval failed", 
                   latitude=latitude, longitude=longitude, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/slope")
async def get_slope_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(100, ge=10, le=1000)
) -> Dict:
    """Get slope data for coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        radius_m: Radius for slope calculation in meters
        
    Returns:
        Slope analysis data
    """
    try:
        slope_data = await geospatial_service.client.calculate_slope(
            latitude, longitude, radius_m
        )
        
        if not slope_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Slope data not available for coordinates: {latitude}, {longitude}"
            )
        
        return {
            "success": True,
            "slope": slope_data.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Slope data calculation failed", 
                   latitude=latitude, longitude=longitude, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/soil")
async def get_soil_data(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
) -> Dict:
    """Get soil data for coordinates.
    
    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate
        
    Returns:
        Soil composition and properties
    """
    try:
        soil_data = await geospatial_service.client.get_soil_data(latitude, longitude)
        
        if not soil_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Soil data not available for coordinates: {latitude}, {longitude}"
            )
        
        return {
            "success": True,
            "soil": soil_data.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Soil data retrieval failed", 
                   latitude=latitude, longitude=longitude, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/distance-matrix")
async def calculate_distance_matrix(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180)
) -> Dict:
    """Calculate distance and travel time between two points.
    
    Args:
        origin_lat: Origin latitude
        origin_lng: Origin longitude
        dest_lat: Destination latitude
        dest_lng: Destination longitude
        
    Returns:
        Distance and travel time data
    """
    try:
        origin = Location(latitude=origin_lat, longitude=origin_lng)
        destination = Location(latitude=dest_lat, longitude=dest_lng)
        
        distance_matrix = await geospatial_service.client.calculate_distance_matrix(
            origin, destination
        )
        
        if not distance_matrix:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Distance calculation not available for the specified route"
            )
        
        return {
            "success": True,
            "distance_matrix": distance_matrix.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Distance matrix calculation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/site-assessment")
async def assess_site(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    address: Optional[str] = Query(None),
    include_logistics: bool = Query(True),
    depot_lat: Optional[float] = Query(None, ge=-90, le=90),
    depot_lng: Optional[float] = Query(None, ge=-180, le=180)
) -> Dict:
    """Perform comprehensive site assessment.
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        address: Optional site address
        include_logistics: Whether to include logistics analysis
        depot_lat: Depot latitude (required if include_logistics=True)
        depot_lng: Depot longitude (required if include_logistics=True)
        
    Returns:
        Complete site assessment
    """
    try:
        location = Location(
            latitude=latitude,
            longitude=longitude,
            address=address
        )
        
        depot_location = None
        if include_logistics:
            if depot_lat is None or depot_lng is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Depot coordinates required when include_logistics=True"
                )
            depot_location = Location(latitude=depot_lat, longitude=depot_lng)
        
        assessment = await geospatial_service.assess_site(
            location, include_logistics, depot_location
        )
        
        return {
            "success": True,
            "assessment": assessment.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Site assessment failed", 
                   latitude=latitude, longitude=longitude, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/logistics-cost")
async def calculate_logistics_cost(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    dest_lat: float = Query(..., ge=-90, le=90),
    dest_lng: float = Query(..., ge=-180, le=180),
    equipment_weight_kg: float = Query(1000, ge=0),
    crew_size: int = Query(4, ge=1, le=20)
) -> Dict:
    """Calculate logistics cost for site access.
    
    Args:
        origin_lat: Origin latitude (depot)
        origin_lng: Origin longitude (depot)
        dest_lat: Destination latitude (site)
        dest_lng: Destination longitude (site)
        equipment_weight_kg: Weight of equipment to transport
        crew_size: Number of crew members
        
    Returns:
        Detailed logistics cost breakdown
    """
    try:
        origin = Location(latitude=origin_lat, longitude=origin_lng)
        destination = Location(latitude=dest_lat, longitude=dest_lng)
        
        logistics_cost = await geospatial_service.calculate_logistics_cost(
            origin, destination, equipment_weight_kg, crew_size
        )
        
        return {
            "success": True,
            "logistics_cost": logistics_cost.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Logistics cost calculation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/comprehensive-analysis")
async def comprehensive_site_analysis(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    address: Optional[str] = Query(None)
) -> Dict:
    """Perform comprehensive geospatial analysis.
    
    Args:
        latitude: Site latitude
        longitude: Site longitude
        address: Optional site address
        
    Returns:
        Complete geospatial analysis
    """
    try:
        location = Location(
            latitude=latitude,
            longitude=longitude,
            address=address
        )
        
        analysis = await geospatial_service.client.analyze_site_comprehensive(location)
        
        return {
            "success": True,
            "analysis": analysis.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Comprehensive analysis failed", 
                   latitude=latitude, longitude=longitude, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/query", response_model=GeospatialResponse)
async def process_geospatial_query(query: GeospatialQuery) -> GeospatialResponse:
    """Process a geospatial query request.
    
    Args:
        query: Geospatial query parameters
        
    Returns:
        Geospatial response with requested data
    """
    try:
        response = await geospatial_service.process_geospatial_query(query)
        return response
        
    except GeospatialAPIError as e:
        logger.error("Geospatial query processing failed", 
                   query_id=query.query_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/batch", response_model=BatchGeospatialResponse)
async def process_batch_request(request: BatchGeospatialRequest) -> BatchGeospatialResponse:
    """Process batch geospatial requests.
    
    Args:
        request: Batch request with multiple queries
        
    Returns:
        Batch response with all results
    """
    try:
        response = await geospatial_service.process_batch_request(request)
        return response
        
    except GeospatialAPIError as e:
        logger.error("Batch request processing failed", 
                   batch_id=request.batch_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/optimal-sites")
async def find_optimal_sites(
    candidate_locations: List[Dict],
    depot_lat: float = Query(..., ge=-90, le=90),
    depot_lng: float = Query(..., ge=-180, le=180),
    max_sites: int = Query(5, ge=1, le=20),
    weight_accessibility: float = Query(0.3, ge=0, le=1),
    weight_cost: float = Query(0.4, ge=0, le=1),
    weight_terrain: float = Query(0.3, ge=0, le=1)
) -> Dict:
    """Find optimal sites from candidate locations.
    
    Args:
        candidate_locations: List of candidate site locations
        depot_lat: Depot latitude
        depot_lng: Depot longitude
        max_sites: Maximum number of sites to return
        weight_accessibility: Weight for accessibility score
        weight_cost: Weight for cost score
        weight_terrain: Weight for terrain score
        
    Returns:
        List of top-ranked site assessments
    """
    try:
        # Validate weights sum to 1.0
        total_weight = weight_accessibility + weight_cost + weight_terrain
        if abs(total_weight - 1.0) > 0.01:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weights must sum to 1.0"
            )
        
        # Convert candidate locations to Location objects
        locations = []
        for loc_data in candidate_locations:
            try:
                location = Location(**loc_data)
                locations.append(location)
            except ValidationError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid location data: {str(e)}"
                )
        
        depot_location = Location(latitude=depot_lat, longitude=depot_lng)
        
        optimal_sites = await geospatial_service.find_optimal_sites(
            locations, depot_location, max_sites,
            weight_accessibility, weight_cost, weight_terrain
        )
        
        return {
            "success": True,
            "optimal_sites": [site.dict() for site in optimal_sites],
            "total_candidates": len(candidate_locations),
            "selected_sites": len(optimal_sites),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except GeospatialAPIError as e:
        logger.error("Optimal site finding failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/capabilities")
async def get_service_capabilities() -> Dict:
    """Get geospatial service capabilities and API information.
    
    Returns:
        Service capabilities and available endpoints
    """
    return {
        "service": "EcoMate Geospatial API",
        "version": "1.0.0",
        "capabilities": {
            "geocoding": {
                "providers": ["Google Maps"],
                "features": ["address_to_coordinates", "coordinates_to_address"]
            },
            "elevation": {
                "providers": ["Google Elevation API", "USGS"],
                "features": ["point_elevation", "batch_elevation"]
            },
            "terrain": {
                "features": ["slope_calculation", "terrain_classification", "aspect_analysis"]
            },
            "soil": {
                "providers": ["SoilGrids"],
                "features": ["soil_composition", "ph_analysis", "organic_matter"]
            },
            "logistics": {
                "features": ["distance_calculation", "cost_estimation", "route_analysis"]
            },
            "analysis": {
                "features": [
                    "comprehensive_site_assessment",
                    "batch_processing",
                    "optimal_site_selection",
                    "accessibility_scoring"
                ]
            }
        },
        "data_sources": [
            "Google Maps Platform",
            "Google Elevation API",
            "USGS Elevation Point Query Service",
            "SoilGrids (ISRIC)"
        ],
        "coordinate_systems": ["WGS84"],
        "rate_limits": {
            "note": "Rate limits depend on external API providers",
            "batch_max_concurrent": 10,
            "batch_max_queries": 100
        },
        "timestamp": datetime.utcnow().isoformat()
    }