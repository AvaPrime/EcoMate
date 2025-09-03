"""
IoT Ingestion Pipeline - Data Models

Pydantic models for IoT devices, messages, alerts, dashboards, and configuration.
Provides comprehensive data validation and serialization for the IoT ecosystem.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator


# Enumerations
class Protocol(str, Enum):
    """Supported IoT communication protocols."""
    MQTT = "mqtt"
    HTTP = "http"
    WEBSOCKET = "websocket"
    COAP = "coap"
    LORAWAN = "lorawan"
    MODBUS = "modbus"
    ZIGBEE = "zigbee"
    BLUETOOTH = "bluetooth"
    WIFI = "wifi"
    CELLULAR = "cellular"


class DeviceType(str, Enum):
    """Types of IoT devices."""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    GATEWAY = "gateway"
    CONTROLLER = "controller"
    CAMERA = "camera"
    DISPLAY = "display"
    BEACON = "beacon"
    TRACKER = "tracker"


class DeviceState(str, Enum):
    """Device operational states."""
    ONLINE = "online"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"
    PROVISIONING = "provisioning"
    DECOMMISSIONED = "decommissioned"


class MessageType(str, Enum):
    """Types of IoT messages."""
    TELEMETRY = "telemetry"
    COMMAND = "command"
    RESPONSE = "response"
    ALERT = "alert"
    HEARTBEAT = "heartbeat"
    CONFIG = "config"
    FIRMWARE = "firmware"
    DIAGNOSTIC = "diagnostic"


class DataFormat(str, Enum):
    """Supported data formats."""
    JSON = "json"
    PROTOBUF = "protobuf"
    AVRO = "avro"
    CSV = "csv"
    XML = "xml"
    BINARY = "binary"
    MSGPACK = "msgpack"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStage(str, Enum):
    """Data processing pipeline stages."""
    INGESTION = "ingestion"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    ENRICHMENT = "enrichment"
    STORAGE = "storage"
    ANALYTICS = "analytics"
    ALERTING = "alerting"


class ChartType(str, Enum):
    """Dashboard chart types."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    GAUGE = "gauge"
    HEATMAP = "heatmap"
    TABLE = "table"
    MAP = "map"


# Device Models
class DeviceCredentials(BaseModel):
    """Device authentication credentials."""
    device_id: str
    certificate_path: Optional[str] = None
    private_key_path: Optional[str] = None
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeviceConfig(BaseModel):
    """Device configuration settings."""
    sampling_rate: int = Field(default=60, description="Data sampling rate in seconds")
    reporting_interval: int = Field(default=300, description="Data reporting interval in seconds")
    heartbeat_interval: int = Field(default=60, description="Heartbeat interval in seconds")
    max_offline_time: int = Field(default=900, description="Max offline time before alert in seconds")
    data_format: DataFormat = DataFormat.JSON
    compression_enabled: bool = False
    encryption_enabled: bool = True
    batch_size: int = Field(default=1, ge=1, le=1000)
    buffer_size: int = Field(default=100, ge=1, le=10000)
    retry_attempts: int = Field(default=3, ge=0, le=10)
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class DeviceLocation(BaseModel):
    """Device geographical location."""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    accuracy: Optional[float] = None
    address: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[str] = None
    room: Optional[str] = None


class DeviceMetrics(BaseModel):
    """Device performance and health metrics."""
    device_id: str
    timestamp: datetime
    cpu_usage: Optional[float] = Field(None, ge=0, le=100)
    memory_usage: Optional[float] = Field(None, ge=0, le=100)
    disk_usage: Optional[float] = Field(None, ge=0, le=100)
    network_usage: Optional[float] = Field(None, ge=0)
    battery_level: Optional[float] = Field(None, ge=0, le=100)
    temperature: Optional[float] = None
    signal_strength: Optional[float] = Field(None, ge=-120, le=0)
    uptime_seconds: Optional[int] = Field(None, ge=0)
    message_count: Optional[int] = Field(None, ge=0)
    error_count: Optional[int] = Field(None, ge=0)
    last_error: Optional[str] = None
    custom_metrics: Dict[str, float] = Field(default_factory=dict)


class Device(BaseModel):
    """IoT device representation."""
    device_id: str = Field(..., description="Unique device identifier")
    name: str = Field(..., description="Human-readable device name")
    device_type: DeviceType
    protocol: Protocol
    state: DeviceState = DeviceState.PROVISIONING
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    firmware_version: Optional[str] = None
    hardware_version: Optional[str] = None
    serial_number: Optional[str] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    location: Optional[DeviceLocation] = None
    config: DeviceConfig = Field(default_factory=DeviceConfig)
    credentials: Optional[DeviceCredentials] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: Optional[datetime] = None
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Message Models
class SensorReading(BaseModel):
    """Individual sensor reading."""
    sensor_id: str
    sensor_type: str
    value: Union[float, int, str, bool]
    unit: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    quality: Optional[float] = Field(None, ge=0, le=1, description="Data quality score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IoTMessage(BaseModel):
    """IoT message structure."""
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    device_id: str
    message_type: MessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: Dict[str, Any]
    sensor_readings: List[SensorReading] = Field(default_factory=list)
    protocol: Protocol
    data_format: DataFormat = DataFormat.JSON
    sequence_number: Optional[int] = None
    correlation_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    ttl_seconds: Optional[int] = Field(None, ge=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Alert Models
class AlertRule(BaseModel):
    """Alert rule definition."""
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    device_id: Optional[str] = None
    device_type: Optional[DeviceType] = None
    condition: str = Field(..., description="Alert condition expression")
    severity: AlertSeverity = AlertSeverity.MEDIUM
    enabled: bool = True
    cooldown_minutes: int = Field(default=15, ge=0)
    notification_channels: List[str] = Field(default_factory=list)
    actions: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Alert(BaseModel):
    """Alert instance."""
    alert_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_id: str
    device_id: str
    title: str
    description: Optional[str] = None
    severity: AlertSeverity
    status: str = Field(default="active", pattern="^(active|acknowledged|resolved|suppressed)$")
    triggered_at: datetime = Field(default_factory=datetime.utcnow)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_by: Optional[str] = None
    trigger_value: Optional[Union[float, int, str]] = None
    threshold_value: Optional[Union[float, int, str]] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Pipeline Models
class TransformationRule(BaseModel):
    """Data transformation rule."""
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    input_field: str
    output_field: str
    transformation_type: str = Field(..., pattern="^(map|filter|aggregate|calculate|format)$")
    expression: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    order: int = Field(default=0, description="Execution order")


class DataPipeline(BaseModel):
    """Data processing pipeline configuration."""
    pipeline_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    device_filter: Optional[str] = None
    message_type_filter: List[MessageType] = Field(default_factory=list)
    stages: List[ProcessingStage] = Field(default_factory=list)
    transformation_rules: List[TransformationRule] = Field(default_factory=list)
    output_destinations: List[str] = Field(default_factory=list)
    batch_size: int = Field(default=100, ge=1, le=10000)
    batch_timeout_ms: int = Field(default=5000, ge=100, le=60000)
    parallel_workers: int = Field(default=1, ge=1, le=16)
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Dashboard Models
class Chart(BaseModel):
    """Dashboard chart configuration."""
    chart_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    chart_type: ChartType
    data_source: str
    query: str
    refresh_interval_ms: int = Field(default=5000, ge=1000, le=300000)
    time_range_minutes: int = Field(default=60, ge=1, le=10080)
    max_data_points: int = Field(default=1000, ge=10, le=10000)
    options: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, int] = Field(default_factory=dict)
    size: Dict[str, int] = Field(default_factory=dict)


class Widget(BaseModel):
    """Dashboard widget."""
    widget_id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    widget_type: str = Field(..., pattern="^(chart|metric|alert|device_status|map)$")
    config: Dict[str, Any] = Field(default_factory=dict)
    chart: Optional[Chart] = None
    position: Dict[str, int] = Field(default_factory=dict)
    size: Dict[str, int] = Field(default_factory=dict)
    visible: bool = True


class Dashboard(BaseModel):
    """IoT dashboard configuration."""
    dashboard_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    widgets: List[Widget] = Field(default_factory=list)
    layout: Dict[str, Any] = Field(default_factory=dict)
    refresh_interval_ms: int = Field(default=5000, ge=1000, le=300000)
    auto_refresh: bool = True
    public: bool = False
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Configuration Models
class ProtocolConfig(BaseModel):
    """Protocol-specific configuration."""
    protocol: Protocol
    host: str = "localhost"
    port: int
    ssl_enabled: bool = False
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: Optional[str] = None
    keep_alive: int = 60
    qos: int = Field(default=1, ge=0, le=2)
    retain: bool = False
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_connections: int = Field(default=100, ge=1, le=10000)
    additional_options: Dict[str, Any] = Field(default_factory=dict)


class SecurityConfig(BaseModel):
    """Security configuration."""
    jwt_secret: str
    jwt_expiry_hours: int = Field(default=24, ge=1, le=8760)
    device_cert_path: Optional[str] = None
    ca_cert_path: Optional[str] = None
    encryption_algorithm: str = "AES-256-GCM"
    hash_algorithm: str = "SHA-256"
    min_password_length: int = Field(default=8, ge=6, le=128)
    require_device_certificates: bool = True
    enable_api_key_auth: bool = True
    enable_jwt_auth: bool = True
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10000)
    max_failed_attempts: int = Field(default=5, ge=1, le=100)
    lockout_duration_minutes: int = Field(default=15, ge=1, le=1440)


class StorageConfig(BaseModel):
    """Storage configuration."""
    timeseries_db: str = Field(default="influxdb", pattern="^(influxdb|timescaledb|prometheus)$")
    influxdb_url: Optional[str] = None
    influxdb_token: Optional[str] = None
    influxdb_org: Optional[str] = None
    influxdb_bucket: Optional[str] = None
    postgres_url: Optional[str] = None
    redis_url: Optional[str] = None
    retention_days: int = Field(default=90, ge=1, le=3650)
    compression_enabled: bool = True
    backup_enabled: bool = True
    backup_interval_hours: int = Field(default=24, ge=1, le=168)


class ProcessingConfig(BaseModel):
    """Data processing configuration."""
    batch_size: int = Field(default=1000, ge=1, le=100000)
    batch_timeout_ms: int = Field(default=5000, ge=100, le=60000)
    max_workers: int = Field(default=4, ge=1, le=64)
    enable_real_time: bool = True
    buffer_size: int = Field(default=10000, ge=100, le=1000000)
    max_memory_mb: int = Field(default=512, ge=64, le=8192)
    enable_compression: bool = True
    enable_deduplication: bool = True
    deduplication_window_minutes: int = Field(default=5, ge=1, le=60)


class IoTConfig(BaseModel):
    """Main IoT service configuration."""
    service_name: str = "iot-ingestion-pipeline"
    version: str = "1.0.0"
    protocols: List[ProtocolConfig] = Field(default_factory=list)
    security: SecurityConfig
    storage: StorageConfig = Field(default_factory=StorageConfig)
    processing: ProcessingConfig = Field(default_factory=ProcessingConfig)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    metrics_enabled: bool = True
    health_check_interval_seconds: int = Field(default=30, ge=5, le=300)
    
    @field_validator('protocols')
    @classmethod
    def validate_protocols(cls, v):
        if not v:
            # Add default MQTT protocol if none specified
            v.append(ProtocolConfig(
                protocol=Protocol.MQTT,
                host="localhost",
                port=1883
            ))
        return v


# Request/Response Models
class DeviceRegistrationRequest(BaseModel):
    """Device registration request."""
    device_id: str
    name: str
    device_type: DeviceType
    protocol: Protocol
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    location: Optional[DeviceLocation] = None
    config: Optional[DeviceConfig] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DeviceUpdateRequest(BaseModel):
    """Device update request."""
    name: Optional[str] = None
    state: Optional[DeviceState] = None
    location: Optional[DeviceLocation] = None
    config: Optional[DeviceConfig] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MessageIngestionRequest(BaseModel):
    """Message ingestion request."""
    device_id: str
    message_type: MessageType = MessageType.TELEMETRY
    payload: Dict[str, Any]
    sensor_readings: List[SensorReading] = Field(default_factory=list)
    timestamp: Optional[datetime] = None
    correlation_id: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)


class BatchMessageRequest(BaseModel):
    """Batch message ingestion request."""
    messages: List[MessageIngestionRequest]
    batch_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))


class QueryRequest(BaseModel):
    """Data query request."""
    device_ids: Optional[List[str]] = None
    message_types: Optional[List[MessageType]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = Field(default=1000, ge=1, le=10000)
    offset: int = Field(default=0, ge=0)
    aggregation: Optional[str] = None
    group_by: Optional[List[str]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    """Data query response."""
    query_id: str = Field(default_factory=lambda: str(uuid4()))
    total_count: int
    returned_count: int
    data: List[Dict[str, Any]]
    execution_time_ms: float
    next_offset: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    """Service health check response."""
    status: str = Field(default="healthy", pattern="^(healthy|degraded|unhealthy)$")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str
    uptime_seconds: int
    active_devices: int
    messages_per_second: float
    storage_usage_percent: float
    memory_usage_percent: float
    cpu_usage_percent: float
    components: Dict[str, str] = Field(default_factory=dict)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }