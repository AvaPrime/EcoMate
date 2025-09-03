from typing import Dict, List, Optional, Any
from datetime import datetime
from .ingestor import (
    process_telemetry_ingestion, evaluate_alerts_dynamic,
    alert_findings_legacy, update_dynamic_baselines
)
from .models import TelemetryIn, TelemetryQuery, BaselineConfig
from .store import get_telemetry_store
import logging

logger = logging.getLogger(__name__)

def activity_alerts(system_id: str, metrics: Dict[str, float]) -> List[str]:
    """Legacy activity to process telemetry alerts for a system (backward compatibility)."""
    return alert_findings_legacy(system_id, metrics)

async def activity_telemetry_ingestion(telemetry_data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced activity for complete telemetry data ingestion with dynamic baselines."""
    try:
        # Convert input to TelemetryIn model
        telemetry = TelemetryIn(**telemetry_data)
        
        # Process complete ingestion pipeline
        result = await process_telemetry_ingestion(telemetry)
        
        return {
            "success": True,
            "system_id": result["system_id"],
            "timestamp": result["timestamp"].isoformat(),
            "metrics_processed": result["metrics_count"],
            "data_stored": result["stored"],
            "baselines_updated": result["baselines_updated"],
            "alerts_count": len(result["alerts"]),
            "alerts": result["alerts"],
            "legacy_alerts_count": len(result["legacy_alerts"]),
            "legacy_alerts": result["legacy_alerts"]
        }
    except Exception as e:
        logger.error(f"Telemetry ingestion activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

async def activity_dynamic_alerts(system_id: str, metrics: Dict[str, float]) -> Dict[str, Any]:
    """Activity to evaluate alerts using dynamic baselines."""
    try:
        alerts = await evaluate_alerts_dynamic(system_id, metrics)
        
        return {
            "success": True,
            "system_id": system_id,
            "alerts_count": len(alerts),
            "alerts": [{
                "metric_type": alert.metric_type,
                "message": alert.alert_message,
                "severity": alert.severity.value,
                "triggered_value": alert.triggered_value,
                "baseline_value": alert.baseline_value,
                "threshold_value": alert.threshold_value,
                "triggered_at": alert.triggered_at.isoformat()
            } for alert in alerts],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Dynamic alerts activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        }

async def activity_baseline_management(system_id: str, metric_types: Optional[List[str]] = None) -> Dict[str, Any]:
    """Activity to manage dynamic baselines for a system."""
    try:
        store = await get_telemetry_store()
        
        if metric_types is None:
            # Get all metric types for the system from recent data
            query = TelemetryQuery(
                system_id=system_id,
                limit=1000
            )
            response = await store.query_telemetry(query)
            metric_types = list(set([data.metric_type for data in response.data]))
        
        # Update baselines
        results = await update_dynamic_baselines(system_id, metric_types)
        
        # Get current baselines
        baseline_response = await store.get_system_baselines(system_id)
        
        return {
            "success": True,
            "system_id": system_id,
            "metric_types_processed": len(metric_types),
            "baselines_updated": results,
            "current_baselines": [{
                "metric_type": baseline.metric_type,
                "mean_value": baseline.mean_value,
                "std_deviation": baseline.std_deviation,
                "sample_count": baseline.sample_count,
                "last_updated": baseline.last_updated.isoformat()
            } for baseline in baseline_response.baselines],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Baseline management activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "system_id": system_id,
            "timestamp": datetime.utcnow().isoformat()
        }

async def activity_telemetry_query(query_params: Dict[str, Any]) -> Dict[str, Any]:
    """Activity to query historical telemetry data."""
    try:
        store = await get_telemetry_store()
        
        # Convert query parameters to TelemetryQuery model
        query = TelemetryQuery(**query_params)
        
        # Execute query
        response = await store.query_telemetry(query)
        
        return {
            "success": True,
            "system_id": response.system_id,
            "data_points": len(response.data),
            "total_count": response.total_count,
            "has_more": response.has_more,
            "query_time_ms": response.query_time_ms,
            "data": [{
                "timestamp": data.timestamp.isoformat(),
                "metric_type": data.metric_type,
                "value": data.value,
                "unit": data.unit,
                "quality_score": data.quality_score,
                "source": data.source
            } for data in response.data],
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Telemetry query activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

async def activity_alert_management(system_id: str, action: str = "get_active", **kwargs) -> Dict[str, Any]:
    """Activity to manage alerts for a system."""
    try:
        store = await get_telemetry_store()
        
        if action == "get_active":
            alert_response = await store.get_active_alerts(system_id)
            return {
                "success": True,
                "system_id": system_id,
                "action": action,
                "total_alerts": alert_response.total_count,
                "active_alerts": alert_response.active_count,
                "critical_alerts": alert_response.critical_count,
                "alerts": [{
                    "id": alert.id,
                    "metric_type": alert.metric_type,
                    "message": alert.alert_message,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "triggered_value": alert.triggered_value,
                    "triggered_at": alert.triggered_at.isoformat()
                } for alert in alert_response.alerts],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "error": f"Unsupported action: {action}",
                "system_id": system_id,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Alert management activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "system_id": system_id,
            "action": action,
            "timestamp": datetime.utcnow().isoformat()
        }

async def activity_baseline_config(system_id: str, metric_type: str, config_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Activity to manage baseline configuration for a metric."""
    try:
        store = await get_telemetry_store()
        
        if config_data:
            # Save new configuration
            config = BaselineConfig(
                system_id=system_id,
                metric_type=metric_type,
                **config_data
            )
            success = await store.save_baseline_config(config)
            
            return {
                "success": success,
                "action": "save_config",
                "system_id": system_id,
                "metric_type": metric_type,
                "config": config.dict(),
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # Get current configuration
            config = await store.get_baseline_config(system_id, metric_type)
            
            return {
                "success": True,
                "action": "get_config",
                "system_id": system_id,
                "metric_type": metric_type,
                "config": config.dict() if config else None,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Baseline config activity failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "system_id": system_id,
            "metric_type": metric_type,
            "timestamp": datetime.utcnow().isoformat()
        }