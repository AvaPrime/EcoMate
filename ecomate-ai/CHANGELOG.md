# Changelog

All notable changes to the EcoMate AI project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive project documentation with installation, usage, and API guides
- Vendor-specific parsers for pump and UV reactor specifications
- Parser dispatcher with domain-based and category-based selection
- LLM fallback processing for complex data extraction
- Unit conversion system for flow rates, pressures, and measurements
- Pydantic models for type-safe data validation
- Environment configuration for parser behavior settings
- Demo test suite for parser functionality validation

### Changed
- Enhanced research workflow with parser-first, LLM-fallback strategy
- Updated `.env.example` with parser configuration options
- Improved data extraction accuracy with structured parsing

### Technical Details
- **Parser System**: Added specialized parsers for pumps (`pumps.py`) and UV reactors (`uv.py`)
- **Dispatcher Logic**: Implemented intelligent parser selection in `dispatcher.py`
- **Data Models**: Created Pydantic models for `SupplierRow`, `PartRow`, `Pump`, and `UVReactor`
- **Normalization**: Added helper functions for unit conversion and data standardization
- **Integration**: Modified `activities_research.py` to use parser-first approach
- **Configuration**: Added `PARSER_STRICT` and `DEFAULT_CURRENCY` environment variables

## [1.0.0] - 2024-01-15

### Added
- Initial release of EcoMate AI platform
- FastAPI-based REST API for workflow triggering
- Temporal workflow orchestration for reliable processing
- PostgreSQL database with pgvector for semantic search
- MinIO object storage for artifact management
- Research workflows for supplier and product data extraction
- Price monitoring with deviation alerts
- GitHub integration for automated documentation updates
- Multi-model AI support (Ollama, Google Vertex AI)
- Docker Compose infrastructure setup

### Core Features
- **Research Endpoints**: `/run/research` and `/run/new-research`
- **Price Monitoring**: `/run/price-monitor` and `/run/scheduled-price-monitor`
- **Web Crawling**: Automated supplier website crawling
- **Data Extraction**: LLM-powered specification extraction
- **Document Generation**: CSV reports and GitHub PR creation
- **Monitoring**: Temporal Web UI and MinIO Console interfaces

### Infrastructure
- **Services**: PostgreSQL, MinIO, Temporal, NATS
- **Dependencies**: FastAPI, Pydantic, Temporal, psycopg, boto3
- **AI Models**: Configurable Ollama and Vertex AI integration
- **Storage**: S3-compatible object storage with MinIO
- **Database**: PostgreSQL 16 with pgvector extension

---

## Release Notes Format

Each release includes:
- **Added**: New features and capabilities
- **Changed**: Modifications to existing functionality
- **Deprecated**: Features marked for removal
- **Removed**: Features removed in this release
- **Fixed**: Bug fixes and corrections
- **Security**: Security-related changes

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: Backward-compatible functionality additions
- **PATCH**: Backward-compatible bug fixes

## Contributing

When contributing changes, please:
1. Update this changelog with your modifications
2. Follow the established format and categories
3. Include technical details for significant changes
4. Reference related issues or pull requests
5. Maintain chronological order (newest first)