from temporalio import workflow

@workflow.defn
class ProposalWorkflow:
    @workflow.run
    async def run(self, client: dict, spec: dict, assumptions: dict):
        res = await workflow.execute_activity("activity_build_proposal", client, spec, assumptions, start_to_close_timeout=600)
        return res