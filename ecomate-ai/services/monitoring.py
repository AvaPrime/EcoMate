"""Monitoring and metrics service for EcoMate API.

Provides Prometheus metrics, health checks, and operational monitoring
for all EcoMate services as specified in the professional readiness assessment.
"""

import time
import psutil
from datetime import datetime
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel


# Prometheus metrics
REQUEST_COUNT = Counter(
    'ecomate_requests_total',
    'Total number of requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'ecomate_request_duration_seconds',
    'Request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_CONNECTIONS = Gauge(
    'ecomate_active_connections',
    'Number of active connections'
)

SYSTEM_MEMORY_USAGE = Gauge(
    'ecomate_memory_usage_bytes',
    'Memory usage in bytes'
)

SYSTEM_CPU_USAGE = Gauge(
    'ecomate_cpu_usage_percent',
    'CPU usage percentage'
)

AI_MODEL_REQUESTS = Counter(
    'ecomate_ai_model_requests_total',
    'Total AI model requests',
    ['model_type', 'status']
)

GOOGLE_MAPS_REQUESTS = Counter(
    'ecomate_google_maps_requests_total',
    'Total Google Maps API requests',
    ['api_type', 'status']
)


class HealthStatus(BaseModel):
    """Health status response model."""
    status: str
    timestamp: str
    version: str
    uptime_seconds: float
    services: Dict[str, str]
    system: Dict[str, Any]


class MetricsService:
    """Service for collecting and exposing metrics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.version = "1.0.0"
    
    def get_uptime(self) -> float:
        """Get service uptime in seconds."""
        return time.time() - self.start_time
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system resource metrics."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Update Prometheus gauges
        SYSTEM_MEMORY_USAGE.set(memory.used)
        SYSTEM_CPU_USAGE.set(cpu_percent)
        
        return {
            'memory_total': memory.total,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'cpu_percent': cpu_percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
    
    def check_database_health(self) -> str:
        """Check database connectivity."""
        try:
            # TODO: Implement actual database health check
            # For now, return healthy status
            return "healthy"
        except Exception:
            return "unhealthy"
    
    def check_ai_service_health(self) -> str:
        """Check AI service health."""
        try:
            # TODO: Implement actual AI service health check
            # For now, return healthy status
            return "healthy"
        except Exception:
            return "unhealthy"
    
    def check_google_maps_health(self) -> str:
        """Check Google Maps API health."""
        try:
            # TODO: Implement actual Google Maps API health check
            # For now, return healthy status
            return "healthy"
        except Exception:
            return "unhealthy"
    
    def get_overall_status(self, services: Dict[str, str]) -> str:
        """Determine overall system status based on service health."""
        unhealthy_services = [k for k, v in services.items() if v == "unhealthy"]
        degraded_services = [k for k, v in services.items() if v == "degraded"]
        
        if unhealthy_services:
            return "unhealthy"
        elif degraded_services:
            return "degraded"
        else:
            return "healthy"
    
    def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status."""
        services = {
            'database': self.check_database_health(),
            'ai_service': self.check_ai_service_health(),
            'google_maps': self.check_google_maps_health()
        }
        
        overall_status = self.get_overall_status(services)
        system_metrics = self.get_system_metrics()
        
        return HealthStatus(
            status=overall_status,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            version=self.version,
            uptime_seconds=self.get_uptime(),
            services=services,
            system=system_metrics
        )


# Global metrics service instance
metrics_service = MetricsService()

# FastAPI router for monitoring endpoints
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint."""
    return metrics_service.get_health_status()


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/ready")
async def readiness_check():
    """Readiness check for Kubernetes."""
    health = metrics_service.get_health_status()
    if health.status == "unhealthy":
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}


@router.get("/live")
async def liveness_check():
    """Liveness check for Kubernetes."""
    return {"status": "alive"}


def record_request_metrics(method: str, endpoint: str, status_code: int, duration: float):
    """Record request metrics."""
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=str(status_code)).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)


def record_ai_request(model_type: str, success: bool):
    """Record AI model request metrics."""
    status = "success" if success else "error"
    AI_MODEL_REQUESTS.labels(model_type=model_type, status=status).inc()


def record_maps_request(api_type: str, success: bool):
    """Record Google Maps API request metrics."""
    status = "success" if success else "error"
    GOOGLE_MAPS_REQUESTS.labels(api_type=api_type, status=status).inc()


def update_active_connections(count: int):
    """Update active connections gauge."""
    ACTIVE_CONNECTIONS.set(count)