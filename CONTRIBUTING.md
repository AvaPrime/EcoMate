# Contributing to EcoMate

We welcome contributions to the EcoMate platform! This document provides guidelines for contributing to both the documentation site and AI services platform.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Documentation Contributions](#documentation-contributions)
- [AI Services Contributions](#ai-services-contributions)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [AI Development Tools](#ai-development-tools)

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please treat all community members with respect and create a welcoming environment for everyone.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/your-username/ecomate.git
   cd ecomate
   ```
3. **Set up the development environment** (see [Development Setup](#development-setup))
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Setup

### Documentation Site Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Serve documentation locally
mkdocs serve
```

### AI Services Setup

```bash
# Navigate to AI services
cd ecomate-ai

# Copy environment template
cp .env.example .env
# Edit .env with your configuration

# Start infrastructure
docker compose up -d postgres minio temporal nats

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest
```

## Contributing Guidelines

### General Principles

- **Quality First**: Ensure all contributions meet high standards for code quality, documentation, and testing
- **AI-Friendly**: Write clear, well-documented code that AI development tools can understand and work with
- **Backward Compatibility**: Avoid breaking changes unless absolutely necessary
- **Security**: Never commit secrets, API keys, or sensitive information

### Coding Standards

- **Python**: Follow PEP 8 style guidelines
- **Documentation**: Use clear, concise Markdown with proper formatting
- **Comments**: Write meaningful comments, especially for complex logic
- **Type Hints**: Use type hints in Python code for better AI tool compatibility

## Documentation Contributions

### File Organization

- **Product docs**: `docs/products/`
- **Operations**: `docs/operations/`
- **API docs**: `docs/api/`
- **Marketing**: `docs/marketing/`
- **Suppliers**: `docs/suppliers/`

### Writing Guidelines

1. **Use clear headings** with proper hierarchy (H1, H2, H3)
2. **Include code examples** where applicable
3. **Add cross-references** to related documentation
4. **Test all links** and ensure they work
5. **Use consistent terminology** throughout

### Documentation Testing

```bash
# Test locally
mkdocs serve

# Check for broken links
mkdocs build --strict

# Generate PDF (optional)
make pdf
```

## AI Services Contributions

### Code Structure

- **Services**: Individual microservices in `services/`
- **Shared code**: Common utilities in `services/shared/`
- **Tests**: Comprehensive test suite in `tests/`
- **Configuration**: Environment-based configuration

### Development Workflow

1. **Write tests first** (TDD approach recommended)
2. **Implement functionality** with proper error handling
3. **Add documentation** including docstrings and API docs
4. **Run full test suite** before submitting

### API Development

- Use **FastAPI** for all API endpoints
- Include **OpenAPI documentation** with examples
- Implement **proper error handling** with meaningful messages
- Add **request/response validation** using Pydantic

## Testing

### Documentation Testing

```bash
# Test documentation build
mkdocs build --strict

# Test locally
mkdocs serve
```

### AI Services Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run performance tests
pytest tests/performance/
```

### Test Requirements

- **Unit tests**: Test individual functions and classes
- **Integration tests**: Test service interactions
- **End-to-end tests**: Test complete workflows
- **Performance tests**: Ensure acceptable response times
- **Documentation tests**: Verify examples work correctly

## Submitting Changes

### Pull Request Process

1. **Update documentation** if your changes affect user-facing functionality
2. **Add tests** for new functionality
3. **Run the test suite** and ensure all tests pass
4. **Update CHANGELOG.md** with a description of your changes
5. **Submit a pull request** with a clear title and description

### Pull Request Requirements

- [ ] Clear description of changes
- [ ] Tests added for new functionality
- [ ] Documentation updated
- [ ] All tests passing
- [ ] No breaking changes (or clearly documented)
- [ ] AI development tools compatibility verified

### Review Process

1. **Automated checks** must pass (CI/CD pipeline)
2. **Code review** by maintainers
3. **Testing** in staging environment
4. **Approval** and merge

## AI Development Tools

### Compatibility Guidelines

To ensure compatibility with AI development tools (ChatGPT, GitHub Copilot, Google Gemini, etc.):

#### Code Structure
- Use **clear, descriptive names** for functions, classes, and variables
- Include **comprehensive docstrings** with examples
- Add **type hints** for all function parameters and return values
- Structure code in **logical, predictable patterns**

#### Documentation
- Write **step-by-step instructions** for complex procedures
- Include **working code examples** that can be copy-pasted
- Use **consistent formatting** and terminology
- Add **context and explanations** for business logic

#### API Design
- Include **OpenAPI/Swagger documentation** with examples
- Use **standard HTTP status codes** and error formats
- Provide **clear request/response schemas**
- Add **usage examples** for each endpoint

#### Testing
- Write **descriptive test names** that explain what is being tested
- Include **test data examples** that AI tools can understand
- Add **comments explaining complex test scenarios**
- Ensure **tests serve as documentation** for expected behavior

### AI Tool Integration Examples

#### For ChatGPT/GPT-4
```python
def calculate_treatment_capacity(
    flow_rate_m3_per_day: float,
    population_equivalent: int,
    safety_factor: float = 1.2
) -> dict:
    """
    Calculate wastewater treatment system capacity requirements.
    
    This function helps size treatment systems based on flow rate and
    population equivalent, commonly used in environmental engineering.
    
    Args:
        flow_rate_m3_per_day: Daily flow rate in cubic meters
        population_equivalent: Number of people equivalent
        safety_factor: Safety margin (default 1.2 = 20% extra capacity)
    
    Returns:
        dict: Contains 'required_capacity', 'recommended_capacity', 'units'
    
    Example:
        >>> calculate_treatment_capacity(100, 500)
        {'required_capacity': 100, 'recommended_capacity': 120, 'units': 'm3/day'}
    """
    required = max(flow_rate_m3_per_day, population_equivalent * 0.2)
    recommended = required * safety_factor
    
    return {
        'required_capacity': required,
        'recommended_capacity': recommended,
        'units': 'm3/day'
    }
```

#### For GitHub Copilot
- Use **predictable patterns** and **consistent naming**
- Add **inline comments** explaining business logic
- Structure code in **small, focused functions**

#### For Google Gemini
- Include **comprehensive examples** in documentation
- Use **standard industry terminology**
- Provide **context about environmental engineering concepts**

## Questions?

If you have questions about contributing:

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Use the bug report issue template
- **Feature requests**: Use the feature request issue template
- **Documentation issues**: Use the documentation issue template
- **Security issues**: Email security@ecomate.com

## Recognition

We appreciate all contributions! Contributors will be:

- **Listed in CONTRIBUTORS.md**
- **Mentioned in release notes** for significant contributions
- **Invited to join** the maintainer team for sustained contributions

Thank you for helping make EcoMate better! 🌱