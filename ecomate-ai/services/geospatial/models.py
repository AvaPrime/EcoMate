"""Geospatial data models for EcoMate AI.

This module defines Pydantic models for geospatial data integration
including Google Maps, elevation, slope, and soil data APIs.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class CoordinateSystem(str, Enum):
    """Supported coordinate systems."""
    WGS84 = "WGS84"
    UTM = "UTM"
    EPSG4326 = "EPSG:4326"
    EPSG3857 = "EPSG:3857"


class TerrainType(str, Enum):
    """Terrain classification types."""
    FLAT = "flat"
    ROLLING = "rolling"
    HILLY = "hilly"
    MOUNTAINOUS = "mountainous"
    COASTAL = "coastal"
    URBAN = "urban"
    RURAL = "rural"


class SoilType(str, Enum):
    """Soil classification types."""
    CLAY = "clay"
    SAND = "sand"
    LOAM = "loam"
    SILT = "silt"
    PEAT = "peat"
    ROCK = "rock"
    UNKNOWN = "unknown"


class AccessibilityLevel(str, Enum):
    """Site accessibility levels."""
    EXCELLENT = "excellent"
    GOOD = "good"
    MODERATE = "moderate"
    DIFFICULT = "difficult"
    INACCESSIBLE = "inaccessible"


class Location(BaseModel):
    """Geographic location with coordinates."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    address: Optional[str] = Field(None, description="Human-readable address")
    formatted_address: Optional[str] = Field(None, description="Formatted address from geocoding")
    coordinate_system: CoordinateSystem = Field(default=CoordinateSystem.WGS84)
    accuracy_m: Optional[float] = Field(None, description="Location accuracy in meters")

    class Config:
        schema_extra = {
            "example": {
                "latitude": -33.9249,
                "longitude": 18.4241,
                "address": "Cape Town, South Africa",
                "coordinate_system": "WGS84"
            }
        }


class ElevationData(BaseModel):
    """Elevation information for a location."""
    location: Location
    elevation_m: float = Field(..., description="Elevation above sea level in meters")
    resolution_m: Optional[float] = Field(None, description="Data resolution in meters")
    data_source: Optional[str] = Field(None, description="Source of elevation data")
    timestamp: Optional[datetime] = Field(None, description="When data was retrieved")


class SlopeData(BaseModel):
    """Slope analysis data."""
    location: Location
    slope_degrees: float = Field(..., ge=0, le=90, description="Slope angle in degrees")
    slope_percentage: float = Field(..., ge=0, description="Slope as percentage")
    aspect_degrees: Optional[float] = Field(None, ge=0, le=360, description="Slope aspect in degrees")
    terrain_type: TerrainType
    data_source: Optional[str] = Field(None)
    timestamp: Optional[datetime] = Field(None)

    @validator('slope_percentage', pre=True, always=True)
    def calculate_slope_percentage(cls, v, values):
        """Calculate slope percentage from degrees if not provided."""
        if v is None and 'slope_degrees' in values:
            import math
            return math.tan(math.radians(values['slope_degrees'])) * 100
        return v


class SoilData(BaseModel):
    """Soil composition and properties."""
    location: Location
    soil_type: SoilType
    ph_level: Optional[float] = Field(None, ge=0, le=14, description="Soil pH level")
    organic_matter_percent: Optional[float] = Field(None, ge=0, le=100)
    clay_percent: Optional[float] = Field(None, ge=0, le=100)
    sand_percent: Optional[float] = Field(None, ge=0, le=100)
    silt_percent: Optional[float] = Field(None, ge=0, le=100)
    drainage_class: Optional[str] = Field(None, description="Soil drainage classification")
    bearing_capacity_kpa: Optional[float] = Field(None, description="Soil bearing capacity in kPa")
    data_source: Optional[str] = Field(None)
    timestamp: Optional[datetime] = Field(None)


class GeospatialAnalysis(BaseModel):
    """Comprehensive geospatial analysis result."""
    location: Location
    elevation: Optional[ElevationData] = None
    slope: Optional[SlopeData] = None
    soil: Optional[SoilData] = None
    accessibility: AccessibilityLevel
    terrain_difficulty_score: float = Field(..., ge=0, le=10, description="Terrain difficulty (0=easy, 10=impossible)")
    installation_feasibility: bool = Field(..., description="Whether installation is feasible")
    estimated_cost_multiplier: float = Field(..., ge=1.0, description="Cost multiplier due to terrain")
    warnings: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.utcnow)


class DistanceMatrix(BaseModel):
    """Distance and travel time between locations."""
    origin: Location
    destination: Location
    distance_km: float = Field(..., ge=0)
    duration_minutes: float = Field(..., ge=0)
    route_type: Optional[str] = Field(None, description="Type of route (driving, walking, etc.)")
    traffic_model: Optional[str] = Field(None)
    status: str = Field(..., description="API response status")


class LogisticsCost(BaseModel):
    """Logistics cost calculation for site access."""
    site_location: Location
    depot_location: Location
    distance_matrix: DistanceMatrix
    base_cost_per_km: float = Field(..., description="Base transportation cost per km")
    terrain_multiplier: float = Field(..., ge=1.0)
    accessibility_multiplier: float = Field(..., ge=1.0)
    total_logistics_cost: float = Field(..., description="Total logistics cost")
    currency: str = Field(default="ZAR")
    breakdown: Dict[str, float] = Field(default_factory=dict)


class GeospatialQuery(BaseModel):
    """Query parameters for geospatial analysis."""
    locations: List[Location] = Field(..., min_items=1, max_items=100)
    include_elevation: bool = Field(default=True)
    include_slope: bool = Field(default=True)
    include_soil: bool = Field(default=True)
    include_logistics: bool = Field(default=False)
    depot_location: Optional[Location] = Field(None, description="Depot for logistics calculation")
    analysis_radius_m: Optional[float] = Field(None, description="Analysis radius in meters")


class GeospatialResponse(BaseModel):
    """Response containing geospatial analysis results."""
    query: GeospatialQuery
    results: List[GeospatialAnalysis]
    logistics_costs: Optional[List[LogisticsCost]] = None
    summary: Dict[str, Union[int, float, str]] = Field(default_factory=dict)
    processing_time_ms: Optional[float] = None
    api_calls_made: Dict[str, int] = Field(default_factory=dict)
    errors: List[str] = Field(default_factory=list)


class SiteAssessment(BaseModel):
    """Comprehensive site assessment for equipment installation."""
    site_id: str
    location: Location
    geospatial_analysis: GeospatialAnalysis
    logistics_cost: Optional[LogisticsCost] = None
    equipment_requirements: List[str] = Field(default_factory=list)
    installation_timeline_days: Optional[int] = None
    risk_factors: List[str] = Field(default_factory=list)
    mitigation_strategies: List[str] = Field(default_factory=list)
    overall_score: float = Field(..., ge=0, le=100, description="Overall site suitability score")
    recommendation: str
    assessment_date: datetime = Field(default_factory=datetime.utcnow)


class BatchGeospatialRequest(BaseModel):
    """Request for batch geospatial processing."""
    sites: List[Dict[str, Union[str, float]]] = Field(..., description="List of sites with addresses or coordinates")
    analysis_type: str = Field(default="full", description="Type of analysis to perform")
    depot_address: Optional[str] = Field(None, description="Depot address for logistics")
    include_detailed_soil: bool = Field(default=False)
    include_slope_analysis: bool = Field(default=True)
    priority: str = Field(default="normal", description="Processing priority")


class BatchGeospatialResponse(BaseModel):
    """Response for batch geospatial processing."""
    request_id: str
    total_sites: int
    processed_sites: int
    failed_sites: int
    site_assessments: List[SiteAssessment]
    processing_summary: Dict[str, Union[int, float, str]]
    total_processing_time_ms: float
    api_usage_summary: Dict[str, int]
    errors: List[Dict[str, str]] = Field(default_factory=list)