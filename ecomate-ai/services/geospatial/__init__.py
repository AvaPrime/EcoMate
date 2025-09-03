"""EcoMate AI Geospatial Services.

This package provides comprehensive geospatial data integration and analysis
for the EcoMate AI platform, including:

- Multi-provider API integration (Google Maps, USGS, SoilGrids)
- Elevation and terrain analysis
- Soil composition and properties
- Site accessibility assessment
- Logistics cost calculation
- Batch processing capabilities
- Optimal site selection

Main Components:
- GeospatialClient: Low-level API client
- GeospatialService: High-level service layer
- FastAPI Router: REST API endpoints
- Pydantic Models: Data validation and serialization

Usage:
    from services.geospatial import GeospatialService, GeospatialClient
    from services.geospatial.models import Location, SiteAssessment
    
    # Initialize service
    service = GeospatialService()
    
    # Assess a site
    location = Location(latitude=40.7128, longitude=-74.0060)
    assessment = await service.assess_site(location)
"""

from .client import GeospatialClient, GeospatialAPIError
from .service import GeospatialService
from .router import router as geospatial_router
from .models import (
    # Core data models
    Location,
    ElevationData,
    SlopeData,
    SoilData,
    GeospatialAnalysis,
    SiteAssessment,
    LogisticsCost,
    DistanceMatrix,
    
    # Request/Response models
    GeospatialQuery,
    GeospatialResponse,
    BatchGeospatialRequest,
    BatchGeospatialResponse,
    
    # Enumerations
    CoordinateSystem,
    TerrainType,
    SoilType,
    AccessibilityLevel,
)

__version__ = "1.0.0"
__author__ = "EcoMate AI Team"
__description__ = "Comprehensive geospatial services for EcoMate AI"

# Package metadata
__all__ = [
    # Main classes
    "GeospatialClient",
    "GeospatialService",
    "GeospatialAPIError",
    "geospatial_router",
    
    # Data models
    "Location",
    "ElevationData",
    "SlopeData",
    "SoilData",
    "GeospatialAnalysis",
    "SiteAssessment",
    "LogisticsCost",
    "DistanceMatrix",
    
    # Request/Response models
    "GeospatialQuery",
    "GeospatialResponse",
    "BatchGeospatialRequest",
    "BatchGeospatialResponse",
    
    # Enumerations
    "CoordinateSystem",
    "TerrainType",
    "SoilType",
    "AccessibilityLevel",
]

# Service configuration
DEFAULT_CONFIG = {
    "timeout": 30,
    "max_concurrent_requests": 10,
    "batch_size_limit": 100,
    "cache_ttl_seconds": 3600,
    "retry_attempts": 3,
    "retry_delay_seconds": 1,
}

# API provider information
API_PROVIDERS = {
    "google_maps": {
        "name": "Google Maps Platform",
        "services": ["geocoding", "elevation", "distance_matrix"],
        "requires_api_key": True,
        "rate_limits": "Varies by service",
        "documentation": "https://developers.google.com/maps/documentation"
    },
    "usgs": {
        "name": "USGS Elevation Point Query Service",
        "services": ["elevation"],
        "requires_api_key": False,
        "rate_limits": "No official limits",
        "documentation": "https://nationalmap.gov/epqs/"
    },
    "soilgrids": {
        "name": "SoilGrids (ISRIC)",
        "services": ["soil_properties"],
        "requires_api_key": False,
        "rate_limits": "Fair use policy",
        "documentation": "https://rest.isric.org/soilgrids/v2.0/docs"
    }
}

# Convenience functions
def create_service(google_api_key: str = None, **kwargs) -> GeospatialService:
    """Create a configured GeospatialService instance.
    
    Args:
        google_api_key: Google Maps API key
        **kwargs: Additional configuration options
        
    Returns:
        Configured GeospatialService instance
    """
    client = GeospatialClient(google_api_key=google_api_key, **kwargs)
    return GeospatialService(client)


def get_api_requirements() -> dict:
    """Get API key requirements and setup information.
    
    Returns:
        Dictionary with API setup information
    """
    return {
        "required_keys": {
            "GOOGLE_API_KEY": {
                "required_for": ["geocoding", "elevation", "distance_matrix"],
                "setup_url": "https://console.cloud.google.com/apis/credentials",
                "apis_to_enable": [
                    "Maps JavaScript API",
                    "Geocoding API",
                    "Elevation API",
                    "Distance Matrix API"
                ]
            }
        },
        "optional_keys": {
            "USGS_API_KEY": {
                "required_for": ["usgs_elevation"],
                "note": "Not currently required, but may be needed for enhanced access"
            },
            "OPEN_TOPO_API_KEY": {
                "required_for": ["advanced_elevation"],
                "note": "For future OpenTopography integration"
            }
        },
        "environment_setup": {
            "description": "Set environment variables or pass keys to client constructor",
            "example": "export GOOGLE_API_KEY=your_api_key_here"
        }
    }


def get_service_info() -> dict:
    """Get comprehensive service information.
    
    Returns:
        Dictionary with service capabilities and information
    """
    return {
        "version": __version__,
        "description": __description__,
        "capabilities": {
            "geocoding": "Convert addresses to coordinates and vice versa",
            "elevation": "Get elevation data from multiple sources",
            "terrain_analysis": "Calculate slope, aspect, and terrain classification",
            "soil_analysis": "Retrieve soil composition and properties",
            "site_assessment": "Comprehensive site evaluation for installations",
            "logistics_costing": "Calculate transportation and access costs",
            "batch_processing": "Process multiple locations efficiently",
            "optimal_selection": "Find best sites from candidate locations"
        },
        "data_sources": list(API_PROVIDERS.keys()),
        "supported_formats": ["JSON", "Pydantic models"],
        "coordinate_systems": ["WGS84"],
        "api_endpoints": [
            "/geocode",
            "/reverse-geocode",
            "/elevation",
            "/slope",
            "/soil",
            "/site-assessment",
            "/logistics-cost",
            "/comprehensive-analysis",
            "/batch",
            "/optimal-sites"
        ]
    }