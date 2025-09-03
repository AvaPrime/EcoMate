import io, json
import pdfplumber

# Returns list[dict] with keys: table_index, rows (list[list[str]]), meta

def extract_tables(pdf_bytes: bytes):
    out = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pi, page in enumerate(pdf.pages):
            tables = page.extract_tables() or []
            for ti, t in enumerate(tables):
                # Normalize rows to strings
                norm = [[(c or "").strip() for c in row] for row in t]
                out.append({
                    "page": pi + 1,
                    "table_index": ti,
                    "rows": norm,
                    "meta": {"n_cols": max((len(r) for r in norm), default=0)}
                })
    return out