"""Tests for the /customers endpoints. Each test checks one behaviour."""

from fastapi.testclient import TestClient

from app.schemas import CustomerCreate, CustomerUpdate

ADA = {"first_name": "Ada", "last_name": "Lovelace", "email": "ada@example.com"}
GRACE = {"first_name": "Grace", "last_name": "Hopper", "email": "grace@example.com"}

# Every field the API accepts, all set. Used by the guard tests at the end.
ADA_WITH_EVERY_FIELD = {
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "phone": "+44 20 7946 0000",
}

# Every field changed to a new value. Used to check that PUT stores every field.
ADA_WITH_EVERY_FIELD_CHANGED = {
    "first_name": "Augusta",
    "last_name": "King",
    "email": "augusta@example.com",
    "phone": "555-0199",
}

# "1" * 30 builds a string of thirty "1" characters: the longest phone allowed.
PHONE_AT_LIMIT = "1" * 30
PHONE_OVER_LIMIT = "1" * 31


def with_changes(customer: dict, changes: dict) -> dict:
    """Return a copy of `customer` with some fields replaced. The original is unchanged."""
    result = customer.copy()
    result.update(changes)
    return result


def create_customer(client: TestClient, customer: dict) -> dict:
    """POST a customer that is expected to be valid, and return the created record.

    Fails the test straight away if the API rejects it, so a broken setup step
    is not mistaken for the behaviour under test.
    """
    response = client.post("/customers", json=customer)
    assert response.status_code == 201, response.text
    return response.json()


def get_customer(client: TestClient, customer_id: int) -> dict:
    """GET a customer that is expected to exist, and return it."""
    response = client.get(f"/customers/{customer_id}")
    assert response.status_code == 200, response.text
    return response.json()


# ---- Create ----


def test_create_customer_returns_201_with_new_id(client):
    """POST stores a customer and returns it with a server-assigned id."""
    response = client.post("/customers", json=ADA)

    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 0
    assert created["email"] == "ada@example.com"


def test_create_rejects_invalid_email(client):
    """An email that is not a valid address is rejected with 422."""
    customer = with_changes(ADA, {"email": "not-an-email"})

    response = client.post("/customers", json=customer)

    assert response.status_code == 422


def test_create_rejects_blank_first_name(client):
    """An empty first name is rejected with 422."""
    customer = with_changes(ADA, {"first_name": ""})

    response = client.post("/customers", json=customer)

    assert response.status_code == 422


def test_create_rejects_duplicate_email(client):
    """Creating a second customer with an email already in use returns 409."""
    create_customer(client, ADA)

    response = client.post("/customers", json=ADA)

    assert response.status_code == 409


# ---- Read and list ----


def test_list_returns_customers_ordered_by_id(client):
    """GET /customers returns every customer, oldest (lowest id) first."""
    create_customer(client, ADA)
    create_customer(client, GRACE)

    response = client.get("/customers")

    assert response.status_code == 200
    customers = response.json()
    emails = [customer["email"] for customer in customers]
    assert emails == ["ada@example.com", "grace@example.com"]


def test_get_customer_by_id(client):
    """GET /customers/{id} returns that customer."""
    ada = create_customer(client, ADA)

    response = client.get(f"/customers/{ada['id']}")

    assert response.status_code == 200
    assert response.json()["first_name"] == "Ada"


def test_get_missing_customer_returns_404(client):
    """Asking for an id that does not exist returns 404."""
    response = client.get("/customers/999")

    assert response.status_code == 404


# ---- Update ----


def test_update_customer(client):
    """PUT replaces the customer's fields and returns the updated customer."""
    ada = create_customer(client, ADA)
    changed = with_changes(ADA, {"last_name": "King"})

    response = client.put(f"/customers/{ada['id']}", json=changed)

    assert response.status_code == 200
    assert response.json()["last_name"] == "King"


def test_update_to_duplicate_email_returns_409(client):
    """Changing a customer's email to one another customer already uses is rejected."""
    # Arrange: two customers with different emails
    create_customer(client, ADA)
    grace = create_customer(client, GRACE)

    # Act: try to give Grace the email that Ada already has
    grace_with_adas_email = with_changes(GRACE, {"email": ADA["email"]})
    response = client.put(f"/customers/{grace['id']}", json=grace_with_adas_email)

    # Assert: the unique-email rule is enforced
    assert response.status_code == 409


def test_update_missing_customer_returns_404(client):
    """Updating an id that does not exist returns 404."""
    response = client.put("/customers/999", json=ADA)

    assert response.status_code == 404


# ---- Delete ----


def test_delete_customer(client):
    """DELETE returns 204, and the customer can no longer be fetched."""
    ada = create_customer(client, ADA)

    delete_response = client.delete(f"/customers/{ada['id']}")

    assert delete_response.status_code == 204
    get_response = client.get(f"/customers/{ada['id']}")
    assert get_response.status_code == 404


def test_delete_missing_customer_returns_404(client):
    """Deleting an id that does not exist returns 404."""
    response = client.delete("/customers/999")

    assert response.status_code == 404


# ---- Phone number (RETAIL-1) ----


def test_create_customer_with_phone(client):
    """A phone number sent on POST is stored and returned by GET."""
    ada = create_customer(client, with_changes(ADA, {"phone": "+44 20 7946 0000"}))

    stored = get_customer(client, ada["id"])

    assert stored["phone"] == "+44 20 7946 0000"


def test_phone_is_null_when_not_set(client):
    """A customer created without a phone number has phone null."""
    ada = create_customer(client, ADA)

    stored = get_customer(client, ada["id"])

    assert stored["phone"] is None


def test_create_accepts_phone_of_30_chars(client):
    """A phone number of exactly 30 characters is accepted."""
    customer = with_changes(ADA, {"phone": PHONE_AT_LIMIT})

    response = client.post("/customers", json=customer)

    assert response.status_code == 201


def test_create_rejects_phone_over_30_chars(client):
    """A phone number longer than 30 characters is rejected with 422 on POST."""
    customer = with_changes(ADA, {"phone": PHONE_OVER_LIMIT})

    response = client.post("/customers", json=customer)

    assert response.status_code == 422


def test_update_sets_phone(client):
    """A phone number sent on PUT is stored and returned by GET."""
    ada = create_customer(client, ADA)
    changed = with_changes(ADA, {"phone": "555-0100"})

    response = client.put(f"/customers/{ada['id']}", json=changed)

    assert response.status_code == 200
    stored = get_customer(client, ada["id"])
    assert stored["phone"] == "555-0100"


def test_update_without_phone_clears_it(client):
    """PUT is a full replacement, so leaving phone out sets it back to null."""
    ada = create_customer(client, with_changes(ADA, {"phone": "555-0100"}))

    response = client.put(f"/customers/{ada['id']}", json=ADA)

    assert response.status_code == 200
    assert response.json()["phone"] is None


def test_update_rejects_phone_over_30_chars(client):
    """A phone number longer than 30 characters is rejected with 422 on PUT."""
    ada = create_customer(client, ADA)
    changed = with_changes(ADA, {"phone": PHONE_OVER_LIMIT})

    response = client.put(f"/customers/{ada['id']}", json=changed)

    assert response.status_code == 422


# ---- Guard tests: routes.py copies fields one by one (see style.md section 6) ----


def test_guard_data_covers_every_schema_field():
    """The guard test data lists exactly the fields that POST and PUT accept.

    If this fails, a field was added to (or removed from) the schemas. Update
    ADA_WITH_EVERY_FIELD, ADA_WITH_EVERY_FIELD_CHANGED and the explicit field
    assignments in routes.py to match.
    """
    create_fields = set(CustomerCreate.model_fields)
    update_fields = set(CustomerUpdate.model_fields)

    assert set(ADA_WITH_EVERY_FIELD) == create_fields
    assert set(ADA_WITH_EVERY_FIELD_CHANGED) == update_fields


def test_create_stores_every_field(client):
    """Every field sent on POST is stored. Fails if routes.py forgets to copy one."""
    ada = create_customer(client, ADA_WITH_EVERY_FIELD)

    stored = get_customer(client, ada["id"])

    for field_name in ADA_WITH_EVERY_FIELD:
        assert stored[field_name] == ADA_WITH_EVERY_FIELD[field_name], field_name


def test_update_stores_every_field(client):
    """Every field sent on PUT is stored. Fails if routes.py forgets to copy one."""
    ada = create_customer(client, ADA_WITH_EVERY_FIELD)

    response = client.put(f"/customers/{ada['id']}", json=ADA_WITH_EVERY_FIELD_CHANGED)

    assert response.status_code == 200
    stored = get_customer(client, ada["id"])
    for field_name in ADA_WITH_EVERY_FIELD_CHANGED:
        assert stored[field_name] == ADA_WITH_EVERY_FIELD_CHANGED[field_name], field_name
