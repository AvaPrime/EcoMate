"""
IoT Security Manager

Comprehensive security management for IoT devices including authentication,
authorization, encryption, and threat detection.
"""

import asyncio
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import jwt
from cryptography.fernet import Fernet

from .models import (
    DeviceCredentials, IoTDevice, SecurityEvent, SecurityLevel,
    ThreatLevel, AuthenticationMethod
)


logger = logging.getLogger(__name__)


class SecurityManager:
    """
    Comprehensive IoT security management.
    
    Provides device authentication, authorization, encryption, threat detection,
    and security monitoring for IoT devices and communications.
    """
    
    def __init__(self, secret_key: Optional[str] = None):
        # Encryption and signing keys
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.jwt_secret = secrets.token_urlsafe(32)
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        # Device credentials and sessions
        self.device_credentials: Dict[str, DeviceCredentials] = {}
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.revoked_tokens: Set[str] = set()
        
        # Security policies and rules
        self.security_policies: Dict[str, Dict[str, Any]] = {}
        self.access_rules: Dict[str, List[str]] = {}
        self.rate_limits: Dict[str, Dict[str, Any]] = {}
        
        # Threat detection
        self.security_events: List[SecurityEvent] = []
        self.threat_patterns: Dict[str, Dict[str, Any]] = {}
        self.blocked_devices: Set[str] = set()
        self.suspicious_activities: Dict[str, List[Dict[str, Any]]] = {}
        
        # Security statistics
        self.stats = {
            "authentication_attempts": 0,
            "authentication_successes": 0,
            "authentication_failures": 0,
            "authorization_checks": 0,
            "authorization_denials": 0,
            "encryption_operations": 0,
            "decryption_operations": 0,
            "security_events": 0,
            "threats_detected": 0,
            "devices_blocked": 0
        }
        
        # Setup default security policies
        self._setup_default_policies()
        
        # Start security monitoring
        asyncio.create_task(self._security_monitor())
        
        logger.info("Security manager initialized")
    
    # Device Authentication
    async def register_device(
        self,
        device: IoTDevice,
        authentication_method: AuthenticationMethod = AuthenticationMethod.API_KEY
    ) -> DeviceCredentials:
        """
        Register a new device and generate credentials.
        
        Args:
            device: IoT device to register
            authentication_method: Authentication method to use
        
        Returns:
            Generated device credentials
        """
        try:
            # Generate credentials based on authentication method
            credentials = await self._generate_credentials(device.device_id, authentication_method)
            
            # Store credentials
            self.device_credentials[device.device_id] = credentials
            
            # Create security event
            await self._log_security_event(
                "device_registered",
                device.device_id,
                {"authentication_method": authentication_method.value}
            )
            
            logger.info(f"Device {device.device_id} registered with {authentication_method.value}")
            return credentials
            
        except Exception as e:
            logger.error(f"Failed to register device {device.device_id}: {e}")
            raise
    
    async def authenticate_device(
        self,
        device_id: str,
        credentials: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Authenticate a device using provided credentials.
        
        Args:
            device_id: ID of the device to authenticate
            credentials: Authentication credentials
        
        Returns:
            Tuple of (success, session_token)
        """
        try:
            self.stats["authentication_attempts"] += 1
            
            # Check if device is blocked
            if device_id in self.blocked_devices:
                await self._log_security_event(
                    "authentication_blocked",
                    device_id,
                    {"reason": "device_blocked"}
                )
                self.stats["authentication_failures"] += 1
                return False, None
            
            # Get stored credentials
            stored_credentials = self.device_credentials.get(device_id)
            if not stored_credentials:
                await self._log_security_event(
                    "authentication_failed",
                    device_id,
                    {"reason": "device_not_registered"}
                )
                self.stats["authentication_failures"] += 1
                return False, None
            
            # Verify credentials based on authentication method
            success = await self._verify_credentials(stored_credentials, credentials)
            
            if success:
                # Generate session token
                session_token = await self._create_session(device_id)
                
                await self._log_security_event(
                    "authentication_success",
                    device_id,
                    {"session_token": session_token[:8] + "..."}
                )
                
                self.stats["authentication_successes"] += 1
                return True, session_token
            else:
                await self._log_security_event(
                    "authentication_failed",
                    device_id,
                    {"reason": "invalid_credentials"}
                )
                
                # Track failed attempts for threat detection
                await self._track_failed_authentication(device_id)
                
                self.stats["authentication_failures"] += 1
                return False, None
            
        except Exception as e:
            logger.error(f"Authentication error for device {device_id}: {e}")
            self.stats["authentication_failures"] += 1
            return False, None
    
    async def validate_session(self, session_token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a session token.
        
        Args:
            session_token: Session token to validate
        
        Returns:
            Tuple of (valid, device_id)
        """
        try:
            # Check if token is revoked
            if session_token in self.revoked_tokens:
                return False, None
            
            # Decode JWT token
            try:
                payload = jwt.decode(
                    session_token,
                    self.jwt_secret,
                    algorithms=["HS256"]
                )
            except jwt.InvalidTokenError:
                return False, None
            
            device_id = payload.get("device_id")
            session_id = payload.get("session_id")
            
            # Check if session exists and is active
            if session_id in self.active_sessions:
                session = self.active_sessions[session_id]
                
                # Check expiration
                if datetime.utcnow() < session["expires_at"]:
                    # Update last activity
                    session["last_activity"] = datetime.utcnow()
                    return True, device_id
                else:
                    # Session expired
                    del self.active_sessions[session_id]
                    return False, None
            
            return False, None
            
        except Exception as e:
            logger.error(f"Session validation error: {e}")
            return False, None
    
    async def revoke_session(self, session_token: str) -> bool:
        """
        Revoke a session token.
        
        Args:
            session_token: Session token to revoke
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Add to revoked tokens
            self.revoked_tokens.add(session_token)
            
            # Try to get session info for cleanup
            try:
                payload = jwt.decode(
                    session_token,
                    self.jwt_secret,
                    algorithms=["HS256"]
                )
                session_id = payload.get("session_id")
                device_id = payload.get("device_id")
                
                # Remove from active sessions
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                await self._log_security_event(
                    "session_revoked",
                    device_id,
                    {"session_id": session_id}
                )
                
            except jwt.InvalidTokenError:
                pass  # Token was already invalid
            
            return True
            
        except Exception as e:
            logger.error(f"Session revocation error: {e}")
            return False
    
    # Authorization
    async def check_authorization(
        self,
        device_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if a device is authorized to perform an action on a resource.
        
        Args:
            device_id: ID of the device
            resource: Resource being accessed
            action: Action being performed
        
        Returns:
            True if authorized, False otherwise
        """
        try:
            self.stats["authorization_checks"] += 1
            
            # Check if device is blocked
            if device_id in self.blocked_devices:
                self.stats["authorization_denials"] += 1
                return False
            
            # Get device credentials for security level
            credentials = self.device_credentials.get(device_id)
            if not credentials:
                self.stats["authorization_denials"] += 1
                return False
            
            # Check access rules
            device_rules = self.access_rules.get(device_id, [])
            
            # Check if specific permission exists
            permission = f"{resource}:{action}"
            if permission in device_rules or "*:*" in device_rules:
                return True
            
            # Check wildcard permissions
            resource_wildcard = f"{resource}:*"
            action_wildcard = f"*:{action}"
            
            if resource_wildcard in device_rules or action_wildcard in device_rules:
                return True
            
            # Check security level based permissions
            if await self._check_security_level_permission(credentials.security_level, resource, action):
                return True
            
            # Authorization denied
            await self._log_security_event(
                "authorization_denied",
                device_id,
                {"resource": resource, "action": action}
            )
            
            self.stats["authorization_denials"] += 1
            return False
            
        except Exception as e:
            logger.error(f"Authorization check error: {e}")
            self.stats["authorization_denials"] += 1
            return False
    
    async def grant_permission(
        self,
        device_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Grant a permission to a device.
        
        Args:
            device_id: ID of the device
            resource: Resource to grant access to
            action: Action to allow
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id not in self.access_rules:
                self.access_rules[device_id] = []
            
            permission = f"{resource}:{action}"
            if permission not in self.access_rules[device_id]:
                self.access_rules[device_id].append(permission)
                
                await self._log_security_event(
                    "permission_granted",
                    device_id,
                    {"resource": resource, "action": action}
                )
                
                logger.info(f"Permission {permission} granted to device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to grant permission: {e}")
            return False
    
    async def revoke_permission(
        self,
        device_id: str,
        resource: str,
        action: str
    ) -> bool:
        """
        Revoke a permission from a device.
        
        Args:
            device_id: ID of the device
            resource: Resource to revoke access from
            action: Action to deny
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id in self.access_rules:
                permission = f"{resource}:{action}"
                if permission in self.access_rules[device_id]:
                    self.access_rules[device_id].remove(permission)
                    
                    await self._log_security_event(
                        "permission_revoked",
                        device_id,
                        {"resource": resource, "action": action}
                    )
                    
                    logger.info(f"Permission {permission} revoked from device {device_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to revoke permission: {e}")
            return False
    
    # Encryption and Decryption
    async def encrypt_data(self, data: str) -> str:
        """
        Encrypt data using symmetric encryption.
        
        Args:
            data: Data to encrypt
        
        Returns:
            Encrypted data as base64 string
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            self.stats["encryption_operations"] += 1
            return encrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise
    
    async def decrypt_data(self, encrypted_data: str) -> str:
        """
        Decrypt data using symmetric encryption.
        
        Args:
            encrypted_data: Encrypted data as base64 string
        
        Returns:
            Decrypted data
        """
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            self.stats["decryption_operations"] += 1
            return decrypted_data.decode()
            
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise
    
    async def sign_message(self, message: str, device_id: str) -> str:
        """
        Sign a message using HMAC.
        
        Args:
            message: Message to sign
            device_id: ID of the device signing the message
        
        Returns:
            Message signature
        """
        try:
            credentials = self.device_credentials.get(device_id)
            if not credentials:
                raise ValueError(f"No credentials found for device {device_id}")
            
            # Use device secret for signing
            signature = hmac.new(
                credentials.secret.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
            
        except Exception as e:
            logger.error(f"Message signing error: {e}")
            raise
    
    async def verify_signature(
        self,
        message: str,
        signature: str,
        device_id: str
    ) -> bool:
        """
        Verify a message signature.
        
        Args:
            message: Original message
            signature: Message signature
            device_id: ID of the device that signed the message
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            expected_signature = await self.sign_message(message, device_id)
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False
    
    # Threat Detection
    async def detect_threats(self, device_id: str, activity_data: Dict[str, Any]) -> List[str]:
        """
        Detect potential security threats based on device activity.
        
        Args:
            device_id: ID of the device
            activity_data: Activity data to analyze
        
        Returns:
            List of detected threats
        """
        threats = []
        
        try:
            # Check for suspicious patterns
            threats.extend(await self._check_rate_limiting(device_id, activity_data))
            threats.extend(await self._check_anomalous_behavior(device_id, activity_data))
            threats.extend(await self._check_known_attack_patterns(device_id, activity_data))
            
            # Log threats
            for threat in threats:
                await self._log_security_event(
                    "threat_detected",
                    device_id,
                    {"threat": threat, "activity": activity_data}
                )
                
                self.stats["threats_detected"] += 1
            
            # Take action on high-severity threats
            if threats:
                await self._handle_threats(device_id, threats)
            
            return threats
            
        except Exception as e:
            logger.error(f"Threat detection error: {e}")
            return []
    
    async def block_device(self, device_id: str, reason: str) -> bool:
        """
        Block a device from accessing the system.
        
        Args:
            device_id: ID of the device to block
            reason: Reason for blocking
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.blocked_devices.add(device_id)
            
            # Revoke all active sessions for the device
            sessions_to_revoke = [
                session_id for session_id, session in self.active_sessions.items()
                if session.get("device_id") == device_id
            ]
            
            for session_id in sessions_to_revoke:
                del self.active_sessions[session_id]
            
            await self._log_security_event(
                "device_blocked",
                device_id,
                {"reason": reason, "sessions_revoked": len(sessions_to_revoke)}
            )
            
            self.stats["devices_blocked"] += 1
            logger.warning(f"Device {device_id} blocked: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to block device {device_id}: {e}")
            return False
    
    async def unblock_device(self, device_id: str) -> bool:
        """
        Unblock a previously blocked device.
        
        Args:
            device_id: ID of the device to unblock
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if device_id in self.blocked_devices:
                self.blocked_devices.remove(device_id)
                
                await self._log_security_event(
                    "device_unblocked",
                    device_id,
                    {}
                )
                
                logger.info(f"Device {device_id} unblocked")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to unblock device {device_id}: {e}")
            return False
    
    # Security Monitoring
    async def get_security_events(
        self,
        device_id: Optional[str] = None,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[SecurityEvent]:
        """
        Get security events with optional filtering.
        
        Args:
            device_id: Filter by device ID
            event_type: Filter by event type
            limit: Maximum number of events to return
        
        Returns:
            List of security events
        """
        try:
            events = self.security_events
            
            # Apply filters
            if device_id:
                events = [e for e in events if e.device_id == device_id]
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            # Sort by timestamp (newest first) and limit
            events.sort(key=lambda x: x.timestamp, reverse=True)
            return events[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get security events: {e}")
            return []
    
    async def get_security_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive security statistics.
        
        Returns:
            Dictionary containing security statistics
        """
        try:
            # Calculate rates
            total_auth_attempts = self.stats["authentication_attempts"]
            auth_success_rate = 0.0
            if total_auth_attempts > 0:
                auth_success_rate = self.stats["authentication_successes"] / total_auth_attempts
            
            total_auth_checks = self.stats["authorization_checks"]
            auth_denial_rate = 0.0
            if total_auth_checks > 0:
                auth_denial_rate = self.stats["authorization_denials"] / total_auth_checks
            
            return {
                "registered_devices": len(self.device_credentials),
                "active_sessions": len(self.active_sessions),
                "blocked_devices": len(self.blocked_devices),
                "revoked_tokens": len(self.revoked_tokens),
                "security_events": len(self.security_events),
                "authentication_success_rate": auth_success_rate,
                "authorization_denial_rate": auth_denial_rate,
                **self.stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get security statistics: {e}")
            return {}
    
    # Private Helper Methods
    async def _generate_credentials(
        self,
        device_id: str,
        auth_method: AuthenticationMethod
    ) -> DeviceCredentials:
        """
        Generate credentials for a device.
        
        Args:
            device_id: ID of the device
            auth_method: Authentication method
        
        Returns:
            Generated credentials
        """
        credentials = DeviceCredentials(
            device_id=device_id,
            authentication_method=auth_method,
            api_key=secrets.token_urlsafe(32) if auth_method == AuthenticationMethod.API_KEY else None,
            secret=secrets.token_urlsafe(32),
            certificate=None,  # Would generate X.509 certificate for certificate auth
            security_level=SecurityLevel.MEDIUM,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),
            last_used=None
        )
        
        return credentials
    
    async def _verify_credentials(
        self,
        stored_credentials: DeviceCredentials,
        provided_credentials: Dict[str, Any]
    ) -> bool:
        """
        Verify provided credentials against stored credentials.
        
        Args:
            stored_credentials: Stored device credentials
            provided_credentials: Provided credentials to verify
        
        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            auth_method = stored_credentials.authentication_method
            
            if auth_method == AuthenticationMethod.API_KEY:
                provided_key = provided_credentials.get("api_key")
                return provided_key == stored_credentials.api_key
            
            elif auth_method == AuthenticationMethod.CERTIFICATE:
                # Certificate verification would be implemented here
                certificate = provided_credentials.get("certificate")
                return certificate == stored_credentials.certificate
            
            elif auth_method == AuthenticationMethod.OAUTH:
                # OAuth token verification would be implemented here
                token = provided_credentials.get("oauth_token")
                return await self._verify_oauth_token(token)
            
            elif auth_method == AuthenticationMethod.HMAC:
                # HMAC signature verification
                message = provided_credentials.get("message", "")
                signature = provided_credentials.get("signature", "")
                expected_signature = hmac.new(
                    stored_credentials.secret.encode(),
                    message.encode(),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(signature, expected_signature)
            
            return False
            
        except Exception as e:
            logger.error(f"Credential verification error: {e}")
            return False
    
    async def _verify_oauth_token(self, token: str) -> bool:
        """
        Verify OAuth token (placeholder implementation).
        
        Args:
            token: OAuth token to verify
        
        Returns:
            True if token is valid, False otherwise
        """
        # In production, this would verify the token with the OAuth provider
        return bool(token and len(token) > 10)
    
    async def _create_session(self, device_id: str) -> str:
        """
        Create a new session for a device.
        
        Args:
            device_id: ID of the device
        
        Returns:
            Session token
        """
        session_id = str(uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=24)  # 24-hour sessions
        
        # Store session
        self.active_sessions[session_id] = {
            "device_id": device_id,
            "created_at": datetime.utcnow(),
            "expires_at": expires_at,
            "last_activity": datetime.utcnow()
        }
        
        # Generate JWT token
        payload = {
            "device_id": device_id,
            "session_id": session_id,
            "exp": expires_at,
            "iat": datetime.utcnow()
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm="HS256")
        return token
    
    async def _track_failed_authentication(self, device_id: str) -> None:
        """
        Track failed authentication attempts for threat detection.
        
        Args:
            device_id: ID of the device
        """
        try:
            if device_id not in self.suspicious_activities:
                self.suspicious_activities[device_id] = []
            
            # Add failed attempt
            self.suspicious_activities[device_id].append({
                "type": "failed_authentication",
                "timestamp": datetime.utcnow(),
                "details": {}
            })
            
            # Check for brute force attacks
            recent_failures = [
                activity for activity in self.suspicious_activities[device_id]
                if activity["type"] == "failed_authentication"
                and activity["timestamp"] > datetime.utcnow() - timedelta(minutes=15)
            ]
            
            if len(recent_failures) >= 5:  # 5 failures in 15 minutes
                await self.block_device(device_id, "Brute force attack detected")
            
        except Exception as e:
            logger.error(f"Failed to track authentication failure: {e}")
    
    async def _check_security_level_permission(
        self,
        security_level: SecurityLevel,
        resource: str,
        action: str
    ) -> bool:
        """
        Check if a security level allows access to a resource/action.
        
        Args:
            security_level: Security level of the device
            resource: Resource being accessed
            action: Action being performed
        
        Returns:
            True if allowed, False otherwise
        """
        # Define security level permissions
        permissions = {
            SecurityLevel.LOW: ["telemetry:read", "status:read"],
            SecurityLevel.MEDIUM: [
                "telemetry:read", "telemetry:write",
                "status:read", "status:write",
                "config:read"
            ],
            SecurityLevel.HIGH: [
                "telemetry:*", "status:*", "config:*",
                "control:read", "control:write"
            ],
            SecurityLevel.CRITICAL: ["*:*"]  # Full access
        }
        
        allowed_permissions = permissions.get(security_level, [])
        permission = f"{resource}:{action}"
        
        return (
            permission in allowed_permissions or
            f"{resource}:*" in allowed_permissions or
            "*:*" in allowed_permissions
        )
    
    async def _check_rate_limiting(
        self,
        device_id: str,
        activity_data: Dict[str, Any]
    ) -> List[str]:
        """
        Check for rate limiting violations.
        
        Args:
            device_id: ID of the device
            activity_data: Activity data
        
        Returns:
            List of detected threats
        """
        threats = []
        
        try:
            # Check message rate
            message_count = activity_data.get("message_count", 0)
            time_window = activity_data.get("time_window_minutes", 1)
            
            # Default rate limit: 100 messages per minute
            rate_limit = self.rate_limits.get(device_id, {}).get("messages_per_minute", 100)
            
            if message_count > rate_limit * time_window:
                threats.append(f"Rate limit exceeded: {message_count} messages in {time_window} minutes")
            
        except Exception as e:
            logger.error(f"Rate limiting check error: {e}")
        
        return threats
    
    async def _check_anomalous_behavior(
        self,
        device_id: str,
        activity_data: Dict[str, Any]
    ) -> List[str]:
        """
        Check for anomalous behavior patterns.
        
        Args:
            device_id: ID of the device
            activity_data: Activity data
        
        Returns:
            List of detected threats
        """
        threats = []
        
        try:
            # Check for unusual activity times
            activity_hour = activity_data.get("activity_hour")
            if activity_hour is not None and (activity_hour < 6 or activity_hour > 22):
                threats.append("Unusual activity time detected")
            
            # Check for data size anomalies
            data_size = activity_data.get("data_size_bytes", 0)
            if data_size > 1024 * 1024:  # 1MB threshold
                threats.append(f"Unusually large data payload: {data_size} bytes")
            
            # Check for geographic anomalies (if location data available)
            location = activity_data.get("location")
            if location:
                # Placeholder for geographic anomaly detection
                pass
            
        except Exception as e:
            logger.error(f"Anomalous behavior check error: {e}")
        
        return threats
    
    async def _check_known_attack_patterns(
        self,
        device_id: str,
        activity_data: Dict[str, Any]
    ) -> List[str]:
        """
        Check for known attack patterns.
        
        Args:
            device_id: ID of the device
            activity_data: Activity data
        
        Returns:
            List of detected threats
        """
        threats = []
        
        try:
            # Check for SQL injection patterns in data
            payload = activity_data.get("payload", "")
            if isinstance(payload, str):
                sql_patterns = ["'; DROP TABLE", "UNION SELECT", "OR 1=1"]
                for pattern in sql_patterns:
                    if pattern.lower() in payload.lower():
                        threats.append(f"SQL injection pattern detected: {pattern}")
            
            # Check for command injection patterns
            command_patterns = ["; rm -rf", "&& rm", "| nc"]
            for pattern in command_patterns:
                if pattern in str(payload):
                    threats.append(f"Command injection pattern detected: {pattern}")
            
        except Exception as e:
            logger.error(f"Attack pattern check error: {e}")
        
        return threats
    
    async def _handle_threats(self, device_id: str, threats: List[str]) -> None:
        """
        Handle detected threats by taking appropriate actions.
        
        Args:
            device_id: ID of the device
            threats: List of detected threats
        """
        try:
            # Determine threat level
            high_severity_patterns = ["injection", "brute force", "rate limit"]
            
            has_high_severity = any(
                any(pattern in threat.lower() for pattern in high_severity_patterns)
                for threat in threats
            )
            
            if has_high_severity:
                # Block device for high-severity threats
                await self.block_device(device_id, f"High-severity threats detected: {', '.join(threats)}")
            else:
                # Log and monitor for lower-severity threats
                logger.warning(f"Threats detected for device {device_id}: {threats}")
        
        except Exception as e:
            logger.error(f"Threat handling error: {e}")
    
    async def _log_security_event(
        self,
        event_type: str,
        device_id: str,
        details: Dict[str, Any]
    ) -> None:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            device_id: ID of the device involved
            details: Additional event details
        """
        try:
            event = SecurityEvent(
                event_id=str(uuid4()),
                event_type=event_type,
                device_id=device_id,
                timestamp=datetime.utcnow(),
                details=details,
                threat_level=ThreatLevel.LOW  # Default, would be determined based on event type
            )
            
            self.security_events.append(event)
            self.stats["security_events"] += 1
            
            # Keep only recent events (last 10000)
            if len(self.security_events) > 10000:
                self.security_events = self.security_events[-10000:]
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _setup_default_policies(self) -> None:
        """
        Setup default security policies.
        """
        self.security_policies = {
            "session_timeout": {"hours": 24},
            "max_failed_attempts": 5,
            "rate_limits": {
                "default_messages_per_minute": 100,
                "default_data_size_mb": 10
            },
            "encryption": {
                "required": True,
                "algorithm": "AES-256"
            },
            "authentication": {
                "require_strong_credentials": True,
                "allow_anonymous": False
            }
        }
    
    async def _security_monitor(self) -> None:
        """
        Background security monitoring task.
        """
        while True:
            try:
                # Clean up expired sessions
                await self._cleanup_expired_sessions()
                
                # Clean up old security events
                await self._cleanup_old_events()
                
                # Monitor for suspicious patterns
                await self._monitor_suspicious_patterns()
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Security monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_expired_sessions(self) -> None:
        """
        Clean up expired sessions.
        """
        try:
            now = datetime.utcnow()
            expired_sessions = [
                session_id for session_id, session in self.active_sessions.items()
                if session["expires_at"] < now
            ]
            
            for session_id in expired_sessions:
                del self.active_sessions[session_id]
            
            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        except Exception as e:
            logger.error(f"Session cleanup error: {e}")
    
    async def _cleanup_old_events(self) -> None:
        """
        Clean up old security events.
        """
        try:
            # Keep events from last 30 days
            cutoff_date = datetime.utcnow() - timedelta(days=30)
            
            old_count = len(self.security_events)
            self.security_events = [
                event for event in self.security_events
                if event.timestamp > cutoff_date
            ]
            
            cleaned_count = old_count - len(self.security_events)
            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} old security events")
        
        except Exception as e:
            logger.error(f"Event cleanup error: {e}")
    
    async def _monitor_suspicious_patterns(self) -> None:
        """
        Monitor for suspicious activity patterns.
        """
        try:
            # Check for devices with multiple recent failures
            for device_id, activities in self.suspicious_activities.items():
                recent_activities = [
                    activity for activity in activities
                    if activity["timestamp"] > datetime.utcnow() - timedelta(hours=1)
                ]
                
                if len(recent_activities) > 10:  # More than 10 suspicious activities in 1 hour
                    await self.block_device(device_id, "Excessive suspicious activity")
        
        except Exception as e:
            logger.error(f"Suspicious pattern monitoring error: {e}")