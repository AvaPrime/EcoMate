from services.utils.github_pr import open_pr
from .scheduler import tasks_for, AssetBasedScheduler
from .models import Asset, AssetType, AssetCondition
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

async def activity_plan(system_id: str) -> Dict[str, Any]:
    """Legacy activity for backward compatibility"""
    try:
        tasks = tasks_for(system_id)
        today = date.today().isoformat()
        
        # Create GitHub PR with maintenance plan
        open_pr(
            f"bot/maintenance-{system_id}-{today}", 
            f"Maintenance plan {system_id}", 
            {f"maintenance/{system_id}_{today}.json": json.dumps(tasks, indent=2)}
        )
        
        return {"tasks": len(tasks), "system_id": system_id, "generated_date": today}
    except Exception as e:
        logger.error(f"Error generating maintenance plan for {system_id}: {str(e)}")
        return {"error": str(e), "tasks": 0}

async def activity_asset_based_plan(system_id: str, assets_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate asset-based maintenance plan"""
    try:
        scheduler = AssetBasedScheduler()
        
        # Convert asset data to Asset objects
        assets = []
        for asset_data in assets_data:
            asset = Asset(
                system_id=system_id,
                asset_id=asset_data.get('asset_id', f"{system_id}-{len(assets)}"),
                asset_type=AssetType(asset_data.get('asset_type', 'tank')),
                site=asset_data.get('site'),
                installation_date=datetime.fromisoformat(asset_data['installation_date']).date() if asset_data.get('installation_date') else None,
                last_service_date=datetime.fromisoformat(asset_data['last_service_date']).date() if asset_data.get('last_service_date') else None,
                usage_hours=asset_data.get('usage_hours', 0.0),
                condition=AssetCondition(asset_data.get('condition', 'good')),
                criticality_score=asset_data.get('criticality_score', 5.0),
                manufacturer=asset_data.get('manufacturer'),
                model=asset_data.get('model'),
                serial_number=asset_data.get('serial_number'),
                warranty_expiry=datetime.fromisoformat(asset_data['warranty_expiry']).date() if asset_data.get('warranty_expiry') else None,
                operating_environment=asset_data.get('operating_environment', {}),
                maintenance_history=asset_data.get('maintenance_history', [])
            )
            assets.append(asset)
        
        # Generate comprehensive maintenance plan
        maintenance_plan = scheduler.generate_maintenance_plan(system_id, assets)
        
        # Prepare data for GitHub PR
        today = date.today().isoformat()
        plan_data = {
            "system_id": maintenance_plan.system_id,
            "generated_date": maintenance_plan.generated_date.isoformat(),
            "total_estimated_cost": maintenance_plan.total_estimated_cost,
            "total_estimated_hours": maintenance_plan.total_estimated_hours,
            "priority_summary": maintenance_plan.priority_summary,
            "work_orders": [
                {
                    "system_id": wo.system_id,
                    "asset_id": wo.asset_id,
                    "task_id": wo.task_id,
                    "task": wo.task,
                    "due_date": wo.due_date,
                    "priority": wo.priority,
                    "maintenance_type": wo.maintenance_type.value,
                    "estimated_duration": wo.estimated_duration,
                    "estimated_cost": wo.estimated_cost,
                    "notes": wo.notes
                } for wo in maintenance_plan.work_orders
            ]
        }
        
        # Create asset summary
        asset_summary = {
            "total_assets": len(assets),
            "assets_by_type": {},
            "assets_by_condition": {},
            "high_criticality_assets": []
        }
        
        for asset in assets:
            # Count by type
            asset_type = asset.asset_type.value
            asset_summary["assets_by_type"][asset_type] = asset_summary["assets_by_type"].get(asset_type, 0) + 1
            
            # Count by condition
            condition = asset.condition.value
            asset_summary["assets_by_condition"][condition] = asset_summary["assets_by_condition"].get(condition, 0) + 1
            
            # Track high criticality assets
            if asset.criticality_score >= 8.0:
                asset_summary["high_criticality_assets"].append({
                    "asset_id": asset.asset_id,
                    "asset_type": asset.asset_type.value,
                    "criticality_score": asset.criticality_score,
                    "condition": asset.condition.value
                })
        
        # Create GitHub PR with enhanced maintenance plan
        pr_files = {
            f"maintenance/{system_id}_plan_{today}.json": json.dumps(plan_data, indent=2),
            f"maintenance/{system_id}_assets_{today}.json": json.dumps(asset_summary, indent=2)
        }
        
        open_pr(
            f"bot/maintenance-asset-based-{system_id}-{today}", 
            f"Asset-based maintenance plan for {system_id} ({len(assets)} assets)", 
            pr_files
        )
        
        return {
            "success": True,
            "system_id": system_id,
            "total_work_orders": len(maintenance_plan.work_orders),
            "total_estimated_cost": maintenance_plan.total_estimated_cost,
            "total_estimated_hours": maintenance_plan.total_estimated_hours,
            "priority_summary": maintenance_plan.priority_summary,
            "asset_summary": asset_summary,
            "generated_date": maintenance_plan.generated_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating asset-based maintenance plan for {system_id}: {str(e)}")
        return {"error": str(e), "success": False}

async def activity_asset_metrics(asset_data: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate and return asset metrics for maintenance scheduling"""
    try:
        scheduler = AssetBasedScheduler()
        
        # Convert to Asset object
        asset = Asset(
            system_id=asset_data['system_id'],
            asset_id=asset_data['asset_id'],
            asset_type=AssetType(asset_data.get('asset_type', 'tank')),
            site=asset_data.get('site'),
            installation_date=datetime.fromisoformat(asset_data['installation_date']).date() if asset_data.get('installation_date') else None,
            last_service_date=datetime.fromisoformat(asset_data['last_service_date']).date() if asset_data.get('last_service_date') else None,
            usage_hours=asset_data.get('usage_hours', 0.0),
            condition=AssetCondition(asset_data.get('condition', 'good')),
            criticality_score=asset_data.get('criticality_score', 5.0),
            operating_environment=asset_data.get('operating_environment', {})
        )
        
        # Calculate metrics
        metrics = scheduler.calculate_asset_metrics(asset)
        
        return {
            "success": True,
            "asset_id": metrics.asset_id,
            "days_since_last_service": metrics.days_since_last_service,
            "usage_hours_since_service": metrics.usage_hours_since_service,
            "condition_score": metrics.condition_score,
            "criticality_multiplier": metrics.criticality_multiplier,
            "environmental_risk_factor": metrics.environmental_risk_factor,
            "recommended_frequency_adjustment": metrics.recommended_frequency_adjustment,
            "maintenance_urgency": "high" if metrics.recommended_frequency_adjustment > 1.5 else "normal"
        }
        
    except Exception as e:
        logger.error(f"Error calculating asset metrics: {str(e)}")
        return {"error": str(e), "success": False}

async def activity_update_asset_condition(asset_id: str, new_condition: str, notes: Optional[str] = None) -> Dict[str, Any]:
    """Update asset condition and trigger maintenance plan recalculation if needed"""
    try:
        # This would typically update a database, but for now we'll simulate
        condition_enum = AssetCondition(new_condition)
        
        update_data = {
            "asset_id": asset_id,
            "previous_condition": "unknown",  # Would come from database
            "new_condition": condition_enum.value,
            "updated_date": datetime.now().isoformat(),
            "notes": notes,
            "requires_immediate_attention": condition_enum in [AssetCondition.POOR, AssetCondition.CRITICAL]
        }
        
        # Create GitHub PR for condition update
        today = date.today().isoformat()
        open_pr(
            f"bot/asset-condition-update-{asset_id}-{today}",
            f"Asset condition update: {asset_id} -> {condition_enum.value}",
            {f"assets/condition_updates/{asset_id}_{today}.json": json.dumps(update_data, indent=2)}
        )
        
        return {
            "success": True,
            "asset_id": asset_id,
            "new_condition": condition_enum.value,
            "requires_immediate_attention": update_data["requires_immediate_attention"],
            "updated_date": update_data["updated_date"]
        }
        
    except Exception as e:
        logger.error(f"Error updating asset condition for {asset_id}: {str(e)}")
        return {"error": str(e), "success": False}