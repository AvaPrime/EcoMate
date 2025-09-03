# tests/integration/test_climate_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_get_forecast(client):
    r = await client.get("/climate/forecast?lat=-34.036&lon=23.047")
    assert r.status_code == 200
    data = r.json()
    assert {"daily", "source"} <= set(data.keys())
