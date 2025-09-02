import asyncio, os
from temporalio.worker import Worker
from temporalio.client import Client
from services.orchestrator.workflows import ResearchWorkflow
from services.orchestrator.model_router import ModelRouter
from services.orchestrator import activities as acts
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
        workflows=[ResearchWorkflow],
        activities={
            "activity_llm_intro": activity_llm_intro,
            "activity_fetch_and_log": acts.activity_fetch_and_log,
            "activity_open_docs_pr": acts.activity_open_docs_pr,
        },
    )
    print("Worker started on task-queue ecomate-ai")
    await worker.run()

if __name__ == "__main__":
    asyncio.run(main())