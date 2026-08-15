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


class ImageUploadClient(SequenceClient):
    def __init__(self, responses):
        super().__init__(responses)
        self.uploads = []

    async def upload_product_image(self, product_id, image_path):
        self.uploads.append({"product_id": product_id, "image_path": image_path})
        return {"status": "success", "product_id": str(product_id), "image_path": image_path}


@pytest.mark.asyncio
async def test_create_product_can_upload_image_after_creation():
    client = ImageUploadClient([{"product": {"id": "10"}}])

    result = await client.create_product(
        name="Test product",
        price=12.5,
        category_id="2",
        image_path=r"C:\images\product.jpg",
    )

    assert client.requests[0]["method"] == "POST"
    assert client.requests[0]["endpoint"] == "products"
    assert client.uploads == [{"product_id": "10", "image_path": r"C:\images\product.jpg"}]
    assert result["image_upload"]["status"] == "success"


@pytest.mark.asyncio
async def test_create_product_starts_disabled():
    client = SequenceClient([{"product": {"id": "10"}}])

    await client.create_product(
        name="Disabled product",
        price=12.5,
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["active"] == "0"


@pytest.mark.asyncio
async def test_create_product_uses_configured_tax_rules_group():
    client = SequenceClient([{"product": {"id": "10"}}])
    client.config.tax_rules_group_id = "7"

    await client.create_product(
        name="Taxed product",
        price=12.5,
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["id_tax_rules_group"] == "7"


@pytest.mark.asyncio
async def test_create_product_returns_stock_update_error_when_stock_permission_fails():
    client = SequenceClient([
        {"product": {"id": "10"}},
        {"stock_availables": [{"id": "99"}]},
    ])

    async def failing_make_request(method, endpoint, params=None, data=None):
        client.requests.append({
            "method": method,
            "endpoint": endpoint,
            "params": params or {},
            "data": data,
        })
        if endpoint == "stock_availables/99":
            raise Exception("PUT stock_availables not allowed")
        return client.responses.pop(0)

    client._make_request = failing_make_request

    result = await client.create_product(
        name="Stock product",
        price=12.5,
        category_id="2",
        quantity=10,
    )

    assert result["stock_update"]["error"] == "PUT stock_availables not allowed"


@pytest.mark.asyncio
async def test_create_product_writes_configured_language_fields():
    client = SequenceClient([{"product": {"id": "10"}}])

    await client.create_product(
        name={
            "es": "Producto prueba",
            "en": "Test product",
            "fr": "Produit test",
        },
        price=12.5,
        description={
            "es": "Descripcion en espanol",
            "en": "English description",
            "fr": "Description francaise",
        },
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["name"] == [
        {"id": 1, "value": "Producto prueba"},
        {"id": 5, "value": "Test product"},
        {"id": 6, "value": "Produit test"},
    ]
    assert product["description"] == [
        {"id": 1, "value": "Descripcion en espanol"},
        {"id": 5, "value": "English description"},
        {"id": 6, "value": "Description francaise"},
    ]
    assert product["link_rewrite"] == [
        {"id": 1, "value": "producto-prueba"},
        {"id": 5, "value": "test-product"},
        {"id": 6, "value": "produit-test"},
    ]


@pytest.mark.asyncio
async def test_create_product_fills_missing_translations_from_spanish():
    client = SequenceClient([{"product": {"id": "10"}}])

    await client.create_product(
        name={"es": "Producto prueba"},
        price=12.5,
        description={"es": "Descripcion base"},
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["name"] == [
        {"id": 1, "value": "Producto prueba"},
        {"id": 5, "value": "Producto prueba"},
        {"id": 6, "value": "Producto prueba"},
    ]
    assert product["description_short"] == [
        {"id": 1, "value": "Descripcion base"},
        {"id": 5, "value": "Descripcion base"},
        {"id": 6, "value": "Descripcion base"},
    ]


@pytest.mark.asyncio
async def test_update_product_stock_updates_existing_stock_record():
    client = SequenceClient([
        {"stock_availables": [{"id": "99"}]},
        {
            "stock_available": {
                "id": "99",
                "id_product": "10",
                "id_product_attribute": "0",
                "id_shop": "1",
                "id_shop_group": "0",
                "quantity": "0",
                "depends_on_stock": "0",
                "out_of_stock": "2",
            }
        },
        {"stock_available": {"id": "99", "quantity": "10"}},
    ])

    result = await client.update_product_stock("10", 10)

    assert client.requests[0]["endpoint"] == "stock_availables"
    assert client.requests[1]["endpoint"] == "stock_availables/99"
    assert client.requests[2]["method"] == "PUT"
    assert client.requests[2]["data"]["stock_available"]["quantity"] == "10"
    assert result["stock_available"]["quantity"] == "10"
