# tests/integration/test_maintenance_api.py
import pytest
from tests.factories import MaintenanceScheduleFactory

pytestmark = pytest.mark.integration

async def test_schedule_maintenance(client):
    # Use the factory to build a payload dictionary.
    job_payload = MaintenanceScheduleFactory.build()
    
    # The plan expects a simple "scheduled" or "queued" status in response.
    # The factory generates a full object, so we send that as the payload.
    r = await client.post("/maintenance/schedule", json=job_payload)
    
    assert r.status_code in (200, 201)
    
    out = r.json()
    # The plan asserts on status. Let's assume the API returns the created object.
    # We can check for a key field from the payload to confirm receipt.
    assert out.get("status") in {"scheduled", "queued", "pending"}
    assert out.get("equipment_id") == job_payload["equipment_id"]
