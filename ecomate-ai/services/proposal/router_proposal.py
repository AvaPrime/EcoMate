from fastapi import APIRouter
from pydantic import BaseModel
from temporalio.client import Client

router = APIRouter(prefix="/proposals", tags=["proposals"])

class ProposalReq(BaseModel):
    client: dict
    spec: dict
    assumptions: dict = {}

@router.post('/compute')
async def compute(req: ProposalReq):
    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        "services.proposal.workflows_proposal.ProposalWorkflow.run",
        req.client, req.spec, req.assumptions,
        id="proposal-req", task_queue="ecomate-ai",
    )
    return await handle.result()