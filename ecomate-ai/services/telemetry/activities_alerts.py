from .ingestor import alert_findings

async def activity_alerts(system_id: str, metrics: dict):
    return {"system_id": system_id, "alerts": alert_findings(metrics)}