"""Climate data models for weather and environmental data integration.

This module defines Pydantic models for climate data from various sources
including Open-Meteo, NASA POWER, and other weather APIs.
"""

from datetime import datetime, date
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class WeatherProvider(str, Enum):
    """Supported weather data providers."""
    OPEN_METEO = "open_meteo"
    NASA_POWER = "nasa_power"
    OPENWEATHER = "openweather"
    WEATHERAPI = "weatherapi"
    NOAA = "noaa"


class TemperatureUnit(str, Enum):
    """Temperature units."""
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    KELVIN = "kelvin"


class PrecipitationUnit(str, Enum):
    """Precipitation units."""
    MM = "mm"
    INCHES = "inches"


class WindSpeedUnit(str, Enum):
    """Wind speed units."""
    MS = "m/s"
    KMH = "km/h"
    MPH = "mph"
    KNOTS = "knots"


class WeatherCondition(str, Enum):
    """Weather condition categories."""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    SNOW = "snow"
    SLEET = "sleet"
    FOG = "fog"
    THUNDERSTORM = "thunderstorm"
    HAIL = "hail"
    UNKNOWN = "unknown"


class ClimateZone(str, Enum):
    """Köppen climate classification zones."""
    TROPICAL_RAINFOREST = "Af"  # Tropical rainforest
    TROPICAL_MONSOON = "Am"     # Tropical monsoon
    TROPICAL_SAVANNA = "Aw"     # Tropical savanna
    DESERT_HOT = "BWh"          # Hot desert
    DESERT_COLD = "BWk"         # Cold desert
    STEPPE_HOT = "BSh"          # Hot semi-arid
    STEPPE_COLD = "BSk"         # Cold semi-arid
    MEDITERRANEAN = "Csa"       # Mediterranean hot summer
    HUMID_SUBTROPICAL = "Cfa"   # Humid subtropical
    OCEANIC = "Cfb"             # Oceanic
    CONTINENTAL_HOT = "Dfa"     # Hot-summer humid continental
    CONTINENTAL_WARM = "Dfb"    # Warm-summer humid continental
    SUBARCTIC = "Dfc"           # Subarctic
    TUNDRA = "ET"               # Tundra
    ICE_CAP = "EF"              # Ice cap


class Location(BaseModel):
    """Geographic location for climate data."""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")
    elevation_m: Optional[float] = Field(None, description="Elevation in meters")
    name: Optional[str] = Field(None, description="Location name")
    country: Optional[str] = Field(None, description="Country code (ISO 3166-1 alpha-2)")
    timezone: Optional[str] = Field(None, description="Timezone identifier")


class WeatherData(BaseModel):
    """Current weather conditions."""
    location: Location
    timestamp: datetime
    provider: WeatherProvider
    
    # Temperature data
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    feels_like_c: Optional[float] = Field(None, description="Feels like temperature in Celsius")
    temperature_min_c: Optional[float] = Field(None, description="Minimum temperature in Celsius")
    temperature_max_c: Optional[float] = Field(None, description="Maximum temperature in Celsius")
    
    # Humidity and pressure
    humidity_percent: Optional[float] = Field(None, ge=0, le=100, description="Relative humidity percentage")
    pressure_hpa: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    
    # Precipitation
    precipitation_mm: Optional[float] = Field(None, ge=0, description="Precipitation in mm")
    precipitation_probability: Optional[float] = Field(None, ge=0, le=100, description="Precipitation probability %")
    
    # Wind data
    wind_speed_ms: Optional[float] = Field(None, ge=0, description="Wind speed in m/s")
    wind_direction_deg: Optional[float] = Field(None, ge=0, lt=360, description="Wind direction in degrees")
    wind_gust_ms: Optional[float] = Field(None, ge=0, description="Wind gust speed in m/s")
    
    # Cloud and visibility
    cloud_cover_percent: Optional[float] = Field(None, ge=0, le=100, description="Cloud cover percentage")
    visibility_km: Optional[float] = Field(None, ge=0, description="Visibility in kilometers")
    
    # Solar radiation
    solar_radiation_wm2: Optional[float] = Field(None, ge=0, description="Solar radiation in W/m²")
    uv_index: Optional[float] = Field(None, ge=0, description="UV index")
    
    # Weather condition
    condition: Optional[WeatherCondition] = Field(None, description="Weather condition category")
    description: Optional[str] = Field(None, description="Weather description")
    
    # Data quality
    data_quality_score: Optional[float] = Field(None, ge=0, le=1, description="Data quality score (0-1)")
    source_station_distance_km: Optional[float] = Field(None, description="Distance to source weather station")


class HistoricalWeatherData(BaseModel):
    """Historical weather data for a specific date."""
    location: Location
    date: date
    provider: WeatherProvider
    
    # Daily temperature statistics
    temperature_mean_c: Optional[float] = Field(None, description="Mean temperature in Celsius")
    temperature_min_c: Optional[float] = Field(None, description="Minimum temperature in Celsius")
    temperature_max_c: Optional[float] = Field(None, description="Maximum temperature in Celsius")
    
    # Daily precipitation
    precipitation_total_mm: Optional[float] = Field(None, ge=0, description="Total precipitation in mm")
    precipitation_hours: Optional[float] = Field(None, ge=0, le=24, description="Hours with precipitation")
    
    # Daily wind statistics
    wind_speed_mean_ms: Optional[float] = Field(None, ge=0, description="Mean wind speed in m/s")
    wind_speed_max_ms: Optional[float] = Field(None, ge=0, description="Maximum wind speed in m/s")
    wind_direction_dominant_deg: Optional[float] = Field(None, ge=0, lt=360, description="Dominant wind direction")
    
    # Daily solar and humidity
    humidity_mean_percent: Optional[float] = Field(None, ge=0, le=100, description="Mean relative humidity")
    solar_radiation_total_wh_m2: Optional[float] = Field(None, ge=0, description="Total solar radiation in Wh/m²")
    sunshine_hours: Optional[float] = Field(None, ge=0, le=24, description="Sunshine hours")
    
    # Extreme events
    frost_occurred: Optional[bool] = Field(None, description="Frost occurred (temp < 0°C)")
    heat_wave_day: Optional[bool] = Field(None, description="Heat wave conditions")
    storm_occurred: Optional[bool] = Field(None, description="Storm conditions occurred")


class ClimateStatistics(BaseModel):
    """Long-term climate statistics for a location."""
    location: Location
    period_start: date
    period_end: date
    provider: WeatherProvider
    
    # Temperature statistics
    temperature_annual_mean_c: Optional[float] = Field(None, description="Annual mean temperature")
    temperature_annual_min_c: Optional[float] = Field(None, description="Annual minimum temperature")
    temperature_annual_max_c: Optional[float] = Field(None, description="Annual maximum temperature")
    temperature_range_c: Optional[float] = Field(None, description="Annual temperature range")
    
    # Monthly temperature normals
    temperature_monthly_means_c: Optional[List[float]] = Field(None, description="Monthly mean temperatures (12 values)")
    
    # Precipitation statistics
    precipitation_annual_total_mm: Optional[float] = Field(None, ge=0, description="Annual precipitation total")
    precipitation_monthly_totals_mm: Optional[List[float]] = Field(None, description="Monthly precipitation totals")
    wet_days_annual: Optional[int] = Field(None, ge=0, description="Annual wet days (>1mm precipitation)")
    
    # Extreme statistics
    frost_days_annual: Optional[int] = Field(None, ge=0, description="Annual frost days")
    hot_days_annual: Optional[int] = Field(None, ge=0, description="Annual hot days (>30°C)")
    
    # Climate classification
    climate_zone: Optional[ClimateZone] = Field(None, description="Köppen climate classification")
    growing_season_days: Optional[int] = Field(None, ge=0, description="Growing season length in days")
    
    @validator('temperature_monthly_means_c')
    def validate_monthly_means(cls, v):
        if v is not None and len(v) != 12:
            raise ValueError('Monthly means must have exactly 12 values')
        return v
    
    @validator('precipitation_monthly_totals_mm')
    def validate_monthly_precipitation(cls, v):
        if v is not None and len(v) != 12:
            raise ValueError('Monthly precipitation must have exactly 12 values')
        return v


class WeatherForecast(BaseModel):
    """Weather forecast data."""
    location: Location
    forecast_date: date
    issued_at: datetime
    provider: WeatherProvider
    forecast_days: int = Field(..., ge=1, le=16, description="Number of forecast days")
    
    # Daily forecasts
    daily_forecasts: List[Dict[str, Union[float, str, bool]]] = Field(
        ..., description="Daily forecast data"
    )
    
    # Forecast confidence
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Forecast confidence (0-1)")
    model_name: Optional[str] = Field(None, description="Weather model used")
    

class ClimateQuery(BaseModel):
    """Climate data query specification."""
    query_id: str = Field(..., description="Unique query identifier")
    locations: List[Location] = Field(..., min_items=1, description="Query locations")
    
    # Time range
    start_date: Optional[date] = Field(None, description="Start date for historical data")
    end_date: Optional[date] = Field(None, description="End date for historical data")
    
    # Data types requested
    include_current: bool = Field(True, description="Include current weather")
    include_historical: bool = Field(False, description="Include historical data")
    include_forecast: bool = Field(False, description="Include forecast data")
    include_climate_stats: bool = Field(False, description="Include climate statistics")
    
    # Forecast parameters
    forecast_days: Optional[int] = Field(None, ge=1, le=16, description="Number of forecast days")
    
    # Provider preferences
    preferred_providers: Optional[List[WeatherProvider]] = Field(None, description="Preferred data providers")
    
    # Quality requirements
    min_data_quality: Optional[float] = Field(None, ge=0, le=1, description="Minimum data quality score")
    max_station_distance_km: Optional[float] = Field(None, ge=0, description="Maximum weather station distance")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ClimateResponse(BaseModel):
    """Climate data query response."""
    query_id: str
    timestamp: datetime
    processing_time_seconds: float
    
    # Response data
    current_weather: Optional[List[WeatherData]] = Field(None, description="Current weather data")
    historical_weather: Optional[List[HistoricalWeatherData]] = Field(None, description="Historical weather data")
    forecasts: Optional[List[WeatherForecast]] = Field(None, description="Weather forecasts")
    climate_statistics: Optional[List[ClimateStatistics]] = Field(None, description="Climate statistics")
    
    # Response metadata
    total_locations: int
    successful_locations: int
    failed_locations: int
    data_providers_used: List[WeatherProvider]
    
    # Errors and warnings
    errors: Optional[List[str]] = Field(None, description="Error messages")
    warnings: Optional[List[str]] = Field(None, description="Warning messages")


class BatchClimateRequest(BaseModel):
    """Batch climate data request."""
    batch_id: str = Field(..., description="Unique batch identifier")
    queries: List[ClimateQuery] = Field(..., min_items=1, max_items=100, description="Climate queries")
    
    # Processing parameters
    max_concurrent_requests: int = Field(5, ge=1, le=20, description="Maximum concurrent requests")
    timeout_seconds: int = Field(300, ge=30, le=600, description="Request timeout")
    
    # Retry configuration
    max_retries: int = Field(3, ge=0, le=5, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(1, ge=0, le=10, description="Delay between retries")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BatchClimateResponse(BaseModel):
    """Batch climate data response."""
    batch_id: str
    timestamp: datetime
    processing_time_seconds: float
    
    # Batch results
    responses: List[ClimateResponse]
    
    # Batch statistics
    total_queries: int
    successful_queries: int
    failed_queries: int
    failed_query_ids: Optional[List[str]] = Field(None, description="IDs of failed queries")
    
    # Performance metrics
    average_response_time_seconds: float
    total_api_calls: int
    api_calls_by_provider: Dict[WeatherProvider, int]


class ClimateAlert(BaseModel):
    """Climate-based alert or warning."""
    alert_id: str = Field(..., description="Unique alert identifier")
    location: Location
    alert_type: str = Field(..., description="Type of alert (e.g., 'extreme_temperature', 'heavy_rain')")
    severity: str = Field(..., description="Alert severity (low, medium, high, critical)")
    
    # Alert details
    title: str = Field(..., description="Alert title")
    description: str = Field(..., description="Detailed alert description")
    
    # Timing
    issued_at: datetime
    valid_from: datetime
    valid_until: datetime
    
    # Thresholds and values
    threshold_value: Optional[float] = Field(None, description="Alert threshold value")
    current_value: Optional[float] = Field(None, description="Current measured value")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    
    # Impact assessment
    impact_level: Optional[str] = Field(None, description="Expected impact level")
    affected_activities: Optional[List[str]] = Field(None, description="Activities that may be affected")
    recommendations: Optional[List[str]] = Field(None, description="Recommended actions")
    
    # Data source
    provider: WeatherProvider
    confidence_score: Optional[float] = Field(None, ge=0, le=1, description="Alert confidence")


class SolarRadiationData(BaseModel):
    """Solar radiation and photovoltaic potential data."""
    location: Location
    date: date
    provider: WeatherProvider
    
    # Solar radiation components
    global_horizontal_irradiance_wh_m2: Optional[float] = Field(None, ge=0, description="GHI in Wh/m²")
    direct_normal_irradiance_wh_m2: Optional[float] = Field(None, ge=0, description="DNI in Wh/m²")
    diffuse_horizontal_irradiance_wh_m2: Optional[float] = Field(None, ge=0, description="DHI in Wh/m²")
    
    # Solar geometry
    solar_elevation_angle_deg: Optional[float] = Field(None, ge=0, le=90, description="Solar elevation angle")
    solar_azimuth_angle_deg: Optional[float] = Field(None, ge=0, lt=360, description="Solar azimuth angle")
    
    # Atmospheric conditions
    clearness_index: Optional[float] = Field(None, ge=0, le=1, description="Clearness index (0-1)")
    atmospheric_turbidity: Optional[float] = Field(None, ge=0, description="Atmospheric turbidity")
    
    # PV potential
    pv_power_output_kwh_kwp: Optional[float] = Field(None, ge=0, description="PV power output kWh/kWp")
    optimal_tilt_angle_deg: Optional[float] = Field(None, ge=0, le=90, description="Optimal panel tilt angle")
    
    # Quality indicators
    data_source_quality: Optional[str] = Field(None, description="Data source quality indicator")
    measurement_uncertainty_percent: Optional[float] = Field(None, ge=0, description="Measurement uncertainty")


class EnvironmentalConditions(BaseModel):
    """Comprehensive environmental conditions for project assessment."""
    location: Location
    assessment_date: date
    
    # Weather conditions
    current_weather: Optional[WeatherData] = Field(None, description="Current weather conditions")
    climate_statistics: Optional[ClimateStatistics] = Field(None, description="Long-term climate data")
    
    # Solar potential
    solar_data: Optional[SolarRadiationData] = Field(None, description="Solar radiation data")
    
    # Environmental factors
    air_quality_index: Optional[int] = Field(None, ge=0, description="Air quality index")
    dust_level: Optional[str] = Field(None, description="Dust level category")
    corrosion_risk: Optional[str] = Field(None, description="Corrosion risk level")
    
    # Seasonal patterns
    wet_season_months: Optional[List[int]] = Field(None, description="Wet season months (1-12)")
    dry_season_months: Optional[List[int]] = Field(None, description="Dry season months (1-12)")
    peak_solar_months: Optional[List[int]] = Field(None, description="Peak solar radiation months")
    
    # Project suitability scores
    solar_suitability_score: Optional[float] = Field(None, ge=0, le=10, description="Solar project suitability (0-10)")
    wind_suitability_score: Optional[float] = Field(None, ge=0, le=10, description="Wind project suitability (0-10)")
    overall_climate_score: Optional[float] = Field(None, ge=0, le=10, description="Overall climate suitability (0-10)")
    
    # Risks and considerations
    climate_risks: Optional[List[str]] = Field(None, description="Identified climate risks")
    seasonal_considerations: Optional[List[str]] = Field(None, description="Seasonal considerations")
    maintenance_recommendations: Optional[List[str]] = Field(None, description="Climate-based maintenance recommendations")