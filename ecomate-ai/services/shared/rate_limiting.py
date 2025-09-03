"""Rate limiting middleware for EcoMate AI API."""

import time
import asyncio
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
import logging
from datetime import datetime, timedelta
from services.shared.logging_config import get_logger

logger = get_logger(__name__)

class RateLimiter:
    """Token bucket rate limiter with sliding window."""
    
    def __init__(self):
        # Store rate limit data: {client_id: {endpoint: deque of timestamps}}
        self.requests: Dict[str, Dict[str, deque]] = defaultdict(lambda: defaultdict(deque))
        self.cleanup_interval = 300  # Clean up old entries every 5 minutes
        self.last_cleanup = time.time()
        
        # Rate limit configurations
        self.rate_limits = {
            # Global limits (requests per minute)
            'global': {'requests': 100, 'window': 60},
            
            # Endpoint-specific limits
            '/run/research': {'requests': 10, 'window': 60},
            '/run/new-research': {'requests': 5, 'window': 60},
            '/run/price-monitor': {'requests': 20, 'window': 60},
            '/run/scheduled-price-monitor': {'requests': 10, 'window': 60},
            
            # Service router limits
            '/api/v1/proposals': {'requests': 50, 'window': 60},
            '/api/v1/catalog': {'requests': 100, 'window': 60},
            '/api/v1/maintenance': {'requests': 30, 'window': 60},
            '/api/v1/compliance': {'requests': 40, 'window': 60},
            '/api/v1/telemetry': {'requests': 200, 'window': 60},
            '/api/v1/regulatory': {'requests': 30, 'window': 60},
            '/api/v1/geospatial': {'requests': 50, 'window': 60},
            '/api/v1/climate': {'requests': 40, 'window': 60},
            '/api/v1/iot': {'requests': 100, 'window': 60},
            
            # Health and monitoring endpoints (more permissive)
            '/health': {'requests': 1000, 'window': 60},
            '/metrics': {'requests': 500, 'window': 60},
            '/ready': {'requests': 1000, 'window': 60},
            '/live': {'requests': 1000, 'window': 60},
        }
    
    def get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Try to get client IP
        client_ip = None
        if request.client:
            client_ip = request.client.host
        
        # Check for forwarded IP headers (for load balancers)
        forwarded_for = request.headers.get('X-Forwarded-For')
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()
        
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            client_ip = real_ip
        
        # Fallback to a default if no IP found
        return client_ip or 'unknown'
    
    def get_rate_limit_config(self, endpoint: str) -> Dict[str, int]:
        """Get rate limit configuration for endpoint."""
        # Check for exact match first
        if endpoint in self.rate_limits:
            return self.rate_limits[endpoint]
        
        # Check for prefix matches (for router endpoints)
        for pattern, config in self.rate_limits.items():
            if endpoint.startswith(pattern):
                return config
        
        # Default rate limit
        return {'requests': 60, 'window': 60}
    
    def cleanup_old_requests(self):
        """Clean up old request records to prevent memory leaks."""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - 3600  # Remove records older than 1 hour
        
        for client_id in list(self.requests.keys()):
            client_data = self.requests[client_id]
            for endpoint in list(client_data.keys()):
                endpoint_requests = client_data[endpoint]
                
                # Remove old timestamps
                while endpoint_requests and endpoint_requests[0] < cutoff_time:
                    endpoint_requests.popleft()
                
                # Remove empty endpoint records
                if not endpoint_requests:
                    del client_data[endpoint]
            
            # Remove empty client records
            if not client_data:
                del self.requests[client_id]
        
        self.last_cleanup = current_time
        logger.debug("Rate limiter cleanup completed", extra={
            'active_clients': len(self.requests),
            'cleanup_time': current_time
        })
    
    def is_rate_limited(self, client_id: str, endpoint: str) -> Tuple[bool, Dict[str, int]]:
        """Check if client is rate limited for endpoint."""
        current_time = time.time()
        config = self.get_rate_limit_config(endpoint)
        window_start = current_time - config['window']
        
        # Get request history for this client and endpoint
        endpoint_requests = self.requests[client_id][endpoint]
        
        # Remove old requests outside the window
        while endpoint_requests and endpoint_requests[0] < window_start:
            endpoint_requests.popleft()
        
        # Check if limit exceeded
        current_requests = len(endpoint_requests)
        is_limited = current_requests >= config['requests']
        
        # Also check global rate limit
        global_config = self.rate_limits['global']
        global_window_start = current_time - global_config['window']
        
        # Count all requests across all endpoints for this client
        total_requests = 0
        for ep_requests in self.requests[client_id].values():
            total_requests += sum(1 for req_time in ep_requests if req_time > global_window_start)
        
        global_limited = total_requests >= global_config['requests']
        
        rate_limit_info = {
            'requests_made': current_requests,
            'requests_limit': config['requests'],
            'window_seconds': config['window'],
            'global_requests': total_requests,
            'global_limit': global_config['requests'],
            'reset_time': int(window_start + config['window'])
        }
        
        return is_limited or global_limited, rate_limit_info
    
    def record_request(self, client_id: str, endpoint: str):
        """Record a request for rate limiting."""
        current_time = time.time()
        self.requests[client_id][endpoint].append(current_time)
        
        # Periodic cleanup
        self.cleanup_old_requests()

# Global rate limiter instance
rate_limiter = RateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Rate limiting middleware."""
    client_id = rate_limiter.get_client_id(request)
    endpoint = request.url.path
    
    # Skip rate limiting for certain endpoints in development
    skip_endpoints = ['/docs', '/redoc', '/openapi.json', '/']
    if endpoint in skip_endpoints:
        return await call_next(request)
    
    # Check rate limit
    is_limited, rate_info = rate_limiter.is_rate_limited(client_id, endpoint)
    
    if is_limited:
        logger.warning("Rate limit exceeded", extra={
            'client_id': client_id,
            'endpoint': endpoint,
            'rate_info': rate_info
        })
        
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {rate_info['requests_limit']} per {rate_info['window_seconds']} seconds",
                "retry_after": rate_info['reset_time'] - int(time.time()),
                "rate_limit_info": rate_info,
                "timestamp": datetime.utcnow().isoformat()
            },
            headers={
                "X-RateLimit-Limit": str(rate_info['requests_limit']),
                "X-RateLimit-Remaining": str(max(0, rate_info['requests_limit'] - rate_info['requests_made'])),
                "X-RateLimit-Reset": str(rate_info['reset_time']),
                "Retry-After": str(max(1, rate_info['reset_time'] - int(time.time())))
            }
        )
    
    # Record the request
    rate_limiter.record_request(client_id, endpoint)
    
    # Add rate limit headers to response
    response = await call_next(request)
    
    response.headers["X-RateLimit-Limit"] = str(rate_info['requests_limit'])
    response.headers["X-RateLimit-Remaining"] = str(max(0, rate_info['requests_limit'] - rate_info['requests_made'] - 1))
    response.headers["X-RateLimit-Reset"] = str(rate_info['reset_time'])
    
    return response

class RateLimitConfig:
    """Configuration class for rate limiting."""
    
    @staticmethod
    def update_rate_limit(endpoint: str, requests: int, window: int):
        """Update rate limit for specific endpoint."""
        rate_limiter.rate_limits[endpoint] = {'requests': requests, 'window': window}
        logger.info("Rate limit updated", extra={
            'endpoint': endpoint,
            'requests': requests,
            'window': window
        })
    
    @staticmethod
    def get_current_limits() -> Dict[str, Dict[str, int]]:
        """Get current rate limit configuration."""
        return rate_limiter.rate_limits.copy()
    
    @staticmethod
    def get_client_stats(client_id: str) -> Dict[str, any]:
        """Get current statistics for a client."""
        if client_id not in rate_limiter.requests:
            return {'endpoints': {}, 'total_requests': 0}
        
        current_time = time.time()
        client_data = rate_limiter.requests[client_id]
        stats = {'endpoints': {}, 'total_requests': 0}
        
        for endpoint, requests in client_data.items():
            # Count requests in last hour
            recent_requests = sum(1 for req_time in requests if req_time > current_time - 3600)
            stats['endpoints'][endpoint] = recent_requests
            stats['total_requests'] += recent_requests
        
        return stats