# tests/integration/test_geospatial_api.py
import pytest

pytestmark = pytest.mark.integration

def make_geojson_point():
    """Helper to create a GeoJSON Point feature for testing."""
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [23.047, -34.036]},
        "properties": {"name": "Site A"},
    }

async def test_validate_geojson_point(client):
    r = await client.post("/geospatial/validate-geojson", json=make_geojson_point())
    assert r.status_code == 200
    body = r.json()
    assert body.get("valid") is True
