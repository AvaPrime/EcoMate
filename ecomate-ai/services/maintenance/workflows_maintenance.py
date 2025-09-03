from temporalio import workflow
from typing import List, Dict, Any, Optional

@workflow.defn
class MaintenancePlanWorkflow:
    @workflow.run
    async def run(self, system_id: str) -> Dict[str, Any]:
        """Legacy maintenance plan workflow"""
        return await workflow.execute_activity(
            'activity_plan', 
            system_id, 
            start_to_close_timeout=300
        )

@workflow.defn
class AssetBasedMaintenancePlanWorkflow:
    @workflow.run
    async def run(self, system_id: str, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Asset-based maintenance plan workflow"""
        return await workflow.execute_activity(
            'activity_asset_based_plan',
            system_id,
            assets_data,
            start_to_close_timeout=600
        )

@workflow.defn
class AssetMetricsWorkflow:
    @workflow.run
    async def run(self, asset_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate asset metrics workflow"""
        return await workflow.execute_activity(
            'activity_asset_metrics',
            asset_data,
            start_to_close_timeout=300
        )

@workflow.defn
class AssetConditionUpdateWorkflow:
    @workflow.run
    async def run(self, asset_id: str, new_condition: str, notes: Optional[str] = None) -> Dict[str, Any]:
        """Update asset condition workflow"""
        return await workflow.execute_activity(
            'activity_update_asset_condition',
            asset_id,
            new_condition,
            notes,
            start_to_close_timeout=300
        )