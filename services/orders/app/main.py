"""Orders service: SCAFFOLD ONLY.

Order CRUD is intentionally not implemented. The agent factory delivers it
via Jira stories RETAIL-3 and RETAIL-4, following the pattern in
services/customers and the rules in style.md. Orders validate customers and products by calling the
other services over HTTP (see CUSTOMERS_URL / PRODUCTS_URL).
"""

import os

from fastapi import FastAPI

# Base addresses of the services this one calls. Docker Compose sets them to
# the container names; the defaults suit running everything on this machine.
CUSTOMERS_URL = os.getenv("CUSTOMERS_URL", "http://localhost:8001")
PRODUCTS_URL = os.getenv("PRODUCTS_URL", "http://localhost:8002")

app = FastAPI(title="Orders Service", version="0.1.0")


# Framework note: the line starting with @ (a "decorator") registers the
# function below it as the handler for GET /health.
@app.get("/health", tags=["ops"])
def health() -> dict[str, str]:
    """Report that the service is running. Used by monitoring and smoke tests."""
    return {"status": "ok", "service": "orders"}
