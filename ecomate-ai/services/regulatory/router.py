"""FastAPI router for regulatory monitoring endpoints."""

import asyncio
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import logging

from .service import RegulatoryService
from .client import RegulatoryClient
from .models import (
    StandardsBody,
    RegulatoryQuery,
    RegulatoryResponse,
    BatchRegulatoryRequest,
    BatchRegulatoryResponse,
    ComplianceReport,
    RegulatoryAlert,
    StandardsUpdate,
    ComplianceCheck,
    AlertSeverity,
    StandardCategory,
    ComplianceStatus
)

logger = logging.getLogger(__name__)

# Create router
regulatory_router = APIRouter(
    prefix="/regulatory",
    tags=["regulatory"],
    responses={
        404: {"description": "Not found"},
        500: {"description": "Internal server error"}
    }
)

# Dependency to get regulatory service
async def get_regulatory_service() -> RegulatoryService:
    """Get configured regulatory service instance."""
    client = RegulatoryClient()
    return RegulatoryService(client)


@regulatory_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow()}


@regulatory_router.get("/standards/search")
async def search_standards(
    query: str = Query(..., description="Search query"),
    body: Optional[StandardsBody] = Query(None, description="Standards body"),
    category: Optional[StandardCategory] = Query(None, description="Standard category"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Search for regulatory standards.
    
    Args:
        query: Search query string
        body: Optional standards body filter
        category: Optional category filter
        limit: Maximum number of results
        offset: Results offset for pagination
        service: RegulatoryService dependency
        
    Returns:
        Search results
    """
    try:
        regulatory_query = RegulatoryQuery(
            query_type="search_standards",
            keywords=[query],
            body=body,
            category=category,
            limit=limit,
            offset=offset
        )
        
        response = await service.process_query(regulatory_query)
        
        if not response.success:
            raise HTTPException(status_code=400, detail=response.message)
        
        return {
            "query": query,
            "body": body,
            "category": category,
            "total_results": len(response.data),
            "results": response.data,
            "processing_time": response.processing_time
        }
        
    except Exception as e:
        logger.error(f"Error searching standards: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.get("/standards/{body}/{standard_id}")
async def get_standard(
    body: StandardsBody,
    standard_id: str,
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Get specific regulatory standard.
    
    Args:
        body: Standards body
        standard_id: Standard identifier
        service: RegulatoryService dependency
        
    Returns:
        Standard details
    """
    try:
        async with service.client:
            standard = await service.client.get_standard(body, standard_id)
        
        if not standard:
            raise HTTPException(
                status_code=404,
                detail=f"Standard {standard_id} not found in {body.value}"
            )
        
        return standard.dict()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting standard {standard_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.get("/updates")
async def get_standards_updates(
    bodies: Optional[List[StandardsBody]] = Query(None, description="Standards bodies"),
    since: Optional[date] = Query(None, description="Get updates since date"),
    categories: Optional[List[StandardCategory]] = Query(None, description="Filter by categories"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Get standards updates.
    
    Args:
        bodies: Optional list of standards bodies
        since: Optional date filter
        categories: Optional category filters
        limit: Maximum results
        service: RegulatoryService dependency
        
    Returns:
        Standards updates
    """
    try:
        updates = await service.track_standards_updates(
            bodies=bodies,
            since=since,
            categories=categories
        )
        
        # Apply limit
        limited_updates = updates[:limit]
        
        return {
            "total_updates": len(updates),
            "returned_updates": len(limited_updates),
            "since": since,
            "bodies": bodies,
            "categories": categories,
            "updates": [update.dict() for update in limited_updates]
        }
        
    except Exception as e:
        logger.error(f"Error getting standards updates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.post("/compliance/monitor")
async def monitor_compliance(
    entity_id: str,
    standards: List[str],
    check_interval: int = 3600,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Start compliance monitoring for an entity.
    
    Args:
        entity_id: Entity identifier
        standards: List of standards to monitor
        check_interval: Check interval in seconds
        background_tasks: FastAPI background tasks
        service: RegulatoryService dependency
        
    Returns:
        Monitoring results
    """
    try:
        # Start monitoring in background
        background_tasks.add_task(
            service.monitor_compliance,
            entity_id,
            standards,
            check_interval
        )
        
        # Return immediate response
        return {
            "message": "Compliance monitoring started",
            "entity_id": entity_id,
            "standards": standards,
            "check_interval": check_interval,
            "started_at": datetime.utcnow()
        }
        
    except Exception as e:
        logger.error(f"Error starting compliance monitoring: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.get("/compliance/check/{entity_id}")
async def check_compliance(
    entity_id: str,
    standards: Optional[List[str]] = Query(None, description="Standards to check"),
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Check compliance for an entity.
    
    Args:
        entity_id: Entity identifier
        standards: Optional list of standards
        service: RegulatoryService dependency
        
    Returns:
        Compliance check results
    """
    try:
        if not standards:
            standards = []  # Will use default standards
        
        result = await service.monitor_compliance(
            entity_id=entity_id,
            standards=standards,
            check_interval=0  # One-time check
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking compliance for {entity_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.post("/compliance/report")
async def generate_compliance_report(
    entity_id: str,
    entity_name: str,
    period_start: date,
    period_end: date,
    standards: Optional[List[str]] = None,
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Generate compliance report.
    
    Args:
        entity_id: Entity identifier
        entity_name: Entity name
        period_start: Report period start
        period_end: Report period end
        standards: Optional standards filter
        service: RegulatoryService dependency
        
    Returns:
        Compliance report
    """
    try:
        report = await service.generate_compliance_report(
            entity_id=entity_id,
            entity_name=entity_name,
            period_start=period_start,
            period_end=period_end,
            standards=standards
        )
        
        return report.dict()
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.get("/alerts")
async def get_alerts(
    entity_id: Optional[str] = Query(None, description="Filter by entity"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    since: Optional[date] = Query(None, description="Get alerts since date"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Get regulatory alerts.
    
    Args:
        entity_id: Optional entity filter
        severity: Optional severity filter
        since: Optional date filter
        limit: Maximum results
        service: RegulatoryService dependency
        
    Returns:
        Regulatory alerts
    """
    try:
        alerts = await service.get_regulatory_alerts(
            entity_id=entity_id,
            severity=severity,
            since=since,
            limit=limit
        )
        
        return {
            "total_alerts": len(alerts),
            "entity_id": entity_id,
            "severity": severity,
            "since": since,
            "alerts": [alert.dict() for alert in alerts]
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.post("/impact/assess")
async def assess_regulatory_impact(
    entity_id: str,
    proposed_changes: List[Dict[str, Any]],
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Assess regulatory impact of proposed changes.
    
    Args:
        entity_id: Entity identifier
        proposed_changes: List of proposed changes
        service: RegulatoryService dependency
        
    Returns:
        Impact assessment results
    """
    try:
        assessment = await service.assess_regulatory_impact(
            entity_id=entity_id,
            proposed_changes=proposed_changes
        )
        
        return assessment
        
    except Exception as e:
        logger.error(f"Error assessing regulatory impact: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.post("/query")
async def process_query(
    query: RegulatoryQuery,
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Process a regulatory query.
    
    Args:
        query: RegulatoryQuery object
        service: RegulatoryService dependency
        
    Returns:
        Query response
    """
    try:
        response = await service.process_query(query)
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.post("/batch")
async def process_batch_request(
    batch_request: BatchRegulatoryRequest,
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Process batch regulatory requests.
    
    Args:
        batch_request: BatchRegulatoryRequest object
        service: RegulatoryService dependency
        
    Returns:
        Batch response
    """
    try:
        response = await service.process_batch_request(batch_request)
        return response.dict()
        
    except Exception as e:
        logger.error(f"Error processing batch request: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@regulatory_router.get("/bodies")
async def get_supported_bodies():
    """Get list of supported standards bodies.
    
    Returns:
        List of supported standards bodies
    """
    return {
        "supported_bodies": [
            {
                "code": body.value,
                "name": body.name,
                "description": _get_body_description(body)
            }
            for body in StandardsBody
        ]
    }


@regulatory_router.get("/categories")
async def get_standard_categories():
    """Get list of standard categories.
    
    Returns:
        List of standard categories
    """
    return {
        "categories": [
            {
                "code": category.value,
                "name": category.name,
                "description": _get_category_description(category)
            }
            for category in StandardCategory
        ]
    }


@regulatory_router.get("/status/{entity_id}")
async def get_compliance_status(
    entity_id: str,
    service: RegulatoryService = Depends(get_regulatory_service)
):
    """Get current compliance status for an entity.
    
    Args:
        entity_id: Entity identifier
        service: RegulatoryService dependency
        
    Returns:
        Compliance status summary
    """
    try:
        # Check if we have cached compliance data
        cache_key = f"{entity_id}:*"  # Simplified cache lookup
        
        # For now, return a basic status
        # In practice, this would query the compliance cache or database
        return {
            "entity_id": entity_id,
            "overall_status": ComplianceStatus.COMPLIANT,
            "last_check": datetime.utcnow() - timedelta(hours=1),
            "next_check": datetime.utcnow() + timedelta(hours=23),
            "standards_monitored": 0,
            "active_alerts": 0,
            "compliance_score": 0.85
        }
        
    except Exception as e:
        logger.error(f"Error getting compliance status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Helper functions

def _get_body_description(body: StandardsBody) -> str:
    """Get description for standards body."""
    descriptions = {
        StandardsBody.SANS: "SysAdmin, Audit, Network, and Security Institute",
        StandardsBody.ISO: "International Organization for Standardization",
        StandardsBody.EPA: "Environmental Protection Agency",
        StandardsBody.OSHA: "Occupational Safety and Health Administration",
        StandardsBody.ANSI: "American National Standards Institute",
        StandardsBody.ASTM: "American Society for Testing and Materials",
        StandardsBody.IEC: "International Electrotechnical Commission",
        StandardsBody.IEEE: "Institute of Electrical and Electronics Engineers"
    }
    return descriptions.get(body, "Standards body")


def _get_category_description(category: StandardCategory) -> str:
    """Get description for standard category."""
    descriptions = {
        StandardCategory.SECURITY: "Information security and cybersecurity standards",
        StandardCategory.ENVIRONMENTAL: "Environmental protection and sustainability standards",
        StandardCategory.SAFETY: "Occupational safety and health standards",
        StandardCategory.QUALITY: "Quality management and assurance standards",
        StandardCategory.TECHNICAL: "Technical specifications and requirements",
        StandardCategory.MANAGEMENT: "Management system standards",
        StandardCategory.COMPLIANCE: "Regulatory compliance and audit standards",
        StandardCategory.OTHER: "Other miscellaneous standards"
    }
    return descriptions.get(category, "Standard category")


# Error handlers

@regulatory_router.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "detail": str(exc)}
    )


@regulatory_router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception in regulatory router: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": "An unexpected error occurred"}
    )