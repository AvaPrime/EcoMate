# tests/integration/test_catalog_api.py
import pytest
from tests.factories import ProductFactory

pytestmark = pytest.mark.integration

async def test_upsert_and_get_item(client):
    item_payload = ProductFactory.build() # Use factory to build the payload dictionary
    
    # The plan uses /catalog/items, let's stick to that for now.
    # The existing mocked test uses /catalog/products. This might need alignment later.
    create_response = await client.post("/catalog/items", json=item_payload)
    assert create_response.status_code in (200, 201)
    
    created_item = create_response.json()
    assert "id" in created_item
    item_id = created_item["id"]
    
    # Use the ID from the creation response to fetch the item
    get_response = await client.get(f"/catalog/items/{item_id}")
    assert get_response.status_code == 200
    
    retrieved_item = get_response.json()
    assert retrieved_item["id"] == item_id
    assert retrieved_item["name"] == item_payload["name"]
