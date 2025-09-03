from fastapi import APIRouter
from temporalio.client import Client
from pydantic import BaseModel

router = APIRouter(prefix='/telemetry', tags=['telemetry'])

class TelemetryReq(BaseModel):
    system_id: str
    metrics: dict

@router.post('/ingest')
async def ingest(req: TelemetryReq):
    client = await Client.connect('localhost:7233')
    h = await client.start_workflow('services.telemetry.workflows_alerts.TelemetryAlertWorkflow.run', req.system_id, req.metrics, id=f'tel-{req.system_id}', task_queue='ecomate-ai')
    return await h.result()