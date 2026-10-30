"""Shapes of the JSON the customers API accepts and returns.

FastAPI checks every request body against these schemas. Input that does not
fit is rejected with HTTP 422 before any endpoint code runs.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerBase(BaseModel):
    """Fields shared by every customer schema.

    Framework note: inheriting from `BaseModel` makes this a Pydantic schema.
    A field without a default value is required; `Field(...)` adds rules such
    as minimum and maximum length.
    """

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    # EmailStr rejects anything that does not look like an email address.
    email: EmailStr
    # Optional: null when the client does not send it.
    phone: str | None = Field(default=None, max_length=30)


class CustomerCreate(CustomerBase):
    """Request body for POST /customers."""


class CustomerUpdate(CustomerBase):
    """Request body for PUT /customers/{id}.

    PUT replaces the whole customer: required fields must be sent, and an
    optional field that is left out becomes null.
    """


class CustomerRead(CustomerBase):
    """A customer as returned by the API, including the fields the server sets."""

    # Lets FastAPI build this schema from a database object (customer.id,
    # customer.email, ...) instead of only from a dictionary.
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
