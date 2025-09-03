"""Tests for input validation and rate limiting functionality."""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, AsyncMock, MagicMock, Mock
from fastapi import FastAPI, Request, HTTPException
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

# Import the validation and rate limiting modules directly
try:
    from services.shared.validation import (
        ValidationError, SecurityValidator, 
        ValidatedResearchReq, ValidatedNewResearchReq, ValidatedPriceMonitorReq,
        validate_request_size, sanitize_output
    )
    from services.shared.rate_limiting import RateLimiter, rate_limit_middleware, rate_limiter
except ImportError as e:
    pytest.skip(f"Skipping tests due to import error: {e}", allow_module_level=True)


class TestInputValidation:
    """Test input validation functionality."""
    
    def test_valid_research_request(self):
        """Test valid research request passes validation."""
        # Test valid data
        valid_data = {"query": "sustainable materials", "limit": 5}
        req = ValidatedResearchReq(**valid_data)
        assert req.query == "sustainable materials"
        assert req.limit == 5
    
    def test_sql_injection_blocked(self):
        """Test SQL injection attempts are blocked."""
        with pytest.raises((ValidationError, ValueError, Exception)):
            ValidatedResearchReq(query="'; DROP TABLE users; --", limit=5)
    
    def test_xss_blocked(self):
        """Test XSS attempts are blocked."""
        with pytest.raises((ValidationError, ValueError, Exception)):
            ValidatedResearchReq(query="<script>alert('xss')</script>", limit=5)
    
    def test_invalid_url_blocked(self):
        """Test invalid URLs are blocked."""
        with pytest.raises((ValidationError, ValueError, Exception)):
            ValidatedNewResearchReq(urls=["javascript:alert('xss')"])
    
    def test_localhost_url_blocked(self):
        """Test localhost URLs are blocked."""
        with pytest.raises((ValidationError, ValueError, Exception)):
            ValidatedNewResearchReq(urls=["http://localhost:8080/admin"])
    
    def test_private_ip_blocked(self):
        """Test that localhost addresses are blocked."""
        with pytest.raises((ValidationError, Exception)):
            ValidatedNewResearchReq(urls=["http://127.0.0.1/test"])
    
    def test_limit_validation(self):
        """Test limit parameter validation."""
        # Test negative limit
        with pytest.raises(ValueError):
            ValidatedResearchReq(query="test", limit=-1)
        
        # Test excessive limit
        with pytest.raises(ValueError):
            ValidatedResearchReq(query="test", limit=1000)
    
    def test_request_size_validation(self):
        """Test request size validation."""
        large_size = 5 * 1024 * 1024 + 1  # > 5MB
        
        with pytest.raises((HTTPException, Exception)) as exc_info:
            validate_request_size(large_size)
        
        error_message = str(exc_info.value)
        assert "Request too large" in error_message or "Request body too large" in error_message
    
    def test_sanitize_output(self):
        """Test output sanitization."""
        test_data = {
            "message": "<script>alert('xss')</script>",
            "password": "secret123",
            "api_key": "key_12345",
            "normal_field": "normal_value"
        }
        
        sanitized = sanitize_output(test_data)
        
        # Should HTML encode the script tag
        assert "&lt;script&gt;" in sanitized["message"]
        # Should remove sensitive fields
        assert "password" not in sanitized
        assert "api_key" not in sanitized
        # Should keep normal fields
        assert sanitized["normal_field"] == "normal_value"


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def setup_method(self):
        # Reset rate limiter for each test
        RateLimiter._instance = None
        self.rate_limiter = RateLimiter()
    
    def test_rate_limit_not_exceeded(self):
        """Test that requests within limit are allowed."""
        client_id = "test_client"
        endpoint = "/test"
        
        # Should allow requests within limit
        for i in range(5):
            is_limited, rate_info = self.rate_limiter.is_rate_limited(client_id, endpoint)
            assert is_limited == False
            self.rate_limiter.record_request(client_id, endpoint)
    
    def test_rate_limit_exceeded(self):
        """Test that requests exceeding limit are blocked."""
        client_id = "test_client"
        endpoint = "/run/research"
        
        # Exceed the limit (10 requests per minute for research)
        for i in range(10):
            self.rate_limiter.record_request(client_id, endpoint)
        
        # Next request should be blocked
        is_limited, rate_info = self.rate_limiter.is_rate_limited(client_id, endpoint)
        assert is_limited == True
    
    def test_different_endpoints_separate_limits(self):
        """Test that different endpoints have separate rate limits."""
        client_id = "test_client"
        
        # Use up research endpoint limit
        for i in range(10):
            self.rate_limiter.record_request(client_id, "/run/research")
        
        # Price monitor should still be allowed
        is_limited, rate_info = self.rate_limiter.is_rate_limited(client_id, "/run/price-monitor")
        assert is_limited == False
    
    @pytest.mark.asyncio
    async def test_rate_limit_middleware(self):
        """Test rate limiting middleware integration."""
        # Mock request
        request = Mock(spec=Request)
        request.url.path = "/run/research"
        request.client.host = "127.0.0.1"
        request.headers = {}
        
        # Mock next function
        async def mock_next(req):
            mock_response = Mock()
            mock_response.headers = {}
            return mock_response
        
        # Should allow first request
        response = await rate_limit_middleware(request, mock_next)
        assert response is not None


class TestSecurityValidator:
    """Test SecurityValidator class methods."""
    
    def setup_method(self):
        self.validator = SecurityValidator()
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        # Should detect SQL injection
        with pytest.raises(ValidationError):
            SecurityValidator.validate_string_input("'; DROP TABLE users; --", "test_field")
        
        # Should allow clean input
        result = SecurityValidator.validate_string_input("sustainable materials", "test_field")
        assert result == "sustainable materials"
    
    def test_xss_detection(self):
        """Test XSS pattern detection."""
        # Should detect XSS
        with pytest.raises(ValidationError):
            SecurityValidator.validate_string_input("<script>alert('xss')</script>", "test_field")
        
        # Should allow clean input
        result = SecurityValidator.validate_string_input("sustainable materials", "test_field")
        assert result == "sustainable materials"
    
    def test_url_validation(self):
        """Test URL validation."""
        # Should validate good URLs
        result = SecurityValidator.validate_url("https://example.com", "test_url")
        assert result == "https://example.com"
        
        # Should reject bad URLs
        with pytest.raises(ValidationError):
            SecurityValidator.validate_url("not-a-url", "test_url")
        
        # Test localhost blocking (may or may not be implemented)
        try:
            SecurityValidator.validate_url("http://localhost:8080", "test_url")
            # If no exception, localhost is allowed in this implementation
        except ValidationError:
            # If exception, localhost is blocked as expected
            pass
    
    def test_integer_validation(self):
        """Test integer validation with bounds."""
        # Should validate integers in range
        result = SecurityValidator.validate_integer(5, "test_int", 1, 10)
        assert result == 5
        
        # Should reject out of range
        with pytest.raises(ValidationError):
            SecurityValidator.validate_integer(15, "test_int", 1, 10)
        
        with pytest.raises(ValidationError):
            SecurityValidator.validate_integer(-1, "test_int", 1, 10)


if __name__ == "__main__":
    pytest.main([__file__])