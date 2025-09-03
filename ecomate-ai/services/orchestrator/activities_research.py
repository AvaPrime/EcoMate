import os, csv, io, json, mimetypes
from datetime import datetime, timezone
from typing import List, Dict
import httpx
from services.utils.robots import allowed
from services.utils.minio_store import put_bytes
from services.utils.pdf_extract import extract_tables
from services.utils.html_tables import extract_first_table
from services.utils.github_pr import open_pr
from services.orchestrator.model_router import ModelRouter
from services.parsers.dispatcher import parse_by_domain, parse_by_category
import yaml

SUPPLIERS = "data/suppliers.csv"
PARTS = "data/parts_list.csv"

# ---------- Helpers ----------

def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

def _ensure_headers(path: str, headers: List[str]):
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(headers)


def _append_or_update_by_key(path: str, key: str, row: Dict[str, str], headers: List[str]):
    rows: List[Dict[str, str]] = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
    found = False
    for r in rows:
        if r.get(key) == row.get(key):
            r.update(row)
            found = True
            break
    if not found:
        rows.append(row)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow({h: r.get(h, "") for h in headers})

# ---------- Activities ----------

async def activity_crawl(urls: List[str]) -> List[Dict]:
    results = []
    async with httpx.AsyncClient(timeout=30) as c:
        for url in urls:
            if not allowed(url):
                results.append({"url": url, "status": "blocked_by_robots"})
                continue
            try:
                r = await c.get(url, headers={"User-Agent": "EcoMateBot/1.0"})
                ct = r.headers.get("Content-Type", "")
                data = r.content
                # Save artifact
                prefix = "artifacts/html" if "html" in ct else "artifacts/pdf"
                s3url = put_bytes(prefix, data, content_type=ct or "application/octet-stream")
                item = {"url": url, "content_type": ct, "artifact": s3url}
                if "pdf" in ct or url.lower().endswith(".pdf"):
                    tables = extract_tables(data)
                    item["pdf_tables"] = tables
                else:
                    # HTML
                    html_text = r.text
                    table = extract_first_table(html_text)
                    item["html_table"] = table
                results.append(item)
            except Exception as e:
                results.append({"url": url, "status": f"error: {e}"})
    return results

async def activity_struct_extract(crawled: List[Dict]) -> Dict[str, List[Dict]]:
    """Parser-first, LLM-fallback strategy to structure supplier & parts rows.
    Returns dict with keys: suppliers, parts, evidence (json).
    """
    # Load router for LLM fallback
    cfg_path = os.path.join(os.path.dirname(__file__), "model_router.py")
    # Actually we need YAML config
    import pathlib, yaml
    cfg = yaml.safe_load(open(pathlib.Path(__file__).with_name("config.yaml")))
    router = ModelRouter(cfg)

    suppliers, parts, evidence = [], [], []

    for item in crawled:
        url = item.get("url")
        if item.get("status"):
            continue
        
        context_rows = item.get("html_table") or []
        if not context_rows and item.get("pdf_tables"):
            # take the largest table by rows
            tables = sorted(item["pdf_tables"], key=lambda t: len(t.get("rows", [])), reverse=True)
            context_rows = tables[0]["rows"] if tables else []
        
        # PARSER-FIRST STRATEGY: Try vendor-specific parsers
        parser_success = False
        try:
            # Try domain-based parser selection
            parser_result = parse_by_domain(url, context_rows)
            if parser_result and (parser_result.get("suppliers") or parser_result.get("parts")):
                # Parser succeeded
                for s in parser_result.get("suppliers", []):
                    s["url"] = s.get("url") or url
                    s["last_seen"] = _now_iso()
                    suppliers.append(s)
                for p in parser_result.get("parts", []):
                    p["url"] = p.get("url") or url
                    p["last_seen"] = _now_iso()
                    parts.append(p)
                evidence.append({"url": url, "method": "parser", "parser_type": "domain_based"})
                parser_success = True
        except Exception as e:
            evidence.append({"url": url, "parser_error": str(e)})
        
        # LLM FALLBACK: If parser failed or found no data
        if not parser_success:
            # Truncate for token safety
            rows_preview = context_rows[:30]
            prompt = (
                "Extract supplier and part details as JSON arrays with keys: "
                "suppliers:[{sku,name,brand,model,category,url,currency,price,availability,moq,lead_time,notes}], "
                "parts:[{part_number,description,category,specs_json,unit,price,currency,supplier,sku,url,notes}].\n"
                f"Source URL: {url}\n"
                "If data not present, omit the field. Be concise. Rows:\n" + json.dumps(rows_preview)
            )
            try:
                resp = await router.run("reason", prompt)
                # Router may return plain text; try to extract JSON
                j = _safe_json(resp)
                if j:
                    for s in j.get("suppliers", []):
                        s["url"] = s.get("url") or url
                        s["last_seen"] = _now_iso()
                        suppliers.append(s)
                    for p in j.get("parts", []):
                        p["url"] = p.get("url") or url
                        p["last_seen"] = _now_iso()
                        # specs_json must be string JSON
                        if isinstance(p.get("specs_json"), (dict, list)):
                            p["specs_json"] = json.dumps(p["specs_json"]) 
                        parts.append(p)
                    evidence.append({"url": url, "method": "llm_fallback", "prompt": prompt[:5000], "raw": resp[:5000]})
            except Exception as e:
                evidence.append({"url": url, "llm_error": str(e)})
    
    return {"suppliers": suppliers, "parts": parts, "evidence": evidence}

async def activity_write_and_pr(payload: Dict):
    # Ensure headers
    _ensure_headers(SUPPLIERS, ["sku","name","brand","model","category","url","currency","price","availability","moq","lead_time","notes","last_seen"])
    _ensure_headers(PARTS, ["part_number","description","category","specs_json","unit","price","currency","supplier","sku","url","notes","last_seen"])

    # Apply upserts
    for s in payload.get("suppliers", []):
        _append_or_update_by_key(SUPPLIERS, "sku", s, ["sku","name","brand","model","category","url","currency","price","availability","moq","lead_time","notes","last_seen"])
    for p in payload.get("parts", []):
        _append_or_update_by_key(PARTS, "part_number", p, ["part_number","description","category","specs_json","unit","price","currency","supplier","sku","url","notes","last_seen"])

    # Build changes content
    with open(SUPPLIERS, encoding="utf-8") as f:
        suppliers_csv = f.read()
    with open(PARTS, encoding="utf-8") as f:
        parts_csv = f.read()
    evidence_json = json.dumps(payload.get("evidence", []), ensure_ascii=False, indent=2)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    branch = f"bot/research-{today}"
    changes = {
        SUPPLIERS: suppliers_csv,
        PARTS: parts_csv,
        f"reports/RESEARCH_EVIDENCE_{today}.json": evidence_json,
    }
    open_pr(branch, f"Research: seed/update suppliers & parts ({today})", changes)
    return {"branch": branch, "suppliers": len(payload.get("suppliers", [])), "parts": len(payload.get("parts", []))}

# ---------- JSON helper ----------

def _safe_json(txt: str):
    try:
        # attempt raw
        return json.loads(txt)
    except Exception:
        # try to locate the first {...} or [...] block
        import re
        m = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", txt)
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except Exception:
            return None