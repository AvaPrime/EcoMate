from temporalio import workflow
from datetime import timedelta
from typing import List, Dict
from .activities_research import activity_crawl, activity_struct_extract, activity_write_and_pr

@workflow.defn
class ResearchWorkflow:
    @workflow.run
    async def run(self, urls: List[str]) -> Dict:
        # Step 1: Crawl URLs
        crawled = await workflow.execute_activity(
            activity_crawl,
            urls,
            start_to_close_timeout=timedelta(minutes=10),
        )
        
        # Step 2: Extract structured data using LLM
        structured = await workflow.execute_activity(
            activity_struct_extract,
            crawled,
            start_to_close_timeout=timedelta(minutes=15),
        )
        
        # Step 3: Write to CSV and create PR
        pr_result = await workflow.execute_activity(
            activity_write_and_pr,
            structured,
            start_to_close_timeout=timedelta(minutes=5),
        )
        
        return {
            "crawled_count": len(crawled),
            "suppliers_found": len(structured.get("suppliers", [])),
            "parts_found": len(structured.get("parts", [])),
            "pr_branch": pr_result.get("branch"),
        }