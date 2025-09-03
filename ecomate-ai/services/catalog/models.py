from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any, Union
from decimal import Decimal
from datetime import datetime
from enum import Enum

class ProductStatus(str, Enum):
    """Standardized product status across all platforms"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"
    OUT_OF_STOCK = "out_of_stock"

class Currency(str, Enum):
    """Supported currencies"""
    ZAR = "ZAR"
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"

class ProductVariant(BaseModel):
    """Normalized product variant structure"""
    id: str
    sku: Optional[str] = None
    title: Optional[str] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    inventory_quantity: Optional[int] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = "kg"
    requires_shipping: bool = True
    taxable: bool = True
    barcode: Optional[str] = None
    
    @field_validator('price', 'compare_at_price', mode='before')
    @classmethod
    def parse_price(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return Decimal(v)
            except ValueError:
                return None
        return Decimal(str(v))

class ProductImage(BaseModel):
    """Normalized product image structure"""
    id: Optional[str] = None
    src: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    position: Optional[int] = None

class ProductCategory(BaseModel):
    """Normalized product category structure"""
    id: str
    name: str
    slug: Optional[str] = None
    parent_id: Optional[str] = None

class ProductAttribute(BaseModel):
    """Normalized product attribute structure"""
    name: str
    value: Union[str, List[str]]
    visible: bool = True
    variation: bool = False

class NormalizedProduct(BaseModel):
    """Unified product structure across all e-commerce platforms"""
    # Core identifiers
    id: str
    sku: Optional[str] = None
    
    # Basic information
    title: str
    description: Optional[str] = None
    short_description: Optional[str] = None
    
    # Vendor/Brand information
    vendor: Optional[str] = None
    brand: Optional[str] = None
    
    # Pricing
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    currency: Currency = Currency.ZAR
    
    # Status and availability
    status: ProductStatus = ProductStatus.ACTIVE
    published: bool = True
    featured: bool = False
    
    # Inventory
    inventory_quantity: Optional[int] = None
    track_inventory: bool = True
    allow_backorders: bool = False
    
    # Physical properties
    weight: Optional[float] = None
    weight_unit: str = "kg"
    dimensions: Optional[Dict[str, float]] = None  # {"length": x, "width": y, "height": z}
    
    # SEO and URLs
    handle: Optional[str] = None  # URL slug
    url: Optional[str] = None
    permalink: Optional[str] = None
    
    # Media
    images: List[ProductImage] = []
    featured_image: Optional[str] = None
    
    # Categorization
    categories: List[ProductCategory] = []
    tags: List[str] = []
    
    # Variants
    variants: List[ProductVariant] = []
    has_variants: bool = False
    
    # Attributes and metadata
    attributes: List[ProductAttribute] = []
    custom_fields: Dict[str, Any] = {}
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    
    # Platform-specific data
    platform: str  # "shopify", "woocommerce", "medusa"
    platform_data: Dict[str, Any] = {}  # Store original platform-specific fields
    
    # Shipping and tax
    requires_shipping: bool = True
    taxable: bool = True
    tax_class: Optional[str] = None
    
    @field_validator('price', 'compare_at_price', mode='before')
    @classmethod
    def parse_price(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            try:
                return Decimal(v)
            except ValueError:
                return None
        return Decimal(str(v))
    
    @field_validator('images', mode='before')
    @classmethod
    def parse_images(cls, v):
        if not v:
            return []
        images = []
        for img in v:
            if isinstance(img, dict):
                images.append(ProductImage(**img))
            elif isinstance(img, str):
                images.append(ProductImage(src=img))
        return images
    
    @field_validator('categories', mode='before')
    @classmethod
    def parse_categories(cls, v):
        if not v:
            return []
        categories = []
        for cat in v:
            if isinstance(cat, dict):
                categories.append(ProductCategory(**cat))
        return categories
    
    @field_validator('variants', mode='before')
    @classmethod
    def parse_variants(cls, v):
        if not v:
            return []
        variants = []
        for variant in v:
            if isinstance(variant, dict):
                variants.append(ProductVariant(**variant))
        return variants
    
    @property
    def primary_image(self) -> Optional[str]:
        """Get the primary product image URL"""
        if self.featured_image:
            return self.featured_image
        if self.images:
            return self.images[0].src
        return None
    
    @property
    def display_price(self) -> Optional[Decimal]:
        """Get the display price (from variants if no main price)"""
        if self.price is not None:
            return self.price
        if self.variants:
            prices = [v.price for v in self.variants if v.price is not None]
            if prices:
                return min(prices)
        return None
    
    @property
    def price_range(self) -> Optional[Dict[str, Decimal]]:
        """Get price range for products with variants"""
        if not self.variants:
            return None
        prices = [v.price for v in self.variants if v.price is not None]
        if not prices:
            return None
        return {"min": min(prices), "max": max(prices)}

class CatalogSyncResult(BaseModel):
    """Result of catalog synchronization"""
    platform: str
    total_fetched: int
    total_normalized: int
    errors: List[str] = []
    warnings: List[str] = []
    sync_timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None

class CatalogFilter(BaseModel):
    """Filter options for catalog queries"""
    platform: Optional[str] = None
    status: Optional[ProductStatus] = None
    vendor: Optional[str] = None
    category: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    has_stock: Optional[bool] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0