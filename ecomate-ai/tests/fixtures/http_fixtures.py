"""HTTP client fixtures and mock data for API testing."""

import pytest
import json
from unittest.mock import Mock, AsyncMock

import httpx


@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client for testing HTTP requests."""
    client = Mock(spec=httpx.AsyncClient)
    
    # Configure default responses
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    client.patch = AsyncMock()
    
    return client


@pytest.fixture
def sample_http_responses():
    """Create sample HTTP response data for testing."""
    return {
        "successful_product_page": {
            "status_code": 200,
            "headers": {
                "content-type": "text/html; charset=utf-8",
                "server": "nginx/1.18.0",
                "cache-control": "public, max-age=3600"
            },
            "content": """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Premium Water Pump - Model XP-2000</title>
                <meta name="description" content="High-efficiency water pump for industrial applications">
            </head>
            <body>
                <div class="product-details">
                    <h1 class="product-name">Premium Water Pump - Model XP-2000</h1>
                    <div class="price-container">
                        <span class="current-price">$2,450.00</span>
                        <span class="original-price">$2,650.00</span>
                        <span class="discount">Save $200</span>
                    </div>
                    <div class="specifications">
                        <div class="spec-item">
                            <span class="spec-label">Flow Rate:</span>
                            <span class="spec-value">200 GPM</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Head Pressure:</span>
                            <span class="spec-value">75 PSI</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Power:</span>
                            <span class="spec-value">1200W</span>
                        </div>
                        <div class="spec-item">
                            <span class="spec-label">Material:</span>
                            <span class="spec-value">Stainless Steel 316</span>
                        </div>
                    </div>
                    <div class="availability">
                        <span class="stock-status in-stock">In Stock</span>
                        <span class="shipping-info">Ships within 2-3 business days</span>
                    </div>
                    <div class="product-images">
                        <img src="/images/xp-2000-main.jpg" alt="Main product image">
                        <img src="/images/xp-2000-side.jpg" alt="Side view">
                        <img src="/images/xp-2000-specs.jpg" alt="Technical specifications">
                    </div>
                </div>
            </body>
            </html>
            """
        },
        "product_not_found": {
            "status_code": 404,
            "headers": {
                "content-type": "text/html; charset=utf-8",
                "server": "nginx/1.18.0"
            },
            "content": """
            <!DOCTYPE html>
            <html>
            <head><title>404 - Product Not Found</title></head>
            <body>
                <h1>Product Not Found</h1>
                <p>The requested product could not be found.</p>
            </body>
            </html>
            """
        },
        "server_error": {
            "status_code": 500,
            "headers": {
                "content-type": "text/html; charset=utf-8",
                "server": "nginx/1.18.0"
            },
            "content": """
            <!DOCTYPE html>
            <html>
            <head><title>500 - Internal Server Error</title></head>
            <body>
                <h1>Internal Server Error</h1>
                <p>An unexpected error occurred.</p>
            </body>
            </html>
            """
        },
        "rate_limited": {
            "status_code": 429,
            "headers": {
                "content-type": "application/json",
                "retry-after": "60",
                "x-ratelimit-limit": "100",
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "1642694400"
            },
            "content": json.dumps({
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later.",
                "retry_after": 60
            })
        },
        "timeout_response": {
            "status_code": None,
            "exception": "httpx.TimeoutException",
            "message": "Request timed out after 30 seconds"
        },
        "connection_error": {
            "status_code": None,
            "exception": "httpx.ConnectError",
            "message": "Failed to establish connection"
        }
    }


@pytest.fixture
def sample_api_requests():
    """Create sample API request data for testing."""
    return {
        "research_request": {
            "method": "POST",
            "url": "/api/v1/research",
            "headers": {
                "content-type": "application/json",
                "authorization": "Bearer test-token-123",
                "user-agent": "EcoMate-AI/1.0"
            },
            "json": {
                "product_urls": [
                    "https://example.com/pump1",
                    "https://example.com/pump2",
                    "https://example.com/uv-reactor1"
                ],
                "categories": ["pumps", "uv_reactors"],
                "research_criteria": {
                    "max_price": 5000.00,
                    "min_flow_rate": 50,
                    "required_certifications": ["NSF", "UL"]
                },
                "user_id": "user-123",
                "priority": "high"
            }
        },
        "price_monitoring_request": {
            "method": "POST",
            "url": "/api/v1/price-monitoring",
            "headers": {
                "content-type": "application/json",
                "authorization": "Bearer test-token-456"
            },
            "json": {
                "product_ids": [1, 2, 3, 4, 5],
                "monitoring_frequency": "daily",
                "price_change_threshold": 5.0,
                "alert_preferences": {
                    "email": True,
                    "webhook": "https://example.com/webhook",
                    "immediate_alerts": True
                },
                "user_id": "user-456"
            }
        },
        "workflow_status_request": {
            "method": "GET",
            "url": "/api/v1/workflows/research-workflow-123/status",
            "headers": {
                "authorization": "Bearer test-token-789"
            }
        },
        "invalid_request": {
            "method": "POST",
            "url": "/api/v1/research",
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "product_urls": [],  # Invalid: empty list
                "categories": ["invalid_category"],  # Invalid category
                "research_criteria": {
                    "max_price": -100  # Invalid: negative price
                }
            }
        }
    }


@pytest.fixture
def sample_api_responses():
    """Create sample API response data for testing."""
    return {
        "research_success_response": {
            "status_code": 201,
            "headers": {
                "content-type": "application/json",
                "location": "/api/v1/workflows/research-workflow-123"
            },
            "json": {
                "workflow_id": "research-workflow-123",
                "status": "started",
                "message": "Research workflow initiated successfully",
                "estimated_completion": "2024-01-15T11:30:00Z",
                "products_to_research": 3,
                "created_at": "2024-01-15T10:30:00Z"
            }
        },
        "price_monitoring_success_response": {
            "status_code": 201,
            "headers": {
                "content-type": "application/json",
                "location": "/api/v1/workflows/price-monitoring-456"
            },
            "json": {
                "workflow_id": "price-monitoring-456",
                "status": "active",
                "message": "Price monitoring activated successfully",
                "products_monitored": 5,
                "next_check": "2024-01-16T10:30:00Z",
                "monitoring_frequency": "daily",
                "created_at": "2024-01-15T10:30:00Z"
            }
        },
        "workflow_status_running_response": {
            "status_code": 200,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "workflow_id": "research-workflow-123",
                "status": "running",
                "progress": {
                    "current_step": "scraping_products",
                    "completed_steps": [
                        "validate_input",
                        "initialize_workflow",
                        "fetch_product_pages"
                    ],
                    "remaining_steps": [
                        "parse_product_data",
                        "generate_report"
                    ],
                    "percentage_complete": 60
                },
                "products_processed": 2,
                "products_remaining": 1,
                "estimated_completion": "2024-01-15T11:15:00Z",
                "started_at": "2024-01-15T10:30:00Z"
            }
        },
        "workflow_status_completed_response": {
            "status_code": 200,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "workflow_id": "research-workflow-123",
                "status": "completed",
                "result": {
                    "products_found": 3,
                    "total_processing_time": "00:45:30",
                    "report_url": "https://reports.ecomate.com/research-workflow-123",
                    "summary": {
                        "pumps_found": 2,
                        "uv_reactors_found": 1,
                        "average_price": 2150.00,
                        "price_range": {
                            "min": 850.00,
                            "max": 3500.00
                        }
                    }
                },
                "started_at": "2024-01-15T10:30:00Z",
                "completed_at": "2024-01-15T11:15:30Z"
            }
        },
        "workflow_status_failed_response": {
            "status_code": 200,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "workflow_id": "research-workflow-789",
                "status": "failed",
                "error": {
                    "error_code": "SCRAPING_FAILED",
                    "error_message": "Failed to scrape product data from multiple sources",
                    "failed_urls": [
                        "https://unavailable-site.com/product1",
                        "https://blocked-site.com/product2"
                    ],
                    "retry_count": 3,
                    "last_error_at": "2024-01-15T10:45:00Z"
                },
                "started_at": "2024-01-15T10:30:00Z",
                "failed_at": "2024-01-15T10:45:00Z"
            }
        },
        "validation_error_response": {
            "status_code": 422,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "detail": [
                    {
                        "loc": ["body", "product_urls"],
                        "msg": "ensure this value has at least 1 items",
                        "type": "value_error.list.min_items",
                        "ctx": {"limit_value": 1}
                    },
                    {
                        "loc": ["body", "research_criteria", "max_price"],
                        "msg": "ensure this value is greater than 0",
                        "type": "value_error.number.not_gt",
                        "ctx": {"limit_value": 0}
                    }
                ]
            }
        },
        "unauthorized_response": {
            "status_code": 401,
            "headers": {
                "content-type": "application/json",
                "www-authenticate": "Bearer"
            },
            "json": {
                "detail": "Invalid authentication credentials",
                "error_code": "UNAUTHORIZED"
            }
        },
        "forbidden_response": {
            "status_code": 403,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "detail": "Insufficient permissions to access this resource",
                "error_code": "FORBIDDEN"
            }
        },
        "not_found_response": {
            "status_code": 404,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "detail": "Workflow not found",
                "error_code": "WORKFLOW_NOT_FOUND",
                "workflow_id": "non-existent-workflow"
            }
        },
        "rate_limit_response": {
            "status_code": 429,
            "headers": {
                "content-type": "application/json",
                "retry-after": "300",
                "x-ratelimit-limit": "100",
                "x-ratelimit-remaining": "0",
                "x-ratelimit-reset": "1642694700"
            },
            "json": {
                "detail": "Rate limit exceeded",
                "error_code": "RATE_LIMIT_EXCEEDED",
                "retry_after": 300,
                "limit": 100,
                "window": "1 hour"
            }
        },
        "server_error_response": {
            "status_code": 500,
            "headers": {
                "content-type": "application/json"
            },
            "json": {
                "detail": "Internal server error occurred",
                "error_code": "INTERNAL_SERVER_ERROR",
                "request_id": "req-123456789"
            }
        }
    }


@pytest.fixture
def mock_response_factory(sample_http_responses):
    """Factory function to create mock HTTP responses."""
    def create_response(response_type: str, **kwargs):
        """Create a mock HTTP response based on type."""
        response_data = sample_http_responses.get(response_type, {})
        
        # Handle exception cases
        if "exception" in response_data:
            if response_data["exception"] == "httpx.TimeoutException":
                raise httpx.TimeoutException(response_data["message"])
            elif response_data["exception"] == "httpx.ConnectError":
                raise httpx.ConnectError(response_data["message"])
        
        # Create mock response
        response = Mock(spec=httpx.Response)
        response.status_code = response_data.get("status_code", 200)
        response.headers = response_data.get("headers", {})
        response.text = response_data.get("content", "")
        response.content = response_data.get("content", "").encode("utf-8")
        
        # Override with any provided kwargs
        for key, value in kwargs.items():
            setattr(response, key, value)
        
        return response
    
    return create_response


@pytest.fixture
def mock_api_response_factory(sample_api_responses):
    """Factory function to create mock API responses."""
    def create_api_response(response_type: str, **kwargs):
        """Create a mock API response based on type."""
        response_data = sample_api_responses.get(response_type, {})
        
        response = Mock()
        response.status_code = response_data.get("status_code", 200)
        response.headers = response_data.get("headers", {})
        response.json.return_value = response_data.get("json", {})
        
        # Override with any provided kwargs
        for key, value in kwargs.items():
            if key == "json":
                response.json.return_value = value
            else:
                setattr(response, key, value)
        
        return response
    
    return create_api_response


@pytest.fixture
def http_client_with_retries():
    """Create an HTTP client configured with retry logic for testing."""
    transport = httpx.HTTPTransport(retries=3)
    client = httpx.AsyncClient(
        transport=transport,
        timeout=httpx.Timeout(30.0),
        limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
    )
    return client


@pytest.fixture
def sample_user_agents():
    """Create sample user agent strings for testing."""
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]


@pytest.fixture
def sample_request_headers():
    """Create sample request headers for testing."""
    return {
        "standard_headers": {
            "User-Agent": "EcoMate-AI/1.0 (+https://ecomate.ai/bot)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        },
        "api_headers": {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "EcoMate-AI-Client/1.0",
            "X-API-Version": "v1"
        },
        "authenticated_headers": {
            "Authorization": "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
            "Content-Type": "application/json",
            "Accept": "application/json"
        },
        "rate_limited_headers": {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "5",
            "X-RateLimit-Reset": "1642694400"
        }
    }


@pytest.fixture
def sample_cookies():
    """Create sample cookies for testing."""
    return {
        "session_cookies": {
            "sessionid": "abc123def456ghi789",
            "csrftoken": "xyz789uvw456rst123"
        },
        "tracking_cookies": {
            "_ga": "GA1.2.123456789.1642694400",
            "_gid": "GA1.2.987654321.1642694400",
            "_fbp": "fb.1.1642694400.123456789"
        },
        "preference_cookies": {
            "currency": "USD",
            "language": "en-US",
            "timezone": "America/New_York"
        }
    }


@pytest.fixture
def http_error_scenarios():
    """Create HTTP error scenarios for testing."""
    return {
        "timeout_scenarios": [
            {"timeout": 1.0, "expected_exception": "httpx.TimeoutException"},
            {"timeout": 5.0, "expected_exception": "httpx.TimeoutException"},
            {"timeout": 30.0, "expected_exception": "httpx.TimeoutException"}
        ],
        "connection_scenarios": [
            {"error": "Connection refused", "expected_exception": "httpx.ConnectError"},
            {"error": "Name resolution failed", "expected_exception": "httpx.ConnectError"},
            {"error": "SSL handshake failed", "expected_exception": "httpx.ConnectError"}
        ],
        "http_status_scenarios": [
            {"status_code": 400, "error_type": "Bad Request"},
            {"status_code": 401, "error_type": "Unauthorized"},
            {"status_code": 403, "error_type": "Forbidden"},
            {"status_code": 404, "error_type": "Not Found"},
            {"status_code": 429, "error_type": "Too Many Requests"},
            {"status_code": 500, "error_type": "Internal Server Error"},
            {"status_code": 502, "error_type": "Bad Gateway"},
            {"status_code": 503, "error_type": "Service Unavailable"},
            {"status_code": 504, "error_type": "Gateway Timeout"}
        ]
    }