"""Shapes of the JSON the products API accepts and returns.

FastAPI checks every request body against these schemas. Input that does not
fit is rejected with HTTP 422 before any endpoint code runs.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Fields shared by every product schema.

    Framework note: inheriting from `BaseModel` makes this a Pydantic schema.
    A field without a default value is required; `Field(...)` adds rules such
    as minimum and maximum length.
    """

    # sku may contain only printable ASCII other than space: "!" (0x21) to "~" (0x7E),
    # i.e. letters, digits and punctuation. Spaces, tabs, control characters and
    # non-ASCII letters are rejected (422). ASCII upper() never changes length,
    # so an uppercased sku still fits String(64).
    sku: str = Field(min_length=1, max_length=64, pattern=r"^[!-~]+$")
    # pattern=r"\S" means "contains at least one non-whitespace character", so
    # whitespace-only values are rejected; the value itself is not trimmed.
    name: str = Field(min_length=1, max_length=200, pattern=r"\S")
    # Optional: null when the client does not send it. The length and pattern
    # rules apply only when a string is sent.
    description: str | None = Field(default=None, min_length=10, max_length=2000, pattern=r"\S")


class ProductInput(ProductBase):
    """Fields a client sends when creating or replacing a product."""

    # Decimal keeps money exact. Accepts a JSON number or a numeric string.
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class ProductCreate(ProductInput):
    """Request body for POST /products."""


class ProductUpdate(ProductInput):
    """Request body for PUT /products/{id}.

    PUT replaces the whole product: required fields must be sent, and an
    optional field that is left out becomes null.
    """


class ProductRead(ProductBase):
    """A product as returned by the API, including the fields the server sets."""

    # Lets FastAPI build this schema from a database object (product.id,
    # product.sku, ...) instead of only from a dictionary.
    model_config = ConfigDict(from_attributes=True)

    id: int
    # float only so the JSON shows a number (19.99) rather than a string. The
    # exact value lives in the database (Numeric) and is validated as a Decimal
    # in ProductInput. Every allowed price fits exactly in a float's precision.
    price: float
    created_at: datetime
    updated_at: datetime
