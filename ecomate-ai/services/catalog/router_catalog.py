from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from temporalio.client import Client
from typing import Optional, List
from .models import CatalogSyncResult
from .activities_catalog import activity_catalog_sync, activity_catalog_sync_all
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/catalog', tags=['catalog'])

class SyncReq(BaseModel):
    source: str = Field(default='shopify', description="Platform to sync from: shopify, woocommerce, or medusa")
    force_refresh: bool = Field(default=False, description="Force refresh even if recently synced")

class SyncAllReq(BaseModel):
    force_refresh: bool = Field(default=False, description="Force refresh for all platforms")
    platforms: Optional[List[str]] = Field(default=None, description="Specific platforms to sync (default: all)")

@router.post('/sync', response_model=CatalogSyncResult)
async def sync_catalog(req: SyncReq):
    """Sync catalog from a specific e-commerce platform with normalization"""
    try:
        # Validate platform
        supported_platforms = ['shopify', 'woocommerce', 'medusa']
        if req.source not in supported_platforms:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported platform '{req.source}'. Supported: {supported_platforms}"
            )
        
        # Use Temporal workflow for production or direct call for development
        try:
            client = await Client.connect('localhost:7233')
            h = await client.start_workflow(
                'services.catalog.workflows_catalog.CatalogSyncWorkflow.run', 
                req.source, 
                id=f'catalog-sync-{req.source}', 
                task_queue='ecomate-ai'
            )
            result = await h.result()
            return result
        except Exception as temporal_error:
            logger.warning(f"Temporal workflow failed, falling back to direct execution: {temporal_error}")
            # Fallback to direct execution
            result = await activity_catalog_sync(req.source)
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Catalog sync failed for {req.source}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.post('/sync-all')
async def sync_all_catalogs(req: SyncAllReq):
    """Sync catalogs from all supported platforms"""
    try:
        platforms = req.platforms or ['shopify', 'woocommerce', 'medusa']
        
        # Validate platforms
        supported_platforms = ['shopify', 'woocommerce', 'medusa']
        invalid_platforms = [p for p in platforms if p not in supported_platforms]
        if invalid_platforms:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platforms: {invalid_platforms}. Supported: {supported_platforms}"
            )
        
        results = await activity_catalog_sync_all()
        
        # Filter results to requested platforms
        if req.platforms:
            results = {k: v for k, v in results.items() if k in req.platforms}
        
        return {
            "results": results,
            "summary": {
                "total_platforms": len(results),
                "successful_syncs": len([r for r in results.values() if not r.errors]),
                "total_products_fetched": sum(r.total_fetched for r in results.values()),
                "total_products_normalized": sum(r.total_normalized for r in results.values())
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bulk catalog sync failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Bulk sync failed: {str(e)}")

@router.get('/platforms')
async def get_supported_platforms():
    """Get list of supported e-commerce platforms"""
    return {
        "platforms": [
            {
                "name": "shopify",
                "display_name": "Shopify",
                "description": "Shopify e-commerce platform",
                "requires_auth": True,
                "auth_fields": ["SHOPIFY_STORE_URL", "SHOPIFY_ADMIN_TOKEN"]
            },
            {
                "name": "woocommerce",
                "display_name": "WooCommerce",
                "description": "WooCommerce WordPress plugin",
                "requires_auth": True,
                "auth_fields": ["WOOCOMMERCE_URL", "WOOCOMMERCE_KEY", "WOOCOMMERCE_SECRET"]
            },
            {
                "name": "medusa",
                "display_name": "Medusa",
                "description": "Medusa e-commerce platform",
                "requires_auth": True,
                "auth_fields": ["MEDUSA_API_URL", "MEDUSA_API_TOKEN"]
            }
        ]
    }

@router.get('/health')
async def catalog_health():
    """Health check for catalog service"""
    return {
        "status": "healthy",
        "service": "catalog",
        "features": {
            "normalization": True,
            "multi_platform": True,
            "temporal_workflows": True
        }
    }