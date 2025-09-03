import asyncio, os
from temporalio.worker import Worker
from temporalio.client import Client
from services.orchestrator.workflows import ResearchWorkflow
from services.orchestrator.price_workflows import PriceMonitorWorkflow, ScheduledPriceMonitorWorkflow
from services.orchestrator.research_workflows import ResearchWorkflow as NewResearchWorkflow
from services.orchestrator.model_router import ModelRouter
from services.orchestrator import activities as acts
from services.orchestrator import activities_price as price_acts
from services.orchestrator import activities_research as research_acts
from dotenv import load_dotenv
import yaml

load_dotenv()

async def activity_llm_intro(query: str) -> str:
    cfg = yaml.safe_load(open(os.path.join(os.path.dirname(__file__), 'config.yaml')))
    router = ModelRouter(cfg)
    return await router.run("draft", f"Summarize research goals for: {query}")

async def main():
    client = await Client.connect("localhost:7233")
    worker = Worker(
        client,
        task_queue="ecomate-ai",
        workflows=[ResearchWorkflow, PriceMonitorWorkflow, ScheduledPriceMonitorWorkflow, NewResearchWorkflow],
        activities={
            "activity_llm_intro": activity_llm_intro,
            "activity_fetch_and_log": acts.activity_fetch_and_log,
            "activity_open_docs_pr": acts.activity_open_docs_pr,
            "activity_fetch_prices": price_acts.activity_fetch_prices,
            "activity_generate_price_report": price_acts.activity_generate_price_report,
            "activity_open_price_pr": price_acts.activity_open_price_pr,
            "activity_crawl": research_acts.activity_crawl,
            "activity_struct_extract": research_acts.activity_struct_extract,
            "activity_write_and_pr": research_acts.activity_write_and_pr,
        },
    )
    print("Worker started on task-queue ecomate-ai")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())