from temporalio import workflow

@workflow.defn
class TelemetryAlertWorkflow:
    @workflow.run
    async def run(self, system_id: str, metrics: dict):
        return await workflow.execute_activity('activity_alerts', system_id, metrics, start_to_close_timeout=120)