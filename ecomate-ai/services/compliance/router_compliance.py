from fastapi import APIRouter
from pydantic import BaseModel
from temporalio.client import Client

router = APIRouter(prefix='/compliance', tags=['compliance'])

class CheckReq(BaseModel):
    system_id: str
    rules: list[str]

@router.post('/check')
async def check(req: CheckReq):
    client = await Client.connect('localhost:7233')
    h = await client.start_workflow('services.compliance.workflows_compliance.ComplianceWorkflow.run', req.system_id, req.rules, id=f'comp-{req.system_id}', task_queue='ecomate-ai')
    return await h.result()