"""Input validation utilities for EcoMate AI API."""

import re
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator
from fastapi import HTTPException, status
from urllib.parse import urlparse
import logging
from services.shared.logging_config import get_logger

logger = get_logger(__name__)

class ValidationError(HTTPException):
    """Custom validation error with structured logging."""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=detail)
        logger.warning("Validation error", extra={
            'field': field,
            'detail': detail,
            'error_type': 'validation_error'
        })

class SecurityValidator:
    """Security-focused input validation."""
    
    # Common patterns for security validation
    SQL_INJECTION_PATTERNS = [
        r"('|(\-\-)|(;)|(\||\|)|(\*|\*))",
        r"(union|select|insert|delete|update|drop|create|alter|exec|execute)",
        r"(script|javascript|vbscript|onload|onerror|onclick)"
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>.*?</iframe>"
    ]
    
    @staticmethod
    def validate_string_input(value: str, field_name: str, max_length: int = 1000) -> str:
        """Validate string input for security threats."""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field_name)
        
        if len(value) > max_length:
            raise ValidationError(f"{field_name} exceeds maximum length of {max_length}", field_name)
        
        # Check for SQL injection patterns
        for pattern in SecurityValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"{field_name} contains potentially malicious content", field_name)
        
        # Check for XSS patterns
        for pattern in SecurityValidator.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                raise ValidationError(f"{field_name} contains potentially malicious script content", field_name)
        
        return value.strip()
    
    @staticmethod
    def validate_url(url: str, field_name: str = "url") -> str:
        """Validate URL format and security."""
        if not isinstance(url, str):
            raise ValidationError(f"{field_name} must be a string", field_name)
        
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError(f"{field_name} must be a valid URL with scheme and domain", field_name)
            
            # Only allow HTTP/HTTPS
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError(f"{field_name} must use HTTP or HTTPS protocol", field_name)
            
            # Block localhost and private IPs in production
            blocked_hosts = ['localhost', '127.0.0.1', '0.0.0.0']
            if parsed.hostname in blocked_hosts:
                raise ValidationError(f"{field_name} cannot target localhost or private IPs", field_name)
            
            return url
        except Exception as e:
            raise ValidationError(f"{field_name} is not a valid URL: {str(e)}", field_name)
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, min_val: int = 0, max_val: int = 1000) -> int:
        """Validate integer input with bounds."""
        try:
            int_val = int(value)
            if int_val < min_val or int_val > max_val:
                raise ValidationError(f"{field_name} must be between {min_val} and {max_val}", field_name)
            return int_val
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} must be a valid integer", field_name)

class ValidatedResearchReq(BaseModel):
    """Validated research request model."""
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)
    
    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        return SecurityValidator.validate_string_input(v, "query", 500)
    
    @field_validator('limit')
    @classmethod
    def validate_limit(cls, v):
        return SecurityValidator.validate_integer(v, "limit", 1, 20)

class ValidatedNewResearchReq(BaseModel):
    """Validated new research request model."""
    urls: List[str] = Field(..., min_items=1, max_items=10)
    
    @field_validator('urls')
    @classmethod
    def validate_urls(cls, v):
        if len(v) > 10:
            raise ValidationError("Maximum 10 URLs allowed", "urls")
        
        validated_urls = []
        for i, url in enumerate(v):
            validated_url = SecurityValidator.validate_url(url, f"urls[{i}]")
            validated_urls.append(validated_url)
        
        return validated_urls

class ValidatedPriceMonitorReq(BaseModel):
    """Validated price monitor request model."""
    create_pr: bool = Field(default=True)
    
    @field_validator('create_pr')
    @classmethod
    def validate_create_pr(cls, v):
        if not isinstance(v, bool):
            raise ValidationError("create_pr must be a boolean", "create_pr")
        return v

def validate_request_size(content_length: Optional[int], max_size: int = 1024 * 1024) -> None:
    """Validate request content size."""
    if content_length and content_length > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Request body too large. Maximum size: {max_size} bytes"
        )

def sanitize_output(data: Any) -> Any:
    """Sanitize output data to prevent information leakage."""
    if isinstance(data, dict):
        # Remove sensitive keys
        sensitive_keys = ['password', 'token', 'secret', 'key', 'api_key']
        return {k: sanitize_output(v) for k, v in data.items() 
                if k.lower() not in sensitive_keys}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    elif isinstance(data, str):
        # Basic HTML encoding for strings
        return data.replace('<', '&lt;').replace('>', '&gt;')
    return data