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
