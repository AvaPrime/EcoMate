from services.utils.github_pr import open_pr
from .connectors import shopify, woocommerce, medusa
from .sync import normalize_shopify
import json, datetime

async def activity_catalog_sync(source: str = 'shopify'):
    if source == 'shopify':
        prods = await shopify.fetch_products()
        rows = normalize_shopify(prods)
    elif source == 'woocommerce':
        prods = await woocommerce.fetch_products()
        rows = prods  # add normalizer similar to Shopify
    else:
        prods = await medusa.fetch_products()
        rows = prods
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    body = json.dumps(rows, ensure_ascii=False, indent=2)
    open_pr(f"bot/catalog-{today}", f"Catalog sync ({source}) {today}", {f"catalog/{source}_{today}.json": body})
    return {"count": len(rows)}