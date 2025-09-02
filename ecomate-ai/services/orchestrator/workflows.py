from temporalio import workflow
from temporalio.contrib.logger import wf_logger
from services.orchestrator.model_router import ModelRouter
import yaml, os

with open(os.path.join(os.path.dirname(__file__), 'config.yaml'), 'r') as f:
    CFG = yaml.safe_load(f)

@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, query: str, urls: list[str]):
        wf_logger.info(f"Research start: {query} (urls={len(urls)})")
        router = ModelRouter(CFG)
        # Use router for a quick classification/draft (demo)
        intro = await workflow.execute_activity("activity_llm_intro", query, start_to_close_timeout=30)
        findings = await workflow.execute_activity("activity_fetch_and_log", urls, start_to_close_timeout=300)
        result = await workflow.execute_activity("activity_open_docs_pr", findings, start_to_close_timeout=120)
        return {"message": intro, **result}