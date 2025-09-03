"""Regulatory Monitor Service

This service provides automated monitoring and compliance tracking for various
regulatory standards bodies including SANS, ISO, EPA, and other environmental
and safety standards organizations.

Features:
- Real-time standards updates monitoring
- Automated compliance checking
- Multi-standard body integration
- Alert and notification system
- Historical compliance tracking
- Regulatory change impact analysis
"""

from .client import RegulatoryClient
from .service import RegulatoryService
from .models import (
    StandardsBody,
    ComplianceStatus,
    RegulatoryStandard,
    ComplianceCheck,
    RegulatoryAlert,
    StandardsUpdate,
    ComplianceReport,
    RegulatoryQuery,
    RegulatoryResponse
)
from .router import regulatory_router

__version__ = "1.0.0"
__author__ = "EcoMate AI Team"
__description__ = "Regulatory compliance monitoring and standards tracking service"

# Default configuration
DEFAULT_CONFIG = {
    "update_interval": 3600,  # 1 hour in seconds
    "max_retries": 3,
    "timeout": 30,
    "cache_ttl": 1800,  # 30 minutes
    "batch_size": 50,
    "alert_threshold": 0.8
}

# Supported standards bodies
SUPPORTED_BODIES = {
    "SANS": "South African National Standards",
    "ISO": "International Organization for Standardization",
    "EPA": "Environmental Protection Agency",
    "OSHA": "Occupational Safety and Health Administration",
    "ANSI": "American National Standards Institute",
    "ASTM": "American Society for Testing and Materials",
    "IEC": "International Electrotechnical Commission",
    "IEEE": "Institute of Electrical and Electronics Engineers"
}

# API endpoints for different standards bodies
API_ENDPOINTS = {
    "SANS": "https://www.sans.org.za/api/standards",
    "ISO": "https://www.iso.org/api/standards",
    "EPA": "https://www.epa.gov/api/regulations",
    "OSHA": "https://www.osha.gov/api/standards",
    "ANSI": "https://webstore.ansi.org/api/standards",
    "ASTM": "https://www.astm.org/api/standards",
    "IEC": "https://webstore.iec.ch/api/standards",
    "IEEE": "https://standards.ieee.org/api/standards"
}

def create_regulatory_service(
    api_keys: dict = None,
    config: dict = None
) -> RegulatoryService:
    """Create a configured RegulatoryService instance.
    
    Args:
        api_keys: Dictionary of API keys for different standards bodies
        config: Service configuration overrides
        
    Returns:
        Configured RegulatoryService instance
    """
    final_config = {**DEFAULT_CONFIG, **(config or {})}
    client = RegulatoryClient(api_keys=api_keys or {})
    return RegulatoryService(client=client, config=final_config)

def get_supported_standards() -> dict:
    """Get information about supported standards bodies.
    
    Returns:
        Dictionary of supported standards bodies and their descriptions
    """
    return SUPPORTED_BODIES.copy()

def get_api_requirements() -> dict:
    """Get API key requirements for different standards bodies.
    
    Returns:
        Dictionary describing API requirements for each standards body
    """
    return {
        "SANS": {"required": False, "description": "Optional for enhanced access"},
        "ISO": {"required": True, "description": "Required for standards access"},
        "EPA": {"required": False, "description": "Public API available"},
        "OSHA": {"required": False, "description": "Public API available"},
        "ANSI": {"required": True, "description": "Required for standards access"},
        "ASTM": {"required": True, "description": "Required for standards access"},
        "IEC": {"required": True, "description": "Required for standards access"},
        "IEEE": {"required": True, "description": "Required for standards access"}
    }

def get_service_info() -> dict:
    """Get comprehensive service information.
    
    Returns:
        Dictionary with service metadata and capabilities
    """
    return {
        "name": "Regulatory Monitor Service",
        "version": __version__,
        "description": __description__,
        "author": __author__,
        "supported_bodies": len(SUPPORTED_BODIES),
        "features": [
            "Real-time standards monitoring",
            "Automated compliance checking",
            "Multi-standard integration",
            "Alert notifications",
            "Historical tracking",
            "Impact analysis"
        ],
        "endpoints": list(API_ENDPOINTS.keys()),
        "config": DEFAULT_CONFIG
    }

__all__ = [
    "RegulatoryClient",
    "RegulatoryService",
    "StandardsBody",
    "ComplianceStatus",
    "RegulatoryStandard",
    "ComplianceCheck",
    "RegulatoryAlert",
    "StandardsUpdate",
    "ComplianceReport",
    "RegulatoryQuery",
    "RegulatoryResponse",
    "regulatory_router",
    "create_regulatory_service",
    "get_supported_standards",
    "get_api_requirements",
    "get_service_info",
    "DEFAULT_CONFIG",
    "SUPPORTED_BODIES",
    "API_ENDPOINTS"
]