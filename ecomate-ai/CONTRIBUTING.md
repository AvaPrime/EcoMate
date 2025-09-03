# Contributing to EcoMate AI

> **Version**: 1.0  
> **Last Updated**: January 2024  
> **Maintainer**: EcoMate Development Team

Thank you for your interest in contributing to EcoMate AI! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be Respectful**: Treat all contributors with respect and professionalism
- **Be Inclusive**: Welcome contributors from all backgrounds and experience levels
- **Be Collaborative**: Work together constructively and share knowledge
- **Be Patient**: Help others learn and grow in their contributions
- **Be Professional**: Maintain high standards in all interactions

## Getting Started

### Prerequisites

Before contributing to EcoMate, ensure you have:

## License

This project is proprietary software owned by AvaPrime Technologies. By contributing to this project, you agree that your contributions will be licensed under the same proprietary license. For licensing inquiries, please contact: licensing@avaprime.co.za

- **Python 3.11+**: Required for all services (3.11.0 or higher recommended)
- **Docker & Docker Compose**: For containerized development (Docker 20.10+, Compose 2.0+)
- **Git**: Version control and collaboration (2.30+)
- **Node.js 18+**: For documentation site and tooling
- **PostgreSQL Client**: For database operations (psql)
- **Basic knowledge of**:
  - FastAPI and async Python development
  - PostgreSQL, pgvector, and database design
  - RESTful API design and OpenAPI specifications
  - Testing frameworks (pytest, unittest)
  - Temporal workflow orchestration
  - Docker containerization and networking
  - Web scraping and data parsing techniques

### First Contribution

1. **Fork the repository**
   ```bash
   # Fork on GitHub, then clone your fork
   git clone https://github.com/YOUR_USERNAME/ecomate-ai.git
   cd ecomate-ai
   ```

2. **Set up development environment**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Upgrade pip and install dependencies
   python -m pip install --upgrade pip
   pip install -r requirements-dev.txt
   ```

3. **Configure pre-commit hooks**
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

4. **Set up environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Initialize development services**
   ```bash
   # Start infrastructure services
   docker-compose up -d postgres minio temporal
   
   # Wait for services to be ready
   make wait-for-services
   
   # Run database migrations
   make migrate
   ```

6. **Verify setup**
   ```bash
   # Run health checks
   make health-check
   
   # Run basic tests
   make test-quick
   ```

7. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

8. **Make your changes and commit**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

9. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub using the provided template
   ```

## Development Setup

### Environment Configuration

1. **Copy environment template**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables**
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://ecomate:ecomate123@localhost:5432/ecomate
   DATABASE_TEST_URL=postgresql://ecomate:ecomate123@localhost:5432/ecomate_test
   
   # MinIO Storage Configuration
   MINIO_ENDPOINT=localhost:9000
   MINIO_ACCESS_KEY=minioadmin
   MINIO_SECRET_KEY=minioadmin
   MINIO_BUCKET_NAME=ecomate-data
   MINIO_SECURE=false
   
   # Temporal Configuration
   TEMPORAL_HOST=localhost:7233
   TEMPORAL_NAMESPACE=default
   TEMPORAL_TASK_QUEUE=ecomate-tasks
   
   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   API_RELOAD=true
   LOG_LEVEL=DEBUG
   
   # Security
   SECRET_KEY=your-secret-key-here
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # External Services
   USER_AGENT="EcoMate/1.0 (+https://ecomate.ai)"
   REQUEST_TIMEOUT=30
   MAX_RETRIES=3
   ```

3. **Start development services**
   ```bash
   # Start all infrastructure services
   docker-compose up -d
   
   # Or start individual services
   docker-compose up -d postgres    # Database
   docker-compose up -d minio       # Object storage
   docker-compose up -d temporal    # Workflow engine
   docker-compose up -d nats        # Message broker
   ```

4. **Development workflow commands**
   ```bash
   # Start API server with hot reload
   make dev-api
   
   # Start Temporal worker
   make dev-worker
   
   # Start all services in development mode
   make dev-all
   
   # Stop all services
   make stop
   
   # Clean up containers and volumes
   make clean
   ```

### Development Dependencies

Install all development tools:

```bash
pip install -r requirements-dev.txt
```

Key development packages:
- **Testing**: `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist`, `httpx`, `factory-boy`
- **Code Quality**: `black`, `ruff`, `mypy`, `pre-commit`, `bandit`, `safety`
- **Documentation**: `mkdocs`, `mkdocs-material`, `mkdocs-swagger-ui-tag`
- **Development**: `watchdog`, `python-dotenv`, `rich`, `typer`
- **Debugging**: `pytest-sugar`, `pytest-clarity`, `ipdb`, `memory-profiler`
- **Database**: `alembic`, `asyncpg`, `psycopg2-binary`
- **Temporal**: `temporalio`, `dataclasses-json`

### Pre-commit Hooks

```bash
# Install pre-commit hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Development Workflow

```bash
# Start development services
docker compose -f docker-compose.dev.yml up -d

# Run tests
pytest tests/ -v

# Run with coverage
pytest --cov=services tests/

# Format code
black services/ tests/

# Lint code
ruff check services/ tests/

# Type checking
mypy services/
```

## Code Standards

### Python Style Guide

We follow PEP 8 with these specific guidelines:

**Formatting and Style:**
- Line length: 88 characters (Black default)
- Use double quotes for strings
- Use trailing commas in multi-line structures
- Import organization: standard library, third-party, local imports

**Type Hints and Documentation:**
```python
# Good: Clear function with comprehensive type hints and docstring
from typing import Optional, Dict, List
from decimal import Decimal
from datetime import datetime

def calculate_price_deviation(
    current_price: Decimal, 
    historical_avg: Decimal,
    threshold: Optional[Decimal] = None
) -> Dict[str, float]:
    """Calculate percentage deviation from historical average.
    
    Args:
        current_price: Current market price in USD
        historical_avg: Historical average price over specified period
        threshold: Optional threshold for significant deviation detection
        
    Returns:
        Dictionary containing:
            - deviation_percent: Percentage deviation as float
            - is_significant: Boolean indicating if deviation exceeds threshold
            - direction: 'increase' or 'decrease'
            
    Raises:
        ValueError: If historical_avg is zero or negative
        TypeError: If inputs are not Decimal types
    """
    if not isinstance(current_price, Decimal) or not isinstance(historical_avg, Decimal):
        raise TypeError("Price values must be Decimal types")
        
    if historical_avg <= 0:
        raise ValueError("Historical average must be positive")
        
    deviation = ((current_price - historical_avg) / historical_avg) * 100
    direction = "increase" if deviation > 0 else "decrease"
    is_significant = threshold is not None and abs(deviation) > threshold
    
    return {
        "deviation_percent": float(deviation),
        "is_significant": is_significant,
        "direction": direction
    }
```

**Code Quality Standards:**
- Use descriptive variable and function names
- Prefer composition over inheritance
- Keep functions small and focused (max 20-30 lines)
- Use dataclasses for data structures
- Implement proper error handling and logging

### File Organization

#### Directory Structure
```
services/
├── api/                     # FastAPI application layer
│   ├── __init__.py
│   ├── main.py             # Application entry point and configuration
│   ├── dependencies.py     # Dependency injection and middleware
│   ├── middleware.py       # Custom middleware components
│   ├── routers/            # API route handlers
│   │   ├── __init__.py
│   │   ├── health.py       # Health check endpoints
│   │   ├── suppliers.py    # Supplier management endpoints
│   │   ├── parts.py        # Parts catalog endpoints
│   │   ├── prices.py       # Price monitoring endpoints
│   │   └── research.py     # Research and analysis endpoints
│   ├── models/             # Pydantic models for API
│   │   ├── __init__.py
│   │   ├── requests.py     # Request models
│   │   ├── responses.py    # Response models
│   │   └── schemas.py      # Shared schema definitions
│   └── exceptions.py       # API-specific exception handlers
├── parsers/                # Web scraping and data parsing
│   ├── __init__.py
│   ├── base.py            # Abstract base parser classes
│   ├── dispatcher.py      # Parser selection and routing logic
│   ├── models.py          # Data models for parsed content
│   ├── vendors/           # Vendor-specific parser implementations
│   │   ├── __init__.py
│   │   ├── grainger.py    # Grainger-specific parsing logic
│   │   ├── mcmaster.py    # McMaster-Carr parsing logic
│   │   ├── amazon.py      # Amazon Business parsing logic
│   │   └── generic.py     # Generic fallback parser
│   └── utils/             # Parsing utilities
│       ├── __init__.py
│       ├── selectors.py   # CSS/XPath selector utilities
│       ├── cleaners.py    # Data cleaning and normalization
│       └── validators.py  # Data validation utilities
├── orchestrator/           # Temporal workflow orchestration
│   ├── __init__.py
│   ├── workflows.py       # Workflow definitions and logic
│   ├── activities.py      # Activity implementations
│   ├── models.py          # Workflow data models
│   └── schedules.py       # Scheduled workflow configurations
├── database/              # Database layer and models
│   ├── __init__.py
│   ├── connection.py      # Database connection management
│   ├── models.py          # SQLAlchemy ORM models
│   ├── repositories.py    # Data access layer
│   └── migrations/        # Alembic migration files
└── utils/                 # Shared utilities and helpers
    ├── __init__.py
    ├── config.py          # Configuration management
    ├── logging.py         # Logging configuration
    ├── storage.py         # MinIO and file operations
    ├── cache.py           # Caching utilities
    ├── metrics.py         # Performance monitoring
    └── security.py        # Security and authentication utilities
```

#### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Error Handling

**Custom Exception Hierarchy:**
```python
# Base exceptions
class EcoMateException(Exception):
    """Base exception for EcoMate application."""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.timestamp = datetime.utcnow()

class ValidationError(EcoMateException):
    """Exception raised for data validation errors."""
    pass

class ParserException(EcoMateException):
    """Exception raised during parsing operations."""
    
    def __init__(self, message: str, url: Optional[str] = None, vendor: Optional[str] = None):
        super().__init__(message)
        self.url = url
        self.vendor = vendor

class DatabaseException(EcoMateException):
    """Exception raised for database operations."""
    pass

class ExternalServiceException(EcoMateException):
    """Exception raised for external service failures."""
    
    def __init__(self, message: str, service_name: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.service_name = service_name
        self.status_code = status_code
```

**Error Handling Patterns:**
```python
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Proper error handling with structured logging
async def parse_supplier_data(
    html_content: str, 
    url: str, 
    vendor: str
) -> Optional[Dict[str, Any]]:
    """Parse supplier data from HTML content with comprehensive error handling."""
    
    # Input validation
    if not html_content or not html_content.strip():
        raise ValidationError("HTML content cannot be empty")
        
    if not url or not vendor:
        raise ValidationError("URL and vendor must be provided")
    
    try:
        logger.info(f"Starting parsing for vendor: {vendor}", extra={
            "vendor": vendor,
            "url": url,
            "content_length": len(html_content)
        })
        
        # Parsing logic here
        parsed_data = await _perform_parsing(html_content, vendor)
        
        if not parsed_data:
            logger.warning(f"No data extracted from {vendor} page", extra={
                "vendor": vendor,
                "url": url
            })
            return None
            
        logger.info(f"Successfully parsed data from {vendor}", extra={
            "vendor": vendor,
            "url": url,
            "items_found": len(parsed_data.get("items", []))
        })
        
        return parsed_data
        
    except ParserException:
        # Re-raise parser exceptions as-is
        raise
    except ValidationError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during parsing: {e}", extra={
            "vendor": vendor,
            "url": url,
            "error_type": type(e).__name__
        }, exc_info=True)
        raise ParserException(
            f"Parsing failed for {vendor}: {e}", 
            url=url, 
            vendor=vendor
        ) from e

# Context manager for resource cleanup
@asynccontextmanager
async def database_transaction():
    """Context manager for database transactions with automatic rollback."""
    transaction = None
    try:
        transaction = await database.transaction()
        yield transaction
        await transaction.commit()
    except Exception as e:
        if transaction:
            await transaction.rollback()
        logger.error(f"Database transaction failed: {e}", exc_info=True)
        raise DatabaseException(f"Transaction failed: {e}") from e
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
│   ├── __init__.py
│   ├── api/                # API layer unit tests
│   │   ├── __init__.py
│   │   ├── test_routers.py
│   │   ├── test_models.py
│   │   └── test_dependencies.py
│   ├── parsers/            # Parser unit tests
│   │   ├── __init__.py
│   │   ├── test_base_parser.py
│   │   ├── test_dispatcher.py
│   │   └── vendors/
│   │       ├── test_grainger.py
│   │       ├── test_mcmaster.py
│   │       └── test_generic.py
│   ├── orchestrator/       # Workflow unit tests
│   │   ├── __init__.py
│   │   ├── test_workflows.py
│   │   └── test_activities.py
│   ├── database/           # Database layer unit tests
│   │   ├── __init__.py
│   │   ├── test_models.py
│   │   └── test_repositories.py
│   └── utils/              # Utility unit tests
│       ├── __init__.py
│       ├── test_config.py
│       ├── test_storage.py
│       └── test_security.py
├── integration/             # Integration tests
│   ├── __init__.py
│   ├── test_api_integration.py      # API endpoint integration
│   ├── test_database_integration.py # Database operations
│   ├── test_parser_integration.py   # Parser with real websites
│   ├── test_workflow_integration.py # Temporal workflow execution
│   └── test_storage_integration.py  # MinIO storage operations
├── e2e/                    # End-to-end tests
│   ├── __init__.py
│   ├── test_price_monitoring.py    # Complete price monitoring flow
│   ├── test_supplier_research.py   # Supplier research scenarios
│   └── test_data_pipeline.py       # Full data processing pipeline
├── performance/            # Performance and load tests
│   ├── __init__.py
│   ├── test_api_performance.py
│   ├── test_parser_performance.py
│   └── test_database_performance.py
├── fixtures/               # Test data and fixtures
│   ├── __init__.py
│   ├── html_samples/       # Sample HTML files for parser testing
│   │   ├── grainger_product.html
│   │   ├── mcmaster_catalog.html
│   │   └── amazon_listing.html
│   ├── mock_responses/     # Mock API responses
│   │   ├── temporal_responses.json
│   │   └── database_fixtures.json
│   ├── test_data.py        # Test data generators
│   └── factories.py        # Factory Boy factories
└── conftest.py             # Pytest configuration and shared fixtures
```

### Writing Tests

#### Unit Test Example
```python
import pytest
from unittest.mock import Mock, patch
from services.parsers.pumps import parse_pump_table
from services.parsers.models import Pump

class TestPumpParser:
    """Test cases for pump parser functionality."""
    
    def test_parse_grundfos_table(self):
        """Test parsing Grundfos pump specifications."""
        # Arrange
        with open('tests/fixtures/html_samples/grundfos_pumps.html') as f:
            html_content = f.read()
        
        # Act
        pumps = parse_pump_table(html_content, 'https://grundfos.com')
        
        # Assert
        assert len(pumps) > 0
        assert all(isinstance(pump, Pump) for pump in pumps)
        assert all(pump.flow_rate_lpm > 0 for pump in pumps)
        assert all(pump.head_meters > 0 for pump in pumps)
    
    def test_parse_empty_table(self):
        """Test handling of empty HTML tables."""
        html_content = "<table></table>"
        pumps = parse_pump_table(html_content, 'https://example.com')
        assert pumps == []
    
    @patch('services.parsers.pumps.requests.get')
    def test_network_error_handling(self, mock_get):
        """Test handling of network errors during parsing."""
        mock_get.side_effect = ConnectionError("Network unavailable")
        
        with pytest.raises(ParserError) as exc_info:
            parse_pump_table("<html></html>", 'https://unreachable.com')
        
        assert "Network unavailable" in str(exc_info.value)
```

#### Integration Test Example
```python
import pytest
from fastapi.testclient import TestClient
from services.api.main import app

class TestResearchAPI:
    """Integration tests for research API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client for API testing."""
        return TestClient(app)
    
    def test_research_endpoint_success(self, client):
        """Test successful research workflow execution."""
        # Arrange
        request_data = {
            "query": "test pumps",
            "limit": 2
        }
        
        # Act
        response = client.post("/run/research", json=request_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "workflow_id" in data
        assert "results" in data
    
    def test_research_endpoint_validation(self, client):
        """Test request validation for research endpoint."""
        # Test missing required field
        response = client.post("/run/research", json={"limit": 5})
        assert response.status_code == 422
        
        # Test invalid limit value
        response = client.post("/run/research", json={
            "query": "test",
            "limit": -1
        })
        assert response.status_code == 422
```

### Test Configuration

#### conftest.py
```python
import pytest
import asyncio
from unittest.mock import AsyncMock

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_temporal_client():
    """Mock Temporal client for testing."""
    client = AsyncMock()
    client.start_workflow.return_value.result.return_value = {
        "status": "completed",
        "results": {"test": "data"}
    }
    return client

@pytest.fixture
def sample_html():
    """Load sample HTML for parser testing."""
    with open('tests/fixtures/html_samples/sample.html') as f:
        return f.read()
```

### Running Tests

**Basic Test Execution:**
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test categories
pytest tests/unit/          # Unit tests only
pytest tests/integration/   # Integration tests only
pytest tests/e2e/          # End-to-end tests only

# Run specific test file
pytest tests/unit/parsers/test_grainger.py

# Run tests matching pattern
pytest -k "test_parser and not integration"

# Run tests with specific markers
pytest -m "slow"           # Run slow tests
pytest -m "not slow"       # Skip slow tests
```

**Coverage and Reporting:**
```bash
# Run with coverage
pytest --cov=services --cov-report=html --cov-report=term

# Coverage with branch analysis
pytest --cov=services --cov-branch --cov-report=html

# Generate coverage report only for changed files
pytest --cov=services --cov-report=html --cov-fail-under=80

# Export coverage to XML (for CI/CD)
pytest --cov=services --cov-report=xml
```

**Parallel and Performance Testing:**
```bash
# Run tests in parallel (requires pytest-xdist)
pytest -n auto              # Auto-detect CPU cores
pytest -n 4                 # Use 4 workers

# Run with profiling
pytest --profile            # Profile test execution
pytest --profile-svg        # Generate SVG profile

# Memory profiling (requires pytest-memray)
pytest --memray
```

**Environment-Specific Testing:**
```bash
# Run tests against different environments
pytest --env=development
pytest --env=staging
pytest --env=production

# Database-specific tests
pytest --db=postgresql      # Test with PostgreSQL
pytest --db=sqlite         # Test with SQLite (faster)

# Integration tests with external services
pytest tests/integration/ --external-services
```

### Code Quality Checks

**Formatting and Linting:**
```bash
# Format code with Black
black services/ tests/
black --check services/ tests/  # Check without modifying

# Lint with Ruff
ruff check services/ tests/
ruff check --fix services/ tests/  # Auto-fix issues

# Import sorting with isort
isort services/ tests/
isort --check-only services/ tests/
```

**Type Checking and Security:**
```bash
# Type checking with mypy
mypy services/
mypy --strict services/     # Strict mode

# Security scanning
bandit -r services/         # Security linting
safety check               # Check for known vulnerabilities

# Dependency analysis
pip-audit                  # Audit dependencies for vulnerabilities
```

**Comprehensive Quality Checks:**
```bash
# Run all quality checks (defined in Makefile)
make lint                  # All linting and formatting
make type-check           # Type checking
make security-check       # Security analysis
make test-all             # All tests with coverage
make quality-gate         # Complete quality gate
```

### Test Configuration

**conftest.py - Shared Fixtures:**
```python
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from temporalio.testing import WorkflowEnvironment
from minio import Minio

from services.api.main import app
from services.database.connection import get_database_session
from services.utils.config import get_settings

# Async test configuration
@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Database fixtures
@pytest.fixture(scope="session")
async def test_db_engine():
    """Create test database engine."""
    settings = get_settings()
    engine = create_async_engine(
        settings.database_test_url,
        echo=True if settings.log_level == "DEBUG" else False
    )
    yield engine
    await engine.dispose()

@pytest.fixture
async def db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create database session for testing."""
    async with AsyncSession(test_db_engine) as session:
        yield session
        await session.rollback()

# API client fixtures
@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test API client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
async def authenticated_client(api_client: AsyncClient) -> AsyncClient:
    """Create authenticated API client."""
    # Add authentication logic here
    api_client.headers.update({"Authorization": "Bearer test-token"})
    return api_client

# Temporal fixtures
@pytest.fixture
async def temporal_env() -> AsyncGenerator[WorkflowEnvironment, None]:
    """Create Temporal test environment."""
    async with WorkflowEnvironment.start_time_skipping() as env:
        yield env

# MinIO fixtures
@pytest.fixture
def minio_client() -> Minio:
    """Create MinIO test client."""
    return Minio(
        "localhost:9000",
        access_key="minioadmin",
        secret_key="minioadmin",
        secure=False
    )

# Mock fixtures
@pytest.fixture
def mock_html_content() -> str:
    """Load sample HTML content for parser testing."""
    with open("tests/fixtures/html_samples/grainger_product.html") as f:
        return f.read()

@pytest.fixture
def sample_product_data() -> dict:
    """Generate sample product data."""
    return {
        "name": "Test Pump",
        "model": "TP-100",
        "price": 1299.99,
        "specifications": {
            "flow_rate": "100 GPM",
            "pressure": "50 PSI",
            "power": "5 HP"
        }
    }

# Pytest markers
pytestmark = [
    pytest.mark.asyncio,  # Enable async support
]
```

## Pull Request Process

### Before Submitting

1. **Sync with Upstream**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/add-new-parser
   ```

3. **Make Changes**
   - Implement your feature or fix
   - Add comprehensive tests
   - Update documentation
   - Follow code standards

4. **Test Thoroughly**
   ```bash
   # Run full test suite
   pytest tests/ -v
   
   # Check code quality
   black --check services/ tests/
   ruff check services/ tests/
   mypy services/
   
   # Run pre-commit hooks
   pre-commit run --all-files
   ```

5. **Update Documentation**
   - Update README.md if needed
   - Add entry to CHANGELOG.md
   - Update docstrings and comments

### PR Requirements

#### Title Format
```
type(scope): brief description

Examples:
feat(parsers): add Xylem pump parser support
fix(api): handle timeout errors in research endpoint
docs(readme): update installation instructions
test(parsers): add comprehensive UV reactor tests
refactor(utils): optimize HTML table parsing
```

#### Description Template
```markdown
## Description
Brief description of the changes and their motivation.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Code refactoring

## Changes Made
- [ ] Added new parser for Xylem pumps
- [ ] Updated dispatcher logic for better domain matching
- [ ] Added comprehensive test coverage
- [ ] Updated documentation

## Testing
- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Manual testing completed
- [ ] Added new tests for changes

## Screenshots (if applicable)
Add screenshots or GIFs demonstrating the changes.

## Breaking Changes
Describe any breaking changes and migration steps.

## Dependencies
List any new dependencies or version updates.

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Code is commented, particularly complex areas
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] CHANGELOG.md updated
```

### Review Process

1. **Automated Checks**: CI/CD pipeline must pass
2. **Code Review**: At least one approving review from maintainer
3. **Testing**: Manual testing for significant changes
4. **Documentation Review**: Ensure docs are accurate and complete
5. **Final Approval**: Maintainer approval required for merge

### After Approval

```bash
# Squash and merge (preferred)
# OR rebase and merge for clean history

# Delete feature branch after merge
git branch -d feature/add-new-parser
git push origin --delete feature/add-new-parser
```

## Issue Reporting

### Bug Reports

Use the bug report template:

```markdown
**Bug Description**
Clear description of the bug.

**Steps to Reproduce**
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**
- OS: [e.g. Ubuntu 22.04]
- Python Version: [e.g. 3.11.5]
- Docker Version: [e.g. 24.0.6]
- Browser: [if applicable]

**Additional Context**
Add any other context, logs, or screenshots.
```

### Feature Requests

```markdown
**Feature Description**
Clear description of the proposed feature.

**Problem Statement**
What problem does this solve?

**Proposed Solution**
Describe your proposed implementation.

**Alternatives Considered**
Other approaches you've considered.

**Additional Context**
Any other relevant information.
```

## Documentation

### Documentation Standards

- **Clarity**: Write for users of all experience levels
- **Completeness**: Cover all features and use cases
- **Examples**: Include practical, working examples
- **Maintenance**: Keep documentation up-to-date with code changes
- **Structure**: Use consistent formatting and organization

### Documentation Types

1. **README.md**: Project overview and quick start
2. **API Documentation**: Endpoint specifications and examples
3. **Code Documentation**: Docstrings and inline comments
4. **User Guides**: Step-by-step instructions
5. **Developer Guides**: Technical implementation details

### Writing Guidelines

- Use clear, concise language
- Include code examples with expected output
- Provide context and explain "why" not just "how"
- Use consistent terminology throughout
- Include troubleshooting sections
- Add diagrams for complex concepts

---

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Code Review**: For feedback on implementation approaches
- **Documentation**: Check existing docs before asking questions

## Recognition

We appreciate all contributions! Contributors will be:
- Listed in the project's contributors section
- Mentioned in release notes for significant contributions
- Invited to join the maintainer team for sustained contributions

Thank you for contributing to EcoMate AI! 🌱