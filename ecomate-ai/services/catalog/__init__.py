"""EcoMate Catalog Service

Provides unified catalog management across multiple e-commerce platforms
with comprehensive product normalization and synchronization capabilities.
"""

from .models import (
    ProductStatus,
    Currency,
    ProductVariant,
    ProductImage,
    ProductCategory,
    ProductAttribute,
    NormalizedProduct,
    CatalogSyncResult,
    CatalogFilter
)

from .sync import CatalogNormalizer, normalize_shopify
from .activities_catalog import activity_catalog_sync, activity_catalog_sync_all
from .router_catalog import router

# Connector imports
from .connectors import shopify, woocommerce, medusa

__all__ = [
    # Models
    'ProductStatus',
    'Currency', 
    'ProductVariant',
    'ProductImage',
    'ProductCategory',
    'ProductAttribute',
    'NormalizedProduct',
    'CatalogSyncResult',
    'CatalogFilter',
    
    # Normalization
    'CatalogNormalizer',
    'normalize_shopify',  # Legacy compatibility
    
    # Activities
    'activity_catalog_sync',
    'activity_catalog_sync_all',
    
    # Router
    'router',
    
    # Connectors
    'shopify',
    'woocommerce', 
    'medusa'
]

__version__ = '1.0.0'
__author__ = 'EcoMate AI Team'
__description__ = 'Multi-platform e-commerce catalog normalization and synchronization'