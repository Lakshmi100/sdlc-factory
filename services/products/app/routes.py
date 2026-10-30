"""HTTP endpoints to create, read, update, delete and list products.

Status codes: POST returns 201, DELETE returns 204, an unknown id returns 404,
a duplicate sku returns 409, and invalid input returns 422 (raised by
FastAPI from the schemas).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductCreate, ProductRead, ProductUpdate

# Every endpoint below is served under /products.
router = APIRouter(prefix="/products", tags=["products"])


def find_product_or_404(session: Session, product_id: int) -> Product:
    """Load a product by id, or end the request with HTTP 404 if there is none."""
    product = session.get(Product, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


def save_or_409(session: Session) -> None:
    """Commit pending changes, turning a duplicate sku into HTTP 409.

    The database enforces unique skus. Checking for a duplicate before saving
    could race with another request doing the same, so the database decides
    and its error is translated here.
    """
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        # `from error` records the database error as the cause, for the logs.
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already in use") from error


# Framework note: the line starting with @ (a "decorator") registers the
# function below it as the handler for an HTTP method and path.
# `response_model` tells FastAPI to turn the returned database object into a
# ProductRead, and `Depends(get_db)` makes FastAPI pass in a database session.
@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, session: Session = Depends(get_db)) -> Product:
    """Create a product from the request body."""
    # Copy each field explicitly so it is clear what gets stored.
    # Python shortcut (copies every field automatically, less to maintain):
    #     product = Product(**payload.model_dump())
    # (the shortcut would also need the sku uppercased afterwards).
    product = Product(
        # Stored uppercase so the unique sku column is case-insensitive.
        sku=payload.sku.upper(),
        name=payload.name,
        description=payload.description,
        price=payload.price,
    )
    session.add(product)
    save_or_409(session)
    # Reload so values set by the database (id, created_at, updated_at) are filled in.
    session.refresh(product)
    return product


@router.get("", response_model=list[ProductRead])
def list_products(session: Session = Depends(get_db)) -> list[Product]:
    """Return every product, ordered by id."""
    query = select(Product).order_by(Product.id)
    result = session.scalars(query)
    return list(result)


# `{product_id}` in the path is passed to the function as the product_id argument.
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, session: Session = Depends(get_db)) -> Product:
    """Return one product by id."""
    product = find_product_or_404(session, product_id)
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, payload: ProductUpdate, session: Session = Depends(get_db)
) -> Product:
    """Replace every field of an existing product with the request body."""
    product = find_product_or_404(session, product_id)
    # PUT is a full replacement, so every field is overwritten, including
    # optional ones the client left out (they become null).
    # Python shortcut (copies every field automatically, less to maintain):
    #     for field, value in payload.model_dump().items():
    #         setattr(product, field, value)
    # (the shortcut would also need the sku uppercased afterwards).
    # Stored uppercase so the unique sku column is case-insensitive.
    product.sku = payload.sku.upper()
    product.name = payload.name
    product.description = payload.description
    product.price = payload.price
    save_or_409(session)
    # Reload so updated_at, set by the database layer, is filled in.
    session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: Session = Depends(get_db)) -> None:
    """Delete a product by id."""
    product = find_product_or_404(session, product_id)
    session.delete(product)
    session.commit()
