"""Database tables for the products service."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    """Return the current time in UTC. Used to stamp created_at and updated_at."""
    return datetime.now(UTC)


class Product(Base):
    """One row in the products table.

    Framework note: each `Mapped[...]` line declares a column. `Mapped[...]`
    gives its Python type (`str | None` means the column may be empty, NULL)
    and `mapped_column(...)` gives how it is stored.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # unique=True: the database refuses two products with the same sku. The
    # routes store every sku in uppercase, so this also makes the check
    # case-insensitive ("wid-001" and "WID-001" clash).
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    # Numeric(10, 2) stores money exactly: up to 10 digits, 2 after the point.
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    # `utcnow` is passed without brackets: the database layer calls it on every
    # insert (default) or update (onupdate), rather than once at start-up.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
