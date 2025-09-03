"""
IoT Device Manager

Manages IoT device lifecycle, authentication, configuration, and monitoring.
Provides centralized device management with security and compliance features.
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .models import (
    Device, DeviceConfig, DeviceCredentials, DeviceLocation, DeviceMetrics,
    DeviceState, DeviceType, Protocol
)


logger = logging.getLogger(__name__)


class DeviceManager:
    """
    Comprehensive device management system for IoT devices.
    
    Handles device registration, authentication, configuration management,
    monitoring, and lifecycle operations with security and compliance features.
    """
    
    def __init__(self):
        self.devices: Dict[str, Device] = {}
        self.device_credentials: Dict[str, DeviceCredentials] = {}
        self.device_sessions: Dict[str, Dict[str, Any]] = {}
        self.device_metrics: Dict[str, DeviceMetrics] = {}
        
        # Security and monitoring
        self.failed_auth_attempts: Dict[str, List[datetime]] = {}
        self.blocked_devices: Set[str] = set()
        self.device_groups: Dict[str, Set[str]] = {}
        
        # Configuration templates
        self.config_templates: Dict[DeviceType, DeviceConfig] = self._create_default_templates()
        
        # Statistics
        self.stats = {
            "total_devices": 0,
            "active_devices": 0,
            "failed_authentications": 0,
            "successful_authentications": 0,
            "device_registrations": 0,
            "device_deregistrations": 0
        }
        
        logger.info("Device manager initialized")
    
    # Device Registration and Management
    async def register_device(
        self,
        device_id: str,
        device_type: DeviceType,
        name: str,
        protocol: Protocol,
        location: Optional[DeviceLocation] = None,
        config: Optional[DeviceConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, Optional[Device]]:
        """
        Register a new IoT device.
        
        Args:
            device_id: Unique device identifier
            device_type: Type of device
            name: Human-readable device name
            protocol: Communication protocol
            location: Device location information
            config: Device configuration (uses template if not provided)
            metadata: Additional device metadata
        
        Returns:
            Tuple of (success, device) where device is None if registration failed
        """
        try:
            # Check if device already exists
            if device_id in self.devices:
                logger.warning(f"Device {device_id} already registered")
                return False, None
            
            # Validate device ID format
            if not self._validate_device_id(device_id):
                logger.error(f"Invalid device ID format: {device_id}")
                return False, None
            
            # Use template config if not provided
            if not config:
                config = self.config_templates.get(device_type, DeviceConfig())
            
            # Generate device credentials
            credentials = await self._generate_device_credentials(device_id, device_type)
            
            # Create device
            device = Device(
                device_id=device_id,
                device_type=device_type,
                name=name,
                protocol=protocol,
                state=DeviceState.REGISTERED,
                location=location,
                config=config,
                metadata=metadata or {},
                created_at=datetime.utcnow(),
                last_seen=None
            )
            
            # Store device and credentials
            self.devices[device_id] = device
            self.device_credentials[device_id] = credentials
            
            # Initialize metrics
            self.device_metrics[device_id] = DeviceMetrics(
                device_id=device_id,
                messages_sent=0,
                messages_received=0,
                bytes_sent=0,
                bytes_received=0,
                connection_count=0,
                last_connection=None,
                uptime_seconds=0,
                error_count=0,
                last_error=None
            )
            
            # Update statistics
            self.stats["total_devices"] += 1
            self.stats["device_registrations"] += 1
            
            logger.info(f"Device {device_id} ({name}) registered successfully")
            return True, device
            
        except Exception as e:
            logger.error(f"Failed to register device {device_id}: {e}")
            return False, None
    
    async def unregister_device(self, device_id: str) -> bool:
        """
        Unregister an IoT device.
        
        Args:
            device_id: Device identifier to unregister
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id not in self.devices:
                logger.warning(f"Device {device_id} not found for unregistration")
                return False
            
            # Remove device from all groups
            for group_name, group_devices in self.device_groups.items():
                group_devices.discard(device_id)
            
            # Clean up device data
            del self.devices[device_id]
            del self.device_credentials[device_id]
            del self.device_metrics[device_id]
            
            # Clean up sessions and security data
            self.device_sessions.pop(device_id, None)
            self.failed_auth_attempts.pop(device_id, None)
            self.blocked_devices.discard(device_id)
            
            # Update statistics
            self.stats["total_devices"] -= 1
            self.stats["device_deregistrations"] += 1
            
            logger.info(f"Device {device_id} unregistered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister device {device_id}: {e}")
            return False
    
    async def update_device(
        self,
        device_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update device information.
        
        Args:
            device_id: Device identifier
            updates: Dictionary of fields to update
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found for update")
                return False
            
            device = self.devices[device_id]
            
            # Update allowed fields
            allowed_fields = {
                'name', 'location', 'config', 'metadata', 'state'
            }
            
            for field, value in updates.items():
                if field in allowed_fields and hasattr(device, field):
                    setattr(device, field, value)
            
            device.updated_at = datetime.utcnow()
            
            logger.info(f"Device {device_id} updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update device {device_id}: {e}")
            return False
    
    # Device Authentication and Security
    async def authenticate_device(
        self,
        device_id: str,
        credentials: Dict[str, str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a device.
        
        Args:
            device_id: Device identifier
            credentials: Authentication credentials
        
        Returns:
            Tuple of (success, session_token)
        """
        try:
            # Check if device is blocked
            if device_id in self.blocked_devices:
                logger.warning(f"Authentication attempt from blocked device: {device_id}")
                return False, None
            
            # Check if device exists
            if device_id not in self.devices:
                logger.warning(f"Authentication attempt from unknown device: {device_id}")
                await self._record_failed_auth(device_id)
                return False, None
            
            # Get stored credentials
            stored_creds = self.device_credentials.get(device_id)
            if not stored_creds:
                logger.error(f"No credentials found for device: {device_id}")
                return False, None
            
            # Validate credentials
            if not await self._validate_credentials(stored_creds, credentials):
                logger.warning(f"Invalid credentials for device: {device_id}")
                await self._record_failed_auth(device_id)
                return False, None
            
            # Generate session token
            session_token = await self._generate_session_token(device_id)
            
            # Create session
            self.device_sessions[device_id] = {
                'token': session_token,
                'created_at': datetime.utcnow(),
                'last_activity': datetime.utcnow(),
                'ip_address': credentials.get('ip_address'),
                'user_agent': credentials.get('user_agent')
            }
            
            # Update device state and metrics
            device = self.devices[device_id]
            device.state = DeviceState.ONLINE
            device.last_seen = datetime.utcnow()
            
            metrics = self.device_metrics[device_id]
            metrics.connection_count += 1
            metrics.last_connection = datetime.utcnow()
            
            # Update statistics
            self.stats["successful_authentications"] += 1
            
            # Clear failed attempts
            self.failed_auth_attempts.pop(device_id, None)
            
            logger.info(f"Device {device_id} authenticated successfully")
            return True, session_token
            
        except Exception as e:
            logger.error(f"Authentication error for device {device_id}: {e}")
            return False, None
    
    async def validate_session(self, device_id: str, session_token: str) -> bool:
        """
        Validate a device session.
        
        Args:
            device_id: Device identifier
            session_token: Session token to validate
        
        Returns:
            True if session is valid, False otherwise
        """
        try:
            session = self.device_sessions.get(device_id)
            if not session:
                return False
            
            # Check token match
            if session['token'] != session_token:
                return False
            
            # Check session expiry
            session_age = datetime.utcnow() - session['created_at']
            if session_age > timedelta(hours=24):  # 24-hour session timeout
                await self.invalidate_session(device_id)
                return False
            
            # Update last activity
            session['last_activity'] = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Session validation error for device {device_id}: {e}")
            return False
    
    async def invalidate_session(self, device_id: str) -> bool:
        """
        Invalidate a device session.
        
        Args:
            device_id: Device identifier
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id in self.device_sessions:
                del self.device_sessions[device_id]
                
                # Update device state
                if device_id in self.devices:
                    self.devices[device_id].state = DeviceState.OFFLINE
                
                logger.info(f"Session invalidated for device {device_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to invalidate session for device {device_id}: {e}")
            return False
    
    # Device Monitoring and Metrics
    async def update_device_metrics(
        self,
        device_id: str,
        metric_updates: Dict[str, Any]
    ) -> bool:
        """
        Update device metrics.
        
        Args:
            device_id: Device identifier
            metric_updates: Dictionary of metric updates
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id not in self.device_metrics:
                logger.error(f"Metrics not found for device: {device_id}")
                return False
            
            metrics = self.device_metrics[device_id]
            
            # Update metrics
            for metric, value in metric_updates.items():
                if hasattr(metrics, metric):
                    if metric in ['messages_sent', 'messages_received', 'bytes_sent', 'bytes_received', 'error_count']:
                        # Increment counters
                        current_value = getattr(metrics, metric)
                        setattr(metrics, metric, current_value + value)
                    else:
                        # Set direct values
                        setattr(metrics, metric, value)
            
            metrics.updated_at = datetime.utcnow()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update metrics for device {device_id}: {e}")
            return False
    
    async def get_device_health(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get device health information.
        
        Args:
            device_id: Device identifier
        
        Returns:
            Device health information or None if device not found
        """
        try:
            if device_id not in self.devices:
                return None
            
            device = self.devices[device_id]
            metrics = self.device_metrics.get(device_id)
            
            # Calculate health metrics
            now = datetime.utcnow()
            
            # Connection health
            connection_health = "healthy"
            if device.last_seen:
                offline_duration = now - device.last_seen
                if offline_duration > timedelta(minutes=30):
                    connection_health = "unhealthy"
                elif offline_duration > timedelta(minutes=10):
                    connection_health = "warning"
            else:
                connection_health = "unknown"
            
            # Error rate
            error_rate = 0.0
            if metrics and metrics.messages_received > 0:
                error_rate = metrics.error_count / metrics.messages_received
            
            # Overall health score
            health_score = 1.0
            if connection_health == "unhealthy":
                health_score -= 0.5
            elif connection_health == "warning":
                health_score -= 0.2
            
            health_score -= min(error_rate, 0.3)  # Cap error penalty at 0.3
            health_score = max(0.0, health_score)
            
            return {
                "device_id": device_id,
                "overall_health": "healthy" if health_score > 0.8 else "warning" if health_score > 0.5 else "unhealthy",
                "health_score": health_score,
                "connection_health": connection_health,
                "error_rate": error_rate,
                "last_seen": device.last_seen.isoformat() if device.last_seen else None,
                "state": device.state.value,
                "uptime_hours": metrics.uptime_seconds / 3600 if metrics else 0,
                "message_count": metrics.messages_received if metrics else 0,
                "error_count": metrics.error_count if metrics else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get health for device {device_id}: {e}")
            return None
    
    # Device Groups and Organization
    async def create_device_group(self, group_name: str, device_ids: List[str]) -> bool:
        """
        Create a device group.
        
        Args:
            group_name: Name of the group
            device_ids: List of device IDs to include
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate devices exist
            valid_devices = [did for did in device_ids if did in self.devices]
            
            if len(valid_devices) != len(device_ids):
                invalid_devices = set(device_ids) - set(valid_devices)
                logger.warning(f"Invalid devices in group {group_name}: {invalid_devices}")
            
            self.device_groups[group_name] = set(valid_devices)
            
            logger.info(f"Device group '{group_name}' created with {len(valid_devices)} devices")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create device group {group_name}: {e}")
            return False
    
    async def add_device_to_group(self, group_name: str, device_id: str) -> bool:
        """
        Add a device to a group.
        
        Args:
            group_name: Name of the group
            device_id: Device ID to add
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id not in self.devices:
                logger.error(f"Device {device_id} not found")
                return False
            
            if group_name not in self.device_groups:
                self.device_groups[group_name] = set()
            
            self.device_groups[group_name].add(device_id)
            
            logger.info(f"Device {device_id} added to group '{group_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add device {device_id} to group {group_name}: {e}")
            return False
    
    async def remove_device_from_group(self, group_name: str, device_id: str) -> bool:
        """
        Remove a device from a group.
        
        Args:
            group_name: Name of the group
            device_id: Device ID to remove
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if group_name in self.device_groups:
                self.device_groups[group_name].discard(device_id)
                logger.info(f"Device {device_id} removed from group '{group_name}'")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to remove device {device_id} from group {group_name}: {e}")
            return False
    
    # Query and Reporting
    async def get_devices(
        self,
        device_type: Optional[DeviceType] = None,
        state: Optional[DeviceState] = None,
        protocol: Optional[Protocol] = None,
        group_name: Optional[str] = None
    ) -> List[Device]:
        """
        Get devices with optional filtering.
        
        Args:
            device_type: Filter by device type
            state: Filter by device state
            protocol: Filter by protocol
            group_name: Filter by group membership
        
        Returns:
            List of matching devices
        """
        try:
            devices = list(self.devices.values())
            
            # Apply filters
            if device_type:
                devices = [d for d in devices if d.device_type == device_type]
            
            if state:
                devices = [d for d in devices if d.state == state]
            
            if protocol:
                devices = [d for d in devices if d.protocol == protocol]
            
            if group_name and group_name in self.device_groups:
                group_devices = self.device_groups[group_name]
                devices = [d for d in devices if d.device_id in group_devices]
            
            return devices
            
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []
    
    async def get_device_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive device statistics.
        
        Returns:
            Dictionary containing device statistics
        """
        try:
            # Basic counts
            total_devices = len(self.devices)
            online_devices = len([d for d in self.devices.values() if d.state == DeviceState.ONLINE])
            offline_devices = len([d for d in self.devices.values() if d.state == DeviceState.OFFLINE])
            
            # Device type distribution
            type_distribution = {}
            for device in self.devices.values():
                device_type = device.device_type.value
                type_distribution[device_type] = type_distribution.get(device_type, 0) + 1
            
            # Protocol distribution
            protocol_distribution = {}
            for device in self.devices.values():
                protocol = device.protocol.value
                protocol_distribution[protocol] = protocol_distribution.get(protocol, 0) + 1
            
            # Health distribution
            health_distribution = {"healthy": 0, "warning": 0, "unhealthy": 0}
            for device_id in self.devices.keys():
                health = await self.get_device_health(device_id)
                if health:
                    health_status = health["overall_health"]
                    health_distribution[health_status] += 1
            
            # Message statistics
            total_messages = sum(m.messages_received for m in self.device_metrics.values())
            total_errors = sum(m.error_count for m in self.device_metrics.values())
            
            return {
                "total_devices": total_devices,
                "online_devices": online_devices,
                "offline_devices": offline_devices,
                "device_types": type_distribution,
                "protocols": protocol_distribution,
                "health_distribution": health_distribution,
                "total_messages_processed": total_messages,
                "total_errors": total_errors,
                "error_rate": total_errors / total_messages if total_messages > 0 else 0,
                "active_sessions": len(self.device_sessions),
                "blocked_devices": len(self.blocked_devices),
                "device_groups": len(self.device_groups),
                **self.stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get device statistics: {e}")
            return {}
    
    # Private Helper Methods
    def _validate_device_id(self, device_id: str) -> bool:
        """
        Validate device ID format.
        
        Args:
            device_id: Device ID to validate
        
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - alphanumeric, hyphens, underscores, 3-64 characters
        import re
        pattern = r'^[a-zA-Z0-9_-]{3,64}$'
        return bool(re.match(pattern, device_id))
    
    async def _generate_device_credentials(
        self,
        device_id: str,
        device_type: DeviceType
    ) -> DeviceCredentials:
        """
        Generate credentials for a device.
        
        Args:
            device_id: Device identifier
            device_type: Type of device
        
        Returns:
            Generated device credentials
        """
        # Generate API key
        api_key = f"iot_{device_type.value}_{uuid4().hex[:16]}"
        
        # Generate secret
        secret = hashlib.sha256(f"{device_id}{api_key}{datetime.utcnow().isoformat()}".encode()).hexdigest()
        
        return DeviceCredentials(
            device_id=device_id,
            api_key=api_key,
            secret_hash=secret,
            certificate_path=None,  # Would be set for certificate-based auth
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365)  # 1 year expiry
        )
    
    async def _validate_credentials(
        self,
        stored_creds: DeviceCredentials,
        provided_creds: Dict[str, str]
    ) -> bool:
        """
        Validate provided credentials against stored credentials.
        
        Args:
            stored_creds: Stored device credentials
            provided_creds: Provided credentials to validate
        
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check expiry
            if stored_creds.expires_at and datetime.utcnow() > stored_creds.expires_at:
                logger.warning(f"Expired credentials for device {stored_creds.device_id}")
                return False
            
            # Validate API key
            if provided_creds.get('api_key') != stored_creds.api_key:
                return False
            
            # Validate secret (in production, this would be properly hashed)
            provided_secret = provided_creds.get('secret', '')
            expected_hash = hashlib.sha256(provided_secret.encode()).hexdigest()
            
            return expected_hash == stored_creds.secret_hash
            
        except Exception as e:
            logger.error(f"Credential validation error: {e}")
            return False
    
    async def _generate_session_token(self, device_id: str) -> str:
        """
        Generate a session token for a device.
        
        Args:
            device_id: Device identifier
        
        Returns:
            Generated session token
        """
        token_data = f"{device_id}{datetime.utcnow().isoformat()}{uuid4().hex}"
        return hashlib.sha256(token_data.encode()).hexdigest()
    
    async def _record_failed_auth(self, device_id: str) -> None:
        """
        Record a failed authentication attempt.
        
        Args:
            device_id: Device identifier
        """
        try:
            now = datetime.utcnow()
            
            if device_id not in self.failed_auth_attempts:
                self.failed_auth_attempts[device_id] = []
            
            self.failed_auth_attempts[device_id].append(now)
            
            # Clean up old attempts (keep only last hour)
            cutoff_time = now - timedelta(hours=1)
            self.failed_auth_attempts[device_id] = [
                attempt for attempt in self.failed_auth_attempts[device_id]
                if attempt > cutoff_time
            ]
            
            # Check if device should be blocked
            recent_failures = len(self.failed_auth_attempts[device_id])
            if recent_failures >= 5:  # Block after 5 failed attempts in 1 hour
                self.blocked_devices.add(device_id)
                logger.warning(f"Device {device_id} blocked due to {recent_failures} failed auth attempts")
            
            self.stats["failed_authentications"] += 1
            
        except Exception as e:
            logger.error(f"Failed to record auth failure for device {device_id}: {e}")
    
    def _create_default_templates(self) -> Dict[DeviceType, DeviceConfig]:
        """
        Create default configuration templates for different device types.
        
        Returns:
            Dictionary mapping device types to default configurations
        """
        templates = {}
        
        # Sensor template
        templates[DeviceType.SENSOR] = DeviceConfig(
            sampling_rate=60,  # 1 minute
            batch_size=10,
            compression_enabled=True,
            encryption_enabled=True,
            max_offline_time=300,  # 5 minutes
            heartbeat_interval=30,  # 30 seconds
            data_retention_days=30,
            alert_thresholds={"data_quality": 0.8, "error_rate": 0.05}
        )
        
        # Gateway template
        templates[DeviceType.GATEWAY] = DeviceConfig(
            sampling_rate=30,  # 30 seconds
            batch_size=50,
            compression_enabled=True,
            encryption_enabled=True,
            max_offline_time=120,  # 2 minutes
            heartbeat_interval=15,  # 15 seconds
            data_retention_days=90,
            alert_thresholds={"connection_count": 100, "error_rate": 0.02}
        )
        
        # Actuator template
        templates[DeviceType.ACTUATOR] = DeviceConfig(
            sampling_rate=10,  # 10 seconds
            batch_size=5,
            compression_enabled=False,  # Real-time control
            encryption_enabled=True,
            max_offline_time=60,  # 1 minute
            heartbeat_interval=10,  # 10 seconds
            data_retention_days=7,
            alert_thresholds={"response_time": 1.0, "error_rate": 0.01}
        )
        
        # Controller template
        templates[DeviceType.CONTROLLER] = DeviceConfig(
            sampling_rate=5,  # 5 seconds
            batch_size=20,
            compression_enabled=True,
            encryption_enabled=True,
            max_offline_time=30,  # 30 seconds
            heartbeat_interval=5,  # 5 seconds
            data_retention_days=60,
            alert_thresholds={"cpu_usage": 0.8, "memory_usage": 0.9, "error_rate": 0.01}
        )
        
        return templates
    
    # Utility Methods
    async def get_device(self, device_id: str) -> Optional[Device]:
        """Get a device by ID."""
        return self.devices.get(device_id)
    
    async def get_device_credentials(self, device_id: str) -> Optional[DeviceCredentials]:
        """Get device credentials by ID."""
        return self.device_credentials.get(device_id)
    
    async def get_device_metrics(self, device_id: str) -> Optional[DeviceMetrics]:
        """Get device metrics by ID."""
        return self.device_metrics.get(device_id)
    
    async def is_device_online(self, device_id: str) -> bool:
        """Check if a device is online."""
        device = self.devices.get(device_id)
        return device is not None and device.state == DeviceState.ONLINE
    
    async def get_device_groups(self) -> Dict[str, Set[str]]:
        """Get all device groups."""
        return self.device_groups.copy()
    
    async def get_group_devices(self, group_name: str) -> Set[str]:
        """Get devices in a specific group."""
        return self.device_groups.get(group_name, set()).copy()