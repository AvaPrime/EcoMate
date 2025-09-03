# tests/integration/test_regulatory_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_list_standards(client):
    r = await client.get("/regulatory/standards")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
