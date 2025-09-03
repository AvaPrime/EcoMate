from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class MetricType(str, Enum):
    FLOW_RATE = "flow_rate"
    PRESSURE = "pressure"
    TEMPERATURE = "temperature"
    PH = "ph"
    TURBIDITY = "turbidity"
    UV_DOSE = "uv_dose"
    DISSOLVED_OXYGEN = "dissolved_oxygen"
    CONDUCTIVITY = "conductivity"
    POWER_CONSUMPTION = "power_consumption"
    EFFICIENCY = "efficiency"
    TSS = "tss"
    BOD = "bod"
    COD = "cod"
    NITROGEN = "nitrogen"
    PHOSPHORUS = "phosphorus"

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"

class TelemetryIn(BaseModel):
    system_id: str
    metrics: Dict[str, float]
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)
    quality_flags: Optional[Dict[str, Any]] = None
    source: Optional[str] = "api"

class TelemetryData(BaseModel):
    id: Optional[int] = None
    system_id: str
    timestamp: datetime
    metric_type: str
    value: float
    unit: Optional[str] = None
    quality_score: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "api"
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class BaselineConfig(BaseModel):
    system_id: str
    metric_type: str
    window_size: int = Field(default=60, description="Number of samples for baseline calculation")
    update_frequency: int = Field(default=300, description="Seconds between baseline updates")
    min_samples: int = Field(default=10, description="Minimum samples required for baseline")
    outlier_threshold: float = Field(default=3.0, description="Z-score threshold for outlier detection")
    enabled: bool = True
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class DynamicBaseline(BaseModel):
    id: Optional[int] = None
    system_id: str
    metric_type: str
    mean_value: float
    std_deviation: float
    min_value: float
    max_value: float
    sample_count: int
    confidence_interval: float = Field(default=0.95)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class AlertRule(BaseModel):
    id: Optional[int] = None
    system_id: str
    metric_type: str
    rule_name: str
    condition: str  # "above_baseline", "below_baseline", "absolute_threshold", "rate_of_change"
    threshold_value: Optional[float] = None
    baseline_multiplier: Optional[float] = None
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = Field(default=15, description="Minutes before same alert can fire again")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

class Alert(BaseModel):
    id: Optional[int] = None
    system_id: str
    rule_id: int
    metric_type: str
    alert_message: str
    severity: AlertSeverity
    status: AlertStatus = AlertStatus.ACTIVE
    triggered_value: float
    baseline_value: Optional[float] = None
    threshold_value: Optional[float] = None
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolution_notes: Optional[str] = None

class TelemetryQuery(BaseModel):
    system_id: str
    metric_types: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: Optional[int] = Field(default=1000, le=10000)
    aggregation: Optional[str] = None  # "avg", "min", "max", "sum", "count"
    interval: Optional[str] = None  # "1m", "5m", "1h", "1d"

class TelemetryResponse(BaseModel):
    system_id: str
    data: List[TelemetryData]
    total_count: int
    has_more: bool = False
    query_time_ms: Optional[float] = None

class BaselineResponse(BaseModel):
    system_id: str
    baselines: List[DynamicBaseline]
    last_updated: datetime

class AlertResponse(BaseModel):
    alerts: List[Alert]
    total_count: int
    active_count: int
    critical_count: int

class SystemMetrics(BaseModel):
    system_id: str
    timestamp: datetime
    metrics: Dict[str, float]
    calculated_metrics: Optional[Dict[str, float]] = None
    quality_flags: Optional[Dict[str, Any]] = None
    alerts_triggered: Optional[List[str]] = None