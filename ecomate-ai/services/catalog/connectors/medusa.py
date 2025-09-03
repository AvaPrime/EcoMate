import os, httpx
BASE=os.getenv('MEDUSA_API_URL'); TOKEN=os.getenv('MEDUSA_API_TOKEN')
async def fetch_products(offset: int = 0, limit: int = 50):
    if not (BASE and TOKEN): return []
    url = f"{BASE}/admin/products?offset={offset}&limit={limit}"
    async with httpx.AsyncClient(timeout=30, headers={"Authorization": f"Bearer {TOKEN}"}) as c:
        r = await c.get(url); r.raise_for_status(); return r.json().get('products', [])