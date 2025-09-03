from selectolax.parser import HTMLParser

# Returns list[list[str]] (rows)

def extract_first_table(html: str):
    doc = HTMLParser(html)
    tbl = doc.css_first("table")
    if not tbl:
        return []
    rows = []
    for tr in tbl.css("tr"):
        cells = [c.text(strip=True) for c in tr.css("th, td")] or []
        if cells:
            rows.append(cells)
    return rows