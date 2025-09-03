from fastapi import APIRouter
from pydantic import BaseModel
from temporalio.client import Client

router = APIRouter(prefix='/catalog', tags=['catalog'])

class SyncReq(BaseModel):
    source: str = 'shopify'

@router.post('/sync')
async def sync(req: SyncReq):
    client = await Client.connect('localhost:7233')
    h = await client.start_workflow('services.catalog.workflows_catalog.CatalogSyncWorkflow.run', req.source, id='catalog-sync', task_queue='ecomate-ai')
    return await h.result()