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
async def test_create_product_associates_default_category_for_catalog_visibility():
    client = SequenceClient([{"product": {"id": "10"}}])

    await client.create_product(
        name="Categorized product",
        price=12.5,
        category_id="210",
    )

    product = client.requests[0]["data"]["product"]
    assert product["id_category_default"] == "210"
    assert product["associations"] == {
        "categories": [
            {
                "category": {
                    "id": "210"
                }
            }
        ]
    }


@pytest.mark.asyncio
async def test_create_product_associates_existing_feature_ids():
    client = SequenceClient([{"product": {"id": "10"}}])

    result = await client.create_product(
        name="Featured product",
        price=12.5,
        category_id="210",
        features=[
            {"feature_id": "3", "feature_value_id": "9"},
            {"id_feature": "4", "id_feature_value": "10"},
        ],
    )

    product = client.requests[0]["data"]["product"]
    assert product["associations"]["product_features"] == [
        {"product_feature": {"id": "3", "id_feature_value": "9"}},
        {"product_feature": {"id": "4", "id_feature_value": "10"}},
    ]
    assert result["feature_links"] == [
        {"id_feature": "3", "id_feature_value": "9"},
        {"id_feature": "4", "id_feature_value": "10"},
    ]


@pytest.mark.asyncio
async def test_create_product_creates_missing_feature_and_value_by_name():
    client = SequenceClient([
        {"product_features": []},
        {"product_feature": {"id": "3"}},
        {"product_feature_values": []},
        {"product_feature_value": {"id": "9"}},
        {"product": {"id": "10"}},
    ])

    await client.create_product(
        name="Featured product",
        price=12.5,
        category_id="210",
        features=[{"nombre": "Composicion", "valor": "100% Poliamida"}],
    )

    assert client.requests[0]["method"] == "GET"
    assert client.requests[0]["endpoint"] == "product_features"
    assert client.requests[1]["method"] == "POST"
    assert client.requests[1]["endpoint"] == "product_features"
    assert client.requests[1]["data"]["product_feature"]["name"][0]["value"] == "Composicion"
    assert client.requests[2]["method"] == "GET"
    assert client.requests[2]["endpoint"] == "product_feature_values"
    assert client.requests[3]["method"] == "POST"
    assert client.requests[3]["endpoint"] == "product_feature_values"
    assert client.requests[3]["data"]["product_feature_value"]["id_feature"] == "3"
    assert client.requests[3]["data"]["product_feature_value"]["value"][0]["value"] == "100% Poliamida"

    product = client.requests[4]["data"]["product"]
    assert product["associations"]["product_features"] == [
        {"product_feature": {"id": "3", "id_feature_value": "9"}},
    ]


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
        {"id": 1, "value": ""},
        {"id": 5, "value": ""},
        {"id": 6, "value": ""},
    ]
    assert product["description_short"] == [
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
async def test_create_product_writes_summary_to_short_description_and_seo_fields():
    client = SequenceClient([{"product": {"id": "10"}}])

    await client.create_product(
        name={
            "es": "Lana Merino Azul",
            "en": "Blue Merino Wool",
            "fr": "Laine Merinos Bleue",
        },
        price=8.95,
        summary={
            "es": "Lana suave para tejer prendas de invierno.",
            "en": "Soft yarn for knitting winter garments.",
            "fr": "Laine douce pour tricoter des vetements d'hiver.",
        },
        meta_title={
            "es": "Lana Merino Azul",
            "en": "Blue Merino Wool",
            "fr": "Laine Merinos Bleue",
        },
        meta_description={
            "es": "Compra lana merino azul suave para punto y crochet.",
            "en": "Buy soft blue merino wool for knitting and crochet.",
            "fr": "Achetez une laine merinos bleue douce pour tricot et crochet.",
        },
        meta_keywords={
            "es": "lana merino, lana azul, punto, crochet",
            "en": "merino wool, blue yarn, knitting, crochet",
            "fr": "laine merinos, laine bleue, tricot, crochet",
        },
        link_rewrite={
            "es": "lana-merino-azul",
            "en": "blue-merino-wool",
            "fr": "laine-merinos-bleue",
        },
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["description_short"] == [
        {"id": 1, "value": "Lana suave para tejer prendas de invierno."},
        {"id": 5, "value": "Soft yarn for knitting winter garments."},
        {"id": 6, "value": "Laine douce pour tricoter des vetements d'hiver."},
    ]
    assert product["description"] == [
        {"id": 1, "value": ""},
        {"id": 5, "value": ""},
        {"id": 6, "value": ""},
    ]
    assert product["meta_title"][1]["value"] == "Blue Merino Wool"
    assert product["meta_description"][2]["value"].startswith("Achetez une laine")
    assert product["meta_keywords"][0]["value"] == "lana merino, lana azul, punto, crochet"
    assert product["link_rewrite"] == [
        {"id": 1, "value": "lana-merino-azul"},
        {"id": 5, "value": "blue-merino-wool"},
        {"id": 6, "value": "laine-merinos-bleue"},
    ]


@pytest.mark.asyncio
async def test_create_product_generates_basic_seo_when_only_summary_is_provided():
    client = SequenceClient([{"product": {"id": "10"}}])

    await client.create_product(
        name={"es": "Lana Algodon Natural"},
        price=5.5,
        summary={"es": "Hilo natural suave para labores de verano."},
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["description"][0]["value"] == ""
    assert product["description_short"][0]["value"] == "Hilo natural suave para labores de verano."
    assert product["meta_title"][0]["value"] == "Lana Algodon Natural"
    assert product["meta_description"][0]["value"] == "Hilo natural suave para labores de verano."
    assert "lana" in product["meta_keywords"][0]["value"]


@pytest.mark.asyncio
async def test_create_product_generates_clean_seo_from_html_summary():
    client = SequenceClient([{"product": {"id": "10"}}])

    summary = (
        "<p>Hilo fantasia suave para labores.</p>"
        "<p><strong>Caracteristicas:</strong></p>"
        "<ul><li>Textura tipo peluche.</li><li>Fabricado en Italia.</li></ul>"
    )

    await client.create_product(
        name={"es": "Hilo Peluche Italiano"},
        price=9.95,
        summary={"es": summary},
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["description_short"][0]["value"] == summary
    assert "<" not in product["meta_description"][0]["value"]
    assert "Hilo fantasia suave para labores" in product["meta_description"][0]["value"]
    assert "strong" not in product["meta_keywords"][0]["value"]
    assert "peluche" in product["meta_keywords"][0]["value"]


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
    assert product["description"] == [
        {"id": 1, "value": ""},
        {"id": 5, "value": ""},
        {"id": 6, "value": ""},
    ]


@pytest.mark.asyncio
async def test_create_product_limits_summary_to_1500_characters():
    client = SequenceClient([{"product": {"id": "10"}}])
    long_summary = "a" * 1600

    await client.create_product(
        name="Long summary product",
        price=12.5,
        summary=long_summary,
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert len(product["description_short"][0]["value"]) == 1500


@pytest.mark.asyncio
async def test_create_product_preserves_html_summary_format():
    client = SequenceClient([{"product": {"id": "10"}}])
    summary = (
        "<p>Resumen visual.</p>"
        "<p><strong>Caracteristicas:</strong></p>"
        "<ul><li>Punto clave 1.</li><li>Punto clave 2.</li></ul>"
    )

    await client.create_product(
        name="HTML summary product",
        price=12.5,
        summary=summary,
        category_id="2",
    )

    product = client.requests[0]["data"]["product"]
    assert product["description_short"][0]["value"] == summary


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


@pytest.mark.asyncio
async def test_update_product_active_true_refreshes_catalog_visibility_fields():
    client = SequenceClient([
        {
            "product": {
                "id": "10",
                "id_category_default": "210",
                "active": "0",
                "state": "1",
                "available_for_order": "1",
                "show_price": "1",
                "indexed": "0",
                "visibility": "none",
                "associations": {"images": [{"id": "5"}]},
            }
        },
        {"product": {"id": "10", "active": "1"}},
    ])

    await client.update_product("10", active=True)

    product = client.requests[1]["data"]["product"]
    assert product["active"] == "1"
    assert product["state"] == "1"
    assert product["available_for_order"] == "1"
    assert product["show_price"] == "1"
    assert product["indexed"] == "1"
    assert product["visibility"] == "both"
    assert product["associations"] == {"images": [{"id": "5"}]}


@pytest.mark.asyncio
async def test_update_product_omits_position_in_category_from_put_payload():
    client = SequenceClient([
        {
            "product": {
                "id": "10",
                "price": "99.000000",
                "position_in_category": "5",
                "manufacturer_name": "Maker",
                "associations": {"images": [{"id": "5"}]},
            }
        },
        {"product": {"id": "10", "price": "80.000000"}},
    ])

    await client.update_product("10", price=80)

    product = client.requests[1]["data"]["product"]
    assert product["price"] == "80"
    assert "position_in_category" not in product
    assert "manufacturer_name" not in product


@pytest.mark.asyncio
async def test_update_product_updates_full_product_fields_and_preserves_associations():
    client = SequenceClient([
        {
            "product": {
                "id": "10",
                "name": [
                    {"id": 1, "value": "Old"},
                    {"id": 5, "value": "Old"},
                    {"id": 6, "value": "Old"},
                ],
                "description": [
                    {"id": 1, "value": ""},
                    {"id": 5, "value": ""},
                    {"id": 6, "value": ""},
                ],
                "description_short": [
                    {"id": 1, "value": "Old summary"},
                    {"id": 5, "value": "Old summary"},
                    {"id": 6, "value": "Old summary"},
                ],
                "meta_title": [
                    {"id": 1, "value": "Old title"},
                    {"id": 5, "value": "Old title"},
                    {"id": 6, "value": "Old title"},
                ],
                "meta_description": [
                    {"id": 1, "value": "Old meta"},
                    {"id": 5, "value": "Old meta"},
                    {"id": 6, "value": "Old meta"},
                ],
                "meta_keywords": [
                    {"id": 1, "value": "old"},
                    {"id": 5, "value": "old"},
                    {"id": 6, "value": "old"},
                ],
                "link_rewrite": [
                    {"id": 1, "value": "old"},
                    {"id": 5, "value": "old"},
                    {"id": 6, "value": "old"},
                ],
                "reference": "OLD",
                "price": "10.000000",
                "wholesale_price": "5.000000",
                "weight": "0.100000",
                "id_tax_rules_group": "15",
                "associations": {
                    "categories": [{"id": "210"}],
                    "images": [{"id": "5"}],
                    "product_features": [{"id": "4", "id_feature_value": "9"}],
                },
            }
        },
        {"product": {"id": "10"}},
    ])

    await client.update_product(
        "10",
        name={"es": "Nuevo", "en": "New", "fr": "Nouveau"},
        summary={"es": "Resumen", "en": "Summary", "fr": "Resume"},
        description={"es": "Descripcion larga", "en": "Long description", "fr": "Description longue"},
        meta_title={"es": "Titulo", "en": "Title", "fr": "Titre"},
        meta_description={"es": "Meta es", "en": "Meta en", "fr": "Meta fr"},
        meta_keywords={"es": "uno, dos", "en": "one, two", "fr": "un, deux"},
        link_rewrite={"es": "nuevo", "en": "new", "fr": "nouveau"},
        reference="NEW-001",
        price=80,
        wholesale_price=40,
        weight=1.25,
        tax_rules_group_id="7",
    )

    product = client.requests[1]["data"]["product"]
    assert product["name"][0]["value"] == "Nuevo"
    assert product["description_short"][1]["value"] == "Summary"
    assert product["description"][2]["value"] == "Description longue"
    assert product["meta_title"][1]["value"] == "Title"
    assert product["meta_description"][2]["value"] == "Meta fr"
    assert product["meta_keywords"][0]["value"] == "uno, dos"
    assert product["link_rewrite"][2]["value"] == "nouveau"
    assert product["reference"] == "NEW-001"
    assert product["price"] == "80"
    assert product["wholesale_price"] == "40"
    assert product["weight"] == "1.25"
    assert product["id_tax_rules_group"] == "7"
    assert product["associations"]["images"] == [{"id": "5"}]
    assert product["associations"]["product_features"] == [{"id": "4", "id_feature_value": "9"}]


@pytest.mark.asyncio
async def test_update_product_can_replace_feature_associations_by_name():
    client = SequenceClient([
        {"product_features": [{"id": "3", "name": [{"id": "1", "value": "Composicion"}]}]},
        {
            "product_feature_values": [
                {"id": "9", "id_feature": "3", "value": [{"id": "1", "value": "100% Poliamida"}]}
            ]
        },
        {
            "product": {
                "id": "10",
                "associations": {
                    "categories": [{"id": "210"}],
                    "images": [{"id": "5"}],
                    "product_features": [{"id": "4", "id_feature_value": "8"}],
                },
            }
        },
        {"product": {"id": "10"}},
    ])

    await client.update_product(
        "10",
        features=[{"name": "Composicion", "value": "100% Poliamida"}],
    )

    product = client.requests[3]["data"]["product"]
    assert product["associations"]["categories"] == [{"id": "210"}]
    assert product["associations"]["images"] == [{"id": "5"}]
    assert product["associations"]["product_features"] == [
        {"product_feature": {"id": "3", "id_feature_value": "9"}}
    ]


@pytest.mark.asyncio
async def test_update_category_can_move_and_update_seo_fields():
    client = SequenceClient([
        {
            "category": {
                "id": "20",
                "id_parent": "2",
                "active": "1",
                "name": [{"id": 1, "value": "Old"}],
                "link_rewrite": [{"id": 1, "value": "old"}],
                "description": [{"id": 1, "value": "Old description"}],
                "meta_title": [{"id": 1, "value": "Old title"}],
                "meta_description": [{"id": 1, "value": "Old meta"}],
                "meta_keywords": [{"id": 1, "value": "old"}],
            }
        },
        {"category": {"id": "20"}},
    ])

    await client.update_category(
        "20",
        name="Nueva subcategoria",
        description="Nueva descripcion",
        parent_id="10",
        link_rewrite="nueva-subcategoria",
        meta_title="Titulo SEO",
        meta_description="Descripcion SEO",
        meta_keywords="lana, algodon",
        active=False,
    )

    category = client.requests[1]["data"]["category"]
    assert category["id_parent"] == "10"
    assert category["active"] == "0"
    assert category["name"][0]["value"] == "Nueva subcategoria"
    assert category["description"][0]["value"] == "Nueva descripcion"
    assert category["link_rewrite"][0]["value"] == "nueva-subcategoria"
    assert category["meta_title"][0]["value"] == "Titulo SEO"
    assert category["meta_description"][0]["value"] == "Descripcion SEO"
    assert category["meta_keywords"][0]["value"] == "lana, algodon"
