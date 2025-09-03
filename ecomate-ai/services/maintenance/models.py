from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime, date
from enum import Enum

class AssetType(str, Enum):
    PUMP = "pump"
    TANK = "tank"
    BLOWER = "blower"
    SENSOR = "sensor"
    UV_SYSTEM = "uv_system"
    ELECTRICAL = "electrical"
    PIPING = "piping"
    CONTROL_PANEL = "control_panel"

class AssetCondition(str, Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

class MaintenanceType(str, Enum):
    PREVENTIVE = "preventive"
    CORRECTIVE = "corrective"
    PREDICTIVE = "predictive"
    EMERGENCY = "emergency"

class Asset(BaseModel):
    system_id: str
    asset_id: str
    asset_type: AssetType
    site: Optional[str] = None
    installation_date: Optional[date] = None
    last_service_date: Optional[date] = None
    usage_hours: Optional[float] = 0.0
    condition: AssetCondition = AssetCondition.GOOD
    criticality_score: float = Field(default=5.0, ge=1.0, le=10.0)
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    warranty_expiry: Optional[date] = None
    operating_environment: Dict[str, Any] = Field(default_factory=dict)
    maintenance_history: List[Dict[str, Any]] = Field(default_factory=list)
    
class MaintenanceTask(BaseModel):
    task_id: str
    task_description: str
    asset_types: List[AssetType]
    base_frequency_days: int
    duration_hours: float
    skill_level: str
    tools_required: List[str]
    safety_requirements: List[str]
    cost_estimate: float
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    condition_triggers: List[AssetCondition] = Field(default_factory=list)
    usage_threshold_hours: Optional[float] = None
    environmental_factors: List[str] = Field(default_factory=list)

class WorkOrder(BaseModel):
    system_id: str
    asset_id: Optional[str] = None
    task_id: str
    task: str
    due_date: str
    priority: str = 'normal'
    maintenance_type: MaintenanceType = MaintenanceType.PREVENTIVE
    estimated_duration: float = 0.0
    estimated_cost: float = 0.0
    assigned_technician: Optional[str] = None
    notes: Optional[str] = None
    
class MaintenancePlan(BaseModel):
    system_id: str
    generated_date: datetime
    work_orders: List[WorkOrder]
    total_estimated_cost: float
    total_estimated_hours: float
    priority_summary: Dict[str, int]
    
class AssetMetrics(BaseModel):
    asset_id: str
    days_since_last_service: int
    usage_hours_since_service: float
    condition_score: float
    criticality_multiplier: float
    environmental_risk_factor: float
    recommended_frequency_adjustment: float