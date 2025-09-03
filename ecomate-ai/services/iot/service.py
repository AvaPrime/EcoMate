"""
IoT Ingestion Pipeline - Core Service

Core business logic for IoT device management, data processing, and analytics.
Provides orchestration for the entire IoT ecosystem.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from .client import IoTClient
from .models import (
    Alert, AlertRule, AlertSeverity, Device, DeviceState, DeviceType,
    IoTMessage, MessageType, QueryRequest,
    QueryResponse, SensorReading
)


logger = logging.getLogger(__name__)


class IoTService:
    """
    Core IoT service providing device management, data processing, and analytics.
    
    Orchestrates the entire IoT ecosystem including device lifecycle management,
    real-time data processing, alert generation, and compliance monitoring.
    """
    
    def __init__(self, client: IoTClient):
        self.client = client
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.processing_pipelines: Dict[str, Any] = {}
        self.message_buffer: List[IoTMessage] = []
        self.analytics_cache: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            "messages_processed": 0,
            "alerts_generated": 0,
            "devices_registered": 0,
            "uptime_start": datetime.utcnow()
        }
        
        # Setup message handlers
        self._setup_message_handlers()
        
        logger.info("IoT service initialized")
    
    async def start(self) -> None:
        """Start the IoT service."""
        await self.client.connect_all()
        
        # Start background tasks
        asyncio.create_task(self._process_message_buffer())
        asyncio.create_task(self._monitor_device_health())
        asyncio.create_task(self._cleanup_expired_alerts())
        
        logger.info("IoT service started")
    
    async def stop(self) -> None:
        """Stop the IoT service."""
        await self.client.disconnect_all()
        logger.info("IoT service stopped")
    
    # Device Management
    async def register_device(self, device: Device) -> bool:
        """Register a new IoT device."""
        try:
            success = await self.client.register_device(device)
            if success:
                self.stats["devices_registered"] += 1
                
                # Setup device-specific alert rules
                await self._setup_default_alert_rules(device)
                
                logger.info(f"Device {device.device_id} registered successfully")
            return success
            
        except Exception as e:
            logger.error(f"Failed to register device {device.device_id}: {e}")
            return False
    
    async def unregister_device(self, device_id: str) -> bool:
        """Unregister an IoT device."""
        try:
            success = await self.client.unregister_device(device_id)
            if success:
                # Clean up device-specific data
                await self._cleanup_device_data(device_id)
                logger.info(f"Device {device_id} unregistered successfully")
            return success
            
        except Exception as e:
            logger.error(f"Failed to unregister device {device_id}: {e}")
            return False
    
    async def update_device_state(self, device_id: str, state: DeviceState) -> bool:
        """Update device operational state."""
        try:
            success = await self.client.update_device_state(device_id, state)
            if success:
                # Generate state change alert if needed
                if state in [DeviceState.OFFLINE, DeviceState.ERROR]:
                    await self._generate_device_state_alert(device_id, state)
                
                logger.info(f"Device {device_id} state updated to {state}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to update device {device_id} state: {e}")
            return False
    
    async def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive device status."""
        status = self.client.get_device_status(device_id)
        if status:
            # Add service-specific information
            status["active_alerts"] = len([a for a in self.active_alerts.values() if a.device_id == device_id])
            status["alert_rules"] = len([r for r in self.alert_rules.values() if r.device_id == device_id])
        return status
    
    # Message Processing
    async def ingest_message(self, message: IoTMessage) -> bool:
        """Ingest a message from an IoT device."""
        try:
            # Validate message
            if not await self._validate_message(message):
                logger.warning(f"Invalid message from device {message.device_id}")
                return False
            
            # Add to processing buffer
            self.message_buffer.append(message)
            self.stats["messages_processed"] += 1
            
            # Process high-priority messages immediately
            if message.priority >= 8:
                await self._process_message(message)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to ingest message: {e}")
            return False
    
    async def ingest_batch_messages(self, messages: List[IoTMessage]) -> Dict[str, bool]:
        """Ingest multiple messages in batch."""
        results = {}
        
        for message in messages:
            results[message.message_id] = await self.ingest_message(message)
        
        return results
    
    async def query_data(
        self,
        request: QueryRequest
    ) -> QueryResponse:
        """Query historical IoT data."""
        try:
            start_time = datetime.utcnow()
            
            # Build query filters
            filters = self._build_query_filters(request)
            
            # Execute query (placeholder - would integrate with time-series DB)
            data = await self._execute_query(filters, request.limit, request.offset)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return QueryResponse(
                total_count=len(data),
                returned_count=min(len(data), request.limit),
                data=data[:request.limit],
                execution_time_ms=execution_time,
                next_offset=request.offset + request.limit if len(data) > request.limit else None
            )
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return QueryResponse(
                total_count=0,
                returned_count=0,
                data=[],
                execution_time_ms=0
            )
    
    # Alert Management
    async def create_alert_rule(self, rule: AlertRule) -> bool:
        """Create a new alert rule."""
        try:
            self.alert_rules[rule.rule_id] = rule
            logger.info(f"Alert rule {rule.name} created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            return False
    
    async def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing alert rule."""
        try:
            if rule_id in self.alert_rules:
                rule = self.alert_rules[rule_id]
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                rule.updated_at = datetime.utcnow()
                logger.info(f"Alert rule {rule_id} updated")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to update alert rule {rule_id}: {e}")
            return False
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                logger.info(f"Alert rule {rule_id} deleted")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete alert rule {rule_id}: {e}")
            return False
    
    async def get_active_alerts(
        self,
        device_id: Optional[str] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """Get active alerts with optional filtering."""
        alerts = list(self.active_alerts.values())
        
        if device_id:
            alerts = [a for a in alerts if a.device_id == device_id]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        return alerts
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = "acknowledged"
                alert.acknowledged_at = datetime.utcnow()
                alert.acknowledged_by = acknowledged_by
                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Resolve an active alert."""
        try:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = "resolved"
                alert.resolved_at = datetime.utcnow()
                alert.resolved_by = resolved_by
                
                # Remove from active alerts
                del self.active_alerts[alert_id]
                
                logger.info(f"Alert {alert_id} resolved by {resolved_by}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False
    
    # Analytics and Reporting
    async def get_device_analytics(
        self,
        device_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for a specific device."""
        try:
            # Default time range to last 24 hours
            if not start_time:
                start_time = datetime.utcnow() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.utcnow()
            
            # Calculate analytics (placeholder implementation)
            analytics = {
                "device_id": device_id,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "message_count": 0,
                "average_message_rate": 0.0,
                "sensor_readings": {},
                "alerts_triggered": 0,
                "uptime_percentage": 0.0,
                "data_quality_score": 0.0
            }
            
            # Get device status
            device_status = await self.get_device_status(device_id)
            if device_status:
                analytics.update({
                    "current_state": device_status["state"],
                    "last_seen": device_status["last_seen"],
                    "connection_stats": device_status.get("statistics", {})
                })
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics for device {device_id}: {e}")
            return {}
    
    async def get_system_analytics(self) -> Dict[str, Any]:
        """Get system-wide analytics."""
        try:
            uptime = datetime.utcnow() - self.stats["uptime_start"]
            
            analytics = {
                "system_status": "operational",
                "uptime_seconds": int(uptime.total_seconds()),
                "total_devices": len(self.client.device_registry),
                "connected_devices": len(self.client._connected_devices),
                "messages_processed": self.stats["messages_processed"],
                "alerts_generated": self.stats["alerts_generated"],
                "active_alerts": len(self.active_alerts),
                "alert_rules": len(self.alert_rules),
                "message_rate": self._calculate_message_rate(),
                "device_types": self._get_device_type_distribution(),
                "protocol_distribution": self._get_protocol_distribution(),
                "health_score": await self._calculate_system_health_score()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get system analytics: {e}")
            return {}
    
    # Private Helper Methods
    def _setup_message_handlers(self) -> None:
        """Setup message handlers for different message types."""
        self.client.add_message_handler(MessageType.TELEMETRY, self._handle_telemetry_message)
        self.client.add_message_handler(MessageType.ALERT, self._handle_alert_message)
        self.client.add_message_handler(MessageType.HEARTBEAT, self._handle_heartbeat_message)
        self.client.add_message_handler(MessageType.DIAGNOSTIC, self._handle_diagnostic_message)
    
    async def _handle_telemetry_message(self, message: IoTMessage) -> None:
        """Handle telemetry messages."""
        try:
            # Process sensor readings
            for reading in message.sensor_readings:
                await self._process_sensor_reading(message.device_id, reading)
            
            # Check alert rules
            await self._evaluate_alert_rules(message)
            
        except Exception as e:
            logger.error(f"Failed to handle telemetry message: {e}")
    
    async def _handle_alert_message(self, message: IoTMessage) -> None:
        """Handle alert messages from devices."""
        try:
            # Create alert from device message
            alert = Alert(
                rule_id="device-generated",
                device_id=message.device_id,
                title=message.payload.get("title", "Device Alert"),
                description=message.payload.get("description"),
                severity=AlertSeverity(message.payload.get("severity", "medium"))
            )
            
            self.active_alerts[alert.alert_id] = alert
            self.stats["alerts_generated"] += 1
            
            logger.info(f"Device alert created: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to handle alert message: {e}")
    
    async def _handle_heartbeat_message(self, message: IoTMessage) -> None:
        """Handle heartbeat messages."""
        try:
            # Update device last seen
            if message.device_id in self.client.device_registry:
                device = self.client.device_registry[message.device_id]
                device.last_seen = datetime.utcnow()
                
                # Update state to online if not already
                if device.state != DeviceState.ONLINE:
                    await self.update_device_state(message.device_id, DeviceState.ONLINE)
            
        except Exception as e:
            logger.error(f"Failed to handle heartbeat message: {e}")
    
    async def _handle_diagnostic_message(self, message: IoTMessage) -> None:
        """Handle diagnostic messages."""
        try:
            # Process diagnostic data
            diagnostic_data = message.payload
            
            # Check for error conditions
            if diagnostic_data.get("error_count", 0) > 0:
                await self._generate_diagnostic_alert(message.device_id, diagnostic_data)
            
        except Exception as e:
            logger.error(f"Failed to handle diagnostic message: {e}")
    
    async def _process_message_buffer(self) -> None:
        """Background task to process message buffer."""
        while True:
            try:
                if self.message_buffer:
                    # Process messages in batches
                    batch = self.message_buffer[:100]
                    self.message_buffer = self.message_buffer[100:]
                    
                    for message in batch:
                        await self._process_message(message)
                
                await asyncio.sleep(1)  # Process every second
                
            except Exception as e:
                logger.error(f"Message buffer processing error: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _process_message(self, message: IoTMessage) -> None:
        """Process a single message."""
        try:
            # Apply transformations
            transformed_message = await self._apply_transformations(message)
            
            # Store in time-series database (placeholder)
            await self._store_message(transformed_message)
            
            # Update analytics cache
            self._update_analytics_cache(transformed_message)
            
        except Exception as e:
            logger.error(f"Failed to process message {message.message_id}: {e}")
    
    async def _validate_message(self, message: IoTMessage) -> bool:
        """Validate incoming message."""
        try:
            # Check if device is registered
            if message.device_id not in self.client.device_registry:
                return False
            
            # Check message structure
            if not message.payload:
                return False
            
            # Check timestamp (not too old or in future)
            now = datetime.utcnow()
            if message.timestamp > now + timedelta(minutes=5):
                return False
            if message.timestamp < now - timedelta(hours=24):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Message validation error: {e}")
            return False
    
    async def _setup_default_alert_rules(self, device: Device) -> None:
        """Setup default alert rules for a device."""
        try:
            # Offline alert rule
            offline_rule = AlertRule(
                name=f"Device Offline - {device.name}",
                description=f"Alert when {device.name} goes offline",
                device_id=device.device_id,
                condition="device_state == 'offline'",
                severity=AlertSeverity.HIGH,
                cooldown_minutes=15
            )
            
            await self.create_alert_rule(offline_rule)
            
            # Add device-type specific rules
            if device.device_type == DeviceType.SENSOR:
                # Data quality rule
                quality_rule = AlertRule(
                    name=f"Data Quality - {device.name}",
                    description=f"Alert when {device.name} data quality is low",
                    device_id=device.device_id,
                    condition="data_quality < 0.8",
                    severity=AlertSeverity.MEDIUM,
                    cooldown_minutes=30
                )
                await self.create_alert_rule(quality_rule)
            
        except Exception as e:
            logger.error(f"Failed to setup default alert rules for {device.device_id}: {e}")
    
    async def _cleanup_device_data(self, device_id: str) -> None:
        """Clean up device-specific data."""
        try:
            # Remove device-specific alert rules
            rules_to_remove = [r.rule_id for r in self.alert_rules.values() if r.device_id == device_id]
            for rule_id in rules_to_remove:
                await self.delete_alert_rule(rule_id)
            
            # Remove active alerts for device
            alerts_to_remove = [a.alert_id for a in self.active_alerts.values() if a.device_id == device_id]
            for alert_id in alerts_to_remove:
                del self.active_alerts[alert_id]
            
        except Exception as e:
            logger.error(f"Failed to cleanup data for device {device_id}: {e}")
    
    async def _evaluate_alert_rules(self, message: IoTMessage) -> None:
        """Evaluate alert rules against incoming message."""
        try:
            device_rules = [r for r in self.alert_rules.values() 
                          if r.device_id == message.device_id and r.enabled]
            
            for rule in device_rules:
                if await self._evaluate_rule_condition(rule, message):
                    await self._generate_alert(rule, message)
            
        except Exception as e:
            logger.error(f"Failed to evaluate alert rules: {e}")
    
    async def _evaluate_rule_condition(self, rule: AlertRule, message: IoTMessage) -> bool:
        """Evaluate if a rule condition is met."""
        try:
            # Simple condition evaluation (would be more sophisticated in production)
            condition = rule.condition.lower()
            
            if "temperature >" in condition:
                temp_threshold = float(condition.split(">")[1].strip())
                for reading in message.sensor_readings:
                    if reading.sensor_type.lower() == "temperature" and float(reading.value) > temp_threshold:
                        return True
            
            # Add more condition types as needed
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to evaluate rule condition: {e}")
            return False
    
    async def _generate_alert(self, rule: AlertRule, message: IoTMessage) -> None:
        """Generate an alert based on a rule."""
        try:
            # Check cooldown period
            if await self._is_rule_in_cooldown(rule):
                return
            
            alert = Alert(
                rule_id=rule.rule_id,
                device_id=message.device_id,
                title=rule.name,
                description=rule.description,
                severity=rule.severity,
                context={
                    "message_id": message.message_id,
                    "trigger_time": message.timestamp.isoformat(),
                    "payload": message.payload
                }
            )
            
            self.active_alerts[alert.alert_id] = alert
            self.stats["alerts_generated"] += 1
            
            logger.info(f"Alert generated: {alert.title} for device {message.device_id}")
            
        except Exception as e:
            logger.error(f"Failed to generate alert: {e}")
    
    async def _is_rule_in_cooldown(self, rule: AlertRule) -> bool:
        """Check if rule is in cooldown period."""
        # Implementation would check last alert time for this rule
        return False
    
    def _calculate_message_rate(self) -> float:
        """Calculate current message processing rate."""
        uptime = datetime.utcnow() - self.stats["uptime_start"]
        if uptime.total_seconds() > 0:
            return self.stats["messages_processed"] / uptime.total_seconds()
        return 0.0
    
    def _get_device_type_distribution(self) -> Dict[str, int]:
        """Get distribution of device types."""
        distribution = {}
        for device in self.client.device_registry.values():
            device_type = device.device_type.value
            distribution[device_type] = distribution.get(device_type, 0) + 1
        return distribution
    
    def _get_protocol_distribution(self) -> Dict[str, int]:
        """Get distribution of protocols."""
        distribution = {}
        for device in self.client.device_registry.values():
            protocol = device.protocol.value
            distribution[protocol] = distribution.get(protocol, 0) + 1
        return distribution
    
    async def _calculate_system_health_score(self) -> float:
        """Calculate overall system health score."""
        try:
            total_devices = len(self.client.device_registry)
            if total_devices == 0:
                return 1.0
            
            connected_devices = len(self.client._connected_devices)
            connection_ratio = connected_devices / total_devices
            
            # Factor in alert levels
            critical_alerts = len([a for a in self.active_alerts.values() if a.severity == AlertSeverity.CRITICAL])
            alert_penalty = min(critical_alerts * 0.1, 0.5)
            
            health_score = max(0.0, connection_ratio - alert_penalty)
            return min(1.0, health_score)
            
        except Exception as e:
            logger.error(f"Failed to calculate health score: {e}")
            return 0.5
    
    # Placeholder methods for database integration
    async def _apply_transformations(self, message: IoTMessage) -> IoTMessage:
        """Apply data transformations to message."""
        # Placeholder for transformation logic
        return message
    
    async def _store_message(self, message: IoTMessage) -> None:
        """Store message in time-series database."""
        # Placeholder for database storage
        pass
    
    def _update_analytics_cache(self, message: IoTMessage) -> None:
        """Update analytics cache with message data."""
        # Placeholder for analytics cache update
        pass
    
    def _build_query_filters(self, request: QueryRequest) -> Dict[str, Any]:
        """Build query filters from request."""
        filters = {}
        
        if request.device_ids:
            filters["device_id"] = {"$in": request.device_ids}
        
        if request.message_types:
            filters["message_type"] = {"$in": [mt.value for mt in request.message_types]}
        
        if request.start_time:
            filters["timestamp"] = {"$gte": request.start_time}
        
        if request.end_time:
            if "timestamp" not in filters:
                filters["timestamp"] = {}
            filters["timestamp"]["$lte"] = request.end_time
        
        filters.update(request.filters)
        
        return filters
    
    async def _execute_query(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Dict[str, Any]]:
        """Execute query against time-series database."""
        # Placeholder for database query execution
        return []
    
    async def _monitor_device_health(self) -> None:
        """Background task to monitor device health."""
        while True:
            try:
                now = datetime.utcnow()
                
                for device_id, device in self.client.device_registry.items():
                    # Check if device is offline
                    if device.last_seen:
                        offline_duration = now - device.last_seen
                        max_offline = timedelta(seconds=device.config.max_offline_time)
                        
                        if offline_duration > max_offline and device.state == DeviceState.ONLINE:
                            await self.update_device_state(device_id, DeviceState.OFFLINE)
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Device health monitoring error: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _cleanup_expired_alerts(self) -> None:
        """Background task to clean up old resolved alerts."""
        while True:
            try:
                cutoff_time = datetime.utcnow() - timedelta(days=7)
                
                # Remove old resolved alerts (would be moved to archive in production)
                expired_alerts = [
                    alert_id for alert_id, alert in self.active_alerts.items()
                    if alert.status == "resolved" and alert.resolved_at and alert.resolved_at < cutoff_time
                ]
                
                for alert_id in expired_alerts:
                    del self.active_alerts[alert_id]
                
                if expired_alerts:
                    logger.info(f"Cleaned up {len(expired_alerts)} expired alerts")
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Alert cleanup error: {e}")
                await asyncio.sleep(3600)
    
    async def _generate_device_state_alert(self, device_id: str, state: DeviceState) -> None:
        """Generate alert for device state changes."""
        try:
            device = self.client.device_registry.get(device_id)
            if not device:
                return
            
            severity = AlertSeverity.HIGH if state == DeviceState.ERROR else AlertSeverity.MEDIUM
            
            alert = Alert(
                rule_id="system-generated",
                device_id=device_id,
                title=f"Device State Change: {device.name}",
                description=f"Device {device.name} changed state to {state.value}",
                severity=severity,
                context={
                    "previous_state": device.state.value,
                    "new_state": state.value,
                    "device_type": device.device_type.value
                }
            )
            
            self.active_alerts[alert.alert_id] = alert
            self.stats["alerts_generated"] += 1
            
        except Exception as e:
            logger.error(f"Failed to generate device state alert: {e}")
    
    async def _generate_diagnostic_alert(self, device_id: str, diagnostic_data: Dict[str, Any]) -> None:
        """Generate alert based on diagnostic data."""
        try:
            device = self.client.device_registry.get(device_id)
            if not device:
                return
            
            error_count = diagnostic_data.get("error_count", 0)
            severity = AlertSeverity.CRITICAL if error_count > 10 else AlertSeverity.HIGH
            
            alert = Alert(
                rule_id="diagnostic-generated",
                device_id=device_id,
                title=f"Diagnostic Alert: {device.name}",
                description=f"Device {device.name} reported {error_count} errors",
                severity=severity,
                context=diagnostic_data
            )
            
            self.active_alerts[alert.alert_id] = alert
            self.stats["alerts_generated"] += 1
            
        except Exception as e:
            logger.error(f"Failed to generate diagnostic alert: {e}")
    
    async def _process_sensor_reading(self, device_id: str, reading: SensorReading) -> None:
        """Process individual sensor reading."""
        try:
            # Validate reading
            if reading.quality is not None and reading.quality < 0.5:
                logger.warning(f"Low quality reading from {device_id}: {reading.sensor_id}")
            
            # Store reading (placeholder)
            # In production, this would store to time-series database
            
        except Exception as e:
            logger.error(f"Failed to process sensor reading: {e}")