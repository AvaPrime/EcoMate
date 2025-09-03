import os, httpx

BASE = os.getenv('SHOPIFY_STORE_URL'); TOKEN = os.getenv('SHOPIFY_ADMIN_TOKEN')

async def fetch_products(limit: int = 50):
    if not (BASE and TOKEN): return []
    url = f"{BASE}/admin/api/2024-04/products.json?limit={limit}"
    async with httpx.AsyncClient(timeout=30, headers={"X-Shopify-Access-Token": TOKEN}) as c:
        r = await c.get(url); r.raise_for_status(); return r.json().get('products', [])