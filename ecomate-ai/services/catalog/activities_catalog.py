from typing import Dict
from services.utils.github_pr import open_pr
from .connectors import shopify, woocommerce, medusa
from .sync import CatalogNormalizer
from .models import CatalogSyncResult
import json, datetime, time
import logging

logger = logging.getLogger(__name__)

async def activity_catalog_sync(source: str = 'shopify') -> CatalogSyncResult:
    """Enhanced catalog sync with comprehensive normalization"""
    start_time = time.time()
    errors = []
    warnings = []
    
    try:
        # Fetch products from the specified platform
        if source == 'shopify':
            raw_products = await shopify.fetch_products()
        elif source == 'woocommerce':
            raw_products = await woocommerce.fetch_products()
        elif source == 'medusa':
            raw_products = await medusa.fetch_products()
        else:
            raise ValueError(f"Unsupported platform: {source}")
        
        if not raw_products:
            warnings.append(f"No products fetched from {source}")
            return CatalogSyncResult(
                platform=source,
                total_fetched=0,
                total_normalized=0,
                warnings=warnings,
                duration_seconds=time.time() - start_time
            )
        
        # Normalize products using the unified normalizer
        normalizer = CatalogNormalizer()
        normalized_products = normalizer.normalize_products(raw_products, source)
        
        # Convert to JSON-serializable format for storage
        serializable_products = []
        for product in normalized_products:
            try:
                product_dict = product.dict()
                # Convert Decimal to string for JSON serialization
                if product_dict.get('price'):
                    product_dict['price'] = str(product_dict['price'])
                if product_dict.get('compare_at_price'):
                    product_dict['compare_at_price'] = str(product_dict['compare_at_price'])
                
                # Handle variants pricing
                for variant in product_dict.get('variants', []):
                    if variant.get('price'):
                        variant['price'] = str(variant['price'])
                    if variant.get('compare_at_price'):
                        variant['compare_at_price'] = str(variant['compare_at_price'])
                
                # Convert datetime objects to ISO strings
                for field in ['created_at', 'updated_at', 'published_at']:
                    if product_dict.get(field):
                        product_dict[field] = product_dict[field].isoformat()
                
                serializable_products.append(product_dict)
                
            except Exception as e:
                error_msg = f"Failed to serialize product {product.id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        # Create GitHub PR with normalized data
        today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
        body = json.dumps(serializable_products, ensure_ascii=False, indent=2)
        
        try:
            open_pr(
                f"bot/catalog-{source}-{today}", 
                f"Catalog sync ({source}) {today} - {len(normalized_products)} products normalized", 
                {f"catalog/{source}_normalized_{today}.json": body}
            )
        except Exception as e:
            error_msg = f"Failed to create GitHub PR: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        # Create sync result
        result = CatalogSyncResult(
            platform=source,
            total_fetched=len(raw_products),
            total_normalized=len(normalized_products),
            errors=errors,
            warnings=warnings,
            duration_seconds=time.time() - start_time
        )
        
        logger.info(f"Catalog sync completed for {source}: {len(normalized_products)}/{len(raw_products)} products normalized")
        return result
        
    except Exception as e:
        error_msg = f"Catalog sync failed for {source}: {str(e)}"
        logger.error(error_msg)
        errors.append(error_msg)
        
        return CatalogSyncResult(
            platform=source,
            total_fetched=0,
            total_normalized=0,
            errors=errors,
            warnings=warnings,
            duration_seconds=time.time() - start_time
        )

async def activity_catalog_sync_all() -> Dict[str, CatalogSyncResult]:
    """Sync catalogs from all supported platforms"""
    platforms = ['shopify', 'woocommerce', 'medusa']
    results = {}
    
    for platform in platforms:
        try:
            result = await activity_catalog_sync(platform)
            results[platform] = result
        except Exception as e:
            logger.error(f"Failed to sync {platform}: {str(e)}")
            results[platform] = CatalogSyncResult(
                platform=platform,
                total_fetched=0,
                total_normalized=0,
                errors=[str(e)]
            )
    
    return results