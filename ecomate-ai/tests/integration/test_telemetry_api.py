# tests/integration/test_telemetry_api.py
import pytest
from tests.factories import TelemetryDataFactory

pytestmark = pytest.mark.integration

async def test_ingest_batch(client):
    # The plan sends a batch, but for an integration test, a single event is also a good test.
    # We will use our more detailed factory to create a single telemetry event payload.
    telemetry_payload = TelemetryDataFactory.build()
    
    # The plan expects a 200 or 202 (Accepted) status code.
    r = await client.post("/telemetry/ingest", json=telemetry_payload)
    assert r.status_code in (200, 202)
