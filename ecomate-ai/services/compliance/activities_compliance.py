from services.utils.github_pr import open_pr
from .engine import load_rules, evaluate
import json, datetime

async def activity_compliance(system_id: str, rules: list[str]):
    # stub: fetch spec from docs/data by system_id; here we use a demo spec
    spec = {"uv_dose_mj_cm2": 38}
    report = {}
    for r in rules:
        rs = load_rules(r)
        report[r] = evaluate(spec, rs)
    today = datetime.date.today().isoformat()
    open_pr(f"bot/compliance-{system_id}-{today}", f"Compliance {system_id}", {f"compliance/{system_id}_{today}.json": json.dumps(report, indent=2)})
    return report