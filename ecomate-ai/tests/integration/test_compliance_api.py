# tests/integration/test_compliance_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_run_compliance_check(client):
    payload = {
        "metrics": {"pressure_kpa": 400, "temp_c": 60},
        "standard": "SANS-10254",
    }
    r = await client.post("/compliance/check", json=payload)
    assert r.status_code == 200
    res = r.json()
    assert {"compliant", "violations"} <= set(res.keys())
