from pydantic import BaseModel
from typing import Optional

class Asset(BaseModel):
    system_id: str
    site: Optional[str] = None

class WorkOrder(BaseModel):
    system_id: str
    task: str
    due_date: str
    priority: str = 'normal'