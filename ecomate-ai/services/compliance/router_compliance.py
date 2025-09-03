import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from temporalio.client import Client

from .workflows_compliance import (
    ComplianceWorkflow,
    EnhancedComplianceWorkflow,
    ComplianceMetricsWorkflow,
    RulesetInfoWorkflow,
    BatchComplianceWorkflow
)
from .models import SystemType, ComplianceStatus
from .engine import ComplianceEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])

# Request Models
class ComplianceCheckRequest(BaseModel):
    system_id: str = Field(..., description="Unique identifier for the system")
    rules: List[str] = Field(..., description="List of rule names to check")

class EnhancedComplianceRequest(BaseModel):
    system_id: str = Field(..., description="Unique identifier for the system")
    system_type: str = Field(..., description="Type of system (e.g., WATER_TREATMENT, SOLAR_HEATING)")
    specifications: Dict[str, Any] = Field(..., description="System specifications and parameters")
    rulesets: List[str] = Field(..., description="List of ruleset names to evaluate")
    location: Optional[str] = Field(None, description="System location")

class ComplianceMetricsRequest(BaseModel):
    system_ids: List[str] = Field(..., description="List of system IDs to analyze")
    date_range_days: int = Field(30, description="Number of days to analyze", ge=1, le=365)

class BatchComplianceRequest(BaseModel):
    systems: List[Dict[str, Any]] = Field(..., description="List of systems to evaluate")
    rulesets: List[str] = Field(..., description="List of ruleset names to evaluate")

# Legacy endpoint for backward compatibility
@router.post("/check")
async def check_compliance(request: ComplianceCheckRequest):
    """Legacy compliance check endpoint"""
    try:
        client = await Client.connect("localhost:7233")
        result = await client.execute_workflow(
            ComplianceWorkflow.run,
            args=[request.system_id, request.rules],
            id=f"compliance-{request.system_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            task_queue="compliance"
        )
        return result
    except Exception as e:
        logger.error(f"Error in compliance check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhanced-check")
async def enhanced_compliance_check(request: EnhancedComplianceRequest):
    """Enhanced compliance check with structured evaluation"""
    try:
        # Validate system type
        try:
            SystemType(request.system_type)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid system_type. Must be one of: {[t.value for t in SystemType]}"
            )
        
        client = await Client.connect("localhost:7233")
        result = await client.execute_workflow(
            EnhancedComplianceWorkflow.run,
            args=[request.system_id, request.system_type, request.specifications, request.rulesets],
            id=f"enhanced-compliance-{request.system_id}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            task_queue="compliance"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in enhanced compliance check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/metrics")
async def compliance_metrics(request: ComplianceMetricsRequest):
    """Calculate compliance metrics across multiple systems"""
    try:
        client = await Client.connect("localhost:7233")
        result = await client.execute_workflow(
            ComplianceMetricsWorkflow.run,
            args=[request.system_ids, request.date_range_days],
            id=f"compliance-metrics-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            task_queue="compliance"
        )
        return result
    except Exception as e:
        logger.error(f"Error calculating compliance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-check")
async def batch_compliance_check(request: BatchComplianceRequest):
    """Run compliance checks for multiple systems in batch"""
    try:
        # Validate all system types
        for system in request.systems:
            if "system_type" in system:
                try:
                    SystemType(system["system_type"])
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid system_type '{system['system_type']}' for system {system.get('system_id', 'unknown')}. Must be one of: {[t.value for t in SystemType]}"
                    )
        
        client = await Client.connect("localhost:7233")
        result = await client.execute_workflow(
            BatchComplianceWorkflow.run,
            args=[request.systems, request.rulesets],
            id=f"batch-compliance-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            task_queue="compliance"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in batch compliance check: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/rulesets")
async def get_rulesets_info(ruleset_name: Optional[str] = Query(None, description="Specific ruleset name to get info for")):
    """Get information about available rulesets"""
    try:
        client = await Client.connect("localhost:7233")
        result = await client.execute_workflow(
            RulesetInfoWorkflow.run,
            args=[ruleset_name],
            id=f"ruleset-info-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            task_queue="compliance"
        )
        return result
    except Exception as e:
        logger.error(f"Error getting ruleset info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/system-types")
async def get_system_types():
    """Get available system types"""
    return {
        "system_types": [
            {
                "value": system_type.value,
                "description": system_type.name.replace("_", " ").title()
            }
            for system_type in SystemType
        ]
    }

@router.get("/compliance-statuses")
async def get_compliance_statuses():
    """Get available compliance statuses"""
    return {
        "compliance_statuses": [
            {
                "value": status.value,
                "description": status.name.replace("_", " ").title()
            }
            for status in ComplianceStatus
        ]
    }

@router.get("/engine-info")
async def get_engine_info():
    """Get information about the compliance engine"""
    try:
        engine = ComplianceEngine()
        available_rulesets = engine.get_available_rulesets()
        
        rulesets_info = {}
        for ruleset_id in available_rulesets:
            info = engine.get_ruleset_info(ruleset_id)
            if info:
                rulesets_info[ruleset_id] = info
        
        return {
            "engine_version": "2.0.0",
            "available_rulesets": available_rulesets,
            "total_rulesets": len(available_rulesets),
            "rulesets_info": rulesets_info,
            "supported_system_types": [t.value for t in SystemType],
            "supported_operators": [
                "EQUALS", "NOT_EQUALS", "GREATER_THAN", "LESS_THAN",
                "GREATER_THAN_OR_EQUAL", "LESS_THAN_OR_EQUAL",
                "CONTAINS", "NOT_CONTAINS", "STARTS_WITH", "ENDS_WITH",
                "REGEX", "IN_LIST", "NOT_IN_LIST"
            ],
            "supported_severities": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        }
    except Exception as e:
        logger.error(f"Error getting engine info: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        engine = ComplianceEngine()
        available_rulesets = engine.get_available_rulesets()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "available_rulesets_count": len(available_rulesets),
            "engine_status": "operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }