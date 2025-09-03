# Geospatial Service

A comprehensive geospatial analysis service that integrates multiple APIs to provide location intelligence, terrain analysis, and site assessment capabilities for EcoMate AI projects.

## Features

### Core Capabilities
- **Multi-Provider Geocoding**: Google Maps API integration with fallback options
- **Elevation Data**: Google Elevation API and USGS Elevation Point Query Service
- **Terrain Analysis**: Slope calculation, aspect determination, and terrain classification
- **Soil Data**: SoilGrids API integration for soil composition and pH analysis
- **Distance Matrix**: Travel time and distance calculations
- **Site Assessment**: Comprehensive project viability analysis
- **Batch Processing**: Concurrent processing of multiple geospatial queries
- **Optimal Site Selection**: Multi-criteria site ranking and selection

### Advanced Features
- **Dynamic Baseline Calculations**: Adaptive terrain difficulty scoring
- **Multi-Condition Analysis**: Complex site assessment with multiple factors
- **Cost Modeling**: Logistics cost estimation based on distance, elevation, and terrain
- **Accessibility Scoring**: Site accessibility classification (EXCELLENT to POOR)
- **Warning System**: Automated alerts for challenging site conditions
- **Recommendation Engine**: Intelligent suggestions for site optimization

## Architecture

### Components

```
services/geospatial/
├── __init__.py          # Package initialization and exports
├── models.py            # Pydantic data models
├── client.py            # API client implementations
├── service.py           # High-level service functions
├── router.py            # FastAPI endpoints
├── test_geospatial.py   # Comprehensive test suite
├── requirements.txt     # Dependencies
└── README.md           # This documentation
```

### Data Models

#### Core Models
- `Location`: Geographic coordinates with optional address
- `ElevationData`: Elevation information with metadata
- `SlopeData`: Slope analysis with terrain classification
- `SoilData`: Soil composition and properties
- `GeospatialAnalysis`: Comprehensive site analysis results
- `SiteAssessment`: Project viability assessment

#### Request/Response Models
- `GeospatialQuery`: Single query specification
- `BatchGeospatialRequest`: Multiple query processing
- `GeospatialResponse`: Query results with metadata
- `LogisticsCost`: Detailed cost breakdown
- `DistanceMatrix`: Travel time and distance data

### API Integrations

#### Google Maps Platform
- **Geocoding API**: Address to coordinates conversion
- **Reverse Geocoding API**: Coordinates to address conversion
- **Elevation API**: High-resolution elevation data
- **Distance Matrix API**: Travel time and distance calculations
- **Requirements**: `GOOGLE_API_KEY` environment variable

#### USGS Services
- **Elevation Point Query Service**: Free elevation data
- **Coverage**: United States and territories
- **Requirements**: No API key needed

#### SoilGrids API
- **Global Soil Information**: Worldwide soil property data
- **Properties**: Clay, sand, silt percentages, pH levels
- **Requirements**: No API key needed

## Installation

### Prerequisites
- Python 3.8+
- FastAPI application framework
- Access to external APIs (Google Maps recommended)

### Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

```bash
# Required for Google Maps integration
export GOOGLE_API_KEY="your_google_maps_api_key"

# Optional: Service configuration
export GEOSPATIAL_TIMEOUT=30
export GEOSPATIAL_MAX_CONCURRENT=10
```

### Google Maps API Setup

1. Visit [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable the following APIs:
   - Geocoding API
   - Elevation API
   - Distance Matrix API
4. Create credentials (API Key)
5. Set usage quotas and billing

## Usage

### Basic Integration

```python
from services.geospatial import GeospatialService, GeospatialClient
from services.geospatial.models import Location

# Initialize service
client = GeospatialClient(google_api_key="your_key")
service = GeospatialService(client=client)

# Geocode an address
location = await client.geocode("123 Main St, New York, NY")
print(f"Coordinates: {location.latitude}, {location.longitude}")

# Get elevation data
elevations = await client.get_elevation_google([(40.7128, -74.0060)])
print(f"Elevation: {elevations[0].elevation_m}m")

# Comprehensive site assessment
assessment = await service.assess_site(location)
print(f"Project viable: {assessment.project_viable}")
print(f"Accessibility: {assessment.geospatial_analysis.accessibility}")
```

### FastAPI Integration

```python
from fastapi import FastAPI
from services.geospatial import geospatial_router

app = FastAPI()
app.include_router(geospatial_router, prefix="/api/v1/geospatial")
```

### API Endpoints

#### Core Endpoints
- `GET /health` - Service health check
- `POST /geocode` - Address to coordinates
- `POST /reverse-geocode` - Coordinates to address
- `POST /elevation` - Elevation data retrieval
- `POST /slope` - Slope analysis
- `POST /soil` - Soil data retrieval
- `POST /distance-matrix` - Distance calculations

#### Advanced Endpoints
- `POST /site-assessment` - Comprehensive site analysis
- `POST /logistics-cost` - Cost estimation
- `POST /comprehensive-analysis` - Full geospatial analysis
- `POST /query` - Single geospatial query
- `POST /batch` - Batch query processing
- `POST /optimal-sites` - Site selection optimization
- `GET /capabilities` - Service capabilities

### Example Requests

#### Site Assessment

```bash
curl -X POST "http://localhost:8000/api/v1/geospatial/site-assessment" \
  -H "Content-Type: application/json" \
  -d '{
    "location": {
      "latitude": 40.7128,
      "longitude": -74.0060
    },
    "include_logistics": true,
    "depot_location": {
      "latitude": 40.7500,
      "longitude": -74.0000
    }
  }'
```

#### Batch Processing

```bash
curl -X POST "http://localhost:8000/api/v1/geospatial/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": "batch-001",
    "queries": [
      {
        "query_id": "query-001",
        "locations": [{"address": "New York, NY"}],
        "data_types": ["elevation", "slope", "soil"]
      }
    ],
    "max_concurrent_requests": 5
  }'
```

## Data Sources and Accuracy

### Elevation Data
- **Google Elevation API**: ~9m resolution globally
- **USGS**: ~10-30m resolution (US only)
- **Accuracy**: ±1-5m depending on terrain and source

### Soil Data
- **SoilGrids**: 250m resolution globally
- **Properties**: Clay, sand, silt, pH at multiple depths
- **Accuracy**: Modeled data, suitable for regional analysis

### Geocoding
- **Google Geocoding**: High accuracy, global coverage
- **Address Matching**: Fuzzy matching with confidence scores
- **Reverse Geocoding**: Precise address from coordinates

## Performance Considerations

### Rate Limits
- **Google Maps APIs**: Varies by API and billing plan
- **USGS**: No official limits, but be respectful
- **SoilGrids**: No official limits, but avoid excessive requests

### Optimization Strategies
- **Batch Processing**: Use batch endpoints for multiple queries
- **Caching**: Implement Redis caching for repeated queries
- **Concurrent Requests**: Configure `max_concurrent_requests`
- **Timeout Management**: Adjust timeouts based on network conditions

### Recommended Limits
- **Concurrent Requests**: 5-10 for most use cases
- **Timeout**: 30 seconds for individual requests
- **Batch Size**: 50-100 queries per batch

## Error Handling

### Common Errors
- `GeospatialAPIError`: API-specific errors
- `ValidationError`: Invalid input data
- `TimeoutError`: Request timeout
- `RateLimitError`: API quota exceeded

### Error Response Format

```json
{
  "error": {
    "type": "GeospatialAPIError",
    "message": "Google API key required for geocoding",
    "details": {
      "api": "google_geocoding",
      "status_code": 401
    }
  }
}
```

## Testing

### Running Tests

```bash
# Run all tests
pytest services/geospatial/test_geospatial.py -v

# Run with coverage
pytest services/geospatial/test_geospatial.py --cov=services.geospatial

# Run integration tests (requires API keys)
pytest services/geospatial/test_geospatial.py -m integration

# Skip integration tests
pytest services/geospatial/test_geospatial.py -m "not integration"
```

### Test Categories
- **Unit Tests**: Mock-based testing of individual components
- **Integration Tests**: Real API testing (requires API keys)
- **Model Tests**: Pydantic model validation
- **Service Tests**: High-level service function testing

### Test Coverage
- **Models**: 100% coverage of validation logic
- **Client**: 95% coverage including error handling
- **Service**: 90% coverage of business logic
- **Router**: 85% coverage of endpoint functionality

## Security

### API Key Management
- Store API keys in environment variables
- Never commit API keys to version control
- Use different keys for development/production
- Monitor API usage and set quotas

### Data Privacy
- Location data may be sensitive
- Implement data retention policies
- Consider GDPR compliance for EU users
- Log access patterns for security monitoring

### Network Security
- Use HTTPS for all API communications
- Validate all input data
- Implement rate limiting
- Monitor for unusual usage patterns

## Monitoring and Logging

### Metrics
- Request count by endpoint
- Response times by API provider
- Error rates and types
- API quota usage

### Logging
- Structured logging with `structlog`
- Request/response logging (excluding sensitive data)
- Error tracking with stack traces
- Performance metrics

### Health Checks
- Service availability
- API connectivity
- Response time monitoring
- Error rate thresholds

## Troubleshooting

### Common Issues

#### "Google API key required"
- Ensure `GOOGLE_API_KEY` environment variable is set
- Verify API key has necessary permissions
- Check API quotas and billing

#### "Geocoding failed"
- Verify address format
- Check for typos in location names
- Try alternative address formats

#### "Elevation data unavailable"
- Check coordinates are valid (lat: -90 to 90, lng: -180 to 180)
- Verify API connectivity
- Try alternative elevation sources (USGS)

#### "Timeout errors"
- Increase timeout values
- Check network connectivity
- Reduce concurrent request limits

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed HTTP logging
import httpx
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.DEBUG)
```

## Contributing

### Development Setup

```bash
# Clone repository
git clone <repository_url>
cd ecomate-ai

# Install development dependencies
pip install -r services/geospatial/requirements.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest services/geospatial/test_geospatial.py
```

### Code Standards
- **Formatting**: Black with 88-character line length
- **Import Sorting**: isort with Black compatibility
- **Linting**: flake8 with standard configuration
- **Type Hints**: mypy for static type checking
- **Documentation**: Comprehensive docstrings

### Pull Request Process
1. Create feature branch from main
2. Implement changes with tests
3. Run full test suite
4. Update documentation
5. Submit pull request with description

## License

This project is part of EcoMate AI and follows the project's licensing terms.

## Support

For issues and questions:
1. Check this documentation
2. Review test cases for usage examples
3. Check API provider documentation
4. Create issue in project repository

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15  
**Maintainer**: EcoMate AI Team