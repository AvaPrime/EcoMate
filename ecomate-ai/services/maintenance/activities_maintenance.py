from services.utils.github_pr import open_pr
from .scheduler import tasks_for
import json, datetime

async def activity_plan(system_id: str):
    tasks = tasks_for(system_id)
    today = datetime.date.today().isoformat()
    open_pr(f"bot/maintenance-{system_id}-{today}", f"Maintenance plan {system_id}", {f"maintenance/{system_id}_{today}.json": json.dumps(tasks, indent=2)})
    return {"tasks": len(tasks)}