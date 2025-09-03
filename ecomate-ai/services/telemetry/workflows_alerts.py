from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
from temporalio import workflow
from .activities_alerts import (
    activity_alerts, activity_telemetry_ingestion, activity_dynamic_alerts,
    activity_baseline_management, activity_telemetry_query, activity_alert_management,
    activity_baseline_config
)
from .models import TelemetryIn, TelemetryQuery, BaselineConfig
import logging

logger = logging.getLogger(__name__)

@workflow.defn
class TelemetryAlertWorkflow:
    """Legacy workflow for processing telemetry alerts (backward compatibility)."""
    
    @workflow.run
    async def run(self, system_id: str, metrics: dict):
        return await workflow.execute_activity('activity_alerts', system_id, metrics, start_to_close_timeout=120)
    
    async def execute(self, system_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Execute the legacy telemetry alert workflow."""
        try:
            alerts = activity_alerts(system_id, metrics)
            
            return {
                "workflow": "telemetry_alert_workflow",
                "system_id": system_id,
                "alerts": alerts,
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Legacy telemetry alert workflow failed: {e}")
            return {
                "workflow": "telemetry_alert_workflow",
                "system_id": system_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

class EnhancedTelemetryWorkflow:
    """Enhanced workflow for complete telemetry data processing with dynamic baselines."""
    
    def __init__(self):
        self.name = "enhanced_telemetry_workflow"
    
    async def execute_ingestion(self, telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute complete telemetry ingestion workflow."""
        try:
            result = await activity_telemetry_ingestion(telemetry_data)
            
            return {
                "workflow": self.name,
                "operation": "ingestion",
                "result": result,
                "status": "completed" if result["success"] else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Enhanced telemetry ingestion workflow failed: {e}")
            return {
                "workflow": self.name,
                "operation": "ingestion",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_dynamic_alerts(self, system_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Execute dynamic alerts evaluation workflow."""
        try:
            result = await activity_dynamic_alerts(system_id, metrics)
            
            return {
                "workflow": self.name,
                "operation": "dynamic_alerts",
                "result": result,
                "status": "completed" if result["success"] else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Dynamic alerts workflow failed: {e}")
            return {
                "workflow": self.name,
                "operation": "dynamic_alerts",
                "status": "failed",
                "error": str(e),
                "system_id": system_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_baseline_management(self, system_id: str, metric_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute baseline management workflow."""
        try:
            result = await activity_baseline_management(system_id, metric_types)
            
            return {
                "workflow": self.name,
                "operation": "baseline_management",
                "result": result,
                "status": "completed" if result["success"] else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Baseline management workflow failed: {e}")
            return {
                "workflow": self.name,
                "operation": "baseline_management",
                "status": "failed",
                "error": str(e),
                "system_id": system_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_telemetry_query(self, query_params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute telemetry data query workflow."""
        try:
            result = await activity_telemetry_query(query_params)
            
            return {
                "workflow": self.name,
                "operation": "telemetry_query",
                "result": result,
                "status": "completed" if result["success"] else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Telemetry query workflow failed: {e}")
            return {
                "workflow": self.name,
                "operation": "telemetry_query",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_alert_management(self, system_id: str, action: str = "get_active", **kwargs) -> Dict[str, Any]:
        """Execute alert management workflow."""
        try:
            result = await activity_alert_management(system_id, action, **kwargs)
            
            return {
                "workflow": self.name,
                "operation": "alert_management",
                "result": result,
                "status": "completed" if result["success"] else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Alert management workflow failed: {e}")
            return {
                "workflow": self.name,
                "operation": "alert_management",
                "status": "failed",
                "error": str(e),
                "system_id": system_id,
                "action": action,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def execute_baseline_config(self, system_id: str, metric_type: str, config_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute baseline configuration workflow."""
        try:
            result = await activity_baseline_config(system_id, metric_type, config_data)
            
            return {
                "workflow": self.name,
                "operation": "baseline_config",
                "result": result,
                "status": "completed" if result["success"] else "failed",
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Baseline config workflow failed: {e}")
            return {
                "workflow": self.name,
                "operation": "baseline_config",
                "status": "failed",
                "error": str(e),
                "system_id": system_id,
                "metric_type": metric_type,
                "timestamp": datetime.utcnow().isoformat()
            }

class TelemetryWorkflowOrchestrator:
    """Orchestrator for managing multiple telemetry workflows."""
    
    def __init__(self):
        self.legacy_workflow = TelemetryAlertWorkflow()
        self.enhanced_workflow = EnhancedTelemetryWorkflow()
    
    async def process_telemetry_complete(self, telemetry_data: Dict[str, Any], enable_legacy: bool = True) -> Dict[str, Any]:
        """Process complete telemetry pipeline with both enhanced and legacy workflows."""
        try:
            # Execute enhanced ingestion
            enhanced_result = await self.enhanced_workflow.execute_ingestion(telemetry_data)
            
            results = {
                "orchestrator": "telemetry_workflow_orchestrator",
                "enhanced_result": enhanced_result,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Optionally run legacy workflow for comparison
            if enable_legacy and "system_id" in telemetry_data and "metrics" in telemetry_data:
                legacy_result = await self.legacy_workflow.execute(
                    telemetry_data["system_id"], 
                    telemetry_data["metrics"]
                )
                results["legacy_result"] = legacy_result
            
            return results
        except Exception as e:
            logger.error(f"Telemetry workflow orchestrator failed: {e}")
            return {
                "orchestrator": "telemetry_workflow_orchestrator",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def process_system_monitoring(self, system_id: str, include_baselines: bool = True, include_alerts: bool = True) -> Dict[str, Any]:
        """Process comprehensive system monitoring workflow."""
        try:
            results = {
                "orchestrator": "system_monitoring_orchestrator",
                "system_id": system_id,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Update baselines if requested
            if include_baselines:
                baseline_result = await self.enhanced_workflow.execute_baseline_management(system_id)
                results["baseline_management"] = baseline_result
            
            # Get active alerts if requested
            if include_alerts:
                alert_result = await self.enhanced_workflow.execute_alert_management(system_id, "get_active")
                results["alert_management"] = alert_result
            
            # Query recent telemetry data
            query_params = {
                "system_id": system_id,
                "limit": 100,
                "order_by": "timestamp",
                "order_direction": "desc"
            }
            query_result = await self.enhanced_workflow.execute_telemetry_query(query_params)
            results["recent_data"] = query_result
            
            return results
        except Exception as e:
            logger.error(f"System monitoring orchestrator failed: {e}")
            return {
                "orchestrator": "system_monitoring_orchestrator",
                "system_id": system_id,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }