# EcoMate - Environmental Technology Platform

EcoMate is a comprehensive platform for environmental technology management, combining intelligent automation with comprehensive documentation. This repository contains both the documentation site and AI-powered services for research, supplier management, and compliance monitoring.

## Platform Overview

### Documentation Site (Docs as Code)
Comprehensive product, operations, and go-to-market documentation built with **MkDocs Material** and published to **GitHub Pages**. Includes automated PDF/Word exports for client deliverables.

### AI Services Platform
Intelligent automation services for environmental technology research, supplier synchronization, price monitoring, specification drafting, and compliance checks. Built with FastAPI, Temporal workflows, and advanced AI models.

## Quick Start

### Documentation Site
```bash
# Set up documentation environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Serve documentation locally
mkdocs serve  # Access at http://127.0.0.1:8000
```

### AI Services
```bash
# Navigate to AI services directory
cd ecomate-ai

# Set up environment
cp .env.example .env
# Edit .env with your configuration

# Start infrastructure services
docker compose up -d postgres minio temporal nats

# Install Python dependencies
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Start services
python services/orchestrator/worker.py  # Terminal 1
uvicorn services.api.main:app --reload --port 8080  # Terminal 2
```

## 📁 Repository Structure

```
EcoMate/
├── docs/                    # Documentation content (Markdown)
│   ├── products/           # Product specifications and guides
│   ├── operations/         # Standard operating procedures
│   ├── suppliers/          # Supplier database and RFQ templates
│   └── marketing/          # Go-to-market materials
├── ecomate-ai/             # AI Services Platform
│   ├── services/           # Microservices (API, parsers, orchestrator)
│   ├── tests/              # Comprehensive test suite
│   ├── storage/            # Database initialization
│   └── docker-compose.yml  # Infrastructure services
├── data/                   # CSV data files for documentation
├── scripts/                # Automation and export scripts
├── overrides/              # MkDocs theme customizations
└── .github/workflows/      # CI/CD automation
```

## EcoMate Roadmap & Blueprints

Our development is guided by a dynamic, unified set of artifacts:

| Document | Description |
|----------|-------------|
| [Master Index & Roadmap Overview](eco_mate_master_index_roadmap_overview.md) | Top-level entry point with links and summaries of all roadmap documents |
| [Future Roadmap (Living Document)](eco_mate_future_roadmap_living_document.md) | Phased development plan from foundation to autonomous ecosystem |
| [Production Implementation Plan](eco_mate_production_implementation_plan_drop_in_files_steps.md) | Immediate codebase-ready drop-ins and steps for Phase 1 |
| [Market & Supply Chain Data Integration](eco_mate_market_supply_chain_data_integration.md) | Vendor APIs, competitor monitoring, and alternative sourcing |
| [Regulatory & Compliance Data Integration](eco_mate_regulatory_compliance_data_integration.md) | Standards APIs, legal feeds, and public record checks |
| [Environmental & Geographic Data Integration](eco_mate_environmental_geographic_data_integration_implementation_plan.md) | Geospatial, climate, and permit-awareness enhancements |
| [Operational & Predictive Data Integration](eco_mate_operational_predictive_data_integration.md) | IoT ingestion, predictive maintenance, and digital twin modeling |

Start with the Master Index to navigate quickly to the relevant blueprint.

## 🔧 Key Features

### Documentation Platform
- **Automated Publishing**: Push to `main` triggers GitHub Actions deployment
- **Multi-format Export**: Generate PDF and DOCX versions for client delivery
- **Data Integration**: Sync CSV data with Google Sheets for collaborative editing
- **Theme Customization**: Material Design with light/dark mode toggle
- **Search Integration**: Full-text search across all documentation

### AI Services Platform
- **Intelligent Research**: Automated web crawling and data extraction from supplier websites
- **Price Monitoring**: Continuous tracking with deviation alerts and automated reporting
- **Vendor Parsers**: Specialized parsers for pumps, UV reactors, and other equipment
- **LLM Integration**: Fallback processing using Ollama and Google Vertex AI
- **Workflow Orchestration**: Reliable execution with Temporal workflows
- **Document Automation**: Automated PR creation and documentation updates

## 🛠 Technology Stack

### Documentation
- **MkDocs Material**: Modern documentation site generator
- **GitHub Pages**: Automated hosting and deployment
- **Pandoc**: Document format conversion (PDF, DOCX)
- **GitHub Actions**: CI/CD pipeline automation

### AI Services
- **FastAPI**: High-performance web API framework
- **Temporal**: Workflow orchestration and reliability
- **PostgreSQL + pgvector**: Database with vector search capabilities
- **MinIO**: S3-compatible object storage
- **Docker**: Containerized infrastructure services
- **Pydantic**: Data validation and type safety

## 📖 Documentation

### Getting Started Guides
- [AI Services Installation](ecomate-ai/README.md#installation-guide) - Complete setup instructions
- [API Documentation](ecomate-ai/README.md#api-documentation) - Endpoint specifications and examples
- [Contributing Guidelines](ecomate-ai/CONTRIBUTING.md) - Development workflow and standards

### User Guides
- [Research Workflows](ecomate-ai/README.md#research-workflow) - Automated supplier research
- [Price Monitoring](ecomate-ai/README.md#price-monitoring) - Continuous price tracking
- [Vendor Parsers](ecomate-ai/README.md#vendor-specific-parsers) - Specialized data extraction

### Operations
- [Standard Operating Procedures](docs/operations/standard-operating-procedures.md)
- [Service Contracts](docs/operations/service-contracts.md)
- [Maintenance Schedules](docs/products/wastewater/maintenance-schedule.md)

## 🚀 Deployment

### Documentation Site
- **Automatic**: Push to `main` branch triggers GitHub Actions deployment
- **Manual**: Run `mkdocs gh-deploy` for immediate deployment
- **Local Preview**: Use `mkdocs serve` for development

### AI Services
- **Development**: Docker Compose for local development environment
- **Production**: Kubernetes deployment with Helm charts (see deployment docs)
- **Monitoring**: Temporal Web UI, MinIO Console, and application metrics

## 📊 Data Management

### CSV Data Integration
- Keep tabular data in `data/*.csv` files
- Import into Google Sheets via File > Import
- Use Apps Script example in `scripts/google_sheets_sync_example.gs`
- Automated synchronization with AI services database

### Export Capabilities
- **PDF Generation**: `make pdf` - Creates client-ready PDF documentation
- **DOCX Export**: `make docx` - Word format for collaborative editing
- **Data Export**: Automated CSV generation from AI services

## 🤝 Contributing

We welcome contributions to both the documentation and AI services platforms!

### Documentation Contributions
1. Edit Markdown files in the `docs/` directory
2. Test locally with `mkdocs serve`
3. Submit pull request with clear description

### AI Services Contributions
1. Follow the [Contributing Guidelines](ecomate-ai/CONTRIBUTING.md)
2. Set up development environment
3. Run comprehensive test suite
4. Submit pull request with tests and documentation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation Issues**: Create GitHub issue with `docs` label
- **AI Services Issues**: Create GitHub issue with `ai-services` label
- **Feature Requests**: Use GitHub Discussions for new feature proposals
- **Security Issues**: Email security@ecomate.com for responsible disclosure

## 🔗 Links

- [Live Documentation Site](https://your-org.github.io/ecomate-docs/)
- [AI Services API](http://localhost:8080/docs) (when running locally)
- [Temporal Web UI](http://localhost:8088) (workflow monitoring)
- [MinIO Console](http://localhost:9001) (object storage management)

---

**EcoMate** - Intelligent Environmental Technology Management