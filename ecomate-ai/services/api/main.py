from fastapi import FastAPI
from pydantic import BaseModel
from temporalio.client import Client
import uuid
from services.proposal.router_proposal import router as proposal_router
from services.catalog.router_catalog import router as catalog_router
from services.maintenance.router_maintenance import router as maintenance_router
from services.compliance.router_compliance import router as compliance_router
from services.telemetry.router_telemetry import router as telemetry_router

app = FastAPI(title="EcoMate AI API")

# Include routers
app.include_router(proposal_router)
app.include_router(catalog_router)
app.include_router(maintenance_router)
app.include_router(compliance_router)
app.include_router(telemetry_router)

class ResearchReq(BaseModel):
    query: str
    limit: int = 5

class PriceMonitorReq(BaseModel):
    create_pr: bool = True

class NewResearchReq(BaseModel):
    urls: list[str]

@app.post("/run/research")
async def run_research(req: ResearchReq):
    urls = [
        "https://www.example.com/",
        "https://www.google.com/",
        "https://en.wikipedia.org/wiki/Moving_bed_biofilm_reactor",
    ][: req.limit]
    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        "services.orchestrator.workflows.ResearchWorkflow.run",
        req.query,
        urls,
        id=f"research-{req.query[:12]}",
        task_queue="ecomate-ai",
    )
    res = await handle.result()
    return res

@app.post("/run/new-research")
async def run_new_research(req: NewResearchReq):
    """Trigger new research workflow for crawling and extracting supplier/parts data."""
    client = await Client.connect("localhost:7233")
    workflow_id = f"new-research-{uuid.uuid4().hex[:8]}"
    
    handle = await client.start_workflow(
        "services.orchestrator.research_workflows.ResearchWorkflow.run",
        req.urls,
        id=workflow_id,
        task_queue="ecomate-ai",
    )
    
    res = await handle.result()
    return res

@app.post("/run/price-monitor")
async def run_price_monitor(req: PriceMonitorReq):
    """Trigger price monitoring workflow."""
    client = await Client.connect("localhost:7233")
    workflow_id = f"price-monitor-{uuid.uuid4().hex[:8]}"
    
    handle = await client.start_workflow(
        "services.orchestrator.price_workflows.PriceMonitorWorkflow.run",
        req.create_pr,
        id=workflow_id,
        task_queue="ecomate-ai",
    )
    
    res = await handle.result()
    return res

@app.post("/run/scheduled-price-monitor")
async def run_scheduled_price_monitor():
    """Trigger scheduled price monitoring workflow (always creates PR)."""
    client = await Client.connect("localhost:7233")
    workflow_id = f"scheduled-price-monitor-{uuid.uuid4().hex[:8]}"
    
    handle = await client.start_workflow(
        "services.orchestrator.price_workflows.ScheduledPriceMonitorWorkflow.run",
        id=workflow_id,
        task_queue="ecomate-ai",
    )
    
    res = await handle.result()
    return res