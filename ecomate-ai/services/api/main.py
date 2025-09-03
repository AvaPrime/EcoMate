from datetime import datetime
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from temporalio.client import Client
import uuid
import logging
import os
import json
import time
from functools import wraps
from contextlib import asynccontextmanager
from services.proposal.router_proposal import router as proposal_router
from services.catalog.router_catalog import router as catalog_router
from services.maintenance.router_maintenance import router as maintenance_router
from services.compliance.router_compliance import router as compliance_router
from services.telemetry.router_telemetry import router as telemetry_router
from services.regulatory.router import router as regulatory_router
from services.geospatial.router import router as geospatial_router
from services.climate.router import router as climate_router
from services.iot.router import router as iot_router
from services.monitoring import router as monitoring_router, record_request_metrics
from services.shared.logging_config import setup_logging, get_logger
from services.shared.rate_limiting import rate_limit_middleware
from services.shared.validation import (
    ValidatedResearchReq, ValidatedNewResearchReq, ValidatedPriceMonitorReq,
    validate_request_size, sanitize_output
)

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# FastAPI app with enhanced metadata
app = FastAPI(
    title="EcoMate AI API",
    description="Enterprise-grade AI-powered environmental management and sustainability platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request tracking middleware
@app.middleware("http")
async def request_tracking_middleware(request, call_next):
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Add request ID to logger context
    logger.info("Request started", extra={
        'request_id': request_id,
        'method': request.method,
        'url': str(request.url),
        'client_ip': request.client.host if request.client else None
    })
    
    response = await call_next(request)
    
    # Calculate duration and log completion
    duration = time.time() - start_time
    logger.info("Request completed", extra={
        'request_id': request_id,
        'method': request.method,
        'url': str(request.url),
        'status_code': response.status_code,
        'duration': duration
    })
    
    # Record metrics
    record_request_metrics(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response

# Include all service routers
app.include_router(proposal_router)
app.include_router(catalog_router)
app.include_router(maintenance_router)
app.include_router(compliance_router)
app.include_router(telemetry_router)
app.include_router(regulatory_router)
app.include_router(geospatial_router)
app.include_router(climate_router)
app.include_router(iot_router)
app.include_router(monitoring_router)

def handle_exceptions(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_id = str(uuid.uuid4())
            logger.error("Exception occurred", extra={
                'error_id': error_id,
                'function': func.__name__,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'args': str(args),
                'kwargs': str(kwargs)
            }, exc_info=True)
            
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e),
                    "error_id": error_id
                }
            )
    return wrapper

# Health check endpoint (required for production)
@app.get("/health")
@handle_exceptions
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
    # Basic health checks
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.1.0",
        "services": {
            "api": "healthy",
            "temporal": "unknown",  # Would check Temporal connection
            "database": "unknown",  # Would check DB connection
        }
    }
    
    # Optional: Add more detailed health checks
    # - Database connectivity
    # - Temporal server connectivity
    # - External API availability
    
    return JSONResponse(
        status_code=200,
        content=health_status
    )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "EcoMate AI API",
        "version": "0.1.0",
        "description": "Enterprise-grade AI-powered environmental management platform",
        "docs_url": "/docs",
        "health_url": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }

# Request/Response models
class ResearchReq(BaseModel):
    query: str
    limit: int = 5

class PriceMonitorReq(BaseModel):
    create_pr: bool = True

class NewResearchReq(BaseModel):
    urls: list[str]

@app.post("/run/research")
@handle_exceptions
async def run_research(req: ResearchReq):
    urls = [
        "https://www.example.com/",
        "https://www.google.com/",
        "https://en.wikipedia.org/wiki/Moving_bed_biofilm_reactor",
    ][: req.limit]
    client = await Client.connect("localhost:7233")
    handle = await client.start_workflow(
        "services.orchestrator.workflows.ResearchWorkflow.run",
        req.query,
        urls,
        id=f"research-{req.query[:12]}",
        task_queue="ecomate-ai",
    )
    res = await handle.result()
    return res

@app.post("/run/new-research")
@handle_exceptions
async def run_new_research(req: NewResearchReq):
    """Trigger new research workflow for crawling and extracting supplier/parts data."""
    client = await Client.connect("localhost:7233")
    workflow_id = f"new-research-{uuid.uuid4().hex[:8]}"
    
    handle = await client.start_workflow(
        "services.orchestrator.research_workflows.ResearchWorkflow.run",
        req.urls,
        id=workflow_id,
        task_queue="ecomate-ai",
    )
    
    res = await handle.result()
    return res

@app.post("/run/price-monitor")
@handle_exceptions
async def run_price_monitor(req: PriceMonitorReq):
    """Trigger price monitoring workflow."""
    client = await Client.connect("localhost:7233")
    workflow_id = f"price-monitor-{uuid.uuid4().hex[:8]}"
    
    handle = await client.start_workflow(
        "services.orchestrator.price_workflows.PriceMonitorWorkflow.run",
        req.create_pr,
        id=workflow_id,
        task_queue="ecomate-ai",
    )
    
    res = await handle.result()
    return res

@app.post("/run/scheduled-price-monitor")
@handle_exceptions
async def run_scheduled_price_monitor():
    """Trigger scheduled price monitoring workflow (always creates PR)."""
    client = await Client.connect("localhost:7233")
    workflow_id = f"scheduled-price-monitor-{uuid.uuid4().hex[:8]}"
    
    handle = await client.start_workflow(
        "services.orchestrator.price_workflows.ScheduledPriceMonitorWorkflow.run",
        id=workflow_id,
        task_queue="ecomate-ai",
    )
    
    res = await handle.result()
    return res