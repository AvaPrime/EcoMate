import httpx, time
from selectolax.parser import HTMLParser

async def fetch_title(url: str) -> dict:
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent":"EcoMateBot/1.0"}) as c:
        r = await c.get(url)
    html = HTMLParser(r.text)
    title = html.css_first("title").text() if html.css_first("title") else url
    return {"url": url, "title": title, "ts": int(time.time())}