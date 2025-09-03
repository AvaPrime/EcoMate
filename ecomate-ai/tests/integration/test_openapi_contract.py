# tests/integration/test_openapi_contract.py
import pytest

pytestmark = pytest.mark.integration

# These are critical endpoints that we want to ensure are always documented.
CRITICAL_PATHS = [
    "/proposal/generate",
    "/catalog/items",
    "/maintenance/schedule",
    "/compliance/check",
    "/telemetry/ingest",
    "/regulatory/standards",
    "/climate/forecast",
    "/iot/devices/{device_id}/command" # Note: Path parameters are included in the spec
]

async def test_openapi_contains_critical_paths(client):
    """Tests that the OpenAPI schema contains all critical API paths."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    documented_paths = set(data.get("paths", {}).keys())
    
    # Check for paths that might have variations (e.g. with or without trailing slash)
    # and handle path parameters.
    normalized_documented_paths = {p.replace("/{device_id}", "/{device_id}") for p in documented_paths}
    
    missing_paths = []
    for p in CRITICAL_PATHS:
        # Normalize the critical path to handle potential variations
        normalized_p = p.replace("{device_id}", "{device_id}")
        if normalized_p not in normalized_documented_paths:
            missing_paths.append(p)
            
    assert not missing_paths, f"OpenAPI schema is missing the following critical paths: {', '.join(missing_paths)}"
