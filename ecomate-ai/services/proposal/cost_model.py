import os
from .models import BOMItem, Quote

LABOUR_RATE = float(os.getenv('LABOUR_RATE_ZAR', '450'))
LOGI_RATE = float(os.getenv('LOGISTICS_RATE_ZAR_PER_KM', '18'))
MARGIN = float(os.getenv('DEFAULT_MARGIN', '0.18'))

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