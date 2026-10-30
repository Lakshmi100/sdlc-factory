"""Tests for the /products endpoints (RETAIL-2). Each test checks one behaviour.

Every test name starts with the id of the case it covers in
docs/stories/RETAIL-2/test-plan.md, for example `test_tc38_...` covers TC38.
The guard tests at the end come from the design (style.md section 6).
TC47 (customers suite still passes) has no test here: it is checked by the
customers CI job and `make test` (see "Automation notes" in the plan).
"""

import json
from datetime import datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.schemas import ProductCreate, ProductUpdate

WIDGET = {
    "sku": "WID-001",
    "name": "Widget",
    "description": "A small widget",
    "price": "9.99",
}
GADGET = {"sku": "GAD-001", "name": "Gadget", "price": "19.50"}

# Two products whose sku and name sort the other way round from their ids.
ZEBRA = {"sku": "ZZZ-1", "name": "Zebra", "price": "5.00"}
AARDVARK = {"sku": "AAA-1", "name": "Aardvark", "price": "6.00"}

# Every field of WIDGET changed to a new value. Used by TC27 to check a full PUT.
WIDGET_REPLACED = {
    "sku": "WID-002",
    "name": "Large widget",
    "description": "A larger widget",
    "price": "24.75",
}

# Every field the API accepts, all set. Used by the guard tests at the end.
# The values round-trip unchanged: sku already uppercase, price a JSON number
# with two decimal places, description at least 10 characters.
WIDGET_WITH_EVERY_FIELD = {
    "sku": "WID-001",
    "name": "Widget",
    "description": "A small widget",
    "price": 19.99,
}

# Every field changed to a new value. Used to check that PUT stores every field.
WIDGET_WITH_EVERY_FIELD_CHANGED = {
    "sku": "WID-900",
    "name": "Large widget",
    "description": "A larger widget",
    "price": 29.99,
}

# Description boundaries: 9 characters (one under the minimum) and exactly 10.
DESCRIPTION_TOO_SHORT = "Too short"
DESCRIPTION_AT_MINIMUM = "Ten chars!"

# "S" * 64 builds a string of sixty-four "S" characters: the longest sku allowed.
SKU_AT_LIMIT = "S" * 64
# "S" * 65 builds sixty-five "S" characters: one more than the sku limit.
SKU_OVER_LIMIT = "S" * 65
# "s" * 64 builds sixty-four lowercase "s" characters: the longest sku, in lowercase.
LOWERCASE_SKU_AT_LIMIT = "s" * 64
# "N" * 200 builds two hundred "N" characters: the longest name allowed.
NAME_AT_LIMIT = "N" * 200
# "N" * 201 builds two hundred and one "N" characters: one more than the name limit.
NAME_OVER_LIMIT = "N" * 201
# "D" * 2000 builds two thousand "D" characters: the longest description allowed.
DESCRIPTION_AT_LIMIT = "D" * 2000
# "D" * 2001 builds two thousand and one "D" characters: one over the description limit.
DESCRIPTION_OVER_LIMIT = "D" * 2001
# " " * 10 builds ten spaces: long enough for the minimum, but whitespace only.
WHITESPACE_ONLY_DESCRIPTION = " " * 10

# "ß" * 40 builds forty German sharp-s letters: 40 characters, but not ASCII.
# Uppercased it would become "SS" * 40, which is 80 characters (review.md Must fix 1).
NON_ASCII_SKU_THAT_GROWS = "ß" * 40
# Letters, digits and punctuation only: allowed, and stored uppercased.
PUNCTUATION_SKU = "wid_001/A.b#~"
PUNCTUATION_SKU_UPPERCASED = "WID_001/A.B#~"

# A failed request must leave these fields exactly as they were.
FIELDS_THAT_MUST_NOT_CHANGE = ["sku", "name", "description", "price", "updated_at"]


def with_changes(product: dict, changes: dict) -> dict:
    """Return a copy of `product` with some fields replaced. The original is unchanged."""
    result = product.copy()
    result.update(changes)
    return result


def without_field(product: dict, field_name: str) -> dict:
    """Return a copy of `product` with one field left out. The original is unchanged."""
    result = product.copy()
    del result[field_name]
    return result


def create_product(client: TestClient, product: dict) -> dict:
    """POST a product that is expected to be valid, and return the created record.

    Fails the test straight away if the API rejects it, so a broken setup step
    is not mistaken for the behaviour under test.
    """
    response = client.post("/products", json=product)
    assert response.status_code == 201, response.text
    return response.json()


def get_product(client: TestClient, product_id: int) -> dict:
    """GET a product that is expected to exist, and return it."""
    response = client.get(f"/products/{product_id}")
    assert response.status_code == 200, response.text
    return response.json()


def list_products(client: TestClient) -> list[dict]:
    """GET the list of products, which is expected to succeed, and return it."""
    response = client.get("/products")
    assert response.status_code == 200, response.text
    return response.json()


def assert_no_products(client: TestClient) -> None:
    """Check that no product has been stored."""
    products = list_products(client)
    assert products == []


def assert_product_unchanged(client: TestClient, before: dict) -> None:
    """Check that the stored product still has the values it had in `before`."""
    after = get_product(client, before["id"])
    for field_name in FIELDS_THAT_MUST_NOT_CHANGE:
        assert after[field_name] == before[field_name], field_name


def assert_price_is_json_number(price: object, expected: str) -> None:
    """Check that a price taken from a response is a JSON number equal to `expected`.

    A price returned as a string such as "9.99" fails this check.
    """
    assert not isinstance(price, str), f"price is the string {price!r}, not a number"
    assert isinstance(price, int | float), f"price {price!r} is not a number"
    assert price == float(expected)


def exact_price_in(response_text: str) -> Decimal:
    """Read the price from raw JSON text without any rounding.

    Numbers with a decimal point are read as Decimal instead of float, so a
    value such as 9.9899999 in the JSON text does not compare equal to 9.99.
    """
    body = json.loads(response_text, parse_float=Decimal)
    return body["price"]


# ---- Create ----


def test_tc01_create_with_every_field_returns_201(client):
    """POST with every field set returns 201 and the product with a new id."""
    response = client.post("/products", json=WIDGET)

    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["sku"] == "WID-001"
    assert created["name"] == "Widget"
    assert created["description"] == "A small widget"
    assert_price_is_json_number(created["price"], "9.99")
    assert created["created_at"] is not None
    assert created["updated_at"] is not None


def test_tc02_create_stores_every_field_sent(client):
    """Every field sent on POST is returned by a later GET."""
    widget = create_product(client, WIDGET)

    stored = get_product(client, widget["id"])

    assert stored["sku"] == "WID-001"
    assert stored["name"] == "Widget"
    assert stored["description"] == "A small widget"
    assert_price_is_json_number(stored["price"], "9.99")


def test_tc03_create_without_description_stores_null(client):
    """A product created without a description has description null."""
    response = client.post("/products", json=without_field(WIDGET, "description"))

    assert response.status_code == 201
    created = response.json()
    assert created["description"] is None
    stored = get_product(client, created["id"])
    assert stored["description"] is None


def test_tc04_create_with_null_description_stores_null(client):
    """A description sent as null is accepted and stored as null."""
    product = with_changes(WIDGET, {"description": None})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    assert response.json()["description"] is None


def test_tc05_create_without_sku_returns_422(client):
    """sku is required on POST."""
    response = client.post("/products", json=without_field(WIDGET, "sku"))

    assert response.status_code == 422


def test_tc06_create_without_name_returns_422(client):
    """name is required on POST."""
    response = client.post("/products", json=without_field(WIDGET, "name"))

    assert response.status_code == 422


def test_tc07_create_without_price_returns_422(client):
    """price is required on POST."""
    response = client.post("/products", json=without_field(WIDGET, "price"))

    assert response.status_code == 422


def test_tc08_create_with_empty_body_returns_422(client):
    """An empty JSON object is rejected with 422."""
    response = client.post("/products", json={})

    assert response.status_code == 422


def test_tc09_create_with_empty_sku_returns_422(client):
    """An empty sku is rejected with 422."""
    product = with_changes(WIDGET, {"sku": ""})

    response = client.post("/products", json=product)

    assert response.status_code == 422


def test_tc10_create_with_empty_name_returns_422(client):
    """An empty name is rejected with 422."""
    product = with_changes(WIDGET, {"name": ""})

    response = client.post("/products", json=product)

    assert response.status_code == 422


def test_tc11_create_with_non_numeric_price_returns_422(client):
    """A price that is not a number is rejected with 422."""
    product = with_changes(WIDGET, {"price": "abc"})

    response = client.post("/products", json=product)

    assert response.status_code == 422


def test_tc12_price_is_stored_and_returned_exactly(client):
    """A price of "9.99" comes back as exactly 9.99, with no float drift."""
    # Act
    post_response = client.post("/products", json=WIDGET)
    assert post_response.status_code == 201
    created = post_response.json()
    get_response = client.get(f"/products/{created['id']}")

    # Assert
    assert get_response.status_code == 200
    assert_price_is_json_number(created["price"], "9.99")
    assert_price_is_json_number(get_response.json()["price"], "9.99")
    assert exact_price_in(post_response.text) == Decimal("9.99")
    assert exact_price_in(get_response.text) == Decimal("9.99")


def test_tc13_price_sent_as_json_number_is_accepted(client):
    """A price sent as the JSON number 9.99 is accepted and returned as a number."""
    product = with_changes(WIDGET, {"price": 9.99})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert_price_is_json_number(created["price"], "9.99")
    stored = get_product(client, created["id"])
    assert_price_is_json_number(stored["price"], "9.99")


def test_tc14_create_with_price_of_one_cent_returns_201(client):
    """The smallest positive price, 0.01, is accepted."""
    product = with_changes(WIDGET, {"price": "0.01"})

    response = client.post("/products", json=product)

    assert response.status_code == 201


def test_tc15_create_with_price_zero_returns_422(client):
    """A price of 0 is rejected with 422."""
    product = with_changes(WIDGET, {"price": 0})

    response = client.post("/products", json=product)

    assert response.status_code == 422


def test_tc16_create_with_price_zero_point_zero_zero_returns_422(client):
    """A price of "0.00" is rejected with 422."""
    product = with_changes(WIDGET, {"price": "0.00"})

    response = client.post("/products", json=product)

    assert response.status_code == 422


def test_tc17_create_with_negative_price_returns_422(client):
    """A negative price is rejected with 422."""
    product = with_changes(WIDGET, {"price": "-1.00"})

    response = client.post("/products", json=product)

    assert response.status_code == 422


def test_tc18_create_with_duplicate_sku_returns_409(client):
    """A second product with a sku already in use is rejected, and not stored."""
    create_product(client, WIDGET)
    second_product = with_changes(GADGET, {"sku": "WID-001"})

    response = client.post("/products", json=second_product)

    assert response.status_code == 409
    products = list_products(client)
    assert len(products) == 1


def test_tc19_create_two_products_with_different_skus(client):
    """Two products with different skus are both created, with different ids."""
    widget = create_product(client, WIDGET)
    gadget = create_product(client, GADGET)

    assert widget["id"] != gadget["id"]


def test_tc20_server_sets_id_and_timestamps_on_create(client):
    """The server assigns id, created_at and updated_at; values sent by the client are ignored."""
    # Arrange: a client that tries to choose its own id and created_at
    product = with_changes(WIDGET, {"id": 12345, "created_at": "2000-01-01T00:00:00+00:00"})

    # Act
    response = client.post("/products", json=product)

    # Assert
    assert response.status_code == 201
    created = response.json()
    assert created["id"] != 12345
    created_at = datetime.fromisoformat(created["created_at"])
    updated_at = datetime.fromisoformat(created["updated_at"])
    assert created_at.year != 2000
    assert updated_at.year != 2000


# ---- Read and list ----


def test_tc21_list_with_no_products_returns_empty_list(client):
    """GET /products returns an empty list when there are no products."""
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == []


def test_tc22_list_returns_products_ordered_by_id(client):
    """GET /products returns every product, oldest (lowest id) first."""
    create_product(client, WIDGET)
    create_product(client, GADGET)

    response = client.get("/products")

    assert response.status_code == 200
    products = response.json()
    skus = [product["sku"] for product in products]
    assert skus == ["WID-001", "GAD-001"]


def test_tc23_list_order_is_by_id_not_by_sku_or_name(client):
    """The list is ordered by id, even when sku and name would sort the other way."""
    create_product(client, ZEBRA)
    create_product(client, AARDVARK)

    products = list_products(client)

    skus = [product["sku"] for product in products]
    assert skus == ["ZZZ-1", "AAA-1"]


def test_tc24_get_product_by_id(client):
    """GET /products/{id} returns that product, matching what POST returned."""
    widget = create_product(client, WIDGET)

    response = client.get(f"/products/{widget['id']}")

    assert response.status_code == 200
    assert response.json() == widget


def test_tc25_get_missing_product_returns_404(client):
    """Asking for an id that does not exist returns 404."""
    response = client.get("/products/999")

    assert response.status_code == 404


def test_tc26_get_with_non_integer_id_returns_422(client):
    """An id that is not a whole number is rejected with 422."""
    response = client.get("/products/abc")

    assert response.status_code == 422


# ---- Update ----


def test_tc27_update_replaces_every_field(client):
    """PUT with every field changed returns and stores every new value."""
    # Arrange
    widget = create_product(client, WIDGET)

    # Act
    response = client.put(f"/products/{widget['id']}", json=WIDGET_REPLACED)

    # Assert: the response and a later GET both show the new values
    assert response.status_code == 200
    updated = response.json()
    stored = get_product(client, widget["id"])
    for product in [updated, stored]:
        assert product["sku"] == "WID-002"
        assert product["name"] == "Large widget"
        assert product["description"] == "A larger widget"
        assert_price_is_json_number(product["price"], "24.75")


def test_tc28_update_keeping_own_sku_is_not_a_duplicate(client):
    """A PUT that keeps the product's own sku succeeds; it does not conflict with itself."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"name": "Widget mark 2"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["sku"] == "WID-001"


def test_tc29_update_without_description_clears_it(client):
    """PUT is a full replacement, so leaving description out sets it back to null."""
    widget = create_product(client, WIDGET)

    response = client.put(f"/products/{widget['id']}", json=without_field(WIDGET, "description"))

    assert response.status_code == 200
    assert response.json()["description"] is None
    stored = get_product(client, widget["id"])
    assert stored["description"] is None


def test_tc30_update_without_sku_returns_422(client):
    """sku is required on PUT."""
    widget = create_product(client, WIDGET)

    response = client.put(f"/products/{widget['id']}", json=without_field(WIDGET, "sku"))

    assert response.status_code == 422


def test_tc31_update_without_name_returns_422(client):
    """name is required on PUT."""
    widget = create_product(client, WIDGET)

    response = client.put(f"/products/{widget['id']}", json=without_field(WIDGET, "name"))

    assert response.status_code == 422


def test_tc32_update_without_price_returns_422(client):
    """price is required on PUT."""
    widget = create_product(client, WIDGET)

    response = client.put(f"/products/{widget['id']}", json=without_field(WIDGET, "price"))

    assert response.status_code == 422


def test_tc33_update_with_price_zero_returns_422(client):
    """A price of 0 is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"price": 0})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc34_update_with_negative_price_returns_422(client):
    """A negative price is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"price": "-1.00"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc35_update_with_price_of_one_cent_returns_200(client):
    """The smallest positive price, 0.01, is accepted on PUT and stored."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"price": "0.01"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert_price_is_json_number(response.json()["price"], "0.01")
    stored = get_product(client, widget["id"])
    assert_price_is_json_number(stored["price"], "0.01")


def test_tc36_update_to_duplicate_sku_returns_409(client):
    """Changing a product's sku to one another product already uses is rejected."""
    # Arrange: two products with different skus
    create_product(client, WIDGET)
    gadget = create_product(client, GADGET)

    # Act: try to give the gadget the widget's sku
    gadget_with_widget_sku = with_changes(GADGET, {"sku": "WID-001"})
    response = client.put(f"/products/{gadget['id']}", json=gadget_with_widget_sku)

    # Assert: the unique-sku rule is enforced and the gadget keeps its sku
    assert response.status_code == 409
    stored = get_product(client, gadget["id"])
    assert stored["sku"] == "GAD-001"


def test_tc37_update_missing_product_returns_404(client):
    """Updating an id that does not exist, with a valid body, returns 404."""
    response = client.put("/products/999", json=WIDGET)

    assert response.status_code == 404


def test_tc38_put_missing_id_invalid_body_returns_422(client):
    """An invalid body on a missing id returns 422, not 404: the body is checked first."""
    invalid_product = with_changes(WIDGET, {"price": 0})

    response = client.put("/products/999", json=invalid_product)

    assert response.status_code == 422


def test_tc39_update_changes_updated_at_but_not_created_at(client):
    """PUT keeps created_at and moves updated_at forward (or leaves it equal)."""
    # Arrange
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"name": "Widget mark 2"})

    # Act
    response = client.put(f"/products/{widget['id']}", json=changed)

    # Assert
    assert response.status_code == 200
    updated = response.json()
    assert updated["created_at"] == widget["created_at"]
    updated_at_before = datetime.fromisoformat(widget["updated_at"])
    updated_at_after = datetime.fromisoformat(updated["updated_at"])
    assert updated_at_after >= updated_at_before


# ---- Delete ----


def test_tc40_delete_product(client):
    """DELETE returns 204 with an empty body, and the product can no longer be fetched."""
    widget = create_product(client, WIDGET)

    delete_response = client.delete(f"/products/{widget['id']}")

    assert delete_response.status_code == 204
    assert delete_response.content == b""
    get_response = client.get(f"/products/{widget['id']}")
    assert get_response.status_code == 404


def test_tc41_delete_removes_only_that_product_from_the_list(client):
    """After deleting one product, the list still holds the others."""
    widget = create_product(client, WIDGET)
    create_product(client, GADGET)

    response = client.delete(f"/products/{widget['id']}")

    assert response.status_code == 204
    products = list_products(client)
    skus = [product["sku"] for product in products]
    assert skus == ["GAD-001"]


def test_tc42_delete_missing_product_returns_404(client):
    """Deleting an id that does not exist returns 404."""
    response = client.delete("/products/999")

    assert response.status_code == 404


def test_tc43_delete_same_product_twice_returns_404_the_second_time(client):
    """The first DELETE succeeds; the second finds nothing and returns 404."""
    widget = create_product(client, WIDGET)

    first_response = client.delete(f"/products/{widget['id']}")
    second_response = client.delete(f"/products/{widget['id']}")

    assert first_response.status_code == 204
    assert second_response.status_code == 404


def test_tc44_sku_can_be_reused_after_delete(client):
    """Once a product is deleted, a new product may use its sku."""
    widget = create_product(client, WIDGET)
    delete_response = client.delete(f"/products/{widget['id']}")
    assert delete_response.status_code == 204

    response = client.post("/products", json=WIDGET)

    assert response.status_code == 201


# ---- Guard data (TC45) ----


def test_tc45_guard_data_covers_every_schema_field():
    """The guard test data lists exactly the fields that POST and PUT accept.

    If this fails, a field was added to (or removed from) the schemas. Update
    WIDGET_WITH_EVERY_FIELD, WIDGET_WITH_EVERY_FIELD_CHANGED and the explicit
    field assignments in routes.py to match.
    """
    create_fields = set(ProductCreate.model_fields)
    update_fields = set(ProductUpdate.model_fields)

    assert set(WIDGET_WITH_EVERY_FIELD) == create_fields
    assert set(WIDGET_WITH_EVERY_FIELD_CHANGED) == update_fields


# ---- Regression ----


def test_tc46_health_still_reports_ok(client):
    """GET /health still works once the product routes are added."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "products"}


def test_tc48_each_test_starts_with_an_empty_database(client):
    """Products created by other tests are not visible here.

    Many tests in this file create WID-001. If the database were shared, the
    list would not be empty and creating WID-001 again would return 409.
    """
    assert_no_products(client)

    response = client.post("/products", json=WIDGET)

    assert response.status_code == 201


# ---- Description length (design gate, round 1) ----


def test_tc49_create_with_description_of_9_chars_returns_422(client):
    """A description one character under the minimum of 10 is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"description": DESCRIPTION_TOO_SHORT})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc50_create_with_description_of_10_chars_returns_201(client):
    """A description of exactly 10 characters is accepted and stored as sent."""
    product = with_changes(WIDGET, {"description": DESCRIPTION_AT_MINIMUM})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["description"] == "Ten chars!"
    stored = get_product(client, created["id"])
    assert stored["description"] == "Ten chars!"


def test_tc51_create_with_empty_description_returns_422(client):
    """An empty-string description is rejected (not turned into null), and nothing is stored."""
    product = with_changes(WIDGET, {"description": ""})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc52_update_with_description_of_9_chars_returns_422(client):
    """A 9-character description is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"description": DESCRIPTION_TOO_SHORT})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc53_update_with_description_of_10_chars_returns_200(client):
    """A description of exactly 10 characters is accepted on PUT and stored."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"description": DESCRIPTION_AT_MINIMUM})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["description"] == "Ten chars!"
    stored = get_product(client, widget["id"])
    assert stored["description"] == "Ten chars!"


def test_tc54_update_with_empty_description_returns_422(client):
    """An empty-string description is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"description": ""})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


# ---- Length limits (design gate, round 2) ----


def test_tc55_create_with_sku_of_64_chars_returns_201(client):
    """A sku of exactly 64 characters is accepted and stored as sent."""
    product = with_changes(WIDGET, {"sku": SKU_AT_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == SKU_AT_LIMIT
    stored = get_product(client, created["id"])
    assert stored["sku"] == SKU_AT_LIMIT


def test_tc56_create_with_sku_of_65_chars_returns_422(client):
    """A sku one character over the limit of 64 is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": SKU_OVER_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc57_create_with_name_of_200_chars_returns_201(client):
    """A name of exactly 200 characters is accepted and stored as sent."""
    product = with_changes(WIDGET, {"name": NAME_AT_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == NAME_AT_LIMIT
    stored = get_product(client, created["id"])
    assert stored["name"] == NAME_AT_LIMIT


def test_tc58_create_with_name_of_201_chars_returns_422(client):
    """A name one character over the limit of 200 is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"name": NAME_OVER_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc59_create_with_description_of_2000_chars_returns_201(client):
    """A description of exactly 2000 characters is accepted and stored as sent."""
    product = with_changes(WIDGET, {"description": DESCRIPTION_AT_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["description"] == DESCRIPTION_AT_LIMIT
    stored = get_product(client, created["id"])
    assert stored["description"] == DESCRIPTION_AT_LIMIT


def test_tc60_create_with_description_of_2001_chars_returns_422(client):
    """A description one character over the limit of 2000 is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"description": DESCRIPTION_OVER_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc61_create_with_sku_of_1_char_returns_201(client):
    """A 1-character sku is accepted and stored."""
    product = with_changes(WIDGET, {"sku": "X"})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == "X"
    stored = get_product(client, created["id"])
    assert stored["sku"] == "X"


def test_tc62_create_with_name_of_1_char_returns_201(client):
    """A 1-character name is accepted and stored."""
    product = with_changes(WIDGET, {"name": "X"})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "X"
    stored = get_product(client, created["id"])
    assert stored["name"] == "X"


def test_tc63_update_with_sku_of_65_chars_returns_422(client):
    """A 65-character sku is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": SKU_OVER_LIMIT})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc64_update_with_name_of_201_chars_returns_422(client):
    """A 201-character name is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"name": NAME_OVER_LIMIT})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc65_update_with_description_of_2001_chars_returns_422(client):
    """A 2001-character description is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"description": DESCRIPTION_OVER_LIMIT})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


# ---- Price precision (design gate, round 2) ----


def test_tc66_create_with_price_of_2_decimal_places_returns_201(client):
    """A price with two decimal places is accepted and returned as a number."""
    product = with_changes(WIDGET, {"price": "19.99"})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert_price_is_json_number(created["price"], "19.99")
    stored = get_product(client, created["id"])
    assert_price_is_json_number(stored["price"], "19.99")


def test_tc67_create_with_price_of_3_decimal_places_returns_422(client):
    """A price with three decimal places is rejected, not rounded and stored."""
    product = with_changes(WIDGET, {"price": "19.999"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc68_create_with_largest_price_returns_201(client):
    """The largest allowed price, 99999999.99, is accepted and returned exactly."""
    # Arrange
    product = with_changes(WIDGET, {"price": "99999999.99"})

    # Act
    post_response = client.post("/products", json=product)
    assert post_response.status_code == 201
    created = post_response.json()
    get_response = client.get(f"/products/{created['id']}")

    # Assert
    assert get_response.status_code == 200
    assert_price_is_json_number(created["price"], "99999999.99")
    assert_price_is_json_number(get_response.json()["price"], "99999999.99")
    assert exact_price_in(post_response.text) == Decimal("99999999.99")
    assert exact_price_in(get_response.text) == Decimal("99999999.99")


def test_tc69_create_with_price_of_11_digits_returns_422(client):
    """A price one cent over the maximum (11 digits) is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"price": "100000000.00"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc70_update_with_price_of_3_decimal_places_returns_422(client):
    """A price with three decimal places is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"price": "19.999"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)
    stored = get_product(client, widget["id"])
    assert_price_is_json_number(stored["price"], "9.99")


# ---- Whitespace-only values and PUT minimums (design gate, rounds 2 and 3) ----


def test_tc71_create_with_whitespace_only_sku_returns_422(client):
    """A sku made only of spaces is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": "   "})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc72_create_with_whitespace_only_name_returns_422(client):
    """A name made only of spaces is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"name": "   "})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc73_update_with_whitespace_only_sku_returns_422(client):
    """A sku made only of spaces is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": "   "})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc74_update_with_whitespace_only_name_returns_422(client):
    """A name made only of spaces is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"name": "   "})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc75_update_with_sku_of_1_char_returns_200(client):
    """A 1-character sku is accepted on PUT and stored."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": "X"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["sku"] == "X"
    stored = get_product(client, widget["id"])
    assert stored["sku"] == "X"


def test_tc76_update_with_name_of_1_char_returns_200(client):
    """A 1-character name is accepted on PUT and stored."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"name": "X"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["name"] == "X"
    stored = get_product(client, widget["id"])
    assert stored["name"] == "X"


def test_tc77_create_with_whitespace_only_description_returns_422(client):
    """A description of ten spaces is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"description": WHITESPACE_ONLY_DESCRIPTION})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc78_update_with_whitespace_only_description_returns_422(client):
    """A description of ten spaces is rejected on PUT, and the stored product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"description": WHITESPACE_ONLY_DESCRIPTION})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


# ---- Price returned as a JSON number (design gate, round 4) ----


def test_tc79_price_sent_as_string_is_returned_as_number_on_create(client):
    """A price sent as the string "9.99" comes back from POST as the number 9.99."""
    response = client.post("/products", json=WIDGET)

    assert response.status_code == 201
    assert_price_is_json_number(response.json()["price"], "9.99")


def test_tc80_get_by_id_returns_price_as_number(client):
    """GET /products/{id} returns price as a number, not a string."""
    widget = create_product(client, WIDGET)

    response = client.get(f"/products/{widget['id']}")

    assert response.status_code == 200
    assert_price_is_json_number(response.json()["price"], "9.99")


def test_tc81_list_returns_every_price_as_number(client):
    """GET /products returns every item's price as a number, in id order."""
    create_product(client, WIDGET)
    create_product(client, GADGET)

    products = list_products(client)

    assert len(products) == 2
    assert_price_is_json_number(products[0]["price"], "9.99")
    assert_price_is_json_number(products[1]["price"], "19.5")


def test_tc82_largest_price_sent_as_json_number_is_returned_exactly(client):
    """The JSON number 99999999.99 is accepted and returned exactly, on POST and GET."""
    # Arrange
    product = with_changes(WIDGET, {"price": 99999999.99})

    # Act
    post_response = client.post("/products", json=product)
    assert post_response.status_code == 201
    created = post_response.json()
    get_response = client.get(f"/products/{created['id']}")

    # Assert
    assert get_response.status_code == 200
    assert_price_is_json_number(created["price"], "99999999.99")
    assert_price_is_json_number(get_response.json()["price"], "99999999.99")
    assert exact_price_in(post_response.text) == Decimal("99999999.99")
    assert exact_price_in(get_response.text) == Decimal("99999999.99")


def test_tc83_price_sent_as_string_is_returned_as_number_on_update(client):
    """A price sent as the string "19.50" on PUT comes back as the number 19.5."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"price": "19.50"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert_price_is_json_number(response.json()["price"], "19.5")
    stored = get_product(client, widget["id"])
    assert_price_is_json_number(stored["price"], "19.5")


# ---- sku stored uppercase, unique regardless of case (design gate, round 4) ----


def test_tc84_create_with_lowercase_sku_stores_it_uppercase(client):
    """A lowercase sku is converted to uppercase before it is saved."""
    product = with_changes(WIDGET, {"sku": "wid-001"})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == "WID-001"
    stored = get_product(client, created["id"])
    assert stored["sku"] == "WID-001"


def test_tc85_create_uppercase_sku_after_lowercase_returns_409(client):
    """ "WID-001" counts as a duplicate of an existing "wid-001"."""
    create_product(client, with_changes(WIDGET, {"sku": "wid-001"}))
    second_product = with_changes(GADGET, {"sku": "WID-001"})

    response = client.post("/products", json=second_product)

    assert response.status_code == 409
    products = list_products(client)
    skus = [product["sku"] for product in products]
    assert skus == ["WID-001"]


def test_tc86_create_lowercase_sku_after_uppercase_returns_409(client):
    """ "wid-001" counts as a duplicate of an existing "WID-001"."""
    create_product(client, WIDGET)
    second_product = with_changes(GADGET, {"sku": "wid-001"})

    response = client.post("/products", json=second_product)

    assert response.status_code == 409
    products = list_products(client)
    skus = [product["sku"] for product in products]
    assert skus == ["WID-001"]


def test_tc87_update_to_other_products_sku_in_lowercase_returns_409(client):
    """A PUT giving one product another product's sku in a different case is rejected."""
    # Arrange: two products with different skus
    widget = create_product(client, WIDGET)
    gadget = create_product(client, GADGET)

    # Act: try to give the gadget the widget's sku, written in lowercase
    gadget_with_widget_sku = with_changes(GADGET, {"sku": "wid-001"})
    response = client.put(f"/products/{gadget['id']}", json=gadget_with_widget_sku)

    # Assert: rejected, the gadget keeps its sku and the widget is untouched
    assert response.status_code == 409
    stored_gadget = get_product(client, gadget["id"])
    assert stored_gadget["sku"] == "GAD-001"
    assert_product_unchanged(client, widget)


def test_tc88_update_changing_only_case_of_own_sku_returns_200(client):
    """A PUT that only changes the case of the product's own sku succeeds, stored uppercase."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": "wid-001"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["sku"] == "WID-001"
    stored = get_product(client, widget["id"])
    assert stored["sku"] == "WID-001"


def test_tc89_create_with_mixed_case_sku_stores_it_uppercase(client):
    """A mixed-case sku is converted to uppercase before it is saved."""
    product = with_changes(WIDGET, {"sku": "Wid-001"})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == "WID-001"
    stored = get_product(client, created["id"])
    assert stored["sku"] == "WID-001"


def test_tc90_create_with_lowercase_sku_of_64_chars_stores_it_uppercase(client):
    """A 64-character lowercase sku is accepted and stored as 64 uppercase characters."""
    product = with_changes(WIDGET, {"sku": LOWERCASE_SKU_AT_LIMIT})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == SKU_AT_LIMIT
    stored = get_product(client, created["id"])
    assert stored["sku"] == SKU_AT_LIMIT


def test_tc91_create_with_non_ascii_sku_that_grows_returns_422(client):
    """ "ß" * 40 is rejected, nothing is stored, and the product list still works."""
    product = with_changes(WIDGET, {"sku": NON_ASCII_SKU_THAT_GROWS})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc92_create_with_non_ascii_sku_returns_422(client):
    """A sku with a non-ASCII letter ("É") is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": "CAFÉ-1"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc93_create_with_space_inside_sku_returns_422(client):
    """A sku with a space in the middle is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": "WID 001"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc94_create_with_leading_space_in_sku_returns_422(client):
    """A sku that starts with a space is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": " WID-001"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc95_create_with_tab_in_sku_returns_422(client):
    """A sku that ends with a tab (a control character) is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": "WID-001\t"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc96_create_with_punctuation_in_sku_returns_201(client):
    """A sku of letters, digits and punctuation is accepted and stored uppercased."""
    product = with_changes(WIDGET, {"sku": PUNCTUATION_SKU})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == PUNCTUATION_SKU_UPPERCASED
    stored = get_product(client, created["id"])
    assert stored["sku"] == PUNCTUATION_SKU_UPPERCASED


def test_tc97_update_with_non_ascii_sku_that_grows_returns_422(client):
    """ "ß" * 40 is rejected on PUT, the product is unchanged, and the list still works."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": NON_ASCII_SKU_THAT_GROWS})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)
    products = list_products(client)
    skus = [product["sku"] for product in products]
    assert skus == ["WID-001"]


def test_tc98_update_with_space_inside_sku_returns_422(client):
    """A sku with a space in the middle is rejected on PUT, and the product is unchanged."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": "WID 001"})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 422
    assert_product_unchanged(client, widget)


def test_tc99_create_with_trailing_space_in_sku_returns_422(client):
    """A sku that ends with a space is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": "WID-001 "})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc100_create_with_del_character_in_sku_returns_422(client):
    """A sku containing DEL (0x7F, just above "~") is rejected, and nothing is stored."""
    product = with_changes(WIDGET, {"sku": "WID-001\x7f"})

    response = client.post("/products", json=product)

    assert response.status_code == 422
    assert_no_products(client)


def test_tc101_create_with_sku_of_exclamation_mark_returns_201(client):
    """ "!" (0x21, the lowest allowed character) is accepted as a 1-character sku."""
    product = with_changes(WIDGET, {"sku": "!"})

    response = client.post("/products", json=product)

    assert response.status_code == 201
    created = response.json()
    assert created["sku"] == "!"
    stored = get_product(client, created["id"])
    assert stored["sku"] == "!"


def test_tc102_update_with_punctuation_in_sku_returns_200(client):
    """A sku of letters, digits and punctuation is accepted on PUT and stored uppercased."""
    widget = create_product(client, WIDGET)
    changed = with_changes(WIDGET, {"sku": PUNCTUATION_SKU})

    response = client.put(f"/products/{widget['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["sku"] == PUNCTUATION_SKU_UPPERCASED
    stored = get_product(client, widget["id"])
    assert stored["sku"] == PUNCTUATION_SKU_UPPERCASED


# ---- Guard tests: routes.py copies fields one by one (see style.md section 6) ----


def test_guard_create_stores_every_field(client):
    """Every field sent on POST is stored. Fails if routes.py forgets to copy one."""
    widget = create_product(client, WIDGET_WITH_EVERY_FIELD)

    stored = get_product(client, widget["id"])

    for field_name in WIDGET_WITH_EVERY_FIELD:
        assert stored[field_name] == WIDGET_WITH_EVERY_FIELD[field_name], field_name


def test_guard_update_stores_every_field(client):
    """Every field sent on PUT is stored. Fails if routes.py forgets to copy one."""
    widget = create_product(client, WIDGET_WITH_EVERY_FIELD)

    response = client.put(f"/products/{widget['id']}", json=WIDGET_WITH_EVERY_FIELD_CHANGED)

    assert response.status_code == 200
    stored = get_product(client, widget["id"])
    for field_name in WIDGET_WITH_EVERY_FIELD_CHANGED:
        assert stored[field_name] == WIDGET_WITH_EVERY_FIELD_CHANGED[field_name], field_name
