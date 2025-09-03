"""Vendor integration models."""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class VendorType(str, Enum):
    """Types of vendors"""
    MANUFACTURER = "manufacturer"
    DISTRIBUTOR = "distributor"
    SUPPLIER = "supplier"
    MARKETPLACE = "marketplace"

class StockStatus(str, Enum):
    """Stock availability status"""
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"
    BACKORDER = "backorder"
    DISCONTINUED = "discontinued"

class StockInfo(BaseModel):
    """Stock information from vendor"""
    status: StockStatus = Field(..., description="Stock availability status")
    quantity_available: Optional[int] = Field(None, description="Available quantity")
    lead_time_days: Optional[int] = Field(None, description="Lead time in days")
    minimum_order_quantity: Optional[int] = Field(None, description="Minimum order quantity")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last stock update")

class LogisticsInfo(BaseModel):
    """Logistics information from vendor"""
    shipping_cost: Optional[float] = Field(None, description="Shipping cost")
    delivery_time_days: Optional[int] = Field(None, description="Delivery time in days")
    shipping_methods: List[str] = Field(default_factory=list, description="Available shipping methods")
    free_shipping_threshold: Optional[float] = Field(None, description="Free shipping threshold")
    origin_location: Optional[str] = Field(None, description="Shipping origin location")

class VendorComponent(BaseModel):
    """Component information from vendor"""
    vendor_sku: str = Field(..., description="Vendor SKU")
    vendor_name: str = Field(..., description="Vendor name")
    vendor_type: VendorType = Field(..., description="Vendor type")
    component_name: str = Field(..., description="Component name")
    manufacturer: str = Field(..., description="Manufacturer")
    model: str = Field(..., description="Model number")
    specifications: Dict[str, Any] = Field(default_factory=dict, description="Technical specifications")
    unit_price: float = Field(..., description="Unit price")
    currency: str = Field(default="USD", description="Price currency")
    stock_info: StockInfo = Field(..., description="Stock information")
    logistics_info: LogisticsInfo = Field(..., description="Logistics information")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last price update")
    data_source: str = Field(..., description="Data source identifier")

class VendorQuote(BaseModel):
    """Quote from vendor for multiple components"""
    vendor_name: str = Field(..., description="Vendor name")
    quote_id: str = Field(..., description="Quote identifier")
    components: List[VendorComponent] = Field(..., description="Quoted components")
    subtotal: float = Field(..., description="Subtotal before taxes and shipping")
    shipping_cost: float = Field(default=0.0, description="Total shipping cost")
    tax_amount: float = Field(default=0.0, description="Tax amount")
    total_amount: float = Field(..., description="Total quote amount")
    currency: str = Field(default="USD", description="Quote currency")
    valid_until: datetime = Field(..., description="Quote validity date")
    terms_conditions: Optional[str] = Field(None, description="Terms and conditions")
    created_at: datetime = Field(default_factory=datetime.now, description="Quote creation time")

class VendorCredentials(BaseModel):
    """Vendor API credentials"""
    vendor_name: str = Field(..., description="Vendor name")
    api_key: Optional[str] = Field(None, description="API key")
    api_secret: Optional[str] = Field(None, description="API secret")
    base_url: str = Field(..., description="API base URL")
    auth_type: str = Field(default="api_key", description="Authentication type")
    additional_params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")

class CacheEntry(BaseModel):
    """Cache entry for vendor data"""
    key: str = Field(..., description="Cache key")
    data: Dict[str, Any] = Field(..., description="Cached data")
    expires_at: datetime = Field(..., description="Expiration time")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")