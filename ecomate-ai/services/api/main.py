from fastapi import FastAPI
from pydantic import BaseModel
from temporalio.client import Client

app = FastAPI(title="EcoMate AI API")

class ResearchReq(BaseModel):
    query: str
    limit: int = 5

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