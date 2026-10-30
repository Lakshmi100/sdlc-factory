"""HTTP endpoints to create, read, update, delete and list customers.

Status codes: POST returns 201, DELETE returns 204, an unknown id returns 404,
a duplicate email returns 409, and invalid input returns 422 (raised by
FastAPI from the schemas).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer
from app.schemas import CustomerCreate, CustomerRead, CustomerUpdate

# Every endpoint below is served under /customers.
router = APIRouter(prefix="/customers", tags=["customers"])


def find_customer_or_404(session: Session, customer_id: int) -> Customer:
    """Load a customer by id, or end the request with HTTP 404 if there is none."""
    customer = session.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Customer not found")
    return customer


def save_or_409(session: Session) -> None:
    """Commit pending changes, turning a duplicate email into HTTP 409.

    The database enforces unique emails. Checking for a duplicate before saving
    could race with another request doing the same, so the database decides
    and its error is translated here.
    """
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        # `from error` records the database error as the cause, for the logs.
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use") from error


# Framework note: the line starting with @ (a "decorator") registers the
# function below it as the handler for an HTTP method and path.
# `response_model` tells FastAPI to turn the returned database object into a
# CustomerRead, and `Depends(get_db)` makes FastAPI pass in a database session.
@router.post("", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, session: Session = Depends(get_db)) -> Customer:
    """Create a customer from the request body."""
    # Copy each field explicitly so it is clear what gets stored.
    # Python shortcut (copies every field automatically, less to maintain):
    #     customer = Customer(**payload.model_dump())
    customer = Customer(
        first_name=payload.first_name,
        last_name=payload.last_name,
        email=payload.email,
        phone=payload.phone,
    )
    session.add(customer)
    save_or_409(session)
    # Reload so values set by the database (id, created_at, updated_at) are filled in.
    session.refresh(customer)
    return customer


@router.get("", response_model=list[CustomerRead])
def list_customers(session: Session = Depends(get_db)) -> list[Customer]:
    """Return every customer, ordered by id."""
    query = select(Customer).order_by(Customer.id)
    result = session.scalars(query)
    return list(result)


# `{customer_id}` in the path is passed to the function as the customer_id argument.
@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer(customer_id: int, session: Session = Depends(get_db)) -> Customer:
    """Return one customer by id."""
    customer = find_customer_or_404(session, customer_id)
    return customer


@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(
    customer_id: int, payload: CustomerUpdate, session: Session = Depends(get_db)
) -> Customer:
    """Replace every field of an existing customer with the request body."""
    customer = find_customer_or_404(session, customer_id)
    # PUT is a full replacement, so every field is overwritten, including
    # optional ones the client left out (they become null).
    # Python shortcut (copies every field automatically, less to maintain):
    #     for field, value in payload.model_dump().items():
    #         setattr(customer, field, value)
    customer.first_name = payload.first_name
    customer.last_name = payload.last_name
    customer.email = payload.email
    customer.phone = payload.phone
    save_or_409(session)
    # Reload so updated_at, set by the database layer, is filled in.
    session.refresh(customer)
    return customer


@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, session: Session = Depends(get_db)) -> None:
    """Delete a customer by id."""
    customer = find_customer_or_404(session, customer_id)
    session.delete(customer)
    session.commit()
