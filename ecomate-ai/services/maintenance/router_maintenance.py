from fastapi import APIRouter
from pydantic import BaseModel
from temporalio.client import Client

router = APIRouter(prefix='/maintenance', tags=['maintenance'])

class PlanReq(BaseModel):
    system_id: str

@router.post('/plan')
async def plan(req: PlanReq):
    client = await Client.connect('localhost:7233')
    h = await client.start_workflow('services.maintenance.workflows_maintenance.MaintenancePlanWorkflow.run', req.system_id, id=f'maint-{req.system_id}', task_queue='ecomate-ai')
    return await h.result()