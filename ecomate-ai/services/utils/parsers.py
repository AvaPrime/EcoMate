from bs4 import BeautifulSoup

def extract_table(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')
    if not table:
        return []
    rows = []
    for tr in table.find_all('tr'):
        cells = [td.get_text(strip=True) for td in tr.find_all(['th','td'])]
        if cells:
            rows.append(cells)
    return rows