# API Endpoints

This document provides detailed information about all available EcoMate API endpoints, including request/response formats, parameters, and examples.

## Base URL

```
https://api.ecomate.com/v1
```

## System Management

### Get System Status

**Endpoint:** `GET /systems/{system_id}/status`

**Description:** Retrieve current operational status of a wastewater treatment system.

**Parameters:**
- `system_id` (path, required): Unique identifier for the system
- `include_metrics` (query, optional): Include performance metrics (default: false)

**Response:**
```json
{
  "system_id": "sys_12345",
  "status": "operational",
  "last_updated": "2024-01-15T10:30:00Z",
  "components": {
    "primary_treatment": "active",
    "secondary_treatment": "active",
    "disinfection": "active"
  },
  "metrics": {
    "flow_rate": 1250.5,
    "efficiency": 94.2,
    "energy_consumption": 45.8
  }
}
```

### Update System Configuration

**Endpoint:** `PUT /systems/{system_id}/config`

**Description:** Update system configuration parameters.

**Request Body:**
```json
{
  "flow_rate_target": 1200,
  "treatment_mode": "standard",
  "alert_thresholds": {
    "ph_min": 6.5,
    "ph_max": 8.5,
    "turbidity_max": 10
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

## Data & Analytics

### Get Telemetry Data

**Endpoint:** `GET /systems/{system_id}/telemetry`

**Description:** Retrieve historical telemetry data for analysis.

**Parameters:**
- `system_id` (path, required): System identifier
- `start_date` (query, required): Start date (ISO 8601 format)
- `end_date` (query, required): End date (ISO 8601 format)
- `metrics` (query, optional): Comma-separated list of metrics
- `interval` (query, optional): Data aggregation interval (1m, 5m, 1h, 1d)

**Example Request:**
```
GET /systems/sys_12345/telemetry?start_date=2024-01-01T00:00:00Z&end_date=2024-01-02T00:00:00Z&metrics=ph,turbidity&interval=1h
```

**Response:**
```json
{
  "system_id": "sys_12345",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-02T00:00:00Z"
  },
  "interval": "1h",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "ph": 7.2,
      "turbidity": 5.8
    },
    {
      "timestamp": "2024-01-01T01:00:00Z",
      "ph": 7.1,
      "turbidity": 6.2
    }
  ]
}
```

### Generate Performance Report

**Endpoint:** `POST /systems/{system_id}/reports`

**Description:** Generate comprehensive performance reports.

**Request Body:**
```json
{
  "report_type": "compliance",
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "format": "pdf",
  "include_charts": true
}
```

**Response:**
```json
{
  "report_id": "rpt_67890",
  "status": "generating",
  "estimated_completion": "2024-01-15T10:40:00Z",
  "download_url": null
}
```

## Alerts & Notifications

### Get Active Alerts

**Endpoint:** `GET /systems/{system_id}/alerts`

**Description:** Retrieve current active alerts for a system.

**Parameters:**
- `system_id` (path, required): System identifier
- `severity` (query, optional): Filter by severity (low, medium, high, critical)
- `status` (query, optional): Filter by status (active, acknowledged, resolved)

**Response:**
```json
{
  "system_id": "sys_12345",
  "alerts": [
    {
      "alert_id": "alt_001",
      "severity": "medium",
      "status": "active",
      "message": "pH level approaching upper threshold",
      "created_at": "2024-01-15T09:45:00Z",
      "metric": "ph",
      "current_value": 8.3,
      "threshold": 8.5
    }
  ]
}
```

### Acknowledge Alert

**Endpoint:** `POST /alerts/{alert_id}/acknowledge`

**Description:** Acknowledge an active alert.

**Request Body:**
```json
{
  "acknowledged_by": "operator_123",
  "notes": "Investigating pH spike, adjusting chemical dosing"
}
```

## User & Access Management

### Get User Profile

**Endpoint:** `GET /users/me`

**Description:** Retrieve current user profile information.

**Response:**
```json
{
  "user_id": "usr_456",
  "username": "john.operator",
  "email": "john@facility.com",
  "role": "operator",
  "permissions": [
    "read_telemetry",
    "acknowledge_alerts",
    "update_config"
  ],
  "systems_access": ["sys_12345", "sys_67890"]
}
```

### Update User Preferences

**Endpoint:** `PUT /users/me/preferences`

**Description:** Update user notification and display preferences.

**Request Body:**
```json
{
  "notifications": {
    "email_alerts": true,
    "sms_alerts": false,
    "alert_frequency": "immediate"
  },
  "dashboard": {
    "default_view": "overview",
    "refresh_interval": 30
  }
}
```

## Control Operations

### Execute System Command

**Endpoint:** `POST /systems/{system_id}/commands`

**Description:** Execute operational commands on system components.

**Request Body:**
```json
{
  "command": "adjust_flow_rate",
  "parameters": {
    "target_rate": 1100,
    "ramp_duration": 300
  },
  "authorization_code": "AUTH123456"
}
```

**Response:**
```json
{
  "command_id": "cmd_789",
  "status": "executing",
  "estimated_completion": "2024-01-15T10:45:00Z",
  "progress": 0
}
```

### Get Command Status

**Endpoint:** `GET /commands/{command_id}`

**Description:** Check the status of a previously executed command.

**Response:**
```json
{
  "command_id": "cmd_789",
  "status": "completed",
  "progress": 100,
  "result": {
    "success": true,
    "final_flow_rate": 1100,
    "completion_time": "2024-01-15T10:43:22Z"
  }
}
```

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "error": "bad_request",
  "message": "Invalid parameter value",
  "details": {
    "field": "start_date",
    "issue": "Date format must be ISO 8601"
  }
}
```

### 401 Unauthorized
```json
{
  "error": "unauthorized",
  "message": "Invalid or expired authentication token"
}
```

### 403 Forbidden
```json
{
  "error": "forbidden",
  "message": "Insufficient permissions for this operation"
}
```

### 404 Not Found
```json
{
  "error": "not_found",
  "message": "System not found",
  "resource_id": "sys_99999"
}
```

### 429 Too Many Requests
```json
{
  "error": "rate_limit_exceeded",
  "message": "API rate limit exceeded",
  "retry_after": 60
}
```

### 500 Internal Server Error
```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred",
  "request_id": "req_abc123"
}
```

## Rate Limits

- **Standard endpoints**: 1000 requests per hour
- **Telemetry data**: 100 requests per hour
- **Control operations**: 50 requests per hour
- **Report generation**: 10 requests per hour

Rate limit headers are included in all responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1642248000
```