"""Monitoring and metrics service for EcoMate API.

Provides Prometheus metrics, health checks, and operational monitoring
for all EcoMate services as specified in the professional readiness assessment.
"""

import time
import psutil
import asyncio
import aiohttp
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi import APIRouter, Response, HTTPException
from pydantic import BaseModel
import os
import logging
from services.shared.logging_config import get_logger

logger = get_logger(__name__)


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

IOT_DEVICE_COUNT = Gauge(
    'ecomate_iot_devices_total',
    'Total number of IoT devices',
    ['status']
)

IOT_DATA_POINTS = Counter(
    'ecomate_iot_data_points_total',
    'Total IoT data points processed',
    ['device_type', 'data_type']
)

WORKFLOW_EXECUTIONS = Counter(
    'ecomate_workflow_executions_total',
    'Total workflow executions',
    ['workflow_type', 'status']
)

WORKFLOW_DURATION = Histogram(
    'ecomate_workflow_duration_seconds',
    'Workflow execution duration',
    ['workflow_type']
)

DATABASE_CONNECTIONS = Gauge(
    'ecomate_database_connections_active',
    'Active database connections'
)

CACHE_OPERATIONS = Counter(
    'ecomate_cache_operations_total',
    'Total cache operations',
    ['operation', 'status']
)

APP_INFO = Info(
    'ecomate_app_info',
    'Application information'
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
        self.version = os.getenv('APP_VERSION', '1.0.0')
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        # Initialize app info metric
        APP_INFO.info({
            'version': self.version,
            'environment': self.environment,
            'python_version': os.sys.version.split()[0],
            'start_time': str(datetime.fromtimestamp(self.start_time))
        })
        
        logger.info('MetricsService initialized', extra={
            'version': self.version,
            'environment': self.environment
        })
    
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
    
    async def check_database_health(self) -> str:
        """Check database connectivity."""
        try:
            # Check PostgreSQL connection
            import asyncpg
            db_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/ecomate')
            
            conn = await asyncpg.connect(db_url)
            await conn.execute('SELECT 1')
            await conn.close()
            
            logger.debug('Database health check passed')
            return "healthy"
        except Exception as e:
            logger.error('Database health check failed', extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            return "unhealthy"
    
    async def check_temporal_health(self) -> str:
        """Check Temporal server connectivity."""
        try:
            from temporalio.client import Client
            
            temporal_host = os.getenv('TEMPORAL_HOST', 'localhost:7233')
            client = await Client.connect(temporal_host)
            
            # Simple health check - list workflows (with limit)
            async for _ in client.list_workflows():
                break
            
            logger.debug('Temporal health check passed')
            return "healthy"
        except Exception as e:
            logger.error('Temporal health check failed', extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            return "unhealthy"
    
    async def check_redis_health(self) -> str:
        """Check Redis connectivity."""
        try:
            import aioredis
            
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
            redis = aioredis.from_url(redis_url)
            
            await redis.ping()
            await redis.close()
            
            logger.debug('Redis health check passed')
            return "healthy"
        except Exception as e:
            logger.error('Redis health check failed', extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            return "unhealthy"
    
    async def check_influxdb_health(self) -> str:
        """Check InfluxDB connectivity."""
        try:
            influx_url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(f'{influx_url}/health', timeout=5) as response:
                    if response.status == 200:
                        logger.debug('InfluxDB health check passed')
                        return "healthy"
                    else:
                        logger.warning('InfluxDB health check returned non-200 status', extra={
                            'status_code': response.status
                        })
                        return "degraded"
        except Exception as e:
            logger.error('InfluxDB health check failed', extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
            return "unhealthy"
    
    async def check_google_maps_health(self) -> str:
        """Check Google Maps API health."""
        try:
            api_key = os.getenv('GOOGLE_MAPS_API_KEY')
            if not api_key:
                logger.warning('Google Maps API key not configured')
                return "degraded"
            
            # Simple geocoding test
            url = f'https://maps.googleapis.com/maps/api/geocode/json?address=test&key={api_key}'
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('status') in ['OK', 'ZERO_RESULTS']:
                            logger.debug('Google Maps health check passed')
                            return "healthy"
                        else:
                            logger.warning('Google Maps API returned error status', extra={
                                'api_status': data.get('status')
                            })
                            return "degraded"
                    else:
                        logger.warning('Google Maps health check returned non-200 status', extra={
                            'status_code': response.status
                        })
                        return "degraded"
        except Exception as e:
            logger.error('Google Maps health check failed', extra={
                'error': str(e),
                'error_type': type(e).__name__
            })
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
    
    async def get_health_status(self) -> HealthStatus:
        """Get comprehensive health status."""
        # Run all health checks concurrently
        health_checks = await asyncio.gather(
            self.check_database_health(),
            self.check_temporal_health(),
            self.check_redis_health(),
            self.check_influxdb_health(),
            self.check_google_maps_health(),
            return_exceptions=True
        )
        
        # Map results to service names
        services = {
            "database": health_checks[0] if not isinstance(health_checks[0], Exception) else "unhealthy",
            "temporal": health_checks[1] if not isinstance(health_checks[1], Exception) else "unhealthy",
            "redis": health_checks[2] if not isinstance(health_checks[2], Exception) else "unhealthy",
            "influxdb": health_checks[3] if not isinstance(health_checks[3], Exception) else "unhealthy",
            "google_maps": health_checks[4] if not isinstance(health_checks[4], Exception) else "unhealthy"
        }
        
        # Log any exceptions
        service_names = ["database", "temporal", "redis", "influxdb", "google_maps"]
        for i, result in enumerate(health_checks):
            if isinstance(result, Exception):
                logger.error(f'{service_names[i]} health check exception', extra={
                    'service': service_names[i],
                    'error': str(result),
                    'error_type': type(result).__name__
                })
        
        overall_status = self.get_overall_status(services)
        system_metrics = self.get_system_metrics()
        
        # Update database connections gauge
        try:
            # This would need actual connection pool info
            DATABASE_CONNECTIONS.set(1)  # Placeholder
        except Exception:
            pass
        
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
    return await metrics_service.get_health_status()


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