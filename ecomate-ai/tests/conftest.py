"""Pytest configuration and shared fixtures for EcoMate AI tests."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator, List
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

# Test configuration
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def test_fixtures_dir() -> Path:
    """Path to test fixtures directory (alias for test_data_dir)."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def html_samples_dir(test_data_dir: Path) -> Path:
    """Path to HTML sample files."""
    return test_data_dir / "html_samples"


@pytest.fixture(scope="session")
def mock_responses_dir(test_data_dir: Path) -> Path:
    """Path to mock HTTP response files."""
    return test_data_dir / "mock_responses"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_env_vars() -> Generator[Dict[str, str], None, None]:
    """Mock environment variables for testing."""
    test_env = {
        "DATABASE_URL": "postgresql://test:test@localhost:5432/test_ecomate",
        "MINIO_ENDPOINT": "localhost:9000",
        "MINIO_ACCESS_KEY": "test_access_key",
        "MINIO_SECRET_KEY": "test_secret_key",
        "TEMPORAL_HOST": "localhost:7233",
        "TEMPORAL_NAMESPACE": "test",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "PARSER_STRICT": "false",
        "DEFAULT_CURRENCY": "USD",
        "GITHUB_TOKEN": "test_token",
        "GITHUB_REPO": "test/repo",
    }
    
    with patch.dict(os.environ, test_env, clear=False):
        yield test_env


@pytest.fixture
def mock_temporal_client() -> AsyncMock:
    """Mock Temporal client for workflow testing."""
    client = AsyncMock()
    
    # Mock workflow execution
    mock_handle = AsyncMock()
    mock_handle.result.return_value = {
        "status": "completed",
        "results": {"test": "data"}
    }
    client.start_workflow.return_value = mock_handle
    
    # Mock workflow query
    client.get_workflow_handle.return_value = mock_handle
    
    return client


@pytest.fixture
def mock_database() -> Generator[Mock, None, None]:
    """Mock database connection and operations."""
    with patch("psycopg.connect") as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        # Mock common database operations
        mock_cursor.fetchall.return_value = []
        mock_cursor.fetchone.return_value = None
        mock_cursor.execute.return_value = None
        
        yield mock_conn


@pytest.fixture
def mock_minio_client() -> Mock:
    """Mock MinIO client for object storage testing."""
    client = Mock()
    
    # Mock bucket operations
    client.bucket_exists.return_value = True
    client.make_bucket.return_value = None
    
    # Mock object operations
    client.put_object.return_value = None
    client.get_object.return_value = Mock()
    client.list_objects.return_value = []
    
    return client


@pytest.fixture
def mock_http_session() -> Generator[Mock, None, None]:
    """Mock HTTP session for web requests."""
    with patch("requests.Session") as mock_session_class:
        mock_session = Mock()
        mock_response = Mock()
        
        # Default successful response
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.content = b"Test content"
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.url = "https://example.com"
        
        mock_session.get.return_value = mock_response
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        yield mock_session


@pytest.fixture
def sample_pump_data() -> List[Dict[str, Any]]:
    """Sample pump data for testing."""
    return [
        {
            "name": "Grundfos CR 3-8",
            "flow_rate_lpm": 120.0,
            "head_meters": 45.0,
            "power_kw": 2.2,
            "efficiency_percent": 85.0,
            "price_usd": 1250.00,
            "supplier": "Grundfos",
            "model_number": "CR3-8",
            "specifications": {
                "inlet_size": "2 inch",
                "outlet_size": "1.5 inch",
                "material": "Stainless Steel",
                "max_temperature": 70
            }
        },
        {
            "name": "Xylem Lowara e-SV 33",
            "flow_rate_lpm": 200.0,
            "head_meters": 35.0,
            "power_kw": 3.0,
            "efficiency_percent": 82.0,
            "price_usd": 1450.00,
            "supplier": "Xylem",
            "model_number": "e-SV33",
            "specifications": {
                "inlet_size": "3 inch",
                "outlet_size": "2 inch",
                "material": "Cast Iron",
                "max_temperature": 80
            }
        }
    ]


@pytest.fixture
def sample_uv_data() -> List[Dict[str, Any]]:
    """Sample UV reactor data for testing."""
    return [
        {
            "name": "Trojan UV3000Plus",
            "flow_rate_lpm": 500.0,
            "uv_dose_mj_cm2": 40.0,
            "power_kw": 1.8,
            "lamp_count": 12,
            "price_usd": 8500.00,
            "supplier": "Trojan Technologies",
            "model_number": "UV3000Plus",
            "specifications": {
                "inlet_size": "6 inch",
                "outlet_size": "6 inch",
                "lamp_type": "Low Pressure",
                "reactor_material": "Stainless Steel 316L"
            }
        },
        {
            "name": "Wedeco Spektron 15",
            "flow_rate_lpm": 300.0,
            "uv_dose_mj_cm2": 35.0,
            "power_kw": 1.2,
            "lamp_count": 8,
            "price_usd": 6200.00,
            "supplier": "Xylem",
            "model_number": "Spektron15",
            "specifications": {
                "inlet_size": "4 inch",
                "outlet_size": "4 inch",
                "lamp_type": "Medium Pressure",
                "reactor_material": "Stainless Steel 304"
            }
        }
    ]


@pytest.fixture
def sample_html_table() -> str:
    """Sample HTML table for parser testing."""
    return """
    <table class="product-table">
        <thead>
            <tr>
                <th>Model</th>
                <th>Flow Rate (L/min)</th>
                <th>Head (m)</th>
                <th>Power (kW)</th>
                <th>Price ($)</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>CR 3-8</td>
                <td>120</td>
                <td>45</td>
                <td>2.2</td>
                <td>$1,250.00</td>
            </tr>
            <tr>
                <td>CR 5-12</td>
                <td>200</td>
                <td>60</td>
                <td>3.5</td>
                <td>$1,850.00</td>
            </tr>
        </tbody>
    </table>
    """


@pytest.fixture
def sample_api_client() -> TestClient:
    """FastAPI test client for API testing."""
    # Import here to avoid circular imports
    from services.api.main import app
    return TestClient(app)


@pytest.fixture
def mock_workflow_activities() -> Dict[str, Mock]:
    """Mock Temporal workflow activities."""
    return {
        "research_activity": Mock(return_value={"results": []}),
        "price_monitor_activity": Mock(return_value={"status": "completed"}),
        "parse_supplier_data": Mock(return_value={"parsed_data": []}),
        "store_results": Mock(return_value={"stored": True}),
        "create_github_pr": Mock(return_value={"pr_url": "https://github.com/test/pr/1"})
    }


class MockResponse:
    """Mock HTTP response for testing."""
    
    def __init__(self, status_code: int = 200, text: str = "", 
                 json_data: Dict[str, Any] = None, headers: Dict[str, str] = None):
        self.status_code = status_code
        self.text = text
        self._json_data = json_data or {}
        self.headers = headers or {}
        self.content = text.encode('utf-8')
        self.url = "https://example.com"
    
    def json(self) -> Dict[str, Any]:
        return self._json_data
    
    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


@pytest.fixture
def mock_successful_response() -> MockResponse:
    """Mock successful HTTP response."""
    return MockResponse(
        status_code=200,
        text="<html><body>Success</body></html>",
        headers={"Content-Type": "text/html"}
    )


@pytest.fixture
def mock_error_response() -> MockResponse:
    """Mock error HTTP response."""
    return MockResponse(
        status_code=404,
        text="Not Found",
        headers={"Content-Type": "text/plain"}
    )


# Pytest hooks for custom behavior
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "network: mark test as requiring network access"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add slow marker to tests that might be slow
        if "e2e" in item.nodeid or "integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Add network marker to tests that use HTTP
        if "http" in item.name.lower() or "fetch" in item.name.lower():
            item.add_marker(pytest.mark.network)
        
        # Add database marker to tests that use database
        if "db" in item.name.lower() or "database" in item.name.lower():
            item.add_marker(pytest.mark.database)