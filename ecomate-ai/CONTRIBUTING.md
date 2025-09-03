# Contributing to EcoMate AI

Thank you for your interest in contributing to EcoMate AI! This document provides guidelines and information for contributors.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Code Standards](#code-standards)
5. [Testing Guidelines](#testing-guidelines)
6. [Pull Request Process](#pull-request-process)
7. [Issue Reporting](#issue-reporting)
8. [Documentation](#documentation)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct:

- **Be Respectful**: Treat all contributors with respect and professionalism
- **Be Inclusive**: Welcome contributors from all backgrounds and experience levels
- **Be Collaborative**: Work together constructively and share knowledge
- **Be Patient**: Help others learn and grow in their contributions
- **Be Professional**: Maintain high standards in all interactions

## Getting Started

### Prerequisites

Before contributing, ensure you have:
- Python 3.11+ installed
- Docker and Docker Compose
- Git for version control
- A GitHub account
- Basic understanding of FastAPI, Temporal, and PostgreSQL

### First Contribution

1. **Fork the Repository**: Create a fork of the EcoMate AI repository
2. **Clone Locally**: Clone your fork to your development machine
3. **Set Up Environment**: Follow the installation guide in README.md
4. **Find an Issue**: Look for "good first issue" labels or create a new issue
5. **Create Branch**: Create a feature branch for your changes
6. **Make Changes**: Implement your contribution
7. **Test Thoroughly**: Ensure all tests pass
8. **Submit PR**: Create a pull request with detailed description

## Development Setup

### Environment Configuration

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/ecomate-ai.git
cd ecomate-ai

# Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/ecomate-ai.git

# Create development environment
cp .env.example .env.dev
# Edit .env.dev with development-specific settings

# Set up Python environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Development Dependencies

Create `requirements-dev.txt` for development tools:
```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-asyncio>=0.21.0
black>=23.0.0
ruff>=0.1.0
mypy>=1.0.0
pre-commit>=3.0.0
```

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

#### Formatting
- **Black**: Use Black formatter with 88-character line length
- **Import Sorting**: Use isort for consistent import organization
- **Line Length**: Maximum 88 characters (Black default)
- **Quotes**: Prefer double quotes for strings

#### Code Quality
- **Linting**: Use Ruff for fast, comprehensive linting
- **Type Hints**: Required for all function signatures and class attributes
- **Docstrings**: Google-style docstrings for all public functions and classes
- **Variable Names**: Use descriptive, snake_case names

#### Example Function

```python
from typing import Optional
from pydantic import BaseModel

class ProductSpec(BaseModel):
    """Product specification data model.
    
    Attributes:
        name: Product name
        flow_rate_lpm: Flow rate in liters per minute
        pressure_bar: Operating pressure in bar
    """
    name: str
    flow_rate_lpm: float
    pressure_bar: Optional[float] = None

def extract_product_specs(
    html_content: str, 
    base_url: str,
    timeout_seconds: int = 30
) -> list[ProductSpec]:
    """Extract product specifications from HTML content.
    
    This function parses HTML tables and extracts structured product
    data using CSS selectors and regex patterns.
    
    Args:
        html_content: Raw HTML content from supplier page
        base_url: Base URL for resolving relative links
        timeout_seconds: Maximum time to spend on extraction
        
    Returns:
        List of ProductSpec objects with extracted data
        
    Raises:
        ParserError: When HTML structure is incompatible
        TimeoutError: When extraction exceeds timeout limit
        
    Example:
        >>> html = "<table><tr><td>Pump A</td><td>100 L/min</td></tr></table>"
        >>> specs = extract_product_specs(html, "https://example.com")
        >>> len(specs)
        1
    """
    # Implementation here
    pass
```

### File Organization

#### Directory Structure
```
services/
├── api/                 # FastAPI application
│   ├── __init__.py
│   ├── main.py         # API endpoints
│   └── models.py       # Request/response models
├── orchestrator/        # Temporal workflows
│   ├── activities.py   # Temporal activities
│   ├── workflows.py    # Workflow definitions
│   └── worker.py       # Worker process
├── parsers/            # Vendor-specific parsers
│   ├── __init__.py
│   ├── models.py       # Data models
│   ├── dispatcher.py   # Parser selection
│   ├── pumps.py        # Pump parser
│   └── uv.py          # UV reactor parser
└── utils/              # Shared utilities
    ├── fetch.py        # HTTP client
    ├── parsers.py      # HTML parsing
    └── minio_store.py  # Object storage
```

#### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Error Handling

#### Custom Exceptions
```python
class EcoMateError(Exception):
    """Base exception for EcoMate AI."""
    pass

class ParserError(EcoMateError):
    """Raised when parser fails to extract data."""
    
    def __init__(self, message: str, url: str, parser_type: str):
        self.url = url
        self.parser_type = parser_type
        super().__init__(f"{parser_type} parser failed for {url}: {message}")

class ValidationError(EcoMateError):
    """Raised when data validation fails."""
    pass
```

#### Error Handling Pattern
```python
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def safe_parse_float(value: str) -> Optional[float]:
    """Safely parse string to float with error handling."""
    try:
        return float(value.strip())
    except (ValueError, AttributeError) as e:
        logger.warning(f"Failed to parse float from '{value}': {e}")
        return None
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_parsers.py     # Parser unit tests
│   ├── test_models.py      # Model validation tests
│   └── test_utils.py       # Utility function tests
├── integration/             # Integration tests
│   ├── test_workflows.py   # Temporal workflow tests
│   ├── test_api.py         # API endpoint tests
│   └── test_database.py    # Database integration tests
├── fixtures/               # Test data
│   ├── html_samples/       # Sample HTML files
│   ├── test_data.json      # JSON test data
│   └── mock_responses/     # HTTP response mocks
└── conftest.py             # Pytest configuration
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

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=services --cov-report=html

# Run specific test file
pytest tests/unit/test_parsers.py

# Run tests matching pattern
pytest -k "test_pump"

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
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