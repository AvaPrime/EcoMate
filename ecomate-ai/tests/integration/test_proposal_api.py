# tests/integration/test_proposal_api.py
import pytest
from tests.factories import ProposalFactory

pytestmark = pytest.mark.integration

def make_proposal_request():
    """Creates a valid proposal request payload."""
    return {
        "site": {"lat": -34.036, "lon": 23.047, "altitude_m": 7},
        "needs": {"hot_water_daily_l": 200, "grid_connection": True},
        "constraints": {"budget_usd": 3500, "roof_area_m2": 20},
    }

async def test_generate_proposal_happy_path(client):
    payload = make_proposal_request()
    r = await client.post("/proposal/generate", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert {"bom", "estimate", "assumptions"} <= set(body.keys())

async def test_generate_proposal_validation_error(client):
    r = await client.post("/proposal/generate", json={"site": {}})
    assert r.status_code in (400, 422)
