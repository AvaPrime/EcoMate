import re, json, os
from typing import Optional
from slugify import slugify
from pint import UnitRegistry
ureg = UnitRegistry()

DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "ZAR").upper()

def to_float(s: str) -> Optional[float]:
    if s is None: return None
    s = s.strip().replace(',', '')
    m = re.search(r"-?\d+(?:\.\d+)?", s)
    return float(m.group()) if m else None

def model_sku(*parts) -> str:
    base = "-".join([p for p in parts if p]).strip()
    return slugify(base).upper()

def flow_to_m3h(val: str) -> Optional[float]:
    # Accept e.g. "25 m3/h", "25 m³/h", "1000 L/h", "16 gpm"
    if not val: return None
    v = val.replace('³','3').lower()
    # quick heuristics
    if 'm3/h' in v or 'm^3/h' in v:
        return to_float(v)
    if 'l/h' in v:
        f = to_float(v)
        return f/1000 if f is not None else None
    if 'gpm' in v:
        f = to_float(v)
        return round((f * 0.227124), 3) if f is not None else None
    # last resort pint
    try:
        q = ureg.Quantity(v)
        return q.to('meter**3/hour').magnitude
    except Exception:
        return to_float(v)

def head_to_m(val: str) -> Optional[float]:
    if not val: return None
    if 'm' in val.lower():
        return to_float(val)
    try:
        q = ureg.Quantity(val)
        return q.to('meter').magnitude
    except Exception:
        return to_float(val)

def currency_or_default(cur: str | None) -> str:
    return (cur or DEFAULT_CURRENCY).upper()

def specs_json(d: dict) -> str:
    return json.dumps({k:v for k,v in d.items() if v is not None}, ensure_ascii=False, separators=(",", ":"))