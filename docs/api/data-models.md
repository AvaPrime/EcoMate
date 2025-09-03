# Data Models

This document defines the data structures used throughout the EcoMate API, including request and response objects, validation rules, and field descriptions.

## Core Models

### System Entity

Represents a wastewater treatment system in the EcoMate platform.

```json
{
  "system_id": "string",
  "name": "string",
  "type": "string",
  "location": {
    "latitude": "number",
    "longitude": "number",
    "address": "string",
    "timezone": "string"
  },
  "capacity": {
    "design_flow": "number",
    "peak_flow": "number",
    "units": "string"
  },
  "components": [
    {
      "component_id": "string",
      "type": "string",
      "status": "string",
      "last_maintenance": "string (ISO 8601)"
    }
  ],
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "status": "string"
}
```

**Field Descriptions:**
- `system_id`: Unique identifier for the system (format: `sys_[alphanumeric]`)
- `name`: Human-readable system name
- `type`: System classification (`municipal`, `industrial`, `commercial`)
- `location.timezone`: IANA timezone identifier (e.g., `America/New_York`)
- `capacity.units`: Flow rate units (`mgd`, `gpm`, `m3/day`)
- `components[].type`: Component classification (`primary_clarifier`, `aeration_tank`, `disinfection`)
- `status`: Operational status (`active`, `maintenance`, `offline`, `decommissioned`)

### Telemetry Data

Represents sensor readings and calculated metrics from system operations.

```json
{
  "system_id": "string",
  "timestamp": "string (ISO 8601)",
  "metrics": {
    "flow_rate": "number",
    "ph": "number",
    "turbidity": "number",
    "dissolved_oxygen": "number",
    "temperature": "number",
    "conductivity": "number",
    "tss": "number",
    "bod": "number",
    "cod": "number",
    "nitrogen": "number",
    "phosphorus": "number"
  },
  "calculated_metrics": {
    "efficiency": "number",
    "energy_consumption": "number",
    "chemical_usage": "number",
    "sludge_production": "number"
  },
  "quality_flags": {
    "data_quality": "string",
    "sensor_status": "object",
    "calibration_due": "boolean"
  }
}
```

**Metric Units:**
- `flow_rate`: Gallons per minute (GPM)
- `ph`: pH units (0-14)
- `turbidity`: Nephelometric Turbidity Units (NTU)
- `dissolved_oxygen`: Milligrams per liter (mg/L)
- `temperature`: Degrees Celsius (°C)
- `conductivity`: Microsiemens per centimeter (µS/cm)
- `tss`: Total Suspended Solids (mg/L)
- `bod`: Biochemical Oxygen Demand (mg/L)
- `cod`: Chemical Oxygen Demand (mg/L)
- `nitrogen`: Total Nitrogen (mg/L)
- `phosphorus`: Total Phosphorus (mg/L)
- `efficiency`: Percentage (0-100)
- `energy_consumption`: Kilowatt-hours (kWh)
- `chemical_usage`: Gallons or pounds per day
- `sludge_production`: Pounds per day

### Alert Object

Represents system alerts and notifications.

```json
{
  "alert_id": "string",
  "system_id": "string",
  "type": "string",
  "severity": "string",
  "status": "string",
  "message": "string",
  "description": "string",
  "metric": "string",
  "current_value": "number",
  "threshold": "number",
  "created_at": "string (ISO 8601)",
  "updated_at": "string (ISO 8601)",
  "acknowledged_at": "string (ISO 8601)",
  "acknowledged_by": "string",
  "resolved_at": "string (ISO 8601)",
  "resolution_notes": "string",
  "escalation_level": "number",
  "notification_sent": "boolean"
}
```

**Enumerated Values:**
- `type`: `threshold`, `equipment_failure`, `maintenance_due`, `compliance_violation`
- `severity`: `low`, `medium`, `high`, `critical`
- `status`: `active`, `acknowledged`, `resolved`, `suppressed`

### User Profile

Represents user account information and permissions.

```json
{
  "user_id": "string",
  "username": "string",
  "email": "string",
  "first_name": "string",
  "last_name": "string",
  "role": "string",
  "permissions": ["string"],
  "systems_access": ["string"],
  "organization": {
    "org_id": "string",
    "name": "string",
    "type": "string"
  },
  "preferences": {
    "notifications": {
      "email_alerts": "boolean",
      "sms_alerts": "boolean",
      "push_notifications": "boolean",
      "alert_frequency": "string"
    },
    "dashboard": {
      "default_view": "string",
      "refresh_interval": "number",
      "timezone": "string"
    }
  },
  "created_at": "string (ISO 8601)",
  "last_login": "string (ISO 8601)",
  "status": "string"
}
```

**Role Types:**
- `admin`: Full system access and user management
- `operator`: System monitoring and control operations
- `technician`: Maintenance and troubleshooting access
- `viewer`: Read-only access to data and reports
- `compliance`: Regulatory reporting and audit access

**Permission Types:**
- `read_telemetry`: View system data and metrics
- `read_alerts`: View system alerts and notifications
- `acknowledge_alerts`: Acknowledge and manage alerts
- `update_config`: Modify system configuration
- `execute_commands`: Perform control operations
- `generate_reports`: Create and download reports
- `manage_users`: User account management
- `system_admin`: Full administrative access

## Request Models

### Configuration Update Request

```json
{
  "flow_rate_target": "number",
  "treatment_mode": "string",
  "alert_thresholds": {
    "ph_min": "number",
    "ph_max": "number",
    "turbidity_max": "number",
    "do_min": "number",
    "flow_rate_max": "number"
  },
  "operational_parameters": {
    "aeration_rate": "number",
    "chemical_dosing": {
      "chlorine": "number",
      "coagulant": "number",
      "polymer": "number"
    },
    "sludge_wasting_rate": "number"
  },
  "maintenance_schedule": {
    "next_inspection": "string (ISO 8601)",
    "calibration_interval": "number",
    "cleaning_frequency": "number"
  }
}
```

### Report Generation Request

```json
{
  "report_type": "string",
  "period": {
    "start": "string (ISO 8601)",
    "end": "string (ISO 8601)"
  },
  "format": "string",
  "include_charts": "boolean",
  "include_raw_data": "boolean",
  "metrics": ["string"],
  "aggregation": "string",
  "filters": {
    "components": ["string"],
    "severity_levels": ["string"],
    "alert_types": ["string"]
  },
  "delivery": {
    "email_recipients": ["string"],
    "schedule": "string"
  }
}
```

**Report Types:**
- `compliance`: Regulatory compliance report
- `performance`: System performance analysis
- `maintenance`: Maintenance and operational summary
- `efficiency`: Energy and chemical efficiency analysis
- `alerts`: Alert and incident summary
- `custom`: User-defined report parameters

### Command Execution Request

```json
{
  "command": "string",
  "parameters": "object",
  "authorization_code": "string",
  "scheduled_execution": "string (ISO 8601)",
  "confirmation_required": "boolean",
  "timeout_seconds": "number"
}
```

**Available Commands:**
- `adjust_flow_rate`: Modify system flow rate
- `start_component`: Activate system component
- `stop_component`: Deactivate system component
- `calibrate_sensor`: Initiate sensor calibration
- `emergency_shutdown`: Emergency system shutdown
- `maintenance_mode`: Enter/exit maintenance mode
- `reset_alarms`: Clear acknowledged alarms
- `update_setpoints`: Modify operational setpoints

## Response Models

### API Response Wrapper

All API responses follow this standard structure:

```json
{
  "success": "boolean",
  "data": "object|array",
  "message": "string",
  "timestamp": "string (ISO 8601)",
  "request_id": "string",
  "pagination": {
    "page": "number",
    "per_page": "number",
    "total": "number",
    "total_pages": "number"
  },
  "metadata": {
    "api_version": "string",
    "response_time_ms": "number",
    "rate_limit": {
      "limit": "number",
      "remaining": "number",
      "reset": "number"
    }
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": {
    "code": "string",
    "message": "string",
    "details": "object",
    "field_errors": [
      {
        "field": "string",
        "message": "string",
        "code": "string"
      }
    ]
  },
  "timestamp": "string (ISO 8601)",
  "request_id": "string"
}
```

## Validation Rules

### Data Type Constraints

- **Timestamps**: Must be in ISO 8601 format with UTC timezone
- **Numbers**: Must be finite, non-NaN values
- **Strings**: Maximum length of 255 characters unless specified
- **Arrays**: Maximum of 100 items unless specified
- **Objects**: Maximum nesting depth of 5 levels

### Business Logic Constraints

- **pH values**: Must be between 0 and 14
- **Flow rates**: Must be positive numbers
- **Percentages**: Must be between 0 and 100
- **Temperatures**: Must be between -50°C and 100°C
- **System IDs**: Must match pattern `sys_[a-zA-Z0-9]{5,10}`
- **User IDs**: Must match pattern `usr_[a-zA-Z0-9]{3,8}`
- **Alert IDs**: Must match pattern `alt_[a-zA-Z0-9]{3,8}`

### Required Fields

**System Entity:**
- `system_id`, `name`, `type`, `status`

**Telemetry Data:**
- `system_id`, `timestamp`, at least one metric in `metrics` object

**Alert Object:**
- `alert_id`, `system_id`, `type`, `severity`, `status`, `message`, `created_at`

**User Profile:**
- `user_id`, `username`, `email`, `role`, `status`

## Data Relationships

### Entity Relationships

- **System** → **Telemetry Data**: One-to-many
- **System** → **Alerts**: One-to-many
- **User** → **Systems**: Many-to-many (through access permissions)
- **Organization** → **Users**: One-to-many
- **Organization** → **Systems**: One-to-many

### Reference Integrity

- All `system_id` references must correspond to existing systems
- All `user_id` references must correspond to active users
- Alert acknowledgments must reference valid user accounts
- Command executions must reference authorized users

## Versioning and Compatibility

### API Versioning

- Current version: `v1`
- Version specified in URL path: `/v1/endpoint`
- Backward compatibility maintained for one major version
- Deprecation notices provided 6 months before removal

### Schema Evolution

- New optional fields may be added without version increment
- Required fields additions require major version increment
- Field removals require major version increment
- Data type changes require major version increment

### Migration Support

- Automatic data migration for minor version updates
- Migration tools provided for major version updates
- Legacy data format support during transition periods