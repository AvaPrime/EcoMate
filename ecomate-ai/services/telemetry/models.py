from pydantic import BaseModel
from typing import Dict

class TelemetryIn(BaseModel):
    system_id: str
    metrics: Dict[str, float]