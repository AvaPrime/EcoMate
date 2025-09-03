import os
from typing import List, Dict, Any, Optional
from .models import BOMItem, Quote, SystemSpec
from .bom_engine import base_bom_for, base_bom_for_with_vendors, setup_vendor_client
from ..vendors.client import VendorClient

LABOUR_RATE = float(os.getenv('LABOUR_RATE_ZAR', '450'))
LOGI_RATE = float(os.getenv('LOGISTICS_RATE_ZAR_PER_KM', '18'))
MARGIN = float(os.getenv('DEFAULT_MARGIN', '0.18'))
LABOUR_PERCENTAGE = 12.0
LOGISTICS_RATE_PER_KM = LOGI_RATE
OPEX_PERCENTAGE = 3.0
MARGIN_PERCENTAGE = MARGIN * 100

def compute_quote(bom: list[BOMItem], distance_km: float) -> Quote:
    materials = sum(i.qty * i.unit_price for i in bom)
    labour = max(1.0, 0.12 * materials / LABOUR_RATE) * LABOUR_RATE  # naive: ~12% of materials value in hours
    logistics = distance_km * LOGI_RATE
    opex_year1 = 0.03 * materials  # naive assumption
    pre_margin = materials + labour + logistics
    total = pre_margin * (1 + MARGIN)
    return Quote(
        bom=bom,
        materials_subtotal=round(materials,2),
        labour=round(labour,2),
        logistics=round(logistics,2),
        opex_year1=round(opex_year1,2),
        total_before_margin=round(pre_margin,2),
        total_quote=round(total,2),
    )

def compute_quote_from_spec(spec: SystemSpec, distance_km: float = 100.0) -> Quote:
    """Compute quote directly from system specification using BOM engine"""
    bom_items = base_bom_for(spec)
    return compute_quote(bom_items, distance_km)

async def compute_quote_with_vendors(spec: SystemSpec, distance_km: float = 100.0, 
                                   vendor_client: Optional[VendorClient] = None) -> Quote:
    """Compute quote with live vendor pricing integration"""
    if vendor_client is None:
        vendor_client = setup_vendor_client()
    
    bom_items = await base_bom_for_with_vendors(spec, vendor_client)
    return compute_quote(bom_items, distance_km)

def compute_quote_enhanced(bom_items: List[Dict[str, Any]], distance_km: float = 100.0,
                         custom_rates: Optional[Dict[str, float]] = None) -> Quote:
    """Enhanced quote computation with customizable rates"""
    rates = {
        'labour_rate': LABOUR_RATE,
        'labour_percentage': LABOUR_PERCENTAGE,
        'logistics_rate': LOGISTICS_RATE_PER_KM,
        'opex_percentage': OPEX_PERCENTAGE,
        'margin_percentage': MARGIN_PERCENTAGE
    }
    
    if custom_rates:
        rates.update(custom_rates)
    
    # Calculate materials cost
    materials_subtotal = sum(item['qty'] * item['unit_price'] for item in bom_items)
    
    # Calculate labour (percentage of materials or fixed rate)
    labour = materials_subtotal * (rates['labour_percentage'] / 100)
    
    # Calculate logistics
    logistics = distance_km * rates['logistics_rate']
    
    # Calculate first year operational expenses
    opex_year1 = materials_subtotal * (rates['opex_percentage'] / 100)
    
    # Total before margin
    total_before_margin = materials_subtotal + labour + logistics + opex_year1
    
    # Apply margin
    total_quote = total_before_margin * (1 + rates['margin_percentage'] / 100)
    
    return Quote(
        bom=bom_items,
        materials_subtotal=materials_subtotal,
        labour=labour,
        logistics=logistics,
        opex_year1=opex_year1,
        total_before_margin=total_before_margin,
        total_quote=total_quote
    )