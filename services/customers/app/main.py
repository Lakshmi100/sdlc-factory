"""Customers service: the FastAPI application and its health check."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routes import router


# Framework note: `@asynccontextmanager` turns this function into the app's
# start-up and shut-down steps. Code before `yield` runs once when the service
# starts; code after it (none here) would run when it stops. FastAPI requires
# this function to be `async`.
@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    """Create any missing database tables when the service starts.

    FastAPI passes in the application; this function does not need it.
    Note that create_all only creates tables that do not exist yet. It never
    adds columns to an existing table.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Customers Service", version="0.1.0", lifespan=lifespan)
app.include_router(router)


@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Report that the service is running. Used by monitoring and smoke tests."""
    return {"status": "ok", "service": "customers"}
