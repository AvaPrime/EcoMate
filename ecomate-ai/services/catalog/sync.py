from typing import List, Dict, Any
from decimal import Decimal
from datetime import datetime
import logging
from .models import (
    NormalizedProduct, ProductStatus, Currency, ProductImage, 
    ProductCategory, ProductVariant, ProductAttribute
)

logger = logging.getLogger(__name__)

class CatalogNormalizer:
    """Unified catalog normalization engine for all e-commerce platforms"""
    
    @staticmethod
    def normalize_shopify(products: List[Dict[str, Any]]) -> List[NormalizedProduct]:
        """Normalize Shopify products to unified structure"""
        normalized = []
        errors = []
        
        for product in products:
            try:
                # Extract basic information
                product_id = str(product.get('id', ''))
                title = product.get('title', '')
                
                if not product_id or not title:
                    errors.append(f"Missing required fields for product: {product}")
                    continue
                
                # Handle variants
                variants = []
                shopify_variants = product.get('variants', [])
                main_price = None
                main_sku = None
                
                for variant in shopify_variants:
                    variant_data = ProductVariant(
                        id=str(variant.get('id', '')),
                        sku=variant.get('sku'),
                        title=variant.get('title'),
                        price=variant.get('price'),
                        compare_at_price=variant.get('compare_at_price'),
                        inventory_quantity=variant.get('inventory_quantity'),
                        weight=variant.get('weight'),
                        weight_unit=variant.get('weight_unit', 'kg'),
                        requires_shipping=variant.get('requires_shipping', True),
                        taxable=variant.get('taxable', True),
                        barcode=variant.get('barcode')
                    )
                    variants.append(variant_data)
                    
                    # Use first variant for main product data
                    if main_price is None and variant_data.price:
                        main_price = variant_data.price
                    if main_sku is None and variant_data.sku:
                        main_sku = variant_data.sku
                
                # Handle images
                images = []
                for img in product.get('images', []):
                    images.append(ProductImage(
                        id=str(img.get('id', '')),
                        src=img.get('src', ''),
                        alt=img.get('alt'),
                        width=img.get('width'),
                        height=img.get('height'),
                        position=img.get('position')
                    ))
                
                # Map status
                status_map = {
                    'active': ProductStatus.ACTIVE,
                    'draft': ProductStatus.DRAFT,
                    'archived': ProductStatus.ARCHIVED
                }
                status = status_map.get(product.get('status', 'active'), ProductStatus.ACTIVE)
                
                # Parse timestamps
                created_at = None
                updated_at = None
                published_at = None
                
                try:
                    if product.get('created_at'):
                        created_at = datetime.fromisoformat(product['created_at'].replace('Z', '+00:00'))
                    if product.get('updated_at'):
                        updated_at = datetime.fromisoformat(product['updated_at'].replace('Z', '+00:00'))
                    if product.get('published_at'):
                        published_at = datetime.fromisoformat(product['published_at'].replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse timestamps for product {product_id}: {e}")
                
                normalized_product = NormalizedProduct(
                    id=product_id,
                    sku=main_sku or product.get('id'),
                    title=title,
                    description=product.get('body_html'),
                    vendor=product.get('vendor'),
                    price=main_price,
                    currency=Currency.ZAR,
                    status=status,
                    published=product.get('published_at') is not None,
                    handle=product.get('handle'),
                    images=images,
                    variants=variants,
                    has_variants=len(variants) > 1,
                    tags=product.get('tags', '').split(',') if product.get('tags') else [],
                    created_at=created_at,
                    updated_at=updated_at,
                    published_at=published_at,
                    platform="shopify",
                    platform_data=product,
                    requires_shipping=True,
                    taxable=True
                )
                
                normalized.append(normalized_product)
                
            except (KeyError, TypeError, ValueError) as e:
                error_msg = f"Failed to normalize Shopify product {product.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        return normalized
    
    @staticmethod
    def normalize_woocommerce(products: List[Dict[str, Any]]) -> List[NormalizedProduct]:
        """Normalize WooCommerce products to unified structure"""
        normalized = []
        errors = []
        
        for product in products:
            try:
                # Extract basic information
                product_id = str(product.get('id', ''))
                title = product.get('name', '')
                
                if not product_id or not title:
                    errors.append(f"Missing required fields for WooCommerce product: {product}")
                    continue
                
                # Handle variants (WooCommerce variations)
                variants = []
                if product.get('type') == 'variable' and product.get('variations'):
                    # Note: WooCommerce API returns variation IDs, not full data
                    # In a real implementation, you'd fetch variation details separately
                    for variation_id in product.get('variations', []):
                        variants.append(ProductVariant(
                            id=str(variation_id),
                            sku=None,  # Would need separate API call
                            title=None,
                            price=None
                        ))
                
                # Handle main product pricing
                price = None
                if product.get('price'):
                    try:
                        price = Decimal(str(product['price']))
                    except ValueError:
                        pass
                
                # Handle images
                images = []
                for img in product.get('images', []):
                    images.append(ProductImage(
                        id=str(img.get('id', '')),
                        src=img.get('src', ''),
                        alt=img.get('alt'),
                        position=img.get('position')
                    ))
                
                # Handle categories
                categories = []
                for cat in product.get('categories', []):
                    categories.append(ProductCategory(
                        id=str(cat.get('id', '')),
                        name=cat.get('name', ''),
                        slug=cat.get('slug')
                    ))
                
                # Handle attributes
                attributes = []
                for attr in product.get('attributes', []):
                    attributes.append(ProductAttribute(
                        name=attr.get('name', ''),
                        value=attr.get('options', []),
                        visible=attr.get('visible', True),
                        variation=attr.get('variation', False)
                    ))
                
                # Map status
                status_map = {
                    'publish': ProductStatus.ACTIVE,
                    'draft': ProductStatus.DRAFT,
                    'private': ProductStatus.INACTIVE,
                    'pending': ProductStatus.DRAFT
                }
                status = status_map.get(product.get('status', 'publish'), ProductStatus.ACTIVE)
                
                # Parse timestamps
                created_at = None
                updated_at = None
                
                try:
                    if product.get('date_created'):
                        created_at = datetime.fromisoformat(product['date_created'].replace('Z', '+00:00'))
                    if product.get('date_modified'):
                        updated_at = datetime.fromisoformat(product['date_modified'].replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse timestamps for WooCommerce product {product_id}: {e}")
                
                normalized_product = NormalizedProduct(
                    id=product_id,
                    sku=product.get('sku'),
                    title=title,
                    description=product.get('description'),
                    short_description=product.get('short_description'),
                    price=price,
                    currency=Currency.ZAR,
                    status=status,
                    published=product.get('status') == 'publish',
                    featured=product.get('featured', False),
                    inventory_quantity=product.get('stock_quantity'),
                    track_inventory=product.get('manage_stock', False),
                    weight=product.get('weight'),
                    dimensions={
                        'length': product.get('dimensions', {}).get('length'),
                        'width': product.get('dimensions', {}).get('width'),
                        'height': product.get('dimensions', {}).get('height')
                    } if product.get('dimensions') else None,
                    permalink=product.get('permalink'),
                    images=images,
                    categories=categories,
                    tags=[tag.get('name', '') for tag in product.get('tags', [])],
                    variants=variants,
                    has_variants=product.get('type') == 'variable',
                    attributes=attributes,
                    created_at=created_at,
                    updated_at=updated_at,
                    platform="woocommerce",
                    platform_data=product,
                    requires_shipping=product.get('shipping_required', True),
                    taxable=product.get('tax_status') == 'taxable',
                    tax_class=product.get('tax_class')
                )
                
                normalized.append(normalized_product)
                
            except (KeyError, TypeError, ValueError) as e:
                error_msg = f"Failed to normalize WooCommerce product {product.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        return normalized
    
    @staticmethod
    def normalize_medusa(products: List[Dict[str, Any]]) -> List[NormalizedProduct]:
        """Normalize Medusa products to unified structure"""
        normalized = []
        errors = []
        
        for product in products:
            try:
                # Extract basic information
                product_id = str(product.get('id', ''))
                title = product.get('title', '')
                
                if not product_id or not title:
                    errors.append(f"Missing required fields for Medusa product: {product}")
                    continue
                
                # Handle variants
                variants = []
                for variant in product.get('variants', []):
                    # Get prices from variant
                    variant_price = None
                    if variant.get('prices'):
                        # Medusa stores prices per currency/region
                        for price_obj in variant['prices']:
                            if price_obj.get('currency_code') == 'zar':  # Prefer ZAR
                                variant_price = Decimal(str(price_obj['amount'])) / 100  # Medusa stores in cents
                                break
                        if not variant_price and variant['prices']:  # Fallback to first price
                            price_obj = variant['prices'][0]
                            variant_price = Decimal(str(price_obj['amount'])) / 100
                    
                    variants.append(ProductVariant(
                        id=str(variant.get('id', '')),
                        sku=variant.get('sku'),
                        title=variant.get('title'),
                        price=variant_price,
                        inventory_quantity=variant.get('inventory_quantity'),
                        weight=variant.get('weight'),
                        requires_shipping=True,
                        taxable=True,
                        barcode=variant.get('barcode')
                    ))
                
                # Get main price from first variant
                main_price = None
                if variants and variants[0].price:
                    main_price = variants[0].price
                
                # Handle images
                images = []
                for img in product.get('images', []):
                    images.append(ProductImage(
                        id=str(img.get('id', '')),
                        src=img.get('url', ''),
                        alt=None
                    ))
                
                # Map status
                status_map = {
                    'published': ProductStatus.ACTIVE,
                    'draft': ProductStatus.DRAFT,
                    'proposed': ProductStatus.DRAFT,
                    'rejected': ProductStatus.INACTIVE
                }
                status = status_map.get(product.get('status', 'draft'), ProductStatus.DRAFT)
                
                # Parse timestamps
                created_at = None
                updated_at = None
                
                try:
                    if product.get('created_at'):
                        created_at = datetime.fromisoformat(product['created_at'].replace('Z', '+00:00'))
                    if product.get('updated_at'):
                        updated_at = datetime.fromisoformat(product['updated_at'].replace('Z', '+00:00'))
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse timestamps for Medusa product {product_id}: {e}")
                
                normalized_product = NormalizedProduct(
                    id=product_id,
                    sku=variants[0].sku if variants else None,
                    title=title,
                    description=product.get('description'),
                    price=main_price,
                    currency=Currency.ZAR,
                    status=status,
                    published=product.get('status') == 'published',
                    handle=product.get('handle'),
                    images=images,
                    variants=variants,
                    has_variants=len(variants) > 1,
                    tags=[tag.get('value', '') for tag in product.get('tags', [])],
                    created_at=created_at,
                    updated_at=updated_at,
                    platform="medusa",
                    platform_data=product,
                    requires_shipping=True,
                    taxable=True
                )
                
                normalized.append(normalized_product)
                
            except (KeyError, TypeError, ValueError) as e:
                error_msg = f"Failed to normalize Medusa product {product.get('id', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue
        
        return normalized
    
    @classmethod
    def normalize_products(cls, products: List[Dict[str, Any]], platform: str) -> List[NormalizedProduct]:
        """Normalize products from any platform"""
        if platform == 'shopify':
            return cls.normalize_shopify(products)
        elif platform == 'woocommerce':
            return cls.normalize_woocommerce(products)
        elif platform == 'medusa':
            return cls.normalize_medusa(products)
        else:
            raise ValueError(f"Unsupported platform: {platform}")

# Legacy compatibility
FIELDS = ["sku", "title", "vendor", "price", "currency", "status", "url", "image"]

def normalize_shopify(products: list[dict]) -> list[dict]:
    """Legacy function for backward compatibility"""
    normalizer = CatalogNormalizer()
    normalized_products = normalizer.normalize_shopify(products)
    
    # Convert to legacy format
    legacy_format = []
    for product in normalized_products:
        legacy_format.append({
            "sku": product.sku,
            "title": product.title,
            "vendor": product.vendor,
            "price": str(product.display_price) if product.display_price else None,
            "currency": product.currency.value,
            "status": product.status.value,
            "url": product.handle,
            "image": product.primary_image
        })
    
    return legacy_format