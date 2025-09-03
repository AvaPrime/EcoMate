# Enhanced Telemetry Service

A comprehensive telemetry system for EcoMate that replaces hardcoded baselines with dynamic, database-driven calculations. This service provides real-time monitoring, intelligent alerting, and historical data analysis for environmental systems.

## Features

### 🔄 Dynamic Baselines
- **Adaptive Calculations**: Automatically calculates baselines using rolling averages, statistical methods
- **Configurable Windows**: Customizable time windows for baseline calculations (hours to days)
- **Outlier Detection**: Intelligent filtering of anomalous data points
- **Auto-Updates**: Scheduled baseline recalculation based on configurable intervals

### 📊 Time-Series Data Storage
- **Optimized Storage**: Efficient time-series data storage with PostgreSQL/TimescaleDB
- **Batch Processing**: High-performance batch ingestion for IoT data streams
- **Data Retention**: Configurable data retention policies
- **Compression**: Automatic data compression for long-term storage

### 🚨 Intelligent Alerting
- **Multi-Condition Alerts**: Threshold-based, deviation-based, and trend-based alerting
- **Severity Levels**: Configurable alert severity (low, medium, high, critical)
- **Alert Management**: Full lifecycle management (active, acknowledged, resolved)
- **Cooldown Periods**: Prevents alert spam with configurable cooldown intervals

### 📈 Advanced Analytics
- **Statistical Analysis**: Mean, standard deviation, confidence intervals
- **Trend Detection**: Identifies patterns and anomalies in time-series data
- **Performance Metrics**: System performance summaries and KPIs
- **Historical Reporting**: Comprehensive historical data analysis

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   IoT Devices   │───▶│  Telemetry API   │───▶│   Time-Series   │
│   & Sensors     │    │   (FastAPI)      │    │    Database     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                         │
                                ▼                         ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Workflow Engine  │───▶│ Dynamic Baselines│
                       │   (Temporal)     │    │   & Alerts      │
                       └──────────────────┘    └─────────────────┘
```

## Database Schema

### Core Tables

1. **telemetry_data** - Time-series metrics storage
2. **baseline_configs** - Baseline calculation configurations
3. **dynamic_baselines** - Calculated baseline values
4. **alert_rules** - Alert condition definitions
5. **alerts** - Triggered alerts and their lifecycle

## API Endpoints

### Telemetry Ingestion

```http
# Legacy endpoint (backward compatibility)
POST /telemetry/ingest

# Enhanced endpoint with full processing
POST /telemetry/ingest/enhanced
```

### Data Querying

```http
# Query historical telemetry data
GET /telemetry/systems/{system_id}/data
  ?start_time=2024-01-01T00:00:00Z
  &end_time=2024-01-02T00:00:00Z
  &metric_types=flow_m3h,uv_dose_mj_cm2
  &limit=1000

# Get system metrics summary
GET /telemetry/systems/{system_id}/metrics/summary?hours=24
```

### Baseline Management

```http
# Get current baselines
GET /telemetry/systems/{system_id}/baselines

# Update baselines
POST /telemetry/systems/{system_id}/baselines/update

# Baseline configuration
GET /telemetry/systems/{system_id}/baseline-config/{metric_type}
POST /telemetry/systems/{system_id}/baseline-config/{metric_type}
```

### Alert Management

```http
# Get system alerts
GET /telemetry/systems/{system_id}/alerts
  ?active_only=true
  &severity_filter=high

# Evaluate dynamic alerts
POST /telemetry/systems/{system_id}/alerts/evaluate
```

### System Monitoring

```http
# Comprehensive monitoring data
GET /telemetry/systems/{system_id}/monitoring
  ?include_baselines=true
  &include_alerts=true

# Health check
GET /telemetry/health
```

## Installation & Setup

### 1. Install Dependencies

```bash
cd services/telemetry
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Initialize database tables
python init_db.py

# Or with custom options
python init_db.py --drop --no-sample-data
```

### 3. Environment Configuration

Create a `.env` file:

```env
# Database Configuration
PGHOST=localhost
PGPORT=5432
PGUSER=postgres
PGPASSWORD=your_password
PGDATABASE=ecomate

# Telemetry Service Configuration
TELEMETRY_LOG_LEVEL=INFO
TELEMETRY_BATCH_SIZE=1000
TELEMETRY_RETENTION_DAYS=365

# TimescaleDB (optional)
ENABLE_TIMESCALEDB=true

# Alert Configuration
DEFAULT_ALERT_COOLDOWN_MINUTES=30
MAX_ACTIVE_ALERTS_PER_SYSTEM=100
```

### 4. Start the Service

```bash
# Development
uvicorn router_telemetry:router --reload --port 8001

# Production
uvicorn router_telemetry:router --host 0.0.0.0 --port 8001 --workers 4
```

## Usage Examples

### Ingest Telemetry Data

```python
import httpx
from datetime import datetime

# Enhanced telemetry ingestion
telemetry_data = {
    "system_id": "system_001",
    "metrics": {
        "flow_m3h": 45.2,
        "uv_dose_mj_cm2": 12.8
    },
    "timestamp": datetime.utcnow().isoformat(),
    "quality_flags": {"validated": True},
    "source": "iot_sensor_v2"
}

async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8001/telemetry/ingest/enhanced",
        json=telemetry_data
    )
    print(response.json())
```

### Query Historical Data

```python
# Query last 24 hours of data
response = await client.get(
    "http://localhost:8001/telemetry/systems/system_001/data",
    params={
        "start_time": "2024-01-01T00:00:00Z",
        "end_time": "2024-01-02T00:00:00Z",
        "metric_types": ["flow_m3h", "uv_dose_mj_cm2"],
        "limit": 1000
    }
)
data = response.json()
print(f"Retrieved {len(data['data'])} data points")
```

### Configure Dynamic Baselines

```python
# Configure baseline calculation
baseline_config = {
    "calculation_method": "rolling_mean",
    "window_size_hours": 48,
    "min_data_points": 20,
    "outlier_threshold": 2.5,
    "update_frequency_minutes": 30
}

response = await client.post(
    "http://localhost:8001/telemetry/systems/system_001/baseline-config/flow_m3h",
    json=baseline_config
)
```

## Migration from Legacy System

The enhanced telemetry service maintains backward compatibility:

### Legacy Support
- **Existing Endpoints**: Original `/ingest` endpoint continues to work
- **Legacy Functions**: `alert_findings_legacy()` preserves original behavior
- **Gradual Migration**: Systems can migrate incrementally

### Migration Steps

1. **Deploy Enhanced Service**: Run alongside existing system
2. **Initialize Database**: Set up new tables and configurations
3. **Configure Baselines**: Define baseline calculation rules
4. **Test Parallel Processing**: Verify enhanced workflows
5. **Switch Endpoints**: Update clients to use enhanced endpoints
6. **Monitor & Optimize**: Fine-tune configurations based on real data

## Performance Considerations

### Database Optimization
- **Indexing**: Optimized indexes for time-series queries
- **Partitioning**: Time-based partitioning for large datasets
- **Connection Pooling**: Efficient database connection management
- **Batch Processing**: Bulk operations for high-throughput scenarios

### Scalability
- **Horizontal Scaling**: Multiple service instances with load balancing
- **Database Scaling**: TimescaleDB clustering for massive datasets
- **Caching**: Redis integration for frequently accessed data
- **Async Processing**: Non-blocking operations for high concurrency

## Monitoring & Observability

### Metrics
- **Ingestion Rate**: Telemetry data points per second
- **Processing Latency**: End-to-end processing time
- **Alert Response Time**: Time from trigger to notification
- **Database Performance**: Query execution times and connection usage

### Logging
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Log Levels**: Configurable logging levels (DEBUG, INFO, WARN, ERROR)
- **Audit Trail**: Complete audit trail for all operations

### Health Checks
- **Service Health**: `/health` endpoint for service status
- **Database Health**: Connection and query performance checks
- **Dependency Health**: External service availability checks

## Security

### Data Protection
- **Encryption**: Data encryption in transit and at rest
- **Access Control**: Role-based access control for API endpoints
- **Input Validation**: Comprehensive input validation and sanitization
- **Rate Limiting**: API rate limiting to prevent abuse

### Compliance
- **Data Retention**: Configurable data retention policies
- **Audit Logging**: Complete audit trail for compliance
- **Privacy**: Data anonymization and pseudonymization options

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database connectivity
   python -c "import asyncio; from store import get_telemetry_store; asyncio.run(get_telemetry_store())"
   ```

2. **Missing TimescaleDB Extension**
   ```sql
   -- Enable TimescaleDB in PostgreSQL
   CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
   ```

3. **High Memory Usage**
   - Reduce batch sizes in configuration
   - Implement data retention policies
   - Monitor connection pool sizes

4. **Slow Queries**
   - Check index usage with `EXPLAIN ANALYZE`
   - Optimize time range queries
   - Consider data partitioning

### Debug Mode

```bash
# Enable debug logging
export TELEMETRY_LOG_LEVEL=DEBUG
python -m uvicorn router_telemetry:router --reload
```

## Contributing

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio black isort mypy

# Run tests
pytest tests/

# Code formatting
black .
isort .

# Type checking
mypy .
```

### Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_store.py -v
pytest tests/test_workflows.py -v

# Run with coverage
pytest --cov=services.telemetry
```

## License

This enhanced telemetry service is part of the EcoMate project and follows the same licensing terms.

---

**Note**: This implementation replaces hardcoded baseline values with a dynamic, database-driven system while maintaining full backward compatibility with existing telemetry workflows.