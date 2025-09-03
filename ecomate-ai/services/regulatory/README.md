# Regulatory Monitor Service

A comprehensive regulatory compliance monitoring service that tracks standards, regulations, and compliance requirements across multiple standards bodies including SANS, ISO, EPA, OSHA, ANSI, ASTM, IEC, and IEEE.

## Features

### Core Capabilities
- **Multi-Standards Body Integration**: Support for 8+ major standards organizations
- **Real-time Compliance Monitoring**: Continuous tracking of compliance status
- **Automated Updates**: Automatic detection and notification of standards changes
- **Compliance Reporting**: Comprehensive compliance reports with actionable insights
- **Regulatory Impact Assessment**: Analysis of proposed changes and their regulatory implications
- **Alert System**: Configurable alerts for compliance violations and updates
- **Batch Processing**: Efficient handling of multiple regulatory queries

### Supported Standards Bodies
- **SANS** (SysAdmin, Audit, Network, Security)
- **ISO** (International Organization for Standardization)
- **EPA** (Environmental Protection Agency)
- **OSHA** (Occupational Safety and Health Administration)
- **ANSI** (American National Standards Institute)
- **ASTM** (American Society for Testing and Materials)
- **IEC** (International Electrotechnical Commission)
- **IEEE** (Institute of Electrical and Electronics Engineers)

## Installation

### Prerequisites
- Python 3.9+
- Redis (for caching)
- PostgreSQL (optional, for persistent storage)

### Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   Create a `.env` file:
   ```env
   # API Keys (obtain from respective standards bodies)
   SANS_API_KEY=your_sans_api_key
   ISO_API_KEY=your_iso_api_key
   EPA_API_KEY=your_epa_api_key
   OSHA_API_KEY=your_osha_api_key
   ANSI_API_KEY=your_ansi_api_key
   ASTM_API_KEY=your_astm_api_key
   IEC_API_KEY=your_iec_api_key
   IEEE_API_KEY=your_ieee_api_key
   
   # Redis Configuration
   REDIS_URL=redis://localhost:6379/0
   
   # Database (optional)
   DATABASE_URL=postgresql://user:password@localhost/regulatory_db
   
   # Service Configuration
   REGULATORY_SERVICE_PORT=8080
   REGULATORY_SERVICE_HOST=0.0.0.0
   LOG_LEVEL=INFO
   
   # Cache Settings
   CACHE_TTL=3600
   MAX_CACHE_SIZE=1000
   
   # Rate Limiting
   RATE_LIMIT_PER_MINUTE=60
   BURST_LIMIT=10
   ```

3. **Start the Service**
   ```bash
   uvicorn services.regulatory.router:regulatory_router --host 0.0.0.0 --port 8080
   ```

## Usage

### Python Client

```python
from services.regulatory import RegulatoryService, RegulatoryClient
from services.regulatory.models import StandardsBody, RegulatoryQuery

# Initialize the service
service = RegulatoryService()

# Monitor compliance for an entity
entity_id = "company-123"
standards = ["ISO-27001", "SANS-20", "EPA-CAA"]

result = await service.monitor_compliance(
    entity_id=entity_id,
    standards=standards,
    check_interval_hours=24
)

print(f"Compliance Status: {result.overall_status}")
for check in result.compliance_checks:
    print(f"- {check.standard_id}: {check.status}")

# Get regulatory updates
updates = await service.track_standards_updates(
    standards_bodies=[StandardsBody.ISO, StandardsBody.SANS],
    categories=["security", "environmental"],
    since_date="2024-01-01"
)

for update in updates.updates:
    print(f"Update: {update.title} ({update.standard_id})")

# Generate compliance report
report = await service.generate_compliance_report(
    entity_id=entity_id,
    standards=standards,
    include_recommendations=True
)

print(f"Report generated: {report.report_id}")
print(f"Overall Score: {report.overall_compliance_score}")
```

### REST API

#### Health Check
```bash
curl http://localhost:8080/regulatory/health
```

#### Search Standards
```bash
curl "http://localhost:8080/regulatory/standards/search?query=security&body=ISO&category=information_security"
```

#### Get Specific Standard
```bash
curl "http://localhost:8080/regulatory/standards/ISO-27001"
```

#### Monitor Compliance
```bash
curl -X POST "http://localhost:8080/regulatory/compliance/monitor" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "company-123",
    "standards": ["ISO-27001", "SANS-20"],
    "check_interval_hours": 24
  }'
```

#### Check Compliance Status
```bash
curl "http://localhost:8080/regulatory/compliance/check/company-123?standards=ISO-27001,SANS-20"
```

#### Generate Compliance Report
```bash
curl -X POST "http://localhost:8080/regulatory/compliance/report" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "company-123",
    "standards": ["ISO-27001"],
    "include_recommendations": true
  }'
```

#### Get Regulatory Alerts
```bash
curl "http://localhost:8080/regulatory/alerts?severity=high&limit=10"
```

#### Assess Regulatory Impact
```bash
curl -X POST "http://localhost:8080/regulatory/impact/assess" \
  -H "Content-Type: application/json" \
  -d '{
    "proposed_changes": ["Implement new encryption standard"],
    "affected_standards": ["ISO-27001"],
    "implementation_timeline": "2024-06-01"
  }'
```

#### Batch Processing
```bash
curl -X POST "http://localhost:8080/regulatory/query/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      {
        "query_id": "q1",
        "standards_body": "ISO",
        "query_text": "information security",
        "filters": {"category": "security"}
      },
      {
        "query_id": "q2",
        "standards_body": "SANS",
        "query_text": "network security"
      }
    ]
  }'
```

## Configuration

### Service Configuration

The service can be configured through environment variables or a configuration file:

```python
from services.regulatory.models import RegulatoryConfig

config = RegulatoryConfig(
    api_keys={
        "SANS": "your_sans_key",
        "ISO": "your_iso_key",
        # ... other keys
    },
    cache_ttl=3600,
    max_retries=3,
    request_timeout=30,
    enable_background_updates=True,
    update_check_interval=3600,
    alert_thresholds={
        "compliance_score": 0.8,
        "days_until_expiry": 30
    }
)

service = RegulatoryService(config=config)
```

### API Rate Limiting

The service implements rate limiting to respect API quotas:

- Default: 60 requests per minute per API key
- Burst limit: 10 requests
- Configurable per standards body

### Caching Strategy

- **Standards Data**: Cached for 1 hour (configurable)
- **Compliance Checks**: Cached for 30 minutes
- **Updates**: Cached for 15 minutes
- **Search Results**: Cached for 2 hours

## Data Models

### Core Models

- **RegulatoryStandard**: Complete standard information
- **ComplianceRequirement**: Specific compliance requirements
- **ComplianceCheck**: Individual compliance verification
- **RegulatoryAlert**: Compliance and update alerts
- **StandardsUpdate**: Standards change notifications
- **ComplianceReport**: Comprehensive compliance analysis

### Enumerations

- **StandardsBody**: Supported standards organizations
- **ComplianceStatus**: Compliance states (compliant, non_compliant, pending, unknown)
- **AlertSeverity**: Alert priority levels (low, medium, high, critical)
- **StandardCategory**: Standard classification categories
- **UpdateType**: Types of standards updates

## Monitoring and Alerting

### Built-in Monitoring

- Health check endpoints
- Prometheus metrics
- Structured logging
- Performance tracking

### Alert Channels

- **Email**: SMTP-based notifications
- **Slack**: Webhook integration
- **SMS**: Twilio integration
- **Webhook**: Custom HTTP callbacks

### Metrics

- API response times
- Cache hit rates
- Compliance check success rates
- Standards update frequencies
- Alert generation rates

## Testing

### Run Tests

```bash
# Unit tests
pytest services/regulatory/test_regulatory.py -v

# Integration tests
pytest services/regulatory/test_regulatory.py::TestRegulatoryIntegration -v

# Performance tests
pytest services/regulatory/test_regulatory.py::TestRegulatoryPerformance -v

# Coverage report
pytest services/regulatory/test_regulatory.py --cov=services.regulatory --cov-report=html
```

### Test Configuration

Tests use mock APIs by default. For integration testing with real APIs:

```bash
export REGULATORY_TEST_MODE=integration
export REGULATORY_TEST_API_KEYS='{"SANS": "test_key", "ISO": "test_key"}'
pytest services/regulatory/test_regulatory.py::TestRegulatoryIntegration
```

## Development

### Code Quality

```bash
# Format code
black services/regulatory/
isort services/regulatory/

# Lint code
flake8 services/regulatory/
mypy services/regulatory/

# Security scan
bandit -r services/regulatory/
safety check
```

### Pre-commit Hooks

```bash
pre-commit install
pre-commit run --all-files
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY services/regulatory/ ./services/regulatory/

EXPOSE 8080
CMD ["uvicorn", "services.regulatory.router:regulatory_router", "--host", "0.0.0.0", "--port", "8080"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: regulatory-monitor
spec:
  replicas: 3
  selector:
    matchLabels:
      app: regulatory-monitor
  template:
    metadata:
      labels:
        app: regulatory-monitor
    spec:
      containers:
      - name: regulatory-monitor
        image: regulatory-monitor:latest
        ports:
        - containerPort: 8080
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: regulatory-secrets
              key: database-url
```

## Troubleshooting

### Common Issues

1. **API Key Authentication Failures**
   - Verify API keys are correct and active
   - Check rate limits haven't been exceeded
   - Ensure proper permissions for standards access

2. **Cache Connection Issues**
   - Verify Redis is running and accessible
   - Check Redis URL configuration
   - Monitor Redis memory usage

3. **Slow Response Times**
   - Check API rate limits
   - Monitor cache hit rates
   - Review network connectivity to standards APIs

4. **Compliance Check Failures**
   - Verify entity data is complete
   - Check standard requirements are up to date
   - Review compliance logic configuration

### Logging

The service uses structured logging with configurable levels:

```python
import logging
logging.getLogger("services.regulatory").setLevel(logging.DEBUG)
```

Log categories:
- `regulatory.client`: API interactions
- `regulatory.service`: Business logic
- `regulatory.compliance`: Compliance checks
- `regulatory.cache`: Caching operations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run quality checks
5. Submit a pull request

### Development Setup

```bash
git clone <repository>
cd ecomate-ai
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r services/regulatory/requirements.txt
pip install -e .
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation
- Contact the development team

## Changelog

### v1.0.0 (2024-01-XX)
- Initial release
- Support for 8 standards bodies
- Compliance monitoring and reporting
- Real-time alerts and updates
- REST API and Python client
- Comprehensive testing suite
- Docker and Kubernetes deployment support