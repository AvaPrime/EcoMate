from typing import List, Dict, Optional
from urllib.parse import urlparse
from .pumps import parse_pump_table
from .uv import parse_uv_table

# Map domain keywords or categories to parser functions
PARSER_MAP = {
    "pump": parse_pump_table,
    "uv": parse_uv_table,
}

# Option A: decide by category hint

def parse_by_category(category: str, rows: List[List[str]], url: str, vendor: Optional[str] = None) -> Optional[Dict]:
    for key, fn in PARSER_MAP.items():
        if key in (category or '').lower():
            return fn(rows, url, vendor)
    return None

# Option B: decide by domain keyword (simple heuristic)
DOMAIN_HINTS = {
    "pumps": "pump",
    "uv": "uv",
}

def parse_by_domain(url: str, rows: List[List[str]]) -> Optional[Dict]:
    host = urlparse(url).netloc.lower()
    for k, cat in DOMAIN_HINTS.items():
        if k in host:
            return parse_by_category(cat, rows, url, vendor=host)
    return None