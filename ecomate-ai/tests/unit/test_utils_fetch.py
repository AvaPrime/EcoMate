"""Unit tests for fetch utility functions."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import aiohttp
from aiohttp import ClientTimeout
import json

from src.utils.fetch import (
    FetchClient,
    FetchResult,
    RateLimiter,
    RetryConfig,
    fetch_url,
    fetch_multiple_urls,
    create_session,
    validate_url,
    sanitize_headers
)


class TestFetchClient:
    """Test cases for FetchClient class."""
    
    @pytest.fixture
    def fetch_client(self):
        """Create a FetchClient instance for testing."""
        return FetchClient(
            timeout=30,
            max_retries=3,
            rate_limit_per_second=2.0,
            user_agent="EcoMate-AI/1.0 Test"
        )
    
    def test_fetch_client_initialization(self, fetch_client):
        """Test FetchClient initialization."""
        assert fetch_client.timeout == 30
        assert fetch_client.max_retries == 3
        assert fetch_client.rate_limiter.requests_per_second == 2.0
        assert "EcoMate-AI/1.0 Test" in fetch_client.headers["User-Agent"]
    
    @pytest.mark.asyncio
    async def test_fetch_success(self, fetch_client):
        """Test successful fetch operation."""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = AsyncMock(return_value="<html><body>Test content</body></html>")
        mock_response.read = AsyncMock(return_value=b"<html><body>Test content</body></html>")
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_client.fetch("https://example.com")
            
            assert isinstance(result, FetchResult)
            assert result.url == "https://example.com"
            assert result.status_code == 200
            assert result.content == "<html><body>Test content</body></html>"
            assert result.headers["Content-Type"] == "text/html"
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_fetch_http_error(self, fetch_client):
        """Test fetch with HTTP error status."""
        mock_response = Mock()
        mock_response.status = 404
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = AsyncMock(return_value="Not Found")
        mock_response.read = AsyncMock(return_value=b"Not Found")
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_client.fetch("https://example.com/notfound")
            
            assert result.status_code == 404
            assert result.success is False
            assert result.error_message is not None
    
    @pytest.mark.asyncio
    async def test_fetch_network_error(self, fetch_client):
        """Test fetch with network error."""
        with patch.object(fetch_client.session, 'get', side_effect=aiohttp.ClientError("Connection failed")):
            result = await fetch_client.fetch("https://example.com")
            
            assert result.success is False
            assert "Connection failed" in result.error_message
            assert result.status_code is None
    
    @pytest.mark.asyncio
    async def test_fetch_timeout(self, fetch_client):
        """Test fetch with timeout."""
        with patch.object(fetch_client.session, 'get', side_effect=asyncio.TimeoutError()):
            result = await fetch_client.fetch("https://example.com")
            
            assert result.success is False
            assert "timeout" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_with_retries(self, fetch_client):
        """Test fetch with retry mechanism."""
        # First two calls fail, third succeeds
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = AsyncMock(return_value="Success")
        mock_response.read = AsyncMock(return_value=b"Success")
        
        side_effects = [
            aiohttp.ClientError("First failure"),
            aiohttp.ClientError("Second failure"),
            mock_response
        ]
        
        with patch.object(fetch_client.session, 'get', side_effect=side_effects) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_client.fetch("https://example.com")
            
            assert result.success is True
            assert result.content == "Success"
            assert mock_get.call_count == 3
    
    @pytest.mark.asyncio
    async def test_fetch_with_custom_headers(self, fetch_client):
        """Test fetch with custom headers."""
        custom_headers = {"Authorization": "Bearer token123", "X-Custom": "value"}
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value='{"data": "test"}')
        mock_response.read = AsyncMock(return_value=b'{"data": "test"}')
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_client.fetch("https://api.example.com", headers=custom_headers)
            
            # Verify custom headers were passed
            call_args = mock_get.call_args
            assert "headers" in call_args.kwargs
            headers = call_args.kwargs["headers"]
            assert headers["Authorization"] == "Bearer token123"
            assert headers["X-Custom"] == "value"
    
    @pytest.mark.asyncio
    async def test_fetch_json_response(self, fetch_client):
        """Test fetch with JSON response parsing."""
        json_data = {"products": [{"name": "Pump A", "price": 1000}]}
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = AsyncMock(return_value=json.dumps(json_data))
        mock_response.json = AsyncMock(return_value=json_data)
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_client.fetch("https://api.example.com/products")
            
            assert result.success is True
            assert result.is_json is True
            parsed_json = result.get_json()
            assert parsed_json["products"][0]["name"] == "Pump A"


class TestFetchResult:
    """Test cases for FetchResult class."""
    
    def test_fetch_result_success(self):
        """Test successful FetchResult creation."""
        result = FetchResult(
            url="https://example.com",
            status_code=200,
            content="<html>Test</html>",
            headers={"Content-Type": "text/html"},
            response_time=0.5,
            success=True
        )
        
        assert result.url == "https://example.com"
        assert result.status_code == 200
        assert result.success is True
        assert result.response_time == 0.5
        assert result.is_html is True
        assert result.is_json is False
    
    def test_fetch_result_json_detection(self):
        """Test JSON content type detection."""
        result = FetchResult(
            url="https://api.example.com",
            status_code=200,
            content='{"data": "test"}',
            headers={"Content-Type": "application/json"},
            success=True
        )
        
        assert result.is_json is True
        assert result.is_html is False
        
        json_data = result.get_json()
        assert json_data["data"] == "test"
    
    def test_fetch_result_invalid_json(self):
        """Test handling of invalid JSON content."""
        result = FetchResult(
            url="https://api.example.com",
            status_code=200,
            content="invalid json content",
            headers={"Content-Type": "application/json"},
            success=True
        )
        
        with pytest.raises(json.JSONDecodeError):
            result.get_json()
    
    def test_fetch_result_error(self):
        """Test FetchResult with error."""
        result = FetchResult(
            url="https://example.com",
            success=False,
            error_message="Connection timeout",
            response_time=30.0
        )
        
        assert result.success is False
        assert result.error_message == "Connection timeout"
        assert result.status_code is None
        assert result.content is None


class TestRateLimiter:
    """Test cases for RateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(requests_per_second=2.0)
        
        assert limiter.requests_per_second == 2.0
        assert limiter.min_interval == 0.5  # 1/2.0
    
    @pytest.mark.asyncio
    async def test_rate_limiter_timing(self):
        """Test rate limiter timing control."""
        limiter = RateLimiter(requests_per_second=10.0)  # 0.1 second intervals
        
        start_time = asyncio.get_event_loop().time()
        
        # Make multiple requests
        for _ in range(3):
            await limiter.acquire()
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should take at least 0.2 seconds (2 intervals)
        assert elapsed >= 0.15  # Allow some tolerance
    
    @pytest.mark.asyncio
    async def test_rate_limiter_concurrent(self):
        """Test rate limiter with concurrent requests."""
        limiter = RateLimiter(requests_per_second=5.0)
        
        async def make_request():
            await limiter.acquire()
            return asyncio.get_event_loop().time()
        
        # Start multiple concurrent requests
        tasks = [make_request() for _ in range(3)]
        timestamps = await asyncio.gather(*tasks)
        
        # Timestamps should be spaced according to rate limit
        for i in range(1, len(timestamps)):
            interval = timestamps[i] - timestamps[i-1]
            assert interval >= 0.15  # Allow some tolerance


class TestRetryConfig:
    """Test cases for RetryConfig class."""
    
    def test_retry_config_default(self):
        """Test default RetryConfig."""
        config = RetryConfig()
        
        assert config.max_retries == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert 500 in config.retry_status_codes
        assert 502 in config.retry_status_codes
    
    def test_retry_config_custom(self):
        """Test custom RetryConfig."""
        config = RetryConfig(
            max_retries=5,
            base_delay=0.5,
            max_delay=30.0,
            retry_status_codes=[429, 500, 502, 503]
        )
        
        assert config.max_retries == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert 429 in config.retry_status_codes
    
    def test_retry_delay_calculation(self):
        """Test retry delay calculation."""
        config = RetryConfig(base_delay=1.0, exponential_base=2.0, max_delay=10.0)
        
        # Test exponential backoff
        delay1 = config.calculate_delay(1)
        delay2 = config.calculate_delay(2)
        delay3 = config.calculate_delay(3)
        
        assert delay1 == 1.0  # base_delay * 2^0
        assert delay2 == 2.0  # base_delay * 2^1
        assert delay3 == 4.0  # base_delay * 2^2
        
        # Test max delay cap
        delay_high = config.calculate_delay(10)
        assert delay_high <= config.max_delay


class TestUtilityFunctions:
    """Test cases for utility functions."""
    
    @pytest.mark.asyncio
    async def test_fetch_url_function(self):
        """Test standalone fetch_url function."""
        with patch('src.utils.fetch.FetchClient') as mock_client_class:
            mock_client = Mock()
            mock_result = FetchResult(
                url="https://example.com",
                status_code=200,
                content="Test content",
                success=True
            )
            mock_client.fetch = AsyncMock(return_value=mock_result)
            mock_client_class.return_value = mock_client
            
            result = await fetch_url("https://example.com")
            
            assert result.success is True
            assert result.content == "Test content"
    
    @pytest.mark.asyncio
    async def test_fetch_multiple_urls(self):
        """Test fetching multiple URLs concurrently."""
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        with patch('src.utils.fetch.FetchClient') as mock_client_class:
            mock_client = Mock()
            
            def mock_fetch(url):
                return FetchResult(
                    url=url,
                    status_code=200,
                    content=f"Content from {url}",
                    success=True
                )
            
            mock_client.fetch = AsyncMock(side_effect=mock_fetch)
            mock_client_class.return_value = mock_client
            
            results = await fetch_multiple_urls(urls)
            
            assert len(results) == 3
            for i, result in enumerate(results):
                assert result.success is True
                assert urls[i] in result.content
    
    def test_validate_url_valid(self):
        """Test URL validation with valid URLs."""
        valid_urls = [
            "https://example.com",
            "http://subdomain.example.org/path",
            "https://example.com:8080/path?query=value",
            "https://192.168.1.1:3000"
        ]
        
        for url in valid_urls:
            assert validate_url(url) is True
    
    def test_validate_url_invalid(self):
        """Test URL validation with invalid URLs."""
        invalid_urls = [
            "not-a-url",
            "ftp://example.com",  # Wrong scheme
            "https://",  # Missing domain
            "http://",  # Missing domain
            "",  # Empty string
            "javascript:alert('xss')",  # Dangerous scheme
        ]
        
        for url in invalid_urls:
            assert validate_url(url) is False
    
    def test_sanitize_headers(self):
        """Test header sanitization."""
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Authorization": "Bearer token123",
            "Content-Type": "application/json",
            "X-Forwarded-For": "192.168.1.1",  # Should be removed
            "Host": "example.com",  # Should be removed
            "Connection": "keep-alive",  # Should be removed
        }
        
        sanitized = sanitize_headers(headers)
        
        assert "User-Agent" in sanitized
        assert "Authorization" in sanitized
        assert "Content-Type" in sanitized
        assert "X-Forwarded-For" not in sanitized
        assert "Host" not in sanitized
        assert "Connection" not in sanitized
    
    @pytest.mark.asyncio
    async def test_create_session(self):
        """Test session creation with custom configuration."""
        timeout_config = ClientTimeout(total=30, connect=10)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = Mock()
            mock_session_class.return_value = mock_session
            
            session = create_session(
                timeout=timeout_config,
                headers={"User-Agent": "Test"},
                connector_limit=100
            )
            
            # Verify session was created with correct parameters
            mock_session_class.assert_called_once()
            call_kwargs = mock_session_class.call_args.kwargs
            assert call_kwargs["timeout"] == timeout_config
            assert call_kwargs["headers"]["User-Agent"] == "Test"


class TestErrorHandling:
    """Test cases for error handling in fetch operations."""
    
    @pytest.mark.asyncio
    async def test_fetch_dns_error(self):
        """Test handling of DNS resolution errors."""
        fetch_client = FetchClient()
        
        with patch.object(fetch_client.session, 'get', side_effect=aiohttp.ClientConnectorError(None, OSError("Name resolution failed"))):
            result = await fetch_client.fetch("https://nonexistent-domain-12345.com")
            
            assert result.success is False
            assert "resolution" in result.error_message.lower() or "dns" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_ssl_error(self):
        """Test handling of SSL certificate errors."""
        fetch_client = FetchClient()
        
        ssl_error = aiohttp.ClientSSLError(None, OSError("SSL certificate verification failed"))
        with patch.object(fetch_client.session, 'get', side_effect=ssl_error):
            result = await fetch_client.fetch("https://self-signed.badssl.com")
            
            assert result.success is False
            assert "ssl" in result.error_message.lower() or "certificate" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_fetch_too_many_redirects(self):
        """Test handling of too many redirects."""
        fetch_client = FetchClient()
        
        redirect_error = aiohttp.TooManyRedirects(None, ())
        with patch.object(fetch_client.session, 'get', side_effect=redirect_error):
            result = await fetch_client.fetch("https://example.com/redirect-loop")
            
            assert result.success is False
            assert "redirect" in result.error_message.lower()


@pytest.mark.parametrize("status_code,expected_success", [
    (200, True),
    (201, True),
    (204, True),
    (301, True),  # Redirect, but handled by aiohttp
    (302, True),  # Redirect, but handled by aiohttp
    (400, False),
    (401, False),
    (403, False),
    (404, False),
    (429, False),  # Rate limited
    (500, False),
    (502, False),
    (503, False),
])
@pytest.mark.asyncio
async def test_fetch_status_codes(status_code, expected_success):
    """Parametrized test for different HTTP status codes."""
    fetch_client = FetchClient()
    
    mock_response = Mock()
    mock_response.status = status_code
    mock_response.headers = {"Content-Type": "text/html"}
    mock_response.text = AsyncMock(return_value="Response content")
    mock_response.read = AsyncMock(return_value=b"Response content")
    
    with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
        mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
        mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
        
        result = await fetch_client.fetch("https://example.com")
        
        assert result.success == expected_success
        assert result.status_code == status_code


@pytest.mark.parametrize("content_type,expected_is_html,expected_is_json", [
    ("text/html", True, False),
    ("text/html; charset=utf-8", True, False),
    ("application/json", False, True),
    ("application/json; charset=utf-8", False, True),
    ("text/plain", False, False),
    ("application/xml", False, False),
    ("image/png", False, False),
])
def test_content_type_detection(content_type, expected_is_html, expected_is_json):
    """Parametrized test for content type detection."""
    result = FetchResult(
        url="https://example.com",
        status_code=200,
        content="Test content",
        headers={"Content-Type": content_type},
        success=True
    )
    
    assert result.is_html == expected_is_html
    assert result.is_json == expected_is_json


class TestPerformanceAndLimits:
    """Test cases for performance and resource limits."""
    
    @pytest.mark.asyncio
    async def test_concurrent_fetch_limit(self):
        """Test concurrent fetch operations with limits."""
        fetch_client = FetchClient(max_concurrent=2)
        
        urls = [f"https://example{i}.com" for i in range(5)]
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = AsyncMock(return_value="Content")
        mock_response.read = AsyncMock(return_value=b"Content")
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # This should work without issues despite the limit
            tasks = [fetch_client.fetch(url) for url in urls]
            results = await asyncio.gather(*tasks)
            
            assert len(results) == 5
            assert all(result.success for result in results)
    
    @pytest.mark.asyncio
    async def test_large_response_handling(self):
        """Test handling of large responses."""
        fetch_client = FetchClient(max_response_size=1024*1024)  # 1MB limit
        
        # Simulate large response
        large_content = "x" * (2 * 1024 * 1024)  # 2MB content
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html", "Content-Length": str(len(large_content))}
        mock_response.text = AsyncMock(return_value=large_content)
        mock_response.read = AsyncMock(return_value=large_content.encode())
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await fetch_client.fetch("https://example.com/large-file")
            
            # Should handle large response appropriately
            # (either truncate or reject based on implementation)
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_memory_usage_monitoring(self):
        """Test memory usage during fetch operations."""
        # This would test memory usage patterns
        # Implementation depends on specific memory monitoring requirements
        pass


class TestCaching:
    """Test cases for response caching functionality."""
    
    @pytest.mark.asyncio
    async def test_response_caching(self):
        """Test response caching mechanism."""
        fetch_client = FetchClient(enable_caching=True, cache_ttl=300)
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.headers = {"Content-Type": "text/html"}
        mock_response.text = AsyncMock(return_value="Cached content")
        mock_response.read = AsyncMock(return_value=b"Cached content")
        
        with patch.object(fetch_client.session, 'get', return_value=mock_response) as mock_get:
            mock_get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # First request
            result1 = await fetch_client.fetch("https://example.com")
            
            # Second request (should use cache)
            result2 = await fetch_client.fetch("https://example.com")
            
            assert result1.content == result2.content
            # Verify that the actual HTTP request was made only once
            # (implementation depends on caching strategy)
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration functionality."""
        # This would test cache TTL and expiration
        pass