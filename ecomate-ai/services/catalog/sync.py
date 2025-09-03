from typing import List, Dict

FIELDS = ["sku","title","vendor","price","currency","status","url","image"]

def normalize_shopify(ps: list[dict]) -> list[dict]:
    out = []
    for p in ps:
        sku = (p.get('variants') or [{}])[0].get('sku')
        out.append({
            "sku": sku or p.get('id'),
            "title": p.get('title'),
            "vendor": p.get('vendor'),
            "price": ((p.get('variants') or [{}])[0].get('price')),
            "currency": "ZAR",
            "status": p.get('status','active'),
            "url": p.get('handle'),
            "image": ((p.get('images') or [{}])[0].get('src')),
        })
    return out