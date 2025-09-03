"""Comprehensive tests for catalog normalization system"""

import pytest
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock

from .models import (
    ProductStatus, Currency, ProductVariant, ProductImage, 
    ProductCategory, ProductAttribute, NormalizedProduct,
    CatalogSyncResult, CatalogFilter
)
from .sync import CatalogNormalizer
from .activities_catalog import activity_catalog_sync, activity_catalog_sync_all


class TestModels:
    """Test catalog data models"""
    
    def test_product_status_enum(self):
        """Test ProductStatus enum values"""
        assert ProductStatus.ACTIVE == "active"
        assert ProductStatus.DRAFT == "draft"
        assert ProductStatus.ARCHIVED == "archived"
    
    def test_currency_enum(self):
        """Test Currency enum values"""
        assert Currency.USD == "USD"
        assert Currency.EUR == "EUR"
        assert Currency.GBP == "GBP"
    
    def test_product_variant_creation(self):
        """Test ProductVariant model creation"""
        variant = ProductVariant(
            id="var_123",
            title="Small Red",
            price=Decimal("29.99"),
            sku="SKU-001",
            inventory_quantity=10,
            weight=Decimal("0.5")
        )
        assert variant.id == "var_123"
        assert variant.price == Decimal("29.99")
        assert variant.inventory_quantity == 10
    
    def test_normalized_product_creation(self):
        """Test NormalizedProduct model creation"""
        product = NormalizedProduct(
            id="prod_123",
            title="Test Product",
            handle="test-product",
            status=ProductStatus.ACTIVE,
            price=Decimal("99.99"),
            currency=Currency.USD,
            inventory_quantity=50,
            platform="shopify",
            platform_id="shopify_123"
        )
        assert product.id == "prod_123"
        assert product.status == ProductStatus.ACTIVE
        assert product.currency == Currency.USD
    
    def test_catalog_sync_result(self):
        """Test CatalogSyncResult model"""
        result = CatalogSyncResult(
            platform="shopify",
            total_fetched=100,
            total_normalized=95,
            errors=["Error 1"],
            warnings=["Warning 1"],
            duration_seconds=45.2
        )
        assert result.platform == "shopify"
        assert result.success_rate == 0.95
        assert len(result.errors) == 1


class TestCatalogNormalizer:
    """Test catalog normalization functionality"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.normalizer = CatalogNormalizer()
    
    def test_normalize_shopify_product(self):
        """Test Shopify product normalization"""
        shopify_data = {
            "id": 123456789,
            "title": "Test Product",
            "handle": "test-product",
            "status": "active",
            "vendor": "Test Vendor",
            "product_type": "Electronics",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-02T00:00:00Z",
            "published_at": "2023-01-01T12:00:00Z",
            "body_html": "<p>Test description</p>",
            "tags": "tag1,tag2,tag3",
            "variants": [{
                "id": 987654321,
                "title": "Default Title",
                "price": "99.99",
                "compare_at_price": "129.99",
                "sku": "TEST-SKU-001",
                "inventory_quantity": 25,
                "weight": 500,
                "weight_unit": "g"
            }],
            "images": [{
                "id": 111222333,
                "src": "https://example.com/image.jpg",
                "alt": "Product image",
                "position": 1
            }],
            "options": [{
                "id": 444555666,
                "name": "Size",
                "values": ["Small", "Medium", "Large"]
            }]
        }
        
        result = self.normalizer.normalize_shopify(shopify_data)
        
        assert result.id == "shopify_123456789"
        assert result.title == "Test Product"
        assert result.handle == "test-product"
        assert result.status == ProductStatus.ACTIVE
        assert result.platform == "shopify"
        assert result.platform_id == "123456789"
        assert result.vendor == "Test Vendor"
        assert result.product_type == "Electronics"
        assert result.price == Decimal("99.99")
        assert result.compare_at_price == Decimal("129.99")
        assert result.currency == Currency.USD
        assert result.inventory_quantity == 25
        assert len(result.variants) == 1
        assert len(result.images) == 1
        assert len(result.tags) == 3
    
    def test_normalize_woocommerce_product(self):
        """Test WooCommerce product normalization"""
        woocommerce_data = {
            "id": 456,
            "name": "WooCommerce Product",
            "slug": "woocommerce-product",
            "status": "publish",
            "type": "simple",
            "description": "Product description",
            "short_description": "Short desc",
            "sku": "WOO-SKU-001",
            "price": "49.99",
            "regular_price": "49.99",
            "sale_price": "39.99",
            "stock_quantity": 15,
            "weight": "0.3",
            "categories": [{
                "id": 789,
                "name": "Electronics",
                "slug": "electronics"
            }],
            "tags": [{
                "id": 101,
                "name": "Popular",
                "slug": "popular"
            }],
            "images": [{
                "id": 202,
                "src": "https://example.com/woo-image.jpg",
                "alt": "WooCommerce image"
            }],
            "attributes": [{
                "id": 303,
                "name": "Color",
                "options": ["Red", "Blue", "Green"]
            }],
            "date_created": "2023-01-01T00:00:00",
            "date_modified": "2023-01-02T00:00:00"
        }
        
        result = self.normalizer.normalize_woocommerce(woocommerce_data)
        
        assert result.id == "woocommerce_456"
        assert result.title == "WooCommerce Product"
        assert result.handle == "woocommerce-product"
        assert result.status == ProductStatus.ACTIVE
        assert result.platform == "woocommerce"
        assert result.platform_id == "456"
        assert result.price == Decimal("39.99")  # Sale price takes precedence
        assert result.compare_at_price == Decimal("49.99")
        assert result.inventory_quantity == 15
        assert len(result.categories) == 1
        assert len(result.images) == 1
    
    def test_normalize_medusa_product(self):
        """Test Medusa product normalization"""
        medusa_data = {
            "id": "prod_medusa_123",
            "title": "Medusa Product",
            "handle": "medusa-product",
            "status": "published",
            "description": "Medusa description",
            "type": {"value": "physical"},
            "collection": {"title": "Main Collection"},
            "variants": [{
                "id": "variant_456",
                "title": "Default",
                "sku": "MED-SKU-001",
                "inventory_quantity": 30,
                "weight": 200,
                "prices": [{
                    "amount": 7999,
                    "currency_code": "usd"
                }]
            }],
            "images": [{
                "id": "img_789",
                "url": "https://example.com/medusa-image.jpg"
            }],
            "tags": [{"value": "premium"}, {"value": "featured"}],
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-02T00:00:00.000Z"
        }
        
        result = self.normalizer.normalize_medusa(medusa_data)
        
        assert result.id == "medusa_prod_medusa_123"
        assert result.title == "Medusa Product"
        assert result.handle == "medusa-product"
        assert result.status == ProductStatus.ACTIVE
        assert result.platform == "medusa"
        assert result.platform_id == "prod_medusa_123"
        assert result.price == Decimal("79.99")
        assert result.inventory_quantity == 30
        assert len(result.variants) == 1
        assert len(result.images) == 1
        assert len(result.tags) == 2
    
    def test_normalize_products_dispatch(self):
        """Test normalize_products method dispatching"""
        shopify_data = [{"id": 123, "title": "Test", "status": "active"}]
        
        results = self.normalizer.normalize_products(shopify_data, "shopify")
        assert len(results) == 1
        assert results[0].platform == "shopify"
        
        # Test invalid platform
        with pytest.raises(ValueError, match="Unsupported platform"):
            self.normalizer.normalize_products(shopify_data, "invalid")
    
    def test_status_mapping(self):
        """Test status mapping across platforms"""
        # Shopify status mapping
        assert self.normalizer._map_shopify_status("active") == ProductStatus.ACTIVE
        assert self.normalizer._map_shopify_status("draft") == ProductStatus.DRAFT
        assert self.normalizer._map_shopify_status("archived") == ProductStatus.ARCHIVED
        
        # WooCommerce status mapping
        assert self.normalizer._map_woocommerce_status("publish") == ProductStatus.ACTIVE
        assert self.normalizer._map_woocommerce_status("draft") == ProductStatus.DRAFT
        assert self.normalizer._map_woocommerce_status("private") == ProductStatus.ARCHIVED
        
        # Medusa status mapping
        assert self.normalizer._map_medusa_status("published") == ProductStatus.ACTIVE
        assert self.normalizer._map_medusa_status("draft") == ProductStatus.DRAFT
        assert self.normalizer._map_medusa_status("rejected") == ProductStatus.ARCHIVED


class TestCatalogActivities:
    """Test catalog sync activities"""
    
    @pytest.mark.asyncio
    async def test_activity_catalog_sync_shopify(self):
        """Test single platform catalog sync"""
        mock_products = [{
            "id": 123,
            "title": "Test Product",
            "status": "active",
            "variants": [{
                "id": 456,
                "title": "Default",
                "price": "99.99",
                "inventory_quantity": 10
            }]
        }]
        
        with patch('services.catalog.activities_catalog.shopify.fetch_products', 
                  new_callable=AsyncMock, return_value=mock_products), \
             patch('services.catalog.activities_catalog.open_pr') as mock_pr:
            
            result = await activity_catalog_sync("shopify")
            
            assert isinstance(result, CatalogSyncResult)
            assert result.platform == "shopify"
            assert result.total_fetched == 1
            assert result.total_normalized == 1
            assert len(result.errors) == 0
            mock_pr.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_activity_catalog_sync_invalid_platform(self):
        """Test sync with invalid platform"""
        result = await activity_catalog_sync("invalid_platform")
        
        assert isinstance(result, CatalogSyncResult)
        assert result.platform == "invalid_platform"
        assert result.total_fetched == 0
        assert result.total_normalized == 0
        assert len(result.errors) > 0
        assert "Unsupported platform" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_activity_catalog_sync_no_products(self):
        """Test sync when no products are fetched"""
        with patch('services.catalog.activities_catalog.shopify.fetch_products', 
                  new_callable=AsyncMock, return_value=[]):
            
            result = await activity_catalog_sync("shopify")
            
            assert result.total_fetched == 0
            assert result.total_normalized == 0
            assert len(result.warnings) > 0
            assert "No products fetched" in result.warnings[0]
    
    @pytest.mark.asyncio
    async def test_activity_catalog_sync_all(self):
        """Test syncing all platforms"""
        mock_products = [{
            "id": 123,
            "title": "Test Product",
            "status": "active",
            "variants": [{"id": 456, "title": "Default", "price": "99.99"}]
        }]
        
        with patch('services.catalog.activities_catalog.shopify.fetch_products', 
                  new_callable=AsyncMock, return_value=mock_products), \
             patch('services.catalog.activities_catalog.woocommerce.fetch_products', 
                  new_callable=AsyncMock, return_value=mock_products), \
             patch('services.catalog.activities_catalog.medusa.fetch_products', 
                  new_callable=AsyncMock, return_value=mock_products), \
             patch('services.catalog.activities_catalog.open_pr'):
            
            results = await activity_catalog_sync_all()
            
            assert len(results) == 3
            assert "shopify" in results
            assert "woocommerce" in results
            assert "medusa" in results
            
            for platform, result in results.items():
                assert isinstance(result, CatalogSyncResult)
                assert result.platform == platform
                assert result.total_fetched == 1
                assert result.total_normalized == 1


class TestCatalogIntegration:
    """Integration tests for catalog system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_normalization(self):
        """Test complete normalization pipeline"""
        # Mock data from different platforms
        shopify_data = [{
            "id": 123,
            "title": "Shopify Product",
            "status": "active",
            "variants": [{"id": 456, "price": "99.99", "inventory_quantity": 10}]
        }]
        
        woocommerce_data = [{
            "id": 789,
            "name": "WooCommerce Product",
            "status": "publish",
            "price": "49.99",
            "stock_quantity": 5
        }]
        
        normalizer = CatalogNormalizer()
        
        # Test normalization
        shopify_normalized = normalizer.normalize_products(shopify_data, "shopify")
        woocommerce_normalized = normalizer.normalize_products(woocommerce_data, "woocommerce")
        
        # Verify consistent structure
        assert len(shopify_normalized) == 1
        assert len(woocommerce_normalized) == 1
        
        shopify_product = shopify_normalized[0]
        woocommerce_product = woocommerce_normalized[0]
        
        # Both should have consistent fields
        for product in [shopify_product, woocommerce_product]:
            assert hasattr(product, 'id')
            assert hasattr(product, 'title')
            assert hasattr(product, 'status')
            assert hasattr(product, 'platform')
            assert hasattr(product, 'price')
            assert hasattr(product, 'currency')
            assert isinstance(product.status, ProductStatus)
            assert isinstance(product.currency, Currency)
    
    def test_catalog_filter_model(self):
        """Test CatalogFilter functionality"""
        filter_obj = CatalogFilter(
            platforms=["shopify", "woocommerce"],
            status=[ProductStatus.ACTIVE],
            min_price=Decimal("10.00"),
            max_price=Decimal("100.00"),
            categories=["Electronics"],
            tags=["featured"]
        )
        
        assert len(filter_obj.platforms) == 2
        assert ProductStatus.ACTIVE in filter_obj.status
        assert filter_obj.min_price == Decimal("10.00")
        assert "Electronics" in filter_obj.categories


if __name__ == "__main__":
    pytest.main([__file__, "-v"])