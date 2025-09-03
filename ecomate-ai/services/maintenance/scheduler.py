import csv
import json
import math
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Any
from pathlib import Path

from .models import (
    Asset, MaintenanceTask, WorkOrder, MaintenancePlan, AssetMetrics,
    AssetType, AssetCondition, MaintenanceType
)

SCHEDULE = 'data/maintenance_schedule.csv'
ASSETS_DATA = 'data/assets.json'
ENVIRONMENTAL_DATA = 'data/environmental_factors.json'

class AssetBasedScheduler:
    def __init__(self):
        self.maintenance_tasks = self._load_maintenance_tasks()
        self.environmental_factors = self._load_environmental_factors()
        
    def _load_maintenance_tasks(self) -> List[MaintenanceTask]:
        """Load maintenance tasks from CSV and convert to structured format"""
        tasks = []
        try:
            with open(SCHEDULE, newline='', encoding='utf-8') as f:
                for r in csv.DictReader(f):
                    # Map CSV frequency to days
                    frequency_map = {
                        'Monthly': 30,
                        'Quarterly': 90,
                        '6-Monthly': 180,
                        'Annual': 365
                    }
                    
                    # Determine asset types based on task description
                    asset_types = self._infer_asset_types(r['Task Description'])
                    
                    task = MaintenanceTask(
                        task_id=r['Task ID'],
                        task_description=r['Task Description'],
                        asset_types=asset_types,
                        base_frequency_days=frequency_map.get(r['Frequency'], 30),
                        duration_hours=float(r['Duration (Hours)']),
                        skill_level=r['Skill Level'],
                        tools_required=r['Tools Required'].split(' '),
                        safety_requirements=[r['Safety Requirements']] if r['Safety Requirements'] != 'None' else [],
                        cost_estimate=float(r['Cost Estimate'].replace('R', '').replace(',', '')),
                        maintenance_type=MaintenanceType.PREVENTIVE
                    )
                    tasks.append(task)
        except FileNotFoundError:
            # Fallback to basic tasks if CSV not found
            tasks = self._get_default_tasks()
        return tasks
    
    def _infer_asset_types(self, description: str) -> List[AssetType]:
        """Infer asset types from task description"""
        description_lower = description.lower()
        asset_types = []
        
        if any(word in description_lower for word in ['pump', 'vibration']):
            asset_types.append(AssetType.PUMP)
        if any(word in description_lower for word in ['tank', 'inlet', 'sludge']):
            asset_types.append(AssetType.TANK)
        if any(word in description_lower for word in ['blower', 'air']):
            asset_types.append(AssetType.BLOWER)
        if any(word in description_lower for word in ['sensor', 'level', 'calibrat']):
            asset_types.append(AssetType.SENSOR)
        if any(word in description_lower for word in ['uv', 'lamp']):
            asset_types.append(AssetType.UV_SYSTEM)
        if any(word in description_lower for word in ['electrical', 'panel']):
            asset_types.append(AssetType.ELECTRICAL)
        if any(word in description_lower for word in ['pipework', 'piping']):
            asset_types.append(AssetType.PIPING)
            
        return asset_types if asset_types else [AssetType.TANK]  # Default fallback
    
    def _load_environmental_factors(self) -> Dict[str, float]:
        """Load environmental risk factors"""
        try:
            with open(ENVIRONMENTAL_DATA, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                'high_humidity': 1.2,
                'corrosive_environment': 1.3,
                'high_usage': 1.15,
                'extreme_temperature': 1.1,
                'dusty_conditions': 1.05
            }
    
    def _get_default_tasks(self) -> List[MaintenanceTask]:
        """Fallback default tasks if CSV is not available"""
        return [
            MaintenanceTask(
                task_id="M001",
                task_description="Visual inspection of tanks and pipework",
                asset_types=[AssetType.TANK, AssetType.PIPING],
                base_frequency_days=30,
                duration_hours=1.0,
                skill_level="Basic",
                tools_required=["Flashlight"],
                safety_requirements=["Safety vest"],
                cost_estimate=200.0
            )
        ]
    
    def calculate_asset_metrics(self, asset: Asset) -> AssetMetrics:
        """Calculate metrics for asset-based scheduling"""
        today = date.today()
        
        # Days since last service
        days_since_service = 0
        if asset.last_service_date:
            days_since_service = (today - asset.last_service_date).days
        elif asset.installation_date:
            days_since_service = (today - asset.installation_date).days
            
        # Usage hours since last service (simplified calculation)
        usage_hours_since_service = asset.usage_hours or 0.0
        
        # Condition score (lower is worse)
        condition_scores = {
            AssetCondition.EXCELLENT: 1.0,
            AssetCondition.GOOD: 0.8,
            AssetCondition.FAIR: 0.6,
            AssetCondition.POOR: 0.4,
            AssetCondition.CRITICAL: 0.2
        }
        condition_score = condition_scores.get(asset.condition, 0.8)
        
        # Criticality multiplier (higher criticality = more frequent maintenance)
        criticality_multiplier = asset.criticality_score / 5.0
        
        # Environmental risk factor
        env_risk = 1.0
        for factor, multiplier in self.environmental_factors.items():
            if factor in asset.operating_environment:
                env_risk *= multiplier
                
        # Recommended frequency adjustment
        frequency_adjustment = (criticality_multiplier * env_risk) / condition_score
        
        return AssetMetrics(
            asset_id=asset.asset_id,
            days_since_last_service=days_since_service,
            usage_hours_since_service=usage_hours_since_service,
            condition_score=condition_score,
            criticality_multiplier=criticality_multiplier,
            environmental_risk_factor=env_risk,
            recommended_frequency_adjustment=frequency_adjustment
        )
    
    def calculate_dynamic_due_date(self, task: MaintenanceTask, asset: Asset, metrics: AssetMetrics) -> date:
        """Calculate dynamic due date based on asset conditions"""
        base_frequency = task.base_frequency_days
        
        # Adjust frequency based on asset metrics
        adjusted_frequency = base_frequency / metrics.recommended_frequency_adjustment
        
        # Usage-based adjustment
        if task.usage_threshold_hours and metrics.usage_hours_since_service > task.usage_threshold_hours:
            adjusted_frequency *= 0.7  # More frequent maintenance for high usage
            
        # Condition-based triggers
        if asset.condition in task.condition_triggers:
            adjusted_frequency *= 0.5  # Immediate attention needed
            
        # Ensure minimum frequency (don't exceed base frequency by more than 50%)
        adjusted_frequency = max(adjusted_frequency, base_frequency * 0.5)
        
        # Calculate due date
        days_to_add = max(1, int(adjusted_frequency - metrics.days_since_last_service))
        return date.today() + timedelta(days=days_to_add)
    
    def determine_priority(self, task: MaintenanceTask, asset: Asset, metrics: AssetMetrics) -> str:
        """Determine work order priority based on asset conditions"""
        priority_score = 0
        
        # Criticality factor
        priority_score += asset.criticality_score
        
        # Condition factor
        condition_weights = {
            AssetCondition.CRITICAL: 10,
            AssetCondition.POOR: 7,
            AssetCondition.FAIR: 4,
            AssetCondition.GOOD: 2,
            AssetCondition.EXCELLENT: 1
        }
        priority_score += condition_weights.get(asset.condition, 2)
        
        # Overdue factor
        if metrics.days_since_last_service > task.base_frequency_days:
            priority_score += 5
            
        # Environmental risk
        if metrics.environmental_risk_factor > 1.2:
            priority_score += 3
            
        # Determine priority level
        if priority_score >= 15:
            return 'critical'
        elif priority_score >= 10:
            return 'high'
        elif priority_score >= 6:
            return 'medium'
        else:
            return 'normal'
    
    def generate_work_orders_for_asset(self, asset: Asset) -> List[WorkOrder]:
        """Generate work orders for a specific asset"""
        work_orders = []
        metrics = self.calculate_asset_metrics(asset)
        
        for task in self.maintenance_tasks:
            # Check if task applies to this asset type
            if asset.asset_type in task.asset_types:
                due_date = self.calculate_dynamic_due_date(task, asset, metrics)
                priority = self.determine_priority(task, asset, metrics)
                
                work_order = WorkOrder(
                    system_id=asset.system_id,
                    asset_id=asset.asset_id,
                    task_id=task.task_id,
                    task=task.task_description,
                    due_date=due_date.isoformat(),
                    priority=priority,
                    maintenance_type=task.maintenance_type,
                    estimated_duration=task.duration_hours,
                    estimated_cost=task.cost_estimate,
                    notes=f"Asset condition: {asset.condition.value}, Criticality: {asset.criticality_score}"
                )
                work_orders.append(work_order)
                
        return work_orders
    
    def generate_maintenance_plan(self, system_id: str, assets: List[Asset]) -> MaintenancePlan:
        """Generate comprehensive maintenance plan for all assets in a system"""
        all_work_orders = []
        
        for asset in assets:
            work_orders = self.generate_work_orders_for_asset(asset)
            all_work_orders.extend(work_orders)
            
        # Sort by priority and due date
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'normal': 3}
        all_work_orders.sort(key=lambda wo: (priority_order.get(wo.priority, 3), wo.due_date))
        
        # Calculate totals
        total_cost = sum(wo.estimated_cost for wo in all_work_orders)
        total_hours = sum(wo.estimated_duration for wo in all_work_orders)
        
        # Priority summary
        priority_summary = {}
        for wo in all_work_orders:
            priority_summary[wo.priority] = priority_summary.get(wo.priority, 0) + 1
            
        return MaintenancePlan(
            system_id=system_id,
            generated_date=datetime.now(),
            work_orders=all_work_orders,
            total_estimated_cost=total_cost,
            total_estimated_hours=total_hours,
            priority_summary=priority_summary
        )

# Legacy function for backward compatibility
def tasks_for(system_id: str) -> List[Dict[str, Any]]:
    """Legacy function - generates basic tasks without asset-based logic"""
    scheduler = AssetBasedScheduler()
    
    # Create a default asset for backward compatibility
    default_asset = Asset(
        system_id=system_id,
        asset_id=f"{system_id}-default",
        asset_type=AssetType.TANK
    )
    
    work_orders = scheduler.generate_work_orders_for_asset(default_asset)
    
    # Convert to legacy format
    return [{
        'system_id': wo.system_id,
        'task': wo.task,
        'due_date': wo.due_date,
        'priority': wo.priority
    } for wo in work_orders]