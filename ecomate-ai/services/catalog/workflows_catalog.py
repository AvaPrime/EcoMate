from temporalio import workflow

@workflow.defn
class CatalogSyncWorkflow:
    @workflow.run
    async def run(self, source: str = 'shopify'):
        return await workflow.execute_activity('activity_catalog_sync', source, start_to_close_timeout=600)