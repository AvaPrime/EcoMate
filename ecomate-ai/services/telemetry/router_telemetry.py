from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from .workflows_alerts import EnhancedTelemetryWorkflow, TelemetryWorkflowOrchestrator
from .models import (
    TelemetryIn, BaselineConfig, TelemetryResponse, BaselineResponse, AlertResponse, SystemMetrics
)
from .store import get_telemetry_store
import logging
from temporalio.client import Client
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/telemetry', tags=['telemetry'])

# Initialize workflow orchestrator
orchestrator = TelemetryWorkflowOrchestrator()

class TelemetryReq(BaseModel):
    system_id: str
    metrics: dict

@router.post('/ingest')
async def ingest(req: TelemetryReq):
    """Legacy telemetry ingestion endpoint (backward compatibility)."""
    client = await Client.connect('localhost:7233')
    h = await client.start_workflow('services.telemetry.workflows_alerts.TelemetryAlertWorkflow.run', req.system_id, req.metrics, id=f'tel-{req.system_id}', task_queue='ecomate-ai')
    return await h.result()

@router.post("/ingest/enhanced")
async def ingest_telemetry_enhanced(telemetry: TelemetryIn):
    """Enhanced telemetry ingestion with dynamic baselines and comprehensive processing."""
    try:
        # Convert TelemetryIn to dict for orchestrator
        telemetry_data = telemetry.dict()
        
        # Process through enhanced workflow
        result = await orchestrator.process_telemetry_complete(telemetry_data, enable_legacy=True)
        
        return {
            "status": "success",
            "message": "Telemetry data processed successfully",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Enhanced telemetry ingestion failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Enhanced telemetry ingestion failed",
            "details": str(e),
            "timestamp": datetime.utcnow().isoformat()
        })

@router.post("/systems/{system_id}/alerts/evaluate")
async def evaluate_dynamic_alerts(system_id: str, metrics: Dict[str, float] = Body(...)):
    """Evaluate alerts using dynamic baselines for a specific system."""
    try:
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_dynamic_alerts(system_id, metrics)
        
        return {
            "status": "success",
            "message": "Dynamic alerts evaluated successfully",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Dynamic alerts evaluation failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Dynamic alerts evaluation failed",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/systems/{system_id}/data", response_model=TelemetryResponse)
async def query_telemetry_data(
    system_id: str,
    start_time: Optional[datetime] = Query(None, description="Start time for data query"),
    end_time: Optional[datetime] = Query(None, description="End time for data query"),
    metric_types: Optional[List[str]] = Query(None, description="Filter by specific metric types"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    order_by: str = Query("timestamp", description="Field to order by"),
    order_direction: str = Query("desc", regex="^(asc|desc)$", description="Order direction")
):
    """Query historical telemetry data for a system."""
    try:
        # Build query parameters
        query_params = {
            "system_id": system_id,
            "limit": limit,
            "offset": offset,
            "order_by": order_by,
            "order_direction": order_direction
        }
        
        if start_time:
            query_params["start_time"] = start_time
        if end_time:
            query_params["end_time"] = end_time
        if metric_types:
            query_params["metric_types"] = metric_types
        
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_telemetry_query(query_params)
        
        if result["status"] == "completed" and result["result"]["success"]:
            return result["result"]
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Query failed"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telemetry data query failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Telemetry data query failed",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/systems/{system_id}/baselines", response_model=BaselineResponse)
async def get_system_baselines(system_id: str):
    """Get current dynamic baselines for a system."""
    try:
        store = await get_telemetry_store()
        baseline_response = await store.get_system_baselines(system_id)
        return baseline_response
    except Exception as e:
        logger.error(f"Get system baselines failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve system baselines",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.post("/systems/{system_id}/baselines/update")
async def update_system_baselines(
    system_id: str, 
    metric_types: Optional[List[str]] = Body(None, description="Specific metric types to update")
):
    """Update dynamic baselines for a system."""
    try:
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_baseline_management(system_id, metric_types)
        
        return {
            "status": "success",
            "message": "Baselines updated successfully",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Update system baselines failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to update system baselines",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/systems/{system_id}/alerts", response_model=AlertResponse)
async def get_system_alerts(
    system_id: str,
    active_only: bool = Query(True, description="Return only active alerts"),
    severity_filter: Optional[str] = Query(None, regex="^(low|medium|high|critical)$", description="Filter by severity")
):
    """Get alerts for a system."""
    try:
        action = "get_active" if active_only else "get_all"
        kwargs = {}
        if severity_filter:
            kwargs["severity_filter"] = severity_filter
        
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_alert_management(system_id, action, **kwargs)
        
        if result["status"] == "completed" and result["result"]["success"]:
            return result["result"]
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Alert retrieval failed"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system alerts failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve system alerts",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/systems/{system_id}/baseline-config/{metric_type}")
async def get_baseline_config(system_id: str, metric_type: str):
    """Get baseline configuration for a specific metric type."""
    try:
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_baseline_config(system_id, metric_type)
        
        return {
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get baseline config failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve baseline configuration",
            "details": str(e),
            "system_id": system_id,
            "metric_type": metric_type,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.post("/systems/{system_id}/baseline-config/{metric_type}")
async def save_baseline_config(system_id: str, metric_type: str, config: BaselineConfig):
    """Save baseline configuration for a specific metric type."""
    try:
        config_data = config.dict(exclude={"system_id", "metric_type"})
        
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_baseline_config(system_id, metric_type, config_data)
        
        return {
            "status": "success",
            "message": "Baseline configuration saved successfully",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Save baseline config failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to save baseline configuration",
            "details": str(e),
            "system_id": system_id,
            "metric_type": metric_type,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/systems/{system_id}/monitoring")
async def get_system_monitoring(
    system_id: str,
    include_baselines: bool = Query(True, description="Include baseline management data"),
    include_alerts: bool = Query(True, description="Include active alerts data")
):
    """Get comprehensive monitoring data for a system."""
    try:
        result = await orchestrator.process_system_monitoring(system_id, include_baselines, include_alerts)
        
        return {
            "status": "success",
            "message": "System monitoring data retrieved successfully",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Get system monitoring failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to retrieve system monitoring data",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/systems/{system_id}/metrics/summary", response_model=SystemMetrics)
async def get_system_metrics_summary(
    system_id: str,
    hours: int = Query(24, ge=1, le=168, description="Number of hours to summarize (max 7 days)")
):
    """Get summarized metrics for a system over a specified time period."""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        query_params = {
            "system_id": system_id,
            "start_time": start_time,
            "end_time": end_time,
            "limit": 10000,  # Get enough data for summary
            "order_by": "timestamp",
            "order_direction": "desc"
        }
        
        enhanced_workflow = EnhancedTelemetryWorkflow()
        result = await enhanced_workflow.execute_telemetry_query(query_params)
        
        if result["status"] == "completed" and result["result"]["success"]:
            data = result["result"]["data"]
            
            # Calculate summary statistics
            metric_summaries = {}
            for point in data:
                metric_type = point["metric_type"]
                if metric_type not in metric_summaries:
                    metric_summaries[metric_type] = {
                        "values": [],
                        "unit": point["unit"],
                        "count": 0
                    }
                metric_summaries[metric_type]["values"].append(point["value"])
                metric_summaries[metric_type]["count"] += 1
            
            # Calculate statistics for each metric
            for metric_type, summary in metric_summaries.items():
                values = summary["values"]
                if values:
                    summary["min_value"] = min(values)
                    summary["max_value"] = max(values)
                    summary["avg_value"] = sum(values) / len(values)
                    summary["latest_value"] = values[0]  # First value (most recent due to desc order)
                else:
                    summary["min_value"] = summary["max_value"] = summary["avg_value"] = summary["latest_value"] = 0
                del summary["values"]  # Remove raw values from response
            
            return SystemMetrics(
                system_id=system_id,
                time_period_hours=hours,
                total_data_points=len(data),
                metric_summaries=metric_summaries,
                summary_generated_at=datetime.utcnow()
            )
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "Metrics summary failed"))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get system metrics summary failed: {e}")
        raise HTTPException(status_code=500, detail={
            "error": "Failed to generate system metrics summary",
            "details": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/health")
async def telemetry_health_check():
    """Health check endpoint for telemetry service."""
    try:
        # Test database connection
        store = await get_telemetry_store()
        await store.close()  # Test connection and close
        
        return {
            "status": "healthy",
            "service": "telemetry",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Telemetry health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "telemetry",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }