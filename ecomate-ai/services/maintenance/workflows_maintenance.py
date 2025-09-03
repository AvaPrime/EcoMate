from temporalio import workflow

@workflow.defn
class MaintenancePlanWorkflow:
    @workflow.run
    async def run(self, system_id: str):
        return await workflow.execute_activity('activity_plan', system_id, start_to_close_timeout=300)