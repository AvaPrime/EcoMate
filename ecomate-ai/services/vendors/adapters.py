"""Vendor-specific adapter implementations for different suppliers."""

import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from .models import (
    VendorComponent, VendorQuote, StockInfo, LogisticsInfo, 
    VendorCredentials, StockStatus
)
from .client import BaseVendorAdapter

logger = logging.getLogger(__name__)


class GrundfosAdapter(BaseVendorAdapter):
    """Adapter for Grundfos pump and equipment API."""
    
    def __init__(self, credentials: VendorCredentials):
        super().__init__(credentials)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with authentication."""
        if self.session is None or self.session.closed:
            headers = {
                'Authorization': f'Bearer {self.credentials.api_key}',
                'Content-Type': 'application/json',
                'User-Agent': 'EcoMate-BOM-Engine/1.0'
            }
            self.session = aiohttp.ClientSession(
                base_url=self.credentials.base_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def get_component_pricing(self, component_ids: List[str]) -> List[VendorComponent]:
        """Get pricing for Grundfos components."""
        session = await self._get_session()
        components = []
        
        try:
            for component_id in component_ids:
                # Grundfos API endpoint for product pricing
                url = f'/api/v1/products/{component_id}/pricing'
                
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Parse Grundfos response format
                        component = VendorComponent(
                            vendor_name=self.credentials.vendor_name,
                            model=component_id,
                            description=data.get('description', ''),
                            unit_price=float(data.get('unit_price', 0)),
                            currency=data.get('currency', 'USD'),
                            minimum_order_qty=data.get('moq', 1),
                            lead_time_days=data.get('lead_time', 14),
                            stock_info=StockInfo(
                                status=StockStatus.IN_STOCK if data.get('in_stock') else StockStatus.LIMITED,
                                quantity_available=data.get('stock_qty', 0),
                                warehouse_location=data.get('warehouse', 'Unknown')
                            ),
                            logistics_info=LogisticsInfo(
                                shipping_cost=float(data.get('shipping_cost', 0)),
                                estimated_delivery_days=data.get('delivery_days', 7),
                                shipping_method=data.get('shipping_method', 'Standard')
                            )
                        )
                        components.append(component)
                    
                    elif response.status == 404:
                        logger.warning(f"Grundfos component {component_id} not found")
                    else:
                        logger.error(f"Grundfos API error {response.status} for {component_id}")
                        
        except Exception as e:
            logger.error(f"Error fetching Grundfos pricing: {e}")
        
        return components
    
    async def get_bulk_quote(self, items: List[Dict[str, Any]]) -> Optional[VendorQuote]:
        """Get bulk quote from Grundfos."""
        session = await self._get_session()
        
        try:
            quote_request = {
                'items': [{
                    'product_id': item['component_id'],
                    'quantity': item['quantity']
                } for item in items],
                'delivery_address': items[0].get('delivery_address', {}),
                'requested_delivery_date': (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            async with session.post('/api/v1/quotes', json=quote_request) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    return VendorQuote(
                        vendor_name=self.credentials.vendor_name,
                        quote_id=data['quote_id'],
                        total_amount=float(data['total_amount']),
                        currency=data.get('currency', 'USD'),
                        valid_until=datetime.fromisoformat(data['valid_until']),
                        items=data['line_items'],
                        terms=data.get('terms', {})
                    )
                    
        except Exception as e:
            logger.error(f"Error getting Grundfos bulk quote: {e}")
        
        return None
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


class GenericDistributorAdapter(BaseVendorAdapter):
    """Generic adapter for industrial equipment distributors."""
    
    def __init__(self, credentials: VendorCredentials):
        super().__init__(credentials)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session with authentication."""
        if self.session is None or self.session.closed:
            headers = {
                'X-API-Key': self.credentials.api_key,
                'Content-Type': 'application/json'
            }
            self.session = aiohttp.ClientSession(
                base_url=self.credentials.base_url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30)
            )
        return self.session
    
    async def get_component_pricing(self, component_ids: List[str]) -> List[VendorComponent]:
        """Get pricing from generic distributor API."""
        session = await self._get_session()
        components = []
        
        try:
            # Batch request for multiple components
            request_data = {'product_codes': component_ids}
            
            async with session.post('/api/pricing/batch', json=request_data) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    for item in data.get('products', []):
                        component = VendorComponent(
                            vendor_name=self.credentials.vendor_name,
                            model=item['product_code'],
                            description=item.get('description', ''),
                            unit_price=float(item.get('price', 0)),
                            currency=item.get('currency', 'USD'),
                            minimum_order_qty=item.get('min_qty', 1),
                            lead_time_days=item.get('lead_time_days', 7),
                            stock_info=StockInfo(
                                status=self._parse_stock_status(item.get('stock_status')),
                                quantity_available=item.get('qty_available', 0),
                                warehouse_location=item.get('warehouse', 'Main')
                            ),
                            logistics_info=LogisticsInfo(
                                shipping_cost=float(item.get('shipping_cost', 50.0)),
                                estimated_delivery_days=item.get('delivery_days', 5),
                                shipping_method=item.get('shipping_method', 'Ground')
                            )
                        )
                        components.append(component)
                        
        except Exception as e:
            logger.error(f"Error fetching distributor pricing: {e}")
        
        return components
    
    def _parse_stock_status(self, status_str: Optional[str]) -> StockStatus:
        """Parse stock status from distributor API."""
        if not status_str:
            return StockStatus.UNKNOWN
        
        status_lower = status_str.lower()
        if 'in stock' in status_lower or 'available' in status_lower:
            return StockStatus.IN_STOCK
        elif 'limited' in status_lower or 'low' in status_lower:
            return StockStatus.LIMITED
        elif 'out' in status_lower or 'unavailable' in status_lower:
            return StockStatus.OUT_OF_STOCK
        else:
            return StockStatus.UNKNOWN
    
    async def get_bulk_quote(self, items: List[Dict[str, Any]]) -> Optional[VendorQuote]:
        """Get bulk quote from distributor."""
        session = await self._get_session()
        
        try:
            quote_data = {
                'line_items': [{
                    'sku': item['component_id'],
                    'qty': item['quantity'],
                    'description': item.get('description', '')
                } for item in items],
                'shipping_address': items[0].get('delivery_address', {})
            }
            
            async with session.post('/api/quotes/create', json=quote_data) as response:
                if response.status == 201:
                    data = await response.json()
                    
                    return VendorQuote(
                        vendor_name=self.credentials.vendor_name,
                        quote_id=data['quote_number'],
                        total_amount=float(data['total']),
                        currency=data.get('currency', 'USD'),
                        valid_until=datetime.fromisoformat(data['expires_at']),
                        items=data['items'],
                        terms=data.get('terms_conditions', {})
                    )
                    
        except Exception as e:
            logger.error(f"Error getting distributor bulk quote: {e}")
        
        return None
    
    async def close(self):
        """Close HTTP session."""
        if self.session and not self.session.closed:
            await self.session.close()


class MockVendorAdapter(BaseVendorAdapter):
    """Mock adapter for testing and development."""
    
    def __init__(self, credentials: VendorCredentials):
        super().__init__(credentials)
        # Mock pricing data
        self.mock_prices = {
            'PUMP_001': 1250.00,
            'BLOWER_002': 850.00,
            'TANK_003': 2100.00,
            'MEMBRANE_004': 450.00,
            'SENSOR_005': 125.00
        }
    
    async def get_component_pricing(self, component_ids: List[str]) -> List[VendorComponent]:
        """Return mock pricing data."""
        components = []
        
        for component_id in component_ids:
            if component_id in self.mock_prices:
                component = VendorComponent(
                    vendor_name=self.credentials.vendor_name,
                    model=component_id,
                    description=f"Mock component {component_id}",
                    unit_price=self.mock_prices[component_id],
                    currency='USD',
                    minimum_order_qty=1,
                    lead_time_days=7,
                    stock_info=StockInfo(
                        status=StockStatus.IN_STOCK,
                        quantity_available=100,
                        warehouse_location='Mock Warehouse'
                    ),
                    logistics_info=LogisticsInfo(
                        shipping_cost=25.0,
                        estimated_delivery_days=3,
                        shipping_method='Express'
                    )
                )
                components.append(component)
        
        return components
    
    async def get_bulk_quote(self, items: List[Dict[str, Any]]) -> Optional[VendorQuote]:
        """Return mock bulk quote."""
        total = sum(self.mock_prices.get(item['component_id'], 100) * item['quantity'] 
                   for item in items)
        
        return VendorQuote(
            vendor_name=self.credentials.vendor_name,
            quote_id=f"MOCK-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            total_amount=total,
            currency='USD',
            valid_until=datetime.now() + timedelta(days=30),
            items=items,
            terms={'payment': '30 days', 'warranty': '1 year'}
        )
    
    async def close(self):
        """No-op for mock adapter."""
        pass