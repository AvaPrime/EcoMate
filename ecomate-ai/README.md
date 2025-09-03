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

EcoMate AI is an intelligent automation platform designed to streamline environmental technology research, supplier management, compliance monitoring, and business operations. The system provides:

- **Automated Research**: Web crawling and data extraction for environmental technology suppliers and products with intelligent content parsing
- **Price Monitoring**: Continuous tracking of product prices with deviation alerts, automated reporting, and GitHub integration
- **Vendor-Specific Parsing**: Specialized parsers for pump and UV reactor specifications with intelligent fallback to LLM processing
- **Proposal & Computation**: Automated generation of technical proposals and cost calculations for environmental systems
- **E-commerce Integration**: Seamless catalog synchronization with Shopify, WooCommerce, and Medusa platforms
- **Maintenance Scheduling**: Predictive maintenance planning and automated scheduling for environmental equipment
- **Compliance Management**: Automated spec drafting and compliance checks for environmental systems with regulatory rule validation
- **Telemetry & Alerts**: Real-time system monitoring with intelligent alerting and digital twin lite functionality
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
- **Proposal Generation**: Automated technical proposal creation with cost calculations and template management
- **E-commerce Catalog Management**: Multi-platform product synchronization and inventory management
- **Maintenance Planning**: Predictive maintenance scheduling with equipment lifecycle tracking
- **Compliance Validation**: Automated regulatory compliance checks with customizable rule engines
- **Telemetry Processing**: Real-time system monitoring with intelligent alerting and anomaly detection
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

# E-commerce Integration
SHOPIFY_API_KEY=your_shopify_api_key
SHOPIFY_API_SECRET=your_shopify_secret
SHOPIFY_WEBHOOK_SECRET=your_webhook_secret
WOOCOMMERCE_CONSUMER_KEY=your_woocommerce_key
WOOCOMMERCE_CONSUMER_SECRET=your_woocommerce_secret
MEDUSA_API_KEY=your_medusa_api_key
MEDUSA_BASE_URL=http://localhost:9000

# Proposal Service
PROPOSAL_TEMPLATE_PATH=./services/proposal/templates
PROPOSAL_DEFAULT_MARGIN=0.15
PROPOSAL_CURRENCY=USD

# Maintenance Service
MAINTENANCE_SCHEDULE_PATH=./data/maintenance_schedule.csv
MAINTENANCE_DEFAULT_INTERVAL=90
MAINTENANCE_ALERT_DAYS=7

# Compliance Service
COMPLIANCE_RULES_PATH=./services/compliance/rules

# Telemetry Service
TELEMETRY_ALERT_HEADROOM=0.10
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

#### 5. Service Dependencies Setup

**E-commerce Platform Configuration**:
- **Shopify**: Create private app and obtain API credentials
- **WooCommerce**: Generate consumer key/secret from WooCommerce > Settings > Advanced > REST API
- **Medusa**: Set up Medusa server and obtain API key

**Compliance Rules Setup**:
```bash
# Create compliance rules directory
mkdir -p services/compliance/rules

# Copy default rules (if available)
cp data/compliance_rules/* services/compliance/rules/
```

**Proposal Templates Setup**:
```bash
# Create proposal templates directory
mkdir -p services/proposal/templates

# Copy default templates (if available)
cp data/proposal_templates/* services/proposal/templates/
```

#### 6. Service Startup
```bash
# Terminal 1: Start Temporal worker (includes all new workflows)
python services/orchestrator/worker.py

# Terminal 2: Start API server (includes all new endpoints)
uvicorn services.api.main:app --reload --port 8080
```

**Service Health Verification**:
```bash
# Test core services
curl http://localhost:8080/health

# Test new service endpoints
curl -X POST http://localhost:8080/proposal/generate -H "Content-Type: application/json" -d '{"project_name":"test"}'
curl -X POST http://localhost:8080/catalog/sync -H "Content-Type: application/json" -d '{"platform":"shopify"}'
curl -X POST http://localhost:8080/maintenance/schedule -H "Content-Type: application/json" -d '{"equipment_id":"test"}'
curl -X POST http://localhost:8080/compliance/check -H "Content-Type: application/json" -d '{"system_specs":{}}'
curl -X POST http://localhost:8080/telemetry/ingest -H "Content-Type: application/json" -d '{"system_id":"test","metrics":{}}'
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

### New Service Workflows

#### 4. Proposal & Computation Service
**Scenario**: Generate technical proposals with cost calculations

```bash
# Generate proposal for water treatment system
curl -X POST 'http://localhost:8080/run/proposal' \
  -H 'Content-Type: application/json' \
  -d '{
    "project_requirements": {
      "flow_rate": "100 m3/h",
      "treatment_type": "MBBR",
      "location": "Cape Town, South Africa",
      "budget_range": "50000-100000 USD"
    },
    "include_calculations": true,
    "format": "pdf"
  }'
```

**Process**:
1. Analyze project requirements and constraints
2. Query product database for suitable equipment
3. Perform engineering calculations (sizing, capacity)
4. Generate cost estimates with supplier pricing
5. Create formatted proposal document
6. Store proposal data for future reference

#### 5. E-commerce Catalog Integration
**Scenario**: Sync product data with e-commerce platforms

```bash
# Sync products to Shopify store
curl -X POST 'http://localhost:8080/run/catalog-sync' \
  -H 'Content-Type: application/json' \
  -d '{
    "platform": "shopify",
    "store_url": "https://mystore.myshopify.com",
    "product_categories": ["pumps", "uv-systems"],
    "sync_mode": "incremental"
  }'

# Update WooCommerce inventory
curl -X POST 'http://localhost:8080/run/inventory-update' \
  -H 'Content-Type: application/json' \
  -d '{
    "platform": "woocommerce",
    "site_url": "https://mysite.com",
    "update_stock": true,
    "update_pricing": true
  }'
```

**Process**:
1. Connect to configured e-commerce platform APIs
2. Map internal product data to platform schemas
3. Sync product information, pricing, and inventory
4. Handle platform-specific requirements and limitations
5. Generate sync reports and error logs
6. Schedule automated sync workflows

#### 6. Maintenance Scheduling
**Scenario**: Schedule and track equipment maintenance

```bash
# Schedule maintenance for installed equipment
curl -X POST 'http://localhost:8080/run/schedule-maintenance' \
  -H 'Content-Type: application/json' \
  -d '{
    "equipment_id": "PUMP-001",
    "maintenance_type": "preventive",
    "schedule": {
      "frequency": "quarterly",
      "next_date": "2024-04-01"
    },
    "technician_assignment": "auto"
  }'

# Get maintenance schedule
curl -X GET 'http://localhost:8080/maintenance/schedule?month=2024-03'
```

**Process**:
1. Analyze equipment specifications and usage patterns
2. Calculate optimal maintenance intervals
3. Schedule maintenance tasks in calendar system
4. Assign technicians based on expertise and availability
5. Generate maintenance checklists and procedures
6. Track completion status and generate reports

#### 7. Compliance Management
**Scenario**: Monitor regulatory compliance and certifications

```bash
# Check compliance status for products
curl -X POST 'http://localhost:8080/run/compliance-check' \
  -H 'Content-Type: application/json' \
  -d '{
    "product_ids": ["PUMP-001", "UV-002"],
    "regulations": ["SANS", "ISO", "CE"],
    "market": "south_africa"
  }'

# Generate compliance report
curl -X POST 'http://localhost:8080/run/compliance-report' \
  -H 'Content-Type: application/json' \
  -d '{
    "report_type": "certification_status",
    "date_range": "2024-Q1",
    "format": "pdf"
  }'
```

**Process**:
1. Cross-reference product specifications with regulations
2. Check certification validity and expiration dates
3. Identify compliance gaps and requirements
4. Generate compliance reports and recommendations
5. Track regulatory updates and changes
6. Alert stakeholders of compliance issues

#### 8. Telemetry & Alerts System
**Scenario**: Monitor system health and performance metrics

```bash
# Configure monitoring alerts
curl -X POST 'http://localhost:8080/telemetry/alerts' \
  -H 'Content-Type: application/json' \
  -d '{
    "alert_type": "performance",
    "metric": "response_time",
    "threshold": 5000,
    "notification_channels": ["email", "slack"]
  }'

# Get system metrics
curl -X GET 'http://localhost:8080/telemetry/metrics?timerange=1h'
```

**Process**:
1. Collect system performance and health metrics
2. Monitor API response times and error rates
3. Track resource utilization (CPU, memory, storage)
4. Analyze workflow execution patterns
5. Generate alerts for anomalies and thresholds
6. Provide dashboards for real-time monitoring

### Integration Examples

#### Multi-Service Workflow
**Scenario**: Complete project lifecycle from research to delivery

```bash
# 1. Research suppliers for project requirements
curl -X POST 'http://localhost:8080/run/research' \
  -d '{"query": "MBBR systems 500m3/day South Africa", "limit": 10}'

# 2. Generate technical proposal
curl -X POST 'http://localhost:8080/run/proposal' \
  -d '{"project_requirements": {...}, "include_calculations": true}'

# 3. Check compliance requirements
curl -X POST 'http://localhost:8080/run/compliance-check' \
  -d '{"product_ids": [...], "regulations": ["SANS"], "market": "south_africa"}'

# 4. Schedule installation and maintenance
curl -X POST 'http://localhost:8080/run/schedule-maintenance' \
  -d '{"equipment_id": "...", "maintenance_type": "installation"}'

# 5. Sync to e-commerce platform
curl -X POST 'http://localhost:8080/run/catalog-sync' \
  -d '{"platform": "shopify", "product_categories": [...]}'
```

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

#### Proposal & Computation Endpoints

**POST /proposal/generate**
- **Purpose**: Generate technical proposals with cost calculations
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "project_name": "string",
    "requirements": {
      "flow_rate": "number",
      "treatment_type": "string",
      "budget_range": "string"
    },
    "template_id": "string"  // Optional: specific template to use
  }
  ```
- **Response**: Generated proposal with cost breakdown and technical specifications
- **Status Codes**: `200`: Success, `400`: Invalid parameters, `500`: Generation error

#### E-commerce Catalog Endpoints

**POST /catalog/sync**
- **Purpose**: Synchronize product catalog with e-commerce platforms
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "platform": "shopify|woocommerce|medusa",
    "store_config": {
      "api_key": "string",
      "store_url": "string",
      "webhook_secret": "string"
    },
    "sync_options": {
      "full_sync": "boolean",
      "categories": ["string"]
    }
  }
  ```
- **Response**: Synchronization results with product counts and status
- **Status Codes**: `200`: Success, `401`: Authentication failed, `500`: Sync error

#### Maintenance Scheduling Endpoints

**POST /maintenance/schedule**
- **Purpose**: Create predictive maintenance schedules
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "equipment_id": "string",
    "equipment_type": "string",
    "installation_date": "ISO8601",
    "operating_hours": "number",
    "maintenance_type": "preventive|predictive|corrective"
  }
  ```
- **Response**: Generated maintenance schedule with recommended intervals
- **Status Codes**: `200`: Success, `404`: Equipment not found, `500`: Scheduling error

**GET /maintenance/plan/{equipment_id}**
- **Purpose**: Retrieve maintenance plan for specific equipment
- **Response**: Detailed maintenance schedule and history

#### Compliance Management Endpoints

**POST /compliance/check**
- **Purpose**: Validate system specifications against regulatory requirements
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "system_specs": {
      "flow_rate": "number",
      "treatment_efficiency": "number",
      "discharge_quality": "object"
    },
    "regulations": ["string"],  // Regulatory frameworks to check
    "jurisdiction": "string"
  }
  ```
- **Response**: Compliance status with detailed validation results
- **Status Codes**: `200`: Success, `400`: Invalid specs, `500`: Validation error

#### Telemetry & Alerts Endpoints

**POST /telemetry/ingest**
- **Purpose**: Ingest real-time system telemetry data
- **Content-Type**: `application/json`
- **Request Body**:
  ```json
  {
    "system_id": "string",
    "metrics": {
      "flow_rate": "number",
      "pressure": "number",
      "temperature": "number",
      "power_consumption": "number",
      "efficiency": "number"
    },
    "timestamp": "ISO8601"
  }
  ```
- **Response**: Processing confirmation and alert status
- **Status Codes**: `200`: Success, `400`: Invalid data, `500`: Processing error

### Request/Response Examples for New Services

#### Proposal Generation Example
```bash
curl -X POST 'http://localhost:8080/proposal/generate' \
  -H 'Content-Type: application/json' \
  -d '{
    "project_name": "Municipal Wastewater Treatment Upgrade",
    "requirements": {
      "flow_rate": 1000,
      "treatment_type": "biological",
      "budget_range": "500000-750000"
    }
  }'
```

#### Catalog Sync Example
```bash
curl -X POST 'http://localhost:8080/catalog/sync' \
  -H 'Content-Type: application/json' \
  -d '{
    "platform": "shopify",
    "store_config": {
      "api_key": "your-api-key",
      "store_url": "your-store.myshopify.com"
    },
    "sync_options": {
      "full_sync": true,
      "categories": ["pumps", "filters"]
    }
  }'
```

#### Maintenance Schedule Example
```bash
curl -X POST 'http://localhost:8080/maintenance/schedule' \
  -H 'Content-Type: application/json' \
  -d '{
    "equipment_id": "pump-001",
    "equipment_type": "submersible_pump",
    "installation_date": "2024-01-15T00:00:00Z",
    "operating_hours": 2400,
    "maintenance_type": "predictive"
  }'
```

#### Compliance Check Example
```bash
curl -X POST 'http://localhost:8080/compliance/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "system_specs": {
      "flow_rate": 500,
      "treatment_efficiency": 0.95,
      "discharge_quality": {
        "bod": 10,
        "tss": 15,
        "ph": 7.2
      }
    },
    "regulations": ["EPA_NPDES", "LOCAL_DISCHARGE"],
    "jurisdiction": "US_CA"
  }'
```

#### Telemetry Ingestion Example
```bash
curl -X POST 'http://localhost:8080/telemetry/ingest' \
  -H 'Content-Type: application/json' \
  -d '{
    "system_id": "plant-001",
    "metrics": {
      "flow_rate": 450.5,
      "pressure": 2.3,
      "temperature": 22.1,
      "power_consumption": 15.2,
      "efficiency": 0.92
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }'
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

#### New Services Troubleshooting

**🔴 Proposal Generation Service Issues**

*Issue: Proposal generation fails with calculation errors*
```
Error: Unable to calculate system sizing for given parameters
```
**Solution**:
1. Verify project requirements format in request body
2. Check unit conversion settings in environment variables
3. Validate equipment database has required specifications
4. Review calculation engine logs: `docker compose logs proposal-service`

*Issue: PDF generation timeout*
```
Error: Proposal PDF generation timed out after 30 seconds
```
**Solution**:
1. Increase PDF generation timeout in configuration
2. Optimize proposal template complexity
3. Check WeasyPrint dependencies: `pip list | grep weasyprint`
4. Monitor memory usage during PDF generation

**🔴 E-commerce Integration Issues**

*Issue: Shopify API authentication failed*
```
Error: 401 Unauthorized - Invalid API credentials
```
**Solution**:
1. Verify Shopify API credentials in `.env`
2. Check API permissions and scopes
3. Regenerate API tokens if expired
4. Test connection: `curl -H "X-Shopify-Access-Token: TOKEN" https://SHOP.myshopify.com/admin/api/2023-10/shop.json`

*Issue: Product sync conflicts*
```
Warning: Product SKU conflicts detected during sync
```
**Solution**:
1. Review product mapping configuration
2. Implement conflict resolution strategy
3. Check for duplicate SKUs in source data
4. Use incremental sync mode to avoid conflicts

**🔴 Maintenance Scheduler Issues**

*Issue: Calendar integration not working*
```
Error: Failed to connect to CalDAV server
```
**Solution**:
1. Verify CalDAV server URL and credentials
2. Check network connectivity to calendar server
3. Test CalDAV connection manually
4. Review calendar integration logs

*Issue: Maintenance notifications not sent*
```
Warning: Failed to send maintenance reminder notifications
```
**Solution**:
1. Check notification channel configuration
2. Verify SMTP/Slack webhook settings
3. Test notification channels individually
4. Review notification service logs

**🔴 Compliance Management Issues**

*Issue: Regulation database out of date*
```
Warning: Regulation data is older than 30 days
```
**Solution**:
1. Update regulation database manually
2. Check automated update schedule
3. Verify external API connectivity
4. Review regulation update logs

*Issue: Certification validation errors*
```
Error: Unable to validate certification status
```
**Solution**:
1. Check certification database integrity
2. Verify certification authority APIs
3. Update certification validation rules
4. Review compliance check logs

**🔴 Telemetry & Alerts Issues**

*Issue: Metrics not being collected*
```
Error: Prometheus metrics endpoint unreachable
```
**Solution**:
1. Verify Prometheus configuration
2. Check metrics endpoint accessibility
3. Review metric collection intervals
4. Test metrics endpoint: `curl http://localhost:8080/metrics`

*Issue: Alert notifications not working*
```
Error: Failed to send alert to configured channels
```
**Solution**:
1. Check alert channel configuration
2. Verify webhook URLs and API keys
3. Test alert channels individually
4. Review alert manager logs

#### Service-Specific Diagnostics

**Proposal Service Health Check**:
```bash
# Test proposal generation
curl -X POST 'http://localhost:8080/run/proposal' \
  -H 'Content-Type: application/json' \
  -d '{"project_requirements": {"flow_rate": "100 m3/h", "treatment_type": "MBBR"}}'

# Check calculation engine
curl http://localhost:8080/proposal/health
```

**E-commerce Service Health Check**:
```bash
# Test platform connectivity
curl -X GET 'http://localhost:8080/catalog/platforms'

# Verify sync status
curl -X GET 'http://localhost:8080/catalog/sync-status'
```

**Maintenance Service Health Check**:
```bash
# Test scheduling functionality
curl -X GET 'http://localhost:8080/maintenance/health'

# Check calendar integration
curl -X GET 'http://localhost:8080/maintenance/calendar-status'
```

**Compliance Service Health Check**:
```bash
# Test compliance checking
curl -X GET 'http://localhost:8080/compliance/health'

# Verify regulation database
curl -X GET 'http://localhost:8080/compliance/regulations/status'
```

**Telemetry Service Health Check**:
```bash
# Test metrics collection
curl -X GET 'http://localhost:8080/telemetry/health'

# Check alert system
curl -X GET 'http://localhost:8080/telemetry/alerts/status'
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
python -m pdb services.api.main.py

# Profile performance
python -m cProfile -o profile.stats services/parsers/_demo_test.py
```

### New Services Testing Procedures

#### 🧪 Proposal & Computation Service Testing

**Unit Tests**:
```bash
# Test calculation engine
pytest tests/unit/test_proposal_calculations.py -v

# Test PDF generation
pytest tests/unit/test_proposal_pdf.py -v

# Test template rendering
pytest tests/unit/test_proposal_templates.py -v
```

**Integration Tests**:
```bash
# Test complete proposal workflow
pytest tests/integration/test_proposal_workflow.py -v

# Test API endpoints
pytest tests/integration/test_proposal_api.py -v
```

**Manual Testing**:
```bash
# Test proposal generation with sample data
curl -X POST 'http://localhost:8080/run/proposal' \
  -H 'Content-Type: application/json' \
  -d '{
    "project_name": "Test WWTP",
    "requirements": {
      "flow_rate": 500,
      "treatment_type": "MBBR",
      "budget_range": "200000-300000"
    },
    "include_calculations": true,
    "generate_pdf": true
  }'

# Verify calculation accuracy
python tests/manual/verify_calculations.py

# Test PDF output quality
python tests/manual/check_pdf_generation.py
```

#### 🛒 E-commerce Catalog Service Testing

**Unit Tests**:
```bash
# Test platform connectors
pytest tests/unit/test_shopify_connector.py -v
pytest tests/unit/test_woocommerce_connector.py -v
pytest tests/unit/test_medusa_connector.py -v

# Test product mapping
pytest tests/unit/test_product_mapping.py -v

# Test inventory sync
pytest tests/unit/test_inventory_sync.py -v
```

**Integration Tests**:
```bash
# Test complete sync workflow
pytest tests/integration/test_catalog_sync.py -v

# Test conflict resolution
pytest tests/integration/test_sync_conflicts.py -v
```

**Manual Testing**:
```bash
# Test Shopify integration
curl -X POST 'http://localhost:8080/catalog/sync' \
  -H 'Content-Type: application/json' \
  -d '{
    "platform": "shopify",
    "store_config": {
      "api_key": "test-key",
      "store_url": "test-store.myshopify.com"
    },
    "sync_options": {
      "dry_run": true,
      "categories": ["pumps"]
    }
  }'

# Test product mapping accuracy
python tests/manual/verify_product_mapping.py

# Test sync performance
python tests/manual/benchmark_sync_speed.py
```

#### 🔧 Maintenance Scheduler Testing

**Unit Tests**:
```bash
# Test scheduling algorithms
pytest tests/unit/test_maintenance_algorithms.py -v

# Test calendar integration
pytest tests/unit/test_calendar_integration.py -v

# Test notification system
pytest tests/unit/test_maintenance_notifications.py -v
```

**Integration Tests**:
```bash
# Test complete scheduling workflow
pytest tests/integration/test_maintenance_workflow.py -v

# Test external calendar sync
pytest tests/integration/test_calendar_sync.py -v
```

**Manual Testing**:
```bash
# Test maintenance scheduling
curl -X POST 'http://localhost:8080/maintenance/schedule' \
  -H 'Content-Type: application/json' \
  -d '{
    "equipment_id": "PUMP-001",
    "equipment_type": "centrifugal_pump",
    "installation_date": "2024-01-15",
    "operating_hours": 2000,
    "maintenance_type": "predictive"
  }'

# Test calendar integration
python tests/manual/test_calendar_sync.py

# Verify notification delivery
python tests/manual/test_notifications.py
```

#### ✅ Compliance Management Testing

**Unit Tests**:
```bash
# Test regulation parsing
pytest tests/unit/test_regulation_parser.py -v

# Test compliance checking
pytest tests/unit/test_compliance_checker.py -v

# Test certification validation
pytest tests/unit/test_certification_validator.py -v
```

**Integration Tests**:
```bash
# Test complete compliance workflow
pytest tests/integration/test_compliance_workflow.py -v

# Test regulation updates
pytest tests/integration/test_regulation_updates.py -v
```

**Manual Testing**:
```bash
# Test compliance checking
curl -X POST 'http://localhost:8080/compliance/check' \
  -H 'Content-Type: application/json' \
  -d '{
    "system_specs": {
      "flow_rate": 1000,
      "treatment_efficiency": 95,
      "discharge_quality": {
        "bod": 10,
        "cod": 30,
        "tss": 15
      }
    },
    "regulations": ["SANS", "ISO"],
    "jurisdiction": "south_africa"
  }'

# Test regulation database updates
python tests/manual/test_regulation_updates.py

# Verify compliance report generation
python tests/manual/test_compliance_reports.py
```

#### 📊 Telemetry & Alerts Testing

**Unit Tests**:
```bash
# Test metrics collection
pytest tests/unit/test_metrics_collector.py -v

# Test alert engine
pytest tests/unit/test_alert_engine.py -v

# Test notification channels
pytest tests/unit/test_notification_channels.py -v
```

**Integration Tests**:
```bash
# Test complete telemetry workflow
pytest tests/integration/test_telemetry_workflow.py -v

# Test alert delivery
pytest tests/integration/test_alert_delivery.py -v
```

**Manual Testing**:
```bash
# Test telemetry ingestion
curl -X POST 'http://localhost:8080/telemetry/ingest' \
  -H 'Content-Type: application/json' \
  -d '{
    "system_id": "WWTP-001",
    "metrics": {
      "flow_rate": 850,
      "pressure": 2.5,
      "temperature": 22.5,
      "power_consumption": 45.2,
      "efficiency": 94.8
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }'

# Test alert configuration
curl -X POST 'http://localhost:8080/telemetry/alerts' \
  -H 'Content-Type: application/json' \
  -d '{
    "alert_type": "threshold",
    "metric": "efficiency",
    "threshold": 90,
    "operator": "less_than",
    "notification_channels": ["email", "slack"]
  }'

# Verify metrics dashboard
python tests/manual/test_metrics_dashboard.py

# Test alert response times
python tests/manual/benchmark_alert_latency.py
```

### Cross-Service Integration Testing

#### Multi-Service Workflow Tests
```bash
# Test complete project lifecycle
pytest tests/integration/test_project_lifecycle.py -v

# Test service communication
pytest tests/integration/test_service_communication.py -v

# Test data consistency across services
pytest tests/integration/test_data_consistency.py -v
```

#### Performance Testing
```bash
# Load testing for new endpoints
python tests/performance/load_test_new_services.py

# Stress testing for concurrent operations
python tests/performance/stress_test_concurrent.py

# Memory usage profiling
python tests/performance/profile_memory_usage.py
```

#### End-to-End Testing
```bash
# Complete system integration test
pytest tests/e2e/test_complete_system.py -v

# User journey testing
pytest tests/e2e/test_user_journeys.py -v

# API contract testing
pytest tests/e2e/test_api_contracts.py -v
```

### Test Data Management

#### Test Fixtures for New Services
```bash
# Generate test data for proposals
python tests/fixtures/generate_proposal_data.py

# Create mock e-commerce data
python tests/fixtures/generate_catalog_data.py

# Setup maintenance test scenarios
python tests/fixtures/generate_maintenance_data.py

# Create compliance test cases
python tests/fixtures/generate_compliance_data.py

# Generate telemetry test data
python tests/fixtures/generate_telemetry_data.py
```

#### Database Test Setup
```bash
# Setup test database with new service schemas
python tests/setup/setup_test_database.py

# Seed test data for all services
python tests/setup/seed_test_data.py

# Clean test environment
python tests/setup/cleanup_test_env.py
```

### Continuous Integration Testing

#### GitHub Actions Workflow
```yaml
# .github/workflows/test-new-services.yml
name: Test New Services
on: [push, pull_request]
jobs:
  test-new-services:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run new service tests
        run: |
          pytest tests/unit/test_proposal* -v
          pytest tests/unit/test_catalog* -v
          pytest tests/unit/test_maintenance* -v
          pytest tests/unit/test_compliance* -v
          pytest tests/unit/test_telemetry* -v
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Generate coverage report
        run: pytest --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### Quality Gates
```bash
# Code coverage requirements
pytest --cov=services --cov-fail-under=80

# Code quality checks
ruff check services/
black --check services/
mypy services/

# Security scanning
bandit -r services/
safety check
```

### Test Data Management

#### Test Fixtures for New Services
```bash
# Generate test data for proposals
python tests/fixtures/generate_proposal_data.py

# Create mock e-commerce data
python tests/fixtures/generate_catalog_data.py

# Setup maintenance test scenarios
python tests/fixtures/generate_maintenance_data.py

# Create compliance test cases
python tests/fixtures/generate_compliance_data.py

# Generate telemetry test data
python tests/fixtures/generate_telemetry_data.py
```

#### Database Test Setup
```bash
# Setup test database with new service schemas
python tests/setup/setup_test_database.py

# Seed test data for all services
python tests/setup/seed_test_data.py

# Clean test environment
python tests/setup/cleanup_test_env.py
```

### Continuous Integration Testing

#### GitHub Actions Workflow
```yaml
# .github/workflows/test-new-services.yml
name: Test New Services
on: [push, pull_request]
jobs:
  test-new-services:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements-dev.txt
      - name: Run new service tests
        run: |
          pytest tests/unit/test_proposal* -v
          pytest tests/unit/test_catalog* -v
          pytest tests/unit/test_maintenance* -v
          pytest tests/unit/test_compliance* -v
          pytest tests/unit/test_telemetry* -v
      - name: Run integration tests
        run: pytest tests/integration/ -v
      - name: Generate coverage report
        run: pytest --cov=services --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### Quality Gates
```bash
# Code coverage requirements
pytest --cov=services --cov-fail-under=80

# Code quality checks
ruff check services/
black --check services/
mypy services/

# Security scanning
bandit -r services/
safety check
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