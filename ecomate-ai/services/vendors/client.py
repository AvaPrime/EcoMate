"""Vendor client abstraction for live pricing, stock, and logistics data."""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import aiohttp
import json
from .models import VendorComponent, VendorQuote, StockInfo, LogisticsInfo, VendorCredentials, CacheEntry
from .cache import VendorCache

logger = logging.getLogger(__name__)

class BaseVendorAdapter(ABC):
    """Base class for vendor-specific adapters"""
    
    def __init__(self, credentials: VendorCredentials):
        self.credentials = credentials
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    @abstractmethod
    async def get_component_pricing(self, component_ids: List[str]) -> List[VendorComponent]:
        """Get pricing for components"""
        pass
    
    @abstractmethod
    async def get_stock_info(self, component_ids: List[str]) -> Dict[str, StockInfo]:
        """Get stock information for components"""
        pass
    
    @abstractmethod
    async def get_logistics_info(self, component_ids: List[str], destination: str) -> Dict[str, LogisticsInfo]:
        """Get logistics information for components"""
        pass
    
    @abstractmethod
    async def request_quote(self, component_quantities: Dict[str, int], destination: str) -> VendorQuote:
        """Request a formal quote from vendor"""
        pass

class GrundfosAdapter(BaseVendorAdapter):
    """Grundfos vendor adapter"""
    
    async def get_component_pricing(self, component_ids: List[str]) -> List[VendorComponent]:
        # Mock implementation - replace with actual Grundfos API calls
        components = []
        for comp_id in component_ids:
            if "pump" in comp_id.lower():
                components.append(VendorComponent(
                    vendor_sku=f"GF-{comp_id}",
                    vendor_name="Grundfos",
                    vendor_type="manufacturer",
                    component_name=f"Grundfos Pump {comp_id}",
                    manufacturer="Grundfos",
                    model=comp_id,
                    unit_price=2500.0,
                    stock_info=StockInfo(status="in_stock", quantity_available=10, lead_time_days=7),
                    logistics_info=LogisticsInfo(shipping_cost=150.0, delivery_time_days=5),
                    data_source="grundfos_api"
                ))
        return components
    
    async def get_stock_info(self, component_ids: List[str]) -> Dict[str, StockInfo]:
        return {comp_id: StockInfo(status="in_stock", quantity_available=10, lead_time_days=7) 
                for comp_id in component_ids}
    
    async def get_logistics_info(self, component_ids: List[str], destination: str) -> Dict[str, LogisticsInfo]:
        return {comp_id: LogisticsInfo(shipping_cost=150.0, delivery_time_days=5) 
                for comp_id in component_ids}
    
    async def request_quote(self, component_quantities: Dict[str, int], destination: str) -> VendorQuote:
        components = await self.get_component_pricing(list(component_quantities.keys()))
        subtotal = sum(comp.unit_price * component_quantities.get(comp.vendor_sku.split('-')[1], 1) 
                      for comp in components)
        return VendorQuote(
            vendor_name="Grundfos",
            quote_id=f"GF-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            components=components,
            subtotal=subtotal,
            shipping_cost=200.0,
            total_amount=subtotal + 200.0,
            valid_until=datetime.now() + timedelta(days=30)
        )

class GenericDistributorAdapter(BaseVendorAdapter):
    """Generic distributor adapter for common APIs"""
    
    async def get_component_pricing(self, component_ids: List[str]) -> List[VendorComponent]:
        # Mock implementation - replace with actual distributor API calls
        components = []
        for comp_id in component_ids:
            components.append(VendorComponent(
                vendor_sku=f"DIST-{comp_id}",
                vendor_name=self.credentials.vendor_name,
                vendor_type="distributor",
                component_name=f"Component {comp_id}",
                manufacturer="Various",
                model=comp_id,
                unit_price=1800.0,  # Typically lower than manufacturer direct
                stock_info=StockInfo(status="in_stock", quantity_available=25, lead_time_days=3),
                logistics_info=LogisticsInfo(shipping_cost=100.0, delivery_time_days=3),
                data_source=f"{self.credentials.vendor_name}_api"
            ))
        return components
    
    async def get_stock_info(self, component_ids: List[str]) -> Dict[str, StockInfo]:
        return {comp_id: StockInfo(status="in_stock", quantity_available=25, lead_time_days=3) 
                for comp_id in component_ids}
    
    async def get_logistics_info(self, component_ids: List[str], destination: str) -> Dict[str, LogisticsInfo]:
        return {comp_id: LogisticsInfo(shipping_cost=100.0, delivery_time_days=3) 
                for comp_id in component_ids}
    
    async def request_quote(self, component_quantities: Dict[str, int], destination: str) -> VendorQuote:
        components = await self.get_component_pricing(list(component_quantities.keys()))
        subtotal = sum(comp.unit_price * component_quantities.get(comp.vendor_sku.split('-')[1], 1) 
                      for comp in components)
        return VendorQuote(
            vendor_name=self.credentials.vendor_name,
            quote_id=f"DIST-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            components=components,
            subtotal=subtotal,
            shipping_cost=150.0,
            total_amount=subtotal + 150.0,
            valid_until=datetime.now() + timedelta(days=15)
        )

class VendorClient:
    """Main vendor client for aggregating data from multiple vendors"""
    
    def __init__(self):
        self.adapters: Dict[str, BaseVendorAdapter] = {}
        self.cache = VendorCache()
        self.fallback_enabled = True
    
    def register_adapter(self, vendor_name: str, adapter: BaseVendorAdapter):
        """Register a vendor adapter"""
        self.adapters[vendor_name] = adapter
    
    async def get_best_pricing(self, component_ids: List[str], destination: str = "default") -> List[VendorComponent]:
        """Get best pricing across all registered vendors"""
        cache_key = f"pricing:{':'.join(component_ids)}:{destination}"
        
        # Check cache first
        cached_data = await self.cache.get(cache_key)
        if cached_data:
            logger.info(f"Using cached pricing data for {len(component_ids)} components")
            return [VendorComponent(**comp) for comp in cached_data]
        
        all_components = []
        
        # Query all vendors concurrently
        tasks = []
        for vendor_name, adapter in self.adapters.items():
            tasks.append(self._safe_get_pricing(vendor_name, adapter, component_ids))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Vendor query failed: {result}")
                continue
            if result:
                all_components.extend(result)
        
        # Select best pricing for each component
        best_components = self._select_best_components(all_components)
        
        # Cache results for 1 hour
        await self.cache.set(cache_key, [comp.model_dump() for comp in best_components], ttl_seconds=3600)
        
        return best_components
    
    async def _safe_get_pricing(self, vendor_name: str, adapter: BaseVendorAdapter, component_ids: List[str]) -> List[VendorComponent]:
        """Safely get pricing from a vendor adapter"""
        try:
            async with adapter:
                return await adapter.get_component_pricing(component_ids)
        except Exception as e:
            logger.error(f"Failed to get pricing from {vendor_name}: {e}")
            if self.fallback_enabled:
                return self._get_fallback_pricing(component_ids, vendor_name)
            return []
    
    def _get_fallback_pricing(self, component_ids: List[str], vendor_name: str) -> List[VendorComponent]:
        """Get fallback pricing when vendor API fails"""
        fallback_components = []
        for comp_id in component_ids:
            fallback_components.append(VendorComponent(
                vendor_sku=f"FALLBACK-{comp_id}",
                vendor_name=f"{vendor_name} (cached)",
                vendor_type="distributor",
                component_name=f"Fallback Component {comp_id}",
                manufacturer="Unknown",
                model=comp_id,
                unit_price=2000.0,  # Conservative fallback price
                stock_info=StockInfo(status="backorder", lead_time_days=14),
                logistics_info=LogisticsInfo(shipping_cost=200.0, delivery_time_days=7),
                data_source="fallback_cache"
            ))
        return fallback_components
    
    def _select_best_components(self, all_components: List[VendorComponent]) -> List[VendorComponent]:
        """Select best components based on price, availability, and delivery time"""
        component_groups = {}
        
        # Group components by model/type
        for comp in all_components:
            key = comp.model
            if key not in component_groups:
                component_groups[key] = []
            component_groups[key].append(comp)
        
        best_components = []
        for model, components in component_groups.items():
            # Score components based on multiple factors
            scored_components = []
            for comp in components:
                score = self._calculate_component_score(comp)
                scored_components.append((score, comp))
            
            # Select highest scoring component
            scored_components.sort(key=lambda x: x[0], reverse=True)
            best_components.append(scored_components[0][1])
        
        return best_components
    
    def _calculate_component_score(self, component: VendorComponent) -> float:
        """Calculate component score based on price, availability, and delivery"""
        score = 0.0
        
        # Price factor (lower is better, normalized)
        price_factor = max(0, 1000 - component.unit_price) / 1000
        score += price_factor * 0.4
        
        # Stock availability factor
        stock_scores = {
            "in_stock": 1.0,
            "low_stock": 0.7,
            "backorder": 0.3,
            "out_of_stock": 0.0,
            "discontinued": 0.0
        }
        score += stock_scores.get(component.stock_info.status, 0.0) * 0.3
        
        # Delivery time factor (faster is better)
        delivery_days = component.logistics_info.delivery_time_days or 14
        delivery_factor = max(0, 1 - (delivery_days / 30))  # Normalize to 30 days
        score += delivery_factor * 0.2
        
        # Vendor type preference (manufacturers often have better support)
        vendor_scores = {
            "manufacturer": 1.0,
            "distributor": 0.8,
            "supplier": 0.6,
            "marketplace": 0.4
        }
        score += vendor_scores.get(component.vendor_type, 0.5) * 0.1
        
        return score
    
    async def get_aggregated_quote(self, component_quantities: Dict[str, int], destination: str = "default") -> Dict[str, Any]:
        """Get aggregated quote from best vendors for each component"""
        component_ids = list(component_quantities.keys())
        best_components = await self.get_best_pricing(component_ids, destination)
        
        total_cost = 0.0
        total_shipping = 0.0
        quote_items = []
        
        for component in best_components:
            quantity = component_quantities.get(component.model, 1)
            line_total = component.unit_price * quantity
            shipping_cost = component.logistics_info.shipping_cost or 0.0
            
            total_cost += line_total
            total_shipping += shipping_cost
            
            quote_items.append({
                "sku": component.vendor_sku,
                "description": component.component_name,
                "qty": quantity,
                "unit_price": component.unit_price,
                "line_total": line_total,
                "vendor": component.vendor_name,
                "lead_time_days": component.stock_info.lead_time_days,
                "delivery_days": component.logistics_info.delivery_time_days
            })
        
        return {
            "items": quote_items,
            "subtotal": total_cost,
            "shipping": total_shipping,
            "total": total_cost + total_shipping,
            "currency": "USD",
            "generated_at": datetime.now().isoformat()
        }