import os, httpx
BASE = os.getenv('WOOCOMMERCE_URL'); KEY=os.getenv('WOOCOMMERCE_KEY'); SECRET=os.getenv('WOOCOMMERCE_SECRET')
async def fetch_products(page: int = 1, per_page: int = 50):
    if not (BASE and KEY and SECRET): return []
    url = f"{BASE}/wp-json/wc/v3/products?page={page}&per_page={per_page}&consumer_key={KEY}&consumer_secret={SECRET}"
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(url); r.raise_for_status(); return r.json()