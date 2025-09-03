from typing import List, Dict
from .models import UVReactor, SupplierRow, PartRow
from .normalize import flow_to_m3h, to_float, model_sku, currency_or_default, specs_json


def parse_uv_table(rows: List[List[str]], url: str, vendor: str | None = None) -> Dict[str, List[dict]]:
    if not rows: return {"suppliers": [], "parts": [], "report": {"status": "no_rows"}}
    headers = [c.lower() for c in rows[0]]
    def col(*names):
        for i,h in enumerate(headers):
            for n in names:
                if n in h: return i
        return None
    i_model = col('model','reactor') or 0
    i_flow  = col('flow','capacity')
    i_dose  = col('dose','mj/cm2','mj cm2')
    i_lampw = col('lamp','w')
    i_qty   = col('qty','lamps')
    i_price = col('price')

    suppliers, parts = [], []
    for r in rows[1:]:
        try:
            model = (r[i_model] if i_model is not None and i_model < len(r) else r[0]).strip()
            flow  = flow_to_m3h(r[i_flow]) if i_flow is not None and i_flow < len(r) else None
            dose  = to_float(r[i_dose]) if i_dose is not None and i_dose < len(r) else None
            lampw = int(to_float(r[i_lampw])) if i_lampw is not None and i_lampw < len(r) else None
            qty   = int(to_float(r[i_qty])) if i_qty is not None and i_qty < len(r) else None
            price = to_float(r[i_price]) if i_price is not None and i_price < len(r) else None

            uv = UVReactor(model=model, flow_m3h=flow, dose_mj_cm2=dose, lamp_w=lampw, lamps_qty=qty)
            sku = model_sku(vendor or 'uv', model)

            suppliers.append(SupplierRow(
                sku=sku, name=f"{uv.model} UV Reactor", brand=uv.brand, model=uv.model,
                category="uv", url=url, currency=currency_or_default(None), price=price
            ).model_dump())

            parts.append(PartRow(
                part_number=sku,
                description=f"UV Reactor {uv.model}",
                category="uv",
                specs_json=specs_json({
                    "flow_m3h": uv.flow_m3h,
                    "dose_mj_cm2": uv.dose_mj_cm2,
                    "lamp_w": uv.lamp_w,
                    "lamps_qty": uv.lamps_qty,
                }),
                price=price, currency=currency_or_default(None), url=url, sku=sku,
            ).model_dump())
        except Exception:
            continue
    return {"suppliers": suppliers, "parts": parts, "report": {"status": "ok", "rows": len(suppliers)}}