import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging
from .models import (
    TelemetryIn, TelemetryData, DynamicBaseline, Alert, AlertRule, 
    AlertSeverity, AlertStatus, BaselineConfig
)
from .store import get_telemetry_store

logger = logging.getLogger(__name__)

# Legacy hardcoded values for backward compatibility
LEGACY_EXPECTED = {
    "flow_m3h": {"mean": 15.2, "std": 2.1},
    "uv_dose_mj_cm2": {"mean": 40.0, "std": 5.0}
}

def mean_std(values: List[float]) -> Tuple[float, float]:
    """Calculate mean and standard deviation of values."""
    if not values:
        return 0.0, 0.0
    
    mean = np.mean(values)
    std = np.std(values)
    return float(mean), float(std)

async def store_telemetry_data(telemetry: TelemetryIn) -> bool:
    """Store incoming telemetry data in the database."""
    try:
        store = await get_telemetry_store()
        
        # Convert metrics dict to individual TelemetryData objects
        data_points = []
        for metric_type, value in telemetry.metrics.items():
            data_point = TelemetryData(
                system_id=telemetry.system_id,
                timestamp=telemetry.timestamp or datetime.utcnow(),
                metric_type=metric_type,
                value=value,
                quality_score=1.0,  # Default quality score
                source=telemetry.source or "api"
            )
            data_points.append(data_point)
        
        # Store batch
        success = await store.store_telemetry_batch(data_points)
        if success:
            logger.info(f"Stored {len(data_points)} telemetry points for system {telemetry.system_id}")
        
        return success
    except Exception as e:
        logger.error(f"Failed to store telemetry data: {e}")
        return False

async def update_dynamic_baselines(system_id: str, metric_types: List[str]) -> Dict[str, bool]:
    """Update dynamic baselines for specified metrics."""
    try:
        store = await get_telemetry_store()
        results = {}
        
        for metric_type in metric_types:
            try:
                baseline = await store.calculate_dynamic_baseline(system_id, metric_type)
                results[metric_type] = baseline is not None
                if baseline:
                    logger.info(f"Updated baseline for {system_id}/{metric_type}: "
                              f"mean={baseline.mean_value:.2f}, std={baseline.std_deviation:.2f}")
            except Exception as e:
                logger.error(f"Failed to update baseline for {metric_type}: {e}")
                results[metric_type] = False
        
        return results
    except Exception as e:
        logger.error(f"Failed to update baselines: {e}")
        return {metric_type: False for metric_type in metric_types}

async def evaluate_alerts_dynamic(system_id: str, metrics: Dict[str, float]) -> List[Alert]:
    """Evaluate alerts using dynamic baselines from database."""
    alerts = []
    
    try:
        store = await get_telemetry_store()
        
        for metric_type, value in metrics.items():
            # Get dynamic baseline
            baseline = await store.get_dynamic_baseline(system_id, metric_type)
            
            if baseline:
                # Check for low value alert (2 sigma below mean)
                threshold = baseline.mean_value - (2 * baseline.std_deviation)
                
                if value < threshold:
                    alert = Alert(
                        system_id=system_id,
                        rule_id=0,  # Default rule ID for dynamic alerts
                        metric_type=metric_type,
                        alert_message=f"Low {metric_type}: {value:.2f} (baseline: {baseline.mean_value:.2f} ± {baseline.std_deviation:.2f})",
                        severity=AlertSeverity.MEDIUM if value < threshold * 0.8 else AlertSeverity.LOW,
                        triggered_value=value,
                        baseline_value=baseline.mean_value,
                        threshold_value=threshold
                    )
                    alerts.append(alert)
                    
                    # Store alert in database
                    try:
                        await store.save_alert(alert)
                    except Exception as e:
                        logger.error(f"Failed to save alert: {e}")
                
                # Check for high value alert (3 sigma above mean)
                high_threshold = baseline.mean_value + (3 * baseline.std_deviation)
                
                if value > high_threshold:
                    alert = Alert(
                        system_id=system_id,
                        rule_id=0,
                        metric_type=metric_type,
                        alert_message=f"High {metric_type}: {value:.2f} (baseline: {baseline.mean_value:.2f} ± {baseline.std_deviation:.2f})",
                        severity=AlertSeverity.HIGH,
                        triggered_value=value,
                        baseline_value=baseline.mean_value,
                        threshold_value=high_threshold
                    )
                    alerts.append(alert)
                    
                    try:
                        await store.save_alert(alert)
                    except Exception as e:
                        logger.error(f"Failed to save alert: {e}")
            else:
                logger.warning(f"No baseline found for {system_id}/{metric_type}, using legacy method")
                # Fall back to legacy method
                legacy_alerts = alert_findings_legacy(system_id, {metric_type: value})
                for alert_msg in legacy_alerts:
                    alert = Alert(
                        system_id=system_id,
                        rule_id=0,
                        metric_type=metric_type,
                        alert_message=alert_msg,
                        severity=AlertSeverity.LOW,
                        triggered_value=value
                    )
                    alerts.append(alert)
    
    except Exception as e:
        logger.error(f"Failed to evaluate dynamic alerts: {e}")
        # Fall back to legacy method
        legacy_alerts = alert_findings_legacy(system_id, metrics)
        for alert_msg in legacy_alerts:
            alert = Alert(
                system_id=system_id,
                rule_id=0,
                metric_type="unknown",
                alert_message=alert_msg,
                severity=AlertSeverity.LOW,
                triggered_value=0.0
            )
            alerts.append(alert)
    
    return alerts

def alert_findings_legacy(system_id: str, metrics: Dict[str, float]) -> List[str]:
    """Legacy alert findings using hardcoded baselines (for backward compatibility)."""
    alerts = []
    
    for metric_name, value in metrics.items():
        # Map new metric names to legacy names
        legacy_name = metric_name
        if metric_name == "flow_rate":
            legacy_name = "flow_m3h"
        elif metric_name == "uv_dose":
            legacy_name = "uv_dose_mj_cm2"
        
        if legacy_name in LEGACY_EXPECTED:
            expected = LEGACY_EXPECTED[legacy_name]
            threshold = expected["mean"] - (2 * expected["std"])  # 2 sigma below mean
            
            if value < threshold:
                alerts.append(
                    f"Low {metric_name}: {value:.2f} (expected: {expected['mean']:.2f} ± {expected['std']:.2f})"
                )
    
    return alerts

# Backward compatibility function
def alert_findings(metrics: dict, headroom: float = 0.8):
    """Legacy function for backward compatibility."""
    findings = []
    for k, exp in LEGACY_EXPECTED.items():
        val = metrics.get(k)
        if val is None: continue
        if val < exp["mean"] * headroom:
            findings.append({"metric": k, "value": val, "expected": exp["mean"], "status": "low"})
    return findings

async def process_telemetry_ingestion(telemetry: TelemetryIn) -> Dict[str, any]:
    """Complete telemetry ingestion pipeline with storage and alerting."""
    result = {
        "system_id": telemetry.system_id,
        "timestamp": telemetry.timestamp or datetime.utcnow(),
        "metrics_count": len(telemetry.metrics),
        "stored": False,
        "baselines_updated": {},
        "alerts": [],
        "legacy_alerts": []
    }
    
    try:
        # 1. Store telemetry data
        result["stored"] = await store_telemetry_data(telemetry)
        
        # 2. Update baselines for new metrics
        metric_types = list(telemetry.metrics.keys())
        result["baselines_updated"] = await update_dynamic_baselines(telemetry.system_id, metric_types)
        
        # 3. Evaluate alerts using dynamic baselines
        alerts = await evaluate_alerts_dynamic(telemetry.system_id, telemetry.metrics)
        result["alerts"] = [{
            "metric_type": alert.metric_type,
            "message": alert.alert_message,
            "severity": alert.severity.value,
            "triggered_value": alert.triggered_value,
            "baseline_value": alert.baseline_value,
            "threshold_value": alert.threshold_value
        } for alert in alerts]
        
        # 4. Also run legacy alerts for comparison
        result["legacy_alerts"] = alert_findings_legacy(telemetry.system_id, telemetry.metrics)
        
        logger.info(f"Processed telemetry for {telemetry.system_id}: "
                   f"{len(alerts)} dynamic alerts, {len(result['legacy_alerts'])} legacy alerts")
        
    except Exception as e:
        logger.error(f"Failed to process telemetry ingestion: {e}")
        result["error"] = str(e)
    
    return result