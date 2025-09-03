from services.utils.fetch import fetch_url
from services.utils.github_pr import open_pr

async def activity_fetch_and_log(urls: list[str]) -> list[dict]:
    results = []
    for u in urls:
        results.append(await fetch_title(u))
    return results

async def activity_open_docs_pr(findings: list[dict]):
    lines = ["url,title,ts"] + [f"{r['url']},{r['title'].replace(',', ' ')},{r['ts']}" for r in findings]
    csv = "\n".join(lines) + "\n"
    branch = "bot/research-initial"
    open_pr(branch, "Research: seed suppliers.csv", {"data/suppliers.csv": csv})
    return {"branch": branch, "rows": len(findings)}