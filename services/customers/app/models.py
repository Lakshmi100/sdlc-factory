"""Database tables for the customers service."""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utcnow() -> datetime:
    """Return the current time in UTC. Used to stamp created_at and updated_at."""
    return datetime.now(UTC)


class Customer(Base):
    """One row in the customers table.

    Framework note: each `Mapped[...]` line declares a column. `Mapped[...]`
    gives its Python type (`str | None` means the column may be empty, NULL)
    and `mapped_column(...)` gives how it is stored.
    """

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    # unique=True: the database refuses two customers with the same email.
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30))
    # `utcnow` is passed without brackets: the database layer calls it on every
    # insert (default) or update (onupdate), rather than once at start-up.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
