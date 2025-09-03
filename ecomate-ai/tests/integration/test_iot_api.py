# tests/integration/test_iot_api.py
import pytest

pytestmark = pytest.mark.integration

async def test_send_device_command(client):
    cmd = {"command": "reboot", "args": {}}
    r = await client.post("/iot/devices/dev-42/command", json=cmd)
    assert r.status_code in (200, 202)
