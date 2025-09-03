from temporalio import workflow

@workflow.defn
class ComplianceWorkflow:
    @workflow.run
    async def run(self, system_id: str, rules: list[str]):
        return await workflow.execute_activity('activity_compliance', system_id, rules, start_to_close_timeout=300)