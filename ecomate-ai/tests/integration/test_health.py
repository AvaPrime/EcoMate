# tests/integration/test_health.py
import pytest

pytestmark = pytest.mark.integration

async def test_openapi_serves(client):
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    data = r.json()
    assert "paths" in data
