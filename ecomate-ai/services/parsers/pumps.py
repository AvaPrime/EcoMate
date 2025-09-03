from typing import List, Dict
from .models import Pump, SupplierRow, PartRow
from .normalize import flow_to_m3h, head_to_m, to_float, model_sku, currency_or_default, specs_json

# Input sources: table rows (list[list[str]]) or a dict extracted elsewhere

def parse_pump_table(rows: List[List[str]], url: str, vendor: str | None = None) -> Dict[str, List[dict]]:
    if not rows: return {"suppliers": [], "parts": [], "report": {"status": "no_rows"}}
    # Heuristic: find header row
    headers = [c.lower() for c in rows[0]]
    def col(name):
        for i,h in enumerate(headers):
            if name in h: return i
        return None
    i_model = col('model') or col('type') or 0
    i_flow  = col('flow')
    i_head  = col('head') or col('pressure')
    i_power = col('power') or col('kw')
    i_price = col('price')

    suppliers, parts = [], []
    for r in rows[1:]:
        try:
            model = (r[i_model] if i_model is not None and i_model < len(r) else r[0]).strip()
            flow  = flow_to_m3h(r[i_flow]) if i_flow is not None and i_flow < len(r) else None
            head  = head_to_m(r[i_head]) if i_head is not None and i_head < len(r) else None
            power = to_float(r[i_power]) if i_power is not None and i_power < len(r) else None
            price = to_float(r[i_price]) if i_price is not None and i_price < len(r) else None
            pump = Pump(model=model, flow_m3h=flow, head_m=head, power_kw=power)
            sku = model_sku(vendor or 'pump', model)

            suppliers.append(SupplierRow(
                sku=sku, name=f"{pump.model} Pump", brand=pump.brand, model=pump.model,
                category="pump", url=url, currency=currency_or_default(None), price=price
            ).model_dump())

            parts.append(PartRow(
                part_number=sku,
                description=f"Centrifugal pump {pump.model}",
                category="pump",
                specs_json=specs_json({
                    "flow_m3h": pump.flow_m3h,
                    "head_m": pump.head_m,
                    "power_kw": pump.power_kw,
                }),
                price=price, currency=currency_or_default(None), url=url, sku=sku,
            ).model_dump())
        except Exception as e:
            continue
    return {"suppliers": suppliers, "parts": parts, "report": {"status": "ok", "rows": len(suppliers)}}