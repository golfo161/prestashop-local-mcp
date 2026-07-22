"""Tests for PrestaShop API client request behavior."""

import pytest

from prestashop_mcp.config import Config
from prestashop_mcp.prestashop_client import PrestaShopClient


class FakeResponse:
    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def text(self):
        return "{}"


class FakeSession:
    closed = False

    def __init__(self):
        self.last_request = None

    def request(self, **kwargs):
        self.last_request = kwargs
        return FakeResponse()


@pytest.mark.asyncio
async def test_make_request_sends_ws_key_query_parameter():
    config = Config(shop_url="https://example.com", api_key="test-api-key-123")
    client = PrestaShopClient(config)
    client.session = FakeSession()

    await client._make_request("GET", "configurations")

    assert client.session.last_request["params"]["ws_key"] == "test-api-key-123"


class SequenceClient(PrestaShopClient):
    def __init__(self, responses):
        super().__init__(Config(shop_url="https://example.com", api_key="test-api-key-123"))
        self.responses = responses
        self.requests = []

    async def _make_request(self, method, endpoint, params=None, data=None):
        self.requests.append({
            "method": method,
            "endpoint": endpoint,
            "params": params or {},
            "data": data,
        })
        return self.responses.pop(0)


@pytest.mark.asyncio
async def test_get_products_by_category_uses_category_associations():
    client = SequenceClient([
        {"categories": [{"id": 145, "name": [{"id": "1", "value": "AGOTADOS"}], "active": "0"}]},
        {
            "categories": [{
                "id": 145,
                "name": [{"id": "1", "value": "AGOTADOS"}],
                "active": "0",
                "associations": {"products": [{"id": "9"}]},
            }]
        },
        {"products": []},
        {
            "products": [{
                "id": 9,
                "name": [{"id": "1", "value": "Sold out product"}],
                "reference": "SO-001",
                "price": "12.500000",
                "quantity": "0",
                "active": "0",
                "id_category_default": "15",
                "associations": {"categories": [{"id": "15"}, {"id": "145"}]},
            }]
        },
    ])

    result = await client.get_products_by_category(category_name="AGOTADOS", limit=10)

    assert result["category"]["id"] == "145"
    assert result["products"] == [{
        "id": "9",
        "name": "Sold out product",
        "reference": "SO-001",
        "price": "12.500000",
        "quantity": "0",
        "active": "0",
        "id_category_default": "15",
        "associated_category_ids": ["15", "145"],
    }]
    assert result["detail_fetches"] == 1
    assert result["scanned_products"] == 0
    assert client.requests[0]["params"]["filter[name]"] == "[AGOTADOS]"
    assert client.requests[1]["endpoint"] == "categories/145"
    assert client.requests[2]["params"]["filter[id_category_default]"] == "145"


@pytest.mark.asyncio
async def test_get_products_by_category_accepts_category_id():
    client = SequenceClient([
        {"categories": [{"id": 145, "name": [{"id": "1", "value": "AGOTADOS"}], "active": "0"}]},
        {"products": []},
    ])

    result = await client.get_products_by_category(category_id="145", limit=10)

    assert result["category"]["name"] == "AGOTADOS"
    assert result["products"] == []
    assert client.requests[0]["endpoint"] == "categories/145"
