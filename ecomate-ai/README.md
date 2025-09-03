# EcoMate AI

Agent services for EcoMate: research, supplier sync, price monitor, spec drafting, and compliance checks.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Installation Guide](#installation-guide)
- [Usage Instructions](#usage-instructions)
- [API Documentation](#api-documentation)
- [Maintenance Guide](#maintenance-guide)
- [Contribution Guidelines](#contribution-guidelines)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## Project Overview

### Purpose and Objectives

EcoMate AI is an intelligent automation platform designed to streamline environmental technology research, supplier management, and compliance monitoring. The system provides:

- **Automated Research**: Web crawling and data extraction for environmental technology suppliers and products with intelligent content parsing
- **Price Monitoring**: Continuous tracking of product prices with deviation alerts, automated reporting, and GitHub integration
- **Vendor-Specific Parsing**: Specialized parsers for pump and UV reactor specifications with intelligent fallback to LLM processing
- **Compliance Management**: Automated spec drafting and compliance checks for environmental systems
- **Documentation Automation**: Automated PR creation and documentation updates with version control integration
- **Workflow Orchestration**: Reliable, fault-tolerant execution of complex business processes using Temporal

### Key Features and Functionality

#### 🔍 **Intelligent Research Capabilities**
- **Advanced Web Crawling**: Automated crawling with respect for robots.txt and intelligent rate limiting
- **Content Extraction**: BeautifulSoup and Selectolax-based parsing with custom selectors
- **Data Classification**: Intelligent categorization of products and specifications
- **Multi-source Aggregation**: Deduplication and normalization across multiple suppliers

#### Core Services
- **Research Workflows**: Automated crawling, parsing, and data extraction from supplier websites
- **Price Monitoring**: Scheduled price tracking with configurable deviation thresholds and alert systems
- **Vendor Parsers**: Domain-specific parsers for pumps and UV reactors with structured data extraction
- **LLM Integration**: Fallback processing using Ollama and Google Vertex AI models with context-aware prompts
- **Document Management**: MinIO-based artifact storage and GitHub integration for documentation

#### Advanced Capabilities
- **Temporal Orchestration**: Reliable workflow execution with retry mechanisms and monitoring
- **Vector Database**: PostgreSQL with pgvector for semantic search and data analysis
- **Multi-Model Support**: Configurable AI models (Ollama local, Google Vertex AI)
- **Structured Data Processing**: Pydantic-based validation and type safety
- **Unit Conversion**: Automatic conversion of flow rates, pressures, and measurements

### Technical Requirements and Dependencies

#### System Requirements
- **Operating System**: Linux, macOS, or Windows with Docker support
- **Memory**: Minimum 8GB RAM (16GB recommended for AI models and concurrent workflows)
- **Storage**: 20GB available disk space (SSD recommended for optimal database performance)
- **Network**: Stable internet connectivity for AI services and web crawling
- **CPU**: 4+ cores recommended (8+ for production workloads)

#### Core Dependencies
- **Python**: 3.11+ with virtual environment support
- **Docker**: For infrastructure services (PostgreSQL, MinIO, Temporal, NATS)
- **PostgreSQL**: 16+ with pgvector extension
- **Temporal**: Workflow orchestration engine
- **MinIO**: S3-compatible object storage

#### Python Dependencies
```
fastapi==0.114.0          # Web API framework
uvicorn[standard]==0.30.6  # ASGI server
httpx==0.27.2             # HTTP client
selectolax==0.3.20        # HTML parsing
beautifulsoup4==4.12.3    # HTML/XML parsing
pydantic==2.8.2           # Data validation
pydantic-settings==2.4.0  # Settings management
python-dotenv==1.0.1      # Environment variables
pint==0.24.4              # Unit conversions
python-slugify==8.0.4     # URL-safe strings
boto3==1.34.152           # AWS SDK (MinIO)
psycopg[binary]==3.2.1    # PostgreSQL adapter
pgvector==0.3.3           # Vector database
temporalio==1.7.0         # Workflow engine
PyYAML==6.0.2             # YAML processing
pdfplumber==0.11.4        # PDF text extraction
```

## Installation Guide

### System Requirements

#### Hardware Requirements
- **CPU**: 4+ cores recommended (8+ for production workloads)
- **RAM**: 8GB minimum, 16GB recommended (32GB for heavy AI processing)
- **Storage**: 20GB available space (SSD strongly recommended)
- **Network**: Stable internet connection with sufficient bandwidth for web crawling

#### Software Prerequisites
- **Docker**: Version 20.10+ with Docker Compose
- **Python**: Version 3.11 or higher
- **Git**: For repository management
- **AI Services**: Ollama (local) or Google Cloud account (Vertex AI)

### Step-by-Step Setup Instructions

#### Prerequisites Checklist
Before starting, ensure you have:
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Docker Desktop or Docker Engine with Compose
- [ ] Git configured with your credentials
- [ ] Sufficient system resources available
- [ ] Internet connection for dependencies

#### 1. Repository Setup
```bash
# Clone the repository
git clone https://github.com/your-org/ecomate-ai.git
cd ecomate-ai

# Create and configure environment
cp .env.example .env

# Make scripts executable (Linux/macOS)
chmod +x scripts/*.sh
```

#### 2. Environment Configuration
Edit `.env` file with your specific values:

```bash
# Database Configuration
PGUSER=postgres
PGPASSWORD=your_secure_password
PGDATABASE=ecomate

# MinIO Storage
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your_secure_password
MINIO_BUCKET=ecomate-artifacts

# AI Models
OLLAMA_URL=http://localhost:11434
VERTEX_PROJECT=your-gcp-project
VERTEX_LOCATION=us-central1
VERTEX_GEMINI_MODEL=gemini-2.5-pro

# GitHub Integration
DOCS_REPO=your-org/ecomate-docs
GH_TOKEN=your_github_token

# Parser Configuration
PARSER_STRICT=false
DEFAULT_CURRENCY=USD
CURRENCY_DEFAULT=ZAR
PRICE_DEVIATION_ALERT=0.10
```

#### 3. Infrastructure Services
```bash
# Start infrastructure services
docker compose up -d postgres minio temporal nats

# Verify services are running
docker compose ps
```

#### 4. Python Environment
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

#### 5. Service Startup
```bash
# Terminal 1: Start Temporal worker
python services/orchestrator/worker.py

# Terminal 2: Start API server
uvicorn services.api.main:app --reload --port 8080
```

### Configuration Details

#### Database Initialization
The PostgreSQL service automatically runs initialization scripts from `storage/init.sql` to set up required tables and extensions.

#### MinIO Setup
1. Access MinIO Console: http://localhost:9001
2. Login with credentials from `.env`
3. Create bucket specified in `MINIO_BUCKET`
4. Configure access policies as needed

#### Temporal Configuration
- Web UI: http://localhost:8088
- gRPC endpoint: localhost:7233
- Task queue: `ecomate-ai`

#### AI Model Setup

**Ollama (Local)**:
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama2
ollama pull codellama
```

**Google Vertex AI**:
1. Create GCP project
2. Enable Vertex AI API
3. Create service account with AI Platform permissions
4. Download service account key
5. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable

## Usage Instructions

### Detailed Operational Procedures

#### Starting the System
1. **Infrastructure**: Ensure Docker services are running
2. **Worker**: Start Temporal worker for workflow execution
3. **API**: Launch FastAPI server for external requests
4. **Monitoring**: Access web interfaces for system monitoring

#### Research Workflow
```bash
# Trigger research for specific query
curl -X POST 'http://localhost:8080/run/research' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "domestic MBBR package South Africa",
    "limit": 5
  }'

# Trigger research for specific URLs
curl -X POST 'http://localhost:8080/run/new-research' \
  -H 'Content-Type: application/json' \
  -d '{
    "urls": [
      "https://supplier1.com/pumps",
      "https://supplier2.com/uv-systems"
    ]
  }'
```

#### Price Monitoring
```bash
# Manual price monitoring
curl -X POST 'http://localhost:8080/run/price-monitor' \
  -H 'Content-Type: application/json' \
  -d '{"create_pr": true}'

# Scheduled price monitoring
curl -X POST 'http://localhost:8080/run/scheduled-price-monitor'
```

### Feature Explanations with Examples

#### Vendor-Specific Parsers
The system includes specialized parsers for different product categories:

**Pump Parser Features**:
- Flow rate extraction and conversion
- Head pressure parsing
- Power consumption analysis
- Material specification detection

**UV Reactor Parser Features**:
- UV dose calculation
- Flow capacity analysis
- Lamp specification extraction
- Treatment efficiency metrics

**Parser Selection Logic**:
```python
# Domain-based selection
parse_by_domain("https://grundfos.com/pumps")  # → pump parser
parse_by_domain("https://trojan-uv.com/systems")  # → UV parser

# Category-based selection
parse_by_category(data, "pump")  # → pump parser
parse_by_category(data, "uv")    # → UV parser
```

#### LLM Fallback Processing
When vendor parsers fail or find insufficient data, the system automatically falls back to LLM processing:

1. **Parser Attempt**: Try domain-specific parser first
2. **Validation**: Check if extracted data meets quality thresholds
3. **LLM Fallback**: Use AI models for complex extraction
4. **Evidence Collection**: Track which method was used for transparency

### Common Use Cases

#### 1. Supplier Research and Data Collection
**Scenario**: Research new suppliers for MBBR systems in South Africa

**Process**:
1. Submit research query via API
2. System crawls relevant supplier websites
3. Vendor parsers extract structured product data
4. LLM processes complex specifications
5. Results stored in PostgreSQL with vector embeddings
6. CSV reports generated and PR created in docs repository

#### 2. Automated Price Monitoring
**Scenario**: Daily price tracking for existing suppliers

**Process**:
1. Scheduled workflow triggers price monitoring
2. System revisits known product URLs
3. Parsers extract current pricing information
4. Price changes calculated and flagged
5. Deviation alerts generated for significant changes
6. Updated pricing data committed to documentation

#### 3. Product Specification Analysis
**Scenario**: Compare pump specifications across multiple suppliers

**Process**:
1. Research workflow collects pump data
2. Pump parser extracts technical specifications
3. Unit conversion normalizes measurements
4. Vector database enables semantic search
5. Comparative analysis reports generated

## API Documentation

### Endpoint Specifications

#### Research Endpoints

**POST /run/research**
- **Purpose**: Trigger research workflow with query-based crawling
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "query": "string",    // Search query for supplier research
    "limit": 5           // Maximum number of URLs to process
  }
  ```
- **Response**: Workflow execution results with extracted data
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request parameters
  - `500`: Internal server error

**POST /run/new-research**
- **Purpose**: Trigger research workflow for specific URLs
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "urls": ["string"]   // Array of URLs to crawl and extract
  }
  ```
- **Response**: Structured data extraction results

#### Price Monitoring Endpoints

**POST /run/price-monitor**
- **Purpose**: Manual price monitoring execution
- **Request Body**:
  ```json
  {
    "create_pr": true    // Whether to create GitHub PR with results
  }
  ```
- **Response**: Price monitoring results and change summary

**POST /run/scheduled-price-monitor**
- **Purpose**: Scheduled price monitoring (always creates PR)
- **Request Body**: None
- **Response**: Automated monitoring results

### Request/Response Examples

#### Research Request Example
```bash
curl -X POST 'http://localhost:8080/run/research' \
  -H 'Content-Type: application/json' \
  -d '{
    "query": "submersible pumps wastewater treatment",
    "limit": 3
  }'
```

#### Research Response Example
```json
{
  "workflow_id": "research-submersible-12345",
  "status": "completed",
  "results": {
    "suppliers_found": 3,
    "products_extracted": 15,
    "parser_success_rate": 0.8,
    "llm_fallback_used": 3,
    "data_quality_score": 0.92
  },
  "artifacts": {
    "csv_file": "suppliers_20240115.csv",
    "pr_url": "https://github.com/org/ecomate-docs/pull/123"
  }
}
```

#### Price Monitor Response Example
```json
{
  "workflow_id": "price-monitor-67890",
  "status": "completed",
  "results": {
    "products_monitored": 45,
    "price_changes_detected": 7,
    "significant_deviations": 2,
    "average_change_percent": 0.03
  },
  "changes": [
    {
      "product_id": "pump-grundfos-123",
      "old_price": 1500.00,
      "new_price": 1650.00,
      "change_percent": 0.10,
      "currency": "USD"
    }
  ]
}
```

### Authentication Requirements

#### Internal Services
- **No Authentication**: API endpoints are currently open for internal use
- **Network Security**: Recommended to run behind firewall or VPN
- **Future Enhancement**: JWT or API key authentication planned

#### External Integrations
- **GitHub**: Personal Access Token (PAT) required for PR creation
  - Scope: `repo` for private repositories
  - Configuration: Set `GH_TOKEN` in environment
- **Google Vertex AI**: Service Account credentials required
  - Permissions: AI Platform User, Vertex AI User
  - Configuration: Set `GOOGLE_APPLICATION_CREDENTIALS`

## Troubleshooting

### Quick Diagnostics

#### System Health Check
```bash
# Check all services status
docker compose ps

# Verify API health
curl http://localhost:8080/health

# Check Temporal UI
open http://localhost:8088

# Test database connection
psql -h localhost -U postgres -d ecomate -c "SELECT version();"
```

#### Common Issues & Solutions

**🔴 Service Won't Start**
```bash
# Check logs for specific service
docker compose logs [service-name]

# Restart specific service
docker compose restart [service-name]

# Full system restart
docker compose down && docker compose up -d
```

**🔴 Port Conflicts**
```bash
# Check what's using the port
lsof -i :8080  # or netstat -tulpn | grep 8080

# Kill process using port
sudo kill -9 [PID]
```

**🔴 Database Connection Issues**
```bash
# Reset database
docker compose down postgres
docker volume rm ecomate-ai_postgres_data
docker compose up -d postgres

# Wait for initialization
sleep 30
```

## Maintenance Guide

### Troubleshooting Procedures

#### Common Issues and Solutions

**Issue: Temporal Worker Connection Failed**
```
Error: Failed to connect to Temporal server at localhost:7233
```
**Solution**:
1. Verify Temporal service is running: `docker compose ps temporal`
2. Check port availability: `netstat -an | grep 7233`
3. Restart Temporal service: `docker compose restart temporal`
4. Wait 30 seconds for service initialization

**Issue: Parser Extraction Failures**
```
Warning: Parser failed, falling back to LLM processing
```
**Solution**:
1. Check website structure changes
2. Update parser selectors in `services/parsers/`
3. Verify network connectivity to target sites
4. Review parser logs for specific error details

**Issue: MinIO Storage Errors**
```
Error: Unable to upload artifact to MinIO
```
**Solution**:
1. Verify MinIO service: `docker compose ps minio`
2. Check bucket exists and permissions
3. Validate credentials in `.env`
4. Test connectivity: `curl http://localhost:9000/minio/health/live`

**Issue: Database Connection Errors**
```
Error: Could not connect to PostgreSQL database
```
**Solution**:
1. Check PostgreSQL service: `docker compose ps postgres`
2. Verify credentials in `.env`
3. Test connection: `psql -h localhost -U postgres -d ecomate`
4. Check database initialization logs

#### Performance Optimization

**Slow Research Workflows**:
1. Increase worker concurrency in `worker.py`
2. Optimize parser selectors for faster extraction
3. Implement caching for frequently accessed sites
4. Monitor memory usage and adjust limits

**High Memory Usage**:
1. Limit concurrent workflow executions
2. Optimize LLM model selection
3. Implement result streaming for large datasets
4. Monitor Docker container resource limits

### Update and Upgrade Instructions

#### System Updates

**Python Dependencies**:
```bash
# Update requirements
pip install --upgrade -r requirements.txt

# Check for security vulnerabilities
pip audit

# Update specific packages
pip install --upgrade pydantic temporalio
```

**Docker Services**:
```bash
# Update service images
docker compose pull

# Restart with new images
docker compose down
docker compose up -d

# Clean up old images
docker image prune
```

**Database Migrations**:
```bash
# Backup database
docker exec postgres pg_dump -U postgres ecomate > backup.sql

# Apply schema changes
psql -h localhost -U postgres -d ecomate -f migrations/001_add_parser_metadata.sql
```

#### Configuration Updates

**Environment Variables**:
1. Compare `.env.example` with current `.env`
2. Add new required variables
3. Update deprecated settings
4. Restart services to apply changes

**Parser Updates**:
1. Update parser logic in `services/parsers/`
2. Test with demo script: `python services/parsers/_demo_test.py`
3. Deploy updated parsers
4. Monitor extraction success rates

#### Monitoring and Alerts

**Health Checks**:
```bash
# API health
curl http://localhost:8080/health

# Temporal health
curl http://localhost:8088/api/v1/namespaces

# Database health
psql -h localhost -U postgres -d ecomate -c "SELECT 1;"
```

**Log Monitoring**:
```bash
# Application logs
tail -f logs/ecomate-ai.log

# Docker service logs
docker compose logs -f temporal
docker compose logs -f postgres
```

## Development

### Development Environment Setup

#### Local Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Start development server with hot reload
uvicorn services.api.main:app --reload --port 8080
```

#### Testing
```bash
# Run all tests with coverage
pytest --cov=services tests/

# Run specific test categories
pytest tests/unit/  # Unit tests only
pytest tests/integration/  # Integration tests only

# Run tests with verbose output
pytest -v -s tests/
```

#### Debugging
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debugger
python -m pdb services/api/main.py

# Profile performance
python -m cProfile -o profile.stats services/parsers/_demo_test.py
```

## Contribution Guidelines

### Code Standards

#### Python Code Style
- **Formatter**: Black with 88-character line length
- **Linter**: Ruff for fast Python linting
- **Type Hints**: Required for all function signatures
- **Docstrings**: Google-style docstrings for all public functions

**Example**:
```python
def extract_pump_specifications(
    html_content: str, 
    base_url: str
) -> list[Pump]:
    """Extract pump specifications from HTML content.
    
    Args:
        html_content: Raw HTML content from supplier page
        base_url: Base URL for resolving relative links
        
    Returns:
        List of Pump objects with extracted specifications
        
    Raises:
        ParserError: When HTML structure is incompatible
    """
    # Implementation here
    pass
```

#### Code Organization
- **Services**: Separate directories for API, orchestrator, parsers, utils
- **Models**: Pydantic models in dedicated files
- **Configuration**: Environment-based settings with validation
- **Error Handling**: Custom exceptions with descriptive messages

#### Dependencies
- **Pinned Versions**: All dependencies must specify exact versions
- **Security**: Regular security audits with `pip audit`
- **Minimal**: Only include necessary dependencies
- **Documentation**: Document purpose of each major dependency

### Testing Requirements

#### Unit Tests
```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=services tests/

# Run specific test file
pytest tests/test_parsers.py
```

#### Test Structure
```
tests/
├── unit/
│   ├── test_parsers.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/
│   ├── test_workflows.py
│   └── test_api.py
└── fixtures/
    ├── sample_html/
    └── test_data.json
```

#### Test Requirements
- **Coverage**: Minimum 80% code coverage
- **Isolation**: Tests must not depend on external services
- **Fixtures**: Use realistic test data from actual supplier sites
- **Mocking**: Mock external API calls and file operations

#### Parser Testing
```python
# Test parser with sample data
def test_pump_parser_grundfos():
    with open('fixtures/grundfos_pumps.html') as f:
        html = f.read()
    
    pumps = parse_pump_table(html, 'https://grundfos.com')
    
    assert len(pumps) > 0
    assert all(pump.flow_rate_lpm > 0 for pump in pumps)
    assert all(pump.head_meters > 0 for pump in pumps)
```

### Pull Request Process

#### Before Submitting
1. **Branch**: Create feature branch from `main`
2. **Tests**: Ensure all tests pass locally
3. **Linting**: Run code formatting and linting
4. **Documentation**: Update relevant documentation
5. **Changelog**: Add entry to `CHANGELOG.md`

#### PR Requirements
- **Title**: Clear, descriptive title with scope
- **Description**: Detailed explanation of changes
- **Testing**: Evidence of testing (screenshots, test output)
- **Breaking Changes**: Clearly marked if applicable
- **Dependencies**: List any new dependencies added

#### Review Process
1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one approving review required
3. **Testing**: Manual testing for significant changes
4. **Documentation**: Review of updated documentation
5. **Merge**: Squash and merge after approval

#### Example PR Template
```markdown
## Description
Brief description of changes and motivation.

## Changes Made
- [ ] Added new UV reactor parser
- [ ] Updated normalization functions
- [ ] Added unit tests

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Breaking Changes
None / List any breaking changes

## Dependencies
List any new dependencies or version updates
```

#### Commit Message Format
```
type(scope): description

feat(parsers): add UV reactor specification extraction
fix(api): handle timeout errors in research endpoint
docs(readme): update installation instructions
test(parsers): add comprehensive pump parser tests
```

---

## Support and Resources

- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Technical discussions in GitHub Discussions
- **Documentation**: Additional docs in `docs/` directory
- **Monitoring**: Temporal Web UI at http://localhost:8088
- **Storage**: MinIO Console at http://localhost:9001

## License

This project is licensed under the MIT License - see the LICENSE file for details.